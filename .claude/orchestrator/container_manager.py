#!/usr/bin/env python3
"""
ContainerManager - Docker-based execution for OrchestratorAgent

Replaces subprocess.Popen with proper Docker container isolation for true parallel,
observable task execution. Addresses critical issues identified in Issue #167.

Key Features:
- Docker SDK integration for container lifecycle management
- Proper Claude CLI invocation with automation flags
- Real-time output streaming and monitoring
- Resource limits and health checks
- Container orchestration for parallel execution

Security Features:
- Container isolation and resource limits
- Secure volume mounting for worktrees
- Network isolation between tasks
- Proper cleanup and garbage collection
"""

import asyncio
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import uuid

try:
    import docker
    from docker.errors import DockerException, ImageNotFound
    docker_available = True
except ImportError:
    logging.warning("Docker SDK not available. Install with: pip install docker")
    docker_available = False
    # Fallback classes
    class DockerException(Exception): pass
    class ImageNotFound(Exception): pass
    docker = None

websocket_available = False
try:
    import websockets  # type: ignore[import]
    websocket_available = True
except ImportError:
    logging.warning("WebSocket support not available. Install with: pip install websockets")
    websockets = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """Configuration for container execution"""
    image: str = "claude-orchestrator:latest"
    cpu_limit: str = "2.0"  # CPU cores
    memory_limit: str = "4g"  # Memory limit
    timeout_seconds: int = 3600  # 1 hour default
    network_mode: str = "bridge"
    auto_remove: bool = True
    detach: bool = False

    # Claude CLI specific settings
    claude_flags: Optional[List[str]] = None
    max_turns: int = 50
    output_format: str = "json"

    def __post_init__(self):
        if self.claude_flags is None:
            self.claude_flags = [
                "--dangerously-skip-permissions",
                "--verbose",
                f"--max-turns={self.max_turns}",
                f"--output-format={self.output_format}"
            ]


@dataclass
class ContainerResult:
    """Result of container execution"""
    container_id: str
    task_id: str
    status: str  # 'success', 'failed', 'timeout', 'cancelled'
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    logs: List[str]
    resource_usage: Dict[str, Any]
    error_message: Optional[str] = None


class ContainerOutputStreamer:
    """Streams container output in real-time"""

    def __init__(self, container_id: str, task_id: str) -> None:
        self.container_id = container_id
        self.task_id = task_id
        self.streaming = False
        self.clients: List[Any] = field(default_factory=list)

    async def start_streaming(self, container):
        """Start streaming container output"""
        self.streaming = True

        try:
            # Stream logs in real-time
            for log_line in container.logs(stream=True, follow=True):
                if not self.streaming:
                    break

                log_text = log_line.decode('utf-8').strip()

                # Broadcast to all WebSocket clients
                if self is not None and self.clients:
                    message = {
                        "task_id": self.task_id,
                        "container_id": self.container_id,
                        "timestamp": datetime.now().isoformat(),
                        "log": log_text
                    }

                    # Send to all connected clients
                    disconnected = []
                    for client in self.clients:
                        try:
                            await client.send(json.dumps(message))
                        except Exception:
                            disconnected.append(client)

                    # Clean up disconnected clients
                    for client in disconnected:
                        self.clients.remove(client)

        except Exception as e:
            logger.error(f"Output streaming error for {self.task_id}: {e}")
        finally:
            self.streaming = False

    def stop_streaming(self):
        """Stop output streaming"""
        self.streaming = False

    def add_client(self, client):
        """Add WebSocket client for output streaming"""
        if websocket_available:
            self.clients.append(client)

    def remove_client(self, client):
        """Remove WebSocket client"""
        if client in self.clients:
            self.clients.remove(client)


