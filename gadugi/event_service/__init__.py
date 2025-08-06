"""
Gadugi Event-Driven Agent Invocation Service

This package provides the core event-driven service for the Gadugi multi-agent system.
It handles GitHub webhooks, local events, and agent invocation coordination.
"""

__version__ = "0.1.0"
__author__ = "Gadugi Development Team"

from .service import GadugiEventService
from .handlers import EventHandler, EventFilter
from .config import ServiceConfig, load_config, save_config
from .events import Event, GitHubEvent, LocalEvent, AgentEvent

__all__ = [
    "GadugiEventService",
    "EventHandler", 
    "EventFilter",
    "ServiceConfig",
    "load_config",
    "save_config",
    "Event",
    "GitHubEvent",
    "LocalEvent", 
    "AgentEvent",
]