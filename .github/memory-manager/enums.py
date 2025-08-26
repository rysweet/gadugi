#!/usr/bin/env python3
"""
Common enums for Memory Manager components
"""

from enum import Enum


class SyncDirection(Enum):
    """Synchronization direction"""
    MEMORY_TO_GITHUB = "memory_to_github"
    GITHUB_TO_MEMORY = "github_to_memory"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    MANUAL = "manual"
    MEMORY_WINS = "memory_wins"
    GITHUB_WINS = "github_wins"
    LATEST_WINS = "latest_wins"
    AUTO_MERGE = "auto_merge"