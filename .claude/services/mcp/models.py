"""Data models for MCP Service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Types of memories supported by the system."""
    
    EPISODIC = "episodic"      # Specific events and interactions
    SEMANTIC = "semantic"       # Facts and knowledge
    PROCEDURAL = "procedural"   # How-to knowledge
    WORKING = "working"         # Current task context
    SHARED = "shared"          # Team knowledge base


class ContextState(Enum):
    """States of agent context."""
    
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    MERGED = "merged"


@dataclass
class Memory:
    """Memory data structure."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.SEMANTIC
    agent_id: str = ""
    content: str = ""
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: int = 1
    parent_id: Optional[str] = None  # For version control
    associations: List[str] = field(default_factory=list)  # Related memory IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "agent_id": self.agent_id,
            "content": self.content,
            "embedding": self.embedding,
            "tags": self.tags,
            "metadata": self.metadata,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "version": self.version,
            "parent_id": self.parent_id,
            "associations": self.associations,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Memory:
        """Create memory from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MemoryType(data.get("type", "semantic")),
            agent_id=data.get("agent_id", ""),
            content=data.get("content", ""),
            embedding=data.get("embedding"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            importance_score=data.get("importance_score", 0.5),
            access_count=data.get("access_count", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            version=data.get("version", 1),
            parent_id=data.get("parent_id"),
            associations=data.get("associations", []),
        )
    
    def update_access(self) -> None:
        """Update access timestamp and count."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def calculate_relevance_score(self, query_embedding: Optional[List[float]] = None) -> float:
        """Calculate relevance score based on importance, recency, and similarity."""
        # Time decay factor (memories become less relevant over time)
        if self.last_accessed:
            time_delta = (datetime.now() - self.last_accessed).total_seconds()
            time_decay = 1.0 / (1.0 + time_delta / 86400)  # Daily decay
        else:
            time_decay = 0.5
        
        # Access frequency factor
        frequency_factor = min(1.0, self.access_count / 10.0)
        
        # Semantic similarity (if embeddings provided)
        similarity = 0.5  # Default similarity
        if query_embedding and self.embedding:
            # Cosine similarity calculation
            dot_product = sum(a * b for a, b in zip(query_embedding, self.embedding))
            norm_a = sum(a ** 2 for a in query_embedding) ** 0.5
            norm_b = sum(b ** 2 for b in self.embedding) ** 0.5
            if norm_a > 0 and norm_b > 0:
                similarity = dot_product / (norm_a * norm_b)
        
        # Combined relevance score
        relevance = (
            self.importance_score * 0.3 +
            time_decay * 0.2 +
            frequency_factor * 0.2 +
            similarity * 0.3
        )
        
        return relevance


@dataclass
class Context:
    """Agent context data structure."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    state: ContextState = ContextState.ACTIVE
    task_id: Optional[str] = None
    memories: List[str] = field(default_factory=list)  # Memory IDs
    working_memory: Dict[str, Any] = field(default_factory=dict)
    parent_context_id: Optional[str] = None
    child_contexts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "state": self.state.value,
            "task_id": self.task_id,
            "memories": self.memories,
            "working_memory": self.working_memory,
            "parent_context_id": self.parent_context_id,
            "child_contexts": self.child_contexts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Context:
        """Create context from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_id=data.get("agent_id", ""),
            state=ContextState(data.get("state", "active")),
            task_id=data.get("task_id"),
            memories=data.get("memories", []),
            working_memory=data.get("working_memory", {}),
            parent_context_id=data.get("parent_context_id"),
            child_contexts=data.get("child_contexts", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            metadata=data.get("metadata", {}),
        )
    
    def add_memory(self, memory_id: str) -> None:
        """Add memory to context."""
        if memory_id not in self.memories:
            self.memories.append(memory_id)
            self.updated_at = datetime.now()
    
    def remove_memory(self, memory_id: str) -> None:
        """Remove memory from context."""
        if memory_id in self.memories:
            self.memories.remove(memory_id)
            self.updated_at = datetime.now()
    
    def merge_with(self, other_context: Context) -> None:
        """Merge another context into this one."""
        # Merge memories (unique)
        for memory_id in other_context.memories:
            if memory_id not in self.memories:
                self.memories.append(memory_id)
        
        # Merge working memory
        self.working_memory.update(other_context.working_memory)
        
        # Update child contexts
        if other_context.id not in self.child_contexts:
            self.child_contexts.append(other_context.id)
        
        self.updated_at = datetime.now()


# API Request/Response Models

@dataclass
class MemorySearchRequest:
    """Request for memory search."""
    
    query: str
    agent_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    threshold: float = 0.5
    use_embeddings: bool = True


@dataclass
class MemorySearchResponse:
    """Response for memory search."""
    
    memories: List[Memory]
    total_count: int
    search_time_ms: float


@dataclass
class ContextSaveRequest:
    """Request to save context."""
    
    agent_id: str
    context: Context
    compress: bool = True


@dataclass
class ContextLoadResponse:
    """Response for context load."""
    
    context: Context
    memories: List[Memory]
    load_time_ms: float


@dataclass
class MemoryPruneRequest:
    """Request to prune memories."""
    
    agent_id: Optional[str] = None
    older_than_days: int = 90
    max_memories: Optional[int] = None
    preserve_important: bool = True
    importance_threshold: float = 0.7


@dataclass
class MemoryPruneResponse:
    """Response for memory pruning."""
    
    pruned_count: int
    retained_count: int
    freed_space_bytes: int