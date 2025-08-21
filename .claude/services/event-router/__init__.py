"""Event Router Service for Gadugi v0.3.

Real-time event-driven communication system with protobuf support.
"""

from .event_router import EventRouterService, EventRouterClient
from .models import (
    Event,
    EventType,
    EventPriority,
    EventFilter,
    Subscription,
    SubscriptionType,
    EventStats,
    create_event,
)
from .dead_letter_queue import DeadLetterQueue, DeadLetterEntry

__all__ = [
    "EventRouterService",
    "EventRouterClient",
    "Event",
    "EventType",
    "EventPriority",
    "EventFilter",
    "Subscription",
    "SubscriptionType",
    "EventStats",
    "create_event",
    "DeadLetterQueue",
    "DeadLetterEntry",
]

__version__ = "0.3.0"