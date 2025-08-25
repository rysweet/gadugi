#!/usr/bin/env python3
"""Core event models for Event Router V2."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import IntEnum, Enum
from typing import Any, Dict, List, Optional, Set, Callable
import json
import uuid


class EventPriority(IntEnum):
    """Event priority levels (1-10)."""
    LOWEST = 1
    LOW = 3
    NORMAL = 5
    HIGH = 7
    CRITICAL = 9
    SYSTEM = 10


class EventType(str, Enum):
    """Standard event types."""
    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_FAILED = "agent.failed"
    AGENT_COMPLETED = "agent.completed"
    
    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Workflow lifecycle
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # System events
    SYSTEM_ALERT = "system.alert"
    SYSTEM_ERROR = "system.error"
    SYSTEM_INFO = "system.info"
    
    # Custom events
    CUSTOM = "custom"


class DeliveryStatus(str, Enum):
    """Event delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class EventMetadata:
    """Event metadata for tracking and debugging."""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "created_at": self.created_at.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "tags": self.tags,
            "headers": self.headers,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EventMetadata:
        """Create from dictionary."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class Event:
    """Core event model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""  # e.g., "user.created", "order.processed"
    type: EventType = EventType.CUSTOM
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""  # Source agent/service
    target: Optional[str] = None  # Target agent/service (optional)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: EventMetadata = field(default_factory=EventMetadata)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    
    # Delivery tracking
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    delivery_attempts: int = 0
    last_delivery_attempt: Optional[datetime] = None
    delivery_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "priority": int(self.priority),
            "source": self.source,
            "target": self.target,
            "payload": self.payload,
            "metadata": self.metadata.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "delivery_status": self.delivery_status.value,
            "delivery_attempts": self.delivery_attempts,
            "last_delivery_attempt": self.last_delivery_attempt.isoformat() if self.last_delivery_attempt else None,
            "delivery_error": self.delivery_error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Create event from dictionary."""
        # Handle enums
        if "type" in data and isinstance(data["type"], str):
            try:
                data["type"] = EventType(data["type"])
            except ValueError:
                data["type"] = EventType.CUSTOM
        
        if "priority" in data:
            data["priority"] = EventPriority(int(data["priority"]))
        
        if "delivery_status" in data and isinstance(data["delivery_status"], str):
            data["delivery_status"] = DeliveryStatus(data["delivery_status"])
        
        # Handle datetime fields
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        if "last_delivery_attempt" in data and data["last_delivery_attempt"]:
            if isinstance(data["last_delivery_attempt"], str):
                data["last_delivery_attempt"] = datetime.fromisoformat(data["last_delivery_attempt"])
        
        # Handle metadata
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = EventMetadata.from_dict(data["metadata"])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> Event:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def matches_topic(self, pattern: str) -> bool:
        """Check if event topic matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        if pattern == self.topic:
            return True
        
        # Support wildcard matching (e.g., "user.*" matches "user.created")
        if "*" in pattern:
            pattern_parts = pattern.split(".")
            topic_parts = self.topic.split(".")
            
            if len(pattern_parts) != len(topic_parts):
                return False
            
            for pattern_part, topic_part in zip(pattern_parts, topic_parts):
                if pattern_part != "*" and pattern_part != topic_part:
                    return False
            return True
        
        return False


@dataclass
class Subscription:
    """Event subscription model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subscriber_id: str = ""
    topics: List[str] = field(default_factory=list)  # Topic patterns to match
    types: List[EventType] = field(default_factory=list)  # Event types to match
    priorities: List[EventPriority] = field(default_factory=list)  # Min priority
    sources: List[str] = field(default_factory=list)  # Source filters
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Delivery configuration
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: float = 30.0  # seconds
    batch_size: int = 1  # For batched delivery
    
    # Callback or endpoint
    callback: Optional[Callable[[Event], None]] = None
    endpoint: Optional[str] = None  # For HTTP/WebSocket delivery
    
    def matches(self, event: Event) -> bool:
        """Check if subscription matches event."""
        if not self.active:
            return False
        
        # Check topic patterns
        if self.topics:
            topic_match = any(event.matches_topic(pattern) for pattern in self.topics)
            if not topic_match:
                return False
        
        # Check event types
        if self.types and event.type not in self.types:
            return False
        
        # Check priorities (subscription specifies minimum priority)
        if self.priorities:
            min_priority = min(self.priorities)
            if event.priority < min_priority:
                return False
        
        # Check sources
        if self.sources and event.source not in self.sources:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "subscriber_id": self.subscriber_id,
            "topics": self.topics,
            "types": [t.value for t in self.types],
            "priorities": [int(p) for p in self.priorities],
            "sources": self.sources,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "batch_size": self.batch_size,
            "endpoint": self.endpoint,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Subscription:
        """Create from dictionary."""
        # Handle enums
        if "types" in data:
            data["types"] = [EventType(t) if isinstance(t, str) else t for t in data["types"]]
        
        if "priorities" in data:
            data["priorities"] = [EventPriority(int(p)) for p in data["priorities"]]
        
        # Handle datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        # Remove callback from dict (can't serialize functions)
        data.pop("callback", None)
        
        return cls(**data)


@dataclass
class EventBatch:
    """Batch of events for efficient delivery."""
    events: List[Event] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add(self, event: Event) -> None:
        """Add event to batch."""
        self.events.append(event)
    
    def size(self) -> int:
        """Get batch size."""
        return len(self.events)
    
    def clear(self) -> List[Event]:
        """Clear and return events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class HealthStatus:
    """Health status for event router."""
    status: str = "healthy"  # healthy, degraded, unhealthy
    uptime: float = 0.0  # seconds
    events_processed: int = 0
    events_failed: int = 0
    events_in_queue: int = 0
    active_subscriptions: int = 0
    connected_clients: int = 0
    last_event_at: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "uptime": self.uptime,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "events_in_queue": self.events_in_queue,
            "active_subscriptions": self.active_subscriptions,
            "connected_clients": self.connected_clients,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
            "errors": self.errors,
        }