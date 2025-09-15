"""
Tests for Security Policy Engine.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import container_runtime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import patch, mock_open

from container_runtime.security_policy import (
    SecurityPolicyEngine,
    ExecutionPolicy,
    SecurityLevel,
    NetworkPolicy,
    ResourceLimits,
    SecurityConstraints,
)


@pytest.fixture
def policy_engine():
    """Security policy engine fixture."""
    return SecurityPolicyEngine()


@pytest.fixture
def sample_policy_yaml():
    """Sample policy YAML configuration."""
    return """
policies:
  test_policy:
    security_level: "hardened"
    network_policy: "none"
    resources:
      memory: "128m"
      cpu: "0.25"
      disk: "100m"
      execution_time: 300
    security:
      read_only_root: true
      no_new_privileges: true
      drop_capabilities: ["ALL"]
      user_id: 65534
      group_id: 65534
    allowed_images:
      - "python:3.11-slim"
      - "alpine:latest"
    blocked_commands:
      - "sudo"
      - "wget"
    environment_whitelist:
      - "PATH"
      - "HOME"
    audit_required: true
"""


def test_policy_engine_initialization():
    """Test policy engine initialization."""
    engine = SecurityPolicyEngine()

    # Should have built-in policies loaded
    assert len(engine.policies) > 0
    assert "standard" in engine.policies
    assert "minimal" in engine.policies
    assert "hardened" in engine.policies
    assert "paranoid" in engine.policies
    assert engine.default_policy_name == "standard"


def test_policy_engine_with_custom_file(sample_policy_yaml):
    """Test policy engine with custom policy file."""
    with patch("builtins.open", mock_open(read_data=sample_policy_yaml)):
        with patch("pathlib.Path.exists", return_value=True):
            engine = SecurityPolicyEngine(policy_file=Path("test_policies.yaml"))

    # Should have built-in policies plus custom policy
    assert "test_policy" in engine.policies

    policy = engine.get_policy("test_policy")
    assert policy.security_level == SecurityLevel.HARDENED
    assert policy.network_policy == NetworkPolicy.NONE
    assert policy.resource_limits.memory == "128m"


def test_builtin_policies(policy_engine):
    """Test built-in security policies."""

    # Test minimal policy
    minimal = policy_engine.get_policy("minimal")
    assert minimal.security_level == SecurityLevel.MINIMAL
    assert minimal.resource_limits.memory == "256m"
    assert not minimal.security_constraints.read_only_root

    # Test standard policy
    standard = policy_engine.get_policy("standard")
    assert standard.security_level == SecurityLevel.STANDARD
    assert standard.resource_limits.memory == "512m"
    assert standard.security_constraints.read_only_root

    # Test hardened policy
    hardened = policy_engine.get_policy("hardened")
    assert hardened.security_level == SecurityLevel.HARDENED
    assert hardened.resource_limits.memory == "256m"
    assert hardened.security_constraints.user_id == 65534

    # Test paranoid policy
    paranoid = policy_engine.get_policy("paranoid")
    assert paranoid.security_level == SecurityLevel.PARANOID
    assert paranoid.resource_limits.memory == "128m"
    assert len(paranoid.allowed_images) == 2  # scratch and distroless/static


def test_get_policy_default(policy_engine):
    """Test getting default policy."""
    policy = policy_engine.get_policy()
    assert policy.name == "standard"


def test_get_policy_not_found(policy_engine):
    """Test getting non-existent policy."""
    with pytest.raises(Exception, match="Security policy 'nonexistent' not found"):
        policy_engine.get_policy("nonexistent")


def test_validate_execution_request_allowed(policy_engine):
    """Test validation of allowed execution request."""
    # Should not raise exception
    result = policy_engine.validate_execution_request(
        image="python:3.11-slim",
        command=["python", "-c", "print('hello')"],
        policy_name="standard",
    )
    assert result is True


def test_validate_execution_request_blocked_image(policy_engine):
    """Test validation with blocked image."""
    with pytest.raises(Exception, match="Image .* not allowed by policy"):
        policy_engine.validate_execution_request(
            image="malicious:latest",
            command=["python", "-c", "print('hello')"],
            policy_name="hardened",
        )


def test_validate_execution_request_blocked_command(policy_engine):
    """Test validation with blocked command."""
    with pytest.raises(Exception, match="Command contains blocked element"):
        policy_engine.validate_execution_request(
            image="python:3.11-slim",
            command=["sudo", "rm", "-rf", "/"],
            policy_name="standard",
        )


def test_apply_policy_to_container_config(policy_engine):
    """Test applying policy to container configuration."""
    base_config = {
        "image": "python:3.11-slim",
        "command": ["python", "script.py"],
        "environment": {"PATH": "/usr/bin", "SECRET": "hidden"},
    }

    # Apply standard policy
    config = policy_engine.apply_policy_to_container_config(base_config, "standard")

    assert config["mem_limit"] == "512m"  # type: ignore[index]
    assert config["cpu_count"] == 1.0  # type: ignore[index]
    assert config["read_only"] is True  # type: ignore[index]
    assert config["user"] == "1000:1000"  # type: ignore[index]
    assert "no-new-privileges:true" in config["security_opt"]  # type: ignore[index]
    assert config["cap_drop"] == ["ALL"]  # type: ignore[index]


def test_apply_hardened_policy_to_container_config(policy_engine):
    """Test applying hardened policy to container configuration."""
    base_config = {
        "image": "gcr.io/distroless/python3",
        "command": ["python", "script.py"],
        "environment": {"PATH": "/usr/bin", "HOME": "/home/user", "SECRET": "hidden"},
    }

    # Apply hardened policy
    config = policy_engine.apply_policy_to_container_config(base_config, "hardened")

    assert config["mem_limit"] == "256m"  # type: ignore[index]
    assert config["cpu_count"] == 0.5  # type: ignore[index]
    assert config["user"] == "65534:65534"  # type: ignore[index]
    assert config["network_mode"] == "none"  # type: ignore[index]

    # Environment should be filtered
    assert "PATH" in config["environment"]  # type: ignore[index]
    assert "HOME" in config["environment"]  # type: ignore[index]
    assert "SECRET" not in config["environment"]  # Not in whitelist  # type: ignore[index]

    # Should have tmpfs configuration
    assert "/tmp" in config["tmpfs"]  # type: ignore[index]
    assert "noexec" in config["tmpfs"]["/tmp"]  # type: ignore[index]


def test_list_policies(policy_engine):
    """Test listing available policies."""
    policies = policy_engine.list_policies()

    assert isinstance(policies, list)
    assert len(policies) >= 4  # At least the built-in policies
    assert "minimal" in policies
    assert "standard" in policies
    assert "hardened" in policies
    assert "paranoid" in policies


def test_get_policy_summary(policy_engine):
    """Test getting policy summary."""
    summary = policy_engine.get_policy_summary("standard")

    assert summary["name"] == "standard"  # type: ignore[index]
    assert summary["security_level"] == "standard"  # type: ignore[index]
    assert summary["network_policy"] == "none"  # type: ignore[index]
    assert summary["memory_limit"] == "512m"  # type: ignore[index]
    assert summary["cpu_limit"] == "1.0"  # type: ignore[index]
    assert isinstance(summary["execution_timeout"], int)  # type: ignore[index]
    assert isinstance(summary["read_only_root"], bool)  # type: ignore[index]
    assert isinstance(summary["allowed_images"], int)  # type: ignore[index]
    assert isinstance(summary["blocked_commands"], int)  # type: ignore[index]
    assert isinstance(summary["audit_required"], bool)  # type: ignore[index]


def test_export_policy(policy_engine):
    """Test exporting policy configuration."""
    exported = policy_engine.export_policy("standard")

    assert exported["name"] == "standard"  # type: ignore[index]
    assert exported["security_level"] == "standard"  # type: ignore[index]
    assert "resources" in exported
    assert "security" in exported
    assert "allowed_images" in exported
    assert "blocked_commands" in exported

    # Resources section
    assert exported["resources"]["memory"] == "512m"  # type: ignore[index]
    assert exported["resources"]["cpu"] == "1.0"  # type: ignore[index]

    # Security section
    assert exported["security"]["read_only_root"] is True  # type: ignore[index]
    assert exported["security"]["user_id"] == 1000  # type: ignore[index]


def test_parse_policy_config_invalid():
    """Test parsing invalid policy configuration."""
    engine = SecurityPolicyEngine()

    invalid_config = {
        "security_level": "invalid_level"  # Invalid enum value
    }

    with pytest.raises(Exception):
        engine._parse_policy_config("invalid", invalid_config)


def test_resource_limits_dataclass():
    """Test ResourceLimits dataclass."""
    limits = ResourceLimits(
        memory="1g",
        cpu="2.0",
        disk="5g",
        processes=2048,
        open_files=2048,
        execution_time=3600,
    )

    assert limits.memory == "1g"
    assert limits.cpu == "2.0"
    assert limits.execution_time == 3600


def test_security_constraints_dataclass():
    """Test SecurityConstraints dataclass."""
    constraints = SecurityConstraints(
        read_only_root=False,
        no_new_privileges=False,
        drop_capabilities=["NET_RAW"],
        add_capabilities=["SYS_TIME"],
        user_id=500,
        group_id=500,
    )

    assert constraints.read_only_root is False
    assert constraints.drop_capabilities == ["NET_RAW"]
    assert constraints.add_capabilities == ["SYS_TIME"]
    assert constraints.user_id == 500


def test_execution_policy_dataclass():
    """Test ExecutionPolicy dataclass."""
    policy = ExecutionPolicy(
        name="test",
        security_level=SecurityLevel.STANDARD,
        network_policy=NetworkPolicy.NONE,
        resource_limits=ResourceLimits(),
        security_constraints=SecurityConstraints(),
        allowed_images={"python:3.11"},
        blocked_commands={"rm"},
        audit_required=True,
    )

    assert policy.name == "test"
    assert policy.security_level == SecurityLevel.STANDARD
    assert "python:3.11" in policy.allowed_images
    assert "rm" in policy.blocked_commands


def test_network_policy_enum():
    """Test NetworkPolicy enum values."""
    assert NetworkPolicy.NONE.value == "none"
    assert NetworkPolicy.INTERNAL.value == "internal"
    assert NetworkPolicy.LIMITED.value == "limited"
    assert NetworkPolicy.FULL.value == "full"


def test_security_level_enum():
    """Test SecurityLevel enum values."""
    assert SecurityLevel.MINIMAL.value == "minimal"
    assert SecurityLevel.STANDARD.value == "standard"
    assert SecurityLevel.HARDENED.value == "hardened"
    assert SecurityLevel.PARANOID.value == "paranoid"


def test_load_policies_from_invalid_file():
    """Test loading policies from invalid file."""
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
        with patch("pathlib.Path.exists", return_value=True):
            with pytest.raises(Exception, match="Failed to load policies"):
                SecurityPolicyEngine(policy_file=Path("invalid.yaml"))


def test_policy_engine_file_not_exists():
    """Test policy engine with non-existent file."""
    with patch("pathlib.Path.exists", return_value=False):
        # Should not raise exception, just skip loading custom policies
        engine = SecurityPolicyEngine(policy_file=Path("nonexistent.yaml"))

        # Should still have built-in policies
        assert len(engine.policies) >= 4
