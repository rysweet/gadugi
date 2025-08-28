"""
End-to-end integration tests for the Neo4j memory system
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / ".claude" / "services" / "neo4j-memory"))
sys.path.append(str(Path(__file__).parent.parent / ".claude" / "shared"))

try:
    from memory_manager import (
        MemoryManager, Memory, MemoryType, MemoryScope,
        MemoryPersistence, KnowledgeNode, Whiteboard
    )
    from memory_integration import AgentMemoryInterface, MemoryEnabledAgent
    HAS_MEMORY_SYSTEM = True
except ImportError:
    HAS_MEMORY_SYSTEM = False


@pytest.mark.skipif(not HAS_MEMORY_SYSTEM, reason="Memory system not available")
@pytest.mark.asyncio
class TestMemorySystem:
    """Test the complete memory system integration."""
    
    @pytest.fixture
    async def memory_manager(self):
        """Create and connect a memory manager."""
        mm = MemoryManager()
        await mm.connect()
        yield mm
        await mm.disconnect()
    
    @pytest.fixture
    async def agent_memory(self):
        """Create an agent memory interface."""
        interface = AgentMemoryInterface(
            agent_id="test_agent_001",
            project_id="test_project",
            task_id="test_task"
        )
        return interface
    
    async def test_short_term_memory(self, memory_manager):
        """Test short-term memory storage and retrieval."""
        # Store short-term memory
        memory = await memory_manager.store_agent_memory(
            agent_id="test_agent",
            content="This is a short-term memory",
            memory_type=MemoryType.SHORT_TERM,
            is_short_term=True
        )
        
        assert memory.id
        assert memory.persistence == MemoryPersistence.VOLATILE
        assert memory.expires_at is not None
        assert memory.decay_rate > 0
        
        # Retrieve short-term memories
        memories = await memory_manager.get_agent_memories(
            agent_id="test_agent",
            short_term_only=True
        )
        
        assert len(memories) > 0
        assert any(m.id == memory.id for m in memories)
    
    async def test_long_term_memory(self, memory_manager):
        """Test long-term memory storage and retrieval."""
        # Store long-term memory
        memory = await memory_manager.store_agent_memory(
            agent_id="test_agent",
            content="This is a long-term memory",
            memory_type=MemoryType.SEMANTIC,
            is_short_term=False,
            importance_score=0.9
        )
        
        assert memory.id
        assert memory.persistence == MemoryPersistence.PERSISTENT
        assert memory.expires_at is None
        assert memory.importance_score == 0.9
        
        # Retrieve long-term memories
        memories = await memory_manager.get_agent_memories(
            agent_id="test_agent",
            long_term_only=True
        )
        
        assert len(memories) > 0
        assert any(m.id == memory.id for m in memories)
    
    async def test_memory_consolidation(self, memory_manager):
        """Test consolidation of short-term to long-term memories."""
        agent_id = "consolidation_test_agent"
        
        # Create old short-term memory with high importance
        old_memory = Memory(
            agent_id=agent_id,
            content="Important short-term memory",
            type=MemoryType.SHORT_TERM,
            persistence=MemoryPersistence.VOLATILE,
            importance_score=0.8,
            access_count=3,
            created_at=datetime.now() - timedelta(hours=25)
        )
        await memory_manager._store_memory(old_memory)
        
        # Consolidate memories
        consolidated = await memory_manager.consolidate_short_term_memories(
            agent_id=agent_id,
            threshold_hours=24
        )
        
        assert len(consolidated) > 0
        assert consolidated[0].persistence == MemoryPersistence.PERSISTENT
    
    async def test_project_shared_memory(self, memory_manager):
        """Test project-wide shared memory."""
        project_id = "test_project"
        
        # Store project memory
        memory = await memory_manager.store_project_memory(
            project_id=project_id,
            content="Shared project knowledge",
            created_by="agent_1",
            importance_score=0.9
        )
        
        assert memory.type == MemoryType.PROJECT_SHARED
        assert memory.scope == MemoryScope.PROJECT
        assert memory.project_id == project_id
        
        # Retrieve project memories
        memories = await memory_manager.get_project_memories(project_id)
        assert len(memories) > 0
        assert any(m.id == memory.id for m in memories)
    
    async def test_task_whiteboard(self, memory_manager):
        """Test task whiteboard functionality."""
        task_id = "test_task_123"
        agent_id = "whiteboard_agent"
        
        # Create whiteboard
        whiteboard = await memory_manager.create_whiteboard(task_id, agent_id)
        assert whiteboard.id
        assert whiteboard.task_id == task_id
        assert agent_id in whiteboard.participants
        
        # Update whiteboard
        await memory_manager.update_whiteboard(
            task_id=task_id,
            agent_id="agent_2",
            section="notes",
            content={"note": "Test note"}
        )
        
        # Retrieve whiteboard
        retrieved = await memory_manager.get_whiteboard(task_id)
        assert retrieved
        assert len(retrieved.notes) > 0
        assert "agent_2" in retrieved.participants
    
    async def test_procedural_memory(self, memory_manager):
        """Test procedural memory storage."""
        agent_id = "procedural_agent"
        
        # Store procedure
        memory = await memory_manager.store_procedural_memory(
            agent_id=agent_id,
            procedure_name="test_procedure",
            steps=["Step 1", "Step 2", "Step 3"],
            context="Testing context"
        )
        
        assert memory.type == MemoryType.PROCEDURAL
        assert memory.structured_data["procedure_name"] == "test_procedure"
        assert len(memory.structured_data["steps"]) == 3
        
        # Retrieve procedures
        procedures = await memory_manager.get_procedural_memories(
            agent_id=agent_id,
            procedure_name="test_procedure"
        )
        assert len(procedures) > 0
    
    async def test_knowledge_graph(self, memory_manager):
        """Test knowledge graph functionality."""
        agent_id = "knowledge_agent"
        
        # Add knowledge nodes
        node1 = await memory_manager.add_knowledge_node(
            agent_id=agent_id,
            concept="Machine Learning",
            description="AI technique for pattern recognition",
            confidence=0.9
        )
        
        node2 = await memory_manager.add_knowledge_node(
            agent_id=agent_id,
            concept="Neural Networks",
            description="Computing system inspired by biological neural networks",
            confidence=0.95
        )
        
        # Link nodes
        await memory_manager.link_knowledge_nodes(
            node1_id=node1.id,
            node2_id=node2.id,
            relationship="is_subtopic_of",
            strength=0.8
        )
        
        # Get knowledge graph
        graph = await memory_manager.get_knowledge_graph(agent_id)
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1
    
    async def test_agent_memory_interface(self, agent_memory):
        """Test the agent memory interface."""
        async with agent_memory as mem:
            # Test short-term memory
            short_id = await mem.remember_short_term(
                "Short-term test memory",
                tags=["test"],
                importance=0.5
            )
            assert short_id
            
            # Test long-term memory
            long_id = await mem.remember_long_term(
                "Long-term test memory",
                memory_type="semantic",
                tags=["test", "knowledge"],
                importance=0.8
            )
            assert long_id
            
            # Test memory recall
            memories = await mem.recall_memories(limit=10)
            assert len(memories) > 0
            
            # Test procedural learning
            proc_id = await mem.learn_procedure(
                procedure_name="test_procedure",
                steps=["Initialize", "Process", "Complete"],
                context="Testing"
            )
            assert proc_id
            
            # Test knowledge addition
            knowledge_id = await mem.add_knowledge(
                concept="Test Concept",
                description="A concept for testing",
                confidence=0.9
            )
            assert knowledge_id
    
    async def test_memory_enabled_agent(self):
        """Test the memory-enabled agent example."""
        agent = MemoryEnabledAgent(
            agent_id="integration_test_agent",
            agent_type="worker",
            project_id="test_project"
        )
        
        await agent.initialize()
        
        # Start task
        await agent.start_task("task_456", "Test task description")
        assert agent.current_task_id == "task_456"
        
        # Learn from experience
        await agent.learn_from_experience(
            experience="Encountered test scenario",
            lesson="Always write comprehensive tests"
        )
        
        # Collaborate
        await agent.collaborate(
            message="Considering test approach",
            decision="Use pytest for testing"
        )
        
        # Recall context
        context = await agent.recall_context()
        assert "short_term" in context
        assert "procedures" in context
        assert "project_knowledge" in context
        
        # End task
        await agent.end_task("Task completed successfully")
        assert agent.current_task_id is None
    
    async def test_memory_expiration(self, memory_manager):
        """Test cleanup of expired memories."""
        agent_id = "expiration_test"
        
        # Create expired memory
        expired_memory = Memory(
            agent_id=agent_id,
            content="Expired memory",
            type=MemoryType.SHORT_TERM,
            persistence=MemoryPersistence.VOLATILE,
            expires_at=datetime.now() - timedelta(hours=1)
        )
        await memory_manager._store_memory(expired_memory)
        
        # Run cleanup
        deleted_count = await memory_manager.cleanup_expired_memories()
        assert deleted_count > 0
        
        # Verify memory is gone
        memories = await memory_manager.get_agent_memories(agent_id)
        assert not any(m.id == expired_memory.id for m in memories)


@pytest.mark.skipif(not HAS_MEMORY_SYSTEM, reason="Memory system not available")
def test_memory_types():
    """Test memory type definitions."""
    assert MemoryType.SHORT_TERM.value == "short_term"
    assert MemoryType.LONG_TERM.value == "long_term"
    assert MemoryType.EPISODIC.value == "episodic"
    assert MemoryType.SEMANTIC.value == "semantic"
    assert MemoryType.PROCEDURAL.value == "procedural"
    assert MemoryType.WORKING.value == "working"
    assert MemoryType.PROJECT_SHARED.value == "project_shared"
    assert MemoryType.TASK_WHITEBOARD.value == "task_whiteboard"
    assert MemoryType.TEAM_KNOWLEDGE.value == "team_knowledge"
    assert MemoryType.KNOWLEDGE_NODE.value == "knowledge_node"
    assert MemoryType.KNOWLEDGE_EDGE.value == "knowledge_edge"


@pytest.mark.skipif(not HAS_MEMORY_SYSTEM, reason="Memory system not available")
def test_memory_scope():
    """Test memory scope definitions."""
    assert MemoryScope.PRIVATE.value == "private"
    assert MemoryScope.TASK.value == "task"
    assert MemoryScope.TEAM.value == "team"
    assert MemoryScope.PROJECT.value == "project"
    assert MemoryScope.GLOBAL.value == "global"


@pytest.mark.skipif(not HAS_MEMORY_SYSTEM, reason="Memory system not available")
def test_memory_persistence():
    """Test memory persistence levels."""
    assert MemoryPersistence.VOLATILE.value == "volatile"
    assert MemoryPersistence.SESSION.value == "session"
    assert MemoryPersistence.PERSISTENT.value == "persistent"
    assert MemoryPersistence.ARCHIVED.value == "archived"