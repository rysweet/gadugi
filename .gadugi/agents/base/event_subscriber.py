"""
Event Subscription System for V0.3 Agents
==========================================

Provides event subscription and reaction capabilities for agents.
Agents can subscribe to events from other agents and react accordingly.
"""

import asyncio
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Set
import logging

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ReactionType(Enum):
    """Types of event reactions."""

    IMMEDIATE = "immediate"
    THROTTLED = "throttled"
    DEBOUNCED = "debounced"
    AGGREGATED = "aggregated"
    CHAINED = "chained"


class FilterOperator(Enum):
    """Filter operators for custom filters."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    MATCHES = "matches"  # For regex patterns


@dataclass
class CustomFilter:
    """Custom filter for event patterns."""

    field: str
    operator: FilterOperator
    value: Any


@dataclass
class AgentEvent:
    """Represents an event from an agent."""

    event_type: str
    agent_id: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EventPattern:
    """Pattern for matching events."""

    event_types: Optional[Set[str]] = None
    agent_sources: Optional[Set[str]] = None
    priorities: Optional[Set[str]] = None
    tag_patterns: Optional[List[Pattern]] = None
    custom_filters: Optional[List[CustomFilter]] = None

    def matches(self, event: AgentEvent) -> bool:
        """Check if an event matches this pattern."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check agent source
        if self.agent_sources and event.agent_id not in self.agent_sources:
            return False

        # Check priority
        if self.priorities and event.priority.value not in self.priorities:
            return False

        # Check tags
        if self.tag_patterns:
            if not any(
                any(pattern.match(tag) for tag in event.tags)
                for pattern in self.tag_patterns
            ):
                return False

        # Apply custom filters
        if self.custom_filters:
            for cf in self.custom_filters:
                field_value = self._get_nested_field(event.data, cf.field)
                if not self._evaluate_filter(field_value, cf.operator, cf.value):
                    return False

        return True

    def _get_nested_field(self, data: Dict[str, Any], field: str) -> Any:
        """Get a nested field from a dictionary."""
        parts = field.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _evaluate_filter(
        self, field_value: Any, operator: FilterOperator, value: Any
    ) -> bool:
        """Evaluate a custom filter."""
        if operator == FilterOperator.EQUALS:
            return field_value == value
        elif operator == FilterOperator.NOT_EQUALS:
            return field_value != value
        elif operator == FilterOperator.CONTAINS:
            return value in str(field_value)
        elif operator == FilterOperator.NOT_CONTAINS:
            return value not in str(field_value)
        elif operator == FilterOperator.GREATER_THAN:
            return field_value > value
        elif operator == FilterOperator.LESS_THAN:
            return field_value < value
        elif operator == FilterOperator.IN:
            return field_value in value
        elif operator == FilterOperator.NOT_IN:
            return field_value not in value
        elif operator == FilterOperator.MATCHES:
            return bool(re.match(value, str(field_value)))
        return False


