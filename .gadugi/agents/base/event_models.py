"""
Event Models for Agent System
==============================

This module provides event models for agent communication and event publishing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """Types of events that can be emitted."""

    AGENT_INITIALIZED = "agent_initialized"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    KNOWLEDGE_LEARNED = "knowledge_learned"
    COLLABORATION_MESSAGE = "collaboration_message"
    MEMORY_STORED = "memory_stored"
    WHITEBOARD_UPDATED = "whiteboard_updated"
    DECISION_MADE = "decision_made"
    ISSUE_REPORTED = "issue_reported"
    AGENT_SHUTDOWN = "agent_shutdown"


class EventPriority(Enum):
    """Priority levels for events."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentEvent:
    """Base class for all agent events."""

    event_type: EventType
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInitializedEvent(AgentEvent):
    """Event emitted when an agent is initialized."""

    agent_type: str = ""
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = EventType.AGENT_INITIALIZED


@dataclass
class TaskStartedEvent(AgentEvent):
    """Event emitted when a task is started."""

    task_id: str = ""
    task_description: str = ""
    estimated_duration: Optional[int] = None

    def __post_init__(self):
        self.event_type = EventType.TASK_STARTED


@dataclass
class TaskCompletedEvent(AgentEvent):
    """Event emitted when a task is completed."""

    task_id: str = ""
    task_type: str = ""
    success: bool = False
    duration_seconds: float = 0.0
    result: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        self.event_type = (
            EventType.TASK_COMPLETED if self.success else EventType.TASK_FAILED
        )


@dataclass
class KnowledgeLearnedEvent(AgentEvent):
    """Event emitted when new knowledge is learned."""

    knowledge_type: str = ""
    content: str = ""
    confidence: float = 0.0
    source: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.KNOWLEDGE_LEARNED


@dataclass
class CollaborationMessageEvent(AgentEvent):
    """Event emitted for collaboration messages."""

    message: str = ""
    message_type: str = ""
    recipient_agents: List[str] = field(default_factory=list)
    whiteboard_id: Optional[str] = None
    decision: Optional[str] = None

    def __post_init__(self):
        self.event_type = EventType.COLLABORATION_MESSAGE
