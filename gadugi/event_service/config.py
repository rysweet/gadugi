"""
Configuration management for Gadugi Event Service

Handles loading, validation, and saving of service configuration.
"""

import os
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class LogConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "text"
    output: str = "stdout"
    file_path: Optional[str] = None
    enable_audit: bool = True
    audit_file_path: Optional[str] = None


@dataclass
class AgentInvocation:
    """Agent invocation configuration."""

    agent_name: str
    method: str = "claude_cli"
    parameters: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    prompt_template: str = ""


@dataclass
class GitHubFilter:
    """GitHub-specific event filtering."""

    repositories: List[str] = field(default_factory=list)
    webhook_events: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    refs: List[str] = field(default_factory=list)
    milestones: List[str] = field(default_factory=list)


@dataclass
class EventFilter:
    """Event filtering configuration."""

    event_types: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    metadata_match: Dict[str, str] = field(default_factory=dict)
    github_filter: Optional[GitHubFilter] = None


@dataclass
class EventHandlerConfig:
    """Event handler configuration."""

    name: str
    filter: Dict[str, Any]
    invocation: Dict[str, Any]
    enabled: bool = True
    priority: int = 100
    timeout_seconds: int = 300
    async_execution: bool = False


@dataclass
class ServiceConfig:
    """Main service configuration."""

    service_name: str = "gadugi-event-service"
    bind_address: str = "127.0.0.1"
    bind_port: int = 8080
    socket_path: Optional[str] = None
    poll_interval_seconds: int = 300  # 5 minutes
    github_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    handlers: List[EventHandlerConfig] = field(default_factory=list)
    log_config: LogConfig = field(default_factory=LogConfig)


def get_default_config_path() -> str:
    """Get the default configuration file path."""
    config_dir = Path.home() / ".gadugi"
    config_dir.mkdir(exist_ok=True)
    return str(config_dir / "config.yaml")


def get_default_socket_path() -> str:
    """Get the default Unix socket path."""
    socket_dir = Path.home() / ".gadugi"
    socket_dir.mkdir(exist_ok=True)
    return str(socket_dir / "events.sock")


def get_default_log_path() -> str:
    """Get the default log file path."""
    log_dir = Path.home() / ".gadugi" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / "gadugi-service.log")


def get_default_audit_log_path() -> str:
    """Get the default audit log file path."""
    log_dir = Path.home() / ".gadugi" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / "gadugi-audit.log")


def create_default_config() -> ServiceConfig:
    """Create a default service configuration."""
    return ServiceConfig(
        socket_path=get_default_socket_path(),
        github_token=os.getenv("GITHUB_TOKEN"),
        webhook_secret=os.getenv("GADUGI_WEBHOOK_SECRET"),
        log_config=LogConfig(
            file_path=get_default_log_path(),
            audit_file_path=get_default_audit_log_path(),
        ),
        handlers=[
            # Default handler for new issues
            EventHandlerConfig(
                name="new-issue-workflow",
                filter={
                    "event_types": ["github.issues.opened"],
                    "github_filter": {
                        "webhook_events": ["issues"],
                        "actions": ["opened"],
                    },
                },
                invocation={
                    "agent_name": "workflow-manager",
                    "method": "claude_cli",
                    "prompt_template": "New issue #{number}: {title}\n\nAnalyze and create workflow for this issue.",
                },
                priority=100,
                timeout_seconds=600,
            ),
            # Default handler for new PRs
            EventHandlerConfig(
                name="new-pr-review",
                filter={
                    "event_types": ["github.pull_request.opened"],
                    "github_filter": {
                        "webhook_events": ["pull_request"],
                        "actions": ["opened"],
                    },
                },
                invocation={
                    "agent_name": "code-reviewer",
                    "method": "claude_cli",
                    "prompt_template": "Review PR #{number}: {title}\n\nPerform comprehensive code review.",
                },
                priority=90,
                timeout_seconds=900,
            ),
            # Default handler for merges to main
            EventHandlerConfig(
                name="main-merge-memory-update",
                filter={
                    "event_types": ["github.push"],
                    "github_filter": {
                        "webhook_events": ["push"],
                        "refs": ["refs/heads/main"],
                    },
                },
                invocation={
                    "agent_name": "memory-manager",
                    "method": "claude_cli",
                    "prompt_template": "Update Memory.md after merge to main: {ref}\n\nSynchronize project memory with latest changes.",
                },
                priority=80,
                timeout_seconds=300,
            ),
        ],
    )


