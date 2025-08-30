"""
Shared interfaces, protocols, and contracts for Gadugi Enhanced Separation architecture.
Provides type-safe contracts for inter-component communication and dependency injection.
"""

from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Type variables for generic interfaces
T = TypeVar("T")
ConfigType = TypeVar("ConfigType")
ResultType = TypeVar("ResultType")


# ============================================================================
# Core Abstract Interfaces
# ============================================================================


class AgentInterface(ABC):
    """
    Core interface for all agents in the Gadugi system.
    Provides contract for agent execution and lifecycle management.
    """

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with given context.

        Args:
            context: Execution context containing input data and configuration

        Returns:
            Dictionary containing execution results and status
        """
        pass

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize agent with configuration (optional override).

        Args:
            config: Agent configuration parameters
        """
        pass

    def cleanup(self) -> None:
        """
        Cleanup resources (optional override).
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status (optional override).

        Returns:
            Dictionary containing agent status information
        """
        return {"status": "ready", "agent": self.__class__.__name__}


class StateManagerInterface(ABC):
    """
    Interface for state management operations.
    Handles persistent state storage and retrieval across workflow phases.
    """

    @abstractmethod
    def save_state(self, state_id: str, data: Dict[str, Any]) -> bool:
        """
        Save state data with given identifier.

        Args:
            state_id: Unique identifier for the state
            data: State data to save

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """
        Load state data by identifier.

        Args:
            state_id: Unique identifier for the state

        Returns:
            State data if found, None otherwise
        """
        pass

    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """
        Delete state data by identifier.

        Args:
            state_id: Unique identifier for the state

        Returns:
            True if successful, False otherwise
        """
        pass

    def list_states(self) -> List[str]:
        """
        List all available state identifiers (optional override).

        Returns:
            List of state identifiers
        """
        return []

    def backup_state(self, state_id: str, backup_id: str) -> bool:
        """
        Create backup of state data (optional override).

        Args:
            state_id: Original state identifier
            backup_id: Backup identifier

        Returns:
            True if successful, False otherwise
        """
        state_data = self.load_state(state_id)
        if state_data:
            return self.save_state(backup_id, state_data)
        return False


class GitHubOperationsInterface(ABC):
    """
    Interface for GitHub operations.
    Handles issue creation, PR management, and repository interactions.
    """

    @abstractmethod
    def create_issue(self, title: str, body: str, **kwargs) -> Dict[str, Any]:
        """
        Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body/description
            **kwargs: Additional issue parameters (labels, assignees, etc.)

        Returns:
            Dictionary containing issue creation result
        """
        pass

    @abstractmethod
    def create_pr(
        self, title: str, body: str, base: str, head: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Create a GitHub pull request.

        Args:
            title: PR title
            body: PR body/description
            base: Base branch
            head: Head branch
            **kwargs: Additional PR parameters

        Returns:
            Dictionary containing PR creation result
        """
        pass

    def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Get issue details by number (optional override).

        Args:
            issue_number: Issue number

        Returns:
            Issue data if found, None otherwise
        """
        return None

    def get_pr(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get PR details by number (optional override).

        Args:
            pr_number: PR number

        Returns:
            PR data if found, None otherwise
        """
        return None

    def close_issue(self, issue_number: int) -> bool:
        """
        Close an issue (optional override).

        Args:
            issue_number: Issue number to close

        Returns:
            True if successful, False otherwise
        """
        return False

    def merge_pr(self, pr_number: int, merge_method: str = "merge") -> bool:
        """
        Merge a pull request (optional override).

        Args:
            pr_number: PR number to merge
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            True if successful, False otherwise
        """
        return False