@dataclass
class EventFilter:
    """Filter criteria for event subscriptions."""

    event_types: Optional[List[str]] = None
    agent_sources: Optional[List[str]] = None
    priorities: Optional[List[EventPriority]] = None
    tag_patterns: Optional[List[Pattern]] = None
    custom_filter: Optional[Callable[[Dict], bool]] = None

    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if an event matches this filter."""
        # Check event type
        if self.event_types and event.get("event_type") not in self.event_types:
            return False

        # Check agent source
        if self.agent_sources and event.get("agent_id") not in self.agent_sources:
            return False

        # Check priority
        if self.priorities:
            event_priority = EventPriority(event.get("priority", "normal"))
            if event_priority not in self.priorities:
                return False

        # Check tags
        if self.tag_patterns:
            event_tags = event.get("tags", [])
            if not any(
                any(pattern.match(tag) for tag in event_tags)
                for pattern in self.tag_patterns
            ):
                return False

        # Apply custom filter
        if self.custom_filter and not self.custom_filter(event):
            return False

        return True


@dataclass
class EventSubscription:
    """Represents an event subscription."""

    subscription_id: str
    filter: EventFilter
    handler: Callable
    is_async: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    async def handle_event(self, event: Dict[str, Any]) -> bool:
        """Handle an event with retry logic."""
        if not self.active or not self.filter.matches(event):
            return False

        retries = 0
        while retries <= self.max_retries:
            try:
                if self.is_async:
                    await self.handler(event)
                else:
                    self.handler(event)
                return True
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(
                        f"Failed to handle event after {self.max_retries} retries: {e}"
                    )
                    return False
                await asyncio.sleep(self.retry_delay * retries)

        return False


@dataclass
class ChainReaction:
    """Defines a chain reaction pattern."""

    trigger_event_type: str
    reaction_event_type: str
    transform: Optional[Callable[[Dict], Dict]] = None
    condition: Optional[Callable[[Dict], bool]] = None
    delay: float = 0.0


@dataclass
class AggregatedReaction:
    """Defines an aggregated reaction pattern."""

    required_events: List[str]
    window_seconds: float
    min_count: int
    reaction: Callable[[List[Dict]], None]
    collected_events: List[Dict] = field(default_factory=list)
    window_start: Optional[datetime] = None


class EventSubscriberMixin:
    """
    Mixin class that adds event subscription capabilities to V03Agent.
    """

    def __init__(self, *args, **kwargs):
        """Initialize event subscriber."""
        super().__init__(*args, **kwargs)

        # Subscription management
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._subscription_lock = threading.RLock()

        # Event processing
        self._event_queue: Optional[asyncio.Queue] = None
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown_event = threading.Event()

        # Reaction patterns
        self._chain_reactions: List[ChainReaction] = []
        self._aggregated_reactions: Dict[str, AggregatedReaction] = {}

        # Statistics
        self._events_received = 0
        self._events_processed = 0
        self._events_failed = 0

    async def start_event_processing(self):
        """Start the event processing loop."""
        if self._event_queue is None:
            self._event_queue = asyncio.Queue()

        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_events())
            logger.info(
                f"Started event processing for agent {getattr(self, 'agent_id', 'unknown')}"
            )

    async def stop_event_processing(self):
        """Stop the event processing loop."""
        self._shutdown_event.set()

        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"Stopped event processing for agent {getattr(self, 'agent_id', 'unknown')}"
        )

    def subscribe(
        self,
        event_types: Optional[List[str]] = None,
        handler: Optional[Callable] = None,
        filter: Optional[EventFilter] = None,
        subscription_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to events with specified criteria.

        Args:
            event_types: List of event types to subscribe to
            handler: Function to handle matching events
            filter: Custom EventFilter for complex filtering
            subscription_id: Optional ID for the subscription

        Returns:
            Subscription ID
        """
        if filter is None:
            filter = EventFilter(event_types=event_types)

        if handler is None:
            raise ValueError("Handler function is required")

        if subscription_id is None:
            subscription_id = f"sub_{datetime.now().timestamp()}_{id(handler)}"

        with self._subscription_lock:
            subscription = EventSubscription(
                subscription_id=subscription_id,
                filter=filter,
                handler=handler,
                is_async=asyncio.iscoroutinefunction(handler),
            )
            self._subscriptions[subscription_id] = subscription

        logger.debug(f"Created subscription {subscription_id} for {event_types}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if removed, False if not found
        """
        with self._subscription_lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                logger.debug(f"Removed subscription {subscription_id}")
                return True
        return False

    def event_handler(
        self,
        event_type: Optional[str] = None,
        priority: Optional[EventPriority] = None,
        agent_source: Optional[str] = None,
    ):
        """
        Decorator for registering event handlers.

        Usage:
            @agent.event_handler(event_type="task.completed")
            async def on_task_completed(event):
                print(f"Task completed: {event}")
        """

        def decorator(func):
            # Create filter based on decorator parameters
            filter = EventFilter(
                event_types=[event_type] if event_type else None,
                priorities=[priority] if priority else None,
                agent_sources=[agent_source] if agent_source else None,
            )

            # Subscribe the handler
            self.subscribe(filter=filter, handler=func)

            return func

        return decorator

    async def receive_event(self, event: Dict[str, Any]):
        """
        Receive an event for processing.

        Args:
            event: Event data to process
        """
        self._events_received += 1

        if self._event_queue is None:
            await self.start_event_processing()

        if self._event_queue is not None:
            await self._event_queue.put(event)

    async def _process_events(self):
        """Main event processing loop."""
        logger.info(
            f"Event processing loop started for {getattr(self, 'agent_id', 'unknown')}"
        )

        while not self._shutdown_event.is_set():
            try:
                # Wait for event with timeout
                if self._event_queue is not None:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                else:
                    await asyncio.sleep(1.0)
                    continue

                # Process the event
                await self._handle_event(event)

                # Check for chain reactions
                await self._check_chain_reactions(event)

                # Check for aggregated reactions
                await self._check_aggregated_reactions(event)

                self._events_processed += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                self._events_failed += 1

    async def _handle_event(self, event: Dict[str, Any]):
        """Handle a single event through all matching subscriptions."""
        tasks = []

        with self._subscription_lock:
            for subscription in self._subscriptions.values():
                if subscription.filter.matches(event):
                    task = asyncio.create_task(subscription.handle_event(event))
                    tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error handling event: {result}")

    def add_chain_reaction(
        self,
        trigger_event_type: str,
        reaction_event_type: str,
        transform: Optional[Callable[[Dict], Dict]] = None,
        condition: Optional[Callable[[Dict], bool]] = None,
        delay: float = 0.0,
    ):
        """
        Add a chain reaction pattern.

        Args:
            trigger_event_type: Event type that triggers the reaction
            reaction_event_type: Event type to emit in response
            transform: Function to transform trigger event to reaction event
            condition: Function to check if reaction should occur
            delay: Delay before emitting reaction event
        """
        reaction = ChainReaction(
            trigger_event_type=trigger_event_type,
            reaction_event_type=reaction_event_type,
            transform=transform,
            condition=condition,
            delay=delay,
        )
        self._chain_reactions.append(reaction)

    async def _check_chain_reactions(self, event: Dict[str, Any]):
        """Check and trigger chain reactions."""
        event_type = event.get("event_type")

        for reaction in self._chain_reactions:
            if reaction.trigger_event_type == event_type:
                # Check condition
                if reaction.condition and not reaction.condition(event):
                    continue

                # Apply delay
                if reaction.delay > 0:
                    await asyncio.sleep(reaction.delay)

                # Transform event
                if reaction.transform:
                    reaction_event = reaction.transform(event)
                else:
                    reaction_event = {
                        "event_type": reaction.reaction_event_type,
                        "triggered_by": event.get("id"),
                        "data": event.get("data", {}),
                    }

                # Emit reaction event
                if hasattr(self, "_emit_event"):
                    await self._emit_event(  # type: ignore[attr-defined]
                        reaction.reaction_event_type, reaction_event.get("data", {})
                    )

    def add_aggregated_reaction(
        self,
        reaction_id: str,
        required_events: List[str],
        window_seconds: float,
        min_count: int,
        reaction: Callable[[List[Dict]], None],
    ):
        """
        Add an aggregated reaction pattern.

        Args:
            reaction_id: Unique ID for this reaction
            required_events: Event types to aggregate
            window_seconds: Time window for aggregation
            min_count: Minimum events needed to trigger reaction
            reaction: Function to call with aggregated events
        """
        self._aggregated_reactions[reaction_id] = AggregatedReaction(
            required_events=required_events,
            window_seconds=window_seconds,
            min_count=min_count,
            reaction=reaction,
        )

    async def _check_aggregated_reactions(self, event: Dict[str, Any]):
        """Check and trigger aggregated reactions."""
        event_type = event.get("event_type")
        current_time = datetime.now()

        for reaction_id, reaction in self._aggregated_reactions.items():
            if event_type in reaction.required_events:
                # Initialize window if needed
                if reaction.window_start is None:
                    reaction.window_start = current_time

                # Check if window expired
                if (
                    current_time - reaction.window_start
                ).total_seconds() > reaction.window_seconds:
                    # Reset window
                    reaction.collected_events = []
                    reaction.window_start = current_time

                # Add event
                reaction.collected_events.append(event)

                # Check if we have enough events
                if len(reaction.collected_events) >= reaction.min_count:
                    # Trigger reaction
                    try:
                        if asyncio.iscoroutinefunction(reaction.reaction):
                            await reaction.reaction(reaction.collected_events)
                        else:
                            reaction.reaction(reaction.collected_events)
                    except Exception as e:
                        logger.error(f"Error in aggregated reaction {reaction_id}: {e}")

                    # Reset
                    reaction.collected_events = []
                    reaction.window_start = None

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get statistics about event subscriptions and processing."""
        return {
            "subscriptions": len(self._subscriptions),
            "chain_reactions": len(self._chain_reactions),
            "aggregated_reactions": len(self._aggregated_reactions),
            "events_received": self._events_received,
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "processing_active": self._processing_task
            and not self._processing_task.done(),
        }


# Example usage patterns
class EventSubscriberExamples:
    """Example patterns for using event subscriptions."""

    @staticmethod
    def task_completion_chain():
        """Example: Chain reaction for task completion."""
        return ChainReaction(
            trigger_event_type="task.completed",
            reaction_event_type="knowledge.learned",
            transform=lambda e: {
                "event_type": "knowledge.learned",
                "data": {
                    "task_id": e.get("task_id"),
                    "lesson": f"Task {e.get('task_id')} completed successfully",
                    "confidence": 0.8,
                },
            },
            condition=lambda e: e.get("data", {}).get("success", False),
        )

    @staticmethod
    def error_aggregation_reaction():
        """Example: Aggregate errors and trigger alert."""

        def alert_on_errors(events: List[Dict]):
            error_count = len(events)
            logger.warning(f"ALERT: {error_count} errors in the last minute!")
            # Could emit an alert event or notify administrators

        return {
            "reaction_id": "error_alert",
            "required_events": ["task.failed", "agent.error"],
            "window_seconds": 60.0,
            "min_count": 5,
            "reaction": alert_on_errors,
        }

    @staticmethod
    def collaboration_filter():
        """Example: Filter for collaboration events from specific agents."""
        return EventFilter(
            event_types=["collaboration.message"],
            agent_sources=["WorkflowManager", "orchestrator"],
            priorities=[EventPriority.HIGH, EventPriority.CRITICAL],
            custom_filter=lambda e: "urgent" in e.get("tags", []),
        )
