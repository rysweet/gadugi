"""Tests for the Memory System Integration."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..memory_system import MemorySystem
from ..models import Memory, MemoryType, Pattern


class TestMemorySystem:
    """Test suite for MemorySystem."""
    
    @pytest.fixture
    async def memory_system(self):
        """Create a memory system instance for testing."""
        system = MemorySystem(
            mcp_service=AsyncMock(),
            event_router=AsyncMock(),
        )
        await system.initialize()
        yield system
        await system.cleanup()
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_system):
        """Test storing a memory."""
        memory = Memory(
            id="test_001",
            type=MemoryType.CONTEXT,
            content="Test memory content",
            tags=["test", "unit"],
        )
        
        memory_id = await memory_system.store_memory(memory)
        
        assert memory_id == "test_001"
        memory_system.mcp_service.store.assert_called_once()
        memory_system.event_router.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_context_from_cache(self, memory_system):
        """Test retrieving memories from cache."""
        # Store test memories
        memories = [
            Memory(
                id=f"test_{i}",
                type=MemoryType.CONTEXT,
                content=f"Python programming tip {i}",
            )
            for i in range(5)
        ]
        
        for memory in memories:
            await memory_system.store_memory(memory)
        
        # Retrieve matching memories
        results = await memory_system.retrieve_context("Python", limit=3)
        
        assert len(results) == 3
        assert all("Python" in m.content for m in results)
    
    @pytest.mark.asyncio
    async def test_retrieve_context_performance(self, memory_system):
        """Test that retrieval meets performance requirements."""
        # Store many memories
        for i in range(100):
            memory = Memory(
                id=f"perf_{i}",
                type=MemoryType.CONTEXT,
                content=f"Performance test memory {i}",
            )
            async with memory_system._cache_lock:
                memory_system._memory_cache[memory.id] = memory
        
        # Measure retrieval time
        start = asyncio.get_event_loop().time()
        results = await memory_system.retrieve_context("test", limit=10)
        elapsed = asyncio.get_event_loop().time() - start
        
        assert elapsed < 0.2  # Must be under 200ms
        assert len(results) <= 10
    
    @pytest.mark.asyncio
    async def test_import_from_memory_md(self, memory_system, tmp_path):
        """Test importing from Memory.md file."""
        # Create test Memory.md file
        memory_md = tmp_path / "Memory.md"
        memory_md.write_text("""# AI Assistant Memory
Last Updated: 2024-01-01T12:00:00Z

## Current Goals
- Complete unit tests
- Improve documentation

## Todo List
- [ ] Write more tests
- [x] Fix bug in parser
- [ ] Update README

## Reflections
The testing framework is working well.
Need to focus on edge cases.
""")
        
        result = await memory_system.import_from_memory_md(memory_md)
        
        assert result.success
        assert result.todos_imported == 3
        assert result.reflections_imported == 1
        assert result.memories_imported == 1
    
    @pytest.mark.asyncio
    async def test_prune_old_memories(self, memory_system):
        """Test pruning old memories."""
        # Add old and new memories
        old_memory = Memory(
            id="old_001",
            type=MemoryType.CONTEXT,
            content="Old memory",
            updated_at=datetime.now() - timedelta(days=40),
            importance=0.3,
        )
        new_memory = Memory(
            id="new_001",
            type=MemoryType.CONTEXT,
            content="New memory",
            updated_at=datetime.now(),
            importance=0.8,
        )
        
        async with memory_system._cache_lock:
            memory_system._memory_cache["old_001"] = old_memory
            memory_system._memory_cache["new_001"] = new_memory
        
        result = await memory_system.prune_old_memories(days=30)
        
        assert result.success
        assert result.memories_pruned == 1
        assert "new_001" in memory_system._memory_cache
        assert "old_001" not in memory_system._memory_cache
    
    @pytest.mark.asyncio
    async def test_extract_patterns_empty(self, memory_system):
        """Test pattern extraction with no Neo4j connection."""
        patterns = await memory_system.extract_patterns()
        
        assert patterns == []
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_sync_with_github(self, mock_client, memory_system):
        """Test GitHub synchronization."""
        memory_system.github_token = "test_token"
        memory_system.github_repo = "test/repo"
        
        # Mock GitHub API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.post.return_value = MagicMock(status_code=201, json=lambda: {"number": 1})
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Add a TODO memory
        todo = Memory(
            id="todo_001",
            type=MemoryType.TODO,
            content="Test TODO item",
        )
        async with memory_system._cache_lock:
            memory_system._memory_cache[todo.id] = todo
        
        result = await memory_system.sync_with_github()
        
        assert result.success
        assert result.issues_created == 1


class TestMemoryModels:
    """Test suite for Memory models."""
    
    def test_memory_to_dict(self):
        """Test converting Memory to dictionary."""
        memory = Memory(
            id="test_001",
            type=MemoryType.DECISION,
            content="Test decision",
            tags=["important"],
            importance=0.9,
        )
        
        data = memory.to_dict()
        
        assert data["id"] == "test_001"
        assert data["type"] == "decision"
        assert data["content"] == "Test decision"
        assert data["tags"] == ["important"]
        assert data["importance"] == 0.9
    
    def test_memory_from_dict(self):
        """Test creating Memory from dictionary."""
        data = {
            "id": "test_002",
            "type": "pattern",
            "content": "Test pattern",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": ["recurring"],
            "importance": 0.7,
        }
        
        memory = Memory.from_dict(data)
        
        assert memory.id == "test_002"
        assert memory.type == MemoryType.PATTERN
        assert memory.content == "Test pattern"
        assert memory.tags == ["recurring"]
        assert memory.importance == 0.7
    
    def test_pattern_to_dict(self):
        """Test converting Pattern to dictionary."""
        pattern = Pattern(
            id="pat_001",
            pattern_type="frequency",
            description="Common error pattern",
            frequency=5,
            memory_ids=["mem_1", "mem_2"],
            confidence=0.85,
        )
        
        data = pattern.to_dict()
        
        assert data["id"] == "pat_001"
        assert data["pattern_type"] == "frequency"
        assert data["frequency"] == 5
        assert data["confidence"] == 0.85