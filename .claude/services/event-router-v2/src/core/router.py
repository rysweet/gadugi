#!/usr/bin/env python3
"""WebSocket-based Event Router Service V2."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Callable, Any
from collections import defaultdict
import traceback

try:
    import websockets
    from websockets.exceptions import WebSocketException
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    websockets = None  # type: ignore
    WebSocketException = Exception  # type: ignore

from .models import (
    Event, EventType, EventPriority, EventMetadata,
    Subscription, HealthStatus, DeliveryStatus
)
from .queue import EventQueue, MultiQueue

logger = logging.getLogger(__name__)


class EventRouter:
    """Core event router with WebSocket support."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9090,
        max_queue_size: int = 10000,
        max_clients: int = 1000,
        use_multi_queue: bool = False
    ):
        """Initialize event router.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            max_queue_size: Maximum queue size
            max_clients: Maximum concurrent clients
            use_multi_queue: Use multiple priority queues
        """
        self.host = host
        self.port = port
        self.max_clients = max_clients
        
        # Event queue
        if use_multi_queue:
            self.queue = MultiQueue()
        else:
            self.queue = EventQueue(max_size=max_queue_size)
        self.use_multi_queue = use_multi_queue
        
        # Subscriptions
        self.subscriptions: Dict[str, Subscription] = {}
        self.subscriber_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # WebSocket connections
        self.clients: Dict[str, Any] = {}  # WebSocketServerProtocol when available
        self.client_info: Dict[str, Dict] = {}
        
        # Statistics
        self.start_time = time.time()
        self.events_processed = 0
        self.events_failed = 0
        self.last_event_at: Optional[datetime] = None
        
        # Service state
        self.running = False
        self.server = None
        self.processor_task = None
        
        # Callbacks for local subscriptions
        self.local_callbacks: Dict[str, Callable] = {}
    
    async def start(self):
        """Start the event router service."""
        if not WEBSOCKET_AVAILABLE:
            raise RuntimeError("websockets library not installed. Install with: pip install websockets")
        
        self.running = True
        logger.info(f"Starting Event Router on {self.host}:{self.port}")
        
        # Start event processor
        self.processor_task = asyncio.create_task(self._process_events())
        
        # Start WebSocket server
        if websockets is not None:
            async with websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                max_size=10**7,  # 10MB max message size
                max_queue=100,
                compression=None  # Disable compression for lower latency
            ) as server:
                self.server = server
                logger.info(f"Event Router listening on ws://{self.host}:{self.port}")
                
                # Keep server running
                await asyncio.Future()  # Run forever
        else:
            raise RuntimeError("websockets module not available")
    
    async def stop(self):
        """Stop the event router service."""
        logger.info("Stopping Event Router...")
        self.running = False
        
        # Cancel processor task
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        # Close all client connections
        for client_id, websocket in list(self.clients.items()):
            await websocket.close()
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Event Router stopped")
    
    async def _handle_client(self, websocket: Any):  # WebSocketServerProtocol when available
        """Handle WebSocket client connection."""
        client_id = str(uuid.uuid4())
        client_address = websocket.remote_address
        path = websocket.path if hasattr(websocket, 'path') else "/"
        
        # Check max clients
        if len(self.clients) >= self.max_clients:
            await websocket.send(json.dumps({
                "type": "error",
                "error": "max_clients_reached",
                "message": f"Maximum clients ({self.max_clients}) reached"
            }))
            await websocket.close()
            return
        
        # Register client
        self.clients[client_id] = websocket
        self.client_info[client_id] = {
            "address": client_address,
            "connected_at": datetime.now(timezone.utc),
            "path": path
        }
        
        logger.info(f"Client {client_id} connected from {client_address}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "client_id": client_id,
            "server_time": datetime.now(timezone.utc).isoformat()
        }))
        
        try:
            # Handle client messages
            async for message in websocket:
                await self._handle_message(client_id, message)
                
        except Exception as e:
            if websockets and isinstance(e, WebSocketException):
                logger.info(f"Client {client_id} disconnected")
            else:
                logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client
            await self._cleanup_client(client_id)
    
    async def _handle_message(self, client_id: str, message: str):
        """Handle message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "ping":
                await self._handle_ping(client_id, data)
            elif msg_type == "publish":
                await self._handle_publish(client_id, data)
            elif msg_type == "subscribe":
                await self._handle_subscribe(client_id, data)
            elif msg_type == "unsubscribe":
                await self._handle_unsubscribe(client_id, data)
            elif msg_type == "get_health":
                await self._handle_get_health(client_id)
            else:
                await self._send_error(client_id, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            await self._send_error(client_id, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self._send_error(client_id, f"Internal error: {e}")
    
    async def _handle_ping(self, client_id: str, data: Dict):
        """Handle ping message."""
        await self._send_to_client(client_id, {
            "type": "pong",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "echo": data.get("echo")
        })
    
    async def _handle_publish(self, client_id: str, data: Dict):
        """Handle publish message."""
        try:
            event_data = data.get("event", {})
            
            # Create event from data
            if isinstance(event_data, dict):
                # Set source if not provided
                if not event_data.get("source"):
                    event_data["source"] = client_id
                
                # Set topic if not provided
                if not event_data.get("topic") and event_data.get("type"):
                    event_data["topic"] = event_data["type"]
                
                event = Event.from_dict(event_data)
            else:
                raise ValueError("Event data must be a dictionary")
            
            # Add to queue
            if self.use_multi_queue:
                success = await self.queue.put(event)
            else:
                success = await self.queue.put(event)
            
            if success:
                logger.debug(f"Event {event.id} published by {client_id}")
                await self._send_to_client(client_id, {
                    "type": "published",
                    "event_id": event.id,
                    "status": "queued"
                })
            else:
                await self._send_to_client(client_id, {
                    "type": "published",
                    "event_id": event.id,
                    "status": "dropped",
                    "reason": "queue_full"
                })
                
        except Exception as e:
            logger.error(f"Error publishing event from {client_id}: {e}")
            await self._send_error(client_id, f"Failed to publish event: {e}")
    
    async def _handle_subscribe(self, client_id: str, data: Dict):
        """Handle subscribe message."""
        try:
            sub_data = data.get("subscription", {})
            
            # Create subscription
            subscription = Subscription(
                subscriber_id=client_id,
                topics=sub_data.get("topics", ["*"]),
                types=[EventType(t) for t in sub_data.get("types", [])] if sub_data.get("types") else [],
                priorities=[EventPriority(p) for p in sub_data.get("priorities", [])] if sub_data.get("priorities") else [],
                sources=sub_data.get("sources", []),
                endpoint=client_id  # Use client_id as endpoint for WebSocket delivery
            )
            
            # Store subscription
            self.subscriptions[subscription.id] = subscription
            self.subscriber_subscriptions[client_id].add(subscription.id)
            
            logger.info(f"Subscription {subscription.id} created for client {client_id}")
            
            await self._send_to_client(client_id, {
                "type": "subscribed",
                "subscription_id": subscription.id,
                "topics": subscription.topics
            })
            
        except Exception as e:
            logger.error(f"Error creating subscription for {client_id}: {e}")
            await self._send_error(client_id, f"Failed to subscribe: {e}")
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict):
        """Handle unsubscribe message."""
        subscription_id = data.get("subscription_id")
        
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            if subscription.subscriber_id == client_id:
                del self.subscriptions[subscription_id]
                self.subscriber_subscriptions[client_id].discard(subscription_id)
                
                await self._send_to_client(client_id, {
                    "type": "unsubscribed",
                    "subscription_id": subscription_id
                })
            else:
                await self._send_error(client_id, "Subscription not owned by client")
        else:
            await self._send_error(client_id, "Subscription not found")
    
    async def _handle_get_health(self, client_id: str):
        """Handle health check request."""
        health = await self.get_health()
        await self._send_to_client(client_id, {
            "type": "health",
            "health": health.to_dict()
        })
    
    async def _send_to_client(self, client_id: str, data: Dict):
        """Send message to specific client."""
        if client_id in self.clients:
            try:
                websocket = self.clients[client_id]
                await websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                await self._cleanup_client(client_id)
    
    async def _send_error(self, client_id: str, error: str):
        """Send error message to client."""
        await self._send_to_client(client_id, {
            "type": "error",
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def _cleanup_client(self, client_id: str):
        """Clean up disconnected client."""
        # Remove client
        if client_id in self.clients:
            del self.clients[client_id]
        
        if client_id in self.client_info:
            del self.client_info[client_id]
        
        # Remove subscriptions
        for sub_id in list(self.subscriber_subscriptions[client_id]):
            if sub_id in self.subscriptions:
                del self.subscriptions[sub_id]
        
        del self.subscriber_subscriptions[client_id]
        
        logger.info(f"Client {client_id} cleaned up")
    
    async def _process_events(self):
        """Process events from queue and deliver to subscribers."""
        logger.info("Event processor started")
        
        while self.running:
            try:
                # Get next event
                if self.use_multi_queue:
                    event = await self.queue.get_next(timeout=1.0)
                else:
                    event = await self.queue.get(timeout=1.0)
                
                if event:
                    await self._deliver_event(event)
                    self.events_processed += 1
                    self.last_event_at = datetime.now(timezone.utc)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                self.events_failed += 1
        
        logger.info("Event processor stopped")
    
    async def _deliver_event(self, event: Event):
        """Deliver event to matching subscribers."""
        delivered_to = set()
        
        for sub_id, subscription in list(self.subscriptions.items()):
            if subscription.matches(event):
                # Deliver via WebSocket
                if subscription.endpoint in self.clients:
                    try:
                        await self._send_to_client(subscription.endpoint, {
                            "type": "event",
                            "event": event.to_dict(),
                            "subscription_id": sub_id
                        })
                        delivered_to.add(subscription.subscriber_id)
                        event.delivery_status = DeliveryStatus.DELIVERED
                        event.delivery_attempts += 1
                        event.last_delivery_attempt = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.error(f"Failed to deliver event {event.id} to {subscription.subscriber_id}: {e}")
                        event.delivery_status = DeliveryStatus.FAILED
                        event.delivery_error = str(e)
                
                # Deliver via local callback
                elif subscription.callback:
                    try:
                        if asyncio.iscoroutinefunction(subscription.callback):
                            await subscription.callback(event)
                        else:
                            subscription.callback(event)
                        delivered_to.add(subscription.subscriber_id)
                        event.delivery_status = DeliveryStatus.DELIVERED
                    except Exception as e:
                        logger.error(f"Callback failed for event {event.id}: {e}")
                        event.delivery_status = DeliveryStatus.FAILED
                        event.delivery_error = str(e)
        
        if delivered_to:
            logger.debug(f"Event {event.id} delivered to {len(delivered_to)} subscribers")
        else:
            logger.debug(f"Event {event.id} had no matching subscribers")
    
    # Local API methods (for in-process use)
    
    async def publish(self, event: Event) -> bool:
        """Publish event locally.
        
        Args:
            event: Event to publish
            
        Returns:
            True if event was queued
        """
        if self.use_multi_queue:
            return await self.queue.put(event)
        else:
            return await self.queue.put(event)
    
    def subscribe(
        self,
        subscriber_id: str,
        topics: Optional[List[str]] = None,
        types: Optional[List[EventType]] = None,
        callback: Optional[Callable[[Event], None]] = None
    ) -> str:
        """Create local subscription.
        
        Args:
            subscriber_id: Subscriber identifier
            topics: Topic patterns to match
            types: Event types to match
            callback: Callback function
            
        Returns:
            Subscription ID
        """
        subscription = Subscription(
            subscriber_id=subscriber_id,
            topics=topics or ["*"],
            types=types or [],
            callback=callback
        )
        
        self.subscriptions[subscription.id] = subscription
        self.subscriber_subscriptions[subscriber_id].add(subscription.id)
        
        return subscription.id
    
    def unsubscribe(self, subscription_id: str):
        """Remove subscription.
        
        Args:
            subscription_id: Subscription to remove
        """
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            del self.subscriptions[subscription_id]
            self.subscriber_subscriptions[subscription.subscriber_id].discard(subscription_id)
    
    async def get_health(self) -> HealthStatus:
        """Get health status.
        
        Returns:
            Health status
        """
        uptime = time.time() - self.start_time
        
        if self.use_multi_queue:
            queue_stats = await self.queue.get_stats()  # type: ignore
            queue_size = sum(s.get("size", 0) for s in queue_stats.values())
        else:
            stats = await self.queue.get_stats()  # type: ignore
            queue_size = stats.get("size", 0)
        
        # Determine health status
        status = "healthy"
        errors = []
        
        if queue_size > 8000:  # 80% full
            status = "degraded"
            errors.append("Queue approaching capacity")
        
        if self.events_failed > self.events_processed * 0.1:  # 10% failure rate
            status = "unhealthy"
            errors.append("High failure rate")
        
        return HealthStatus(
            status=status,
            uptime=uptime,
            events_processed=self.events_processed,
            events_failed=self.events_failed,
            events_in_queue=queue_size,
            active_subscriptions=len(self.subscriptions),
            connected_clients=len(self.clients),
            last_event_at=self.last_event_at,
            errors=errors
        )