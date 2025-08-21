"""Memory Control Protocol (MCP) Service for Gadugi v0.3.

Provides intelligent memory management and context persistence for agents.
"""

from .cache import LRUCache, CacheEntry
from .mcp_service import MCPService, app
from .models import (
    Memory,
    MemoryType,
    Context,
    ContextState,
    MemorySearchRequest,
    MemorySearchResponse,
    ContextSaveRequest,
    ContextLoadResponse,
)
from .neo4j_client import Neo4jMemoryClient

__all__ = [
    "MCPService",
    "app",
    "Memory",
    "MemoryType",
    "Context",
    "ContextState",
    "MemorySearchRequest",
    "MemorySearchResponse",
    "ContextSaveRequest",
    "ContextLoadResponse",
    "LRUCache",
    "CacheEntry",
    "Neo4jMemoryClient",
]

__version__ = "0.3.0"