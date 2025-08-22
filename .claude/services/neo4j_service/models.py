"""
Neo4j Data Models for Gadugi v0.3

Defines data models for entities stored in Neo4j.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .client import Neo4jClient

T = TypeVar("T", bound="Neo4jEntityBase")


class Neo4jEntityBase(ABC):
    """Base class for Neo4j entities."""

    def __init__(
        self,
        id: Optional[str] = None,
        created: Optional[datetime] = None,
        updated: Optional[datetime] = None,
        **kwargs: Any,
    ):
        """
        Initialize entity.

        Args:
            id: Unique identifier (auto-generated if not provided)
            created: Creation timestamp
            updated: Last update timestamp
            **kwargs: Additional entity properties
        """
        self.id = id or str(uuid.uuid4())
        self.created = created or datetime.now(timezone.utc)
        self.updated = updated

        # Store additional properties
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    @abstractmethod
    def label(self) -> str:
        """Neo4j label for this entity type."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for Neo4j storage."""
        data = {
            "id": self.id,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }

        # Add all other attributes
        for key, value in self.__dict__.items():
            if key not in ["id", "created", "updated"]:
                # Handle complex types
                if isinstance(value, (dict, list)):
                    data[key] = json.dumps(value)
                elif isinstance(value, datetime):
                    data[key] = value.isoformat()
                else:
                    data[key] = value

        return data

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """Create entity from dictionary."""
        # Parse timestamps
        created = None
        if "created" in data and data["created"]:
            created = datetime.fromisoformat(data["created"])

        updated = None
        if "updated" in data and data["updated"]:
            updated = datetime.fromisoformat(data["updated"])

        # Create instance
        kwargs = data.copy()
        kwargs["created"] = created
        kwargs["updated"] = updated

        return cls(**kwargs)

    def create(self, client: "Neo4jClient") -> Dict[str, Any]:
        """Create this entity in Neo4j."""
        data = self.to_dict()

        # Build property string for Cypher
        properties = ", ".join([f"{key}: ${key}" for key in data.keys()])

        query = f"""
        CREATE (n:{self.label} {{{properties}}})
        RETURN n
        """

        results = client.execute_write_query(query, data)
        return results[0]["n"] if results else {}

    def update(self, client: "Neo4jClient") -> bool:
        """Update this entity in Neo4j."""
        self.updated = datetime.now(timezone.utc)
        data = self.to_dict()

        # Remove id from updates
        entity_id = data.pop("id")

        return client.update_entity(self.label, entity_id, data)

    def delete(self, client: "Neo4jClient") -> bool:
        """Delete this entity from Neo4j."""
        return client.delete_entity(self.label, self.id)


class Agent(Neo4jEntityBase):
    """Represents an agent in the system."""

    @property
    def label(self) -> str:
        return "Agent"

    def __init__(
        self,
        name: str,
        type: str,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        status: str = "active",
        **kwargs: Any,
    ):
        """
        Initialize Agent.

        Args:
            name: Agent name
            type: Agent type (e.g., 'orchestrator', 'manager', 'worker')
            description: Agent description
            capabilities: List of agent capabilities
            config: Agent configuration
            status: Agent status (active, inactive, error)
            **kwargs: Additional properties
        """
        # Input validation
        if not name or not isinstance(name, str):
            raise ValueError("Agent name must be a non-empty string")
        if not type or not isinstance(type, str):
            raise ValueError("Agent type must be a non-empty string")
        if status not in ["active", "inactive", "error", "pending"]:
            raise ValueError(f"Invalid agent status: {status}")

        super().__init__(**kwargs)
        self.name = name.strip()
        self.type = type.strip()
        self.description = description
        self.capabilities = capabilities or []
        self.config = config or {}
        self.status = status


