#!/usr/bin/env python3
"""
Event Router Service for Gadugi v0.3

Real-time event-driven communication system with protobuf support.
Handles event routing, filtering, and agent coordination across the platform.
"""

import asyncio
import json
import logging
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Protobuf imports (would be generated from .proto files)
try:
    # These would be generated from protobuf definitions
    from . import events_pb2
    from . import agent_messages_pb2

    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False


class EventType(Enum):
    """Event type enumeration."""

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    SYSTEM_ALERT = "system_alert"
    CUSTOM_EVENT = "custom_event"


class EventPriority(Enum):
    """Event priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SubscriptionType(Enum):
    """Subscription type enumeration."""

    ALL = "all"
    FILTERED = "filtered"
    PATTERN = "pattern"
    CONDITIONAL = "conditional"


@dataclass
class Event:
    """Event data structure."""

    id: str
    type: EventType
    priority: EventPriority
    timestamp: datetime
    source: str
    target: Optional[str]
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "target": self.target,
            "payload": self.payload,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            priority=EventPriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            target=data.get("target"),
            payload=data["payload"],
            metadata=data["metadata"],
            correlation_id=data.get("correlation_id"),
        )


@dataclass
class EventFilter:
    """Event filtering configuration."""

    event_types: Optional[List[EventType]] = None
    sources: Optional[List[str]] = None
    targets: Optional[List[str]] = None
    priorities: Optional[List[EventPriority]] = None
    pattern: Optional[str] = None
    custom_filter: Optional[Callable[[Event], bool]] = None


@dataclass
class Subscription:
    """Event subscription configuration."""

    id: str
    subscriber_id: str
    subscription_type: SubscriptionType
    filter: Optional[EventFilter]
    callback: Optional[Callable[[Event], None]]
    endpoint: Optional[str]
    active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class EventStats:
    """Event processing statistics."""

    total_events: int = 0
    events_by_type: Dict[str, int] = None
    events_by_priority: Dict[str, int] = None
    events_by_source: Dict[str, int] = None
    average_processing_time: float = 0.0
    failed_deliveries: int = 0
    active_subscriptions: int = 0

    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = {}
        if self.events_by_priority is None:
            self.events_by_priority = {}
        if self.events_by_source is None:
            self.events_by_source = {}


class EventQueue:
    """Thread-safe event queue with priority support."""

    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self._queues = {
            EventPriority.CRITICAL: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.HIGH: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.NORMAL: asyncio.Queue(maxsize=maxsize // 2),
            EventPriority.LOW: asyncio.Queue(maxsize=maxsize // 4),
        }
        self._lock = threading.Lock()
        self._total_size = 0

    async def put(self, event: Event):
        """Add event to queue."""
        if self._total_size >= self.maxsize:
            # Remove oldest low priority event to make space
            try:
                await asyncio.wait_for(
                    self._queues[EventPriority.LOW].get(), timeout=0.1
                )
                self._total_size -= 1
            except asyncio.TimeoutError:
                pass

        await self._queues[event.priority].put(event)
        with self._lock:
            self._total_size += 1

    async def get(self) -> Event:
        """Get next event from queue (priority order)."""
        # Try to get from priority queues in order
        for priority in [
            EventPriority.CRITICAL,
            EventPriority.HIGH,
            EventPriority.NORMAL,
            EventPriority.LOW,
        ]:
            try:
                event = await asyncio.wait_for(
                    self._queues[priority].get(), timeout=0.1
                )
                with self._lock:
                    self._total_size -= 1
                return event
            except asyncio.TimeoutError:
                continue

        # If no events available, wait for any
        tasks = [asyncio.create_task(queue.get()) for queue in self._queues.values()]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel pending tasks
        for task in pending:
            task.cancel()

        # Get result from completed task
        result = done.pop().result()
        with self._lock:
            self._total_size -= 1
        return result

    def qsize(self) -> int:
        """Get total queue size."""
        return self._total_size

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._total_size == 0


class EventRouterService:
    """Event router service for real-time event processing."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9090,
        max_workers: int = 10,
        queue_size: int = 10000,
    ):
        """Initialize the event router service."""
        self.host = host
        self.port = port
        self.max_workers = max_workers

        self.logger = self._setup_logging()

        # Core components
        self.event_queue = EventQueue(maxsize=queue_size)
        self.subscriptions: Dict[str, Subscription] = {}
        self.stats = EventStats()

        # Service state
        self.running = False
        self.server_task: Optional[asyncio.Task] = None
        self.processor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Event history (for debugging and replay)
        self.event_history: List[Event] = []
        self.max_history_size = 1000

        # Connection management
        self.active_connections: Dict[str, Any] = {}

        # Protobuf support
        self.protobuf_enabled = PROTOBUF_AVAILABLE
        if not PROTOBUF_AVAILABLE:
            self.logger.warning("Protobuf not available, using JSON serialization")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the event router service."""
        logger = logging.getLogger("event_router")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def start(self):
        """Start the event router service."""
        if self.running:
            self.logger.warning("Event router service is already running")
            return

        self.running = True
        self.logger.info(f"Starting event router service on {self.host}:{self.port}")

        # Start server task
        self.server_task = asyncio.create_task(self._run_server())

        # Start event processor task
        self.processor_task = asyncio.create_task(self._process_events())

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("Event router service started successfully")

    async def stop(self):
        """Stop the event router service."""
        if not self.running:
            return

        self.logger.info("Stopping event router service")
        self.running = False

        # Cancel tasks
        if self.server_task:
            self.server_task.cancel()
        if self.processor_task:
            self.processor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Wait for tasks to complete
        tasks = [
            task
            for task in [self.server_task, self.processor_task, self.cleanup_task]
            if task
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        self.logger.info("Event router service stopped")

    async def _run_server(self):
        """Run the event server."""
        try:
            server = await asyncio.start_server(
                self._handle_client, self.host, self.port
            )

            self.logger.info(f"Server listening on {self.host}:{self.port}")

            async with server:
                await server.serve_forever()

        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
        except Exception as e:
            self.logger.error(f"Server error: {e}")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle client connections."""
        client_addr = writer.get_extra_info("peername")
        client_id = f"{client_addr[0]}:{client_addr[1]}:{int(time.time())}"

        self.logger.info(f"Client connected: {client_id}")
        self.active_connections[client_id] = {
            "reader": reader,
            "writer": writer,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
        }

        try:
            while self.running:
                # Read message length
                length_data = await reader.read(4)
                if not length_data:
                    break

                message_length = int.from_bytes(length_data, byteorder="big")

                # Read message data
                message_data = await reader.read(message_length)
                if not message_data:
                    break

                # Update activity
                self.active_connections[client_id]["last_activity"] = datetime.now()

                # Process message
                await self._process_client_message(client_id, message_data)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.active_connections.pop(client_id, None)
            self.logger.info(f"Client disconnected: {client_id}")

    async def _process_client_message(self, client_id: str, message_data: bytes):
        """Process message from client."""
        try:
            if self.protobuf_enabled:
                # Parse protobuf message
                message = self._parse_protobuf_message(message_data)
            else:
                # Parse JSON message
                message = json.loads(message_data.decode("utf-8"))

            message_type = message.get("type", "unknown")

            if message_type == "publish_event":
                await self._handle_publish_event(client_id, message)
            elif message_type == "subscribe":
                await self._handle_subscription(client_id, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(client_id, message)
            elif message_type == "ping":
                await self._handle_ping(client_id)
            else:
                self.logger.warning(
                    f"Unknown message type from {client_id}: {message_type}"
                )

        except Exception as e:
            self.logger.error(f"Error processing message from {client_id}: {e}")

    def _parse_protobuf_message(self, data: bytes) -> Dict[str, Any]:
        """Parse protobuf message (placeholder)."""
        # In real implementation, this would parse the actual protobuf message
        # For now, fall back to JSON
        return json.loads(data.decode("utf-8"))

    async def _handle_publish_event(self, client_id: str, message: Dict[str, Any]):
        """Handle event publishing."""
        try:
            event_data = message.get("event", {})

            # Create event
            event = Event(
                id=event_data.get("id", str(uuid.uuid4())),
                type=EventType(event_data.get("type", "custom_event")),
                priority=EventPriority(event_data.get("priority", "normal")),
                timestamp=datetime.now(),
                source=event_data.get("source", client_id),
                target=event_data.get("target"),
                payload=event_data.get("payload", {}),
                metadata=event_data.get("metadata", {}),
                correlation_id=event_data.get("correlation_id"),
            )

            # Queue event for processing
            await self.publish_event(event)

            # Send acknowledgment
            await self._send_to_client(
                client_id, {"type": "ack", "event_id": event.id, "status": "queued"}
            )

        except Exception as e:
            self.logger.error(f"Error handling publish event from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})

    async def _handle_subscription(self, client_id: str, message: Dict[str, Any]):
        """Handle subscription request."""
        try:
            sub_data = message.get("subscription", {})

            # Create event filter
            filter_data = sub_data.get("filter", {})
            event_filter = EventFilter(
                event_types=[EventType(t) for t in filter_data.get("event_types", [])],
                sources=filter_data.get("sources"),
                targets=filter_data.get("targets"),
                priorities=[
                    EventPriority(p) for p in filter_data.get("priorities", [])
                ],
                pattern=filter_data.get("pattern"),
            )

            # Create subscription
            subscription = Subscription(
                id=sub_data.get("id", str(uuid.uuid4())),
                subscriber_id=client_id,
                subscription_type=SubscriptionType(sub_data.get("type", "filtered")),
                filter=event_filter,
                endpoint=client_id,  # Use client_id as endpoint for direct delivery
            )

            self.subscriptions[subscription.id] = subscription
            self.logger.info(
                f"Created subscription {subscription.id} for client {client_id}"
            )

            # Send acknowledgment
            await self._send_to_client(
                client_id,
                {"type": "subscription_created", "subscription_id": subscription.id},
            )

        except Exception as e:
            self.logger.error(f"Error handling subscription from {client_id}: {e}")
            await self._send_to_client(client_id, {"type": "error", "message": str(e)})

    async def _handle_unsubscription(self, client_id: str, message: Dict[str, Any]):
        """Handle unsubscription request."""
        try:
            subscription_id = message.get("subscription_id")

            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.subscriber_id == client_id:
                    del self.subscriptions[subscription_id]
                    self.logger.info(
                        f"Removed subscription {subscription_id} for client {client_id}"
                    )

                    await self._send_to_client(
                        client_id,
                        {"type": "unsubscribed", "subscription_id": subscription_id},
                    )
                else:
                    await self._send_to_client(
                        client_id,
                        {
                            "type": "error",
                            "message": "Subscription not owned by client",
                        },
                    )
            else:
                await self._send_to_client(
                    client_id, {"type": "error", "message": "Subscription not found"}
                )

        except Exception as e:
            self.logger.error(f"Error handling unsubscription from {client_id}: {e}")

    async def _handle_ping(self, client_id: str):
        """Handle ping request."""
        await self._send_to_client(
            client_id, {"type": "pong", "timestamp": datetime.now().isoformat()}
        )

    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        if client_id not in self.active_connections:
            return

        try:
            connection = self.active_connections[client_id]
            writer = connection["writer"]

            # Serialize message
            if self.protobuf_enabled:
                message_data = self._serialize_protobuf_message(message)
            else:
                message_data = json.dumps(message).encode("utf-8")

            # Send length prefix + message
            length_prefix = len(message_data).to_bytes(4, byteorder="big")
            writer.write(length_prefix + message_data)
            await writer.drain()

        except Exception as e:
            self.logger.error(f"Error sending message to client {client_id}: {e}")
            # Remove client connection on error
            self.active_connections.pop(client_id, None)

    def _serialize_protobuf_message(self, message: Dict[str, Any]) -> bytes:
        """Serialize message to protobuf (placeholder)."""
        # In real implementation, this would serialize to actual protobuf
        # For now, fall back to JSON
        return json.dumps(message).encode("utf-8")

    async def _process_events(self):
        """Process events from the queue."""
        self.logger.info("Event processor started")

        try:
            while self.running:
                try:
                    # Get next event from queue
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                    # Process event
                    start_time = time.time()
                    await self._route_event(event)
                    processing_time = time.time() - start_time

                    # Update stats
                    self._update_stats(event, processing_time)

                    # Add to history
                    self._add_to_history(event)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing event: {e}")

        except asyncio.CancelledError:
            self.logger.info("Event processor cancelled")

    async def _route_event(self, event: Event):
        """Route event to subscribers."""
        matching_subscriptions = self._find_matching_subscriptions(event)

        if not matching_subscriptions:
            self.logger.debug(f"No subscribers for event {event.id}")
            return

        # Deliver event to all matching subscribers
        delivery_tasks = []
        for subscription in matching_subscriptions:
            task = asyncio.create_task(self._deliver_event(event, subscription))
            delivery_tasks.append(task)

        # Wait for all deliveries
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)

        # Count failed deliveries
        failed_count = sum(1 for result in results if isinstance(result, Exception))
        self.stats.failed_deliveries += failed_count

        if failed_count > 0:
            self.logger.warning(
                f"Failed to deliver event {event.id} to {failed_count} subscribers"
            )

    def _find_matching_subscriptions(self, event: Event) -> List[Subscription]:
        """Find subscriptions that match the event."""
        matching = []

        for subscription in self.subscriptions.values():
            if not subscription.active:
                continue

            if self._event_matches_filter(event, subscription.filter):
                matching.append(subscription)

        return matching

    def _event_matches_filter(
        self, event: Event, event_filter: Optional[EventFilter]
    ) -> bool:
        """Check if event matches filter criteria."""
        if not event_filter:
            return True

        # Check event types
        if event_filter.event_types and event.type not in event_filter.event_types:
            return False

        # Check sources
        if event_filter.sources and event.source not in event_filter.sources:
            return False

        # Check targets
        if (
            event_filter.targets
            and event.target
            and event.target not in event_filter.targets
        ):
            return False

        # Check priorities
        if event_filter.priorities and event.priority not in event_filter.priorities:
            return False

        # Check pattern (simple string matching)
        if event_filter.pattern:
            import re

            pattern_text = json.dumps(event.payload)
            if not re.search(event_filter.pattern, pattern_text, re.IGNORECASE):
                return False

        # Check custom filter
        if event_filter.custom_filter:
            try:
                if not event_filter.custom_filter(event):
                    return False
            except Exception as e:
                self.logger.error(f"Error in custom filter: {e}")
                return False

        return True

    async def _deliver_event(self, event: Event, subscription: Subscription):
        """Deliver event to subscriber."""
        try:
            if subscription.callback:
                # Direct callback
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, subscription.callback, event
                )
            elif subscription.endpoint:
                # Send to client endpoint
                await self._send_to_client(
                    subscription.endpoint,
                    {
                        "type": "event",
                        "subscription_id": subscription.id,
                        "event": event.to_dict(),
                    },
                )

        except Exception as e:
            self.logger.error(
                f"Error delivering event {event.id} to subscription {subscription.id}: {e}"
            )
            raise

    def _update_stats(self, event: Event, processing_time: float):
        """Update event processing statistics."""
        self.stats.total_events += 1

        # Update by type
        event_type = event.type.value
        self.stats.events_by_type[event_type] = (
            self.stats.events_by_type.get(event_type, 0) + 1
        )

        # Update by priority
        priority = event.priority.value
        self.stats.events_by_priority[priority] = (
            self.stats.events_by_priority.get(priority, 0) + 1
        )

        # Update by source
        source = event.source
        self.stats.events_by_source[source] = (
            self.stats.events_by_source.get(source, 0) + 1
        )

        # Update average processing time
        current_avg = self.stats.average_processing_time
        total = self.stats.total_events
        self.stats.average_processing_time = (
            current_avg * (total - 1) + processing_time
        ) / total

        # Update active subscriptions count
        self.stats.active_subscriptions = len(
            [s for s in self.subscriptions.values() if s.active]
        )

    def _add_to_history(self, event: Event):
        """Add event to history."""
        self.event_history.append(event)

        # Limit history size
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size :]

    async def _cleanup_loop(self):
        """Cleanup loop for expired subscriptions and connections."""
        self.logger.info("Cleanup loop started")

        try:
            while self.running:
                await asyncio.sleep(60)  # Run every minute

                # Clean up inactive subscriptions
                current_time = datetime.now()
                expired_subscriptions = []

                for sub_id, subscription in self.subscriptions.items():
                    # Remove subscriptions for disconnected clients
                    if (
                        subscription.endpoint
                        and subscription.endpoint not in self.active_connections
                    ):
                        expired_subscriptions.append(sub_id)

                for sub_id in expired_subscriptions:
                    del self.subscriptions[sub_id]
                    self.logger.info(f"Cleaned up expired subscription: {sub_id}")

                # Clean up stale connections
                stale_connections = []
                for client_id, connection in self.active_connections.items():
                    last_activity = connection["last_activity"]
                    if current_time - last_activity > timedelta(minutes=30):
                        stale_connections.append(client_id)

                for client_id in stale_connections:
                    connection = self.active_connections.pop(client_id)
                    try:
                        writer = connection["writer"]
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
                    self.logger.info(f"Cleaned up stale connection: {client_id}")

        except asyncio.CancelledError:
            self.logger.info("Cleanup loop cancelled")

    # Public API methods
    async def publish_event(self, event: Event):
        """Publish an event to the router."""
        await self.event_queue.put(event)
        self.logger.debug(f"Event {event.id} queued for processing")

    def subscribe(
        self,
        subscriber_id: str,
        event_filter: Optional[EventFilter] = None,
        callback: Optional[Callable[[Event], None]] = None,
    ) -> str:
        """Subscribe to events with optional filtering."""
        subscription = Subscription(
            id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            subscription_type=SubscriptionType.FILTERED,
            filter=event_filter,
            callback=callback,
        )

        self.subscriptions[subscription.id] = subscription
        self.logger.info(f"Created subscription {subscription.id} for {subscriber_id}")

        return subscription.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            self.logger.info(f"Removed subscription {subscription_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get event processing statistics."""
        return asdict(self.stats)

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history."""
        recent_events = self.event_history[-limit:] if limit > 0 else self.event_history
        return [event.to_dict() for event in recent_events]

    def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Get list of active subscriptions."""
        active_subs = []
        for subscription in self.subscriptions.values():
            if subscription.active:
                sub_info = {
                    "id": subscription.id,
                    "subscriber_id": subscription.subscriber_id,
                    "type": subscription.subscription_type.value,
                    "created_at": subscription.created_at.isoformat(),
                    "has_filter": subscription.filter is not None,
                    "has_callback": subscription.callback is not None,
                }
                active_subs.append(sub_info)

        return active_subs

    def health_check(self) -> Dict[str, Any]:
        """Get service health information."""
        return {
            "status": "running" if self.running else "stopped",
            "active_connections": len(self.active_connections),
            "active_subscriptions": len(
                [s for s in self.subscriptions.values() if s.active]
            ),
            "queue_size": self.event_queue.qsize(),
            "total_events_processed": self.stats.total_events,
            "average_processing_time": self.stats.average_processing_time,
            "failed_deliveries": self.stats.failed_deliveries,
            "protobuf_enabled": self.protobuf_enabled,
            "uptime": datetime.now().isoformat() if self.running else None,
        }


class EventRouterClient:
    """Client for connecting to the event router service."""

    def __init__(self, host: str = "localhost", port: int = 9090):
        """Initialize the event router client."""
        self.host = host
        self.port = port
        self.connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.logger = logging.getLogger("event_router_client")
        self.message_handlers: Dict[str, Callable] = {}
        self.listener_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to the event router service."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.connected = True

            # Start message listener
            self.listener_task = asyncio.create_task(self._listen_for_messages())

            self.logger.info(f"Connected to event router at {self.host}:{self.port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to event router: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the event router service."""
        if not self.connected:
            return

        self.connected = False

        if self.listener_task:
            self.listener_task.cancel()

        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        self.logger.info("Disconnected from event router")

    async def publish_event(self, event: Event) -> bool:
        """Publish an event."""
        if not self.connected:
            return False

        try:
            message = {"type": "publish_event", "event": event.to_dict()}

            await self._send_message(message)
            return True

        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")
            return False

    async def subscribe(
        self,
        event_filter: Optional[EventFilter] = None,
        subscription_type: SubscriptionType = SubscriptionType.FILTERED,
    ) -> Optional[str]:
        """Subscribe to events."""
        if not self.connected:
            return None

        try:
            filter_dict = {}
            if event_filter:
                if event_filter.event_types:
                    filter_dict["event_types"] = [
                        t.value for t in event_filter.event_types
                    ]
                if event_filter.sources:
                    filter_dict["sources"] = event_filter.sources
                if event_filter.targets:
                    filter_dict["targets"] = event_filter.targets
                if event_filter.priorities:
                    filter_dict["priorities"] = [
                        p.value for p in event_filter.priorities
                    ]
                if event_filter.pattern:
                    filter_dict["pattern"] = event_filter.pattern

            message = {
                "type": "subscribe",
                "subscription": {
                    "type": subscription_type.value,
                    "filter": filter_dict,
                },
            }

            await self._send_message(message)
            # Would need to wait for subscription_created response to get ID
            return "pending"  # Placeholder

        except Exception as e:
            self.logger.error(f"Failed to subscribe: {e}")
            return None

    async def _send_message(self, message: Dict[str, Any]):
        """Send message to server."""
        if not self.writer:
            raise Exception("Not connected")

        message_data = json.dumps(message).encode("utf-8")
        length_prefix = len(message_data).to_bytes(4, byteorder="big")

        self.writer.write(length_prefix + message_data)
        await self.writer.drain()

    async def _listen_for_messages(self):
        """Listen for messages from server."""
        try:
            while self.connected and self.reader:
                # Read message length
                length_data = await self.reader.read(4)
                if not length_data:
                    break

                message_length = int.from_bytes(length_data, byteorder="big")

                # Read message data
                message_data = await self.reader.read(message_length)
                if not message_data:
                    break

                # Parse and handle message
                message = json.loads(message_data.decode("utf-8"))
                await self._handle_message(message)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error listening for messages: {e}")
            self.connected = False

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from server."""
        message_type = message.get("type", "unknown")

        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](message)
            except Exception as e:
                self.logger.error(f"Error handling message type {message_type}: {e}")
        else:
            self.logger.debug(f"Unhandled message type: {message_type}")

    def set_message_handler(self, message_type: str, handler: Callable):
        """Set handler for specific message type."""
        self.message_handlers[message_type] = handler


# Utility functions
def create_event(
    event_type: EventType,
    source: str,
    payload: Dict[str, Any],
    priority: EventPriority = EventPriority.NORMAL,
    target: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Event:
    """Create a new event."""
    return Event(
        id=str(uuid.uuid4()),
        type=event_type,
        priority=priority,
        timestamp=datetime.now(),
        source=source,
        target=target,
        payload=payload,
        metadata={},
        correlation_id=correlation_id,
    )


async def main():
    """Main function for testing the event router service."""
    # Start the service
    service = EventRouterService()

    try:
        await service.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

            # Print stats every 30 seconds
            if int(time.time()) % 30 == 0:
                health = service.health_check()
                print(f"Service health: {health}")

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
