"""Configuration models for the event service."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentInvocation:
    """Configuration for invoking an agent."""
    agent_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 60
    retry_count: int = 0
    retry_delay_seconds: int = 5
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AgentInvocation':
        """Create invocation from configuration dictionary."""
        return cls(
            agent_name=config.get('agent_name', ''),
            parameters=config.get('parameters', {}),
            environment=config.get('environment', {}),
            timeout_seconds=config.get('timeout_seconds', 60),
            retry_count=config.get('retry_count', 0),
            retry_delay_seconds=config.get('retry_delay_seconds', 5)
        )


@dataclass
class EventServiceConfig:
    """Configuration for the event service."""
    service_name: str = "event-service"
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    max_workers: int = 10
    event_buffer_size: int = 1000
    persistence_enabled: bool = False
    persistence_path: str = "/tmp/event-service"
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'EventServiceConfig':
        """Create configuration from dictionary."""
        return cls(
            service_name=config.get('service_name', 'event-service'),
            host=config.get('host', 'localhost'),
            port=config.get('port', 8000),
            debug=config.get('debug', False),
            max_workers=config.get('max_workers', 10),
            event_buffer_size=config.get('event_buffer_size', 1000),
            persistence_enabled=config.get('persistence_enabled', False),
            persistence_path=config.get('persistence_path', '/tmp/event-service')
        )