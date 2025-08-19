from typing import Any, Dict, List, Optional

import json
import time

"""
Event data models for Gadugi Event Service

Defines the core event structures used throughout the system.
"""

from dataclasses import dataclass, field, asdict
from uuid import uuid4


@dataclass
class GitHubEvent:
    """GitHub webhook event data."""

    webhook_event: str = ""
    repository: str = ""
    number: Optional[int] = None
    action: str = ""
    actor: str = ""
    ref: str = ""
    labels: List[str] = field(default_factory=list)
    title: str = ""
    body: str = ""
    state: str = ""
    milestone: str = ""
    assignees: List[str] = field(default_factory=list)


@dataclass
class LocalEvent:
    """Local system event data."""

    event_name: str = ""
    working_directory: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    files_changed: List[str] = field(default_factory=list)


@dataclass
class AgentEvent:
    """Agent-generated event data."""

    agent_name: str = ""
    task_id: str = ""
    phase: str = ""
    status: str = ""
    message: str = ""
    context: Dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    """Base event structure."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time()))
    source: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        # Handle payload conversion
        payload = data.get("payload", {})

        if "github_event" in payload:
            github_data = payload["github_event"]
            payload["github_event"] = GitHubEvent(**github_data)

        elif "local_event" in payload:
            local_data = payload["local_event"]
            payload["local_event"] = LocalEvent(**local_data)

        elif "agent_event" in payload:
            agent_data = payload["agent_event"]
            payload["agent_event"] = AgentEvent(**agent_data)

        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=data.get("event_type", ""),
            timestamp=data.get("timestamp", int(time.time())),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
            payload=payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Event to dictionary."""
        data = asdict(self)

        # Convert payload objects to dicts
        payload = data["payload"]
        for key, value in payload.items():
            if hasattr(value, "__dict__"):
                payload[key] = asdict(value)

        return data

    def to_json(self) -> str:
        """Convert Event to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create Event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_github_event(self) -> Optional[GitHubEvent]:
        """Get GitHub event payload if present."""
        return self.payload.get("github_event")

    def get_local_event(self) -> Optional[LocalEvent]:
        """Get local event payload if present."""
        return self.payload.get("local_event")

    def get_agent_event(self) -> Optional[AgentEvent]:
        """Get agent event payload if present."""
        return self.payload.get("agent_event")

    def is_github_event(self) -> bool:
        """Check if this is a GitHub event."""
        return "github_event" in self.payload

    def is_local_event(self) -> bool:
        """Check if this is a local event."""
        return "local_event" in self.payload

    def is_agent_event(self) -> bool:
        """Check if this is an agent event."""
        return "agent_event" in self.payload


def create_github_event(
    event_type: str,
    repository: str,
    action: str = "",
    actor: str = "",
    number: Optional[int] = None,
    title: str = "",
    body: str = "",
    labels: Optional[List[str]] = None,
    **kwargs,
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
        **kwargs,
    )

    return Event(
        event_type=f"github.{event_type}.{action}"
        if action
        else f"github.{event_type}",
        source="github",
        payload={"github_event": github_event},
    )


def create_local_event(
    event_name: str,
    working_directory: str = "",
    environment: Optional[Dict[str, str]] = None,
    files_changed: Optional[List[str]] = None,
    **kwargs,
) -> Event:
    """Create a local event."""
    local_event = LocalEvent(
        event_name=event_name,
        working_directory=working_directory,
        environment=environment or {},
        files_changed=files_changed or [],
    )

    return Event(
        event_type=f"local.{event_name}",
        source="local",
        metadata=kwargs,
        payload={"local_event": local_event},
    )


def create_agent_event(
    agent_name: str,
    task_id: str = "",
    phase: str = "",
    status: str = "",
    message: str = "",
    context: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Event:
    """Create an agent event."""
    agent_event = AgentEvent(
        agent_name=agent_name,
        task_id=task_id,
        phase=phase,
        status=status,
        message=message,
        context=context or {},
    )

    return Event(
        event_type=f"agent.{agent_name}.{status}" if status else f"agent.{agent_name}",
        source="agent",
        metadata=kwargs,
        payload={"agent_event": agent_event},
    )
