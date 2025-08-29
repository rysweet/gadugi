"""Event Router Client SDK - Simple, powerful, production-ready."""

from __future__ import annotations

import asyncio
import functools
import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from ..core.models import Event, EventBatch, Subscription  # type: ignore
from ..transport.factory import TransportFactory  # type: ignore
from .connection import ConnectionManager  # type: ignore
from .reconnect import AutoReconnector  # type: ignore

logger = logging.getLogger(__name__)


class EventRouterClient:
    """
    Simple, developer-friendly client SDK for Event Router.

    Examples:
        # Simple usage
        client = EventRouterClient()
        await client.publish("user.created", {"id": 123, "name": "Alice"})

        # With decorator
        @client.on("user.*")
        async def handle_user_events(event):
            print(f"User event: {event}")

        # With context manager
        async with EventRouterClient() as client:
            await client.publish("test", {"data": "value"})
    """

    def __init__(
        self,
        url: str = "localhost:8080",
        transport: str = "auto",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Event Router client.

        Args:
            url: Event router URL (default: localhost:8080)
            transport: Transport type (auto, memory, websocket, redis)
            config: Optional configuration dictionary
        """
        self.url = url
        self.config = config or {}

        # Set defaults
        self.config.setdefault("transport", transport)
        self.config.setdefault("url", url)
        self.config.setdefault("reconnect", {"enabled": True, "max_attempts": 5})
        self.config.setdefault("batch", {"size": 100, "timeout": 0.1})

        # Create transport
        self.transport = TransportFactory.create(self.config)

        # Create managers
        self.connection = ConnectionManager(self.transport)
        self.reconnector = AutoReconnector(self.transport)

        # Track subscriptions
        self.subscriptions: Dict[str, Subscription] = {}
        self.handlers: Dict[str, List[Callable]] = {}

        # Batching
        self.batch = EventBatch()
        self.batch_lock = asyncio.Lock()
        self.batch_task = None

        # State
        self.connected = False
        self.running = False

    # === Context Manager Support ===

    async def __aenter__(self) -> "EventRouterClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:  # type: ignore
        """Async context manager exit."""
        await self.disconnect()

    # === Connection Management ===

    async def connect(self) -> None:
        """Connect to event router."""
        if self.connected:
            return

        await self.connection.connect()
        self.connected = True
        self.running = True

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"Connected to event router at {self.url}")

    async def disconnect(self) -> None:
        """Disconnect from event router."""
        if not self.connected:
            return

        self.running = False

        # Stop background tasks
        await self._stop_background_tasks()

        # Disconnect transport
        await self.connection.disconnect()
        self.connected = False

        logger.info("Disconnected from event router")

    async def reconnect(self) -> None:
        """Reconnect to event router."""
        await self.reconnector.reconnect()

    # === Publishing Events ===

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Publish an event.

        Args:
            event_type: Type of event (e.g., "user.created")
            payload: Event payload data
            **kwargs: Additional event fields (priority, target, etc.)

        Returns:
            Event ID

        Examples:
            # Simple
            await client.publish("user.created", {"id": 123})

            # With options
            await client.publish(
                "order.placed",
                {"order_id": 456},
                priority=8,
                target="payment_service"
            )
        """
        if not self.connected:
            await self.connect()

        # Create event
        event = Event(  # type: ignore
            type=event_type,  # type: ignore[assignment]
            payload=payload,
            source=self.config.get("client_id", "unknown"),
            **kwargs
        )

        # Send through transport
        await self.transport.send(event.to_dict())

        logger.debug(f"Published event: {event.id}")
        return event.id

    def publish_nowait(
        self,
        event_type: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> None:
        """
        Publish event without waiting (fire and forget).

        Args:
            event_type: Type of event
            payload: Event payload
            **kwargs: Additional event fields

        Examples:
            client.publish_nowait("metric.recorded", {"cpu": 75})
        """
        asyncio.create_task(
            self.publish(event_type, payload, **kwargs)
        )

    async def publish_batch(
        self,
        events: List[Union[tuple, Event]]
    ) -> List[str]:
        """
        Publish multiple events efficiently.

        Args:
            events: List of (type, payload) tuples or Event objects

        Returns:
            List of event IDs

        Examples:
            events = [
                ("user.created", {"id": 1}),
                ("user.created", {"id": 2}),
            ]
            ids = await client.publish_batch(events)
        """
        if not self.connected:
            await self.connect()

        event_ids = []

        for item in events:
            if isinstance(item, tuple):
                event_type, payload = item
                event = Event(type=event_type, payload=payload)
            else:
                event = item

            await self.transport.send(event.to_dict())
            event_ids.append(event.id)

        logger.debug(f"Published batch of {len(events)} events")
        return event_ids

    # === Subscribing to Events ===

    def on(self, *event_types: str):
        """
        Decorator for subscribing to events.

        Args:
            *event_types: Event types to subscribe to

        Examples:
            @client.on("user.created")
            async def handle_user_created(event):
                print(f"New user: {event.payload}")

            @client.on("order.*", "payment.*")
            async def handle_business_events(event):
                await process_event(event)
        """
        def decorator(func: Callable[[Event], Awaitable[None]]) -> Callable[[Event], Awaitable[None]]:
            # Register handler  # type: ignore
            for event_type in event_types:
                if event_type not in self.handlers:
                    self.handlers[event_type] = []
                self.handlers[event_type].append(func)

            # Create subscription
            asyncio.create_task(self._create_subscription(event_types, func))  # type: ignore

            return func

        return decorator

    def on_pattern(self, pattern: str):
        """
        Decorator for pattern-based event subscription.

        Args:
            pattern: Regex pattern for event types

        Examples:
            @client.on_pattern(r"user\\.(created|updated|deleted)")
            async def handle_user_lifecycle(event):
                await update_user_cache(event)
        """
        def decorator(func: Callable[[Event], Awaitable[None]]) -> Callable[[Event], Awaitable[None]]:
            # Register pattern handler
            asyncio.create_task(  # type: ignore
                self._create_pattern_subscription(pattern, func)
            )
            return func

        return decorator

    async def subscribe(
        self,
        topics: Union[str, List[str]],
        handler: Optional[Callable[[Event], Awaitable[None]]] = None,
        event_filter: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        Subscribe to events programmatically.

        Args:
            topics: Topic or list of topics to subscribe to
            handler: Event handler function
            event_filter: Optional event filter

        Returns:
            Subscription object

        Examples:
            # Simple subscription
            sub = await client.subscribe("user.*", handler=process_user)

            # With filter
            sub = await client.subscribe(
                "payment.*",
                event_filter={"payload.amount": {"$gt": 100}},
                handler=audit_large_payment
            )
        """
        if not self.connected:
            await self.connect()

        # Normalize topics
        if isinstance(topics, str):
            topics = [topics]

        # Create subscription
        subscription = Subscription(  # type: ignore
            subscriber_id=self.config.get("client_id", "unknown"),
            topics=topics,
            filter=event_filter,  # type: ignore[misc]
            handler=handler  # type: ignore[misc]
        )

        # Register subscription
        self.subscriptions[subscription.id] = subscription

        # Send subscription to router
        await self.transport.send({
            "type": "subscribe",
            "subscription": subscription.to_dict()
        })

        logger.info(f"Created subscription {subscription.id} for topics {topics}")
        return subscription

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID of subscription to cancel
        """
        if subscription_id in self.subscriptions:
            # Send unsubscribe message
            await self.transport.send({
                "type": "unsubscribe",
                "subscription_id": subscription_id
            })

            # Remove subscription
            del self.subscriptions[subscription_id]

            logger.info(f"Unsubscribed from {subscription_id}")

    # === Stream Processing ===

    async def stream(
        self,
        topics: Union[str, List[str]],
        batch_size: int = 1,
        timeout: Optional[float] = None
    ) -> Any:  # type: ignore
        """
        Stream events as async generator.

        Args:
            topics: Topics to stream
            batch_size: Number of events per batch
            timeout: Batch timeout in seconds

        Yields:
            Event or list of events (if batch_size > 1)

        Examples:
            # Stream individual events
            async for event in client.stream("sensor.*"):
                await process_sensor_data(event)

            # Stream batches
            async for batch in client.stream("logs.*", batch_size=100):
                await bulk_insert_logs(batch)
        """
        if not self.connected:
            await self.connect()

        # Create queue for streaming
        queue = asyncio.Queue()  # type: ignore

        # Create subscription with queue handler
        async def queue_handler(event: Event) -> None:  # type: ignore
            await queue.put(event)

        subscription = await self.subscribe(topics, handler=queue_handler)

        try:
            batch = []

            while True:
                try:
                    # Get event with timeout
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=timeout or 1.0
                    )

                    if batch_size == 1:
                        yield event
                    else:
                        batch.append(event)

                        if len(batch) >= batch_size:
                            yield batch
                            batch = []

                except asyncio.TimeoutError:
                    # Timeout - yield partial batch if exists
                    if batch:
                        yield batch
                        batch = []

        finally:
            # Clean up subscription
            await self.unsubscribe(subscription.id)

    # === Request-Response Pattern ===

    async def request(
        self,
        event_type: str,
        payload: Dict[str, Any],
        timeout: float = 5.0
    ) -> Event:
        """
        Make a request and wait for response.

        Args:
            event_type: Request event type
            payload: Request payload
            timeout: Response timeout in seconds

        Returns:
            Response event

        Examples:
            response = await client.request(
                "calculator.add",
                {"x": 10, "y": 20},
                timeout=5.0
            )
            print(f"Result: {response.payload['result']}")
        """
        if not self.connected:
            await self.connect()

        # Create correlation ID for request-response matching
        correlation_id = str(uuid.uuid4())

        # Create response queue
        response_queue = asyncio.Queue(maxsize=1)  # type: ignore

        # Subscribe to response
        async def response_handler(event: Event) -> None:  # type: ignore
            if event.correlation_id == correlation_id:  # type: ignore
                await response_queue.put(event)

        response_subscription = await self.subscribe(
            f"{event_type}.response",
            handler=response_handler
        )

        try:
            # Send request
            await self.publish(
                event_type,
                payload,
                correlation_id=correlation_id
            )

            # Wait for response
            response = await asyncio.wait_for(
                response_queue.get(),
                timeout=timeout
            )

            return response

        finally:
            # Clean up subscription
            await self.unsubscribe(response_subscription.id)

    def respond(self, event_type: str):
        """
        Decorator for handling requests.

        Args:
            event_type: Request event type to handle

        Examples:
            @client.respond("calculator.add")
            async def add_numbers(request):
                x = request.payload["x"]
                y = request.payload["y"]
                return {"result": x + y}
        """
        def decorator(func: Callable[[Event], Awaitable[Dict[str, Any]]]) -> Callable[[Event], Awaitable[Dict[str, Any]]]:
            @self.on(event_type)  # type: ignore
            async def handler(request: Event) -> None:  # type: ignore
                try:
                    # Call handler function
                    result = await func(request)

                    # Send response
                    await self.publish(
                        f"{event_type}.response",
                        result,
                        correlation_id=request.correlation_id  # type: ignore
                    )

                except Exception as e:
                    # Send error response
                    await self.publish(
                        f"{event_type}.error",
                        {"error": str(e)},
                        correlation_id=request.correlation_id  # type: ignore
                    )

            return func

        return decorator

    # === Background Tasks ===

    def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Start batch flush task
        if self.config["batch"]["size"] > 1:
            self.batch_task = asyncio.create_task(self._batch_flush_loop())  # type: ignore

        # Start event receive task
        asyncio.create_task(self._receive_loop())

    async def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        # Cancel batch task
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass

    async def _batch_flush_loop(self) -> None:
        """Periodically flush event batch."""
        timeout = self.config["batch"]["timeout"]

        while self.running:
            await asyncio.sleep(timeout)

            async with self.batch_lock:
                if self.batch.size() > 0:
                    await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Flush current batch."""
        if self.batch.size() == 0:
            return

        # Send batch
        await self.transport.send({
            "type": "batch",
            "events": [e.to_dict() for e in self.batch.events]
        })

        # Clear batch
        self.batch = EventBatch()

    async def _receive_loop(self) -> None:
        """Receive events from transport."""
        while self.running:
            try:
                # Receive message from transport
                message = await self.transport.receive()

                if message:
                    await self._handle_message(message)

            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle received message."""
        msg_type = message.get("type")

        if msg_type == "event":
            # Handle incoming event
            event = Event.from_dict(message["event"])
            await self._dispatch_event(event)

        elif msg_type == "error":
            # Handle error message
            logger.error(f"Received error: {message.get('error')}")

        elif msg_type == "ack":
            # Handle acknowledgment
            logger.debug(f"Received ack for {message.get('event_id')}")

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to handlers."""
        # Check subscriptions
        for subscription in self.subscriptions.values():
            if subscription.matches(event):
                if subscription.handler:  # type: ignore
                    asyncio.create_task(subscription.handler(event))  # type: ignore

        # Check registered handlers
        for pattern, handlers in self.handlers.items():
            if self._matches_pattern(event.type, pattern):
                for handler in handlers:
                    asyncio.create_task(handler(event))

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return event_type.startswith(prefix)
        return event_type == pattern

    async def _create_subscription(
        self,
        event_types: tuple,
        handler: Callable[[Event], Awaitable[None]]
    ) -> None:
        """Create subscription for decorator."""
        if not self.connected:
            await self.connect()

        await self.subscribe(list(event_types), handler=handler)

    async def _create_pattern_subscription(
        self,
        pattern: str,
        handler: Callable[[Event], Awaitable[None]]
    ) -> None:
        """Create pattern subscription for decorator."""
        if not self.connected:
            await self.connect()

        # Convert pattern to subscription
        await self.subscribe(
            "*",  # Subscribe to all
            handler=handler,
            event_filter={"type": {"$regex": pattern}}
        )


# Convenience function for quick usage
def create_client(**kwargs) -> EventRouterClient:
    """Create an event router client with defaults."""
    return EventRouterClient(**kwargs)
