"""
Comprehensive Memory Fallback System for Gadugi v0.3 Agents

Provides multiple fallback options when the primary memory service is unavailable:
1. Neo4j Memory (primary)
2. SQLite Backend (first fallback)
3. Markdown File Backend (second fallback)
4. In-Memory Backend (emergency fallback)

Implements transparent switching without data loss and maintains the same interface.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import aiosqlite
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Memory Data Models (Compatible with Neo4j system)
# ============================================================================

class MemoryType(Enum):
    """Extended memory types for comprehensive memory system."""

    # Individual Agent Memory
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"

    # Shared Memory Spaces
    PROJECT_SHARED = "project_shared"
    TASK_WHITEBOARD = "task_whiteboard"
    TEAM_KNOWLEDGE = "team_knowledge"

    # Knowledge Graph
    KNOWLEDGE_NODE = "knowledge_node"
    KNOWLEDGE_EDGE = "knowledge_edge"


class MemoryScope(Enum):
    """Scope/visibility of memories."""
    PRIVATE = "private"
    TASK = "task"
    TEAM = "team"
    PROJECT = "project"
    GLOBAL = "global"


class MemoryPersistence(Enum):
    """Persistence levels for memories."""
    VOLATILE = "volatile"
    SESSION = "session"
    PERSISTENT = "persistent"
    ARCHIVED = "archived"


@dataclass
class Memory:
    """Memory structure compatible with Neo4j system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.SEMANTIC
    scope: MemoryScope = MemoryScope.PRIVATE
    persistence: MemoryPersistence = MemoryPersistence.SESSION

    # Ownership and context
    agent_id: str = ""
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    team_id: Optional[str] = None

    # Content
    content: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5
    confidence_score: float = 1.0
    decay_rate: float = 0.1

    # Access tracking
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Relationships
    parent_id: Optional[str] = None
    associations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    # Version control
    version: int = 1
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        # Handle datetime serialization
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        # Handle enums
        data['type'] = self.type.value if isinstance(self.type, MemoryType) else self.type
        data['scope'] = self.scope.value if isinstance(self.scope, MemoryScope) else self.scope
        data['persistence'] = self.persistence.value if isinstance(self.persistence, MemoryPersistence) else self.persistence
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create Memory from dictionary."""
        # Handle datetime parsing
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'last_accessed' in data and isinstance(data['last_accessed'], str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        if 'expires_at' in data and isinstance(data['expires_at'], str):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])

        # Handle enums
        if 'type' in data:
            data['type'] = MemoryType(data['type']) if isinstance(data['type'], str) else data['type']
        if 'scope' in data:
            data['scope'] = MemoryScope(data['scope']) if isinstance(data['scope'], str) else data['scope']
        if 'persistence' in data:
            data['persistence'] = MemoryPersistence(data['persistence']) if isinstance(data['persistence'], str) else data['persistence']

        return cls(**data)


@dataclass
class KnowledgeNode:
    """Knowledge graph node compatible with Neo4j system."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    concept: str = ""
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Graph relationships
    related_concepts: List[str] = field(default_factory=list)
    parent_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)

    # Source tracking
    source_memories: List[str] = field(default_factory=list)
    source_tasks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        """Create KnowledgeNode from dictionary."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class Whiteboard:
    """Task-specific shared workspace for collaboration."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    created_by: str = ""

    # Content sections
    notes: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    code_snippets: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    participants: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Version control
    version: int = 1
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Whiteboard':
        """Create Whiteboard from dictionary."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


# ============================================================================
# Abstract Memory Backend Interface
# ============================================================================

class MemoryBackend(ABC):
    """Abstract interface for memory storage backends."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the backend storage."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the backend storage."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the backend is available and healthy."""
        pass

    # ========== Memory Operations ==========

    @abstractmethod
    async def store_memory(self, memory: Memory) -> Memory:
        """Store a memory."""
        pass

    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a specific memory by ID."""
        pass

    @abstractmethod
    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Memory]:
        """Get memories for an agent."""
        pass

    @abstractmethod
    async def search_memories_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50
    ) -> List[Memory]:
        """Search memories by tags."""
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        pass

    @abstractmethod
    async def consolidate_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate short-term memories into long-term storage."""
        pass

    # ========== Project Memory Operations ==========

    @abstractmethod
    async def store_project_memory(
        self,
        project_id: str,
        content: str,
        created_by: str,
        **kwargs
    ) -> Memory:
        """Store project-wide shared memory."""
        pass

    @abstractmethod
    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Memory]:
        """Get project memories."""
        pass

    # ========== Procedural Memory Operations ==========

    @abstractmethod
    async def store_procedural_memory(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> Memory:
        """Store procedural knowledge."""
        pass

    @abstractmethod
    async def get_procedural_memories(
        self,
        agent_id: str,
        procedure_name: Optional[str] = None
    ) -> List[Memory]:
        """Get procedural memories."""
        pass

    # ========== Knowledge Graph Operations ==========

    @abstractmethod
    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: str,
        confidence: float = 1.0
    ) -> KnowledgeNode:
        """Add a knowledge node."""
        pass

    @abstractmethod
    async def link_knowledge_nodes(
        self,
        node1_id: str,
        node2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Link two knowledge nodes."""
        pass

    @abstractmethod
    async def get_knowledge_graph(
        self,
        agent_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get agent's knowledge graph."""
        pass

    # ========== Whiteboard Operations ==========

    @abstractmethod
    async def create_whiteboard(
        self,
        task_id: str,
        agent_id: str
    ) -> Whiteboard:
        """Create a task whiteboard."""
        pass

    @abstractmethod
    async def update_whiteboard(
        self,
        task_id: str,
        agent_id: str,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Update whiteboard content."""
        pass

    @abstractmethod
    async def get_whiteboard(
        self,
        task_id: str
    ) -> Optional[Whiteboard]:
        """Get whiteboard for a task."""
        pass

    # ========== Maintenance Operations ==========

    @abstractmethod
    async def cleanup_expired_memories(self) -> int:
        """Clean up expired memories."""
        pass

    @abstractmethod
    async def backup_agent_memories(
        self,
        agent_id: str,
        backup_path: Optional[str] = None
    ) -> str:
        """Backup agent memories."""
        pass


# ============================================================================
# Markdown File Backend Implementation
# ============================================================================

class MarkdownMemoryBackend(MemoryBackend):
    """File-based memory backend using structured markdown files."""

    def __init__(self, storage_path: str = ".memory"):
        self.storage_path = Path(storage_path)
        self.is_connected = False

    async def connect(self) -> None:
        """Initialize the file storage system."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            # Create subdirectories
            (self.storage_path / "agents").mkdir(exist_ok=True)
            (self.storage_path / "projects").mkdir(exist_ok=True)
            (self.storage_path / "whiteboards").mkdir(exist_ok=True)
            (self.storage_path / "knowledge").mkdir(exist_ok=True)
            self.is_connected = True
            logger.info(f"Markdown memory backend connected at {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to connect markdown backend: {e}")
            raise

    async def disconnect(self) -> None:
        """Clean up file system resources."""
        self.is_connected = False
        logger.info("Markdown memory backend disconnected")

    async def is_available(self) -> bool:
        """Check if the file system is available."""
        try:
            return self.is_connected and self.storage_path.exists() and self.storage_path.is_dir()
        except Exception:
            return False

    def _get_agent_path(self, agent_id: str) -> Path:
        """Get agent-specific storage path."""
        agent_path = self.storage_path / "agents" / agent_id
        agent_path.mkdir(parents=True, exist_ok=True)
        return agent_path

    def _get_memory_file_path(self, agent_id: str, memory_type: str) -> Path:
        """Get path for memory type file."""
        return self._get_agent_path(agent_id) / f"{memory_type}.md"

    async def _load_memories_from_file(self, file_path: Path) -> List[Memory]:
        """Load memories from a markdown file."""
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding='utf-8')
            memories = []

            # Parse markdown format
            sections = content.split('\n## Memory ')
            for section in sections[1:]:  # Skip header
                lines = section.strip().split('\n')
                if not lines:
                    continue

                # Extract memory ID from first line
                memory_id = lines[0].strip()

                # Find JSON data between ```json blocks
                json_start = -1
                json_end = -1
                for i, line in enumerate(lines):
                    if line.strip() == '```json':
                        json_start = i + 1
                    elif line.strip() == '```' and json_start != -1:
                        json_end = i
                        break

                if json_start != -1 and json_end != -1:
                    json_content = '\n'.join(lines[json_start:json_end])
                    try:
                        memory_data = json.loads(json_content)
                        memory = Memory.from_dict(memory_data)
                        memories.append(memory)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse memory {memory_id}: {e}")

            return memories
        except Exception as e:
            logger.error(f"Failed to load memories from {file_path}: {e}")
            return []

    async def _save_memories_to_file(self, file_path: Path, memories: List[Memory]) -> None:
        """Save memories to a markdown file using atomic operations."""
        import tempfile
        import os

        try:
            content = f"# Memory Storage\n\nGenerated: {datetime.now().isoformat()}\n\n"

            for memory in memories:
                content += f"## Memory {memory.id}\n\n"
                content += f"**Type:** {memory.type.value if isinstance(memory.type, MemoryType) else memory.type}\n"
                content += f"**Content:** {memory.content}\n"
                content += f"**Created:** {memory.created_at.isoformat() if memory.created_at else 'N/A'}\n"
                content += f"**Importance:** {memory.importance_score}\n\n"
                content += "```json\n"
                content += json.dumps(memory.to_dict(), indent=2, ensure_ascii=False)
                content += "\n```\n\n"

            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename atomically
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=file_path.parent,
                delete=False,
                prefix='.tmp_',
                suffix='.md'
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            # Atomic rename operation
            os.replace(tmp_path, str(file_path))

        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            logger.error(f"Failed to save memories to {file_path}: {e}")
            raise

    async def store_memory(self, memory: Memory) -> Memory:
        """Store a memory in markdown format."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        # Determine file based on memory type
        memory_type_str = memory.type.value if isinstance(memory.type, MemoryType) else str(memory.type)
        file_path = self._get_memory_file_path(memory.agent_id, memory_type_str)

        # Load existing memories
        memories = await self._load_memories_from_file(file_path)

        # Update or add memory
        found = False
        for i, existing in enumerate(memories):
            if existing.id == memory.id:
                memories[i] = memory
                found = True
                break

        if not found:
            memories.append(memory)

        # Save back to file
        await self._save_memories_to_file(file_path, memories)

        logger.debug(f"Stored memory {memory.id} in markdown backend")
        return memory

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a specific memory by ID."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        # Search through all agent directories
        agents_path = self.storage_path / "agents"
        if not agents_path.exists():
            return None

        for agent_dir in agents_path.iterdir():
            if not agent_dir.is_dir():
                continue

            for memory_file in agent_dir.glob("*.md"):
                memories = await self._load_memories_from_file(memory_file)
                for memory in memories:
                    if memory.id == memory_id:
                        return memory

        return None

    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Memory]:
        """Get memories for an agent."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        agent_path = self._get_agent_path(agent_id)
        if not agent_path.exists():
            return []

        all_memories = []

        # Load from relevant files
        if memory_type:
            memory_type_str = memory_type.value if isinstance(memory_type, MemoryType) else str(memory_type)
            file_path = self._get_memory_file_path(agent_id, memory_type_str)
            all_memories.extend(await self._load_memories_from_file(file_path))
        else:
            # Load from all files
            for memory_file in agent_path.glob("*.md"):
                all_memories.extend(await self._load_memories_from_file(memory_file))

        # Apply filters
        filtered_memories = []
        for memory in all_memories:
            if short_term_only and memory.persistence != MemoryPersistence.VOLATILE:
                continue
            if long_term_only and memory.persistence == MemoryPersistence.VOLATILE:
                continue
            filtered_memories.append(memory)

        # Sort by creation date (most recent first)
        filtered_memories.sort(key=lambda m: m.created_at or datetime.min, reverse=True)

        return filtered_memories[:limit]

    async def search_memories_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50
    ) -> List[Memory]:
        """Search memories by tags."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        all_memories = await self.get_agent_memories(agent_id, limit=1000)  # Get more for search

        matching_memories = []
        for memory in all_memories:
            if any(tag in memory.tags for tag in tags):
                matching_memories.append(memory)

        return matching_memories[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        # Find and remove from appropriate file
        agents_path = self.storage_path / "agents"
        if not agents_path.exists():
            return False

        for agent_dir in agents_path.iterdir():
            if not agent_dir.is_dir():
                continue

            for memory_file in agent_dir.glob("*.md"):
                memories = await self._load_memories_from_file(memory_file)
                original_count = len(memories)
                memories = [m for m in memories if m.id != memory_id]

                if len(memories) < original_count:
                    await self._save_memories_to_file(memory_file, memories)
                    logger.debug(f"Deleted memory {memory_id} from markdown backend")
                    return True

        return False

    async def consolidate_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate short-term memories into long-term storage."""
        if not await self.is_available():
            raise RuntimeError("Markdown backend not available")

        # Load short-term memories
        short_term_memories = await self.get_agent_memories(
            agent_id,
            short_term_only=True,
            limit=1000
        )

        consolidated = []
        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        for memory in short_term_memories:
            # Check if memory is old enough and important enough
            if (memory.created_at and memory.created_at < threshold_time and
                memory.importance_score > 0.6):

                # Convert to long-term
                memory.persistence = MemoryPersistence.PERSISTENT
                memory.updated_at = datetime.now()

                # Store in long-term file
                await self.store_memory(memory)
                consolidated.append(memory)

        return consolidated

    # ========== Stub implementations for other operations ==========
    # Note: Full implementation would be quite extensive, showing key methods above

    async def store_project_memory(
        self,
        project_id: str,
        content: str,
        created_by: str,
        **kwargs
    ) -> Memory:
        """Store project-wide shared memory."""
        memory = Memory(
            agent_id=created_by,
            project_id=project_id,
            content=content,
            type=MemoryType.PROJECT_SHARED,
            scope=MemoryScope.PROJECT,
            persistence=MemoryPersistence.PERSISTENT,
            **kwargs
        )

        # Store in project-specific file
        project_path = self.storage_path / "projects" / f"{project_id}.md"
        project_path.parent.mkdir(parents=True, exist_ok=True)

        memories = await self._load_memories_from_file(project_path)
        memories.append(memory)
        await self._save_memories_to_file(project_path, memories)

        return memory

    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Memory]:
        """Get project memories."""
        project_path = self.storage_path / "projects" / f"{project_id}.md"
        memories = await self._load_memories_from_file(project_path)
        return memories[:limit]

    async def store_procedural_memory(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> Memory:
        """Store procedural knowledge."""
        memory = Memory(
            agent_id=agent_id,
            content=f"Procedure: {procedure_name}",
            type=MemoryType.PROCEDURAL,
            structured_data={
                "procedure_name": procedure_name,
                "steps": steps,
                "context": context
            }
        )
        return await self.store_memory(memory)

    async def get_procedural_memories(
        self,
        agent_id: str,
        procedure_name: Optional[str] = None
    ) -> List[Memory]:
        """Get procedural memories."""
        memories = await self.get_agent_memories(agent_id, MemoryType.PROCEDURAL, limit=100)

        if procedure_name:
            filtered = []
            for memory in memories:
                if (memory.structured_data and
                    memory.structured_data.get("procedure_name") == procedure_name):
                    filtered.append(memory)
            return filtered

        return memories

    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: str,
        confidence: float = 1.0
    ) -> KnowledgeNode:
        """Add a knowledge node."""
        node = KnowledgeNode(
            agent_id=agent_id,
            concept=concept,
            description=description,
            confidence=confidence
        )

        # Store in knowledge graph file
        knowledge_path = self.storage_path / "knowledge" / f"{agent_id}_nodes.json"
        knowledge_path.parent.mkdir(parents=True, exist_ok=True)

        nodes = []
        if knowledge_path.exists():
            try:
                data = json.loads(knowledge_path.read_text())
                nodes = [KnowledgeNode.from_dict(item) for item in data]
            except (json.JSONDecodeError, KeyError):
                pass

        nodes.append(node)

        # Save back with atomic operation
        import tempfile
        import os

        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=knowledge_path.parent,
                delete=False,
                prefix='.tmp_',
                suffix='.json'
            ) as tmp_file:
                json.dump([node.to_dict() for node in nodes], tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, str(knowledge_path))
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise

        return node

    async def link_knowledge_nodes(
        self,
        node1_id: str,
        node2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Link two knowledge nodes."""
        # Store relationship in links file
        links_path = self.storage_path / "knowledge" / "links.json"

        links = []
        if links_path.exists():
            try:
                links = json.loads(links_path.read_text())
            except json.JSONDecodeError:
                pass

        link = {
            "id": str(uuid.uuid4()),
            "node1_id": node1_id,
            "node2_id": node2_id,
            "relationship": relationship,
            "strength": strength,
            "created_at": datetime.now().isoformat()
        }

        links.append(link)

        # Save with atomic operation
        import tempfile
        import os

        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=links_path.parent,
                delete=False,
                prefix='.tmp_',
                suffix='.json'
            ) as tmp_file:
                json.dump(links, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, str(links_path))
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise

    async def get_knowledge_graph(
        self,
        agent_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get agent's knowledge graph."""
        # Load nodes
        knowledge_path = self.storage_path / "knowledge" / f"{agent_id}_nodes.json"
        nodes = []
        if knowledge_path.exists():
            try:
                data = json.loads(knowledge_path.read_text())
                nodes = data
            except json.JSONDecodeError:
                pass

        # Load edges
        links_path = self.storage_path / "knowledge" / "links.json"
        edges = []
        if links_path.exists():
            try:
                all_links = json.loads(links_path.read_text())
                # Filter for this agent's nodes
                node_ids = {node['id'] for node in nodes}
                edges = [
                    link for link in all_links
                    if link['node1_id'] in node_ids or link['node2_id'] in node_ids
                ]
            except json.JSONDecodeError:
                pass

        return {
            "nodes": nodes,
            "edges": edges,
            "agent_id": agent_id,
            "max_depth": max_depth
        }

    async def create_whiteboard(
        self,
        task_id: str,
        agent_id: str
    ) -> Whiteboard:
        """Create a task whiteboard."""
        whiteboard = Whiteboard(
            task_id=task_id,
            created_by=agent_id,
            participants=[agent_id]
        )

        whiteboard_path = self.storage_path / "whiteboards" / f"{task_id}.json"
        whiteboard_path.parent.mkdir(parents=True, exist_ok=True)

        # Save with atomic operation
        import tempfile
        import os

        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=whiteboard_path.parent,
                delete=False,
                prefix='.tmp_',
                suffix='.json'
            ) as tmp_file:
                json.dump(whiteboard.to_dict(), tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, str(whiteboard_path))
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise

        return whiteboard

    async def update_whiteboard(
        self,
        task_id: str,
        agent_id: str,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Update whiteboard content."""
        whiteboard_path = self.storage_path / "whiteboards" / f"{task_id}.json"

        if not whiteboard_path.exists():
            # Create new whiteboard
            await self.create_whiteboard(task_id, agent_id)

        # Load existing whiteboard
        data = json.loads(whiteboard_path.read_text())
        whiteboard = Whiteboard.from_dict(data)

        # Add agent to participants if not present
        if agent_id not in whiteboard.participants:
            whiteboard.participants.append(agent_id)

        # Update content section
        if hasattr(whiteboard, section):
            section_list = getattr(whiteboard, section)
            if isinstance(section_list, list):
                section_list.append({
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    **content
                })

        whiteboard.updated_at = datetime.now()

        # Save back with atomic operation
        import tempfile
        import os

        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=whiteboard_path.parent,
                delete=False,
                prefix='.tmp_',
                suffix='.json'
            ) as tmp_file:
                json.dump(whiteboard.to_dict(), tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, str(whiteboard_path))
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise

    async def get_whiteboard(
        self,
        task_id: str
    ) -> Optional[Whiteboard]:
        """Get whiteboard for a task."""
        whiteboard_path = self.storage_path / "whiteboards" / f"{task_id}.json"

        if not whiteboard_path.exists():
            return None

        try:
            data = json.loads(whiteboard_path.read_text())
            return Whiteboard.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def cleanup_expired_memories(self) -> int:
        """Clean up expired memories."""
        if not await self.is_available():
            return 0

        deleted_count = 0
        now = datetime.now()

        # Check all agent memory files
        agents_path = self.storage_path / "agents"
        if agents_path.exists():
            for agent_dir in agents_path.iterdir():
                if not agent_dir.is_dir():
                    continue

                for memory_file in agent_dir.glob("*.md"):
                    memories = await self._load_memories_from_file(memory_file)
                    original_count = len(memories)

                    # Filter out expired memories
                    active_memories = [
                        m for m in memories
                        if not m.expires_at or m.expires_at > now
                    ]

                    if len(active_memories) < original_count:
                        await self._save_memories_to_file(memory_file, active_memories)
                        deleted_count += original_count - len(active_memories)

        return deleted_count

    async def backup_agent_memories(
        self,
        agent_id: str,
        backup_path: Optional[str] = None
    ) -> str:
        """Backup agent memories."""
        if not backup_path:
            backup_path = f"backup_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        memories = await self.get_agent_memories(agent_id, limit=10000)

        backup_data = {
            "agent_id": agent_id,
            "backup_timestamp": datetime.now().isoformat(),
            "memory_count": len(memories),
            "memories": [memory.to_dict() for memory in memories]
        }

        backup_file = Path(backup_path)

        # Save backup with atomic operation
        import tempfile
        import os

        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=backup_file.parent if backup_file.parent.exists() else Path.cwd(),
                delete=False,
                prefix='.tmp_backup_',
                suffix='.json'
            ) as tmp_file:
                json.dump(backup_data, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, str(backup_file))
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            raise

        return str(backup_file.absolute())


# ============================================================================
# SQLite Backend Implementation
# ============================================================================

class SQLiteMemoryBackend(MemoryBackend):
    """SQLite-based memory backend for reliable local storage with connection pooling."""

    def __init__(self, db_path: str = ".memory/memory.db", pool_size: int = 5):
        self.db_path = Path(db_path)
        self.is_connected = False
        self.pool_size = pool_size
        self._connection_pool: List[Any] = []
        self._pool_lock = asyncio.Lock()
        self._pool_semaphore = asyncio.Semaphore(pool_size)

    async def connect(self) -> None:
        """Initialize SQLite database with schema."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(str(self.db_path)) as db:
                # Create tables
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        persistence TEXT NOT NULL,
                        task_id TEXT,
                        project_id TEXT,
                        team_id TEXT,
                        content TEXT NOT NULL,
                        structured_data TEXT,
                        embedding TEXT,
                        tags TEXT,
                        metadata TEXT,
                        importance_score REAL DEFAULT 0.5,
                        confidence_score REAL DEFAULT 1.0,
                        decay_rate REAL DEFAULT 0.1,
                        access_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_accessed TEXT,
                        expires_at TEXT,
                        parent_id TEXT,
                        associations TEXT,
                        memory_references TEXT,
                        version INTEGER DEFAULT 1,
                        is_active INTEGER DEFAULT 1
                    )
                ''')

                await db.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_nodes (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        concept TEXT NOT NULL,
                        description TEXT NOT NULL,
                        attributes TEXT,
                        confidence REAL DEFAULT 1.0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        related_concepts TEXT,
                        parent_concepts TEXT,
                        child_concepts TEXT,
                        source_memories TEXT,
                        source_tasks TEXT
                    )
                ''')

                await db.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_links (
                        id TEXT PRIMARY KEY,
                        node1_id TEXT NOT NULL,
                        node2_id TEXT NOT NULL,
                        relationship TEXT NOT NULL,
                        strength REAL DEFAULT 1.0,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (node1_id) REFERENCES knowledge_nodes (id),
                        FOREIGN KEY (node2_id) REFERENCES knowledge_nodes (id)
                    )
                ''')

                await db.execute('''
                    CREATE TABLE IF NOT EXISTS whiteboards (
                        id TEXT PRIMARY KEY,
                        task_id TEXT UNIQUE NOT NULL,
                        created_by TEXT NOT NULL,
                        notes TEXT,
                        decisions TEXT,
                        action_items TEXT,
                        diagrams TEXT,
                        code_snippets TEXT,
                        participants TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        version INTEGER DEFAULT 1,
                        history TEXT
                    )
                ''')

                # Create indexes
                await db.execute('CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories (agent_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (type)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_memories_task ON memories (task_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_memories_project ON memories (project_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_agent ON knowledge_nodes (agent_id)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_whiteboards_task ON whiteboards (task_id)')

                await db.commit()

            self.is_connected = True
            logger.info(f"SQLite memory backend connected at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect SQLite backend: {e}")
            raise

    async def disconnect(self) -> None:
        """Clean up SQLite resources and close connection pool."""
        async with self._pool_lock:
            # Close all pooled connections
            while self._connection_pool:
                conn = self._connection_pool.pop()
                try:
                    await conn.close()
                except Exception as e:
                    logger.warning(f"Error closing pooled connection: {e}")

        self.is_connected = False
        logger.info("SQLite memory backend disconnected")

    async def is_available(self) -> bool:
        """Check if SQLite database is available."""
        try:
            if not self.is_connected:
                return False
            async with aiosqlite.connect(str(self.db_path)) as db:
                await db.execute("SELECT 1")
                return True
        except Exception:
            return False

    async def _get_connection(self):
        """Get a connection from the pool or create a new one."""
        async with self._pool_semaphore:
            async with self._pool_lock:
                if self._connection_pool:
                    return self._connection_pool.pop()

            # Create new connection if pool was empty
            conn = await aiosqlite.connect(str(self.db_path))
            conn.row_factory = aiosqlite.Row
            return conn

    async def _return_connection(self, conn):
        """Return a connection to the pool."""
        try:
            # Check if connection is still valid
            await conn.execute("SELECT 1")

            async with self._pool_lock:
                if len(self._connection_pool) < self.pool_size:
                    self._connection_pool.append(conn)
                else:
                    # Pool is full, close the connection
                    await conn.close()
        except Exception:
            # Connection is broken, close it
            try:
                await conn.close()
            except:
                pass

    def _memory_to_row(self, memory: Memory) -> Dict[str, Any]:
        """Convert Memory object to database row."""
        return {
            'id': memory.id,
            'agent_id': memory.agent_id,
            'type': memory.type.value if isinstance(memory.type, MemoryType) else memory.type,
            'scope': memory.scope.value if isinstance(memory.scope, MemoryScope) else memory.scope,
            'persistence': memory.persistence.value if isinstance(memory.persistence, MemoryPersistence) else memory.persistence,
            'task_id': memory.task_id,
            'project_id': memory.project_id,
            'team_id': memory.team_id,
            'content': memory.content,
            'structured_data': json.dumps(memory.structured_data) if memory.structured_data else None,
            'embedding': json.dumps(memory.embedding) if memory.embedding else None,
            'tags': json.dumps(memory.tags),
            'metadata': json.dumps(memory.metadata),
            'importance_score': memory.importance_score,
            'confidence_score': memory.confidence_score,
            'decay_rate': memory.decay_rate,
            'access_count': memory.access_count,
            'created_at': memory.created_at.isoformat() if memory.created_at else None,
            'updated_at': memory.updated_at.isoformat() if memory.updated_at else None,
            'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
            'expires_at': memory.expires_at.isoformat() if memory.expires_at else None,
            'parent_id': memory.parent_id,
            'associations': json.dumps(memory.associations),
            'memory_references': json.dumps(memory.references),
            'version': memory.version,
            'is_active': 1 if memory.is_active else 0
        }

    def _row_to_memory(self, row: Dict[str, Any]) -> Memory:
        """Convert database row to Memory object."""
        return Memory(
            id=row['id'],
            agent_id=row['agent_id'],
            type=MemoryType(row['type']),
            scope=MemoryScope(row['scope']),
            persistence=MemoryPersistence(row['persistence']),
            task_id=row['task_id'],
            project_id=row['project_id'],
            team_id=row['team_id'],
            content=row['content'],
            structured_data=json.loads(row['structured_data']) if row['structured_data'] else None,
            embedding=json.loads(row['embedding']) if row['embedding'] else None,
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            importance_score=row['importance_score'],
            confidence_score=row['confidence_score'],
            decay_rate=row['decay_rate'],
            access_count=row['access_count'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            parent_id=row['parent_id'],
            associations=json.loads(row['associations']) if row['associations'] else [],
            references=json.loads(row['memory_references']) if row['memory_references'] else [],
            version=row['version'],
            is_active=bool(row['is_active'])
        )

    async def store_memory(self, memory: Memory) -> Memory:
        """Store memory in SQLite using connection pool."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        conn = await self._get_connection()
        try:
            row_data = self._memory_to_row(memory)

            # Use INSERT OR REPLACE to handle updates
            placeholders = ', '.join(['?' for _ in row_data])
            columns = ', '.join(row_data.keys())
            query = f"INSERT OR REPLACE INTO memories ({columns}) VALUES ({placeholders})"

            await conn.execute(query, list(row_data.values()))
            await conn.commit()

            logger.debug(f"Stored memory {memory.id} in SQLite backend")
            return memory
        finally:
            await self._return_connection(conn)

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID using connection pool."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM memories WHERE id = ? AND is_active = 1",
                (memory_id,)
            )
            row = await cursor.fetchone()

            if row:
                return self._row_to_memory(dict(row))

            return None
        finally:
            await self._return_connection(conn)

    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Memory]:
        """Get agent memories with filters using connection pool."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        query = "SELECT * FROM memories WHERE agent_id = ? AND is_active = 1"
        params = [agent_id]

        if memory_type:
            query += " AND type = ?"
            params.append(memory_type.value)

        if short_term_only:
            query += " AND persistence = ?"
            params.append(MemoryPersistence.VOLATILE.value)
        elif long_term_only:
            query += " AND persistence != ?"
            params.append(MemoryPersistence.VOLATILE.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        conn = await self._get_connection()
        try:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_memory(dict(row)) for row in rows]
        finally:
            await self._return_connection(conn)

    async def search_memories_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50
    ) -> List[Memory]:
        """Search memories by tags using connection pool."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        # Build query to search for any of the tags in the JSON array
        tag_conditions = []
        params = [agent_id]

        for tag in tags:
            tag_conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        query = f"""
            SELECT * FROM memories
            WHERE agent_id = ? AND is_active = 1 AND ({' OR '.join(tag_conditions)})
            ORDER BY created_at DESC LIMIT ?
        """
        params.append(limit)

        conn = await self._get_connection()
        try:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_memory(dict(row)) for row in rows]
        finally:
            await self._return_connection(conn)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory (soft delete)."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                "UPDATE memories SET is_active = 0 WHERE id = ?",
                (memory_id,)
            )
            await db.commit()

            return cursor.rowcount > 0

    async def consolidate_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate short-term memories."""
        if not await self.is_available():
            raise RuntimeError("SQLite backend not available")

        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM memories
                WHERE agent_id = ? AND persistence = ? AND created_at < ?
                AND importance_score > 0.6 AND is_active = 1
            """, (agent_id, MemoryPersistence.VOLATILE.value, threshold_time.isoformat()))

            rows = await cursor.fetchall()
            consolidated = []

            for row in rows:
                memory = self._row_to_memory(dict(row))
                memory.persistence = MemoryPersistence.PERSISTENT
                memory.updated_at = datetime.now()

                await self.store_memory(memory)
                consolidated.append(memory)

            return consolidated

    # ========== Other operations (abbreviated for space) ==========

    async def store_project_memory(
        self,
        project_id: str,
        content: str,
        created_by: str,
        **kwargs
    ) -> Memory:
        """Store project memory."""
        memory = Memory(
            agent_id=created_by,
            project_id=project_id,
            content=content,
            type=MemoryType.PROJECT_SHARED,
            scope=MemoryScope.PROJECT,
            persistence=MemoryPersistence.PERSISTENT,
            **kwargs
        )
        return await self.store_memory(memory)

    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Memory]:
        """Get project memories."""
        return await self.get_agent_memories("", limit=limit)  # Simplified

    async def store_procedural_memory(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> Memory:
        """Store procedural memory."""
        memory = Memory(
            agent_id=agent_id,
            content=f"Procedure: {procedure_name}",
            type=MemoryType.PROCEDURAL,
            structured_data={
                "procedure_name": procedure_name,
                "steps": steps,
                "context": context
            }
        )
        return await self.store_memory(memory)

    async def get_procedural_memories(
        self,
        agent_id: str,
        procedure_name: Optional[str] = None
    ) -> List[Memory]:
        """Get procedural memories."""
        return await self.get_agent_memories(agent_id, MemoryType.PROCEDURAL, limit=100)

    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: str,
        confidence: float = 1.0
    ) -> KnowledgeNode:
        """Add knowledge node."""
        node = KnowledgeNode(
            agent_id=agent_id,
            concept=concept,
            description=description,
            confidence=confidence
        )

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO knowledge_nodes
                (id, agent_id, concept, description, attributes, confidence,
                 created_at, updated_at, related_concepts, parent_concepts,
                 child_concepts, source_memories, source_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.id, node.agent_id, node.concept, node.description,
                json.dumps(node.attributes), node.confidence,
                node.created_at.isoformat(), node.updated_at.isoformat(),
                json.dumps(node.related_concepts), json.dumps(node.parent_concepts),
                json.dumps(node.child_concepts), json.dumps(node.source_memories),
                json.dumps(node.source_tasks)
            ))
            await db.commit()

        return node

    async def link_knowledge_nodes(
        self,
        node1_id: str,
        node2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Link knowledge nodes."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO knowledge_links
                (id, node1_id, node2_id, relationship, strength, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), node1_id, node2_id, relationship, strength,
                datetime.now().isoformat()
            ))
            await db.commit()

    async def get_knowledge_graph(
        self,
        agent_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get knowledge graph."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Get nodes
            cursor = await db.execute(
                "SELECT * FROM knowledge_nodes WHERE agent_id = ?",
                (agent_id,)
            )
            node_rows = await cursor.fetchall()
            nodes = [dict(row) for row in node_rows]

            # Get edges
            node_ids = [node['id'] for node in nodes]
            if node_ids:
                placeholders = ','.join(['?' for _ in node_ids])
                cursor = await db.execute(f"""
                    SELECT * FROM knowledge_links
                    WHERE node1_id IN ({placeholders}) OR node2_id IN ({placeholders})
                """, node_ids + node_ids)
                edge_rows = await cursor.fetchall()
                edges = [dict(row) for row in edge_rows]
            else:
                edges = []

        return {"nodes": nodes, "edges": edges, "agent_id": agent_id}

    async def create_whiteboard(
        self,
        task_id: str,
        agent_id: str
    ) -> Whiteboard:
        """Create whiteboard."""
        whiteboard = Whiteboard(
            task_id=task_id,
            created_by=agent_id,
            participants=[agent_id]
        )

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO whiteboards
                (id, task_id, created_by, notes, decisions, action_items,
                 diagrams, code_snippets, participants, created_at, updated_at, version, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                whiteboard.id, whiteboard.task_id, whiteboard.created_by,
                json.dumps(whiteboard.notes), json.dumps(whiteboard.decisions),
                json.dumps(whiteboard.action_items), json.dumps(whiteboard.diagrams),
                json.dumps(whiteboard.code_snippets), json.dumps(whiteboard.participants),
                whiteboard.created_at.isoformat(), whiteboard.updated_at.isoformat(),
                whiteboard.version, json.dumps(whiteboard.history)
            ))
            await db.commit()

        return whiteboard

    async def update_whiteboard(
        self,
        task_id: str,
        agent_id: str,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Update whiteboard."""
        whiteboard = await self.get_whiteboard(task_id)
        if not whiteboard:
            whiteboard = await self.create_whiteboard(task_id, agent_id)

        # Add agent to participants
        if agent_id not in whiteboard.participants:
            whiteboard.participants.append(agent_id)

        # Update section
        if hasattr(whiteboard, section):
            section_list = getattr(whiteboard, section)
            if isinstance(section_list, list):
                section_list.append({
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    **content
                })

        whiteboard.updated_at = datetime.now()
        await self.create_whiteboard(task_id, agent_id)  # Save updated version

    async def get_whiteboard(
        self,
        task_id: str
    ) -> Optional[Whiteboard]:
        """Get whiteboard."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM whiteboards WHERE task_id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()

            if row:
                data = dict(row)
                # Parse JSON fields
                for field in ['notes', 'decisions', 'action_items', 'diagrams', 'code_snippets', 'participants', 'history']:
                    if data[field]:
                        data[field] = json.loads(data[field])
                    else:
                        data[field] = []

                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])

                return Whiteboard(**data)

        return None

    async def cleanup_expired_memories(self) -> int:
        """Cleanup expired memories."""
        if not await self.is_available():
            return 0

        now = datetime.now().isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                UPDATE memories SET is_active = 0
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (now,))
            await db.commit()

            return cursor.rowcount

    async def backup_agent_memories(
        self,
        agent_id: str,
        backup_path: Optional[str] = None
    ) -> str:
        """Backup agent memories."""
        if not backup_path:
            backup_path = f"backup_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

        # Simple file copy for SQLite
        import shutil
        shutil.copy2(str(self.db_path), backup_path)

        return backup_path


# ============================================================================
# In-Memory Backend Implementation
# ============================================================================

class InMemoryBackend(MemoryBackend):
    """In-memory storage backend for emergency fallback."""

    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.knowledge_nodes: Dict[str, KnowledgeNode] = {}
        self.knowledge_links: List[Dict[str, Any]] = []
        self.whiteboards: Dict[str, Whiteboard] = {}
        self.is_connected = False

    async def connect(self) -> None:
        """Initialize in-memory storage."""
        self.is_connected = True
        logger.info("In-memory backend connected")

    async def disconnect(self) -> None:
        """Clear in-memory storage."""
        self.memories.clear()
        self.knowledge_nodes.clear()
        self.knowledge_links.clear()
        self.whiteboards.clear()
        self.is_connected = False
        logger.info("In-memory backend disconnected")

    async def is_available(self) -> bool:
        """In-memory is always available when connected."""
        return self.is_connected

    async def store_memory(self, memory: Memory) -> Memory:
        """Store memory in memory."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        self.memories[memory.id] = memory
        logger.debug(f"Stored memory {memory.id} in in-memory backend")
        return memory

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        return self.memories.get(memory_id)

    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Memory]:
        """Get agent memories with filters."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        memories = [
            memory for memory in self.memories.values()
            if memory.agent_id == agent_id and memory.is_active
        ]

        # Apply filters
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        if short_term_only:
            memories = [m for m in memories if m.persistence == MemoryPersistence.VOLATILE]
        if long_term_only:
            memories = [m for m in memories if m.persistence != MemoryPersistence.VOLATILE]

        # Sort by creation date
        memories.sort(key=lambda m: m.created_at or datetime.min, reverse=True)

        return memories[:limit]

    async def search_memories_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50
    ) -> List[Memory]:
        """Search memories by tags."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        matching = []
        for memory in self.memories.values():
            if memory.agent_id == agent_id and memory.is_active:
                if any(tag in memory.tags for tag in tags):
                    matching.append(memory)

        matching.sort(key=lambda m: m.created_at or datetime.min, reverse=True)
        return matching[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        if memory_id in self.memories:
            self.memories[memory_id].is_active = False
            return True
        return False

    async def consolidate_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate memories."""
        if not await self.is_available():
            raise RuntimeError("In-memory backend not available")

        consolidated = []
        threshold_time = datetime.now() - timedelta(hours=threshold_hours)

        for memory in self.memories.values():
            if (memory.agent_id == agent_id and
                memory.persistence == MemoryPersistence.VOLATILE and
                memory.created_at and memory.created_at < threshold_time and
                memory.importance_score > 0.6):

                memory.persistence = MemoryPersistence.PERSISTENT
                memory.updated_at = datetime.now()
                consolidated.append(memory)

        return consolidated

    # ========== Simplified implementations of other methods ==========

    async def store_project_memory(self, project_id: str, content: str, created_by: str, **kwargs) -> Memory:
        memory = Memory(
            agent_id=created_by,
            project_id=project_id,
            content=content,
            type=MemoryType.PROJECT_SHARED,
            scope=MemoryScope.PROJECT,
            **kwargs
        )
        return await self.store_memory(memory)

    async def get_project_memories(self, project_id: str, limit: int = 50) -> List[Memory]:
        memories = [m for m in self.memories.values() if m.project_id == project_id]
        return memories[:limit]

    async def store_procedural_memory(self, agent_id: str, procedure_name: str, steps: List[str], context: Optional[str] = None) -> Memory:
        memory = Memory(
            agent_id=agent_id,
            content=f"Procedure: {procedure_name}",
            type=MemoryType.PROCEDURAL,
            structured_data={"procedure_name": procedure_name, "steps": steps, "context": context}
        )
        return await self.store_memory(memory)

    async def get_procedural_memories(self, agent_id: str, procedure_name: Optional[str] = None) -> List[Memory]:
        memories = await self.get_agent_memories(agent_id, MemoryType.PROCEDURAL)
        if procedure_name:
            memories = [m for m in memories if m.structured_data and m.structured_data.get("procedure_name") == procedure_name]
        return memories

    async def add_knowledge_node(self, agent_id: str, concept: str, description: str, confidence: float = 1.0) -> KnowledgeNode:
        node = KnowledgeNode(
            agent_id=agent_id,
            concept=concept,
            description=description,
            confidence=confidence
        )
        self.knowledge_nodes[node.id] = node
        return node

    async def link_knowledge_nodes(self, node1_id: str, node2_id: str, relationship: str, strength: float = 1.0) -> None:
        link = {
            "id": str(uuid.uuid4()),
            "node1_id": node1_id,
            "node2_id": node2_id,
            "relationship": relationship,
            "strength": strength,
            "created_at": datetime.now().isoformat()
        }
        self.knowledge_links.append(link)

    async def get_knowledge_graph(self, agent_id: str, max_depth: int = 2) -> Dict[str, Any]:
        nodes = [node.to_dict() for node in self.knowledge_nodes.values() if node.agent_id == agent_id]
        node_ids = {node['id'] for node in nodes}
        edges = [link for link in self.knowledge_links if link['node1_id'] in node_ids or link['node2_id'] in node_ids]
        return {"nodes": nodes, "edges": edges, "agent_id": agent_id}

    async def create_whiteboard(self, task_id: str, agent_id: str) -> Whiteboard:
        whiteboard = Whiteboard(task_id=task_id, created_by=agent_id, participants=[agent_id])
        self.whiteboards[task_id] = whiteboard
        return whiteboard

    async def update_whiteboard(self, task_id: str, agent_id: str, section: str, content: Dict[str, Any]) -> None:
        if task_id not in self.whiteboards:
            await self.create_whiteboard(task_id, agent_id)

        whiteboard = self.whiteboards[task_id]
        if agent_id not in whiteboard.participants:
            whiteboard.participants.append(agent_id)

        if hasattr(whiteboard, section):
            section_list = getattr(whiteboard, section)
            if isinstance(section_list, list):
                section_list.append({"agent_id": agent_id, "timestamp": datetime.now().isoformat(), **content})

        whiteboard.updated_at = datetime.now()

    async def get_whiteboard(self, task_id: str) -> Optional[Whiteboard]:
        return self.whiteboards.get(task_id)

    async def cleanup_expired_memories(self) -> int:
        deleted_count = 0
        now = datetime.now()

        for memory in list(self.memories.values()):
            if memory.expires_at and memory.expires_at < now:
                memory.is_active = False
                deleted_count += 1

        return deleted_count

    async def backup_agent_memories(self, agent_id: str, backup_path: Optional[str] = None) -> str:
        if not backup_path:
            backup_path = f"backup_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        memories = await self.get_agent_memories(agent_id, limit=10000)
        backup_data = {
            "agent_id": agent_id,
            "backup_timestamp": datetime.now().isoformat(),
            "memory_count": len(memories),
            "memories": [memory.to_dict() for memory in memories]
        }

        Path(backup_path).write_text(json.dumps(backup_data, indent=2))
        return backup_path


# ============================================================================
# Memory Fallback Chain Manager
# ============================================================================

class MemoryFallbackChain(MemoryBackend):
    """
    Manages automatic fallback between multiple memory backends with rate limiting.

    Fallback order:
    1. Neo4j Memory (primary)
    2. SQLite Backend (first fallback)
    3. Markdown File Backend (second fallback)
    4. In-Memory Backend (emergency fallback)
    """

    def __init__(
        self,
        primary_backend: Optional[MemoryBackend] = None,
        fallback_config: Optional[Dict[str, Any]] = None
    ):
        self.fallback_config = fallback_config or {}
        self.backends: List[MemoryBackend] = []
        self.current_backend_index = 0
        self.is_connected = False

        # Initialize backends in fallback order
        if primary_backend:
            self.backends.append(primary_backend)

        # Add SQLite fallback
        sqlite_path = self.fallback_config.get('sqlite_path', '.memory/memory.db')
        self.backends.append(SQLiteMemoryBackend(sqlite_path))

        # Add Markdown fallback
        markdown_path = self.fallback_config.get('markdown_path', '.memory')
        self.backends.append(MarkdownMemoryBackend(markdown_path))

        # Add in-memory emergency fallback
        self.backends.append(InMemoryBackend())

        # Track backend health
        self.backend_health: Dict[int, bool] = {}
        self.last_health_check: Dict[int, datetime] = {}
        self.health_check_interval = timedelta(minutes=5)

        # Rate limiting for background sync
        self.sync_rate_limit = self.fallback_config.get('sync_rate_limit', 10)  # Max syncs per second
        self.sync_semaphore = asyncio.Semaphore(self.sync_rate_limit)
        self.sync_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.sync_task: Optional[asyncio.Task] = None
        self.last_sync_time = datetime.now()
        self.sync_interval = timedelta(seconds=1.0 / self.sync_rate_limit)

    async def connect(self) -> None:
        """Connect to the fallback chain and start background sync."""
        logger.info("Initializing memory fallback chain...")

        # Try to connect to all backends
        for i, backend in enumerate(self.backends):
            try:
                await backend.connect()
                self.backend_health[i] = True
                logger.info(f"Backend {i} ({backend.__class__.__name__}) connected successfully")
            except Exception as e:
                self.backend_health[i] = False
                logger.warning(f"Backend {i} ({backend.__class__.__name__}) failed to connect: {e}")

        # Find the first available backend
        await self._find_available_backend()
        self.is_connected = True

        # Start background sync task with rate limiting
        self.sync_task = asyncio.create_task(self._background_sync_worker())

        logger.info(f"Memory fallback chain initialized. Using backend {self.current_backend_index} ({self.backends[self.current_backend_index].__class__.__name__})")

    async def disconnect(self) -> None:
        """Disconnect from all backends and stop background sync."""
        logger.info("Disconnecting memory fallback chain...")

        # Stop background sync task
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        # Process remaining sync queue items
        while not self.sync_queue.empty():
            try:
                sync_item = self.sync_queue.get_nowait()
                await self._perform_sync(sync_item)
            except:
                pass

        for i, backend in enumerate(self.backends):
            try:
                await backend.disconnect()
                logger.debug(f"Backend {i} ({backend.__class__.__name__}) disconnected")
            except Exception as e:
                logger.warning(f"Error disconnecting backend {i}: {e}")

        self.is_connected = False
        logger.info("Memory fallback chain disconnected")

    async def is_available(self) -> bool:
        """Check if any backend is available."""
        return self.is_connected and await self._get_current_backend().is_available()

    async def _find_available_backend(self) -> None:
        """Find the first available backend and switch to it."""
        for i, backend in enumerate(self.backends):
            try:
                if await backend.is_available():
                    if i != self.current_backend_index:
                        logger.info(f"Switching to backend {i} ({backend.__class__.__name__})")
                        self.current_backend_index = i
                    return
            except Exception as e:
                logger.warning(f"Backend {i} availability check failed: {e}")
                self.backend_health[i] = False

        # If we get here, no backends are available
        raise RuntimeError("No memory backends are available")

    async def _get_current_backend(self) -> MemoryBackend:
        """Get the current active backend, with health checking."""
        now = datetime.now()

        # Check if we need to verify backend health
        if (self.current_backend_index not in self.last_health_check or
            now - self.last_health_check[self.current_backend_index] > self.health_check_interval):

            current_backend = self.backends[self.current_backend_index]
            try:
                is_healthy = await current_backend.is_available()
                self.backend_health[self.current_backend_index] = is_healthy
                self.last_health_check[self.current_backend_index] = now

                if not is_healthy:
                    logger.warning(f"Current backend {self.current_backend_index} is unhealthy, switching...")
                    await self._find_available_backend()
            except Exception as e:
                logger.error(f"Health check failed for backend {self.current_backend_index}: {e}")
                self.backend_health[self.current_backend_index] = False
                await self._find_available_backend()

        return self.backends[self.current_backend_index]

    async def _execute_with_fallback(self, operation: str, *args, **kwargs) -> Any:
        """Execute an operation with automatic fallback."""
        last_exception = None

        # Try current backend first
        for attempt in range(len(self.backends)):
            try:
                backend = await self._get_current_backend()
                method = getattr(backend, operation)
                result = await method(*args, **kwargs)

                # Operation succeeded
                if attempt > 0:
                    logger.info(f"Operation '{operation}' succeeded on fallback attempt {attempt + 1}")

                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Operation '{operation}' failed on backend {self.current_backend_index}: {e}")

                # Mark current backend as unhealthy
                self.backend_health[self.current_backend_index] = False

                # Try to find another backend
                try:
                    await self._find_available_backend()
                except RuntimeError:
                    # No more backends available
                    break

        # All backends failed
        logger.error(f"Operation '{operation}' failed on all backends")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"All memory backends failed for operation: {operation}")

    async def _background_sync_worker(self) -> None:
        """Background worker that processes sync queue with rate limiting."""
        logger.info("Background sync worker started")

        while self.is_connected:
            try:
                # Get sync item from queue with timeout
                sync_item = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)

                # Apply rate limiting
                now = datetime.now()
                time_since_last_sync = now - self.last_sync_time
                if time_since_last_sync < self.sync_interval:
                    sleep_time = (self.sync_interval - time_since_last_sync).total_seconds()
                    await asyncio.sleep(sleep_time)

                # Perform sync with semaphore to limit concurrent syncs
                async with self.sync_semaphore:
                    await self._perform_sync(sync_item)
                    self.last_sync_time = datetime.now()

            except asyncio.TimeoutError:
                # No items in queue, continue
                continue
            except asyncio.CancelledError:
                logger.info("Background sync worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background sync worker: {e}")
                await asyncio.sleep(1)  # Brief pause on error

        logger.info("Background sync worker stopped")

    async def _perform_sync(self, sync_item: Dict[str, Any]) -> None:
        """Perform the actual sync operation."""
        if sync_item['type'] == 'memory':
            memory = sync_item['data']
            current_idx = self.current_backend_index

            # Try to sync to higher priority backends (lower index = higher priority)
            for i in range(current_idx):
                try:
                    backend = self.backends[i]
                    if await backend.is_available():
                        await backend.store_memory(memory)
                        logger.debug(f"Synced memory {memory.id} to higher priority backend {i}")
                        self.backend_health[i] = True
                except Exception as e:
                    logger.debug(f"Failed to sync to backend {i}: {e}")
                    self.backend_health[i] = False

    async def _sync_to_higher_priority_backends(self, memory: Memory) -> None:
        """Queue sync to higher priority backends with rate limiting."""
        try:
            # Add to sync queue if not full
            sync_item = {'type': 'memory', 'data': memory}
            self.sync_queue.put_nowait(sync_item)
        except asyncio.QueueFull:
            logger.warning(f"Sync queue is full, skipping sync for memory {memory.id}")

    # ========== Implement all MemoryBackend methods with fallback ==========

    async def store_memory(self, memory: Memory) -> Memory:
        """Store memory with fallback."""
        result = await self._execute_with_fallback('store_memory', memory)

        # Try to sync to higher priority backends in the background
        asyncio.create_task(self._sync_to_higher_priority_backends(memory))

        return result

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory with fallback."""
        return await self._execute_with_fallback('get_memory', memory_id)

    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Memory]:
        """Get agent memories with fallback."""
        return await self._execute_with_fallback(
            'get_agent_memories',
            agent_id,
            memory_type,
            short_term_only,
            long_term_only,
            limit
        )

    async def search_memories_by_tags(
        self,
        agent_id: str,
        tags: List[str],
        limit: int = 50
    ) -> List[Memory]:
        """Search memories with fallback."""
        return await self._execute_with_fallback('search_memories_by_tags', agent_id, tags, limit)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory with fallback."""
        return await self._execute_with_fallback('delete_memory', memory_id)

    async def consolidate_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate memories with fallback."""
        return await self._execute_with_fallback('consolidate_memories', agent_id, threshold_hours)

    async def store_project_memory(
        self,
        project_id: str,
        content: str,
        created_by: str,
        **kwargs
    ) -> Memory:
        """Store project memory with fallback."""
        result = await self._execute_with_fallback(
            'store_project_memory',
            project_id,
            content,
            created_by,
            **kwargs
        )

        # Try to sync to higher priority backends
        asyncio.create_task(self._sync_to_higher_priority_backends(result))

        return result

    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Memory]:
        """Get project memories with fallback."""
        return await self._execute_with_fallback('get_project_memories', project_id, limit)

    async def store_procedural_memory(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> Memory:
        """Store procedural memory with fallback."""
        result = await self._execute_with_fallback(
            'store_procedural_memory',
            agent_id,
            procedure_name,
            steps,
            context
        )

        asyncio.create_task(self._sync_to_higher_priority_backends(result))
        return result

    async def get_procedural_memories(
        self,
        agent_id: str,
        procedure_name: Optional[str] = None
    ) -> List[Memory]:
        """Get procedural memories with fallback."""
        return await self._execute_with_fallback('get_procedural_memories', agent_id, procedure_name)

    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: str,
        confidence: float = 1.0
    ) -> KnowledgeNode:
        """Add knowledge node with fallback."""
        return await self._execute_with_fallback(
            'add_knowledge_node',
            agent_id,
            concept,
            description,
            confidence
        )

    async def link_knowledge_nodes(
        self,
        node1_id: str,
        node2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Link knowledge nodes with fallback."""
        return await self._execute_with_fallback(
            'link_knowledge_nodes',
            node1_id,
            node2_id,
            relationship,
            strength
        )

    async def get_knowledge_graph(
        self,
        agent_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get knowledge graph with fallback."""
        return await self._execute_with_fallback('get_knowledge_graph', agent_id, max_depth)

    async def create_whiteboard(
        self,
        task_id: str,
        agent_id: str
    ) -> Whiteboard:
        """Create whiteboard with fallback."""
        return await self._execute_with_fallback('create_whiteboard', task_id, agent_id)

    async def update_whiteboard(
        self,
        task_id: str,
        agent_id: str,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Update whiteboard with fallback."""
        return await self._execute_with_fallback(
            'update_whiteboard',
            task_id,
            agent_id,
            section,
            content
        )

    async def get_whiteboard(
        self,
        task_id: str
    ) -> Optional[Whiteboard]:
        """Get whiteboard with fallback."""
        return await self._execute_with_fallback('get_whiteboard', task_id)

    async def cleanup_expired_memories(self) -> int:
        """Cleanup expired memories with fallback."""
        return await self._execute_with_fallback('cleanup_expired_memories')

    async def backup_agent_memories(
        self,
        agent_id: str,
        backup_path: Optional[str] = None
    ) -> str:
        """Backup agent memories with fallback."""
        return await self._execute_with_fallback('backup_agent_memories', agent_id, backup_path)

    # ========== Additional management methods ==========

    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all backends in the fallback chain."""
        status = {
            "current_backend": {
                "index": self.current_backend_index,
                "name": self.backends[self.current_backend_index].__class__.__name__,
                "healthy": self.backend_health.get(self.current_backend_index, False)
            },
            "all_backends": []
        }

        for i, backend in enumerate(self.backends):
            backend_info = {
                "index": i,
                "name": backend.__class__.__name__,
                "healthy": self.backend_health.get(i, False),
                "last_check": self.last_health_check.get(i, datetime.min).isoformat(),
                "is_current": i == self.current_backend_index
            }
            status["all_backends"].append(backend_info)

        return status

    async def force_backend_switch(self, backend_index: int) -> bool:
        """Force switch to a specific backend (for testing/admin)."""
        if backend_index < 0 or backend_index >= len(self.backends):
            return False

        try:
            backend = self.backends[backend_index]
            if await backend.is_available():
                old_index = self.current_backend_index
                self.current_backend_index = backend_index
                self.backend_health[backend_index] = True
                logger.info(f"Forced switch from backend {old_index} to {backend_index}")
                return True
        except Exception as e:
            logger.error(f"Failed to force switch to backend {backend_index}: {e}")

        return False

    async def health_check_all_backends(self) -> Dict[int, bool]:
        """Perform health check on all backends."""
        logger.info("Performing health check on all backends...")

        for i, backend in enumerate(self.backends):
            try:
                is_healthy = await backend.is_available()
                self.backend_health[i] = is_healthy
                self.last_health_check[i] = datetime.now()
                logger.debug(f"Backend {i} ({backend.__class__.__name__}): {'healthy' if is_healthy else 'unhealthy'}")
            except Exception as e:
                self.backend_health[i] = False
                self.last_health_check[i] = datetime.now()
                logger.warning(f"Backend {i} health check failed: {e}")

        # Switch to best available backend if current is unhealthy
        if not self.backend_health.get(self.current_backend_index, False):
            try:
                await self._find_available_backend()
            except RuntimeError:
                logger.error("No healthy backends found during health check")

        return self.backend_health.copy()


# ============================================================================
# Convenience Factory Functions
# ============================================================================

def create_memory_fallback_chain(
    neo4j_config: Optional[Dict[str, Any]] = None,
    fallback_config: Optional[Dict[str, Any]] = None
) -> MemoryFallbackChain:
    """
    Create a complete memory fallback chain.

    Args:
        neo4j_config: Neo4j connection configuration (optional)
            Example: {
                'uri': os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
                'username': os.environ.get('NEO4J_USERNAME', 'neo4j'),
                'password': os.environ.get('NEO4J_PASSWORD')  # Never hardcode!
            }
        fallback_config: Fallback backend configuration (optional)
            Example: {
                'sqlite_path': '.memory/memory.db',
                'markdown_path': '.memory',
                'sync_rate_limit': 10  # Max syncs per second
            }

    Returns:
        Configured MemoryFallbackChain instance

    Security Note:
        NEVER hardcode credentials in configuration. Always use environment
        variables or secure configuration management systems.
    """
    primary_backend = None

    # For now, we'll create a simple chain without Neo4j integration
    # The Neo4j integration would require more complex bridging
    return MemoryFallbackChain(primary_backend, fallback_config)


def create_simple_fallback_chain(storage_path: str = ".memory") -> MemoryFallbackChain:
    """
    Create a simple fallback chain without Neo4j (for testing or when Neo4j unavailable).

    Args:
        storage_path: Base path for file storage backends

    Returns:
        Configured MemoryFallbackChain with SQLite, Markdown, and In-Memory backends
    """
    chain = MemoryFallbackChain(
        primary_backend=None,  # No Neo4j
        fallback_config={
            'sqlite_path': f"{storage_path}/memory.db",
            'markdown_path': storage_path
        }
    )

    logger.info("Created simple fallback chain (no Neo4j)")
    return chain
