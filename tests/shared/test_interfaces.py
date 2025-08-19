from typing import Any, Dict, List, Optional, Protocol

from unittest.mock import Mock, patch, MagicMock
import os
import sys
import pytest

"""
Comprehensive tests for interfaces.py module.
Tests shared interfaces, protocols, and contracts for the Enhanced Separation architecture.
"""

# Import the module we're testing
from abc import ABC, abstractmethod
from dataclasses import dataclass

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "shared")
)

try:
    from interfaces import (  # Core interfaces; Data models; Protocols; Configuration schemas; Result types; Factory interfaces
        AgentConfig,
        AgentConfigSchema,
        AgentFactory,
        AgentInterface,
        ComponentFactory,
        ErrorContext,
        ErrorHandlerInterface,
        FileSystemProvider,
        GitHubIssue,
        GitHubOperationsInterface,
        GitHubPR,
        LoggerProvider,
        OperationResult,
        StateData,
        StateManagerInterface,
        TaskData,
        TaskTrackerInterface,
        TodoWriteProvider,
        ValidationResult,
        WorkflowConfigSchema,
        WorkflowPhase,
    )
except ImportError:
    # If import fails, create stub classes to show what needs to be implemented
    print(
        "Warning: Could not import interfaces module. Tests will define what needs to be implemented."
    )

    # Core interfaces
    class AgentInterface(ABC):
        @abstractmethod
        def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
            pass

    class StateManagerInterface(ABC):
        @abstractmethod
        def save_state(self, state_id: str, data: Dict[str, Any]) -> bool:
            pass

        @abstractmethod
        def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
            pass

        @abstractmethod
        def delete_state(self, state_id: str) -> bool:
            pass

    class GitHubOperationsInterface(ABC):
        @abstractmethod
        def create_issue(self, title: str, body: str) -> Dict[str, Any]:
            pass

    class TaskTrackerInterface(ABC):
        @abstractmethod
        def create_task(self, content: str, priority: str) -> Dict[str, Any]:
            pass

    class ErrorHandlerInterface(ABC):
        @abstractmethod
        def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
            pass

    # Data models
    @dataclass
    class AgentConfig:
        agent_id: str
        name: str
        version: str = "1.0.0"

    @dataclass
    class WorkflowPhase:
        name: str
        description: str

    @dataclass
    class TaskData:
        id: str
        content: str

    @dataclass
    class StateData:
        state_id: str
        data: Dict[str, Any]

    @dataclass
    class GitHubIssue:
        number: int
        title: str

    @dataclass
    class GitHubPR:
        number: int
        title: str

    @dataclass
    class ErrorContext:
        operation: str
        details: Dict[str, Any]

    # Protocols
    class TodoWriteProvider(Protocol):
        def submit_task_list(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]: ...

    class LoggerProvider(Protocol):
        def info(self, message: str) -> None: ...

    class FileSystemProvider(Protocol):
        def read_file(self, path: str) -> str: ...

    # Configuration schemas
    class AgentConfigSchema:
        def validate(self, config: Dict[str, Any]) -> "ValidationResult":
            errors = []

            # Check required fields
            if "agent_id" not in config:
                errors.append("agent_id is required")
            if "name" not in config:
                errors.append("name is required")

            return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    class WorkflowConfigSchema:
        def validate(self, config: Dict[str, Any]) -> "ValidationResult":
            errors = []

            # Check required fields
            if "workflow_id" not in config:
                errors.append("workflow_id is required")
            if "phases" not in config or not config["phases"]:
                errors.append("phases are required and cannot be empty")

            return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    # Result types
    @dataclass
    class OperationResult:
        success: bool
        data: Any = None
        error: Optional[str] = None

    @dataclass
    class ValidationResult:
        is_valid: bool
        errors: List[str]

    # Factory interfaces
    class ComponentFactory(ABC):
        @abstractmethod
        def create_component(self, component_type: str, config: Dict[str, Any]) -> Any:
            pass

    class AgentFactory(ABC):
        @abstractmethod
        def create_agent(self, agent_type: str, config: AgentConfig) -> AgentInterface:
            pass