class TaskTrackerInterface(ABC):
    """
    Interface for task tracking and management.
    Handles task lifecycle and TodoWrite integration.
    """

    @abstractmethod
    def create_task(
        self, content: str, priority: str = "medium", **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            content: Task content/description
            priority: Task priority (low, medium, high, critical)
            **kwargs: Additional task parameters

        Returns:
            Dictionary containing task creation result
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status (pending, in_progress, completed, etc.)

        Returns:
            Dictionary containing update result
        """
        pass

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task details by ID (optional override).

        Args:
            task_id: Task identifier

        Returns:
            Task data if found, None otherwise
        """
        return None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List tasks, optionally filtered by status (optional override).

        Args:
            status: Optional status filter

        Returns:
            List of task data
        """
        return []

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task (optional override).

        Args:
            task_id: Task identifier

        Returns:
            True if successful, False otherwise
        """
        return False


class ErrorHandlerInterface(ABC):
    """
    Interface for error handling and recovery.
    Provides consistent error handling across components.
    """

    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Handle an error with optional recovery.

        Args:
            error: The exception that occurred
            context: Context information about the error

        Returns:
            Recovery result or re-raises if no recovery possible
        """
        pass

    def register_recovery_strategy(self, error_type: type, strategy_func) -> None:
        """
        Register error recovery strategy (optional override).

        Args:
            error_type: Exception type to handle
            strategy_func: Recovery function
        """
        pass

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error handling statistics (optional override).

        Returns:
            Dictionary containing error statistics
        """
        return {"total_errors": 0, "recovery_success_rate": 0.0}


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class AgentConfig:
    """Configuration data for agents."""

    agent_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    timeout_seconds: int = 300
    max_retries: int = 3
    config_data: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "ValidationResult":
        """Validate agent configuration."""
        errors = []

        if not self.agent_id or not self.agent_id.strip():
            errors.append("Agent ID is required")

        if not self.name or not self.name.strip():
            errors.append("Agent name is required")

        if self.timeout_seconds <= 0:
            errors.append("Timeout must be positive")

        if self.max_retries < 0:
            errors.append("Max retries cannot be negative")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class WorkflowPhase:
    """Represents a workflow phase."""

    name: str
    description: str
    order: int = 0
    timeout_minutes: int = 60
    dependencies: List[str] = field(default_factory=list)
    tasks: List["TaskData"] = field(default_factory=list)

    def validate(self) -> "ValidationResult":
        """Validate workflow phase."""
        errors = []

        if not self.name or not self.name.strip():
            errors.append("Phase name is required")

        if self.timeout_minutes <= 0:
            errors.append("Timeout must be positive")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class TaskData:
    """Task data model."""

    id: str
    content: str
    status: str = "pending"
    priority: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def to_todowrite_format(self) -> Dict[str, Any]:
        """Convert to TodoWrite format."""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
        }

    def validate(self) -> "ValidationResult":
        """Validate task data."""
        errors = []

        if not self.id or not self.id.strip():
            errors.append("Task ID is required")

        if not self.content or not self.content.strip():
            errors.append("Task content is required")

        valid_statuses = ["pending", "in_progress", "completed", "blocked", "cancelled"]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status: {self.status}")

        valid_priorities = ["low", "medium", "high", "critical"]
        if self.priority not in valid_priorities:
            errors.append(f"Invalid priority: {self.priority}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class StateData:
    """State data model."""

    state_id: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "ValidationResult":
        """Validate state data."""
        errors = []

        if not self.state_id or not self.state_id.strip():
            errors.append("State ID is required")

        if self.data is None:
            errors.append("State data cannot be None")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class GitHubIssue:
    """GitHub issue data model."""

    number: int
    title: str
    body: str = ""
    state: str = "open"
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    def validate(self) -> "ValidationResult":
        """Validate GitHub issue data."""
        errors = []

        if self.number <= 0:
            errors.append("Issue number must be positive")

        if not self.title or not self.title.strip():
            errors.append("Issue title is required")

        valid_states = ["open", "closed"]
        if self.state not in valid_states:
            errors.append(f"Invalid issue state: {self.state}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class GitHubPR:
    """GitHub PR data model."""

    number: int
    title: str
    body: str = ""
    state: str = "open"
    base: str = "main"
    head: str = ""
    draft: bool = False
    mergeable: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None

    def validate(self) -> "ValidationResult":
        """Validate GitHub PR data."""
        errors = []

        if self.number <= 0:
            errors.append("PR number must be positive")

        if not self.title or not self.title.strip():
            errors.append("PR title is required")

        if not self.head or not self.head.strip():
            errors.append("Head branch is required")

        valid_states = ["open", "closed", "merged"]
        if self.state not in valid_states:
            errors.append(f"Invalid PR state: {self.state}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class ErrorContext:
    """Error context information."""

    operation: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    severity: str = "medium"

    def validate(self) -> "ValidationResult":
        """Validate error context."""
        errors = []

        if not self.operation or not self.operation.strip():
            errors.append("Operation is required")

        valid_severities = ["low", "medium", "high", "critical"]
        if self.severity not in valid_severities:
            errors.append(f"Invalid severity: {self.severity}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


# ============================================================================
# Result Types
# ============================================================================


@dataclass
class OperationResult(Generic[T]):
    """Generic operation result."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls, data: T, metadata: Optional[Dict[str, Any]] = None
    ) -> "OperationResult[T]":
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def error_result(
        cls,
        error: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "OperationResult[T]":
        """Create error result."""
        return cls(
            success=False, error=error, error_code=error_code, metadata=metadata or {}
        )


@dataclass
class ValidationResult:
    """Validation result."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add validation warning."""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


# ============================================================================
# Protocols for Dependency Injection
# ============================================================================


class TodoWriteProvider(Protocol):
    """Protocol for TodoWrite functionality."""

    def submit_task_list(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit task list to TodoWrite."""
        ...

    def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """Update single task status."""
        ...


class LoggerProvider(Protocol):
    """Protocol for logging functionality."""

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        ...

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...


class FileSystemProvider(Protocol):
    """Protocol for file system operations."""

    def read_file(self, path: str) -> str:
        """Read file contents."""
        ...

    def write_file(self, path: str, content: str) -> bool:
        """Write file contents."""
        ...

    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        ...

    def create_directory(self, path: str) -> bool:
        """Create directory."""
        ...


class GitProvider(Protocol):
    """Protocol for Git operations."""

    def create_branch(self, branch_name: str) -> bool:
        """Create Git branch."""
        ...

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout Git branch."""
        ...

    def commit_changes(self, message: str) -> bool:
        """Commit changes."""
        ...

    def push_branch(self, branch_name: str) -> bool:
        """Push branch to remote."""
        ...


# ============================================================================
# Configuration Schemas
# ============================================================================


class AgentConfigSchema:
    """Schema for agent configuration validation."""

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate agent configuration."""
        result = ValidationResult(is_valid=True)

        # Required fields
        required_fields = ["agent_id", "name"]
        for field in required_fields:
            if field not in config or not config[field]:
                result.add_error(f"Required field '{field}' is missing or empty")

        # Version validation
        if "version" in config:
            version = config["version"]
            if not isinstance(version, str) or not version.strip():
                result.add_error("Version must be a non-empty string")

        # Timeout validation
        if "timeout_seconds" in config:
            timeout = config["timeout_seconds"]
            if not isinstance(timeout, int) or timeout <= 0:
                result.add_error("Timeout must be a positive integer")

        # Max retries validation
        if "max_retries" in config:
            retries = config["max_retries"]
            if not isinstance(retries, int) or retries < 0:
                result.add_error("Max retries must be a non-negative integer")

        return result


class WorkflowConfigSchema:
    """Schema for workflow configuration validation."""

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate workflow configuration."""
        result = ValidationResult(is_valid=True)

        # Required fields
        if "workflow_id" not in config or not config["workflow_id"]:
            result.add_error("Required field 'workflow_id' is missing or empty")

        # Phases validation
        if "phases" not in config:
            result.add_error("Required field 'phases' is missing")
        else:
            phases = config["phases"]
            if not isinstance(phases, list):
                result.add_error("Phases must be a list")
            elif len(phases) == 0:
                result.add_error("At least one phase must be defined")
            else:
                # Validate each phase
                for i, phase in enumerate(phases):
                    if not isinstance(phase, dict):
                        result.add_error(f"Phase {i} must be a dictionary")
                        continue

                    if "name" not in phase or not phase["name"]:
                        result.add_error(f"Phase {i} missing required 'name' field")

                    if "description" not in phase:
                        result.add_warning(f"Phase {i} missing 'description' field")

        # Timeout validation
        if "timeout_minutes" in config:
            timeout = config["timeout_minutes"]
            if not isinstance(timeout, int) or timeout <= 0:
                result.add_error("Timeout must be a positive integer")

        return result


class TaskConfigSchema:
    """Schema for task configuration validation."""

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate task configuration."""
        result = ValidationResult(is_valid=True)

        # Required fields
        required_fields = ["id", "content"]
        for field in required_fields:
            if field not in config or not config[field]:
                result.add_error(f"Required field '{field}' is missing or empty")

        # Status validation
        if "status" in config:
            valid_statuses = [
                "pending",
                "in_progress",
                "completed",
                "blocked",
                "cancelled",
            ]
            if config["status"] not in valid_statuses:
                result.add_error(f"Invalid status: {config['status']}")

        # Priority validation
        if "priority" in config:
            valid_priorities = ["low", "medium", "high", "critical"]
            if config["priority"] not in valid_priorities:
                result.add_error(f"Invalid priority: {config['priority']}")

        return result


# ============================================================================
# Factory Interfaces
# ============================================================================


class ComponentFactory(ABC):
    """Abstract factory for creating system components."""

    @abstractmethod
    def create_component(self, component_type: str, config: Dict[str, Any]) -> Any:
        """
        Create a component of specified type.

        Args:
            component_type: Type of component to create
            config: Component configuration

        Returns:
            Created component instance
        """
        pass

    def get_supported_types(self) -> List[str]:
        """
        Get list of supported component types (optional override).

        Returns:
            List of supported component type names
        """
        return []

    def validate_config(
        self, component_type: str, config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate component configuration (optional override).

        Args:
            component_type: Type of component
            config: Configuration to validate

        Returns:
            Validation result
        """
        return ValidationResult(is_valid=True)


class AgentFactory(ABC):
    """Abstract factory for creating agents."""

    @abstractmethod
    def create_agent(self, agent_type: str, config: AgentConfig) -> AgentInterface:
        """
        Create an agent of specified type.

        Args:
            agent_type: Type of agent to create
            config: Agent configuration

        Returns:
            Created agent instance
        """
        pass

    def get_supported_agent_types(self) -> List[str]:
        """
        Get list of supported agent types (optional override).

        Returns:
            List of supported agent type names
        """
        return []

    def validate_agent_config(
        self, agent_type: str, config: AgentConfig
    ) -> ValidationResult:
        """
        Validate agent configuration (optional override).

        Args:
            agent_type: Type of agent
            config: Configuration to validate

        Returns:
            Validation result
        """
        return config.validate()


# ============================================================================
# Service Locator Interface
# ============================================================================


class ServiceLocator(ABC):
    """Service locator for dependency injection."""

    @abstractmethod
    def get_service(self, service_type: type) -> Any:
        """
        Get service instance by type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance
        """
        pass

    @abstractmethod
    def register_service(self, service_type: type, instance: Any) -> None:
        """
        Register service instance.

        Args:
            service_type: Type of service
            instance: Service instance
        """
        pass

    def has_service(self, service_type: type) -> bool:
        """
        Check if service is registered (optional override).

        Args:
            service_type: Type of service

        Returns:
            True if service is registered
        """
        try:
            self.get_service(service_type)
            return True
        except Exception:
            return False

    def unregister_service(self, service_type: type) -> bool:
        """
        Unregister service (optional override).

        Args:
            service_type: Type of service to unregister

        Returns:
            True if service was unregistered
        """
        return False


# ============================================================================
# Event System Interfaces
# ============================================================================


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle an event."""
        ...


class EventBus(ABC):
    """Abstract event bus for component communication."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Event handler
        """
        pass

    @abstractmethod
    def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event
            event_data: Event data
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe from events.

        Args:
            event_type: Type of event
            handler: Event handler to remove
        """
        pass

    def get_subscribers(self, event_type: str) -> List[EventHandler]:
        """
        Get list of subscribers for event type (optional override).

        Args:
            event_type: Type of event

        Returns:
            List of event handlers
        """
        return []


# ============================================================================
# Configuration Management
# ============================================================================


class ConfigurationManager(ABC):
    """Abstract configuration manager."""

    @abstractmethod
    def get_config(self, config_key: str) -> Any:
        """
        Get configuration value.

        Args:
            config_key: Configuration key

        Returns:
            Configuration value
        """
        pass

    @abstractmethod
    def set_config(self, config_key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            config_key: Configuration key
            value: Configuration value
        """
        pass

    def has_config(self, config_key: str) -> bool:
        """
        Check if configuration key exists (optional override).

        Args:
            config_key: Configuration key

        Returns:
            True if key exists
        """
        try:
            self.get_config(config_key)
            return True
        except Exception:
            return False

    def remove_config(self, config_key: str) -> bool:
        """
        Remove configuration key (optional override).

        Args:
            config_key: Configuration key to remove

        Returns:
            True if key was removed
        """
        return False


# ============================================================================
# Utility Functions
# ============================================================================


def validate_interface_implementation(
    instance: Any, interface_class: type
) -> ValidationResult:
    """
    Validate that an instance properly implements an interface.

    Args:
        instance: Instance to validate
        interface_class: Interface class to check against

    Returns:
        Validation result
    """
    result = ValidationResult(is_valid=True)

    if not isinstance(instance, interface_class):
        result.add_error(f"Instance does not implement {interface_class.__name__}")
        return result

    # Check that all abstract methods are implemented
    if hasattr(interface_class, "__abstractmethods__"):
        for method_name in interface_class.__abstractmethods__:
            if not hasattr(instance, method_name):
                result.add_error(f"Missing required method: {method_name}")
            elif not callable(getattr(instance, method_name)):
                result.add_error(f"Method {method_name} is not callable")

    return result


def create_operation_result(
    success: bool, data: Any = None, error: Optional[str] = None
) -> OperationResult:
    """
    Helper function to create operation results.

    Args:
        success: Success status
        data: Result data
        error: Error message if failed

    Returns:
        Operation result
    """
    if success:
        return OperationResult.success_result(data)
    else:
        return OperationResult.error_result(error or "Operation failed")


# ============================================================================
# Interface Registry
# ============================================================================


class InterfaceRegistry:
    """Registry for interface implementations."""

    def __init__(self):
        self._implementations: Dict[type, List[type]] = {}

    def register_implementation(
        self, interface_class: type, implementation_class: type
    ) -> None:
        """
        Register an implementation for an interface.

        Args:
            interface_class: Interface class
            implementation_class: Implementation class
        """
        if interface_class not in self._implementations:
            self._implementations[interface_class] = []

        if implementation_class not in self._implementations[interface_class]:
            self._implementations[interface_class].append(implementation_class)
            logger.debug(
                f"Registered implementation {implementation_class.__name__} for {interface_class.__name__}"
            )

    def get_implementations(self, interface_class: type) -> List[type]:
        """
        Get all registered implementations for an interface.

        Args:
            interface_class: Interface class

        Returns:
            List of implementation classes
        """
        return self._implementations.get(interface_class, [])

    def has_implementations(self, interface_class: type) -> bool:
        """
        Check if interface has registered implementations.

        Args:
            interface_class: Interface class

        Returns:
            True if implementations exist
        """
        return len(self.get_implementations(interface_class)) > 0


# Global interface registry instance
interface_registry = InterfaceRegistry()
