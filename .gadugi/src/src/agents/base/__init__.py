"""
Base agent classes and interfaces for the Gadugi agent framework.

This package provides the foundational classes and utilities for building agents.
"""

from .v03_agent import V03Agent
from .whiteboard_collaboration import WhiteboardManager, SharedWhiteboard, AccessLevel

__all__ = ["V03Agent", "WhiteboardManager", "SharedWhiteboard", "AccessLevel"]