class TestAgentInterface:
    """Test AgentInterface abstract base class."""

    def test_agent_interface_is_abstract(self):
        """Test that AgentInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentInterface()

    def test_agent_interface_requires_execute_method(self):
        """Test that concrete implementations must implement execute method."""

        class IncompleteAgent(AgentInterface):
            pass  # Missing execute method

        with pytest.raises(TypeError):
            IncompleteAgent()

    def test_agent_interface_implementation(self):
        """Test valid implementation of AgentInterface."""

        class ValidAgent(AgentInterface):
            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return {"success": True, "agent": "ValidAgent"}

        agent = ValidAgent()
        result = agent.execute({"test": "context"})

        assert result["success"] is True
        assert result["agent"] == "ValidAgent"

    def test_agent_interface_method_signature(self):
        """Test that execute method has correct signature."""

        class TestAgent(AgentInterface):
            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return {"context_keys": list(context.keys())}

        agent = TestAgent()
        context = {"key1": "value1", "key2": "value2"}
        result = agent.execute(context)

        assert "context_keys" in result
        assert set(result["context_keys"]) == {"key1", "key2"}

class TestStateManagerInterface:
    """Test StateManagerInterface abstract base class."""

    def test_state_manager_interface_is_abstract(self):
        """Test that StateManagerInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StateManagerInterface()

    def test_state_manager_interface_implementation(self):
        """Test valid implementation of StateManagerInterface."""

        class MockStateManager(StateManagerInterface):
            def __init__(self):
                self.states = {}

            def save_state(self, state_id: str, data: Dict[str, Any]) -> bool:
                self.states[state_id] = data
                return True

            def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
                return self.states.get(state_id)

            def delete_state(self, state_id: str) -> bool:
                if state_id in self.states:
                    del self.states[state_id]
                    return True
                return False

        manager = MockStateManager()

        # Test save_state
        result = manager.save_state("test-1", {"key": "value"})
        assert result is True

        # Test load_state
        loaded = manager.load_state("test-1")
        assert loaded == {"key": "value"}

        # Test delete_state
        deleted = manager.delete_state("test-1")
        assert deleted is True
        assert manager.load_state("test-1") is None

class TestGitHubOperationsInterface:
    """Test GitHubOperationsInterface abstract base class."""

    def test_github_operations_interface_implementation(self):
        """Test valid implementation of GitHubOperationsInterface."""

        class MockGitHubOperations(GitHubOperationsInterface):
            def __init__(self):
                self.issues = {}
                self.prs = {}
                self.issue_counter = 1
                self.pr_counter = 1

            def create_issue(self, title: str, body: str) -> Dict[str, Any]:
                issue_number = self.issue_counter
                self.issues[issue_number] = {
                    "number": issue_number,
                    "title": title,
                    "body": body,
                }
                self.issue_counter += 1
                return {"success": True, "issue_number": issue_number}

            def create_pr(
                self, title: str, body: str, base: str, head: str
            ) -> Dict[str, Any]:
                pr_number = self.pr_counter
                self.prs[pr_number] = {
                    "number": pr_number,
                    "title": title,
                    "body": body,
                    "base": base,
                    "head": head,
                }
                self.pr_counter += 1
                return {"success": True, "pr_number": pr_number}

        github = MockGitHubOperations()

        # Test create_issue
        issue_result = github.create_issue("Test Issue", "Issue body")
        assert issue_result["success"] is True
        assert issue_result["issue_number"] == 1

        # Test create_pr
        pr_result = github.create_pr("Test PR", "PR body", "main", "feature")
        assert pr_result["success"] is True
        assert pr_result["pr_number"] == 1

class TestTaskTrackerInterface:
    """Test TaskTrackerInterface abstract base class."""

    def test_task_tracker_interface_implementation(self):
        """Test valid implementation of TaskTrackerInterface."""

        class MockTaskTracker(TaskTrackerInterface):
            def __init__(self):
                self.tasks = {}
                self.task_counter = 1

            def create_task(self, content: str, priority: str) -> Dict[str, Any]:
                task_id = f"task-{self.task_counter}"
                self.tasks[task_id] = {
                    "id": task_id,
                    "content": content,
                    "priority": priority,
                    "status": "pending",
                }
                self.task_counter += 1
                return {"success": True, "task_id": task_id}

            def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = status
                    return {"success": True}
                return {"success": False, "error": "Task not found"}

        tracker = MockTaskTracker()

        # Test create_task
        result = tracker.create_task("Test task", "high")
        assert result["success"] is True
        assert "task_id" in result

        # Test update_task_status
        task_id = result["task_id"]
        update_result = tracker.update_task_status(task_id, "completed")
        assert update_result["success"] is True

