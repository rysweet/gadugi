
import logging
import yaml
import sys
import os

"""
Security Policy Engine for Container Execution.

Implements comprehensive security policies for container execution,
including resource limits, capability restrictions, and access controls.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import Enhanced Separation shared modules

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", ".claude", "shared", "utils")
)
from error_handling import GadugiError

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for different execution contexts."""

    MINIMAL = "minimal"  # Basic isolation
    STANDARD = "standard"  # Default security level
    HARDENED = "hardened"  # Enhanced security
    PARANOID = "paranoid"  # Maximum security

class NetworkPolicy(Enum):
    """Network access policies."""

    NONE = "none"  # No network access
    INTERNAL = "internal"  # Internal network only
    LIMITED = "limited"  # Limited external access
    FULL = "full"  # Full network access

@dataclass
class ResourceLimits:
    """Resource limit specifications."""

    memory: str = "512m"
    cpu: str = "1.0"
    disk: str = "1g"
    processes: int = 1024
    open_files: int = 1024
    execution_time: int = 1800  # 30 minutes

@dataclass
class SecurityConstraints:
    """Security constraint specifications."""

    read_only_root: bool = True
    no_new_privileges: bool = True
    drop_capabilities: List[str] = field(default_factory=lambda: ["ALL"])
    add_capabilities: List[str] = field(default_factory=list)
    seccomp_profile: Optional[str] = None
    apparmor_profile: Optional[str] = None
    user_id: int = 1000
    group_id: int = 1000

@dataclass
class ExecutionPolicy:
    """Complete execution policy specification."""

    name: str
    security_level: SecurityLevel
    network_policy: NetworkPolicy
    resource_limits: ResourceLimits
    security_constraints: SecurityConstraints
    allowed_images: Set[str] = field(default_factory=set)
    blocked_commands: Set[str] = field(default_factory=set)
    environment_whitelist: Set[str] = field(default_factory=set)
    mount_restrictions: Dict[str, Any] = field(default_factory=dict)
    audit_required: bool = True

