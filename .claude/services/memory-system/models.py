from typing import Any, Dict, List, Optional

"""Data models for the Memory System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

class MemoryType(Enum):
    """Types of memories stored in the system."""

    CONTEXT = "context"
    DECISION = "decision"
    PATTERN = "pattern"
    ACHIEVEMENT = "achievement"
    TODO = "todo"
    REFLECTION = "reflection"

@dataclass
class Memory:
    """Represents a single memory in the system."""

    id: str
    type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    references: List[str] = field(default_factory=list)  # Related memory IDs
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0  # 0.0 to 1.0
    github_issue_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "references": self.references,
            "tags": self.tags,
            "importance": self.importance,
            "github_issue_id": self.github_issue_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create memory from dictionary."""
        return cls(
            id=data["id"],
            type=MemoryType(data["type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            references=data.get("references", []),
            tags=data.get("tags", []),
            importance=data.get("importance", 1.0),
            github_issue_id=data.get("github_issue_id"),
        )

@dataclass
class Pattern:
    """Represents a pattern extracted from memories."""

    id: str
    pattern_type: str
    description: str
    frequency: int
    memory_ids: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "memory_ids": self.memory_ids,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

@dataclass
class SyncResult:
    """Result of GitHub synchronization."""

    success: bool
    issues_created: int = 0
    issues_updated: int = 0
    issues_closed: int = 0
    memories_created: int = 0
    memories_updated: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "issues_created": self.issues_created,
            "issues_updated": self.issues_updated,
            "issues_closed": self.issues_closed,
            "memories_created": self.memories_created,
            "memories_updated": self.memories_updated,
            "errors": self.errors,
        }

@dataclass
class ImportResult:
    """Result of importing from Memory.md."""

    success: bool
    memories_imported: int = 0
    todos_imported: int = 0
    reflections_imported: int = 0
    errors: List[str] = field(default_factory=list)
    filepath: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "memories_imported": self.memories_imported,
            "todos_imported": self.todos_imported,
            "reflections_imported": self.reflections_imported,
            "errors": self.errors,
            "filepath": str(self.filepath) if self.filepath else None,
        }

@dataclass
class PruneResult:
    """Result of pruning old memories."""

    success: bool
    memories_pruned: int = 0
    memories_archived: int = 0
    space_freed_mb: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "memories_pruned": self.memories_pruned,
            "memories_archived": self.memories_archived,
            "space_freed_mb": self.space_freed_mb,
            "errors": self.errors,
        }
