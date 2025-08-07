#!/usr/bin/env python3
"""MCP (Memory and Context Persistence) Service for Gadugi v0.3.

Advanced memory management and context persistence for multi-agent systems.
Handles long-term memory, context switching, session persistence, and intelligent memory retrieval.
"""
from __future__ import annotations

import asyncio
import base64
import contextlib
import gzip
import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    # Mock Redis for development
    class MockRedis:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get(self, key) -> None:
            return None

        def set(self, key, value, ex=None) -> bool:
            return True

        def delete(self, key) -> bool:
            return True

        def exists(self, key) -> bool:
            return False

        def keys(self, pattern="*"):
            return []

        def flushdb(self) -> bool:
            return True

        def ping(self) -> bool:
            return True

        def close(self) -> None:
            pass


class MemoryType(Enum):
    """Memory type enumeration."""

    EPISODIC = "episodic"  # Event-based memories
    SEMANTIC = "semantic"  # Factual knowledge
    PROCEDURAL = "procedural"  # Skills and procedures
    WORKING = "working"  # Short-term context
    DECLARATIVE = "declarative"  # Explicit knowledge
    ASSOCIATIVE = "associative"  # Relationship-based memories


class ContextType(Enum):
    """Context type enumeration."""

    SESSION = "session"  # User session context
    WORKFLOW = "workflow"  # Workflow execution context
    AGENT = "agent"  # Agent state context
    TASK = "task"  # Task-specific context
    CONVERSATION = "conversation"  # Dialogue context
    PROJECT = "project"  # Project-wide context


class PersistenceLevel(Enum):
    """Persistence level enumeration."""

    TEMPORARY = "temporary"  # In-memory only
    SESSION = "session"  # Persist for session duration
    PERMANENT = "permanent"  # Long-term storage
    ARCHIVAL = "archival"  # Long-term compressed storage


class RetrievalStrategy(Enum):
    """Memory retrieval strategy enumeration."""

    CHRONOLOGICAL = "chronological"  # Time-based ordering
    RELEVANCE = "relevance"  # Semantic similarity
    FREQUENCY = "frequency"  # Access frequency
    RECENCY = "recency"  # Recent access
    IMPORTANCE = "importance"  # Priority-based
    ASSOCIATIVE = "associative"  # Related concepts