def load_config(config_path: Optional[str] = None) -> ServiceConfig:
    """Load service configuration from file or create default."""
    if config_path is None:
        config_path = get_default_config_path()

    config_file = Path(config_path)

    if config_file.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            # Convert to ServiceConfig object
            config = _dict_to_config(config_data)
            _validate_config(config)
            return config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            return create_default_config()
    else:
        logger.info(f"Configuration file not found at {config_path}, using defaults")
        config = create_default_config()

        # Save default config for future use
        try:
            save_config(config, config_path)
            logger.info(f"Saved default configuration to {config_path}")
        except Exception as e:
            logger.warning(f"Could not save default configuration: {e}")

        return config


def save_config(config: ServiceConfig, config_path: Optional[str] = None) -> None:
    """Save service configuration to file."""
    if config_path is None:
        config_path = get_default_config_path()

    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dictionary
    config_data = _config_to_dict(config)

    with open(config_file, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)

    logger.info(f"Configuration saved to {config_path}")


def _dict_to_config(data: Dict[str, Any]) -> ServiceConfig:
    """Convert dictionary to ServiceConfig object."""
    # Handle log_config
    log_config_data = data.get("log_config", {})
    log_config = LogConfig(**log_config_data)

    # Handle handlers
    handlers_data = data.get("handlers", [])
    handlers = []
    for handler_data in handlers_data:
        handler = EventHandlerConfig(**handler_data)
        handlers.append(handler)

    # Create main config
    config_data = dict(data)
    config_data["log_config"] = log_config
    config_data["handlers"] = handlers

    return ServiceConfig(**config_data)


def _config_to_dict(config: ServiceConfig) -> Dict[str, Any]:
    """Convert ServiceConfig object to dictionary."""
    data = asdict(config)

    # Remove None values for cleaner YAML
    def remove_none(obj):
        if isinstance(obj, dict):
            return {k: remove_none(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_none(item) for item in obj]
        else:
            return obj

    return remove_none(data)


def _validate_config(config: ServiceConfig) -> None:
    """Validate service configuration."""
    errors = []

    # Validate bind port
    if not (1 <= config.bind_port <= 65535):
        errors.append(f"Invalid bind_port: {config.bind_port}")

    # Validate poll interval
    if config.poll_interval_seconds < 0:
        errors.append(f"Invalid poll_interval_seconds: {config.poll_interval_seconds}")

    # Validate handlers
    for i, handler in enumerate(config.handlers):
        if not handler.name:
            errors.append(f"Handler {i} missing name")

        if handler.timeout_seconds <= 0:
            errors.append(
                f"Handler {handler.name} has invalid timeout: {handler.timeout_seconds}"
            )

        if not handler.invocation.get("agent_name"):
            errors.append(f"Handler {handler.name} missing agent_name")

    if errors:
        raise ValueError(f"Configuration validation errors: {', '.join(errors)}")


# Environment variable configuration
def load_config_from_env() -> Dict[str, Any]:
    """Load configuration overrides from environment variables."""
    env_config = {}

    # Service settings
    if "GADUGI_BIND_ADDRESS" in os.environ:
        env_config["bind_address"] = os.environ["GADUGI_BIND_ADDRESS"]

    if "GADUGI_BIND_PORT" in os.environ:
        env_config["bind_port"] = int(os.environ["GADUGI_BIND_PORT"])

    if "GADUGI_SOCKET_PATH" in os.environ:
        env_config["socket_path"] = os.environ["GADUGI_SOCKET_PATH"]

    if "GADUGI_POLL_INTERVAL" in os.environ:
        env_config["poll_interval_seconds"] = int(os.environ["GADUGI_POLL_INTERVAL"])

    # GitHub settings
    if "GITHUB_TOKEN" in os.environ:
        env_config["github_token"] = os.environ["GITHUB_TOKEN"]

    if "GADUGI_WEBHOOK_SECRET" in os.environ:
        env_config["webhook_secret"] = os.environ["GADUGI_WEBHOOK_SECRET"]

    # Logging settings
    log_config = {}
    if "GADUGI_LOG_LEVEL" in os.environ:
        log_config["level"] = os.environ["GADUGI_LOG_LEVEL"]

    if "GADUGI_LOG_FILE" in os.environ:
        log_config["file_path"] = os.environ["GADUGI_LOG_FILE"]
        log_config["output"] = "file"

    if log_config:
        env_config["log_config"] = log_config

    return env_config


def merge_config_with_env(config: ServiceConfig) -> ServiceConfig:
    """Merge configuration with environment variable overrides."""
    env_overrides = load_config_from_env()

    if not env_overrides:
        return config

    logger.info(f"Applying environment overrides: {list(env_overrides.keys())}")

    # Convert config to dict, merge, convert back
    config_dict = _config_to_dict(config)

    def deep_merge(base_dict: Dict, override_dict: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base_dict.copy()
        for key, value in override_dict.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    merged_dict = deep_merge(config_dict, env_overrides)
    return _dict_to_config(merged_dict)
