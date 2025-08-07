#!/usr/bin/env python3
"""
Tests for MCP (Memory and Context Persistence) Service
"""

import asyncio
import unittest
import tempfile
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'mcp'))

from mcp_service import (
    MCPService,
    MemoryManager,
    ContextManager,
    MemoryType,
    ContextType,
    PersistenceLevel,
    RetrievalStrategy,
    MemoryEntry,
    ContextSnapshot,
    RetrievalQuery,
    MemoryStats,
    OperationResult,
    create_episodic_memory,
    create_semantic_memory,
    create_session_context,
    create_workflow_context
)


class TestMCPService(unittest.IsolatedAsyncioTestCase):
    """Test cases for MCP Service."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize MCP service with test storage
        self.service = MCPService(
            storage_path=self.temp_dir,
            redis_url=None,  # Use mock Redis
            cleanup_interval=60  # Short interval for testing
        )
        
        # Sample test data
        self.test_memory = MemoryEntry(
            id="test-memory-001",
            type=MemoryType.EPISODIC,
            content={
                "event": "User requested feature",
                "timestamp": datetime.now().isoformat(),
                "details": "Implement new search functionality"
            },
            context={"user": "test_user", "session": "session_123"},
            metadata={"priority": "high", "category": "feature_request"},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            importance_score=0.8,
            tags=["feature", "search", "user_request"]
        )
        
        self.test_context = ContextSnapshot(
            id="test-context-001",
            type=ContextType.SESSION,
            context_data={
                "user_preferences": {"theme": "dark", "language": "en"},
                "current_project": "test_project",
                "active_tasks": ["task_1", "task_2"]
            },
            metadata={"session_id": "session_123", "user": "test_user"},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
    
    async def asyncTearDown(self):
        """Clean up test fixtures."""
        if self.service.running:
            await self.service.stop()
        
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test service initializes properly."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.memory_manager)
        self.assertIsNotNone(self.service.context_manager)
        self.assertIsNotNone(self.service.logger)
        self.assertFalse(self.service.running)
        self.assertEqual(self.service.operation_count, 0)
        self.assertEqual(self.service.total_operation_time, 0.0)
    
    def test_memory_type_enum(self):
        """Test MemoryType enum functionality."""
        self.assertEqual(MemoryType.EPISODIC.value, "episodic")
        self.assertEqual(MemoryType.SEMANTIC.value, "semantic")
        self.assertEqual(MemoryType.PROCEDURAL.value, "procedural")
        self.assertEqual(MemoryType.WORKING.value, "working")
        self.assertEqual(MemoryType.DECLARATIVE.value, "declarative")
        self.assertEqual(MemoryType.ASSOCIATIVE.value, "associative")
    
    def test_context_type_enum(self):
        """Test ContextType enum functionality."""
        self.assertEqual(ContextType.SESSION.value, "session")
        self.assertEqual(ContextType.WORKFLOW.value, "workflow")
        self.assertEqual(ContextType.AGENT.value, "agent")
        self.assertEqual(ContextType.TASK.value, "task")
        self.assertEqual(ContextType.CONVERSATION.value, "conversation")
        self.assertEqual(ContextType.PROJECT.value, "project")
    
    def test_persistence_level_enum(self):
        """Test PersistenceLevel enum functionality."""
        self.assertEqual(PersistenceLevel.TEMPORARY.value, "temporary")
        self.assertEqual(PersistenceLevel.SESSION.value, "session")
        self.assertEqual(PersistenceLevel.PERMANENT.value, "permanent")
        self.assertEqual(PersistenceLevel.ARCHIVAL.value, "archival")
    
    def test_retrieval_strategy_enum(self):
        """Test RetrievalStrategy enum functionality."""
        self.assertEqual(RetrievalStrategy.CHRONOLOGICAL.value, "chronological")
        self.assertEqual(RetrievalStrategy.RELEVANCE.value, "relevance")
        self.assertEqual(RetrievalStrategy.FREQUENCY.value, "frequency")
        self.assertEqual(RetrievalStrategy.RECENCY.value, "recency")
        self.assertEqual(RetrievalStrategy.IMPORTANCE.value, "importance")
        self.assertEqual(RetrievalStrategy.ASSOCIATIVE.value, "associative")
    
    def test_memory_entry_dataclass(self):
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
            tags=["python", "programming"]
        )
        
        self.assertEqual(memory.id, "test-123")
        self.assertEqual(memory.type, MemoryType.SEMANTIC)
        self.assertEqual(memory.content["fact"], "Python is a programming language")
        self.assertEqual(memory.importance_score, 0.7)
        self.assertEqual(memory.access_count, 0)  # Default value
        self.assertIn("python", memory.tags)
    
    def test_context_snapshot_dataclass(self):
        """Test ContextSnapshot dataclass functionality."""
        context = ContextSnapshot(
            id="context-456",
            type=ContextType.WORKFLOW,
            context_data={"step": 1, "variables": {"x": 10}},
            metadata={"workflow_name": "test_workflow"},
            created_at=datetime.now()
        )
        
        self.assertEqual(context.id, "context-456")
        self.assertEqual(context.type, ContextType.WORKFLOW)
        self.assertEqual(context.context_data["step"], 1)
        self.assertIsNone(context.expires_at)  # Default
        self.assertFalse(context.compressed)  # Default
        self.assertNotEqual(context.checksum, "")  # Should be calculated
    
    def test_context_snapshot_checksum(self):
        """Test context snapshot checksum calculation."""
        context_data = {"test": "data", "number": 42}
        
        context1 = ContextSnapshot(
            id="test-1",
            type=ContextType.SESSION,
            context_data=context_data,
            metadata={},
            created_at=datetime.now()
        )
        
        context2 = ContextSnapshot(
            id="test-2",
            type=ContextType.SESSION,
            context_data=context_data,
            metadata={},
            created_at=datetime.now()
        )
        
        # Same data should produce same checksum
        self.assertEqual(context1.checksum, context2.checksum)
        
        # Different data should produce different checksum
        context3 = ContextSnapshot(
            id="test-3",
            type=ContextType.SESSION,
            context_data={"different": "data"},
            metadata={},
            created_at=datetime.now()
        )
        
        self.assertNotEqual(context1.checksum, context3.checksum)
    
    def test_retrieval_query_dataclass(self):
        """Test RetrievalQuery dataclass functionality."""
        query = RetrievalQuery(
            query_text="search term",
            memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            tags=["important"],
            max_results=50,
            strategy=RetrievalStrategy.IMPORTANCE
        )
        
        self.assertEqual(query.query_text, "search term")
        self.assertEqual(len(query.memory_types), 2)
        self.assertIn(MemoryType.EPISODIC, query.memory_types)
        self.assertEqual(query.max_results, 50)
        self.assertEqual(query.strategy, RetrievalStrategy.IMPORTANCE)
        self.assertTrue(query.include_context)  # Default
    
    def test_operation_result_dataclass(self):
        """Test OperationResult dataclass functionality."""
        result = OperationResult(
            success=True,
            operation="test_operation",
            data={"result": "success"},
            metadata={"execution_time": 1.5},
            execution_time=1.5,
            warnings=["minor warning"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "test_operation")
        self.assertEqual(result.data["result"], "success")
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.errors), 0)  # Default empty list
    
    def test_memory_stats_dataclass(self):
        """Test MemoryStats dataclass functionality."""
        stats = MemoryStats(
            total_memories=100,
            memories_by_type={"episodic": 60, "semantic": 40},
            total_contexts=25,
            storage_size=1024000,
            cache_hit_rate=0.85
        )
        
        self.assertEqual(stats.total_memories, 100)
        self.assertEqual(stats.memories_by_type["episodic"], 60)
        self.assertEqual(stats.total_contexts, 25)
        self.assertEqual(stats.cache_hit_rate, 0.85)
        self.assertIsNotNone(stats.last_cleanup)  # Default value
    
    async def test_service_start_stop(self):
        """Test service start and stop functionality."""
        self.assertFalse(self.service.running)
        
        await self.service.start()
        self.assertTrue(self.service.running)
        self.assertIsNotNone(self.service.cleanup_task)
        
        await self.service.stop()
        self.assertFalse(self.service.running)
    
    async def test_store_memory_success(self):
        """Test successful memory storage."""
        await self.service.start()
        
        result = await self.service.store_memory(self.test_memory)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "store_memory")
        self.assertIn("memory_id", result.data)
        self.assertEqual(result.data["memory_id"], self.test_memory.id)
        self.assertGreater(result.execution_time, 0)
    
    async def test_retrieve_memory_success(self):
        """Test successful memory retrieval."""
        await self.service.start()
        
        # Store memory first
        store_result = await self.service.store_memory(self.test_memory)
        self.assertTrue(store_result.success)
        
        # Retrieve memory
        result = await self.service.retrieve_memory(self.test_memory.id)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "retrieve_memory")
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data.id, self.test_memory.id)
        self.assertEqual(result.data.content["event"], "User requested feature")
    
    async def test_retrieve_memory_not_found(self):
        """Test memory retrieval when memory doesn't exist."""
        await self.service.start()
        
        result = await self.service.retrieve_memory("nonexistent-memory")
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("not found", result.warnings[0])
    
    async def test_query_memories_success(self):
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
                tags=["test", f"event_{i}"]
            )
            for i in range(1, 6)
        ]
        
        for memory in memories:
            store_result = await self.service.store_memory(memory)
            self.assertTrue(store_result.success)
        
        # Query memories
        query = RetrievalQuery(
            memory_types=[MemoryType.EPISODIC],
            tags=["test"],
            max_results=10,
            strategy=RetrievalStrategy.IMPORTANCE
        )
        
        result = await self.service.query_memories(query)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "query_memories")
        self.assertGreaterEqual(len(result.data), 5)
        self.assertEqual(result.metadata["result_count"], len(result.data))
        
        # Results should be ordered by importance (descending)
        for i in range(len(result.data) - 1):
            self.assertGreaterEqual(
                result.data[i].importance_score,
                result.data[i + 1].importance_score
            )
    
    async def test_delete_memory_success(self):
        """Test successful memory deletion."""
        await self.service.start()
        
        # Store memory first
        store_result = await self.service.store_memory(self.test_memory)
        self.assertTrue(store_result.success)
        
        # Delete memory
        result = await self.service.delete_memory(self.test_memory.id)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "delete_memory")
        self.assertEqual(result.data["memory_id"], self.test_memory.id)
        
        # Verify memory is deleted
        retrieve_result = await self.service.retrieve_memory(self.test_memory.id)
        self.assertFalse(retrieve_result.success)
    
    async def test_save_context_success(self):
        """Test successful context saving."""
        await self.service.start()
        
        result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.SESSION
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "save_context")
        self.assertEqual(result.data["context_id"], self.test_context.id)
        self.assertEqual(result.metadata["persistence_level"], "session")
    
    async def test_load_context_success(self):
        """Test successful context loading."""
        await self.service.start()
        
        # Save context first
        save_result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.SESSION
        )
        self.assertTrue(save_result.success)
        
        # Load context
        result = await self.service.load_context(self.test_context.id)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "load_context")
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data.id, self.test_context.id)
        self.assertEqual(result.data.context_data["user_preferences"]["theme"], "dark")
    
    async def test_load_context_not_found(self):
        """Test context loading when context doesn't exist."""
        await self.service.start()
        
        result = await self.service.load_context("nonexistent-context")
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("not found", result.warnings[0])
    
    async def test_list_contexts_success(self):
        """Test successful context listing."""
        await self.service.start()
        
        # Save multiple contexts
        contexts = [
            ContextSnapshot(
                id=f"context-{i}",
                type=ContextType.SESSION if i % 2 == 0 else ContextType.WORKFLOW,
                context_data={"data": f"value_{i}"},
                metadata={"index": i},
                created_at=datetime.now()
            )
            for i in range(1, 4)
        ]
        
        for context in contexts:
            save_result = await self.service.save_context(context, PersistenceLevel.PERMANENT)
            self.assertTrue(save_result.success)
        
        # List all contexts
        result = await self.service.list_contexts()
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "list_contexts")
        self.assertGreaterEqual(len(result.data), 3)
        self.assertEqual(result.metadata["result_count"], len(result.data))
        
        # List contexts by type
        session_result = await self.service.list_contexts(ContextType.SESSION)
        
        self.assertTrue(session_result.success)
        session_contexts = [c for c in session_result.data if c.type == ContextType.SESSION]
        self.assertGreaterEqual(len(session_contexts), 1)
    
    async def test_delete_context_success(self):
        """Test successful context deletion."""
        await self.service.start()
        
        # Save context first
        save_result = await self.service.save_context(
            self.test_context,
            PersistenceLevel.PERMANENT
        )
        self.assertTrue(save_result.success)
        
        # Delete context
        result = await self.service.delete_context(self.test_context.id)
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "delete_context")
        self.assertEqual(result.data["context_id"], self.test_context.id)
        
        # Verify context is deleted
        load_result = await self.service.load_context(self.test_context.id)
        self.assertFalse(load_result.success)
    
    async def test_store_episodic_memory_convenience(self):
        """Test episodic memory convenience method."""
        await self.service.start()
        
        result = await self.service.store_episodic_memory(
            "User completed task successfully",
            {"user": "test_user", "task_id": "task_123"},
            importance=0.9
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "store_memory")
        
        # Retrieve and verify the stored memory
        memory_id = result.data["memory_id"]
        retrieve_result = await self.service.retrieve_memory(memory_id)
        
        self.assertTrue(retrieve_result.success)
        self.assertEqual(retrieve_result.data.type, MemoryType.EPISODIC)
        self.assertEqual(retrieve_result.data.content["event"], "User completed task successfully")
        self.assertEqual(retrieve_result.data.importance_score, 0.9)
        self.assertIn("episodic", retrieve_result.data.tags)
    
    async def test_store_semantic_memory_convenience(self):
        """Test semantic memory convenience method."""
        await self.service.start()
        
        knowledge = {
            "concept": "Machine Learning",
            "definition": "A subset of AI that enables computers to learn from data",
            "applications": ["image recognition", "natural language processing"]
        }
        
        result = await self.service.store_semantic_memory(
            knowledge,
            category="technology",
            importance=0.8
        )
        
        self.assertTrue(result.success)
        
        # Retrieve and verify
        memory_id = result.data["memory_id"]
        retrieve_result = await self.service.retrieve_memory(memory_id)
        
        self.assertTrue(retrieve_result.success)
        self.assertEqual(retrieve_result.data.type, MemoryType.SEMANTIC)
        self.assertEqual(retrieve_result.data.content["concept"], "Machine Learning")
        self.assertIn("technology", retrieve_result.data.tags)
    
    async def test_save_session_context_convenience(self):
        """Test session context convenience method."""
        await self.service.start()
        
        context_data = {
            "user_id": "user_123",
            "preferences": {"notifications": True},
            "current_view": "dashboard"
        }
        
        result = await self.service.save_session_context(
            "session_456",
            context_data,
            expires_in_hours=12
        )
        
        self.assertTrue(result.success)
        
        # Load and verify
        load_result = await self.service.load_context("session_456")
        
        self.assertTrue(load_result.success)
        self.assertEqual(load_result.data.type, ContextType.SESSION)
        self.assertEqual(load_result.data.context_data["user_id"], "user_123")
        self.assertIsNotNone(load_result.data.expires_at)
    
    async def test_save_workflow_context_convenience(self):
        """Test workflow context convenience method."""
        await self.service.start()
        
        context_data = {
            "workflow_name": "data_processing",
            "current_step": 3,
            "variables": {"input_file": "data.csv", "processed_rows": 1500}
        }
        
        result = await self.service.save_workflow_context(
            "workflow_789",
            context_data
        )
        
        self.assertTrue(result.success)
        
        # Load and verify
        load_result = await self.service.load_context("workflow_789")
        
        self.assertTrue(load_result.success)
        self.assertEqual(load_result.data.type, ContextType.WORKFLOW)
        self.assertEqual(load_result.data.context_data["workflow_name"], "data_processing")
        self.assertIsNone(load_result.data.expires_at)  # Permanent context
    
    async def test_get_system_stats(self):
        """Test system statistics retrieval."""
        await self.service.start()
        
        # Store some data
        await self.service.store_memory(self.test_memory)
        await self.service.save_context(self.test_context, PersistenceLevel.SESSION)
        
        result = await self.service.get_system_stats()
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "get_system_stats")
        self.assertIn("memory_stats", result.data)
        self.assertIn("service_performance", result.data)
        self.assertIn("storage_info", result.data)
        
        # Check service performance stats
        perf_stats = result.data["service_performance"]
        self.assertGreater(perf_stats["total_operations"], 0)
        self.assertGreaterEqual(perf_stats["total_operation_time"], 0)
    
    async def test_health_check_healthy(self):
        """Test health check when service is healthy."""
        await self.service.start()
        
        health = await self.service.health_check()
        
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["running"])
        self.assertEqual(health["components"]["memory_manager"], "healthy")
        self.assertEqual(health["components"]["context_manager"], "healthy")
        self.assertIn("performance", health)
    
    async def test_health_check_stopped(self):
        """Test health check when service is stopped."""
        health = await self.service.health_check()
        
        self.assertEqual(health["status"], "stopped")
        self.assertFalse(health["running"])
    
    def test_create_episodic_memory_utility(self):
        """Test episodic memory creation utility."""
        memory = create_episodic_memory(
            "Important event occurred",
            {"location": "office", "participants": ["alice", "bob"]},
            importance=0.9,
            tags=["important", "meeting"]
        )
        
        self.assertEqual(memory.type, MemoryType.EPISODIC)
        self.assertEqual(memory.content["event"], "Important event occurred")
        self.assertEqual(memory.importance_score, 0.9)
        self.assertIn("important", memory.tags)
        self.assertIn("episodic", memory.tags)
        self.assertEqual(memory.context["location"], "office")
    
    def test_create_semantic_memory_utility(self):
        """Test semantic memory creation utility."""
        knowledge = {
            "term": "RESTful API",
            "definition": "An API that follows REST architectural style",
            "principles": ["stateless", "cacheable", "uniform interface"]
        }
        
        memory = create_semantic_memory(
            knowledge,
            category="software_engineering",
            importance=0.7
        )
        
        self.assertEqual(memory.type, MemoryType.SEMANTIC)
        self.assertEqual(memory.content["term"], "RESTful API")
        self.assertEqual(memory.importance_score, 0.7)
        self.assertIn("semantic", memory.tags)
        self.assertIn("software_engineering", memory.tags)
        self.assertEqual(memory.context["category"], "software_engineering")
    
    def test_create_session_context_utility(self):
        """Test session context creation utility."""
        context_data = {
            "user": "test_user",
            "permissions": ["read", "write"],
            "last_activity": datetime.now().isoformat()
        }
        
        context = create_session_context(
            "session_abc",
            context_data,
            expires_in_hours=6
        )
        
        self.assertEqual(context.type, ContextType.SESSION)
        self.assertEqual(context.id, "session_abc")
        self.assertEqual(context.context_data["user"], "test_user")
        self.assertIsNotNone(context.expires_at)
        self.assertEqual(context.metadata["session_id"], "session_abc")
    
    def test_create_workflow_context_utility(self):
        """Test workflow context creation utility."""
        context_data = {
            "process": "ml_training",
            "epoch": 15,
            "loss": 0.0045,
            "accuracy": 0.97
        }
        
        context = create_workflow_context(
            "training_workflow_xyz",
            context_data
        )
        
        self.assertEqual(context.type, ContextType.WORKFLOW)
        self.assertEqual(context.id, "training_workflow_xyz")
        self.assertEqual(context.context_data["process"], "ml_training")
        self.assertIsNone(context.expires_at)  # Permanent workflow context
        self.assertEqual(context.metadata["workflow_id"], "training_workflow_xyz")
    
    def test_memory_manager_initialization(self):
        """Test MemoryManager initialization."""
        storage_path = os.path.join(self.temp_dir, "test_memory")
        manager = MemoryManager(storage_path, compression_enabled=True)
        
        self.assertIsNotNone(manager)
        self.assertTrue(Path(storage_path).exists())
        self.assertTrue(manager.compression_enabled)
        self.assertEqual(len(manager.memory_cache), 0)
        self.assertEqual(manager.cache_max_size, 10000)
        
        # Check database initialization
        self.assertTrue(manager.db_path.exists())
    
    def test_context_manager_initialization(self):
        """Test ContextManager initialization."""
        storage_path = os.path.join(self.temp_dir, "test_context")
        manager = ContextManager(storage_path, redis_url=None)
        
        self.assertIsNotNone(manager)
        self.assertTrue(Path(storage_path).exists())
        self.assertIsNotNone(manager.redis_client)  # Mock Redis
        
        # Check database initialization
        self.assertTrue(manager.db_path.exists())
    
    def test_memory_database_schema(self):
        """Test memory database schema creation."""
        storage_path = os.path.join(self.temp_dir, "test_memory_db")
        manager = MemoryManager(storage_path)
        
        # Check if tables exist
        with sqlite3.connect(str(manager.db_path)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn("memories", tables)
            self.assertIn("memories_fts", tables)
            
            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Should have at least our custom indexes
            index_names = [name for name in indexes if name.startswith("idx_memories")]
            self.assertGreater(len(index_names), 0)
    
    def test_context_database_schema(self):
        """Test context database schema creation."""
        storage_path = os.path.join(self.temp_dir, "test_context_db")
        manager = ContextManager(storage_path)
        
        # Check if tables exist
        with sqlite3.connect(str(manager.db_path)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn("contexts", tables)
            
            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Should have at least our custom indexes
            index_names = [name for name in indexes if name.startswith("idx_contexts")]
            self.assertGreater(len(index_names), 0)
    
    def test_operation_stats_tracking(self):
        """Test operation statistics tracking."""
        self.assertEqual(self.service.operation_count, 0)
        self.assertEqual(self.service.total_operation_time, 0.0)
        
        # Simulate operation stats update
        self.service._update_operation_stats(1.5)
        
        self.assertEqual(self.service.operation_count, 1)
        self.assertEqual(self.service.total_operation_time, 1.5)
        
        # Add another operation
        self.service._update_operation_stats(0.8)
        
        self.assertEqual(self.service.operation_count, 2)
        self.assertEqual(self.service.total_operation_time, 2.3)
    
    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.service.logger)
        self.assertEqual(self.service.logger.name, "mcp_service")
        
        # Test component loggers
        self.assertEqual(self.service.memory_manager.logger.name, "mcp_memory")
        self.assertEqual(self.service.context_manager.logger.name, "mcp_context")
    
    def test_redis_availability_detection(self):
        """Test Redis availability detection."""
        self.assertIsInstance(self.service.redis_available, bool)
        
        # Service should handle missing Redis gracefully
        self.assertIsNotNone(self.service.context_manager.redis_client)
    
    async def test_cleanup_loop_functionality(self):
        """Test cleanup loop functionality."""
        # Set short cleanup interval for testing
        self.service.cleanup_interval = 0.1
        
        await self.service.start()
        
        # Let cleanup loop run a few times
        await asyncio.sleep(0.3)
        
        # Cleanup task should be running
        self.assertIsNotNone(self.service.cleanup_task)
        self.assertFalse(self.service.cleanup_task.done())
        
        await self.service.stop()
        
        # Cleanup task should be cancelled
        self.assertTrue(self.service.cleanup_task.done())
    
    async def test_concurrent_operations(self):
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
                tags=["concurrent", "test"]
            )
            memory_tasks.append(self.service.store_memory(memory))
            
            context = ContextSnapshot(
                id=f"concurrent-context-{i}",
                type=ContextType.TASK,
                context_data={"task": f"task_{i}"},
                metadata={"index": i},
                created_at=datetime.now()
            )
            context_tasks.append(self.service.save_context(context, PersistenceLevel.TEMPORARY))
        
        # Execute all operations concurrently
        memory_results = await asyncio.gather(*memory_tasks)
        context_results = await asyncio.gather(*context_tasks)
        
        # All operations should succeed
        for result in memory_results:
            self.assertTrue(result.success)
        
        for result in context_results:
            self.assertTrue(result.success)