@dataclass
class MemoryEntry:
    """Represents a memory entry in the system."""

    id: str
    type: MemoryType
    content: dict[str, Any]
    context: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    importance_score: float = 1.0
    decay_rate: float = 0.1
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ContextSnapshot:
    """Represents a context snapshot."""

    id: str
    type: ContextType
    context_data: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    expires_at: datetime | None = None
    compressed: bool = False
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for context data integrity."""
        content = json.dumps(self.context_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class RetrievalQuery:
    """Query for memory retrieval operations."""

    query_text: str | None = None
    memory_types: list[MemoryType] | None = None
    context_types: list[ContextType] | None = None
    tags: list[str] | None = None
    time_range: tuple[datetime, datetime] | None = None
    importance_threshold: float = 0.0
    max_results: int = 100
    strategy: RetrievalStrategy = RetrievalStrategy.RELEVANCE
    include_context: bool = True

    def __post_init__(self):
        if self.memory_types is None:
            self.memory_types = []
        if self.context_types is None:
            self.context_types = []
        if self.tags is None:
            self.tags = []


@dataclass
class MemoryStats:
    """Memory system statistics."""

    total_memories: int = 0
    memories_by_type: dict[str, int] = None
    total_contexts: int = 0
    contexts_by_type: dict[str, int] = None
    storage_size: int = 0
    cache_hit_rate: float = 0.0
    average_access_time: float = 0.0
    compression_ratio: float = 0.0
    last_cleanup: datetime = None

    def __post_init__(self):
        if self.memories_by_type is None:
            self.memories_by_type = {}
        if self.contexts_by_type is None:
            self.contexts_by_type = {}
        if self.last_cleanup is None:
            self.last_cleanup = datetime.now()


@dataclass
class OperationResult:
    """Result of MCP operations."""

    success: bool
    operation: str
    data: Any = None
    metadata: dict[str, Any] = None
    execution_time: float = 0.0
    warnings: list[str] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class MemoryManager:
    """Memory management component of MCP service."""

    def __init__(self, storage_path: str, compression_enabled: bool = True) -> None:
        self.storage_path = Path(storage_path)
        self.compression_enabled = compression_enabled
        self.logger = logging.getLogger("mcp_memory")

        # In-memory cache
        self.memory_cache: dict[str, MemoryEntry] = {}
        self.cache_max_size = 10000
        self.cache_access_order = []

        # Storage
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "memories.db"
        self._init_database()

        # Thread safety
        self.lock = threading.RLock()

    def _init_database(self) -> None:
        """Initialize SQLite database for memory storage."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    importance_score REAL DEFAULT 1.0,
                    decay_rate REAL DEFAULT 0.1,
                    tags TEXT DEFAULT '[]',
                    compressed BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score)
            """)

            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id, content, tags, content='memories', content_rowid='rowid'
                )
            """)

            conn.commit()

    def store_memory(self, memory: MemoryEntry) -> OperationResult:
        """Store a memory entry."""
        start_time = time.time()

        try:
            with self.lock:
                # Update access info
                memory.accessed_at = datetime.now()

                # Serialize data
                content_json = json.dumps(memory.content)
                context_json = json.dumps(memory.context)
                metadata_json = json.dumps(memory.metadata)
                tags_json = json.dumps(memory.tags)

                # Compress if enabled and content is large
                compressed = False
                if self.compression_enabled and len(content_json) > 1024:
                    content_json = base64.b64encode(
                        gzip.compress(content_json.encode()),
                    ).decode()
                    compressed = True

                # Store in database
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO memories
                        (id, type, content, context, metadata, created_at, accessed_at,
                         access_count, importance_score, decay_rate, tags, compressed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            memory.id,
                            memory.type.value,
                            content_json,
                            context_json,
                            metadata_json,
                            memory.created_at.isoformat(),
                            memory.accessed_at.isoformat(),
                            memory.access_count,
                            memory.importance_score,
                            memory.decay_rate,
                            tags_json,
                            compressed,
                        ),
                    )

                    # Update FTS index
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO memories_fts (rowid, id, content, tags)
                        SELECT rowid, id, ?, ? FROM memories WHERE id = ?
                    """,
                        (json.dumps(memory.content), tags_json, memory.id),
                    )

                    conn.commit()

                # Cache the memory
                self._cache_memory(memory)

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="store_memory",
                    data={"memory_id": memory.id},
                    metadata={
                        "compressed": compressed,
                        "cache_size": len(self.memory_cache),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to store memory {memory.id}: {e}")

            return OperationResult(
                success=False,
                operation="store_memory",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def retrieve_memory(self, memory_id: str) -> OperationResult:
        """Retrieve a specific memory by ID."""
        start_time = time.time()

        try:
            with self.lock:
                # Check cache first
                if memory_id in self.memory_cache:
                    memory = self.memory_cache[memory_id]
                    memory.access_count += 1
                    memory.accessed_at = datetime.now()

                    # Update access tracking in cache
                    if memory_id in self.cache_access_order:
                        self.cache_access_order.remove(memory_id)
                    self.cache_access_order.append(memory_id)

                    execution_time = time.time() - start_time

                    return OperationResult(
                        success=True,
                        operation="retrieve_memory",
                        data=memory,
                        metadata={
                            "source": "cache",
                            "access_count": memory.access_count,
                        },
                        execution_time=execution_time,
                    )

                # Retrieve from database
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        """
                        SELECT * FROM memories WHERE id = ?
                    """,
                        (memory_id,),
                    )

                    row = cursor.fetchone()
                    if not row:
                        execution_time = time.time() - start_time
                        return OperationResult(
                            success=False,
                            operation="retrieve_memory",
                            execution_time=execution_time,
                            warnings=[f"Memory {memory_id} not found"],
                        )

                    memory = self._row_to_memory(row)

                    # Update access count
                    memory.access_count += 1
                    memory.accessed_at = datetime.now()

                    conn.execute(
                        """
                        UPDATE memories SET access_count = ?, accessed_at = ?
                        WHERE id = ?
                    """,
                        (
                            memory.access_count,
                            memory.accessed_at.isoformat(),
                            memory_id,
                        ),
                    )

                    conn.commit()

                # Cache the memory
                self._cache_memory(memory)

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="retrieve_memory",
                    data=memory,
                    metadata={
                        "source": "database",
                        "access_count": memory.access_count,
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to retrieve memory {memory_id}: {e}")

            return OperationResult(
                success=False,
                operation="retrieve_memory",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def query_memories(self, query: RetrievalQuery) -> OperationResult:
        """Query memories based on criteria."""
        start_time = time.time()

        try:
            with self.lock:
                # Build SQL query based on retrieval query
                sql_conditions = []
                params = []

                if query.memory_types:
                    type_placeholders = ",".join("?" * len(query.memory_types))
                    sql_conditions.append(f"type IN ({type_placeholders})")
                    params.extend([mt.value for mt in query.memory_types])

                if query.time_range:
                    sql_conditions.append("created_at BETWEEN ? AND ?")
                    params.extend(
                        [
                            query.time_range[0].isoformat(),
                            query.time_range[1].isoformat(),
                        ],
                    )

                if query.importance_threshold > 0:
                    sql_conditions.append("importance_score >= ?")
                    params.append(query.importance_threshold)

                # Full-text search if query text provided
                if query.query_text:
                    base_query = """
                        SELECT m.* FROM memories m
                        JOIN memories_fts fts ON m.rowid = fts.rowid
                        WHERE fts.content MATCH ?
                    """
                    params.insert(0, query.query_text)
                else:
                    base_query = "SELECT * FROM memories"

                # Add conditions
                if sql_conditions:
                    if query.query_text:
                        base_query += " AND " + " AND ".join(sql_conditions)
                    else:
                        base_query += " WHERE " + " AND ".join(sql_conditions)

                # Add ordering based on strategy
                if query.strategy == RetrievalStrategy.CHRONOLOGICAL:
                    base_query += " ORDER BY created_at DESC"
                elif query.strategy == RetrievalStrategy.FREQUENCY:
                    base_query += " ORDER BY access_count DESC"
                elif query.strategy == RetrievalStrategy.RECENCY:
                    base_query += " ORDER BY accessed_at DESC"
                elif query.strategy == RetrievalStrategy.IMPORTANCE:
                    base_query += " ORDER BY importance_score DESC"
                else:  # RELEVANCE or ASSOCIATIVE
                    base_query += " ORDER BY importance_score DESC, accessed_at DESC"

                # Add limit
                base_query += " LIMIT ?"
                params.append(query.max_results)

                # Execute query
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(base_query, params)
                    rows = cursor.fetchall()

                # Convert rows to memories
                memories = [self._row_to_memory(row) for row in rows]

                # Apply tag filtering if specified
                if query.tags:
                    memories = [
                        m for m in memories if any(tag in m.tags for tag in query.tags)
                    ]

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="query_memories",
                    data=memories,
                    metadata={
                        "query_strategy": query.strategy.value,
                        "result_count": len(memories),
                        "max_results": query.max_results,
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to query memories: {e}")

            return OperationResult(
                success=False,
                operation="query_memories",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def delete_memory(self, memory_id: str) -> OperationResult:
        """Delete a memory entry."""
        start_time = time.time()

        try:
            with self.lock:
                # Remove from cache
                if memory_id in self.memory_cache:
                    del self.memory_cache[memory_id]
                    if memory_id in self.cache_access_order:
                        self.cache_access_order.remove(memory_id)

                # Remove from database
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        "DELETE FROM memories WHERE id = ?", (memory_id,),
                    )

                    if cursor.rowcount == 0:
                        execution_time = time.time() - start_time
                        return OperationResult(
                            success=False,
                            operation="delete_memory",
                            execution_time=execution_time,
                            warnings=[f"Memory {memory_id} not found"],
                        )

                    # Remove from FTS index
                    conn.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
                    conn.commit()

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="delete_memory",
                    data={"memory_id": memory_id},
                    metadata={"cache_size": len(self.memory_cache)},
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to delete memory {memory_id}: {e}")

            return OperationResult(
                success=False,
                operation="delete_memory",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def _row_to_memory(self, row) -> MemoryEntry:
        """Convert database row to MemoryEntry."""
        content_json = row[2]

        # Decompress if needed
        if row[11]:  # compressed flag
            content_json = gzip.decompress(base64.b64decode(content_json)).decode()

        return MemoryEntry(
            id=row[0],
            type=MemoryType(row[1]),
            content=json.loads(content_json),
            context=json.loads(row[3]),
            metadata=json.loads(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            accessed_at=datetime.fromisoformat(row[6]),
            access_count=row[7],
            importance_score=row[8],
            decay_rate=row[9],
            tags=json.loads(row[10]),
        )

    def _cache_memory(self, memory: MemoryEntry) -> None:
        """Add memory to cache with LRU eviction."""
        self.memory_cache[memory.id] = memory

        # Update access order
        if memory.id in self.cache_access_order:
            self.cache_access_order.remove(memory.id)
        self.cache_access_order.append(memory.id)

        # Evict least recently used if cache is full
        while len(self.memory_cache) > self.cache_max_size:
            lru_id = self.cache_access_order.pop(0)
            del self.memory_cache[lru_id]

    def get_stats(self) -> MemoryStats:
        """Get memory system statistics."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Total memories
                cursor = conn.execute("SELECT COUNT(*) FROM memories")
                total_memories = cursor.fetchone()[0]

                # Memories by type
                cursor = conn.execute(
                    "SELECT type, COUNT(*) FROM memories GROUP BY type",
                )
                memories_by_type = dict(cursor.fetchall())

                # Storage size approximation
                storage_size = (
                    os.path.getsize(self.db_path) if self.db_path.exists() else 0
                )

                return MemoryStats(
                    total_memories=total_memories,
                    memories_by_type=memories_by_type,
                    storage_size=storage_size,
                    cache_hit_rate=0.0,  # Would need to track hits/misses
                    average_access_time=0.0,  # Would need to track access times
                    compression_ratio=0.0,  # Would need to track compressed vs uncompressed
                )

        except Exception as e:
            self.logger.exception(f"Failed to get memory stats: {e}")
            return MemoryStats()


