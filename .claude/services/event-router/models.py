"""Data models for the Event Router Service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, Dict, List


class EventType(Enum):
    """Event type enumeration."""

    # Agent lifecycle events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_ERROR = "agent.error"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # System events
    SYSTEM_CONFIG_CHANGED = "system.config_changed"
    SYSTEM_RESOURCE_ALERT = "system.resource_alert"
    SYSTEM_ERROR = "system.error"
    
    # User interaction events
    USER_APPROVAL_NEEDED = "user.approval_needed"
    USER_QUESTION_ASKED = "user.question_asked"
    USER_RESPONSE_RECEIVED = "user.response_received"
    
    # Memory events
    MEMORY_CREATED = "memory.created"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_PRUNED = "memory.pruned"
    MEMORY_ACCESSED = "memory.accessed"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PHASE_CHANGED = "workflow.phase_changed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # Custom events
    CUSTOM_EVENT = "custom.event"


class EventPriority(Enum):
    """Event priority enumeration."""

    CRITICAL = "critical"  # System failures, security issues
    HIGH = "high"          # Important user interactions, errors
    NORMAL = "normal"      # Regular events, status updates
    LOW = "low"           # Debug info, non-critical updates


class SubscriptionType(Enum):
    """Subscription type enumeration."""

    ALL = "all"                    # Receive all events
    FILTERED = "filtered"          # Receive filtered events
    PATTERN = "pattern"            # Pattern-based matching
    CONDITIONAL = "conditional"    # Complex condition matching


@dataclass
class Event:
    """Event data structure."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM_EVENT
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    target: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

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
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Create event from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=EventType(data.get("type", "custom.event")),
            priority=EventPriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            source=data.get("source", ""),
            target=data.get("target"),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            correlation_id=data.get("correlation_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )

    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.metadata["last_retry"] = datetime.now().isoformat()


@dataclass
class EventFilter:
    """Event filtering configuration."""

    event_types: Optional[List[EventType]] = None
    sources: Optional[List[str]] = None
    targets: Optional[List[str]] = None
    priorities: Optional[List[EventPriority]] = None
    pattern: Optional[str] = None
    custom_filter: Optional[Callable[[Event], bool]] = None
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event types
        if self.event_types and event.type not in self.event_types:
            return False
        
        # Check sources
        if self.sources and event.source not in self.sources:
            return False
        
        # Check targets
        if self.targets and event.target and event.target not in self.targets:
            return False
        
        # Check priorities
        if self.priorities and event.priority not in self.priorities:
            return False
        
        # Check pattern (simple string matching in payload)
        if self.pattern:
            import re
            import json
            pattern_text = json.dumps(event.payload)
            if not re.search(self.pattern, pattern_text, re.IGNORECASE):
                return False
        
        # Check custom filter
        if self.custom_filter:
            try:
                if not self.custom_filter(event):
                    return False
            except Exception:
                return False
        
        return True


@dataclass
class Subscription:
    """Event subscription configuration."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subscriber_id: str = ""
    subscription_type: SubscriptionType = SubscriptionType.FILTERED
    filter: Optional[EventFilter] = None
    callback: Optional[Callable[[Event], None]] = None
    endpoint: Optional[str] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    error_count: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_failures: int = 0
    circuit_breaker_threshold: int = 5

    def record_delivery(self) -> None:
        """Record successful delivery."""
        self.last_delivery = datetime.now()
        self.delivery_count += 1
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False

    def record_error(self) -> None:
        """Record delivery error."""
        self.error_count += 1
        self.circuit_breaker_failures += 1
        
        # Open circuit breaker if threshold reached
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True

    def is_available(self) -> bool:
        """Check if subscription is available for delivery."""
        return self.active and not self.circuit_breaker_open

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker."""
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0


@dataclass
class EventStats:
    """Event processing statistics."""

    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_priority: Dict[str, int] = field(default_factory=dict)
    events_by_source: Dict[str, int] = field(default_factory=dict)
    average_processing_time: float = 0.0
    failed_deliveries: int = 0
    successful_deliveries: int = 0
    active_subscriptions: int = 0
    dead_letter_count: int = 0
    circuit_breakers_open: int = 0
    
    def update_from_event(self, event: Event, processing_time: float) -> None:
        """Update statistics from processed event."""
        self.total_events += 1
        
        # Update by type
        event_type = event.type.value
        self.events_by_type[event_type] = self.events_by_type.get(event_type, 0) + 1
        
        # Update by priority
        priority = event.priority.value
        self.events_by_priority[priority] = self.events_by_priority.get(priority, 0) + 1
        
        # Update by source
        source = event.source
        self.events_by_source[source] = self.events_by_source.get(source, 0) + 1
        
        # Update average processing time
        current_avg = self.average_processing_time
        total = self.total_events
        self.average_processing_time = (current_avg * (total - 1) + processing_time) / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return asdict(self)


def create_event(
    event_type: EventType,
    source: str,
    payload: Dict[str, Any],
    priority: EventPriority = EventPriority.NORMAL,
    target: Optional[str] = None,
    correlation_id: Optional[str] = None,
    max_retries: int = 3,
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
        metadata={
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
        },
        correlation_id=correlation_id,
        max_retries=max_retries,
    )