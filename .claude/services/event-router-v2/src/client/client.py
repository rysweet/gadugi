#!/usr/bin/env python3
"""Event Router Client SDK with auto-reconnection."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict
from enum import Enum

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    WebSocketClientProtocol = Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import Event, EventType, EventPriority, EventMetadata

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class EventRouterClient:
    """Event Router client with auto-reconnection."""
    
    def __init__(
        self,
        url: str = "ws://localhost:9090",
        auto_reconnect: bool = True,
        reconnect_interval: float = 1.0,
        max_reconnect_interval: float = 30.0,
        reconnect_decay: float = 1.5,
        heartbeat_interval: float = 30.0,
        timeout: float = 10.0
    ):
        """Initialize event router client.
        
        Args:
            url: WebSocket URL
            auto_reconnect: Enable auto-reconnection
            reconnect_interval: Initial reconnection interval
            max_reconnect_interval: Maximum reconnection interval
            reconnect_decay: Exponential backoff factor
            heartbeat_interval: Heartbeat interval
            timeout: Connection timeout
        """
        self.url = url
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_interval = max_reconnect_interval
        self.reconnect_decay = reconnect_decay
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        
        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        
        # Reconnection
        self.reconnect_task: Optional[asyncio.Task] = None
        self.current_reconnect_interval = reconnect_interval
        self.reconnect_attempts = 0
        
        # Heartbeat
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.last_pong: Optional[float] = None
        
        # Message handling
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.pending_messages: List[Dict] = []
        
        # Subscriptions
        self.subscriptions: Dict[str, Dict] = {}
        self.subscription_callbacks: Dict[str, Callable] = {}
        
        # Statistics
        self.connected_at: Optional[datetime] = None
        self.messages_sent = 0
        self.messages_received = 0
        self.events_published = 0
        self.events_received = 0
    
    async def connect(self) -> bool:
        """Connect to event router.
        
        Returns:
            True if connected successfully
        """
        if self.state == ConnectionState.CONNECTED:
            return True
        
        self.state = ConnectionState.CONNECTING
        
        try:
            if not WEBSOCKET_AVAILABLE:
                raise RuntimeError("websockets library not installed")
            
            # Connect with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.url,
                    max_size=10**7,
                    compression=None
                ),
                timeout=self.timeout
            )
            
            self.state = ConnectionState.CONNECTED
            self.connected_at = datetime.now(timezone.utc)
            self.reconnect_attempts = 0
            self.current_reconnect_interval = self.reconnect_interval
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            # Start heartbeat
            if self.heartbeat_interval > 0:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Wait for welcome message
            await self._wait_for_welcome()
            
            logger.info(f"Connected to {self.url} as {self.client_id}")
            
            # Re-establish subscriptions
            await self._restore_subscriptions()
            
            # Send pending messages
            await self._send_pending_messages()
            
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.url}")
            self.state = ConnectionState.DISCONNECTED
            await self._schedule_reconnect()
            return False
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.DISCONNECTED
            await self._schedule_reconnect()
            return False
    
    async def disconnect(self):
        """Disconnect from event router."""
        self.state = ConnectionState.CLOSED
        self.auto_reconnect = False
        
        # Cancel tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.reconnect_task:
            self.reconnect_task.cancel()
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.client_id = None
        logger.info("Disconnected from event router")
    
    async def _handle_messages(self):
        """Handle incoming messages."""
        try:
            async for message in self.websocket:
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
        finally:
            if self.state != ConnectionState.CLOSED:
                self.state = ConnectionState.DISCONNECTED
                await self._schedule_reconnect()
    
    async def _process_message(self, message: str):
        """Process incoming message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            self.messages_received += 1
            
            # Handle specific message types
            if msg_type == "welcome":
                self.client_id = data.get("client_id")
                await self._trigger_handlers("welcome", data)
                
            elif msg_type == "event":
                event = Event.from_dict(data.get("event", {}))
                self.events_received += 1
                await self._deliver_event(event, data.get("subscription_id"))
                
            elif msg_type == "pong":
                self.last_pong = time.time()
                await self._trigger_handlers("pong", data)
                
            elif msg_type == "subscribed":
                sub_id = data.get("subscription_id")
                if sub_id:
                    self.subscriptions[sub_id]["confirmed"] = True
                await self._trigger_handlers("subscribed", data)
                
            elif msg_type == "published":
                await self._trigger_handlers("published", data)
                
            elif msg_type == "error":
                logger.error(f"Server error: {data.get('error')}")
                await self._trigger_handlers("error", data)
                
            else:
                await self._trigger_handlers(msg_type, data)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _trigger_handlers(self, msg_type: str, data: Dict):
        """Trigger message handlers."""
        handlers = self.message_handlers.get(msg_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Handler error for {msg_type}: {e}")
    
    async def _deliver_event(self, event: Event, subscription_id: Optional[str]):
        """Deliver event to handlers."""
        # Check subscription callback
        if subscription_id and subscription_id in self.subscription_callbacks:
            callback = self.subscription_callbacks[subscription_id]
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Subscription callback error: {e}")
        
        # Check topic handlers
        for pattern in self.event_handlers:
            if event.matches_topic(pattern):
                for handler in self.event_handlers[pattern]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
    
    async def _wait_for_welcome(self):
        """Wait for welcome message."""
        timeout = 5.0
        start = time.time()
        
        while not self.client_id and time.time() - start < timeout:
            await asyncio.sleep(0.1)
        
        if not self.client_id:
            raise TimeoutError("No welcome message received")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.state == ConnectionState.CONNECTED:
            try:
                await self.ping()
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check for missed pong
                if self.last_pong and time.time() - self.last_pong > self.heartbeat_interval * 2:
                    logger.warning("Heartbeat timeout, reconnecting...")
                    await self.websocket.close()
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _schedule_reconnect(self):
        """Schedule reconnection attempt."""
        if not self.auto_reconnect or self.state == ConnectionState.CLOSED:
            return
        
        if self.reconnect_task and not self.reconnect_task.done():
            return
        
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1
        
        logger.info(f"Reconnecting in {self.current_reconnect_interval:.1f}s (attempt {self.reconnect_attempts})")
        
        await asyncio.sleep(self.current_reconnect_interval)
        
        # Exponential backoff
        self.current_reconnect_interval = min(
            self.current_reconnect_interval * self.reconnect_decay,
            self.max_reconnect_interval
        )
        
        # Attempt reconnection
        await self.connect()
    
    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection."""
        for sub_id, sub_data in list(self.subscriptions.items()):
            if sub_data.get("active"):
                await self._send({
                    "type": "subscribe",
                    "subscription": sub_data["config"]
                })
    
    async def _send_pending_messages(self):
        """Send pending messages after reconnection."""
        pending = self.pending_messages.copy()
        self.pending_messages.clear()
        
        for message in pending:
            await self._send(message)
    
    async def _send(self, data: Dict) -> bool:
        """Send message to server.
        
        Args:
            data: Message data
            
        Returns:
            True if sent successfully
        """
        if self.state != ConnectionState.CONNECTED:
            # Queue message for later
            self.pending_messages.append(data)
            return False
        
        try:
            await self.websocket.send(json.dumps(data))
            self.messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.pending_messages.append(data)
            return False
    
    # Public API
    
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        type: EventType = EventType.CUSTOM,
        target: Optional[str] = None
    ) -> Optional[str]:
        """Publish an event.
        
        Args:
            topic: Event topic
            payload: Event payload
            priority: Event priority
            type: Event type
            target: Target subscriber
            
        Returns:
            Event ID if published
        """
        event = Event(
            topic=topic,
            payload=payload,
            priority=priority,
            type=type,
            target=target,
            source=self.client_id or "client"
        )
        
        success = await self._send({
            "type": "publish",
            "event": event.to_dict()
        })
        
        if success:
            self.events_published += 1
            return event.id
        
        return None
    
    async def subscribe(
        self,
        topics: List[str] = None,
        types: List[EventType] = None,
        priorities: List[EventPriority] = None,
        sources: List[str] = None,
        callback: Optional[Callable[[Event], None]] = None
    ) -> Optional[str]:
        """Subscribe to events.
        
        Args:
            topics: Topic patterns
            types: Event types
            priorities: Minimum priorities
            sources: Source filters
            callback: Event callback
            
        Returns:
            Subscription ID
        """
        sub_config = {
            "topics": topics or ["*"],
            "types": [t.value for t in types] if types else [],
            "priorities": [int(p) for p in priorities] if priorities else [],
            "sources": sources or []
        }
        
        sub_id = str(uuid.uuid4())
        
        # Store subscription
        self.subscriptions[sub_id] = {
            "config": sub_config,
            "callback": callback,
            "active": True,
            "confirmed": False
        }
        
        if callback:
            self.subscription_callbacks[sub_id] = callback
        
        # Send subscription
        success = await self._send({
            "type": "subscribe",
            "subscription": sub_config
        })
        
        if success:
            return sub_id
        
        return None
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events.
        
        Args:
            subscription_id: Subscription to remove
            
        Returns:
            True if unsubscribed
        """
        if subscription_id not in self.subscriptions:
            return False
        
        success = await self._send({
            "type": "unsubscribe",
            "subscription_id": subscription_id
        })
        
        if success:
            self.subscriptions[subscription_id]["active"] = False
            if subscription_id in self.subscription_callbacks:
                del self.subscription_callbacks[subscription_id]
        
        return success
    
    async def ping(self) -> bool:
        """Send ping to server.
        
        Returns:
            True if sent
        """
        return await self._send({
            "type": "ping",
            "echo": time.time()
        })
    
    async def get_health(self) -> Optional[Dict]:
        """Get server health status.
        
        Returns:
            Health status or None
        """
        health_data = {}
        health_received = asyncio.Event()
        
        async def health_handler(data):
            health_data.update(data.get("health", {}))
            health_received.set()
        
        # Register temporary handler
        self.message_handlers["health"].append(health_handler)
        
        try:
            # Request health
            await self._send({"type": "get_health"})
            
            # Wait for response
            await asyncio.wait_for(health_received.wait(), timeout=5.0)
            
            return health_data
            
        except asyncio.TimeoutError:
            return None
        finally:
            self.message_handlers["health"].remove(health_handler)
    
    def on(self, topic: str):
        """Decorator for event handlers.
        
        Args:
            topic: Topic pattern to match
            
        Returns:
            Decorator function
        """
        def decorator(func):
            self.event_handlers[topic].append(func)
            return func
        return decorator
    
    def on_message(self, msg_type: str):
        """Decorator for message handlers.
        
        Args:
            msg_type: Message type
            
        Returns:
            Decorator function
        """
        def decorator(func):
            self.message_handlers[msg_type].append(func)
            return func
        return decorator
    
    async def wait_until_connected(self, timeout: float = 10.0) -> bool:
        """Wait until connected.
        
        Args:
            timeout: Maximum wait time
            
        Returns:
            True if connected
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if self.state == ConnectionState.CONNECTED:
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.state == ConnectionState.CONNECTED
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()