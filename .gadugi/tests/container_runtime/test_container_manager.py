"""
Tests for Container Manager.
"""

import pytest
import docker
from unittest.mock import Mock, patch

from container_runtime.container_manager import (
    ContainerManager,
    ContainerConfig,
    ContainerResult,
)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client fixture."""
    client = Mock(spec=docker.DockerClient)
    client.ping.return_value = True
    return client


@pytest.fixture
def container_manager(mock_docker_client):
    """Container manager fixture."""
    return ContainerManager(docker_client=mock_docker_client)


@pytest.fixture
def sample_config():
    """Sample container configuration."""
    return ContainerConfig(
        image="python:3.11-slim",
        command=["python", "-c", "print('Hello World')"],
        memory_limit="256m",
        cpu_limit="0.5",
        timeout=60,
    )


def test_container_manager_initialization(mock_docker_client):
    """Test container manager initialization."""
    manager = ContainerManager(docker_client=mock_docker_client)

    assert manager.client == mock_docker_client
    assert len(manager.active_containers) == 0
    assert len(manager.execution_history) == 0
    mock_docker_client.ping.assert_called_once()


def test_container_manager_initialization_without_client():
    """Test container manager initialization without client."""
    with patch("docker.from_env") as mock_from_env:
        mock_client = Mock(spec=docker.DockerClient)
        mock_client.ping.return_value = True
        mock_from_env.return_value = mock_client

        manager = ContainerManager()

        assert manager.client == mock_client
        mock_from_env.assert_called_once()
        mock_client.ping.assert_called_once()


def test_container_manager_docker_connection_failure():
    """Test container manager with Docker connection failure."""
    mock_client = Mock(spec=docker.DockerClient)
    mock_client.ping.side_effect = Exception("Connection failed")

    with pytest.raises(Exception, match="Failed to connect to Docker daemon"):
        ContainerManager(docker_client=mock_client)


def test_create_container_success(container_manager, sample_config):
    """Test successful container creation."""
    # Mock container creation
    mock_container = Mock()
    mock_container.name = "gadugi-test"
    container_manager.client.containers.create.return_value = mock_container

    container_id = container_manager.create_container(sample_config)

    assert container_id is not None  # type: ignore[comparison-overlap]
    assert len(container_id) > 0
    assert container_id in container_manager.active_containers
    assert container_manager.active_containers[container_id] == mock_container  # type: ignore[index]

    # Verify Docker API was called with correct parameters
    call_args = container_manager.client.containers.create.call_args
    assert call_args[1]["image"] == sample_config.image  # type: ignore[index]
    assert call_args[1]["command"] == sample_config.command  # type: ignore[index]
    assert call_args[1]["mem_limit"] == sample_config.memory_limit  # type: ignore[index]


def test_create_container_failure(container_manager, sample_config):
    """Test container creation failure."""
    # Create a mock APIError exception
    from docker.errors import APIError

    container_manager.client.containers.create.side_effect = APIError("Creation failed")

    with pytest.raises(Exception, match="Docker API error creating container"):
        container_manager.create_container(sample_config)


def test_start_container_success(container_manager, sample_config):
    """Test successful container start."""
    # Create container first
    mock_container = Mock()
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    # Start container
    container_manager.start_container(container_id)

    mock_container.start.assert_called_once()


def test_start_container_not_found(container_manager):
    """Test starting non-existent container."""
    with pytest.raises(Exception, match="Container .* not found"):
        container_manager.start_container("non-existent")


def test_start_container_failure(container_manager, sample_config):
    """Test container start failure."""
    # Create container first
    from docker.errors import APIError

    mock_container = Mock()
    mock_container.start.side_effect = APIError("Start failed")
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    with pytest.raises(Exception, match="Docker API error starting container"):
        container_manager.start_container(container_id)


def test_execute_container_success(container_manager, sample_config):
    """Test successful container execution."""
    # Mock container
    mock_container = Mock()
    mock_container.wait.return_value = 0  # Success exit code
    mock_container.logs.return_value = b"Hello World\n"

    container_manager.client.containers.create.return_value = mock_container

    with patch.object(container_manager, "_get_resource_usage", return_value={}):
        result = container_manager.execute_container(sample_config)

    assert isinstance(result, ContainerResult)
    assert result.exit_code == 0
    assert result.stdout == "Hello World\n"
    assert result is not None  # type: ignore[comparison-overlap] and result.status == ContainerStatus.STOPPED
    assert result.execution_time > 0


def test_execute_container_failure(container_manager, sample_config):
    """Test container execution with non-zero exit code."""
    # Mock container
    mock_container = Mock()
    mock_container.wait.return_value = 1  # Failure exit code
    mock_container.logs.return_value = b"Error occurred\n"

    container_manager.client.containers.create.return_value = mock_container

    with patch.object(container_manager, "_get_resource_usage", return_value={}):
        result = container_manager.execute_container(sample_config)

    assert result.exit_code == 1
    assert result is not None  # type: ignore[comparison-overlap] and result.status == ContainerStatus.FAILED


def test_execute_container_timeout(container_manager, sample_config):
    """Test container execution timeout."""
    # Mock container with timeout
    mock_container = Mock()
    mock_container.wait.side_effect = Exception("Timeout")
    mock_container.logs.return_value = b"Partial output\n"

    container_manager.client.containers.create.return_value = mock_container

    with patch.object(container_manager, "stop_container") as mock_stop:
        with patch.object(container_manager, "_get_resource_usage", return_value={}):
            result = container_manager.execute_container(sample_config)

    assert result.exit_code == 124  # Timeout exit code
    mock_stop.assert_called_once()


def test_stop_container_graceful(container_manager, sample_config):
    """Test graceful container stop."""
    # Create container
    mock_container = Mock()
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    # Stop container
    container_manager.stop_container(container_id, force=False, timeout=5)

    mock_container.stop.assert_called_once_with(timeout=5)


def test_stop_container_force(container_manager, sample_config):
    """Test forced container stop."""
    # Create container
    mock_container = Mock()
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    # Force stop container
    container_manager.stop_container(container_id, force=True)

    mock_container.kill.assert_called_once()


def test_stop_container_not_found(container_manager):
    """Test stopping non-existent container."""
    # Should not raise exception
    container_manager.stop_container("non-existent")


def test_cleanup_container(container_manager, sample_config):
    """Test container cleanup."""
    # Create container
    mock_container = Mock()
    mock_container.status = "exited"
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    # Cleanup container
    container_manager.cleanup_container(container_id)

    mock_container.remove.assert_called_once_with(force=True)
    assert container_id not in container_manager.active_containers


def test_cleanup_running_container(container_manager, sample_config):
    """Test cleanup of running container."""
    # Create running container
    mock_container = Mock()
    mock_container.status = "running"
    container_manager.client.containers.create.return_value = mock_container
    container_id = container_manager.create_container(sample_config)

    # Cleanup container
    container_manager.cleanup_container(container_id)

    mock_container.stop.assert_called_once_with(timeout=5)
    mock_container.remove.assert_called_once_with(force=True)


def test_get_resource_usage(container_manager):
    """Test resource usage collection."""
    mock_container = Mock()

    # Mock stats data
    stats_data = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 10000000000,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 500000000},
            "system_cpu_usage": 9000000000,
        },
        "memory_stats": {
            "usage": 134217728,  # 128MB
            "limit": 536870912,  # 512MB
        },
        "networks": {"eth0": {"rx_bytes": 1024, "tx_bytes": 2048}},
        "blkio_stats": {},
    }

    mock_container.stats.return_value = stats_data

    usage = container_manager._get_resource_usage(mock_container)

    assert "cpu_percent" in usage
    assert "memory_usage_bytes" in usage
    assert "memory_percent" in usage
    assert usage["memory_usage_bytes"] == 134217728  # type: ignore[index]
    assert usage["memory_percent"] == 25.0  # 128MB / 512MB * 100  # type: ignore[index]


def test_list_active_containers(container_manager, sample_config):
    """Test listing active containers."""
    # Create multiple containers
    mock_container1 = Mock()
    mock_container1.name = "gadugi-test1"
    mock_container1.status = "running"
    mock_container1.image.tags = ["python:3.11-slim"]

    mock_container2 = Mock()
    mock_container2.name = "gadugi-test2"
    mock_container2.status = "exited"
    mock_container2.image.tags = ["node:18-alpine"]

    container_manager.client.containers.create.return_value = mock_container1
    container_id1 = container_manager.create_container(sample_config)

    container_manager.client.containers.create.return_value = mock_container2
    container_id2 = container_manager.create_container(sample_config)

    containers = container_manager.list_active_containers()

    assert len(containers) == 2
    assert any(c["container_id"] == container_id1 for c in containers)  # type: ignore[index]
    assert any(c["container_id"] == container_id2 for c in containers)  # type: ignore[index]


def test_cleanup_all(container_manager, sample_config):
    """Test cleanup of all containers."""
    # Create multiple containers
    mock_container1 = Mock()
    mock_container2 = Mock()

    container_manager.client.containers.create.return_value = mock_container1
    container_manager.create_container(sample_config)

    container_manager.client.containers.create.return_value = mock_container2
    container_manager.create_container(sample_config)

    # Cleanup all
    container_manager.cleanup_all()

    assert len(container_manager.active_containers) == 0


def test_get_execution_history(container_manager, sample_config):
    """Test getting execution history."""
    # Execute a container to create history
    mock_container = Mock()
    mock_container.wait.return_value = 0
    mock_container.logs.return_value = b"Test output\n"

    container_manager.client.containers.create.return_value = mock_container

    with patch.object(container_manager, "_get_resource_usage", return_value={}):
        container_manager.execute_container(sample_config)

    history = container_manager.get_execution_history()

    assert len(history) == 1
    assert history[0].exit_code == 0  # type: ignore[index]

    # Test with limit
    limited_history = container_manager.get_execution_history(limit=1)
    assert len(limited_history) == 1