class ContainerManager:
    """Manages Docker container execution for orchestrator tasks"""

    def __init__(self, config: ContainerConfig) -> None:
        self.config = config or ContainerConfig()
        self.docker_client = None
        self.active_containers: Dict[Any, Any] = field(default_factory=dict)
        self.output_streamers: Dict[Any, Any] = field(default_factory=dict)
        self._initialize_docker()

    def _initialize_docker(self):
        """Initialize Docker client"""
        if not docker_available:
            raise RuntimeError("Docker SDK not available. Please install: pip install docker")

        try:
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")

            # Ensure orchestrator image exists
            self._ensure_orchestrator_image()

        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(f"Docker initialization failed: {e}")

    def _ensure_orchestrator_image(self):
        """Ensure the Claude orchestrator Docker image exists"""
        try:
            if self.docker_client is not None:
                self.docker_client.images.get(self.config.image)
            logger.info(f"Docker image {self.config.image} found")
        except ImageNotFound:
            logger.info(f"Building Docker image: {self.config.image}")
            self._build_orchestrator_image()

    def _build_orchestrator_image(self):
        """Build the Claude orchestrator Docker image"""
        # Create Dockerfile content
        dockerfile_content = '''
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN curl -fsSL https://claude.ai/cli/install.sh | sh

# Install Python dependencies
RUN pip install --no-cache-dir \\
    docker \\
    psutil \\
    websockets \\
    asyncio

# Set working directory
WORKDIR /workspace

# Default command
CMD ["bash"]
'''

        # Create temporary build context
        import tempfile
        with tempfile.TemporaryDirectory() as build_dir:
            dockerfile_path = Path(build_dir) / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)

            try:
                # Build the image
                logger.info("Building Claude orchestrator Docker image...")
                image, build_logs = self.docker_client.images.build(
                    path=build_dir,
                    tag=self.config.image,
                    rm=True
                )

                # Log build output
                for log in build_logs:
                    if isinstance(log, dict) and 'stream' in log:
                        stream_text = log['stream']
                        if isinstance(stream_text, str):
                            logger.info(f"Docker build: {stream_text.strip()}")

                logger.info(f"Successfully built image: {self.config.image}")

            except DockerException as e:
                logger.error(f"Failed to build Docker image: {e}")
                raise

    def execute_containerized_task(
        self,
        task_id: str,
        worktree_path: Path,
        prompt_file: str,
        task_context: Optional[Dict] = None,
        progress_callback: Optional[Callable] = None
    ) -> ContainerResult:
        """Execute a task in a Docker container"""

        if not self.docker_client:
            raise RuntimeError("Docker client not initialized")

        # Validate API key before container creation
        api_key = os.getenv('CLAUDE_API_KEY', '').strip()
        if not api_key:
            logger.error(f"CLAUDE_API_KEY not set for task {task_id}")
            return ContainerResult(
                container_id="none",
                task_id=task_id,
                status="failed",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0.0,
                exit_code=-1,
                stdout="",
                stderr="ERROR: CLAUDE_API_KEY environment variable not set",
                logs=[],
                resource_usage={},
                error_message="CLAUDE_API_KEY not set"
            )

        container_id = f"orchestrator-{task_id}-{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()

        # Validate host system resources
        try:
            import psutil
            mem = psutil.virtual_memory()
            if mem.available < 1024 * 1024 * 1024:  # Less than 1GB available
                logger.warning(f"Low memory available: {mem.available / (1024**3):.2f}GB")
                if mem.available < 512 * 1024 * 1024:  # Less than 512MB
                    return ContainerResult(
                        task_id=task_id,
                        status="failed",
                        exit_code=-1,
                        stdout="",
                        stderr="ERROR: Insufficient memory to create container",
                        logs="",
                        start_time=start_time,
                        end_time=datetime.now(),
                        duration=0.0,
                        resource_usage={}
                    )
        except ImportError:
            logger.warning("psutil not available, skipping resource check")

        logger.info(f"Starting containerized task: {task_id}")

        # Prepare container volumes
        volumes = {
            str(worktree_path.absolute()): {
                'bind': '/workspace',
                'mode': 'rw'
            }
        }

        # Prepare Claude CLI command with proper flags and path escaping
        import shlex
        escaped_prompt = shlex.quote(prompt_file)
        claude_cmd = [
            "claude",
            "-p", escaped_prompt
        ] + (self.config.claude_flags or [])

        logger.info(f"Container command: {' '.join(claude_cmd)}")

        try:
            # Create and start container
            container = self.docker_client.containers.run(
                image=self.config.image,
                command=claude_cmd,
                volumes=volumes,
                working_dir="/workspace",
                cpu_count=float(self.config.cpu_limit),
                mem_limit=self.config.memory_limit,
                network_mode=self.config.network_mode,
                detach=True,
                auto_remove=self.config.auto_remove,
                name=container_id,
                environment={
                    'PYTHONUNBUFFERED': '1',
                    'CLAUDE_API_KEY': os.getenv('CLAUDE_API_KEY', ''),
                    'TASK_ID': task_id
                }
            )

            self.active_containers[task_id] = container

            # Start output streaming
            streamer = ContainerOutputStreamer(container.id, task_id)
            self.output_streamers[task_id] = streamer

            # Start streaming in background thread
            if websocket_available:
                streaming_thread = threading.Thread(
                    target=lambda: asyncio.run(streamer.start_streaming(container)),
                    daemon=True
                )
                streaming_thread.start()

            # Wait for completion with timeout
            exit_code = container.wait(timeout=self.config.timeout_seconds)['StatusCode']

            # Get container logs
            logs = container.logs().decode('utf-8')
            stdout = logs  # Docker combines stdout/stderr
            stderr = ""

            # Determine status
            status = "success" if exit_code == 0 else "failed"

            # Get resource usage stats
            stats = container.stats(stream=False)
            resource_usage = {
                'memory_usage': stats.get('memory_stats', {}).get('usage', 0),
                'cpu_usage': stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0),
                'network_rx': stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0),
                'network_tx': stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0)
            }

        except docker.errors.ImageNotFound as e:
            logger.error(f"Docker image not found for {task_id}: {e}")
            exit_code = -2
            status = "failed"
            stdout = ""
            stderr = f"Docker image not found: {self.config.image}. Run 'docker build' first."
            logs = ""
            resource_usage = {}
        except docker.errors.APIError as e:
            logger.error(f"Docker API error for {task_id}: {e}")
            exit_code = -3
            status = "failed"
            stdout = ""
            stderr = f"Docker API error: {e}"
            logs = ""
            resource_usage = {}
        except docker.errors.ContainerError as e:
            logger.error(f"Container error for {task_id}: {e}")
            exit_code = e.exit_status
            status = "failed"
            stdout = e.stdout.decode('utf-8') if e.stdout else ""
            stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
            logs = ""
            resource_usage = {}
        except Exception as e:
            logger.error(f"Unexpected container execution error for {task_id}: {e}")
            exit_code = -99
            status = "failed"
            stdout = ""
            stderr = f"Unexpected error: {type(e).__name__}: {e}"
            logs = ""
            resource_usage = {}

            # Try to get partial logs
            if task_id in self.active_containers:
                try:
                    container = self.active_containers[task_id]
                    logs = container.logs().decode('utf-8')
                    stdout = logs
                except Exception:
                    pass

        finally:
            # Cleanup
            if task_id in self.active_containers:
                try:
                    container = self.active_containers[task_id]
                    container.stop(timeout=10)
                    if not self.config.auto_remove:
                        container.remove()
                except Exception as e:
                    logger.warning(f"Container cleanup failed for {task_id}: {e}")
                finally:
                    del self.active_containers[task_id]

            # Stop output streaming
            if task_id in self.output_streamers:
                self.output_streamers[task_id].stop_streaming()
                del self.output_streamers[task_id]

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = ContainerResult(
            container_id=container_id,
            task_id=task_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            logs=logs.split('\n') if logs else [],
            resource_usage=resource_usage,
            error_message=stderr if status == "failed" else None
        )

        logger.info(f"Container task completed: {task_id}, status={status}, duration={duration:.1f}s")

        # Progress callback
        if progress_callback:
            progress_callback(task_id, result)

        return result

    def execute_parallel_tasks(
        self,
        tasks: List[Dict],
        max_parallel: int = 4,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ContainerResult]:
        """Execute multiple tasks in parallel containers"""

        if not tasks:
            return {}

        logger.info(f"Starting parallel execution of {len(tasks)} tasks in containers")

        results = {}

        # Use ThreadPoolExecutor for parallel container execution
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                task_id = task['id']
                worktree_path = Path(task['worktree_path'])
                prompt_file = task['prompt_file']
                task_context = task.get('context', {})

                future = executor.submit(
                    self.execute_containerized_task,
                    task_id,
                    worktree_path,
                    prompt_file,
                    task_context,
                    progress_callback
                )
                future_to_task[future] = task_id

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    result = future.result()
                    results[task_id] = result
                except Exception as e:
                    logger.error(f"Task execution failed: {task_id}, error={e}")

                    # Create failed result
                    results[task_id] = ContainerResult(
                        container_id=f"failed-{task_id}",
                        task_id=task_id,
                        status="failed",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration=0.0,
                        exit_code=-1,
                        stdout="",
                        stderr=str(e),
                        logs=[],
                        resource_usage={},
                        error_message=str(e)
                    )

        return results

    def cancel_task(self, task_id: str):
        """Cancel a running containerized task"""
        if task_id in self.active_containers:
            try:
                container = self.active_containers[task_id]
                container.stop(timeout=10)
                logger.info(f"Cancelled containerized task: {task_id}")
            except Exception as e:
                logger.error(f"Failed to cancel task {task_id}: {e}")

    def cancel_all_tasks(self):
        """Cancel all running containerized tasks"""
        for task_id in list(self.active_containers.keys()):
            self.cancel_task(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a containerized task"""
        if task_id not in self.active_containers:
            return None

        try:
            container = self.active_containers[task_id]
            container.reload()  # Refresh container state

            stats = container.stats(stream=False)

            return {
                'task_id': task_id,
                'container_id': container.id,
                'status': (container.status if container is not None else None),
                'created': container.attrs['Created'],
                'started': container.attrs['State']['StartedAt'],
                'memory_usage': stats.get('memory_stats', {}).get('usage', 0),
                'cpu_percent': self._calculate_cpu_percent(stats),
                'network_io': stats.get('networks', {})
            }
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            return None

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})

            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})

            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(cpu_usage.get('percpu_usage', [])) * 100
                return round(cpu_percent, 2)

            return 0.0
        except Exception:
            return 0.0

    def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up ContainerManager resources...")

        # Cancel all active tasks
        self.cancel_all_tasks()

        # Stop all output streaming
        for streamer in self.output_streamers.values():
            streamer.stop_streaming()
        self.output_streamers.clear()

        # Close Docker client
        if self is not None and self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                logger.warning(f"Error closing Docker client: {e}")

        logger.info("ContainerManager cleanup complete")


def main():
    """CLI entry point for ContainerManager testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Container Manager for Orchestrator")
    parser.add_argument("--task-id", required=True, help="Task ID")
    parser.add_argument("--worktree-path", required=True, help="Worktree path")
    parser.add_argument("--prompt-file", required=True, help="Prompt file")
    parser.add_argument("--image", default="claude-orchestrator:latest", help="Docker image")

    args = parser.parse_args()

    # Create container manager
    config = ContainerConfig(image=args.image)
    manager = ContainerManager(config)

    try:
        # Execute single task
        result = manager.execute_containerized_task(
            task_id=(args.task_id if args is not None else None),
            worktree_path=Path(args.worktree_path),
            prompt_file=(args.prompt_file if args is not None else None)
        )

        print(f"Task completed: {(result.status if result is not None else None)}")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Exit code: {result.exit_code}")

        if result is not None and result.stdout:
            print(f"Output: {result.stdout[:500]}...")

        return 0 if (result.status if result is not None else None) == 'success' else 1

    except Exception as e:
        logger.error(f"Container execution failed: {e}")
        return 1
    finally:
        manager.cleanup()


if __name__ == "__main__":
    exit(main())