class Tool(Neo4jEntityBase):
    """Represents a tool available to agents."""

    @property
    def label(self) -> str:
        return "Tool"

    def __init__(
        self,
        name: str,
        category: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize Tool.

        Args:
            name: Tool name
            category: Tool category (e.g., 'file_ops', 'execution', 'search')
            description: Tool description
            parameters: Tool parameter schema
            version: Tool version
            **kwargs: Additional properties
        """
        # Input validation
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not category or not isinstance(category, str):
            raise ValueError("Tool category must be a non-empty string")

        super().__init__(**kwargs)
        self.name = name.strip()
        self.category = category.strip()
        self.description = description
        self.parameters = parameters or {}
        self.version = version


class Context(Neo4jEntityBase):
    """Represents context information in the system."""

    @property
    def label(self) -> str:
        return "Context"

    def __init__(
        self,
        content: str,
        source: str,
        context_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """
        Initialize Context.

        Args:
            content: Context content
            source: Source of context (agent, user, system)
            context_type: Type of context (general, error, success, etc.)
            metadata: Additional metadata
            tags: Context tags for categorization
            **kwargs: Additional properties
        """
        # Input validation
        if not content or not isinstance(content, str):
            raise ValueError("Context content must be a non-empty string")
        if not source or not isinstance(source, str):
            raise ValueError("Context source must be a non-empty string")
        if context_type not in ["general", "error", "success", "warning", "info", "debug"]:
            raise ValueError(f"Invalid context type: {context_type}")

        super().__init__(**kwargs)
        self.content = content.strip()
        self.source = source.strip()
        self.context_type = context_type
        self.metadata = metadata or {}
        self.tags = tags or []


class Workflow(Neo4jEntityBase):
    """Represents a workflow execution."""

    @property
    def label(self) -> str:
        return "Workflow"

    def __init__(
        self,
        name: str,
        status: str = "pending",
        phases: Optional[List[Dict[str, Any]]] = None,
        current_phase: Optional[int] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        Initialize Workflow.

        Args:
            name: Workflow name
            status: Workflow status (pending, running, completed, failed)
            phases: List of workflow phases
            current_phase: Current phase number
            agent_id: ID of the executing agent
            metadata: Additional workflow metadata
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)
        self.name = name
        self.status = status
        self.phases = phases or []
        self.current_phase = current_phase
        self.agent_id = agent_id
        self.metadata = metadata or {}


class Recipe(Neo4jEntityBase):
    """Represents a recipe in the system."""

    @property
    def label(self) -> str:
        return "Recipe"

    def __init__(
        self,
        name: str,
        requirements: Dict[str, Any],
        design: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        status: str = "draft",
        version: str = "1.0.0",
        author: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize Recipe.

        Args:
            name: Recipe name
            requirements: Recipe requirements
            design: Recipe design specification
            dependencies: List of dependency recipe IDs
            status: Recipe status (draft, active, deprecated)
            version: Recipe version
            author: Recipe author
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)
        self.name = name
        self.requirements = requirements
        self.design = design
        self.dependencies = dependencies or []
        self.status = status
        self.version = version
        self.author = author


class Event(Neo4jEntityBase):
    """Represents an event in the system."""

    @property
    def label(self) -> str:
        return "Event"

    def __init__(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        status: str = "pending",
        priority: int = 0,
        **kwargs: Any,
    ):
        """
        Initialize Event.

        Args:
            event_type: Type of event
            source: Event source (agent ID or system)
            data: Event data payload
            status: Event status (pending, processed, failed)
            priority: Event priority (higher numbers = higher priority)
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)
        self.event_type = event_type
        self.source = source
        self.data = data
        self.status = status
        self.priority = priority


class Task(Neo4jEntityBase):
    """Represents a task in the system."""

    @property
    def label(self) -> str:
        return "Task"

    def __init__(
        self,
        name: str,
        description: str,
        status: str = "pending",
        priority: int = 0,
        assigned_agent: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        Initialize Task.

        Args:
            name: Task name
            description: Task description
            status: Task status (pending, in_progress, completed, failed)
            priority: Task priority
            assigned_agent: ID of assigned agent
            dependencies: List of dependency task IDs
            metadata: Additional task metadata
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.status = status
        self.priority = priority
        self.assigned_agent = assigned_agent
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
