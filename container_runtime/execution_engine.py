"""
Container Execution Engine for Gadugi Multi-Agent System.

Main interface for secure containerized execution that integrates
all container runtime components with enhanced separation architecture.
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from .container_manager import ContainerManager, ContainerConfig, ContainerResult
from .security_policy import SecurityPolicyEngine, ExecutionPolicy
from .resource_manager import ResourceManager, ResourceAlert
from .audit_logger import AuditLogger
from .image_manager import ImageManager

# Import Enhanced Separation shared modules
import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", ".claude", "shared", "utils")
)
try:
    from error_handling import GadugiError  # type: ignore
except ImportError:
    class GadugiError(Exception):  # type: ignore
        pass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRequest:
    """Container execution request."""

    runtime: str  # python, node, shell, multi
    command: List[str]
    code: Optional[str] = None
    files: Optional[Dict[str, str]] = None  # filename: content
    environment: Optional[Dict[str, str]] = None
    security_policy: Optional[str] = None
    timeout: Optional[int] = None
    user_id: Optional[str] = None
    working_directory: str = "/workspace"


@dataclass
class ExecutionResponse:
    """Container execution response."""

    request_id: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    resource_usage: Dict[str, Any]
    security_events: List[Dict[str, Any]]
    audit_events: List[str]
    error_message: Optional[str] = None


class ContainerExecutionEngine:
    """
    Main container execution engine for Gadugi multi-agent system.

    Provides high-level interface for secure containerized execution
    with comprehensive security, monitoring, and audit capabilities.
    """

    def __init__(
        self,
        policy_file: Optional[Path] = None,
        audit_log_dir: Optional[Path] = None,
        image_cache_dir: Optional[Path] = None,
    ):
        """
        Initialize container execution engine.

        Args:
            policy_file: Security policy configuration file
            audit_log_dir: Directory for audit logs
            image_cache_dir: Directory for image cache
        """
        self.execution_id_counter = 0
        self.execution_lock = threading.Lock()

        # Initialize core components
        self.container_manager = ContainerManager()
        self.security_policy = SecurityPolicyEngine(policy_file)
        self.resource_manager = ResourceManager()
        self.audit_logger = AuditLogger(audit_log_dir)
        self.image_manager = ImageManager(image_cache_dir=image_cache_dir)

        # Track active executions
        self.active_executions: Dict[str, Dict[str, Any]] = {}

        # Register resource alert handler
        self.resource_manager.add_alert_handler(self._handle_resource_alert)

        logger.info("Container execution engine initialized")

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        with self.execution_lock:
            self.execution_id_counter += 1
            return f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.execution_id_counter:04d}"

    def _handle_resource_alert(self, alert: ResourceAlert) -> None:
        """Handle resource alerts from resource manager."""
        # Log security violation if critical resource usage
        if alert.severity == "critical":
            self.audit_logger.log_security_violation(
                container_id=alert.container_id,
                violation_type="resource_exhaustion",
                description=alert.message,
                security_context={
                    "resource_type": alert.resource_type,
                    "threshold": alert.threshold,
                    "actual_value": alert.current_value,
                },
            )
        else:
            self.audit_logger.log_resource_limit_exceeded(
                container_id=alert.container_id,
                resource_type=alert.resource_type,
                limit=alert.threshold,
                actual=alert.current_value,
            )

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        Execute code in secure container environment.

        Args:
            request: Execution request with code and configuration

        Returns:
            Execution response with results and audit information

        Raises:
            GadugiError: If execution fails
        """
        request_id = self._generate_request_id()

        # Validate system capacity
        if not self.resource_manager.check_system_capacity():
            raise GadugiError(
                "System at capacity - cannot execute additional containers"
            )

        audit_events = []
        security_events = []

        try:
            # Get security policy
            policy = self.security_policy.get_policy(request.security_policy)

            # Validate execution request against policy
            image_name = self._get_runtime_image(request.runtime)
            self.security_policy.validate_execution_request(
                image=image_name,
                command=request.command,
                policy_name=request.security_policy,
            )

            # Log policy application
            policy_event_id = self.audit_logger.log_policy_applied(
                container_id=request_id,
                policy_name=policy.name,
                policy_details=self.security_policy.get_policy_summary(policy.name),
                user_id=request.user_id,
            )
            audit_events.append(policy_event_id)

            # Prepare container configuration
            container_config = self._build_container_config(request, policy, image_name)

            # Track active execution
            self.active_executions[request_id] = {
                "started": datetime.now(),
                "request": request,
                "policy": policy.name,
                "container_id": None,
            }

            # Execute container
            result = self._execute_container(
                request_id, container_config, request.user_id
            )

            # Build response
            response = ExecutionResponse(
                request_id=request_id,
                success=result.exit_code == 0,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=result.execution_time,
                resource_usage=result.resource_usage,
                security_events=security_events,
                audit_events=audit_events,
            )

            logger.info(
                f"Execution completed: {request_id} (success={response.success})"
            )
            return response

        except Exception as e:
            # Log execution failure
            error_event_id = self.audit_logger.log_container_failed(
                container_id=request_id, error=str(e), user_id=request.user_id
            )
            audit_events.append(error_event_id)

            # Return error response
            return ExecutionResponse(
                request_id=request_id,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                resource_usage={},
                security_events=security_events,
                audit_events=audit_events,
                error_message=str(e),
            )

        finally:
            # Clean up active execution tracking
            self.active_executions.pop(request_id, None)

    def _get_runtime_image(self, runtime: str) -> str:
        """Get or create runtime image for execution."""
        try:
            return self.image_manager.get_or_create_runtime_image(runtime)
        except Exception as e:
            raise GadugiError(f"Failed to get runtime image for {runtime}: {e}")

    def _build_container_config(
        self, request: ExecutionRequest, policy: ExecutionPolicy, image_name: str
    ) -> ContainerConfig:
        """Build container configuration from request and policy."""

        # Base configuration
        base_config = {
            "image": image_name,
            "command": request.command,
            "working_dir": request.working_directory,
            "environment": request.environment or {},
            "timeout": request.timeout or policy.resource_limits.execution_time,
        }

        # Apply security policy
        secured_config = self.security_policy.apply_policy_to_container_config(
            base_config, policy.name
        )

        # Convert to ContainerConfig
        return ContainerConfig(
            image=secured_config["image"],
            command=secured_config["command"],
            memory_limit=secured_config.get("mem_limit", "512m"),
            cpu_limit=str(secured_config.get("cpu_count", 1.0)),
            network_mode=secured_config.get("network_mode", "none"),
            read_only=secured_config.get("read_only", True),
            user=secured_config.get("user", "1000:1000"),
            working_dir=secured_config.get("working_dir", "/workspace"),
            environment=secured_config.get("environment", {}),
            security_opt=secured_config.get("security_opt", []),
            cap_drop=secured_config.get("cap_drop", ["ALL"]),
            timeout=secured_config.get("timeout", 1800),
        )

    def _execute_container(
        self, request_id: str, config: ContainerConfig, user_id: Optional[str]
    ) -> ContainerResult:
        """Execute container with monitoring and audit logging."""

        # Log container creation
        self.audit_logger.log_container_created(
            container_id=request_id,
            image=config.image,
            command=config.command,
            security_policy=config.security_opt,
            resource_limits={
                "memory": config.memory_limit,
                "cpu": config.cpu_limit,
                "timeout": config.timeout,
            },
            user_id=user_id,
        )

        try:
            # Execute container
            result = self.container_manager.execute_container(config)

            # Register container for monitoring (if it was created successfully)
            if (
                hasattr(result, "container_id")
                and result.container_id in self.container_manager.active_containers
            ):
                container = self.container_manager.active_containers[
                    result.container_id
                ]
                self.resource_manager.register_container(result.container_id, container)

            # Log container completion
            self.audit_logger.log_container_stopped(
                container_id=request_id,
                exit_code=result.exit_code,
                execution_time=result.execution_time,
                resource_usage=result.resource_usage,
                user_id=user_id,
            )

            return result

        except Exception as e:
            # Log container failure
            self.audit_logger.log_container_failed(
                container_id=request_id, error=str(e), user_id=user_id
            )
            raise

        finally:
            # Ensure container is unregistered from monitoring
            try:
                self.resource_manager.unregister_container(request_id)
            except Exception:
                pass  # Not critical if unregistration fails

    def execute_python_code(
        self,
        code: str,
        packages: Optional[List[str]] = None,
        security_policy: Optional[str] = None,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> ExecutionResponse:
        """
        Execute Python code in secure container.

        Args:
            code: Python code to execute
            packages: Optional Python packages to install
            security_policy: Security policy to apply
            timeout: Execution timeout in seconds
            user_id: User ID for audit logging

        Returns:
            Execution response
        """
        # Create temporary Python file
        files = {"main.py": code}

        # If packages specified, create requirements.txt
        if packages:
            files["requirements.txt"] = "\n".join(packages)
            command = ["sh", "-c", "pip install -r requirements.txt && python main.py"]
        else:
            command = ["python", "main.py"]

        request = ExecutionRequest(
            runtime="python",
            command=command,
            code=code,
            files=files,
            security_policy=security_policy,
            timeout=timeout,
            user_id=user_id,
        )

        return self.execute(request)

    def execute_shell_script(
        self,
        script: str,
        security_policy: Optional[str] = None,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> ExecutionResponse:
        """
        Execute shell script in secure container.

        Args:
            script: Shell script to execute
            security_policy: Security policy to apply
            timeout: Execution timeout in seconds
            user_id: User ID for audit logging

        Returns:
            Execution response
        """
        files = {"script.sh": script}
        command = ["sh", "script.sh"]

        request = ExecutionRequest(
            runtime="shell",
            command=command,
            code=script,
            files=files,
            security_policy=security_policy,
            timeout=timeout,
            user_id=user_id,
        )

        return self.execute(request)

    def execute_node_code(
        self,
        code: str,
        packages: Optional[List[str]] = None,
        security_policy: Optional[str] = None,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> ExecutionResponse:
        """
        Execute Node.js code in secure container.

        Args:
            code: Node.js code to execute
            packages: Optional npm packages to install
            security_policy: Security policy to apply
            timeout: Execution timeout in seconds
            user_id: User ID for audit logging

        Returns:
            Execution response
        """
        files = {"main.js": code}

        # If packages specified, create package.json
        if packages:
            package_json = {
                "name": "gadugi-execution",
                "version": "1.0.0",
                "dependencies": {pkg: "latest" for pkg in packages},
            }
            files["package.json"] = json.dumps(package_json, indent=2)
            command = ["sh", "-c", "npm install && node main.js"]
        else:
            command = ["node", "main.js"]

        request = ExecutionRequest(
            runtime="node",
            command=command,
            code=code,
            files=files,
            security_policy=security_policy,
            timeout=timeout,
            user_id=user_id,
        )

        return self.execute(request)

    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List currently active executions."""
        active = []
        current_time = datetime.now()

        for request_id, info in self.active_executions.items():
            duration = (current_time - info["started"]).total_seconds()
            active.append(
                {
                    "request_id": request_id,
                    "runtime": info["request"].runtime,
                    "policy": info["policy"],
                    "duration_seconds": duration,
                    "user_id": info["request"].user_id,
                }
            )

        return active

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics and system status."""
        return {
            "active_executions": len(self.active_executions),
            "system_usage": self.resource_manager.get_system_usage(),
            "container_usage": self.resource_manager.get_usage_summary(),
            "security_summary": self.image_manager.get_security_summary(),
            "audit_statistics": self.audit_logger.get_statistics(),
            "available_policies": self.security_policy.list_policies(),
        }

    def get_security_alerts(
        self, since: Optional[datetime] = None
    ) -> List[ResourceAlert]:
        """Get recent security alerts."""
        return self.resource_manager.get_alerts(severity="critical", since=since)

    def cleanup_resources(self) -> Dict[str, int]:
        """Clean up old resources and return cleanup statistics."""
        stats = {}

        try:
            # Clean up old containers
            self.container_manager.cleanup_all()

            # Clean up old images
            images_removed = self.image_manager.cleanup_old_images()
            stats["images_removed"] = images_removed

            # Clean up old audit logs
            logs_removed = self.audit_logger.cleanup_old_logs()
            stats["audit_logs_removed"] = logs_removed

            # Clean up resource monitoring
            self.resource_manager.cleanup()

            logger.info(f"Resource cleanup completed: {stats}")

        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
            stats["error"] = str(e)

        return stats

    def shutdown(self) -> None:
        """Gracefully shutdown execution engine."""
        logger.info("Shutting down container execution engine")

        try:
            # Stop all active executions
            for request_id in list(self.active_executions.keys()):
                try:
                    # Force stop container if still running
                    if request_id in self.container_manager.active_containers:
                        self.container_manager.stop_container(request_id, force=True)
                except Exception as e:
                    logger.warning(f"Error stopping execution {request_id}: {e}")

            # Cleanup all resources
            self.cleanup_resources()

            logger.info("Container execution engine shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Convenience functions for direct usage
def execute_python(
    code: str,
    packages: Optional[List[str]] = None,
    security_policy: str = "standard",
    timeout: int = 300,
) -> ExecutionResponse:
    """Convenience function to execute Python code."""
    engine = ContainerExecutionEngine()
    try:
        return engine.execute_python_code(code, packages, security_policy, timeout)
    finally:
        engine.shutdown()


def execute_shell(
    script: str, security_policy: str = "standard", timeout: int = 300
) -> ExecutionResponse:
    """Convenience function to execute shell script."""
    engine = ContainerExecutionEngine()
    try:
        return engine.execute_shell_script(script, security_policy, timeout)
    finally:
        engine.shutdown()


def execute_node(
    code: str,
    packages: Optional[List[str]] = None,
    security_policy: str = "standard",
    timeout: int = 300,
) -> ExecutionResponse:
    """Convenience function to execute Node.js code."""
    engine = ContainerExecutionEngine()
    try:
        return engine.execute_node_code(code, packages, security_policy, timeout)
    finally:
        engine.shutdown()
