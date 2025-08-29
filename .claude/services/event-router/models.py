"""
Data models for event-router service.

This module defines Pydantic models for request/response validation
and data structures used throughout the event-router service.
Includes event models for agent lifecycle events and memory system integration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import uuid4


class RequestModel(BaseModel):
    """Request model for incoming data."""

    id: Optional[str] = Field(None, description="Request ID")
    data: Dict[str, Any] = Field(..., description="Request data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator('data')
    def validate_data(cls, v):
        """Validate request data."""
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class ResponseModel(BaseModel):
    """Response model for outgoing data."""

    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Validation result model."""

    is_valid: bool = Field(..., description="Validation status")
    error: Optional[str] = Field(None, description="Validation error message")
    warnings: List[str] = Field(default_factory=list)


class StateModel(BaseModel):
    """State model for tracking."""

    id: str = Field(..., description="State ID")
    status: str = Field(..., description="Current status")
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update(self, **kwargs):
        """Update state with new data."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()


# ========== Event System Models ==========

class EventType(str, Enum):
    """Event types for agent lifecycle tracking."""
    AGENT_INITIALIZED = "agent.initialized"
    AGENT_SHUTDOWN = "agent.shutdown"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    KNOWLEDGE_LEARNED = "knowledge.learned"
    COLLABORATION_MESSAGE = "collaboration.message"
    MEMORY_STORED = "memory.stored"
    MEMORY_RECALLED = "memory.recalled"
    ERROR_OCCURRED = "error.occurred"
    SYSTEM_HEALTH_CHECK = "system.health_check"


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentEvent(BaseModel):
    """Base model for agent lifecycle events."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Event ID")
    event_type: EventType = Field(..., description="Type of event")
    agent_id: str = Field(..., description="ID of the agent that generated the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    priority: EventPriority = Field(default=EventPriority.NORMAL, description="Event priority")

    # Event data
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    # Context information
    task_id: Optional[str] = Field(None, description="Associated task ID")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    session_id: Optional[str] = Field(None, description="Session ID")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Event tags for filtering")

    # Memory integration
    stored_in_memory: bool = Field(default=False, description="Whether event is persisted")
    memory_id: Optional[str] = Field(None, description="Memory system storage ID")

    class Config:
        """Pydantic config."""
        use_enum_values = True


class AgentInitializedEvent(AgentEvent):
    """Event for agent initialization."""

    event_type: EventType = Field(default=EventType.AGENT_INITIALIZED)
    agent_type: str = Field(..., description="Type of agent (e.g., 'TaskDecomposer', 'CodeWriter')")
    version: Optional[str] = Field(None, description="Agent version")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")


class TaskStartedEvent(AgentEvent):
    """Event for task initiation."""

    event_type: EventType = Field(default=EventType.TASK_STARTED)
    task_description: str = Field(..., description="Description of the task")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")


class TaskCompletedEvent(AgentEvent):
    """Event for task completion."""

    event_type: EventType = Field(default=EventType.TASK_COMPLETED)
    result: str = Field(..., description="Task result or outcome")
    duration: Optional[int] = Field(None, description="Actual duration in minutes")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifacts")
    success_metrics: Dict[str, Any] = Field(default_factory=dict, description="Success metrics")


class KnowledgeLearnedEvent(AgentEvent):
    """Event for knowledge acquisition."""

    event_type: EventType = Field(default=EventType.KNOWLEDGE_LEARNED)
    knowledge_type: str = Field(..., description="Type of knowledge (procedure, concept, pattern)")
    content: str = Field(..., description="Knowledge content")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in knowledge")
    source: Optional[str] = Field(None, description="Knowledge source")


class CollaborationMessageEvent(AgentEvent):
    """Event for inter-agent collaboration."""

    event_type: EventType = Field(default=EventType.COLLABORATION_MESSAGE)
    recipient_id: Optional[str] = Field(None, description="Target agent ID (None for broadcast)")
    message_type: str = Field(..., description="Message type (request, response, notification)")
    content: str = Field(..., description="Message content")
    requires_response: bool = Field(default=False, description="Whether response is required")


class EventFilter(BaseModel):
    """Model for event filtering criteria."""

    event_types: Optional[List[EventType]] = Field(None, description="Filter by event types")
    agent_ids: Optional[List[str]] = Field(None, description="Filter by agent IDs")
    task_ids: Optional[List[str]] = Field(None, description="Filter by task IDs")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
    priority: Optional[EventPriority] = Field(None, description="Filter by priority")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (AND logic)")

    # Time-based filtering
    start_time: Optional[datetime] = Field(None, description="Filter events after this time")
    end_time: Optional[datetime] = Field(None, description="Filter events before this time")

    # Pagination
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum events to return")
    offset: int = Field(default=0, ge=0, description="Number of events to skip")


class EventReplayRequest(BaseModel):
    """Model for event replay requests."""

    session_id: str = Field(..., description="Session ID to replay")
    agent_id: Optional[str] = Field(None, description="Specific agent to replay (optional)")
    from_timestamp: Optional[datetime] = Field(None, description="Replay from this timestamp")
    to_timestamp: Optional[datetime] = Field(None, description="Replay until this timestamp")
    event_types: Optional[List[EventType]] = Field(None, description="Event types to replay")


class EventStorageInfo(BaseModel):
    """Information about event storage."""

    total_events: int = Field(..., description="Total events stored")
    events_by_type: Dict[str, int] = Field(default_factory=dict, description="Event count by type")
    oldest_event: Optional[datetime] = Field(None, description="Timestamp of oldest event")
    newest_event: Optional[datetime] = Field(None, description="Timestamp of newest event")
    storage_size_mb: Optional[float] = Field(None, description="Storage size in MB")


class MemoryIntegrationStatus(BaseModel):
    """Status of memory system integration."""

    connected: bool = Field(..., description="Whether memory system is connected")
    backend_type: str = Field(..., description="Type of memory backend (sqlite, neo4j)")
    last_sync: Optional[datetime] = Field(None, description="Last synchronization time")
    pending_events: int = Field(default=0, description="Events pending storage")
    failed_events: int = Field(default=0, description="Events that failed to store")