class SecurityPolicyEngine:
    """
    Manages and enforces security policies for container execution.

    Provides policy definition, validation, and enforcement mechanisms
    to ensure secure container execution with proper isolation and
    resource management.
    """

    def __init__(self, policy_file: Optional[Path] = None):
        """Initialize security policy engine."""
        self.policies: Dict[str, ExecutionPolicy] = {}
        self.default_policy_name = "standard"

        # Load built-in policies
        self._load_builtin_policies()

        # Load custom policies if provided
        if policy_file and policy_file.exists():
            self._load_policies_from_file(policy_file)

    def _load_builtin_policies(self) -> None:
        """Load built-in security policies."""

        # Minimal security policy
        minimal_policy = ExecutionPolicy(
            name="minimal",
            security_level=SecurityLevel.MINIMAL,
            network_policy=NetworkPolicy.NONE,
            resource_limits=ResourceLimits(
                memory="256m",
                cpu="0.5",
                disk="500m",
                execution_time=900,  # 15 minutes
            ),
            security_constraints=SecurityConstraints(
                read_only_root=False,
                no_new_privileges=True,
                drop_capabilities=["NET_RAW", "SYS_ADMIN"],
                user_id=1000,
                group_id=1000,
            ),
            allowed_images={"python:3.11-slim", "node:18-alpine", "alpine:latest"},
            audit_required=False,
        )

        # Standard security policy (default)
        standard_policy = ExecutionPolicy(
            name="standard",
            security_level=SecurityLevel.STANDARD,
            network_policy=NetworkPolicy.NONE,
            resource_limits=ResourceLimits(),
            security_constraints=SecurityConstraints(),
            allowed_images={
                "python:3.11-slim",
                "node:18-alpine",
                "alpine:latest",
                "ubuntu:22.04",
                "debian:11-slim",
                "gadugi/python:test",
            },
            blocked_commands={
                "sudo",
                "su",
                "passwd",
                "chown",
                "chmod",
                "mount",
                "umount",
                "iptables",
                "systemctl",
                "service",
                "crontab",
                "at",
            },
        )

        # Hardened security policy
        hardened_policy = ExecutionPolicy(
            name="hardened",
            security_level=SecurityLevel.HARDENED,
            network_policy=NetworkPolicy.NONE,
            resource_limits=ResourceLimits(
                memory="256m",
                cpu="0.5",
                disk="500m",
                processes=512,
                open_files=512,
                execution_time=600,  # 10 minutes
            ),
            security_constraints=SecurityConstraints(
                read_only_root=True,
                no_new_privileges=True,
                drop_capabilities=["ALL"],
                seccomp_profile="runtime/default",
                user_id=65534,  # nobody user
                group_id=65534,
            ),
            allowed_images={"gcr.io/distroless/python3", "gcr.io/distroless/nodejs"},
            blocked_commands={
                "sudo",
                "su",
                "passwd",
                "chown",
                "chmod",
                "mount",
                "umount",
                "iptables",
                "systemctl",
                "service",
                "crontab",
                "at",
                "wget",
                "curl",
                "nc",
                "netcat",
                "telnet",
                "ssh",
                "scp",
                "rsync",
            },
            environment_whitelist={"PATH", "HOME", "USER", "LANG"},
            mount_restrictions={
                "tmpfs_only": True,
                "max_size": "100m",
                "no_exec": True,
                "no_suid": True,
            },
        )

        # Paranoid security policy
        paranoid_policy = ExecutionPolicy(
            name="paranoid",
            security_level=SecurityLevel.PARANOID,
            network_policy=NetworkPolicy.NONE,
            resource_limits=ResourceLimits(
                memory="128m",
                cpu="0.25",
                disk="100m",
                processes=64,
                open_files=64,
                execution_time=300,  # 5 minutes
            ),
            security_constraints=SecurityConstraints(
                read_only_root=True,
                no_new_privileges=True,
                drop_capabilities=["ALL"],
                seccomp_profile="runtime/default",
                apparmor_profile="docker-default",
                user_id=65534,
                group_id=65534,
            ),
            allowed_images={"scratch", "gcr.io/distroless/static"},
            blocked_commands=set(),  # All commands blocked by default
            environment_whitelist=set(),  # No environment variables allowed
            mount_restrictions={
                "tmpfs_only": True,
                "max_size": "50m",
                "no_exec": True,
                "no_suid": True,
                "no_dev": True,
            },
        )

        # Register all policies
        for policy in [
            minimal_policy,
            standard_policy,
            hardened_policy,
            paranoid_policy,
        ]:
            self.policies[policy.name] = policy

        logger.info(f"Loaded {len(self.policies)} built-in security policies")

    def _load_policies_from_file(self, policy_file: Path) -> None:
        """Load custom policies from YAML file."""
        try:
            with open(policy_file, "r") as f:
                policy_data = yaml.safe_load(f)

            for policy_name, policy_config in policy_data.get("policies", {}).items():
                policy = self._parse_policy_config(policy_name, policy_config)
                self.policies[policy_name] = policy

            logger.info(f"Loaded custom policies from {policy_file}")

        except Exception as e:
            raise GadugiError(f"Failed to load policies from {policy_file}: {e}")

    def _parse_policy_config(
        self, name: str, config: Dict[str, Any]
    ) -> ExecutionPolicy:
        """Parse policy configuration from dictionary."""
        try:
            # Parse resource limits
            resources = config.get("resources", {})
            resource_limits = ResourceLimits(
                memory=resources.get("memory", "512m"),
                cpu=resources.get("cpu", "1.0"),
                disk=resources.get("disk", "1g"),
                processes=resources.get("processes", 1024),
                open_files=resources.get("open_files", 1024),
                execution_time=resources.get("execution_time", 1800),
            )

            # Parse security constraints
            security = config.get("security", {})
            security_constraints = SecurityConstraints(
                read_only_root=security.get("read_only_root", True),
                no_new_privileges=security.get("no_new_privileges", True),
                drop_capabilities=security.get("drop_capabilities", ["ALL"]),
                add_capabilities=security.get("add_capabilities", []),
                seccomp_profile=security.get("seccomp_profile"),
                apparmor_profile=security.get("apparmor_profile"),
                user_id=security.get("user_id", 1000),
                group_id=security.get("group_id", 1000),
            )

            # Create policy
            policy = ExecutionPolicy(
                name=name,
                security_level=SecurityLevel(config.get("security_level", "standard")),
                network_policy=NetworkPolicy(config.get("network_policy", "none")),
                resource_limits=resource_limits,
                security_constraints=security_constraints,
                allowed_images=set(config.get("allowed_images", [])),
                blocked_commands=set(config.get("blocked_commands", [])),
                environment_whitelist=set(config.get("environment_whitelist", [])),
                mount_restrictions=config.get("mount_restrictions", {}),
                audit_required=config.get("audit_required", True),
            )

            return policy

        except Exception as e:
            raise GadugiError(f"Failed to parse policy configuration for {name}: {e}")

    def get_policy(self, policy_name: Optional[str] = None) -> ExecutionPolicy:
        """
        Get security policy by name.

        Args:
            policy_name: Name of policy to retrieve, defaults to default policy

        Returns:
            ExecutionPolicy object

        Raises:
            GadugiError: If policy not found
        """
        name = policy_name or self.default_policy_name

        if name not in self.policies:
            raise GadugiError(f"Security policy '{name}' not found")

        return self.policies[name]

    def validate_execution_request(
        self, image: str, command: List[str], policy_name: Optional[str] = None
    ) -> bool:
        """
        Validate if an execution request meets policy requirements.

        Args:
            image: Container image name
            command: Command to execute
            policy_name: Security policy to use

        Returns:
            True if request is valid

        Raises:
            GadugiError: If request violates policy
        """
        policy = self.get_policy(policy_name)

        # Check image whitelist with normalization
        if policy.allowed_images:
            normalized_image = self._normalize_image_reference(image)
            normalized_allowed = set(
                self._normalize_image_reference(img) for img in policy.allowed_images
            )
            if normalized_image not in normalized_allowed:
                raise GadugiError(
                    f"Image '{image}' not allowed by policy '{policy.name}'"
                )

        # Check command blacklist
        if command and policy.blocked_commands:
            for cmd_part in command:
                if isinstance(cmd_part, str):
                    # Check if any part of the command is blocked
                    for blocked in policy.blocked_commands:
                        if blocked in cmd_part:
                            raise GadugiError(
                                f"Command contains blocked element '{blocked}'"
                            )

        return True

    def _normalize_image_reference(self, image: str) -> str:
        """Normalize Docker image reference for comparison."""
        # Handle special case for empty or None
        if not image:
            return ""

        # Strip whitespace
        image = image.strip()

        # Add default tag if missing
        if ":" not in image:
            image = f"{image}:latest"

        # Handle registry prefix normalization
        # docker.io/library/image:tag -> library/image:tag
        if image.startswith("docker.io/"):
            image = image.removeprefix("docker.io/")

        # Official images on Docker Hub are in the library namespace
        if "/" not in image.split(":")[0]:
            image = f"library/{image}"

        return image

    def apply_policy_to_container_config(
        self, base_config: Dict[str, Any], policy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply security policy to container configuration.

        Args:
            base_config: Base container configuration
            policy_name: Security policy to apply

        Returns:
            Modified container configuration with policy applied
        """
        policy = self.get_policy(policy_name)
        config = base_config.copy()

        # Apply resource limits
        config["mem_limit"] = policy.resource_limits.memory
        config["cpu_count"] = float(policy.resource_limits.cpu)

        # Apply security constraints
        config["read_only"] = policy.security_constraints.read_only_root
        config["user"] = (
            f"{policy.security_constraints.user_id}:{policy.security_constraints.group_id}"
        )

        # Security options
        security_opt = config.get("security_opt", [])
        if policy.security_constraints.no_new_privileges:
            security_opt.append("no-new-privileges:true")
        if policy.security_constraints.seccomp_profile:
            security_opt.append(
                f"seccomp={policy.security_constraints.seccomp_profile}"
            )
        if policy.security_constraints.apparmor_profile:
            security_opt.append(
                f"apparmor={policy.security_constraints.apparmor_profile}"
            )
        config["security_opt"] = security_opt

        # Capabilities
        config["cap_drop"] = policy.security_constraints.drop_capabilities
        if policy.security_constraints.add_capabilities:
            config["cap_add"] = policy.security_constraints.add_capabilities

        # Network policy
        if policy.network_policy == NetworkPolicy.NONE:
            config["network_mode"] = "none"
        elif policy.network_policy == NetworkPolicy.INTERNAL:
            config["network_mode"] = "bridge"

        # Process limits
        ulimits = config.get("ulimits", [])
        ulimits.extend(
            [
                {
                    "Name": "nproc",
                    "Soft": policy.resource_limits.processes,
                    "Hard": policy.resource_limits.processes,
                },
                {
                    "Name": "nofile",
                    "Soft": policy.resource_limits.open_files,
                    "Hard": policy.resource_limits.open_files,
                },
            ]
        )
        config["ulimits"] = ulimits

        # Environment variable filtering
        if policy.environment_whitelist:
            env = config.get("environment", {})
            config["environment"] = {
                k: v for k, v in env.items() if k in policy.environment_whitelist
            }

        # Mount restrictions
        if policy.mount_restrictions.get("tmpfs_only"):
            tmpfs_config = "rw"
            if policy.mount_restrictions.get("no_exec"):
                tmpfs_config += ",noexec"
            if policy.mount_restrictions.get("no_suid"):
                tmpfs_config += ",nosuid"
            if policy.mount_restrictions.get("no_dev"):
                tmpfs_config += ",nodev"

            max_size = policy.mount_restrictions.get("max_size", "100m")
            tmpfs_config += f",size={max_size}"

            config["tmpfs"] = {"/tmp": tmpfs_config}

        return config

    def list_policies(self) -> List[str]:
        """List all available policy names."""
        return list(self.policies.keys())

    def get_policy_summary(self, policy_name: str) -> Dict[str, Any]:
        """Get summary information about a policy."""
        policy = self.get_policy(policy_name)

        return {
            "name": policy.name,
            "security_level": policy.security_level.value,
            "network_policy": policy.network_policy.value,
            "memory_limit": policy.resource_limits.memory,
            "cpu_limit": policy.resource_limits.cpu,
            "execution_timeout": policy.resource_limits.execution_time,
            "read_only_root": policy.security_constraints.read_only_root,
            "allowed_images": len(policy.allowed_images),
            "blocked_commands": len(policy.blocked_commands),
            "audit_required": policy.audit_required,
        }

    def export_policy(self, policy_name: str) -> Dict[str, Any]:
        """Export policy configuration as dictionary."""
        policy = self.get_policy(policy_name)

        return {
            "name": policy.name,
            "security_level": policy.security_level.value,
            "network_policy": policy.network_policy.value,
            "resources": {
                "memory": policy.resource_limits.memory,
                "cpu": policy.resource_limits.cpu,
                "disk": policy.resource_limits.disk,
                "processes": policy.resource_limits.processes,
                "open_files": policy.resource_limits.open_files,
                "execution_time": policy.resource_limits.execution_time,
            },
            "security": {
                "read_only_root": policy.security_constraints.read_only_root,
                "no_new_privileges": policy.security_constraints.no_new_privileges,
                "drop_capabilities": policy.security_constraints.drop_capabilities,
                "add_capabilities": policy.security_constraints.add_capabilities,
                "seccomp_profile": policy.security_constraints.seccomp_profile,
                "apparmor_profile": policy.security_constraints.apparmor_profile,
                "user_id": policy.security_constraints.user_id,
                "group_id": policy.security_constraints.group_id,
            },
            "allowed_images": list(policy.allowed_images),
            "blocked_commands": list(policy.blocked_commands),
            "environment_whitelist": list(policy.environment_whitelist),
            "mount_restrictions": policy.mount_restrictions,
            "audit_required": policy.audit_required,
        }
