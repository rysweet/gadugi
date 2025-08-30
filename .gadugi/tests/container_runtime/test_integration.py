"""
Integration tests for Container Execution Environment.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from container_runtime import ContainerExecutionEngine
from container_runtime.agent_integration import AgentContainerExecutor


@pytest.fixture
def temp_dir():
    """Temporary directory fixture."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_execution_engine():
    """Mock execution engine for testing."""
    with patch("container_runtime.agent_integration.ContainerExecutionEngine") as mock_engine:
        engine_instance = Mock()
        mock_engine.return_value = engine_instance
        yield engine_instance


class TestContainerExecutionEngine:
    """Test container execution engine integration."""

    def test_engine_initialization(self, temp_dir):
        """Test execution engine initialization."""
        # Mock Docker client to avoid requiring actual Docker
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            assert engine.container_manager is not None  # type: ignore[union-attr]
            assert engine.security_policy is not None  # type: ignore[union-attr]
            assert engine.resource_manager is not None  # type: ignore[union-attr]
            assert engine.audit_logger is not None  # type: ignore[union-attr]
            assert engine.image_manager is not None  # type: ignore[union-attr]

    def test_python_code_execution_mock(self, temp_dir):
        """Test Python code execution with mocked components."""
        with patch("docker.from_env") as mock_docker:
            # Mock Docker client
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            # Mock container execution
            with patch(
                "container_runtime.container_manager.ContainerManager.execute_container"
            ) as mock_execute:
                from container_runtime.container_manager import (
                    ContainerResult,
                    ContainerStatus,
                )

                mock_result = ContainerResult(
                    container_id="test-123",
                    exit_code=0,
                    stdout="Hello from Python!\n",
                    stderr="",
                    execution_time=1.5,
                    resource_usage={
                        "cpu_percent": 10.0,
                        "memory_usage_bytes": 50000000,
                    },
                    status=ContainerStatus.STOPPED,
                )
                mock_execute.return_value = mock_result

                # Mock image manager
                with patch(
                    "container_runtime.image_manager.ImageManager.get_or_create_runtime_image"
                ) as mock_image:
                    mock_image.return_value = "gadugi/python:test"

                    # Mock resource manager capacity check
                    with patch(
                        "container_runtime.resource_manager.ResourceManager.check_system_capacity"
                    ) as mock_capacity:
                        mock_capacity.return_value = True

                        engine = ContainerExecutionEngine(
                            audit_log_dir=temp_dir / "audit",
                            image_cache_dir=temp_dir / "images",
                        )

                        response = engine.execute_python_code("print('Hello from Python!')")

                        assert response.success is True
                        assert response.exit_code == 0
                        assert "Hello from Python!" in response.stdout
                        assert response.execution_time == 1.5

    def test_security_policy_enforcement(self, temp_dir):
        """Test security policy enforcement."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            # Test policy validation - should raise exception for blocked command
            with pytest.raises(Exception):
                engine.security_policy.validate_execution_request(
                    image="python:3.11-slim",
                    command=["sudo", "rm", "-rf", "/"],
                    policy_name="standard",
                )

    def test_audit_logging(self, temp_dir):
        """Test audit logging functionality."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            # Log a test event
            from container_runtime.audit_logger import AuditEventType, AuditSeverity

            event_id = engine.audit_logger.log_event(
                event_type=AuditEventType.CONTAINER_CREATED,
                severity=AuditSeverity.INFO,
                message="Test container created",
                container_id="test-123",
                details={"test": True},
            )

            assert event_id is not None  # type: ignore[comparison-overlap]
            assert len(event_id) > 0

            # Verify audit log file was created
            audit_files = list((temp_dir / "audit").glob("audit_*.jsonl"))
            assert len(audit_files) > 0

    def test_resource_monitoring(self, temp_dir):
        """Test resource monitoring functionality."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            # Test system capacity check
            with patch("psutil.cpu_percent", return_value=50.0):
                with patch("psutil.virtual_memory") as mock_memory:
                    mock_memory.return_value.percent = 60.0

                    capacity = engine.resource_manager.check_system_capacity()
                    assert capacity is True  # Should have capacity

    def test_execution_statistics(self, temp_dir):
        """Test execution statistics collection."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            stats = engine.get_execution_statistics()

            assert "active_executions" in stats
            assert "system_usage" in stats
            assert "container_usage" in stats
            assert "security_summary" in stats
            assert "available_policies" in stats

            # Should have built-in policies
            assert len(stats["available_policies"]) >= 4  # type: ignore[index]


