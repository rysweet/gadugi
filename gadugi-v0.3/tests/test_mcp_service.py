#!/usr/bin/env python3
"""Tests for MCP (Memory and Context Persistence) Service."""

import asyncio
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add services directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "mcp"))

from mcp_service import (
    ContextManager,
    ContextSnapshot,
    ContextType,
    MCPService,
    MemoryEntry,
    MemoryManager,
    MemoryStats,
    MemoryType,
    OperationResult,
    PersistenceLevel,
    RetrievalQuery,
    RetrievalStrategy,
    create_episodic_memory,
    create_semantic_memory,
    create_session_context,
    create_workflow_context,
)


class TestMCPService(unittest.IsolatedAsyncioTestCase):
    """Test cases for MCP Service."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Initialize MCP service with test storage
        self.service = MCPService(
            storage_path=self.temp_dir,
            redis_url=None,  # Use mock Redis
            cleanup_interval=60,  # Short interval for testing
        )

        # Sample test data
        self.test_memory = MemoryEntry(
            id="test-memory-001",
            type=MemoryType.EPISODIC,
            content={
                "event": "User requested feature",
                "timestamp": datetime.now().isoformat(),
                "details": "Implement new search functionality",
            },
            context={"user": "test_user", "session": "session_123"},
            metadata={"priority": "high", "category": "feature_request"},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            importance_score=0.8,
            tags=["feature", "search", "user_request"],
        )

        self.test_context = ContextSnapshot(
            id="test-context-001",
            type=ContextType.SESSION,
            context_data={
                "user_preferences": {"theme": "dark", "language": "en"},
                "current_project": "test_project",
                "active_tasks": ["task_1", "task_2"],
            },
            metadata={"session_id": "session_123", "user": "test_user"},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
        )

    async def asyncTearDown(self) -> None:
        """Clean up test fixtures."""
        if self.service.running:
            await self.service.stop()

        # Clean up temporary directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_service_initialization(self) -> None:
        """Test service initializes properly."""
        assert self.service is not None
        assert self.service.memory_manager is not None
        assert self.service.context_manager is not None
        assert self.service.logger is not None
        assert not self.service.running
        assert self.service.operation_count == 0
        assert self.service.total_operation_time == 0.0

    def test_memory_type_enum(self) -> None:
        """Test MemoryType enum functionality."""
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.PROCEDURAL.value == "procedural"
        assert MemoryType.WORKING.value == "working"
        assert MemoryType.DECLARATIVE.value == "declarative"
        assert MemoryType.ASSOCIATIVE.value == "associative"

    def test_context_type_enum(self) -> None:
        """Test ContextType enum functionality."""
        assert ContextType.SESSION.value == "session"
        assert ContextType.WORKFLOW.value == "workflow"
        assert ContextType.AGENT.value == "agent"
        assert ContextType.TASK.value == "task"
        assert ContextType.CONVERSATION.value == "conversation"
        assert ContextType.PROJECT.value == "project"

    def test_persistence_level_enum(self) -> None:
        """Test PersistenceLevel enum functionality."""
        assert PersistenceLevel.TEMPORARY.value == "temporary"
        assert PersistenceLevel.SESSION.value == "session"
        assert PersistenceLevel.PERMANENT.value == "permanent"
        assert PersistenceLevel.ARCHIVAL.value == "archival"

    def test_retrieval_strategy_enum(self) -> None:
        """Test RetrievalStrategy enum functionality."""
        assert RetrievalStrategy.CHRONOLOGICAL.value == "chronological"
        assert RetrievalStrategy.RELEVANCE.value == "relevance"
        assert RetrievalStrategy.FREQUENCY.value == "frequency"
        assert RetrievalStrategy.RECENCY.value == "recency"
        assert RetrievalStrategy.IMPORTANCE.value == "importance"
        assert RetrievalStrategy.ASSOCIATIVE.value == "associative"

    def test_memory_entry_dataclass(self) -> None:
        """Test MemoryEntry dataclass functionality."""
        memory = MemoryEntry(
            id="test-123",
            type=MemoryType.SEMANTIC,
            content={"fact": "Python is a programming language"},
            context={"domain": "programming"},
            metadata={"confidence": 0.9},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            importance_score=0.7,
            tags=["python", "programming"],
        )

        assert memory.id == "test-123"
        assert memory.type == MemoryType.SEMANTIC
        assert memory.content["fact"] == "Python is a programming language"
        assert memory.importance_score == 0.7
        assert memory.access_count == 0  # Default value
        assert "python" in memory.tags

    def test_context_snapshot_dataclass(self) -> None:
        """Test ContextSnapshot dataclass functionality."""
        context = ContextSnapshot(
            id="context-456",
            type=ContextType.WORKFLOW,
            context_data={"step": 1, "variables": {"x": 10}},
            metadata={"workflow_name": "test_workflow"},
            created_at=datetime.now(),
        )

        assert context.id == "context-456"
        assert context.type == ContextType.WORKFLOW
        assert context.context_data["step"] == 1
        assert context.expires_at is None  # Default
        assert not context.compressed  # Default
        assert context.checksum != ""  # Should be calculated

    def test_context_snapshot_checksum(self) -> None:
        """Test context snapshot checksum calculation."""
        context_data = {"test": "data", "number": 42}

        context1 = ContextSnapshot(
            id="test-1",
            type=ContextType.SESSION,
            context_data=context_data,
            metadata={},
            created_at=datetime.now(),
        )

        context2 = ContextSnapshot(
            id="test-2",
            type=ContextType.SESSION,
            context_data=context_data,
            metadata={},
            created_at=datetime.now(),
        )

        # Same data should produce same checksum
        assert context1.checksum == context2.checksum

        # Different data should produce different checksum
        context3 = ContextSnapshot(
            id="test-3",
            type=ContextType.SESSION,
            context_data={"different": "data"},
            metadata={},
            created_at=datetime.now(),
        )

        assert context1.checksum != context3.checksum

    def test_retrieval_query_dataclass(self) -> None:
        """Test RetrievalQuery dataclass functionality."""
        query = RetrievalQuery(
            query_text="search term",
            memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            tags=["important"],
            max_results=50,
            strategy=RetrievalStrategy.IMPORTANCE,
        )

        assert query.query_text == "search term"
        assert len(query.memory_types) == 2
        assert MemoryType.EPISODIC in query.memory_types
        assert query.max_results == 50
        assert query.strategy == RetrievalStrategy.IMPORTANCE
        assert query.include_context  # Default

    def test_operation_result_dataclass(self) -> None:
        """Test OperationResult dataclass functionality."""
        result = OperationResult(
            success=True,
            operation="test_operation",
            data={"result": "success"},
            metadata={"execution_time": 1.5},
            execution_time=1.5,
            warnings=["minor warning"],
        )

        assert result.success
        assert result.operation == "test_operation"
        assert result.data["result"] == "success"
        assert result.execution_time == 1.5
        assert len(result.warnings) == 1
        assert len(result.errors) == 0  # Default empty list

    def test_memory_stats_dataclass(self) -> None:
        """Test MemoryStats dataclass functionality."""
        stats = MemoryStats(
            total_memories=100,
            memories_by_type={"episodic": 60, "semantic": 40},
            total_contexts=25,
            storage_size=1024000,
            cache_hit_rate=0.85,
        )

        assert stats.total_memories == 100
        assert stats.memories_by_type["episodic"] == 60
        assert stats.total_contexts == 25
        assert stats.cache_hit_rate == 0.85
        assert stats.last_cleanup is not None  # Default value

    async def test_service_start_stop(self) -> None:
        """Test service start and stop functionality."""
        assert not self.service.running

        await self.service.start()
        assert self.service.running
        assert self.service.cleanup_task is not None

        await self.service.stop()
        assert not self.service.running

    async def test_store_memory_success(self) -> None:
        """Test successful memory storage."""
        await self.service.start()

        result = await self.service.store_memory(self.test_memory)

        assert result.success
        assert result.operation == "store_memory"
        assert "memory_id" in result.data
        assert result.data["memory_id"] == self.test_memory.id
        assert result.execution_time > 0

    async def test_retrieve_memory_success(self) -> None:
        """Test successful memory retrieval."""
        await self.service.start()

        # Store memory first
        store_result = await self.service.store_memory(self.test_memory)
        assert store_result.success

        # Retrieve memory
        result = await self.service.retrieve_memory(self.test_memory.id)

        assert result.success
        assert result.operation == "retrieve_memory"
        assert result.data is not None
        assert result.data.id == self.test_memory.id
        assert result.data.content["event"] == "User requested feature"

    async def test_retrieve_memory_not_found(self) -> None:
        """Test memory retrieval when memory doesn't exist."""
        await self.service.start()

        result = await self.service.retrieve_memory("nonexistent-memory")

        assert not result.success
        assert len(result.warnings) == 1
        assert "not found" in result.warnings[0]

    async def test_query_memories_success(self) -> None:
        """Test successful memory querying."""
        await self.service.start()

        # Store multiple memories
        memories = [
            MemoryEntry(
                id=f"memory-{i}",
                type=MemoryType.EPISODIC,
                content={"event": f"Event {i}", "importance": i * 0.2},
                context={"session": "test"},
                metadata={},
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                importance_score=i * 0.2,
                tags=["test", f"event_{i}"],
            )
            for i in range(1, 6)
        ]

        for memory in memories:
            store_result = await self.service.store_memory(memory)
            assert store_result.success

        # Query memories
        query = RetrievalQuery(
            memory_types=[MemoryType.EPISODIC],
            tags=["test"],
            max_results=10,
            strategy=RetrievalStrategy.IMPORTANCE,
        )

        result = await self.service.query_memories(query)

        assert result.success
        assert result.operation == "query_memories"
        assert len(result.data) >= 5
        assert result.metadata["result_count"] == len(result.data)

        # Results should be ordered by importance (descending)
        for i in range(len(result.data) - 1):
            assert result.data[i].importance_score >= result.data[i + 1].importance_score

    async def test_delete_memory_success(self) -> None:
        """Test successful memory deletion."""
        await self.service.start()

        # Store memory first
        store_result = await self.service.store_memory(self.test_memory)
        assert store_result.success

        # Delete memory
        result = await self.service.delete_memory(self.test_memory.id)

        assert result.success
        assert result.operation == "delete_memory"
        assert result.data["memory_id"] == self.test_memory.id

        # Verify memory is deleted
        retrieve_result = await self.service.retrieve_memory(self.test_memory.id)
        assert not retrieve_result.success

    async def test_save_context_success(self) -> None:
        """Test successful context saving."""
        await self.service.start()

        result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.SESSION,
        )

        assert result.success
        assert result.operation == "save_context"
        assert result.data["context_id"] == self.test_context.id
        assert result.metadata["persistence_level"] == "session"

    async def test_load_context_success(self) -> None:
        """Test successful context loading."""
        await self.service.start()

        # Save context first
        save_result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.SESSION,
        )
        assert save_result.success

        # Load context
        result = await self.service.load_context(self.test_context.id)

        assert result.success
        assert result.operation == "load_context"
        assert result.data is not None
        assert result.data.id == self.test_context.id
        assert result.data.context_data["user_preferences"]["theme"] == "dark"

    async def test_load_context_not_found(self) -> None:
        """Test context loading when context doesn't exist."""
        await self.service.start()

        result = await self.service.load_context("nonexistent-context")

        assert not result.success
        assert len(result.warnings) == 1
        assert "not found" in result.warnings[0]

    async def test_list_contexts_success(self) -> None:
        """Test successful context listing."""
        await self.service.start()

        # Save multiple contexts
        contexts = [
            ContextSnapshot(
                id=f"context-{i}",
                type=ContextType.SESSION if i % 2 == 0 else ContextType.WORKFLOW,
                context_data={"data": f"value_{i}"},
                metadata={"index": i},
                created_at=datetime.now(),
            )
            for i in range(1, 4)
        ]

        for context in contexts:
            save_result = await self.service.save_context(
                context,
                PersistenceLevel.PERMANENT,
            )
            assert save_result.success

        # List all contexts
        result = await self.service.list_contexts()

        assert result.success
        assert result.operation == "list_contexts"
        assert len(result.data) >= 3
        assert result.metadata["result_count"] == len(result.data)

        # List contexts by type
        session_result = await self.service.list_contexts(ContextType.SESSION)

        assert session_result.success
        session_contexts = [c for c in session_result.data if c.type == ContextType.SESSION]
        assert len(session_contexts) >= 1

    async def test_delete_context_success(self) -> None:
        """Test successful context deletion."""
        await self.service.start()

        # Save context first
        save_result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.PERMANENT,
        )
        assert save_result.success

        # Delete context
        result = await self.service.delete_context(self.test_context.id)

        assert result.success
        assert result.operation == "delete_context"
        assert result.data["context_id"] == self.test_context.id

        # Verify context is deleted
        load_result = await self.service.load_context(self.test_context.id)
        assert not load_result.success

    async def test_store_episodic_memory_convenience(self) -> None:
        """Test episodic memory convenience method."""
        await self.service.start()

        result = await self.service.store_episodic_memory(
            "User completed task successfully",
            {"user": "test_user", "task_id": "task_123"},
            importance=0.9,
        )

        assert result.success
        assert result.operation == "store_memory"

        # Retrieve and verify the stored memory
        memory_id = result.data["memory_id"]
        retrieve_result = await self.service.retrieve_memory(memory_id)

        assert retrieve_result.success
        assert retrieve_result.data.type == MemoryType.EPISODIC
        assert retrieve_result.data.content["event"] == "User completed task successfully"
        assert retrieve_result.data.importance_score == 0.9
        assert "episodic" in retrieve_result.data.tags

    async def test_store_semantic_memory_convenience(self) -> None:
        """Test semantic memory convenience method."""
        await self.service.start()

        knowledge = {
            "concept": "Machine Learning",
            "definition": "A subset of AI that enables computers to learn from data",
            "applications": ["image recognition", "natural language processing"],
        }

        result = await self.service.store_semantic_memory(
            knowledge,
            category="technology",
            importance=0.8,
        )

        assert result.success

        # Retrieve and verify
        memory_id = result.data["memory_id"]
        retrieve_result = await self.service.retrieve_memory(memory_id)

        assert retrieve_result.success
        assert retrieve_result.data.type == MemoryType.SEMANTIC
        assert retrieve_result.data.content["concept"] == "Machine Learning"
        assert "technology" in retrieve_result.data.tags

    async def test_save_session_context_convenience(self) -> None:
        """Test session context convenience method."""
        await self.service.start()

        context_data = {
            "user_id": "user_123",
            "preferences": {"notifications": True},
            "current_view": "dashboard",
        }

        result = await self.service.save_session_context(
            "session_456",
            context_data,
            expires_in_hours=12,
        )

        assert result.success

        # Load and verify
        load_result = await self.service.load_context("session_456")

        assert load_result.success
        assert load_result.data.type == ContextType.SESSION
        assert load_result.data.context_data["user_id"] == "user_123"
        assert load_result.data.expires_at is not None

    async def test_save_workflow_context_convenience(self) -> None:
        """Test workflow context convenience method."""
        await self.service.start()

        context_data = {
            "workflow_name": "data_processing",
            "current_step": 3,
            "variables": {"input_file": "data.csv", "processed_rows": 1500},
        }

        result = await self.service.save_workflow_context("workflow_789", context_data)

        assert result.success

        # Load and verify
        load_result = await self.service.load_context("workflow_789")

        assert load_result.success
        assert load_result.data.type == ContextType.WORKFLOW
        assert load_result.data.context_data["workflow_name"] == "data_processing"
        assert load_result.data.expires_at is None  # Permanent context

    async def test_get_system_stats(self) -> None:
        """Test system statistics retrieval."""
        await self.service.start()

        # Store some data
        await self.service.store_memory(self.test_memory)
        await self.service.save_context(self.test_context, PersistenceLevel.SESSION)

        result = await self.service.get_system_stats()

        assert result.success
        assert result.operation == "get_system_stats"
        assert "memory_stats" in result.data
        assert "service_performance" in result.data
        assert "storage_info" in result.data

        # Check service performance stats
        perf_stats = result.data["service_performance"]
        assert perf_stats["total_operations"] > 0
        assert perf_stats["total_operation_time"] >= 0

    async def test_health_check_healthy(self) -> None:
        """Test health check when service is healthy."""
        await self.service.start()

        health = await self.service.health_check()

        assert health["status"] == "healthy"
        assert health["running"]
        assert health["components"]["memory_manager"] == "healthy"
        assert health["components"]["context_manager"] == "healthy"
        assert "performance" in health

    async def test_health_check_stopped(self) -> None:
        """Test health check when service is stopped."""
        health = await self.service.health_check()

        assert health["status"] == "stopped"
        assert not health["running"]

    def test_create_episodic_memory_utility(self) -> None:
        """Test episodic memory creation utility."""
        memory = create_episodic_memory(
            "Important event occurred",
            {"location": "office", "participants": ["alice", "bob"]},
            importance=0.9,
            tags=["important", "meeting"],
        )

        assert memory.type == MemoryType.EPISODIC
        assert memory.content["event"] == "Important event occurred"
        assert memory.importance_score == 0.9
        assert "important" in memory.tags
        assert "episodic" in memory.tags
        assert memory.context["location"] == "office"

    def test_create_semantic_memory_utility(self) -> None:
        """Test semantic memory creation utility."""
        knowledge = {
            "term": "RESTful API",
            "definition": "An API that follows REST architectural style",
            "principles": ["stateless", "cacheable", "uniform interface"],
        }

        memory = create_semantic_memory(
            knowledge,
            category="software_engineering",
            importance=0.7,
        )

        assert memory.type == MemoryType.SEMANTIC
        assert memory.content["term"] == "RESTful API"
        assert memory.importance_score == 0.7
        assert "semantic" in memory.tags
        assert "software_engineering" in memory.tags
        assert memory.context["category"] == "software_engineering"

    def test_create_session_context_utility(self) -> None:
        """Test session context creation utility."""
        context_data = {
            "user": "test_user",
            "permissions": ["read", "write"],
            "last_activity": datetime.now().isoformat(),
        }

        context = create_session_context(
            "session_abc",
            context_data,
            expires_in_hours=6,
        )

        assert context.type == ContextType.SESSION
        assert context.id == "session_abc"
        assert context.context_data["user"] == "test_user"
        assert context.expires_at is not None
        assert context.metadata["session_id"] == "session_abc"

    def test_create_workflow_context_utility(self) -> None:
        """Test workflow context creation utility."""
        context_data = {
            "process": "ml_training",
            "epoch": 15,
            "loss": 0.0045,
            "accuracy": 0.97,
        }

        context = create_workflow_context("training_workflow_xyz", context_data)

        assert context.type == ContextType.WORKFLOW
        assert context.id == "training_workflow_xyz"
        assert context.context_data["process"] == "ml_training"
        assert context.expires_at is None  # Permanent workflow context
        assert context.metadata["workflow_id"] == "training_workflow_xyz"

    def test_memory_manager_initialization(self) -> None:
        """Test MemoryManager initialization."""
        storage_path = os.path.join(self.temp_dir, "test_memory")
        manager = MemoryManager(storage_path, compression_enabled=True)

        assert manager is not None
        assert Path(storage_path).exists()
        assert manager.compression_enabled
        assert len(manager.memory_cache) == 0
        assert manager.cache_max_size == 10000

        # Check database initialization
        assert manager.db_path.exists()

    def test_context_manager_initialization(self) -> None:
        """Test ContextManager initialization."""
        storage_path = os.path.join(self.temp_dir, "test_context")
        manager = ContextManager(storage_path, redis_url=None)

        assert manager is not None
        assert Path(storage_path).exists()
        assert manager.redis_client is not None  # Mock Redis

        # Check database initialization
        assert manager.db_path.exists()

    def test_memory_database_schema(self) -> None:
        """Test memory database schema creation."""
        storage_path = os.path.join(self.temp_dir, "test_memory_db")
        manager = MemoryManager(storage_path)

        # Check if tables exist
        with sqlite3.connect(str(manager.db_path)) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "memories" in tables
            assert "memories_fts" in tables

            # Check indexes
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]

            # Should have at least our custom indexes
            index_names = [name for name in indexes if name.startswith("idx_memories")]
            assert len(index_names) > 0

    def test_context_database_schema(self) -> None:
        """Test context database schema creation."""
        storage_path = os.path.join(self.temp_dir, "test_context_db")
        manager = ContextManager(storage_path)

        # Check if tables exist
        with sqlite3.connect(str(manager.db_path)) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "contexts" in tables

            # Check indexes
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]

            # Should have at least our custom indexes
            index_names = [name for name in indexes if name.startswith("idx_contexts")]
            assert len(index_names) > 0

    def test_operation_stats_tracking(self) -> None:
        """Test operation statistics tracking."""
        assert self.service.operation_count == 0
        assert self.service.total_operation_time == 0.0

        # Simulate operation stats update
        self.service._update_operation_stats(1.5)

        assert self.service.operation_count == 1
        assert self.service.total_operation_time == 1.5

        # Add another operation
        self.service._update_operation_stats(0.8)

        assert self.service.operation_count == 2
        assert self.service.total_operation_time == 2.3

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.service.logger is not None
        assert self.service.logger.name == "mcp_service"

        # Test component loggers
        assert self.service.memory_manager.logger.name == "mcp_memory"
        assert self.service.context_manager.logger.name == "mcp_context"

    def test_redis_availability_detection(self) -> None:
        """Test Redis availability detection."""
        assert isinstance(self.service.redis_available, bool)

        # Service should handle missing Redis gracefully
        assert self.service.context_manager.redis_client is not None

    async def test_cleanup_loop_functionality(self) -> None:
        """Test cleanup loop functionality."""
        # Set short cleanup interval for testing
        self.service.cleanup_interval = 0.1

        await self.service.start()

        # Let cleanup loop run a few times
        await asyncio.sleep(0.3)

        # Cleanup task should be running
        assert self.service.cleanup_task is not None
        assert not self.service.cleanup_task.done()

        await self.service.stop()

        # Cleanup task should be cancelled
        assert self.service.cleanup_task.done()

    async def test_concurrent_operations(self) -> None:
        """Test concurrent memory and context operations."""
        await self.service.start()

        # Create multiple operations
        memory_tasks = []
        context_tasks = []

        for i in range(5):
            memory = MemoryEntry(
                id=f"concurrent-memory-{i}",
                type=MemoryType.WORKING,
                content={"data": f"value_{i}"},
                context={"session": f"session_{i}"},
                metadata={"index": i},
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                tags=["concurrent", "test"],
            )
            memory_tasks.append(self.service.store_memory(memory))

            context = ContextSnapshot(
                id=f"concurrent-context-{i}",
                type=ContextType.TASK,
                context_data={"task": f"task_{i}"},
                metadata={"index": i},
                created_at=datetime.now(),
            )
            context_tasks.append(
                self.service.save_context(context, PersistenceLevel.TEMPORARY),
            )

        # Execute all operations concurrently
        memory_results = await asyncio.gather(*memory_tasks)
        context_results = await asyncio.gather(*context_tasks)

        # All operations should succeed
        for result in memory_results:
            assert result.success

        for result in context_results:
            assert result.success