class ContextManager:
    """Context management component of MCP service."""

    def __init__(self, storage_path: str, redis_url: str | None = None) -> None:
        self.storage_path = Path(storage_path)
        self.logger = logging.getLogger("mcp_context")

        # Redis for fast context access
        self.redis_client = None
        if REDIS_AVAILABLE and redis_url:
            try:
                import redis

                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
            except Exception as e:
                self.logger.warning(
                    f"Redis connection failed, using local storage: {e}",
                )
                self.redis_client = None

        if not self.redis_client:
            self.redis_client = MockRedis()

        # Local storage fallback
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "contexts.db"
        self._init_database()

        # Thread safety
        self.lock = threading.RLock()

    def _init_database(self) -> None:
        """Initialize SQLite database for context storage."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    compressed BOOLEAN DEFAULT FALSE,
                    checksum TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contexts_type ON contexts(type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contexts_expires_at ON contexts(expires_at)
            """)

            conn.commit()

    def save_context(
        self,
        context: ContextSnapshot,
        persistence_level: PersistenceLevel = PersistenceLevel.SESSION,
    ) -> OperationResult:
        """Save a context snapshot."""
        start_time = time.time()

        try:
            with self.lock:
                # Serialize context data
                context_json = json.dumps(context.context_data)
                metadata_json = json.dumps(context.metadata)

                # Compress if beneficial
                compressed = False
                if len(context_json) > 1024:
                    context_json = base64.b64encode(
                        gzip.compress(context_json.encode()),
                    ).decode()
                    compressed = True

                if persistence_level in [
                    PersistenceLevel.TEMPORARY,
                    PersistenceLevel.SESSION,
                ]:
                    # Store in Redis for fast access
                    redis_key = f"context:{context.id}"
                    redis_data = {
                        "type": context.type.value,
                        "data": context_json,
                        "metadata": metadata_json,
                        "created_at": context.created_at.isoformat(),
                        "expires_at": context.expires_at.isoformat()
                        if context.expires_at
                        else "",
                        "compressed": compressed,
                        "checksum": context.checksum,
                    }

                    # Set expiration based on persistence level
                    expire_seconds = None
                    if persistence_level == PersistenceLevel.TEMPORARY:
                        expire_seconds = 3600  # 1 hour
                    elif persistence_level == PersistenceLevel.SESSION:
                        expire_seconds = 86400  # 24 hours

                    self.redis_client.set(
                        redis_key, json.dumps(redis_data), ex=expire_seconds,
                    )

                if persistence_level in [
                    PersistenceLevel.PERMANENT,
                    PersistenceLevel.ARCHIVAL,
                ]:
                    # Store in database for persistence
                    with sqlite3.connect(str(self.db_path)) as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO contexts
                            (id, type, context_data, metadata, created_at, expires_at, compressed, checksum)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                context.id,
                                context.type.value,
                                context_json,
                                metadata_json,
                                context.created_at.isoformat(),
                                context.expires_at.isoformat()
                                if context.expires_at
                                else None,
                                compressed,
                                context.checksum,
                            ),
                        )
                        conn.commit()

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="save_context",
                    data={"context_id": context.id},
                    metadata={
                        "persistence_level": persistence_level.value,
                        "compressed": compressed,
                        "storage_size": len(context_json),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to save context {context.id}: {e}")

            return OperationResult(
                success=False,
                operation="save_context",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def load_context(self, context_id: str) -> OperationResult:
        """Load a context snapshot."""
        start_time = time.time()

        try:
            with self.lock:
                # Try Redis first
                redis_key = f"context:{context_id}"
                redis_data = self.redis_client.get(redis_key)

                if redis_data:
                    data = json.loads(redis_data)
                    context = self._dict_to_context(context_id, data)

                    execution_time = time.time() - start_time

                    return OperationResult(
                        success=True,
                        operation="load_context",
                        data=context,
                        metadata={"source": "redis"},
                        execution_time=execution_time,
                    )

                # Try database
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        "SELECT * FROM contexts WHERE id = ?", (context_id,),
                    )
                    row = cursor.fetchone()

                    if not row:
                        execution_time = time.time() - start_time
                        return OperationResult(
                            success=False,
                            operation="load_context",
                            execution_time=execution_time,
                            warnings=[f"Context {context_id} not found"],
                        )

                    context = self._row_to_context(row)

                    execution_time = time.time() - start_time

                    return OperationResult(
                        success=True,
                        operation="load_context",
                        data=context,
                        metadata={"source": "database"},
                        execution_time=execution_time,
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to load context {context_id}: {e}")

            return OperationResult(
                success=False,
                operation="load_context",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def list_contexts(
        self, context_type: ContextType | None = None,
    ) -> OperationResult:
        """List available contexts."""
        start_time = time.time()

        try:
            with self.lock:
                contexts = []

                # Get from Redis
                pattern = "context:*"
                redis_keys = (
                    self.redis_client.keys(pattern)
                    if hasattr(self.redis_client, "keys")
                    else []
                )

                for key in redis_keys:
                    try:
                        key_str = key.decode() if isinstance(key, bytes) else str(key)
                        redis_data = self.redis_client.get(key_str)
                        if redis_data:
                            data = json.loads(redis_data)
                            if (
                                context_type is None
                                or data["type"] == context_type.value
                            ):
                                context_id = key_str.replace("context:", "")
                                context = self._dict_to_context(context_id, data)
                                contexts.append(context)
                    except Exception:
                        continue

                # Get from database
                with sqlite3.connect(str(self.db_path)) as conn:
                    query = "SELECT * FROM contexts"
                    params = []

                    if context_type:
                        query += " WHERE type = ?"
                        params.append(context_type.value)

                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()

                    # Add database contexts that aren't already in the list
                    existing_ids = {c.id for c in contexts}
                    for row in rows:
                        if row[0] not in existing_ids:  # id is first column
                            context = self._row_to_context(row)
                            contexts.append(context)

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="list_contexts",
                    data=contexts,
                    metadata={
                        "context_type": context_type.value if context_type else None,
                        "result_count": len(contexts),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to list contexts: {e}")

            return OperationResult(
                success=False,
                operation="list_contexts",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def delete_context(self, context_id: str) -> OperationResult:
        """Delete a context snapshot."""
        start_time = time.time()

        try:
            with self.lock:
                # Delete from Redis
                redis_key = f"context:{context_id}"
                self.redis_client.delete(redis_key)

                # Delete from database
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        "DELETE FROM contexts WHERE id = ?", (context_id,),
                    )
                    db_deleted = cursor.rowcount > 0
                    conn.commit()

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="delete_context",
                    data={"context_id": context_id},
                    metadata={"deleted_from_db": db_deleted},
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to delete context {context_id}: {e}")

            return OperationResult(
                success=False,
                operation="delete_context",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def cleanup_expired_contexts(self) -> OperationResult:
        """Clean up expired contexts."""
        start_time = time.time()

        try:
            with self.lock:
                current_time = datetime.now()
                deleted_count = 0

                # Clean up database contexts
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        """
                        DELETE FROM contexts
                        WHERE expires_at IS NOT NULL AND expires_at < ?
                    """,
                        (current_time.isoformat(),),
                    )

                    deleted_count += cursor.rowcount
                    conn.commit()

                # Redis contexts expire automatically, but we can check manually
                pattern = "context:*"
                redis_keys = (
                    self.redis_client.keys(pattern)
                    if hasattr(self.redis_client, "keys")
                    else []
                )

                for key in redis_keys:
                    try:
                        key_str = key.decode() if isinstance(key, bytes) else str(key)
                        redis_data = self.redis_client.get(key_str)
                        if redis_data:
                            data = json.loads(redis_data)
                            if data.get("expires_at"):
                                expires_at = datetime.fromisoformat(data["expires_at"])
                                if expires_at < current_time:
                                    self.redis_client.delete(key_str)
                                    deleted_count += 1
                    except Exception:
                        continue

                execution_time = time.time() - start_time

                return OperationResult(
                    success=True,
                    operation="cleanup_expired_contexts",
                    data={"deleted_count": deleted_count},
                    metadata={"cleanup_time": current_time.isoformat()},
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to cleanup expired contexts: {e}")

            return OperationResult(
                success=False,
                operation="cleanup_expired_contexts",
                execution_time=execution_time,
                errors=[str(e)],
            )

    def _dict_to_context(self, context_id: str, data: dict) -> ContextSnapshot:
        """Convert dictionary to ContextSnapshot."""
        context_data = data["data"]

        # Decompress if needed
        if data.get("compressed", False):
            context_data = gzip.decompress(base64.b64decode(context_data)).decode()

        return ContextSnapshot(
            id=context_id,
            type=ContextType(data["type"]),
            context_data=json.loads(context_data),
            metadata=json.loads(data["metadata"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
            compressed=data.get("compressed", False),
            checksum=data.get("checksum", ""),
        )

    def _row_to_context(self, row) -> ContextSnapshot:
        """Convert database row to ContextSnapshot."""
        context_data = row[2]

        # Decompress if needed
        if row[6]:  # compressed flag
            context_data = gzip.decompress(base64.b64decode(context_data)).decode()

        return ContextSnapshot(
            id=row[0],
            type=ContextType(row[1]),
            context_data=json.loads(context_data),
            metadata=json.loads(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            expires_at=datetime.fromisoformat(row[5]) if row[5] else None,
            compressed=row[6],
            checksum=row[7],
        )


class MCPService:
    """Main MCP (Memory and Context Persistence) Service."""

    def __init__(
        self,
        storage_path: str = "./mcp_data",
        redis_url: str | None = None,
        max_workers: int = 10,
        cleanup_interval: int = 3600,
    ) -> None:
        """Initialize the MCP service."""
        self.storage_path = Path(storage_path)
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.cleanup_interval = cleanup_interval

        self.logger = self._setup_logging()

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.memory_manager = MemoryManager(
            str(self.storage_path / "memory"), compression_enabled=True,
        )

        self.context_manager = ContextManager(
            str(self.storage_path / "context"), redis_url=redis_url,
        )

        # Service state
        self.running = False
        self.cleanup_task: asyncio.Task | None = None

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Performance tracking
        self.operation_count = 0
        self.total_operation_time = 0.0

        # Check dependencies
        self.redis_available = REDIS_AVAILABLE
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available, using mock implementation")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the MCP service."""
        logger = logging.getLogger("mcp_service")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def start(self) -> None:
        """Start the MCP service."""
        if self.running:
            self.logger.warning("MCP service is already running")
            return

        self.running = True
        self.logger.info("Starting MCP service")

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("MCP service started successfully")

    async def stop(self) -> None:
        """Stop the MCP service."""
        if not self.running:
            return

        self.logger.info("Stopping MCP service")
        self.running = False

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.cleanup_task

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Close Redis connection if available
        if hasattr(self.context_manager.redis_client, "close"):
            self.context_manager.redis_client.close()

        self.logger.info("MCP service stopped")

    # Memory Operations

    async def store_memory(self, memory: MemoryEntry) -> OperationResult:
        """Store a memory entry."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.memory_manager.store_memory, memory,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def retrieve_memory(self, memory_id: str) -> OperationResult:
        """Retrieve a memory entry."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.memory_manager.retrieve_memory, memory_id,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def query_memories(self, query: RetrievalQuery) -> OperationResult:
        """Query memory entries."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.memory_manager.query_memories, query,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def delete_memory(self, memory_id: str) -> OperationResult:
        """Delete a memory entry."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.memory_manager.delete_memory, memory_id,
        )
        self._update_operation_stats(result.execution_time)
        return result

    # Context Operations

    async def save_context(
        self,
        context: ContextSnapshot,
        persistence_level: PersistenceLevel = PersistenceLevel.SESSION,
    ) -> OperationResult:
        """Save a context snapshot."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.context_manager.save_context, context, persistence_level,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def load_context(self, context_id: str) -> OperationResult:
        """Load a context snapshot."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.context_manager.load_context, context_id,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def list_contexts(
        self, context_type: ContextType | None = None,
    ) -> OperationResult:
        """List available contexts."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.context_manager.list_contexts, context_type,
        )
        self._update_operation_stats(result.execution_time)
        return result

    async def delete_context(self, context_id: str) -> OperationResult:
        """Delete a context snapshot."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self.context_manager.delete_context, context_id,
        )
        self._update_operation_stats(result.execution_time)
        return result

    # High-level convenience methods

    async def store_episodic_memory(
        self, event_description: str, context: dict[str, Any], importance: float = 1.0,
    ) -> OperationResult:
        """Store an episodic memory (event-based)."""
        memory = MemoryEntry(
            id=str(uuid.uuid4()),
            type=MemoryType.EPISODIC,
            content={
                "event": event_description,
                "timestamp": datetime.now().isoformat(),
            },
            context=context,
            metadata={"auto_generated": True},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            importance_score=importance,
            tags=["episodic", "auto"],
        )
        return await self.store_memory(memory)

    async def store_semantic_memory(
        self,
        knowledge: dict[str, Any],
        category: str = "general",
        importance: float = 1.0,
    ) -> OperationResult:
        """Store semantic memory (factual knowledge)."""
        memory = MemoryEntry(
            id=str(uuid.uuid4()),
            type=MemoryType.SEMANTIC,
            content=knowledge,
            context={"category": category},
            metadata={"auto_generated": True},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            importance_score=importance,
            tags=["semantic", category, "auto"],
        )
        return await self.store_memory(memory)

    async def save_session_context(
        self, session_id: str, context_data: dict[str, Any], expires_in_hours: int = 24,
    ) -> OperationResult:
        """Save session context with expiration."""
        context = ContextSnapshot(
            id=session_id,
            type=ContextType.SESSION,
            context_data=context_data,
            metadata={"auto_generated": True, "session_id": session_id},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=expires_in_hours),
        )
        return await self.save_context(context, PersistenceLevel.SESSION)

    async def save_workflow_context(
        self, workflow_id: str, context_data: dict[str, Any],
    ) -> OperationResult:
        """Save workflow context permanently."""
        context = ContextSnapshot(
            id=workflow_id,
            type=ContextType.WORKFLOW,
            context_data=context_data,
            metadata={"auto_generated": True, "workflow_id": workflow_id},
            created_at=datetime.now(),
        )
        return await self.save_context(context, PersistenceLevel.PERMANENT)

    # Analytics and Maintenance

    async def get_system_stats(self) -> OperationResult:
        """Get comprehensive system statistics."""
        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            memory_stats = await loop.run_in_executor(
                self.executor, self.memory_manager.get_stats,
            )

            # Context stats would need to be implemented in ContextManager
            # For now, return memory stats with service-level metrics

            service_stats = {
                "memory_stats": asdict(memory_stats),
                "service_performance": {
                    "total_operations": self.operation_count,
                    "total_operation_time": self.total_operation_time,
                    "average_operation_time": self.total_operation_time
                    / self.operation_count
                    if self.operation_count > 0
                    else 0,
                    "redis_available": self.redis_available,
                },
                "storage_info": {
                    "storage_path": str(self.storage_path),
                    "memory_db_path": str(self.memory_manager.db_path),
                    "context_db_path": str(self.context_manager.db_path),
                },
            }

            execution_time = time.time() - start_time

            return OperationResult(
                success=True,
                operation="get_system_stats",
                data=service_stats,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.exception(f"Failed to get system stats: {e}")

            return OperationResult(
                success=False,
                operation="get_system_stats",
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the MCP service."""
        health_info = {
            "status": "unknown",
            "running": self.running,
            "storage_path": str(self.storage_path),
            "redis_available": self.redis_available,
            "components": {"memory_manager": "unknown", "context_manager": "unknown"},
            "performance": {
                "total_operations": self.operation_count,
                "average_operation_time": self.total_operation_time
                / self.operation_count
                if self.operation_count > 0
                else 0,
            },
        }

        if not self.running:
            health_info["status"] = "stopped"
            return health_info

        try:
            # Test memory manager
            test_memory = MemoryEntry(
                id="health-check-memory",
                type=MemoryType.WORKING,
                content={"test": True},
                context={},
                metadata={"health_check": True},
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                tags=["health_check"],
            )

            memory_result = await self.store_memory(test_memory)
            if memory_result.success:
                health_info["components"]["memory_manager"] = "healthy"
                # Clean up test memory
                await self.delete_memory("health-check-memory")
            else:
                health_info["components"]["memory_manager"] = "unhealthy"

            # Test context manager
            test_context = ContextSnapshot(
                id="health-check-context",
                type=ContextType.SESSION,
                context_data={"test": True},
                metadata={"health_check": True},
                created_at=datetime.now(),
            )

            context_result = await self.save_context(
                test_context, PersistenceLevel.TEMPORARY,
            )
            if context_result.success:
                health_info["components"]["context_manager"] = "healthy"
                # Clean up test context
                await self.delete_context("health-check-context")
            else:
                health_info["components"]["context_manager"] = "unhealthy"

            # Overall status
            all_healthy = all(
                status == "healthy" for status in health_info["components"].values()
            )
            health_info["status"] = "healthy" if all_healthy else "degraded"

        except Exception as e:
            health_info["status"] = "error"
            health_info["error"] = str(e)

        return health_info

    async def _cleanup_loop(self) -> None:
        """Background cleanup task."""
        self.logger.info("Cleanup loop started")

        try:
            while self.running:
                await asyncio.sleep(self.cleanup_interval)

                if not self.running:
                    break

                try:
                    # Clean up expired contexts
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor, self.context_manager.cleanup_expired_contexts,
                    )

                    if result.success and result.data.get("deleted_count", 0) > 0:
                        self.logger.info(
                            f"Cleaned up {result.data['deleted_count']} expired contexts",
                        )

                except Exception as e:
                    self.logger.exception(f"Error during cleanup: {e}")

        except asyncio.CancelledError:
            self.logger.info("Cleanup loop cancelled")

    def _update_operation_stats(self, execution_time: float) -> None:
        """Update operation performance statistics."""
        self.operation_count += 1
        self.total_operation_time += execution_time


# Utility functions for creating common memory and context entries


def create_episodic_memory(
    event_description: str,
    context: dict[str, Any],
    importance: float = 1.0,
    tags: list[str] | None = None,
) -> MemoryEntry:
    """Create an episodic memory entry."""
    if tags is None:
        tags = ["episodic"]

    return MemoryEntry(
        id=str(uuid.uuid4()),
        type=MemoryType.EPISODIC,
        content={
            "event": event_description,
            "timestamp": datetime.now().isoformat(),
            "location": context.get("location", "unknown"),
        },
        context=context,
        metadata={"auto_generated": True},
        created_at=datetime.now(),
        accessed_at=datetime.now(),
        importance_score=importance,
        tags=tags,
    )


def create_semantic_memory(
    knowledge: dict[str, Any], category: str = "general", importance: float = 1.0,
) -> MemoryEntry:
    """Create a semantic memory entry."""
    return MemoryEntry(
        id=str(uuid.uuid4()),
        type=MemoryType.SEMANTIC,
        content=knowledge,
        context={"category": category},
        metadata={"auto_generated": True},
        created_at=datetime.now(),
        accessed_at=datetime.now(),
        importance_score=importance,
        tags=["semantic", category],
    )


def create_session_context(
    session_id: str, context_data: dict[str, Any], expires_in_hours: int = 24,
) -> ContextSnapshot:
    """Create a session context snapshot."""
    return ContextSnapshot(
        id=session_id,
        type=ContextType.SESSION,
        context_data=context_data,
        metadata={"session_id": session_id, "auto_generated": True},
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=expires_in_hours),
    )


def create_workflow_context(
    workflow_id: str, context_data: dict[str, Any],
) -> ContextSnapshot:
    """Create a workflow context snapshot."""
    return ContextSnapshot(
        id=workflow_id,
        type=ContextType.WORKFLOW,
        context_data=context_data,
        metadata={"workflow_id": workflow_id, "auto_generated": True},
        created_at=datetime.now(),
    )


async def main() -> None:
    """Main function for testing the MCP service."""
    service = MCPService(
        storage_path="./test_mcp_data",
        redis_url="redis://localhost:6379/0" if REDIS_AVAILABLE else None,
    )

    try:
        await service.start()

        # Test memory operations
        episodic_memory = create_episodic_memory(
            "User requested new feature implementation",
            {"user": "test_user", "session": "session_123"},
            importance=0.8,
            tags=["feature_request", "user_interaction"],
        )

        await service.store_memory(episodic_memory)

        # Test context operations
        session_context = create_session_context(
            "session_123",
            {
                "user_preferences": {"theme": "dark", "language": "en"},
                "current_project": "test_project",
                "active_tasks": ["task_1", "task_2"],
            },
        )

        await service.save_context(session_context)

        # Test queries
        query = RetrievalQuery(
            query_text="feature request",
            memory_types=[MemoryType.EPISODIC],
            max_results=10,
        )

        await service.query_memories(query)

        # Health check
        await service.health_check()

        # System stats
        stats_result = await service.get_system_stats()
        if stats_result.success:
            stats_result.data["memory_stats"]

    except KeyboardInterrupt:
        pass
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
