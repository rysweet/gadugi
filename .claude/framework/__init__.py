"""Agent Framework for Gadugi Platform.

Provides the foundational framework for all agents including base classes,
event handling, tool invocation, and memory integration.
"""

from .base_agent import BaseAgent, AgentMetadata, AgentResponse
from .frontmatter_parser import parse_agent_definition
from .tool_registry import ToolRegistry, Tool

__all__ = [
    "BaseAgent",
    "AgentMetadata",
    "AgentResponse",
    "parse_agent_definition",
    "ToolRegistry",
    "Tool",
]