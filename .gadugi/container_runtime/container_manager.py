"""
Container Manager for secure container lifecycle management.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    import docker
else:
    docker = None

# Runtime import attempt
try:
    import docker  # type: ignore[import-untyped]

    docker_available = True
except ImportError:
    docker_available = False

# Import Enhanced Separation shared modules
import sys
import os

# Add parent directory to path to import from shared
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.utils.error_handling import GadugiError  # type: ignore[import]

logger = logging.getLogger(__name__)


class ContainerStatus(Enum):
    """Container status enumeration."""

    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    REMOVED = "removed"


@dataclass
class ContainerConfig:
    """Container configuration."""

    image: str
    command: List[str]
    memory_limit: str = "512m"
    cpu_limit: str = "1.0"
    network_mode: str = "none"
    read_only: bool = True
    user: str = "1000:1000"
    working_dir: str = "/workspace"
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[Dict[str, Dict[str, str]]] = None
    security_opt: Optional[List[str]] = None
    cap_drop: Optional[List[str]] = None
    timeout: int = 1800  # 30 minutes default


@dataclass
class ContainerResult:
    """Container execution result."""

    container_id: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    resource_usage: Dict[str, Any]
    status: ContainerStatus


class ContainerManager:
    """
    Manages Docker container lifecycle for secure code execution.

    Provides container creation, execution, monitoring, and cleanup
    with comprehensive security controls and resource management.
    """

    def __init__(self, docker_client: Optional[Any] = None):
        """Initialize container manager."""
        if not docker_available:
            raise GadugiError("Docker is not available. Please install docker package.")

        self.client = docker_client or docker.from_env()  # type: ignore[attr-defined]
        self.active_containers: Dict[str, Any] = {}
        self.execution_history: List[ContainerResult] = []

        # Verify Docker daemon is accessible
        try:
            self.client.ping()
            logger.info("Docker daemon connection established")
        except Exception as e:
            raise GadugiError(f"Failed to connect to Docker daemon: {e}")

    def create_container(self, config: ContainerConfig) -> str:
        """
        Create a new container with security hardening.

        Args:
            config: Container configuration

        Returns:
            Container ID

        Raises:
            GadugiError: If container creation fails
        """
        container_id = str(uuid.uuid4())

        try:
            # Build container configuration with security hardening
            container_args = {
                "image": config.image,
                "command": config.command,
                "name": f"gadugi-{container_id[:8]}",
                "detach": True,
                "remove": False,  # We'll remove manually for better control
                "user": config.user,
                "working_dir": config.working_dir,
                "network_mode": config.network_mode,
                "read_only": config.read_only,
                "mem_limit": config.memory_limit,
                "cpu_count": float(config.cpu_limit),
                "security_opt": config.security_opt or ["no-new-privileges:true"],
                "cap_drop": config.cap_drop or ["ALL"],
                "environment": config.environment or {},
                "volumes": config.volumes or {},
                "tmpfs": {"/tmp": "rw,noexec,nosuid,size=100m"},
                "ulimits": [
                    docker.types.Ulimit(name="nproc", soft=1024, hard=1024),  # type: ignore[attr-defined]
                    docker.types.Ulimit(name="nofile", soft=1024, hard=1024),  # type: ignore[attr-defined]
                ],
            }

            # Create container
            container = self.client.containers.create(**container_args)
            self.active_containers[container_id] = container

            logger.info(f"Container created: {container_id[:8]} ({container.name})")
            return container_id

        except docker.errors.APIError as e:  # type: ignore[attr-defined]
            raise GadugiError(f"Docker API error creating container: {e}")
        except Exception as e:
            raise GadugiError(f"Unexpected error creating container: {e}")

    def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id: Container ID to start

        Raises:
            GadugiError: If container start fails
        """
        if container_id not in self.active_containers:
            raise GadugiError(f"Container {container_id} not found")

        try:
            container = self.active_containers[container_id]
            container.start()
            logger.info(f"Container started: {container_id[:8]}")

        except docker.errors.APIError as e:  # type: ignore[attr-defined]
            raise GadugiError(f"Docker API error starting container: {e}")
        except Exception as e:
            raise GadugiError(f"Unexpected error starting container: {e}")

    def execute_container(self, config: ContainerConfig) -> ContainerResult:
        """
        Execute a container from creation to completion.

        Args:
            config: Container configuration

        Returns:
            Container execution result

        Raises:
            GadugiError: If execution fails
        """
        start_time = time.time()
        container_id = None

        try:
            # Create and start container
            container_id = self.create_container(config)
            self.start_container(container_id)

            container = self.active_containers[container_id]

            # Wait for completion with timeout
            try:
                exit_code = container.wait(timeout=config.timeout)
                if isinstance(exit_code, dict):
                    exit_code = exit_code.get("StatusCode", 1)
            except Exception as e:
                logger.warning(f"Container timeout or error: {e}")
                self.stop_container(container_id, force=True)
                exit_code = 124  # Timeout exit code

            # Get logs
            try:
                logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                stdout = logs  # Docker combines stdout/stderr
                stderr = ""
            except Exception as e:
                logger.warning(f"Failed to retrieve container logs: {e}")
                stdout = ""
                stderr = f"Log retrieval failed: {e}"

            # Get resource usage stats
            resource_usage = self._get_resource_usage(container)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Create result
            result = ContainerResult(
                container_id=container_id,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                resource_usage=resource_usage,
                status=ContainerStatus.STOPPED if exit_code == 0 else ContainerStatus.FAILED,
            )

            # Store in history
            self.execution_history.append(result)

            logger.info(
                f"Container execution completed: {container_id[:8]} "
                f"(exit_code={exit_code}, time={execution_time:.2f}s)"
            )

            return result

        finally:
            # Always cleanup container
            if container_id:
                self.cleanup_container(container_id)

    def stop_container(self, container_id: str, force: bool = False, timeout: int = 10) -> None:
        """
        Stop a running container.

        Args:
            container_id: Container ID to stop
            force: Force kill container if graceful stop fails
            timeout: Timeout for graceful stop
        """
        if container_id not in self.active_containers:
            logger.warning(f"Container {container_id} not found for stopping")
            return

        try:
            container = self.active_containers[container_id]

            if force:
                container.kill()
                logger.info(f"Container killed: {container_id[:8]}")
            else:
                container.stop(timeout=timeout)
                logger.info(f"Container stopped: {container_id[:8]}")

        except docker.errors.NotFound:  # type: ignore[attr-defined]
            logger.info(f"Container {container_id[:8]} already removed")
        except Exception as e:
            logger.error(f"Error stopping container {container_id[:8]}: {e}")

    def cleanup_container(self, container_id: str) -> None:
        """
        Clean up container resources.

        Args:
            container_id: Container ID to cleanup
        """
        if container_id not in self.active_containers:
            return

        try:
            container = self.active_containers[container_id]

            # Stop if still running
            try:
                if container.status == "running":
                    container.stop(timeout=5)

                # Remove container
                container.remove(force=True)
                logger.info(f"Container cleaned up: {container_id[:8]}")

            except docker.errors.NotFound:  # type: ignore[attr-defined]
                logger.info(f"Container {container_id[:8]} already removed")
            except Exception as e:
                logger.warning(f"Error during container cleanup: {e}")

        finally:
            # Remove from active containers
            self.active_containers.pop(container_id, None)

    def _get_resource_usage(self, container) -> Dict[str, Any]:
        """Get container resource usage statistics."""
        try:
            stats = container.stats(stream=False)

            # Calculate CPU usage percentage
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            cpu_percent = 0.0
            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get(
                    "cpu_usage", {}
                ).get("total_usage", 0)
                system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                    "system_cpu_usage", 0
                )

                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0

            # Memory usage
            memory_stats = stats.get("memory_stats", {})
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)

            return {
                "cpu_percent": cpu_percent,
                "memory_usage_bytes": memory_usage,
                "memory_limit_bytes": memory_limit,
                "memory_percent": (memory_usage / memory_limit * 100) if memory_limit > 0 else 0,
                "network_stats": stats.get("networks", {}),
                "block_io_stats": stats.get("blkio_stats", {}),
            }

        except Exception as e:
            logger.warning(f"Failed to get container resource usage: {e}")
            return {}

    def list_active_containers(self) -> List[Dict[str, Any]]:
        """List all active containers managed by this instance."""
        containers = []
        for container_id, container in self.active_containers.items():
            try:
                container.reload()
                containers.append(
                    {
                        "container_id": container_id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                    }
                )
            except Exception as e:
                logger.warning(f"Error getting container info for {container_id}: {e}")

        return containers

    def cleanup_all(self) -> None:
        """Clean up all active containers."""
        container_ids = list(self.active_containers.keys())
        for container_id in container_ids:
            self.cleanup_container(container_id)

        logger.info(f"Cleaned up {len(container_ids)} containers")

    def get_execution_history(self, limit: Optional[int] = None) -> List[ContainerResult]:
        """Get container execution history."""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()
