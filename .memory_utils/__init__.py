"""
Hierarchical Memory System Utilities

This package provides utilities for the Gadugi memory system:
- memory_manager: Core file operations and memory management
- agent_interface: Agent-specific memory access with permissions
- security_manager: XPIA protection and secrets scanning
- migration_tool: Migration from old Memory.md system
"""

from .memory_manager import MemoryManager, MemoryLevel, MemoryEntry, MemorySection
from .agent_interface import (
    AgentMemoryInterface,
    AgentPermissions,
    get_memory_interface,
)
from .security_manager import SecurityManager, SecurityResult

__all__ = [
    "MemoryManager",
    "MemoryLevel",
    "MemoryEntry",
    "MemorySection",
    "AgentMemoryInterface",
    "AgentPermissions",
    "get_memory_interface",
    "SecurityManager",
    "SecurityResult",
]
