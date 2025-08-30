"""Event data models for the event service."""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GitHubEvent:
    """GitHub event data model."""
    webhook_event: str = ""
    repository: str = ""
    number: Optional[int] = None
    action: str = ""
    actor: str = ""
    title: str = ""
    body: str = ""
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    ref: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LocalEvent:
    """Local system event data model."""
    event_name: str = ""
    working_directory: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    files_changed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AgentEvent:
    """Agent event data model."""
    agent_name: str = ""
    task_id: str = ""
    phase: str = ""
    status: str = ""
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert TaskStatus enum to string if present
        if isinstance(self.status, TaskStatus):
            data['status'] = self.status.value
        return data


@dataclass
class Event:
    """Base event model."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        data = asdict(self)
        # Convert nested dataclass objects in payload
        for key, value in self.payload.items():
            if hasattr(value, 'to_dict'):
                data['payload'][key] = value.to_dict()
        return data
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        # Handle payload reconstruction
        payload = data.get('payload', {})
        reconstructed_payload = {}
        
        for key, value in payload.items():
            if key == 'github_event' and isinstance(value, dict):
                reconstructed_payload[key] = GitHubEvent(**value)
            elif key == 'local_event' and isinstance(value, dict):
                reconstructed_payload[key] = LocalEvent(**value)
            elif key == 'agent_event' and isinstance(value, dict):
                reconstructed_payload[key] = AgentEvent(**value)
            else:
                reconstructed_payload[key] = value
        
        return cls(
            event_id=data.get('event_id', str(uuid.uuid4())),
            event_type=data.get('event_type', ''),
            timestamp=data.get('timestamp', time.time()),
            source=data.get('source', ''),
            metadata=data.get('metadata', {}),
            payload=reconstructed_payload
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_github_event(self) -> bool:
        """Check if this is a GitHub event."""
        return 'github_event' in self.payload
    
    def is_local_event(self) -> bool:
        """Check if this is a local event."""
        return 'local_event' in self.payload
    
    def is_agent_event(self) -> bool:
        """Check if this is an agent event."""
        return 'agent_event' in self.payload
    
    def get_github_event(self) -> Optional[GitHubEvent]:
        """Get GitHub event from payload."""
        return self.payload.get('github_event')
    
    def get_local_event(self) -> Optional[LocalEvent]:
        """Get local event from payload."""
        return self.payload.get('local_event')
    
    def get_agent_event(self) -> Optional[AgentEvent]:
        """Get agent event from payload."""
        return self.payload.get('agent_event')


def create_github_event(
    event_type: str,
    repository: str,
    action: str = "",
    actor: str = "",
    number: Optional[int] = None,
    title: str = "",
    body: str = "",
    labels: Optional[List[str]] = None,
    ref: str = "",
    **metadata
) -> Event:
    """Create a GitHub event."""
    github_event = GitHubEvent(
        webhook_event=event_type,
        repository=repository,
        action=action,
        actor=actor,
        number=number,
        title=title,
        body=body,
        labels=labels or [],
        ref=ref
    )
    
    event_type_str = f"github.{event_type}"
    if action:
        event_type_str += f".{action}"
    
    return Event(
        event_type=event_type_str,
        source="github",
        payload={"github_event": github_event},
        metadata=metadata
    )


def create_local_event(
    event_name: str,
    working_directory: str = "",
    environment: Optional[Dict[str, str]] = None,
    files_changed: Optional[List[str]] = None,
    **metadata
) -> Event:
    """Create a local event."""
    local_event = LocalEvent(
        event_name=event_name,
        working_directory=working_directory,
        environment=environment or {},
        files_changed=files_changed or []
    )
    
    return Event(
        event_type=f"local.{event_name}",
        source="local",
        payload={"local_event": local_event},
        metadata=metadata
    )


def create_agent_event(
    agent_name: str,
    task_id: str = "",
    phase: str = "",
    status: Union[str, TaskStatus] = "",
    message: str = "",
    context: Optional[Dict[str, Any]] = None,
    **metadata
) -> Event:
    """Create an agent event."""
    # Convert TaskStatus enum to string if needed
    status_str = status.value if isinstance(status, TaskStatus) else str(status)
    
    agent_event = AgentEvent(
        agent_name=agent_name,
        task_id=task_id,
        phase=phase,
        status=status_str,
        message=message,
        context=context or {}
    )
    
    event_type = f"agent.{agent_name}"
    if status_str:
        event_type += f".{status_str}"
    
    return Event(
        event_type=event_type,
        source="agent",
        payload={"agent_event": agent_event},
        metadata=metadata
    )