class TestAgentContainerExecutor:
    """Test agent container executor integration."""

    def test_executor_initialization(self, mock_execution_engine):
        """Test executor initialization."""
        executor = AgentContainerExecutor(default_policy="testing", audit_enabled=True)

        assert executor.default_policy == "testing"
        assert executor.audit_enabled is True
        assert executor.execution_engine is not None  # type: ignore[union-attr]

    def test_python_code_execution(self, mock_execution_engine):
        """Test Python code execution through executor."""
        from container_runtime.execution_engine import ExecutionResponse

        # Mock response
        mock_response = ExecutionResponse(
            request_id="test-123",
            success=True,
            exit_code=0,
            stdout="Hello Python!\n",
            stderr="",
            execution_time=2.0,
            resource_usage={},
            security_events=[],
            audit_events=[],
        )

        mock_execution_engine.execute_python_code.return_value = mock_response

        executor = AgentContainerExecutor()
        result = executor.execute_python_code("print('Hello Python!')")

        assert result["success"] is True  # type: ignore[index]
        assert result["exit_code"] == 0  # type: ignore[index]
        assert result["stdout"] == "Hello Python!\n"  # type: ignore[index]
        assert result["execution_time"] == 2.0  # type: ignore[index]

    def test_shell_script_execution(self, mock_execution_engine, temp_dir):
        """Test shell script execution through executor."""
        from container_runtime.execution_engine import ExecutionResponse

        # Create test script
        script_file = temp_dir / "test_script.sh"
        with open(script_file, "w") as f:
            f.write("#!/bin/sh\necho 'Hello Shell!'\n")

        # Mock response
        mock_response = ExecutionResponse(
            request_id="test-456",
            success=True,
            exit_code=0,
            stdout="Hello Shell!\n",
            stderr="",
            execution_time=1.0,
            resource_usage={},
            security_events=[],
            audit_events=[],
        )

        mock_execution_engine.execute_shell_script.return_value = mock_response

        executor = AgentContainerExecutor()
        result = executor.execute_script(str(script_file))

        assert result["success"] is True  # type: ignore[index]
        assert result["stdout"] == "Hello Shell!\n"  # type: ignore[index]

    def test_command_execution(self, mock_execution_engine):
        """Test command execution through executor."""
        from container_runtime.execution_engine import ExecutionResponse

        # Mock response
        mock_response = ExecutionResponse(
            request_id="test-789",
            success=True,
            exit_code=0,
            stdout="Command output\n",
            stderr="",
            execution_time=0.5,
            resource_usage={},
            security_events=[],
            audit_events=[],
        )

        mock_execution_engine.execute.return_value = mock_response

        executor = AgentContainerExecutor()
        result = executor.execute_command(["echo", "Command output"])

        assert result["success"] is True  # type: ignore[index]
        assert result["stdout"] == "Command output\n"  # type: ignore[index]

    def test_runtime_detection(self, mock_execution_engine):
        """Test runtime detection from file extensions."""
        executor = AgentContainerExecutor()

        assert executor._detect_runtime(Path("script.py")) == "python"
        assert executor._detect_runtime(Path("script.js")) == "node"
        assert executor._detect_runtime(Path("script.mjs")) == "node"
        assert executor._detect_runtime(Path("script.sh")) == "shell"
        assert executor._detect_runtime(Path("script.bash")) == "shell"
        assert executor._detect_runtime(Path("script.unknown")) == "shell"

    def test_system_status(self, mock_execution_engine):
        """Test system status retrieval."""
        mock_stats = {
            "active_executions": 0,
            "system_usage": {"cpu_percent": 25.0},
            "available_policies": ["minimal", "standard", "hardened"],
        }

        mock_execution_engine.get_execution_statistics.return_value = mock_stats

        executor = AgentContainerExecutor()
        status = executor.get_system_status()

        assert status == mock_stats
        assert status["active_executions"] == 0  # type: ignore[index]

    def test_error_handling(self, mock_execution_engine):
        """Test error handling in executor."""
        mock_execution_engine.execute_python_code.side_effect = Exception("Test error")

        executor = AgentContainerExecutor()
        result = executor.execute_python_code("print('test')")

        assert result["success"] is False  # type: ignore[index]
        assert result["exit_code"] == 1  # type: ignore[index]
        assert "Test error" in result["stderr"]  # type: ignore[index]
        assert result["error"] == "Test error"  # type: ignore[index]

    def test_script_file_not_found(self, mock_execution_engine):
        """Test handling of non-existent script file."""
        executor = AgentContainerExecutor()
        result = executor.execute_script("/nonexistent/script.py")

        assert result["success"] is False  # type: ignore[index]
        assert result["exit_code"] == 1  # type: ignore[index]
        assert "not found" in result["stderr"].lower()  # type: ignore[index]


class TestSecurityPolicyIntegration:
    """Test security policy integration."""

    def test_policy_file_loading(self, temp_dir):
        """Test loading custom policies from file."""
        policy_data = {
            "policies": {
                "test_policy": {
                    "security_level": "standard",
                    "network_policy": "none",
                    "resources": {"memory": "256m", "cpu": "0.5"},
                    "security": {"read_only_root": True, "user_id": 1000},
                    "allowed_images": ["python:3.11-slim"],
                    "audit_required": True,
                }
            }
        }

        policy_file = temp_dir / "test_policies.yaml"
        with open(policy_file, "w") as f:
            import yaml

            yaml.dump(policy_data, f)

        from container_runtime.security_policy import SecurityPolicyEngine

        engine = SecurityPolicyEngine(policy_file=policy_file)

        assert "test_policy" in engine.policies
        policy = engine.get_policy("test_policy")
        assert policy.resource_limits.memory == "256m"
        assert policy.security_constraints.user_id == 1000


class TestCleanupAndShutdown:
    """Test cleanup and shutdown functionality."""

    def test_cleanup_resources(self, temp_dir):
        """Test resource cleanup."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            # Mock cleanup methods
            with patch.object(engine.container_manager, "cleanup_all"):
                with patch.object(engine.image_manager, "cleanup_old_images", return_value=2):
                    with patch.object(engine.audit_logger, "cleanup_old_logs", return_value=3):
                        stats = engine.cleanup_resources()

                        assert "images_removed" in stats
                        assert "audit_logs_removed" in stats
                        assert stats["images_removed"] == 2  # type: ignore[index]
                        assert stats["audit_logs_removed"] == 3  # type: ignore[index]

    def test_shutdown(self, temp_dir):
        """Test graceful shutdown."""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client

            engine = ContainerExecutionEngine(
                audit_log_dir=temp_dir / "audit", image_cache_dir=temp_dir / "images"
            )

            # Mock active executions
            engine.active_executions = {
                "exec-1": {"container_id": "container-1"},
                "exec-2": {"container_id": "container-2"},
            }

            with patch.object(engine.container_manager, "stop_container"):
                with patch.object(engine, "cleanup_resources", return_value={}):
                    # Should not raise exception
                    engine.shutdown()