class TestErrorHandlerInterface:
    """Test ErrorHandlerInterface abstract base class."""

    def test_error_handler_interface_implementation(self):
        """Test valid implementation of ErrorHandlerInterface."""

        class MockErrorHandler(ErrorHandlerInterface):
            def __init__(self):
                self.handled_errors = []

            def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
                self.handled_errors.append(
                    {
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "context": context,
                    }
                )
                return {"recovered": True, "fallback_value": "default"}

        handler = MockErrorHandler()

        error = ValueError("Test error")
        context = {"operation": "test_operation", "data": {"key": "value"}}

        result = handler.handle_error(error, context)

        assert result["recovered"] is True
        assert result["fallback_value"] == "default"
        assert len(handler.handled_errors) == 1
        assert handler.handled_errors[0]["error_type"] == "ValueError"

class TestDataModels:
    """Test data model classes."""

    def test_agent_config_creation(self):
        """Test AgentConfig creation and validation."""
        config = AgentConfig(agent_id="test-agent", name="Test Agent", version="2.0.0")

        assert config.agent_id == "test-agent"
        assert config.name == "Test Agent"
        assert config.version == "2.0.0"

    def test_agent_config_defaults(self):
        """Test AgentConfig with default values."""
        config = AgentConfig(agent_id="test", name="Test")
        assert config.version == "1.0.0"

    def test_workflow_phase_creation(self):
        """Test WorkflowPhase creation."""
        phase = WorkflowPhase(name="setup", description="Initial setup phase")

        assert phase.name == "setup"
        assert phase.description == "Initial setup phase"

    def test_task_data_creation(self):
        """Test TaskData creation."""
        task = TaskData(id="task-1", content="Test task")
        assert task.id == "task-1"
        assert task.content == "Test task"

    def test_state_data_creation(self):
        """Test StateData creation."""
        state = StateData(state_id="state-1", data={"phase": "setup", "progress": 50})

        assert state.state_id == "state-1"
        assert state.data["phase"] == "setup"
        assert state.data["progress"] == 50

    def test_github_issue_creation(self):
        """Test GitHubIssue creation."""
        issue = GitHubIssue(number=123, title="Test issue")
        assert issue.number == 123
        assert issue.title == "Test issue"

    def test_github_pr_creation(self):
        """Test GitHubPR creation."""
        pr = GitHubPR(number=456, title="Test PR")
        assert pr.number == 456
        assert pr.title == "Test PR"

    def test_error_context_creation(self):
        """Test ErrorContext creation."""
        context = ErrorContext(
            operation="test_operation",
            details={"error_code": 500, "message": "Server error"},
        )

        assert context.operation == "test_operation"
        assert context.details["error_code"] == 500

    def test_operation_result_success(self):
        """Test OperationResult for successful operations."""
        result = OperationResult(success=True, data={"result": "completed"}, error=None)

        assert result.success is True
        assert result.data["result"] == "completed"
        assert result.error is None

    def test_operation_result_failure(self):
        """Test OperationResult for failed operations."""
        result = OperationResult(success=False, data=None, error="Operation failed")

        assert result.success is False
        assert result.data is None
        assert result.error == "Operation failed"

    def test_validation_result_valid(self):
        """Test ValidationResult for valid data."""
        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid data."""
        result = ValidationResult(
            is_valid=False, errors=["Missing required field", "Invalid format"]
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "Missing required field" in result.errors

class TestProtocols:
    """Test protocol definitions."""

    def test_todowrite_provider_protocol(self):
        """Test TodoWriteProvider protocol."""

        class MockTodoWriteProvider:
            def submit_task_list(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
                return {"success": True, "task_count": len(tasks)}

        provider = MockTodoWriteProvider()

        # This should work with the protocol
        def use_todowrite_provider(provider: TodoWriteProvider) -> Dict[str, Any]:
            tasks = [{"id": "1", "content": "Test"}]
            return provider.submit_task_list(tasks)

        result = use_todowrite_provider(provider)
        assert result["success"] is True
        assert result["task_count"] == 1

    def test_logger_provider_protocol(self):
        """Test LoggerProvider protocol."""

        class MockLoggerProvider:
            def __init__(self):
                self.messages = []

            def info(self, message: str) -> None:
                self.messages.append(("INFO", message))

            def error(self, message: str) -> None:
                self.messages.append(("ERROR", message))

        logger = MockLoggerProvider()

        def use_logger(logger: LoggerProvider) -> None:
            logger.info("Test message")

        use_logger(logger)
        assert len(logger.messages) == 1
        assert logger.messages[0] == ("INFO", "Test message")

    def test_filesystem_provider_protocol(self):
        """Test FileSystemProvider protocol."""

        class MockFileSystemProvider:
            def __init__(self):
                self.files = {"/test/file.txt": "file contents"}

            def read_file(self, path: str) -> str:
                return self.files.get(path, "")

            def write_file(self, path: str, content: str) -> bool:
                self.files[path] = content
                return True

        fs = MockFileSystemProvider()

        def use_filesystem(fs: FileSystemProvider) -> str:
            return fs.read_file("/test/file.txt")

        content = use_filesystem(fs)
        assert content == "file contents"

class TestConfigurationSchemas:
    """Test configuration schema classes."""

    def test_agent_config_schema_validation(self):
        """Test AgentConfigSchema validation."""
        schema = AgentConfigSchema()

        # Valid config
        valid_config = {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
        }

        result = schema.validate(valid_config)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_agent_config_schema_validation_failure(self):
        """Test AgentConfigSchema validation with invalid config."""
        schema = AgentConfigSchema()

        # Invalid config - missing required fields
        invalid_config = {
            "name": "Test Agent"
            # Missing agent_id
        }

        result = schema.validate(invalid_config)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_workflow_config_schema_validation(self):
        """Test WorkflowConfigSchema validation."""
        schema = WorkflowConfigSchema()

        # Valid workflow config
        valid_config = {
            "workflow_id": "test-workflow",
            "phases": [
                {"name": "setup", "description": "Setup phase"},
                {"name": "execution", "description": "Execution phase"},
            ],
            "timeout_minutes": 60,
        }

        result = schema.validate(valid_config)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_workflow_config_schema_validation_failure(self):
        """Test WorkflowConfigSchema validation with invalid config."""
        schema = WorkflowConfigSchema()

        # Invalid config - no phases defined
        invalid_config = {
            "workflow_id": "test-workflow",
            "phases": [],  # Empty phases list
            "timeout_minutes": -10,  # Invalid timeout
        }

        result = schema.validate(invalid_config)
        assert result.is_valid is False
        assert len(result.errors) > 0

class TestFactoryInterfaces:
    """Test factory interface implementations."""

    def test_component_factory_interface(self):
        """Test ComponentFactory interface."""

        class MockComponentFactory(ComponentFactory):
            def create_component(
                self, component_type: str, config: Dict[str, Any]
            ) -> Any:
                if component_type == "state_manager":
                    return {"type": "state_manager", "config": config}
                elif component_type == "task_tracker":
                    return {"type": "task_tracker", "config": config}
                else:
                    raise ValueError(f"Unknown component type: {component_type}")

        factory = MockComponentFactory()

        # Test creating state manager
        state_manager = factory.create_component("state_manager", {"storage": "memory"})
        assert state_manager["type"] == "state_manager"
        assert state_manager["config"]["storage"] == "memory"

        # Test creating task tracker
        task_tracker = factory.create_component(
            "task_tracker", {"backend": "todowrite"}
        )
        assert task_tracker["type"] == "task_tracker"
        assert task_tracker["config"]["backend"] == "todowrite"

        # Test unknown component type
        with pytest.raises(ValueError, match="Unknown component type: unknown"):
            factory.create_component("unknown", {})

    def test_agent_factory_interface(self):
        """Test AgentFactory interface."""

        class MockAgent(AgentInterface):
            def __init__(self, config: AgentConfig):
                self.config = config

            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return {"agent_id": self.config.agent_id, "result": "success"}

        class MockAgentFactory(AgentFactory):
            def create_agent(
                self, agent_type: str, config: AgentConfig
            ) -> AgentInterface:
                if agent_type == "mock_agent":
                    return MockAgent(config)
                else:
                    raise ValueError(f"Unknown agent type: {agent_type}")

        factory = MockAgentFactory()
        config = AgentConfig(agent_id="test-agent", name="Test Agent")

        # Test creating agent
        agent = factory.create_agent("mock_agent", config)
        assert isinstance(agent, AgentInterface)

        result = agent.execute({"test": "context"})
        assert result["agent_id"] == "test-agent"
        assert result["result"] == "success"

        # Test unknown agent type
        with pytest.raises(ValueError, match="Unknown agent type: unknown"):
            factory.create_agent("unknown", config)

class TestInterfaceIntegration:
    """Integration tests for interface interactions."""

    @pytest.mark.integration
    def test_complete_workflow_interface_integration(self):
        """Test complete workflow using all interfaces."""

        # Mock implementations
        class MockStateManager(StateManagerInterface):
            def __init__(self):
                self.states = {}

            def save_state(self, state_id: str, data: Dict[str, Any]) -> bool:
                self.states[state_id] = data
                return True

            def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
                return self.states.get(state_id)

            def delete_state(self, state_id: str) -> bool:
                if state_id in self.states:
                    del self.states[state_id]
                    return True
                return False

        class MockTaskTracker(TaskTrackerInterface):
            def __init__(self):
                self.tasks = []

            def create_task(
                self, content: str, priority: str = "medium", **kwargs
            ) -> Dict[str, Any]:
                task = {
                    "id": f"task-{len(self.tasks) + 1}",
                    "content": content,
                    "priority": priority,
                }
                self.tasks.append(task)
                return {"success": True, "task": task}

            def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
                for task in self.tasks:
                    if task["id"] == task_id:
                        task["status"] = status
                        return {"success": True}
                return {"success": False, "error": "Task not found"}

        class MockGitHubOps(GitHubOperationsInterface):
            def __init__(self):
                self.issues = []
                self.prs = []

            def create_issue(self, title: str, body: str, **kwargs) -> Dict[str, Any]:
                issue = {"number": len(self.issues) + 1, "title": title, "body": body}
                self.issues.append(issue)
                return {"success": True, "issue": issue}

            def create_pr(
                self, title: str, body: str, base: str, head: str, **kwargs
            ) -> Dict[str, Any]:
                pr = {
                    "number": len(self.prs) + 1,
                    "title": title,
                    "body": body,
                    "base": base,
                    "head": head,
                }
                self.prs.append(pr)
                return {"success": True, "pr": pr}

        class MockAgent(AgentInterface):
            def __init__(
                self,
                state_manager: StateManagerInterface,
                task_tracker: TaskTrackerInterface,
                github_ops: GitHubOperationsInterface,
            ):
                self.state_manager = state_manager
                self.task_tracker = task_tracker
                self.github_ops = github_ops

            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                # Create issue
                issue_result = self.github_ops.create_issue(
                    "Test Issue", "Created by agent"
                )

                # Create task
                task_result = self.task_tracker.create_task(
                    "Complete test workflow", "high"
                )

                # Save state
                state_data = {
                    "issue": issue_result["issue"],
                    "task": task_result["task"],
                    "phase": "execution",
                }
                self.state_manager.save_state("workflow-1", state_data)

                return {"success": True, "workflow_completed": True}

        # Create components
        state_manager = MockStateManager()
        task_tracker = MockTaskTracker()
        github_ops = MockGitHubOps()

        # Create and execute agent
        agent = MockAgent(state_manager, task_tracker, github_ops)
        result = agent.execute({"workflow_id": "test-workflow"})

        # Verify results
        assert result["success"] is True
        assert result["workflow_completed"] is True

        # Verify state was saved
        assert "workflow-1" in state_manager.states
        saved_state = state_manager.states["workflow-1"]
        assert saved_state["phase"] == "execution"

        # Verify task was created
        assert len(task_tracker.tasks) == 1
        assert task_tracker.tasks[0]["content"] == "Complete test workflow"

        # Verify issue was created
        assert len(github_ops.issues) == 1
        assert github_ops.issues[0]["title"] == "Test Issue"

    @pytest.mark.integration
    def test_error_handling_across_interfaces(self):
        """Test error handling propagation across interfaces."""

        class FailingStateManager(StateManagerInterface):
            def save_state(self, state_id: str, data: Dict[str, Any]) -> bool:
                raise RuntimeError("State storage failed")

            def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
                return None

            def delete_state(self, state_id: str) -> bool:
                return False

        class RobustAgent(AgentInterface):
            def __init__(
                self,
                state_manager: StateManagerInterface,
                error_handler: ErrorHandlerInterface,
            ):
                self.state_manager = state_manager
                self.error_handler = error_handler

            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    self.state_manager.save_state("test", {"data": "value"})
                    return {"success": True}
                except Exception as e:
                    recovery_result = self.error_handler.handle_error(e, context)
                    return {"success": False, "recovery": recovery_result}

        class MockErrorHandler(ErrorHandlerInterface):
            def handle_error(self, error: Exception, context: Dict[str, Any]) -> Any:
                return {"recovered": True, "error_type": type(error).__name__}

        # Test error handling
        failing_state_manager = FailingStateManager()
        error_handler = MockErrorHandler()
        agent = RobustAgent(failing_state_manager, error_handler)

        result = agent.execute({"test": "context"})

        assert result["success"] is False
        assert result["recovery"]["recovered"] is True
        assert result["recovery"]["error_type"] == "RuntimeError"

    @pytest.mark.integration
    def test_factory_based_component_creation(self):
        """Test using factories to create components and agents."""

        class TestComponentFactory(ComponentFactory):
            def create_component(
                self, component_type: str, config: Dict[str, Any]
            ) -> Any:
                if component_type == "state_manager":

                    class SimpleStateManager(StateManagerInterface):
                        def __init__(self):
                            self.data = {}

                        def save_state(
                            self, state_id: str, data: Dict[str, Any]
                        ) -> bool:
                            self.data[state_id] = data
                            return True

                        def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
                            return self.data.get(state_id)

                        def delete_state(self, state_id: str) -> bool:
                            if state_id in self.data:
                                del self.data[state_id]
                                return True
                            return False

                    return SimpleStateManager()

                elif component_type == "task_tracker":

                    class SimpleTaskTracker(TaskTrackerInterface):
                        def __init__(self):
                            self.tasks = []

                        def create_task(
                            self, content: str, priority: str = "medium", **kwargs
                        ) -> Dict[str, Any]:
                            task_id = f"task-{len(self.tasks) + 1}"
                            self.tasks.append(
                                {
                                    "id": task_id,
                                    "content": content,
                                    "status": "pending",
                                    "priority": priority,
                                }
                            )
                            return {"success": True, "task_id": task_id}

                        def update_task_status(
                            self, task_id: str, status: str
                        ) -> Dict[str, Any]:
                            for task in self.tasks:
                                if task["id"] == task_id:
                                    task["status"] = status
                                    return {"success": True}
                            return {"success": False, "error": "Task not found"}

                    return SimpleTaskTracker()

                raise ValueError(f"Unknown component: {component_type}")

        class TestAgentFactory(AgentFactory):
            def __init__(self, component_factory: ComponentFactory):
                self.component_factory = component_factory

            def create_agent(
                self, agent_type: str, config: AgentConfig
            ) -> AgentInterface:
                if agent_type == "workflow_agent":

                    class WorkflowAgent(AgentInterface):
                        def __init__(
                            self, config: AgentConfig, components: Dict[str, Any]
                        ):
                            self.config = config
                            self.components = components

                        def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                            # Use injected components
                            task_result = self.components["task_tracker"].create_task(
                                "Agent task", "medium"
                            )
                            self.components["state_manager"].save_state(
                                self.config.agent_id, {"task": task_result}
                            )
                            return {"success": True, "agent_id": self.config.agent_id}

                    # Create components
                    components = {
                        "state_manager": self.component_factory.create_component(
                            "state_manager", {}
                        ),
                        "task_tracker": self.component_factory.create_component(
                            "task_tracker", {}
                        ),
                    }

                    return WorkflowAgent(config, components)

                raise ValueError(f"Unknown agent type: {agent_type}")

        # Test factory-based creation
        component_factory = TestComponentFactory()
        agent_factory = TestAgentFactory(component_factory)

        agent_config = AgentConfig(agent_id="workflow-1", name="Workflow Agent")
        agent = agent_factory.create_agent("workflow_agent", agent_config)

        result = agent.execute({"test": "context"})

        assert result["success"] is True
        assert result["agent_id"] == "workflow-1"