class TestMemoryManager(unittest.TestCase):
    """Test cases for MemoryManager component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MemoryManager(self.temp_dir, compression_enabled=True)
        
        self.test_memory = MemoryEntry(
            id="test-memory",
            type=MemoryType.EPISODIC,
            content={"event": "Test event", "data": "x" * 2000},  # Large content for compression test
            context={"test": True},
            metadata={"compressed_test": True},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            tags=["test", "compression"]
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_store_and_retrieve_memory(self):
        """Test memory storage and retrieval."""
        # Store memory
        store_result = self.manager.store_memory(self.test_memory)
        self.assertTrue(store_result.success)
        
        # Retrieve memory
        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        self.assertTrue(retrieve_result.success)
        
        retrieved_memory = retrieve_result.data
        self.assertEqual(retrieved_memory.id, self.test_memory.id)
        self.assertEqual(retrieved_memory.content["event"], "Test event")
        self.assertEqual(retrieved_memory.access_count, 1)  # Incremented on retrieval
    
    def test_memory_compression(self):
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
            tags=["compression_test"]
        )
        
        result = self.manager.store_memory(large_memory)
        self.assertTrue(result.success)
        self.assertTrue(result.metadata.get("compressed", False))
        
        # Retrieve and verify decompression
        retrieve_result = self.manager.retrieve_memory("large-memory")
        self.assertTrue(retrieve_result.success)
        self.assertEqual(len(retrieve_result.data.content["large_data"]), 2000)
    
    def test_cache_functionality(self):
        """Test memory caching."""
        # Store memory (should be cached)
        store_result = self.manager.store_memory(self.test_memory)
        self.assertTrue(store_result.success)
        
        # Should be in cache
        self.assertIn(self.test_memory.id, self.manager.memory_cache)
        
        # Retrieve should hit cache
        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        self.assertTrue(retrieve_result.success)
        self.assertEqual(retrieve_result.metadata["source"], "cache")
        
        # Clear cache and retrieve again (should hit database)
        self.manager.memory_cache.clear()
        self.manager.cache_access_order.clear()
        
        retrieve_result = self.manager.retrieve_memory(self.test_memory.id)
        self.assertTrue(retrieve_result.success)
        self.assertEqual(retrieve_result.metadata["source"], "database")


class TestContextManager(unittest.TestCase):
    """Test cases for ContextManager component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ContextManager(self.temp_dir, redis_url=None)  # Use mock Redis
        
        self.test_context = ContextSnapshot(
            id="test-context",
            type=ContextType.SESSION,
            context_data={"user": "test", "data": {"key": "value"}},
            metadata={"test": True},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_context(self):
        """Test context saving and loading."""
        # Save context
        save_result = self.manager.save_context(self.test_context, PersistenceLevel.PERMANENT)
        self.assertTrue(save_result.success)
        
        # Load context
        load_result = self.manager.load_context(self.test_context.id)
        self.assertTrue(load_result.success)
        
        loaded_context = load_result.data
        self.assertEqual(loaded_context.id, self.test_context.id)
        self.assertEqual(loaded_context.context_data["user"], "test")
        self.assertEqual(loaded_context.checksum, self.test_context.checksum)
    
    def test_context_compression(self):
        """Test context compression functionality."""
        # Large context should trigger compression
        large_context = ContextSnapshot(
            id="large-context",
            type=ContextType.WORKFLOW,
            context_data={"large_data": "x" * 2000},  # Large data
            metadata={},
            created_at=datetime.now()
        )
        
        save_result = self.manager.save_context(large_context, PersistenceLevel.PERMANENT)
        self.assertTrue(save_result.success)
        self.assertTrue(save_result.metadata.get("compressed", False))
        
        # Load and verify decompression
        load_result = self.manager.load_context("large-context")
        self.assertTrue(load_result.success)
        self.assertEqual(len(load_result.data.context_data["large_data"]), 2000)
    
    def test_list_contexts_filtering(self):
        """Test context listing with filtering."""
        # Save contexts of different types
        session_context = ContextSnapshot(
            id="session-ctx",
            type=ContextType.SESSION,
            context_data={"type": "session"},
            metadata={},
            created_at=datetime.now()
        )
        
        workflow_context = ContextSnapshot(
            id="workflow-ctx",
            type=ContextType.WORKFLOW,
            context_data={"type": "workflow"},
            metadata={},
            created_at=datetime.now()
        )
        
        self.manager.save_context(session_context, PersistenceLevel.PERMANENT)
        self.manager.save_context(workflow_context, PersistenceLevel.PERMANENT)
        
        # List all contexts
        all_result = self.manager.list_contexts()
        self.assertTrue(all_result.success)
        self.assertGreaterEqual(len(all_result.data), 2)
        
        # List session contexts only
        session_result = self.manager.list_contexts(ContextType.SESSION)
        self.assertTrue(session_result.success)
        
        session_contexts = [c for c in session_result.data if c.type == ContextType.SESSION]
        self.assertGreaterEqual(len(session_contexts), 1)


if __name__ == '__main__':
    unittest.main()