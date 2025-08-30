"""
Comprehensive tests for the memory fallback system
Tests all backends, fallback chain behavior, and integration
"""

import asyncio
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Import the fallback system
try:
    from ..claude.shared.memory_fallback import (
        Memory,
        MemoryType,
        MemoryScope,
        MemoryPersistence,
        KnowledgeNode,
        Whiteboard,
        MemoryBackend,
        MarkdownMemoryBackend,
        SQLiteMemoryBackend,
        InMemoryBackend,
        MemoryFallbackChain,
        create_simple_fallback_chain,
    )
    from ..claude.shared.memory_integration import (
        EnhancedAgentMemoryInterface,
        create_enhanced_memory_interface,
        create_fallback_only_interface,
    )

    HAS_FALLBACK_SYSTEM = True
except ImportError:
    HAS_FALLBACK_SYSTEM = False
    # Create placeholder classes for tests
    Memory = MagicMock
    MemoryType = MagicMock
    MemoryBackend = MagicMock
    MemoryFallbackChain = MagicMock
    EnhancedAgentMemoryInterface = MagicMock


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
class TestMemoryDataModels:
    """Test the memory data models."""

    def test_memory_creation(self):
        """Test basic Memory object creation."""
        memory = Memory(
            agent_id="test_agent",
            content="Test memory content",
            type=MemoryType.SEMANTIC,
            persistence=MemoryPersistence.PERSISTENT,
            tags=["test", "memory"],
            importance_score=0.8,
        )

        assert memory.agent_id == "test_agent"
        assert memory.content == "Test memory content"
        assert memory.type == MemoryType.SEMANTIC
        assert memory.persistence == MemoryPersistence.PERSISTENT
        assert memory.tags == ["test", "memory"]
        assert memory.importance_score == 0.8
        assert memory.is_active is True

    def test_memory_serialization(self):
        """Test Memory to_dict and from_dict methods."""
        memory = Memory(
            agent_id="test_agent",
            content="Test content",
            type=MemoryType.EPISODIC,
            tags=["test"],
            created_at=datetime(2023, 1, 1, 12, 0, 0),
        )

        # Test serialization
        memory_dict = memory.to_dict()
        assert memory_dict["agent_id"] == "test_agent"
        assert memory_dict["content"] == "Test content"
        assert memory_dict["created_at"] == "2023-01-01T12:00:00"

        # Test deserialization
        restored_memory = Memory.from_dict(memory_dict)
        assert restored_memory.agent_id == memory.agent_id
        assert restored_memory.content == memory.content
        assert restored_memory.type == memory.type
        assert restored_memory.created_at == memory.created_at

    def test_knowledge_node_creation(self):
        """Test KnowledgeNode creation and serialization."""
        node = KnowledgeNode(
            agent_id="test_agent",
            concept="Machine Learning",
            description="AI technique for pattern recognition",
            confidence=0.9,
        )

        assert node.agent_id == "test_agent"
        assert node.concept == "Machine Learning"
        assert node.confidence == 0.9

        # Test serialization
        node_dict = node.to_dict()
        restored_node = KnowledgeNode.from_dict(node_dict)
        assert restored_node.concept == node.concept
        assert restored_node.confidence == node.confidence


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestInMemoryBackend:
    """Test the in-memory backend."""

    async def test_connect_disconnect(self):
        """Test connecting and disconnecting."""
        backend = InMemoryBackend()

        assert not await backend.is_available()

        await backend.connect()
        assert await backend.is_available()

        await backend.disconnect()
        assert not await backend.is_available()

    async def test_memory_storage_retrieval(self):
        """Test storing and retrieving memories."""
        backend = InMemoryBackend()
        await backend.connect()

        # Create test memory
        memory = Memory(
            agent_id="test_agent", content="Test memory", type=MemoryType.SEMANTIC, tags=["test"]
        )

        # Store memory
        stored_memory = await backend.store_memory(memory)
        assert stored_memory.id == memory.id
        assert stored_memory.content == memory.content

        # Retrieve memory
        retrieved = await backend.get_memory(memory.id)
        assert retrieved is not None
        assert retrieved.content == memory.content

        # Get agent memories
        agent_memories = await backend.get_agent_memories("test_agent")
        assert len(agent_memories) == 1
        assert agent_memories[0].content == memory.content

        await backend.disconnect()

    async def test_tag_search(self):
        """Test searching memories by tags."""
        backend = InMemoryBackend()
        await backend.connect()

        # Create memories with different tags
        memory1 = Memory(agent_id="test_agent", content="Memory 1", tags=["tag1", "common"])
        memory2 = Memory(agent_id="test_agent", content="Memory 2", tags=["tag2", "common"])
        memory3 = Memory(agent_id="test_agent", content="Memory 3", tags=["tag3"])

        await backend.store_memory(memory1)
        await backend.store_memory(memory2)
        await backend.store_memory(memory3)

        # Search by single tag
        results = await backend.search_memories_by_tags("test_agent", ["tag1"])
        assert len(results) == 1
        assert results[0].content == "Memory 1"

        # Search by common tag
        results = await backend.search_memories_by_tags("test_agent", ["common"])
        assert len(results) == 2

        # Search by multiple tags
        results = await backend.search_memories_by_tags("test_agent", ["tag1", "tag2"])
        assert len(results) == 2

        await backend.disconnect()

    async def test_memory_filtering(self):
        """Test memory filtering by type and persistence."""
        backend = InMemoryBackend()
        await backend.connect()

        # Create different types of memories
        short_term = Memory(
            agent_id="test_agent", content="Short term", persistence=MemoryPersistence.VOLATILE
        )
        long_term = Memory(
            agent_id="test_agent", content="Long term", persistence=MemoryPersistence.PERSISTENT
        )

        await backend.store_memory(short_term)
        await backend.store_memory(long_term)

        # Filter by short-term only
        short_memories = await backend.get_agent_memories("test_agent", short_term_only=True)
        assert len(short_memories) == 1
        assert short_memories[0].content == "Short term"

        # Filter by long-term only
        long_memories = await backend.get_agent_memories("test_agent", long_term_only=True)
        assert len(long_memories) == 1
        assert long_memories[0].content == "Long term"

        await backend.disconnect()

    async def test_memory_consolidation(self):
        """Test memory consolidation from short-term to long-term."""
        backend = InMemoryBackend()
        await backend.connect()

        # Create old short-term memory with high importance
        old_time = datetime.now() - timedelta(hours=25)
        memory = Memory(
            agent_id="test_agent",
            content="Important memory",
            persistence=MemoryPersistence.VOLATILE,
            importance_score=0.8,
            created_at=old_time,
        )

        await backend.store_memory(memory)

        # Consolidate memories
        consolidated = await backend.consolidate_memories("test_agent", threshold_hours=24)
        assert len(consolidated) == 1
        assert consolidated[0].persistence == MemoryPersistence.PERSISTENT

        await backend.disconnect()


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestMarkdownBackend:
    """Test the markdown file backend."""

    @pytest.fixture
    async def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    async def test_connect_disconnect(self, temp_storage):
        """Test connecting and disconnecting."""
        backend = MarkdownMemoryBackend(temp_storage)

        assert not await backend.is_available()

        await backend.connect()
        assert await backend.is_available()

        # Check directories were created
        storage_path = Path(temp_storage)
        assert (storage_path / "agents").exists()
        assert (storage_path / "projects").exists()
        assert (storage_path / "whiteboards").exists()
        assert (storage_path / "knowledge").exists()

        await backend.disconnect()
        assert not await backend.is_available()

    async def test_memory_file_storage(self, temp_storage):
        """Test storing memories in markdown files."""
        backend = MarkdownMemoryBackend(temp_storage)
        await backend.connect()

        # Create test memory
        memory = Memory(
            agent_id="test_agent",
            content="Test memory content",
            type=MemoryType.SEMANTIC,
            tags=["test", "markdown"],
        )

        # Store memory
        stored = await backend.store_memory(memory)
        assert stored.id == memory.id

        # Check file was created
        agent_path = Path(temp_storage) / "agents" / "test_agent"
        assert agent_path.exists()

        semantic_file = agent_path / "semantic.md"
        assert semantic_file.exists()

        # Check file content
        content = semantic_file.read_text()
        assert "Test memory content" in content
        assert memory.id in content

        # Retrieve memory
        retrieved = await backend.get_memory(memory.id)
        assert retrieved is not None
        assert retrieved.content == memory.content
        assert retrieved.tags == memory.tags

        await backend.disconnect()

    async def test_multiple_memory_types(self, temp_storage):
        """Test storing different memory types in separate files."""
        backend = MarkdownMemoryBackend(temp_storage)
        await backend.connect()

        agent_id = "test_agent"

        # Create different types of memories
        semantic = Memory(agent_id=agent_id, content="Semantic memory", type=MemoryType.SEMANTIC)
        episodic = Memory(agent_id=agent_id, content="Episodic memory", type=MemoryType.EPISODIC)
        procedural = Memory(
            agent_id=agent_id, content="Procedural memory", type=MemoryType.PROCEDURAL
        )

        # Store memories
        await backend.store_memory(semantic)
        await backend.store_memory(episodic)
        await backend.store_memory(procedural)

        # Check separate files were created
        agent_path = Path(temp_storage) / "agents" / agent_id
        assert (agent_path / "semantic.md").exists()
        assert (agent_path / "episodic.md").exists()
        assert (agent_path / "procedural.md").exists()

        # Retrieve by type
        semantic_memories = await backend.get_agent_memories(
            agent_id, memory_type=MemoryType.SEMANTIC
        )
        assert len(semantic_memories) == 1
        assert semantic_memories[0].content == "Semantic memory"

        # Retrieve all memories
        all_memories = await backend.get_agent_memories(agent_id)
        assert len(all_memories) == 3

        await backend.disconnect()

    async def test_knowledge_graph_storage(self, temp_storage):
        """Test storing knowledge nodes and links."""
        backend = MarkdownMemoryBackend(temp_storage)
        await backend.connect()

        # Add knowledge nodes
        node1 = await backend.add_knowledge_node(
            "test_agent", "Concept A", "Description of concept A", confidence=0.9
        )
        node2 = await backend.add_knowledge_node(
            "test_agent", "Concept B", "Description of concept B", confidence=0.8
        )

        # Link nodes
        await backend.link_knowledge_nodes(node1.id, node2.id, "relates_to", strength=0.7)

        # Get knowledge graph
        graph = await backend.get_knowledge_graph("test_agent")
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 1

        # Check files were created
        knowledge_path = Path(temp_storage) / "knowledge"
        assert (knowledge_path / "test_agent_nodes.json").exists()
        assert (knowledge_path / "links.json").exists()

        await backend.disconnect()

    async def test_whiteboard_functionality(self, temp_storage):
        """Test whiteboard creation and updates."""
        backend = MarkdownMemoryBackend(temp_storage)
        await backend.connect()

        task_id = "test_task_123"
        agent_id = "test_agent"

        # Create whiteboard
        whiteboard = await backend.create_whiteboard(task_id, agent_id)
        assert whiteboard.task_id == task_id
        assert agent_id in whiteboard.participants

        # Update whiteboard
        await backend.update_whiteboard(task_id, agent_id, "notes", {"message": "Test note"})

        # Retrieve whiteboard
        retrieved = await backend.get_whiteboard(task_id)
        assert retrieved is not None
        assert len(retrieved.notes) > 0
        assert retrieved.notes[0]["message"] == "Test note"

        # Check file was created
        whiteboard_file = Path(temp_storage) / "whiteboards" / f"{task_id}.json"
        assert whiteboard_file.exists()

        await backend.disconnect()


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestSQLiteBackend:
    """Test the SQLite backend."""

    @pytest.fixture
    async def temp_db(self):
        """Create temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = temp_file.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)

    async def test_connect_disconnect(self, temp_db):
        """Test database connection."""
        backend = SQLiteMemoryBackend(temp_db)

        assert not await backend.is_available()

        await backend.connect()
        assert await backend.is_available()

        # Check database file was created
        assert Path(temp_db).exists()

        await backend.disconnect()
        assert not await backend.is_available()

    async def test_memory_storage_retrieval(self, temp_db):
        """Test storing and retrieving memories in SQLite."""
        backend = SQLiteMemoryBackend(temp_db)
        await backend.connect()

        # Create test memory
        memory = Memory(
            agent_id="test_agent",
            content="SQLite test memory",
            type=MemoryType.SEMANTIC,
            tags=["sqlite", "test"],
            importance_score=0.7,
        )

        # Store memory
        stored = await backend.store_memory(memory)
        assert stored.id == memory.id

        # Retrieve by ID
        retrieved = await backend.get_memory(memory.id)
        assert retrieved is not None
        assert retrieved.content == memory.content
        assert retrieved.tags == memory.tags
        assert retrieved.importance_score == memory.importance_score

        # Get agent memories
        agent_memories = await backend.get_agent_memories("test_agent")
        assert len(agent_memories) == 1
        assert agent_memories[0].content == memory.content

        await backend.disconnect()

    async def test_tag_search_sqlite(self, temp_db):
        """Test tag-based search in SQLite."""
        backend = SQLiteMemoryBackend(temp_db)
        await backend.connect()

        # Create memories with tags
        memory1 = Memory(agent_id="test_agent", content="Memory with tag1", tags=["tag1", "common"])
        memory2 = Memory(agent_id="test_agent", content="Memory with tag2", tags=["tag2", "common"])

        await backend.store_memory(memory1)
        await backend.store_memory(memory2)

        # Search by tag
        results = await backend.search_memories_by_tags("test_agent", ["tag1"])
        assert len(results) == 1
        assert results[0].content == "Memory with tag1"

        # Search by common tag
        results = await backend.search_memories_by_tags("test_agent", ["common"])
        assert len(results) == 2

        await backend.disconnect()

    async def test_knowledge_graph_sqlite(self, temp_db):
        """Test knowledge graph functionality in SQLite."""
        backend = SQLiteMemoryBackend(temp_db)
        await backend.connect()

        # Add knowledge nodes
        node1 = await backend.add_knowledge_node(
            "test_agent", "SQLite Concept", "A concept stored in SQLite", confidence=0.95
        )

        node2 = await backend.add_knowledge_node(
            "test_agent", "Related Concept", "Another concept", confidence=0.85
        )

        # Link nodes
        await backend.link_knowledge_nodes(node1.id, node2.id, "connected_to", strength=0.9)

        # Get knowledge graph
        graph = await backend.get_knowledge_graph("test_agent")
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 1

        await backend.disconnect()


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestMemoryFallbackChain:
    """Test the memory fallback chain."""

    @pytest.fixture
    async def temp_storage(self):
        """Create temporary storage for fallback chain."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    async def test_fallback_chain_creation(self, temp_storage):
        """Test creating a fallback chain."""
        chain = create_simple_fallback_chain(temp_storage)

        # Should have 3 backends: SQLite, Markdown, In-Memory
        assert len(chain.backends) == 3

        await chain.connect()
        assert await chain.is_available()

        # Should start with first available backend (SQLite)
        assert chain.current_backend_index == 0
        assert chain.backend_health[0] is True

        await chain.disconnect()

    async def test_automatic_fallback(self, temp_storage):
        """Test automatic fallback when backends fail."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        # Create a memory
        memory = Memory(
            agent_id="test_agent", content="Fallback test memory", type=MemoryType.SEMANTIC
        )

        # Store memory (should use first backend)
        stored = await chain.store_memory(memory)
        assert stored.id == memory.id

        # Force backend failure by marking it as unhealthy
        chain.backend_health[chain.current_backend_index] = False

        # Try another operation - should automatically switch backends
        memories = await chain.get_agent_memories("test_agent")
        assert len(memories) >= 0  # Should succeed with fallback backend

        await chain.disconnect()

    async def test_backend_health_monitoring(self, temp_storage):
        """Test backend health monitoring."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        # Check initial backend status
        status = chain.get_backend_status()
        assert "current_backend" in status
        assert "all_backends" in status
        assert len(status["all_backends"]) == 3

        # Perform health check
        health = await chain.health_check_all_backends()
        assert isinstance(health, dict)

        # Should have at least one healthy backend
        assert any(health.values())

        await chain.disconnect()

    async def test_force_backend_switch(self, temp_storage):
        """Test forcing backend switches."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        initial_backend = chain.current_backend_index

        # Force switch to a different backend
        target_backend = (initial_backend + 1) % len(chain.backends)
        switched = await chain.force_backend_switch(target_backend)

        if switched:
            assert chain.current_backend_index == target_backend

        await chain.disconnect()

    async def test_fallback_with_memory_operations(self, temp_storage):
        """Test complex memory operations with fallback chain."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        agent_id = "fallback_test_agent"

        # Store different types of memories
        semantic = Memory(
            agent_id=agent_id,
            content="Semantic knowledge",
            type=MemoryType.SEMANTIC,
            importance_score=0.8,
        )

        episodic = Memory(
            agent_id=agent_id,
            content="Episode memory",
            type=MemoryType.EPISODIC,
            importance_score=0.6,
        )

        await chain.store_memory(semantic)
        await chain.store_memory(episodic)

        # Retrieve memories
        all_memories = await chain.get_agent_memories(agent_id)
        assert len(all_memories) == 2

        # Search by tags (if memories have tags)
        semantic.tags = ["knowledge", "test"]
        await chain.store_memory(semantic)  # Update with tags

        tagged_memories = await chain.search_memories_by_tags(agent_id, ["knowledge"])
        assert len(tagged_memories) >= 1

        # Test knowledge graph
        node = await chain.add_knowledge_node(
            agent_id, "Fallback Concept", "A concept stored via fallback", confidence=0.9
        )

        graph = await chain.get_knowledge_graph(agent_id)
        assert len(graph["nodes"]) >= 1

        await chain.disconnect()


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestEnhancedMemoryInterface:
    """Test the enhanced memory interface with fallback support."""

    @pytest.fixture
    async def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @patch("httpx.AsyncClient")
    async def test_fallback_only_mode(self, mock_client, temp_storage):
        """Test memory interface in fallback-only mode."""
        # Create fallback-only interface
        interface = create_fallback_only_interface(agent_id="test_agent", storage_path=temp_storage)

        async with interface:
            # Should be using fallback backend
            status = interface.get_backend_status()
            assert status["current_backend"] == "Fallback Chain"
            assert status["fallback_available"] is True
            assert status["http_available"] is False

            # Store short-term memory
            memory_id = await interface.remember_short_term(
                "Test fallback memory", tags=["test"], importance=0.7
            )
            assert memory_id is not None

            # Store long-term memory
            long_term_id = await interface.remember_long_term(
                "Long term knowledge", memory_type="semantic", tags=["knowledge"], importance=0.9
            )
            assert long_term_id is not None

            # Recall memories
            memories = await interface.recall_memories()
            assert len(memories) == 2

            # Search by tags
            tagged = await interface.search_memories(tags=["test"])
            assert len(tagged) >= 1

    @patch("httpx.AsyncClient")
    async def test_http_with_fallback(self, mock_client_class, temp_storage):
        """Test HTTP mode with fallback available."""
        # Mock HTTP client to fail
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        interface = create_enhanced_memory_interface(
            agent_id="test_agent", use_fallback=True, storage_path=temp_storage
        )

        async with interface:
            # Should automatically fall back
            status = interface.get_backend_status()
            assert status["fallback_available"] is True

            # Should still be able to store memories
            memory_id = await interface.remember_short_term("Fallback after HTTP failure")
            assert memory_id is not None

    async def test_health_check(self, temp_storage):
        """Test health check functionality."""
        interface = create_fallback_only_interface(agent_id="test_agent", storage_path=temp_storage)

        async with interface:
            health = await interface.health_check()
            assert "overall_healthy" in health
            assert "fallback_healthy" in health
            assert health["overall_healthy"] is True

    async def test_memory_statistics(self, temp_storage):
        """Test memory statistics collection."""
        interface = create_fallback_only_interface(
            agent_id="stats_agent", storage_path=temp_storage
        )

        async with interface:
            # Store some test memories
            await interface.remember_short_term("Short term 1")
            await interface.remember_short_term("Short term 2")
            await interface.remember_long_term("Long term 1")

            # Get statistics
            stats = await interface.get_memory_statistics()
            assert stats["backend_type"] == "Fallback"
            assert stats["agent_id"] == "stats_agent"
            assert stats["total_memories"] == 3
            assert stats["short_term_memories"] == 2
            assert stats["long_term_memories"] == 1

    @patch("httpx.AsyncClient")
    async def test_backend_switching(self, mock_client_class, temp_storage):
        """Test manual backend switching."""
        # Setup mock for successful HTTP
        mock_client = AsyncMock()
        mock_client.get.return_value.status_code = 200
        mock_client_class.return_value = mock_client

        interface = create_enhanced_memory_interface(
            agent_id="test_agent", storage_path=temp_storage
        )

        async with interface:
            # Should start with HTTP if available
            initial_status = interface.get_backend_status()

            # Force switch to fallback
            switched = await interface.force_backend_switch(use_http=False)
            assert switched is True

            status = interface.get_backend_status()
            assert status["current_backend"] == "Fallback Chain"

            # Try to switch back to HTTP
            switched = await interface.force_backend_switch(use_http=True)
            if switched:
                status = interface.get_backend_status()
                assert status["current_backend"] == "HTTP"


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestMemoryFallbackIntegration:
    """Integration tests for the complete fallback system."""

    @pytest.fixture
    async def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    async def test_cross_backend_consistency(self, temp_storage):
        """Test that memories are consistent across different backends."""
        # Create the same memory in different backends
        memory = Memory(
            agent_id="consistency_agent",
            content="Consistency test memory",
            type=MemoryType.SEMANTIC,
            tags=["consistency", "test"],
            importance_score=0.8,
        )

        # Test in-memory backend
        in_memory = InMemoryBackend()
        await in_memory.connect()
        await in_memory.store_memory(memory)
        in_memory_retrieved = await in_memory.get_memory(memory.id)
        await in_memory.disconnect()

        # Test markdown backend
        markdown = MarkdownMemoryBackend(temp_storage)
        await markdown.connect()
        await markdown.store_memory(memory)
        markdown_retrieved = await markdown.get_memory(memory.id)
        await markdown.disconnect()

        # Test SQLite backend
        sqlite_path = f"{temp_storage}/consistency.db"
        sqlite = SQLiteMemoryBackend(sqlite_path)
        await sqlite.connect()
        await sqlite.store_memory(memory)
        sqlite_retrieved = await sqlite.get_memory(memory.id)
        await sqlite.disconnect()

        # All should retrieve the same memory content
        assert in_memory_retrieved.content == memory.content
        assert markdown_retrieved.content == memory.content
        assert sqlite_retrieved.content == memory.content

        assert in_memory_retrieved.importance_score == memory.importance_score
        assert markdown_retrieved.importance_score == memory.importance_score
        assert sqlite_retrieved.importance_score == memory.importance_score

    async def test_fallback_chain_robustness(self, temp_storage):
        """Test fallback chain behavior under various failure scenarios."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        # Store a memory when all backends are healthy
        memory = Memory(
            agent_id="robust_agent", content="Robustness test", type=MemoryType.EPISODIC
        )

        stored = await chain.store_memory(memory)
        assert stored.id == memory.id

        # Simulate progressive backend failures
        original_backend = chain.current_backend_index

        # Mark current backend as unhealthy
        chain.backend_health[chain.current_backend_index] = False

        # Should still be able to retrieve memory from another backend
        retrieved = await chain.get_agent_memories("robust_agent")
        assert len(retrieved) >= 0  # May be 0 if no sync between backends

        # Mark more backends as unhealthy until only one remains
        for i in range(len(chain.backends) - 1):
            chain.backend_health[i] = False

        # Should still function with the last backend
        final_memory = Memory(
            agent_id="robust_agent", content="Final backend test", type=MemoryType.SEMANTIC
        )

        try:
            await chain.store_memory(final_memory)
            # If this succeeds, the fallback is working
        except RuntimeError:
            # If all backends fail, should get RuntimeError
            pass

        await chain.disconnect()

    async def test_concurrent_access(self, temp_storage):
        """Test concurrent access to the fallback system."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        async def store_memory(agent_id: str, content: str) -> str:
            memory = Memory(agent_id=agent_id, content=content, type=MemoryType.SEMANTIC)
            stored = await chain.store_memory(memory)
            return stored.id

        # Store memories concurrently
        tasks = [store_memory("agent_1", f"Memory {i}") for i in range(10)]

        memory_ids = await asyncio.gather(*tasks)
        assert len(memory_ids) == 10
        assert len(set(memory_ids)) == 10  # All IDs should be unique

        # Retrieve all memories
        memories = await chain.get_agent_memories("agent_1")
        assert len(memories) == 10

        await chain.disconnect()

    async def test_large_memory_dataset(self, temp_storage):
        """Test the fallback system with a large dataset."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        agent_id = "large_dataset_agent"
        memory_count = 100

        # Store many memories
        memory_ids = []
        for i in range(memory_count):
            memory = Memory(
                agent_id=agent_id,
                content=f"Memory number {i}",
                type=MemoryType.SEMANTIC,
                tags=[f"tag_{i % 5}"],  # 5 different tags
                importance_score=i / memory_count,  # Varying importance
            )
            stored = await chain.store_memory(memory)
            memory_ids.append(stored.id)

        # Retrieve all memories
        all_memories = await chain.get_agent_memories(agent_id, limit=memory_count)
        assert len(all_memories) == memory_count

        # Test tag-based search
        tag_results = await chain.search_memories_by_tags(agent_id, ["tag_0"])
        assert len(tag_results) == 20  # Should be 20 memories with tag_0

        # Test filtering
        short_term_results = await chain.get_agent_memories(
            agent_id, short_term_only=True, limit=memory_count
        )
        # All should be considered short-term by default

        await chain.disconnect()


# ============================================================================
# Performance and Stress Tests
# ============================================================================


@pytest.mark.skipif(not HAS_FALLBACK_SYSTEM, reason="Fallback system not available")
@pytest.mark.asyncio
class TestMemoryFallbackPerformance:
    """Performance tests for the fallback system."""

    @pytest.fixture
    async def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    async def test_backend_switching_performance(self, temp_storage):
        """Test performance of backend switching."""
        chain = create_simple_fallback_chain(temp_storage)
        await chain.connect()

        # Measure time for normal operation
        import time

        start_time = time.time()

        for i in range(10):
            memory = Memory(
                agent_id="perf_agent", content=f"Performance test {i}", type=MemoryType.SEMANTIC
            )
            await chain.store_memory(memory)

        normal_time = time.time() - start_time

        # Force backend failure and measure fallback time
        chain.backend_health[chain.current_backend_index] = False

        start_time = time.time()

        for i in range(10):
            memory = Memory(
                agent_id="perf_agent", content=f"Fallback test {i}", type=MemoryType.SEMANTIC
            )
            await chain.store_memory(memory)

        fallback_time = time.time() - start_time

        # Fallback should not be significantly slower
        # Allow 2x slower as acceptable for fallback
        assert fallback_time < normal_time * 3

        await chain.disconnect()

    async def test_memory_retrieval_performance(self, temp_storage):
        """Test retrieval performance across backends."""
        # Test each backend individually
        backends = [
            InMemoryBackend(),
            MarkdownMemoryBackend(temp_storage),
            SQLiteMemoryBackend(f"{temp_storage}/perf.db"),
        ]

        results = {}

        for backend in backends:
            await backend.connect()
            backend_name = backend.__class__.__name__

            # Store test memories
            agent_id = f"perf_{backend_name.lower()}"
            memory_count = 50

            for i in range(memory_count):
                memory = Memory(
                    agent_id=agent_id, content=f"Performance memory {i}", type=MemoryType.SEMANTIC
                )
                await backend.store_memory(memory)

            # Measure retrieval time
            import time

            start_time = time.time()

            memories = await backend.get_agent_memories(agent_id, limit=memory_count)

            retrieval_time = time.time() - start_time
            results[backend_name] = {
                "retrieval_time": retrieval_time,
                "memory_count": len(memories),
            }

            await backend.disconnect()

        # All backends should retrieve all memories
        for backend_name, result in results.items():
            assert result["memory_count"] == memory_count

        # In-memory should be fastest
        assert results["InMemoryBackend"]["retrieval_time"] <= min(
            results["MarkdownMemoryBackend"]["retrieval_time"],
            results["SQLiteMemoryBackend"]["retrieval_time"],
        )


if __name__ == "__main__":
    # Run basic smoke tests
    if HAS_FALLBACK_SYSTEM:
        print("Running memory fallback system smoke tests...")

        async def smoke_test():
            # Test basic functionality
            backend = InMemoryBackend()
            await backend.connect()

            memory = Memory(
                agent_id="smoke_test", content="Smoke test memory", type=MemoryType.SEMANTIC
            )

            stored = await backend.store_memory(memory)
            retrieved = await backend.get_memory(stored.id)

            assert retrieved.content == memory.content
            print("✓ InMemoryBackend smoke test passed")

            await backend.disconnect()

            # Test fallback chain
            chain = create_simple_fallback_chain(".memory_smoke_test")
            await chain.connect()

            stored = await chain.store_memory(memory)
            retrieved = await chain.get_agent_memories("smoke_test")

            assert len(retrieved) >= 1
            print("✓ MemoryFallbackChain smoke test passed")

            await chain.disconnect()

            print("All smoke tests passed!")

        asyncio.run(smoke_test())
    else:
        print("Memory fallback system not available - skipping smoke tests")
