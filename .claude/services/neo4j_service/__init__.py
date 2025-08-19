"""
Neo4j Service for Gadugi v0.3

Provides Neo4j database connectivity and operations for the Gadugi system.
"""

from .client import Neo4jClient
from .models import (
    Agent,
    Tool,
    Context,
    Workflow,
    Recipe,
    Neo4jEntityBase,
)
from .schema import SchemaManager

__all__ = [
    "Neo4jClient",
    "Agent",
    "Tool",
    "Context",
    "Workflow",
    "Recipe",
    "Neo4jEntityBase",
    "SchemaManager",
]