class TestMemoryManager(unittest.TestCase):
    """Test cases for MemoryManager component."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MemoryManager(self.temp_dir, compression_enabled=True)

        self.test_memory = MemoryEntry(
            id="test-memory",
            type=MemoryType.EPISODIC,
            content={
                "event": "Test event",
                "data": "x" * 2000,
            },  # Large content for compression test
            context={"test": True},
            metadata={"compressed_test": True},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            tags=["test", "compression"],
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve_memory(self) -> None:
        """Test memory storage and retrieval."""
        # Store memory
        store_result = self.manager.store_memory(self.test_memory)
        assert store_result.success

        # Retrieve memory
        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        assert retrieve_result.success

        retrieved_memory = retrieve_result.data
        assert retrieved_memory.id == self.test_memory.id
        assert retrieved_memory.content["event"] == "Test event"
        assert retrieved_memory.access_count == 1  # Incremented on retrieval

    def test_memory_compression(self) -> None:
        """Test memory compression functionality."""
        # Large content should trigger compression
        large_memory = MemoryEntry(
            id="large-memory",
            type=MemoryType.SEMANTIC,
            content={"large_data": "x" * 2000},  # 2KB+ should trigger compression
            context={},
            metadata={},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            tags=["compression_test"],
        )

        result = self.manager.store_memory(large_memory)
        assert result.success
        assert result.metadata.get("compressed", False)

        # Retrieve and verify decompression
        retrieve_result = self.manager.retrieve_memory("large-memory")
        assert retrieve_result.success
        assert len(retrieve_result.data.content["large_data"]) == 2000

    def test_cache_functionality(self) -> None:
        """Test memory caching."""
        # Store memory (should be cached)
        store_result = self.manager.store_memory(self.test_memory)
        assert store_result.success

        # Should be in cache
        assert self.test_memory.id in self.manager.memory_cache

        # Retrieve should hit cache
        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        assert retrieve_result.success
        assert retrieve_result.metadata["source"] == "cache"

        # Clear cache and retrieve again (should hit database)
        self.manager.memory_cache.clear()
        self.manager.cache_access_order.clear()

        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        assert retrieve_result.success
        assert retrieve_result.metadata["source"] == "database"


class TestContextManager(unittest.TestCase):
    """Test cases for ContextManager component."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ContextManager(self.temp_dir, redis_url=None)  # Use mock Redis

        self.test_context = ContextSnapshot(
            id="test-context",
            type=ContextType.SESSION,
            context_data={"user": "test", "data": {"key": "value"}},
            metadata={"test": True},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_and_load_context(self) -> None:
        """Test context saving and loading."""
        # Save context
        save_result = self.manager.save_context(
            self.test_context,
            PersistenceLevel.PERMANENT,
        )
        assert save_result.success

        # Load context
        load_result = self.manager.load_context(self.test_context.id)
        assert load_result.success

        loaded_context = load_result.data
        assert loaded_context.id == self.test_context.id
        assert loaded_context.context_data["user"] == "test"
        assert loaded_context.checksum == self.test_context.checksum

    def test_context_compression(self) -> None:
        """Test context compression functionality."""
        # Large context should trigger compression
        large_context = ContextSnapshot(
            id="large-context",
            type=ContextType.WORKFLOW,
            context_data={"large_data": "x" * 2000},  # Large data
            metadata={},
            created_at=datetime.now(),
        )

        save_result = self.manager.save_context(
            large_context,
            PersistenceLevel.PERMANENT,
        )
        assert save_result.success
        assert save_result.metadata.get("compressed", False)

        # Load and verify decompression
        load_result = self.manager.load_context("large-context")
        assert load_result.success
        assert len(load_result.data.context_data["large_data"]) == 2000

    def test_list_contexts_filtering(self) -> None:
        """Test context listing with filtering."""
        # Save contexts of different types
        session_context = ContextSnapshot(
            id="session-ctx",
            type=ContextType.SESSION,
            context_data={"type": "session"},
            metadata={},
            created_at=datetime.now(),
        )

        workflow_context = ContextSnapshot(
            id="workflow-ctx",
            type=ContextType.WORKFLOW,
            context_data={"type": "workflow"},
            metadata={},
            created_at=datetime.now(),
        )

        self.manager.save_context(session_context, PersistenceLevel.PERMANENT)
        self.manager.save_context(workflow_context, PersistenceLevel.PERMANENT)

        # List all contexts
        all_result = self.manager.list_contexts()
        assert all_result.success
        assert len(all_result.data) >= 2

        # List session contexts only
        session_result = self.manager.list_contexts(ContextType.SESSION)
        assert session_result.success

        session_contexts = [c for c in session_result.data if c.type == ContextType.SESSION]
        assert len(session_contexts) >= 1


if __name__ == "__main__":
    unittest.main()
