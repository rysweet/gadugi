"""
Whiteboard Collaboration System for V0.3 Agents
================================================

Provides shared whiteboard functionality for multi-agent collaboration.
Agents can share information, coordinate tasks, and make collective decisions.
"""

import asyncio
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import hashlib
from pathlib import Path

# Import memory backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.memory.sqlite_memory_backend import SQLiteMemoryBackend


class AccessLevel(Enum):
    """Whiteboard access levels."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class WhiteboardType(Enum):
    """Standard whiteboard types."""
    TASK_COORDINATION = "task_coordination"
    DESIGN_DECISION = "design_decision"
    PROBLEM_SOLVING = "problem_solving"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    STATUS_TRACKING = "status_tracking"


@dataclass
class WhiteboardEntry:
    """Single entry on a whiteboard."""
    entry_id: str
    agent_id: str
    content: Dict[str, Any]
    timestamp: datetime
    version: int
    tags: List[str] = field(default_factory=list)


@dataclass
class WhiteboardVersion:
    """Version snapshot of whiteboard state."""
    version: int
    timestamp: datetime
    entries: List[WhiteboardEntry]
    modified_by: str
    change_description: str


class SharedWhiteboard:
    """
    Shared whiteboard for multi-agent collaboration.
    Provides versioning, access control, and conflict resolution.
    """

    def __init__(
        self,
        whiteboard_id: str,
        whiteboard_type: WhiteboardType,
        owner_agent: str,
        backend: Optional[SQLiteMemoryBackend] = None
    ):
        """Initialize shared whiteboard."""
        self.whiteboard_id = whiteboard_id
        self.whiteboard_type = whiteboard_type
        self.owner_agent = owner_agent
        self.backend = backend or SQLiteMemoryBackend()

        # Access control
        self.permissions: Dict[str, AccessLevel] = {
            owner_agent: AccessLevel.ADMIN
        }

        # Versioning
        self.current_version = 0
        self.version_history: List[WhiteboardVersion] = []

        # Content
        self.entries: Dict[str, WhiteboardEntry] = {}

        # Concurrency control
        self._lock = threading.RLock()
        self._update_locks: Dict[str, threading.Lock] = {}

        # Subscriptions
        self._subscribers: Dict[str, Callable] = {}

        # Metadata
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.metadata: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize whiteboard in backend."""
        if not hasattr(self.backend, '_initialized'):
            await self.backend.initialize()
            self.backend._initialized = True

        # Create whiteboard in backend
        await self.backend.create_whiteboard(self.whiteboard_id, self.owner_agent)

    def grant_access(self, agent_id: str, level: AccessLevel):
        """Grant access to an agent."""
        with self._lock:
            self.permissions[agent_id] = level

    def revoke_access(self, agent_id: str):
        """Revoke access from an agent."""
        with self._lock:
            if agent_id in self.permissions and agent_id != self.owner_agent:
                del self.permissions[agent_id]

    def check_access(self, agent_id: str, required_level: AccessLevel) -> bool:
        """Check if agent has required access level."""
        agent_level = self.permissions.get(agent_id)
        if not agent_level:
            return False

        # Admin has all permissions
        if agent_level == AccessLevel.ADMIN:
            return True

        # Write has read and write
        if agent_level == AccessLevel.WRITE:
            return required_level in [AccessLevel.READ, AccessLevel.WRITE]

        # Read only has read
        return required_level == AccessLevel.READ

    async def write(
        self,
        agent_id: str,
        key: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Write content to whiteboard.

        Args:
            agent_id: ID of agent writing
            key: Key for the content
            content: Content to write
            tags: Optional tags for the entry

        Returns:
            True if successful
        """
        if not self.check_access(agent_id, AccessLevel.WRITE):
            raise PermissionError(f"Agent {agent_id} lacks write access")

        with self._lock:
            # Create entry
            entry_id = f"{key}_{datetime.now().timestamp()}"
            entry = WhiteboardEntry(
                entry_id=entry_id,
                agent_id=agent_id,
                content={key: content},
                timestamp=datetime.now(),
                version=self.current_version + 1,
                tags=tags or []
            )

            # Store entry
            self.entries[key] = entry

            # Update version
            self._create_version_snapshot(agent_id, f"Updated {key}")

            # Update backend
            await self.backend.update_whiteboard(
                self.whiteboard_id,
                content={key: content}
            )

            # Notify subscribers
            await self._notify_subscribers(key, content, agent_id)

            self.last_modified = datetime.now()
            return True

    async def read(
        self,
        agent_id: str,
        key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Read content from whiteboard.

        Args:
            agent_id: ID of agent reading
            key: Optional specific key to read

        Returns:
            Content or None
        """
        if not self.check_access(agent_id, AccessLevel.READ):
            raise PermissionError(f"Agent {agent_id} lacks read access")

        with self._lock:
            if key:
                entry = self.entries.get(key)
                return entry.content if entry else None
            else:
                # Return all content
                return {
                    key: entry.content[key]
                    for key, entry in self.entries.items()
                    if key in entry.content
                }

    async def update_atomic(
        self,
        agent_id: str,
        key: str,
        update_func: Callable[[Any], Any]
    ) -> bool:
        """
        Atomically update a value.

        Args:
            agent_id: ID of agent updating
            key: Key to update
            update_func: Function to apply to current value

        Returns:
            True if successful
        """
        if not self.check_access(agent_id, AccessLevel.WRITE):
            raise PermissionError(f"Agent {agent_id} lacks write access")

        # Get or create lock for this key
        if key not in self._update_locks:
            self._update_locks[key] = threading.Lock()

        with self._update_locks[key]:
            # Read current value
            current = await self.read(agent_id, key)

            # Apply update function
            if current and key in current:
                new_value = update_func(current[key])
            else:
                new_value = update_func(None)

            # Write back
            return await self.write(agent_id, key, new_value)

    def _create_version_snapshot(self, agent_id: str, description: str):
        """Create a version snapshot."""
        self.current_version += 1

        snapshot = WhiteboardVersion(
            version=self.current_version,
            timestamp=datetime.now(),
            entries=list(self.entries.values()),
            modified_by=agent_id,
            change_description=description
        )

        self.version_history.append(snapshot)

        # Keep only last 100 versions
        if len(self.version_history) > 100:
            self.version_history = self.version_history[-100:]

    def get_version(self, version: int) -> Optional[WhiteboardVersion]:
        """Get a specific version snapshot."""
        for v in self.version_history:
            if v.version == version:
                return v
        return None

    def rollback_to_version(self, version: int, agent_id: str) -> bool:
        """Rollback to a specific version."""
        if not self.check_access(agent_id, AccessLevel.ADMIN):
            raise PermissionError(f"Agent {agent_id} lacks admin access")

        snapshot = self.get_version(version)
        if not snapshot:
            return False

        with self._lock:
            # Restore entries
            self.entries = {
                entry.entry_id: entry
                for entry in snapshot.entries
            }

            # Create new version
            self._create_version_snapshot(agent_id, f"Rollback to version {version}")

            return True

    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe to whiteboard changes."""
        if not self.check_access(agent_id, AccessLevel.READ):
            raise PermissionError(f"Agent {agent_id} lacks read access")

        self._subscribers[agent_id] = callback

    def unsubscribe(self, agent_id: str):
        """Unsubscribe from whiteboard changes."""
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]

    async def _notify_subscribers(self, key: str, content: Any, modified_by: str):
        """Notify subscribers of changes."""
        tasks = []
        for agent_id, callback in self._subscribers.items():
            if agent_id != modified_by:  # Don't notify the modifier
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(key, content, modified_by))
                else:
                    callback(key, content, modified_by)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get whiteboard statistics."""
        return {
            'whiteboard_id': self.whiteboard_id,
            'type': self.whiteboard_type.value,
            'owner': self.owner_agent,
            'version': self.current_version,
            'entries': len(self.entries),
            'subscribers': len(self._subscribers),
            'permissions': {
                agent: level.value
                for agent, level in self.permissions.items()
            },
            'created': self.created_at.isoformat(),
            'modified': self.last_modified.isoformat()
        }


class WhiteboardManager:
    """
    Manages all whiteboards in the system.
    Provides discovery and lifecycle management.
    """

    def __init__(self, backend: Optional[SQLiteMemoryBackend] = None):
        """Initialize whiteboard manager."""
        self.backend = backend or SQLiteMemoryBackend()
        self._whiteboards: Dict[str, SharedWhiteboard] = {}
        self._lock = threading.RLock()
        self._initialized = False

    async def initialize(self):
        """Initialize the manager."""
        if not self._initialized:
            await self.backend.initialize()
            self._initialized = True

    async def create_whiteboard(
        self,
        whiteboard_type: WhiteboardType,
        owner_agent: str,
        whiteboard_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SharedWhiteboard:
        """Create a new whiteboard."""
        if not self._initialized:
            await self.initialize()

        # Generate ID if not provided
        if whiteboard_id is None:
            type_str = whiteboard_type.value
            timestamp = datetime.now().isoformat()
            whiteboard_id = hashlib.md5(
                f"{type_str}_{owner_agent}_{timestamp}".encode()
            ).hexdigest()[:12]

        with self._lock:
            # Create whiteboard
            whiteboard = SharedWhiteboard(
                whiteboard_id=whiteboard_id,
                whiteboard_type=whiteboard_type,
                owner_agent=owner_agent,
                backend=self.backend
            )

            # Set metadata
            if metadata:
                whiteboard.metadata = metadata

            # Initialize in backend
            await whiteboard.initialize()

            # Store reference
            self._whiteboards[whiteboard_id] = whiteboard

            return whiteboard

    def get_whiteboard(self, whiteboard_id: str) -> Optional[SharedWhiteboard]:
        """Get a whiteboard by ID."""
        return self._whiteboards.get(whiteboard_id)

    def find_whiteboards(
        self,
        whiteboard_type: Optional[WhiteboardType] = None,
        owner_agent: Optional[str] = None,
        accessible_by: Optional[str] = None
    ) -> List[SharedWhiteboard]:
        """
        Find whiteboards matching criteria.

        Args:
            whiteboard_type: Filter by type
            owner_agent: Filter by owner
            accessible_by: Filter by agent access

        Returns:
            List of matching whiteboards
        """
        results = []

        with self._lock:
            for whiteboard in self._whiteboards.values():
                # Check type
                if whiteboard_type and whiteboard.whiteboard_type != whiteboard_type:
                    continue

                # Check owner
                if owner_agent and whiteboard.owner_agent != owner_agent:
                    continue

                # Check access
                if accessible_by and accessible_by not in whiteboard.permissions:
                    continue

                results.append(whiteboard)

        return results

    async def delete_whiteboard(self, whiteboard_id: str, agent_id: str) -> bool:
        """Delete a whiteboard."""
        whiteboard = self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            return False

        # Check permission
        if not whiteboard.check_access(agent_id, AccessLevel.ADMIN):
            raise PermissionError(f"Agent {agent_id} lacks admin access")

        with self._lock:
            del self._whiteboards[whiteboard_id]
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            'total_whiteboards': len(self._whiteboards),
            'by_type': self._count_by_type(),
            'total_subscribers': sum(
                len(wb._subscribers)
                for wb in self._whiteboards.values()
            )
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count whiteboards by type."""
        counts = {}
        for wb in self._whiteboards.values():
            type_name = wb.whiteboard_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts


# Whiteboard templates for common patterns

def create_task_coordination_whiteboard(
    manager: WhiteboardManager,
    owner_agent: str,
    task_id: str
) -> SharedWhiteboard:
    """Create a task coordination whiteboard."""
    return asyncio.run(manager.create_whiteboard(
        whiteboard_type=WhiteboardType.TASK_COORDINATION,
        owner_agent=owner_agent,
        whiteboard_id=f"task_{task_id}",
        metadata={
            'task_id': task_id,
            'sections': ['status', 'assignments', 'dependencies', 'progress']
        }
    ))


def create_design_decision_whiteboard(
    manager: WhiteboardManager,
    owner_agent: str,
    decision_topic: str
) -> SharedWhiteboard:
    """Create a design decision whiteboard."""
    return asyncio.run(manager.create_whiteboard(
        whiteboard_type=WhiteboardType.DESIGN_DECISION,
        owner_agent=owner_agent,
        metadata={
            'topic': decision_topic,
            'sections': ['problem', 'options', 'pros_cons', 'decision', 'rationale']
        }
    ))


def create_problem_solving_whiteboard(
    manager: WhiteboardManager,
    owner_agent: str,
    problem_id: str
) -> SharedWhiteboard:
    """Create a problem solving whiteboard."""
    return asyncio.run(manager.create_whiteboard(
        whiteboard_type=WhiteboardType.PROBLEM_SOLVING,
        owner_agent=owner_agent,
        whiteboard_id=f"problem_{problem_id}",
        metadata={
            'problem_id': problem_id,
            'sections': ['description', 'analysis', 'hypotheses', 'solutions', 'results']
        }
    ))
