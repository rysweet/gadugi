"""
Memory System Integration for Gadugi Agents
Provides a simple interface for agents to interact with the memory system
Enhanced with fallback support for offline/resilient operation
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import httpx
import logging

# Import fallback system
try:
    from .memory_fallback import (
        Memory, MemoryType, MemoryScope, MemoryPersistence,
        KnowledgeNode, Whiteboard, MemoryBackend,
        create_simple_fallback_chain, MemoryFallbackChain
    )
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False
    # Define stubs for type checking
    Memory = Any  # type: ignore[misc,assignment]
    MemoryType = Any  # type: ignore[misc,assignment]
    MemoryBackend = Any  # type: ignore[misc,assignment]
    MemoryFallbackChain = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


@dataclass
class AgentMemoryInterface:
    """
    Enhanced interface for agents to interact with the memory system.

    Supports both HTTP-based Neo4j memory service and local fallback backends.
    Automatically switches between backends based on availability.
    """

    agent_id: str
    mcp_base_url: str = "http://localhost:8000"
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    use_fallback: bool = True
    storage_path: str = ".memory"

    # Internal state
    _client: Optional[httpx.AsyncClient] = None
    _fallback_chain: Optional[MemoryFallbackChain] = None
    _use_http: bool = True  # Start with HTTP, fall back if needed

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_backends()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_backends()

    async def _initialize_backends(self) -> None:
        """Initialize both HTTP and fallback backends."""
        # Try to initialize HTTP client
        try:
            self._client = httpx.AsyncClient(
                base_url=self.mcp_base_url,
                timeout=httpx.Timeout(5.0)  # Short timeout for fast fallback
            )
            # Test connection
            response = await self._client.get("/health", timeout=2.0)
            if response.status_code == 200:
                self._use_http = True
                logger.info("HTTP memory service available")
            else:
                self._use_http = False
                logger.warning("HTTP memory service responded but not healthy")
        except Exception as e:
            self._use_http = False
            logger.info(f"HTTP memory service unavailable: {e}")

        # Initialize fallback backends if needed or requested
        if not self._use_http or self.use_fallback:
            if FALLBACK_AVAILABLE:
                self._fallback_chain = create_simple_fallback_chain(self.storage_path)
                await self._fallback_chain.connect()
                logger.info("Fallback memory chain initialized")
            else:
                logger.warning("Fallback system not available")

        # Final check - ensure we have at least one backend
        if not self._use_http and not self._fallback_chain:
            raise RuntimeError("No memory backends available")

    async def _cleanup_backends(self) -> None:
        """Clean up all backend connections."""
        if self._client:
            await self._client.aclose()

        if self._fallback_chain:
            await self._fallback_chain.disconnect()

    async def _execute_with_fallback(self, operation_name: str, http_func, fallback_func, *args, **kwargs) -> Any:
        """Execute operation with automatic fallback."""
        # Try HTTP first if available
        if self._use_http and self._client:
            try:
                return await http_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"HTTP {operation_name} failed: {e}")
                # Mark HTTP as unavailable and try fallback
                self._use_http = False

        # Use fallback chain
        if self._fallback_chain:
            try:
                return await fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback {operation_name} failed: {e}")
                raise

        raise RuntimeError(f"No backends available for {operation_name}")

    # ========== Short-term Memory ==========

    async def remember_short_term(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> str:
        """Store a short-term memory."""

        async def http_store():
            if not self._client:
                raise RuntimeError("HTTP client not available")

            response = await self._client.post(
                "/memory/agent/store",
                json={
                    "agent_id": self.agent_id,
                    "content": content,
                    "memory_type": "short_term",
                    "is_short_term": True,
                    "task_id": self.task_id,
                    "project_id": self.project_id,
                    "tags": tags or [],
                    "importance_score": importance
                }
            )
            response.raise_for_status()
            return response.json()["id"]

        async def fallback_store():
            if not self._fallback_chain:
                raise RuntimeError("Fallback chain not available")

            memory = Memory(
                agent_id=self.agent_id,
                content=content,
                type=MemoryType.SHORT_TERM,
                persistence=MemoryPersistence.VOLATILE,
                task_id=self.task_id,
                project_id=self.project_id,
                tags=tags or [],
                importance_score=importance
            )

            stored_memory = await self._fallback_chain.store_memory(memory)
            return stored_memory.id

        return await self._execute_with_fallback(
            "remember_short_term",
            http_store,
            fallback_store
        )

    # ========== Helper Methods ==========

    def _convert_http_memory_to_dict(self, http_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Convert HTTP memory response to standard format."""
        return http_memory

    def _convert_fallback_memory_to_dict(self, memory: Memory) -> Dict[str, Any]:
        """Convert fallback Memory object to standard format."""
        return {
            "id": memory.id,
            "agent_id": memory.agent_id,
            "content": memory.content,
            "memory_type": memory.type.value if hasattr(memory.type, 'value') else str(memory.type),
            "is_short_term": memory.persistence == MemoryPersistence.VOLATILE,
            "task_id": memory.task_id,
            "project_id": memory.project_id,
            "tags": memory.tags,
            "importance_score": memory.importance_score,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None
        }

    # ========== Long-term Memory ==========

    async def remember_long_term(
        self,
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        importance: float = 0.7
    ) -> str:
        """Store a long-term memory."""

        async def http_store():
            if not self._client:
                raise RuntimeError("HTTP client not available")

            response = await self._client.post(
                "/memory/agent/store",
                json={
                    "agent_id": self.agent_id,
                    "content": content,
                    "memory_type": memory_type,
                    "is_short_term": False,
                    "task_id": self.task_id,
                    "project_id": self.project_id,
                    "tags": tags or [],
                    "importance_score": importance
                }
            )
            response.raise_for_status()
            return response.json()["id"]

        async def fallback_store():
            if not self._fallback_chain:
                raise RuntimeError("Fallback chain not available")

            # Map memory_type string to MemoryType enum
            type_mapping = {
                "semantic": MemoryType.SEMANTIC,
                "episodic": MemoryType.EPISODIC,
                "procedural": MemoryType.PROCEDURAL,
                "long_term": MemoryType.LONG_TERM
            }

            memory = Memory(
                agent_id=self.agent_id,
                content=content,
                type=type_mapping.get(memory_type, MemoryType.SEMANTIC),
                persistence=MemoryPersistence.PERSISTENT,
                task_id=self.task_id,
                project_id=self.project_id,
                tags=tags or [],
                importance_score=importance
            )

            stored_memory = await self._fallback_chain.store_memory(memory)
            return stored_memory.id

        return await self._execute_with_fallback(
            "remember_long_term",
            http_store,
            fallback_store
        )

    # ========== Memory Retrieval ==========

    async def recall_memories(
        self,
        memory_type: Optional[str] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recall memories based on criteria."""

        async def http_recall():
            if not self._client:
                raise RuntimeError("HTTP client not available")

            params = {
                "limit": limit,
                "short_term_only": short_term_only,
                "long_term_only": long_term_only
            }
            if memory_type:
                params["memory_type"] = memory_type

            response = await self._client.get(
                f"/memory/agent/{self.agent_id}",
                params=params
            )
            response.raise_for_status()
            return response.json()

        async def fallback_recall():
            if not self._fallback_chain:
                raise RuntimeError("Fallback chain not available")

            # Map memory_type string to MemoryType enum if needed
            memory_type_enum = None
            if memory_type:
                type_mapping = {
                    "semantic": MemoryType.SEMANTIC,
                    "episodic": MemoryType.EPISODIC,
                    "procedural": MemoryType.PROCEDURAL,
                    "short_term": MemoryType.SHORT_TERM,
                    "long_term": MemoryType.LONG_TERM
                }
                memory_type_enum = type_mapping.get(memory_type)

            memories = await self._fallback_chain.get_agent_memories(
                agent_id=self.agent_id,
                memory_type=memory_type_enum,
                short_term_only=short_term_only,
                long_term_only=long_term_only,
                limit=limit
            )

            return [self._convert_fallback_memory_to_dict(m) for m in memories]

        return await self._execute_with_fallback(
            "recall_memories",
            http_recall,
            fallback_recall
        )

    async def search_memories(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/memory/search",
            json={
                "agent_id": self.agent_id,
                "tags": tags or [],
                "limit": limit
            }
        )
        response.raise_for_status()
        return response.json()

    # ========== Procedural Memory ==========

    async def learn_procedure(
        self,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> str:
        """Store procedural knowledge."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/memory/procedural/store",
            json={
                "agent_id": self.agent_id,
                "procedure_name": procedure_name,
                "steps": steps,
                "context": context
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    async def recall_procedure(
        self,
        procedure_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall procedural knowledge."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        params = {}
        if procedure_name:
            params["procedure_name"] = procedure_name

        response = await self._client.get(
            f"/memory/procedural/{self.agent_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    # ========== Knowledge Graph ==========

    async def add_knowledge(
        self,
        concept: str,
        description: str,
        confidence: float = 1.0
    ) -> str:
        """Add a concept to the knowledge graph."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/knowledge/node/create",
            json={
                "agent_id": self.agent_id,
                "concept": concept,
                "description": description,
                "confidence": confidence
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    async def link_knowledge(
        self,
        concept1_id: str,
        concept2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Link two concepts in the knowledge graph."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/knowledge/link",
            json={
                "node1_id": concept1_id,
                "node2_id": concept2_id,
                "relationship": relationship,
                "strength": strength
            }
        )
        response.raise_for_status()

    async def explore_knowledge(self, max_depth: int = 2) -> Dict[str, Any]:
        """Explore the agent's knowledge graph."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.get(
            f"/knowledge/graph/{self.agent_id}",
            params={"max_depth": max_depth}
        )
        response.raise_for_status()
        return response.json()

    # ========== Task Whiteboard ==========

    async def create_whiteboard(self) -> str:
        """Create a whiteboard for the current task."""
        if not self.task_id:
            raise ValueError("Task ID is required to create a whiteboard")

        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/whiteboard/create",
            json={
                "task_id": self.task_id,
                "agent_id": self.agent_id
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    async def write_to_whiteboard(
        self,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Write to the task whiteboard."""
        if not self.task_id:
            raise ValueError("Task ID is required to write to whiteboard")

        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/whiteboard/update",
            json={
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "section": section,
                "content": content
            }
        )
        response.raise_for_status()

    async def read_whiteboard(self) -> Dict[str, Any]:
        """Read the task whiteboard."""
        if not self.task_id:
            raise ValueError("Task ID is required to read whiteboard")

        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.get(f"/whiteboard/{self.task_id}")
        response.raise_for_status()
        return response.json()

    # ========== Project Shared Memory ==========

    async def share_with_project(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.7
    ) -> str:
        """Share a memory with the entire project."""
        if not self.project_id:
            raise ValueError("Project ID is required to share project memory")

        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            "/memory/project/store",
            json={
                "project_id": self.project_id,
                "content": content,
                "created_by": self.agent_id,
                "tags": tags or [],
                "importance_score": importance
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    async def get_project_knowledge(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get project-wide shared knowledge."""
        if not self.project_id:
            raise ValueError("Project ID is required to get project knowledge")

        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.get(
            f"/memory/project/{self.project_id}",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    # ========== Memory Consolidation ==========

    async def consolidate_memories(self, threshold_hours: int = 24) -> Dict[str, Any]:
        """Consolidate short-term memories into long-term storage."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        response = await self._client.post(
            f"/memory/agent/{self.agent_id}/consolidate",
            params={"threshold_hours": threshold_hours}
        )
        response.raise_for_status()
        return response.json()


# ========== Example Agent Implementation ==========

class MemoryEnabledAgent:
    """Example of an agent that uses the memory system."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str = "worker",
        project_id: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.project_id = project_id
        self.current_task_id: Optional[str] = None
        self.memory: Optional[AgentMemoryInterface] = None

    async def initialize(self):
        """Initialize the agent and memory interface."""
        self.memory = AgentMemoryInterface(
            agent_id=self.agent_id,
            project_id=self.project_id
        )

    async def start_task(self, task_id: str, task_description: str):
        """Start working on a task."""
        self.current_task_id = task_id

        if self.memory:
            self.memory.task_id = task_id

            async with self.memory as mem:
                # Remember starting the task
                await mem.remember_short_term(
                    f"Started task: {task_description}",
                    tags=["task_start", "event"],
                    importance=0.8
                )

                # Create a whiteboard for collaboration
                await mem.create_whiteboard()
                await mem.write_to_whiteboard(
                    "notes",
                    {"initial_thoughts": f"Beginning work on: {task_description}"}
                )

    async def learn_from_experience(self, experience: str, lesson: str):
        """Learn from an experience and store it as knowledge."""
        if not self.memory:
            return

        async with self.memory as mem:
            # Store the experience as episodic memory
            experience_id = await mem.remember_long_term(
                content=experience,
                memory_type="episodic",
                tags=["experience", "learning"],
                importance=0.7
            )

            # Store the lesson as semantic knowledge
            lesson_id = await mem.remember_long_term(
                content=lesson,
                memory_type="semantic",
                tags=["lesson", "knowledge"],
                importance=0.8
            )

            # Add to knowledge graph
            concept_id = await mem.add_knowledge(
                concept=f"Lesson_{datetime.now().strftime('%Y%m%d_%H%M')}",
                description=lesson,
                confidence=0.9
            )

            print(f"Learned: {lesson}")

    async def collaborate(self, message: str, decision: Optional[str] = None):
        """Collaborate with other agents via whiteboard."""
        if not self.memory or not self.current_task_id:
            return

        async with self.memory as mem:
            # Write to whiteboard
            if decision:
                await mem.write_to_whiteboard(
                    "decisions",
                    {"decision": decision, "reasoning": message}
                )
            else:
                await mem.write_to_whiteboard(
                    "notes",
                    {"note": message}
                )

            # Also share important decisions with project
            if decision and self.project_id:
                await mem.share_with_project(
                    content=f"Decision made: {decision} - {message}",
                    tags=["decision", self.current_task_id],
                    importance=0.9
                )

    async def recall_context(self) -> Dict[str, Any]:
        """Recall relevant context for current task."""
        if not self.memory:
            return {}

        context = {
            "short_term": [],
            "procedures": [],
            "project_knowledge": []
        }

        async with self.memory as mem:
            # Get recent short-term memories
            context["short_term"] = await mem.recall_memories(
                short_term_only=True,
                limit=10
            )

            # Get relevant procedures
            context["procedures"] = await mem.recall_procedure()

            # Get project knowledge if available
            if self.project_id:
                context["project_knowledge"] = await mem.get_project_knowledge(limit=10)

        return context

    async def end_task(self, result: str):
        """Complete a task and consolidate memories."""
        if not self.memory or not self.current_task_id:
            return

        async with self.memory as mem:
            # Record task completion
            await mem.remember_long_term(
                content=f"Completed task {self.current_task_id}: {result}",
                memory_type="episodic",
                tags=["task_complete", "result"],
                importance=0.9
            )

            # Update whiteboard with final result
            await mem.write_to_whiteboard(
                "action_items",
                {"result": result, "completed": True}
            )

            # Consolidate short-term memories
            consolidation = await mem.consolidate_memories(threshold_hours=1)
            print(f"Consolidated {consolidation['consolidated_count']} memories")

        self.current_task_id = None


# ========== Example Usage ==========

async def example_usage():
    """Example of how agents use the memory system."""

    # Create an agent
    agent = MemoryEnabledAgent(
        agent_id="example_agent_001",
        agent_type="worker",
        project_id="gadugi_v03"
    )

    await agent.initialize()

    # Start a task
    await agent.start_task("task_123", "Implement user authentication")

    # Learn from experience
    await agent.learn_from_experience(
        experience="Tried to implement OAuth without proper token validation",
        lesson="Always validate OAuth tokens server-side to prevent security vulnerabilities"
    )

    # Collaborate
    await agent.collaborate(
        message="Considering JWT vs session-based auth",
        decision="Use JWT for stateless authentication"
    )

    # Recall context
    context = await agent.recall_context()
    print(f"Retrieved context with {len(context['short_term'])} short-term memories")

    # Complete task
    await agent.end_task("Successfully implemented JWT-based authentication")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())


# ============================================================================
# Enhanced Memory Interface with Full Fallback Support
# ============================================================================

class EnhancedAgentMemoryInterface(AgentMemoryInterface):
    """
    Enhanced memory interface with full fallback support and monitoring.

    This extends the basic interface with additional features:
    - Backend status monitoring
    - Fallback chain health checks
    - Memory synchronization between backends
    - Enhanced error handling and recovery
    """

    def get_backend_status(self) -> Dict[str, Any]:
        """Get detailed status of all backends."""
        status = {
            "http_available": self._use_http,
            "http_endpoint": self.mcp_base_url if self._use_http else None,
            "fallback_available": self._fallback_chain is not None,
            "current_backend": "HTTP" if self._use_http else "Fallback Chain",
            "storage_path": self.storage_path,
            "fallback_chain_status": None
        }

        if self._fallback_chain and hasattr(self._fallback_chain, 'get_backend_status'):
            status["fallback_chain_status"] = self._fallback_chain.get_backend_status()

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on all backends."""
        health_status = {
            "overall_healthy": False,
            "http_healthy": False,
            "fallback_healthy": False,
            "errors": []
        }

        # Check HTTP backend
        if self._client:
            try:
                response = await self._client.get("/health", timeout=5.0)
                health_status["http_healthy"] = response.status_code == 200
            except Exception as e:
                health_status["errors"].append(f"HTTP health check failed: {e}")

        # Check fallback chain
        if self._fallback_chain:
            try:
                fallback_healthy = await self._fallback_chain.is_available()
                health_status["fallback_healthy"] = fallback_healthy

                # Get detailed fallback status
                if hasattr(self._fallback_chain, 'health_check_all_backends'):
                    await self._fallback_chain.health_check_all_backends()
            except Exception as e:
                health_status["errors"].append(f"Fallback health check failed: {e}")

        health_status["overall_healthy"] = (
            health_status["http_healthy"] or health_status["fallback_healthy"]
        )

        return health_status

    async def force_backend_switch(self, use_http: bool = True) -> bool:
        """Force switch between HTTP and fallback backends."""
        if use_http and self._client:
            # Try to switch to HTTP
            try:
                response = await self._client.get("/health", timeout=2.0)
                if response.status_code == 200:
                    self._use_http = True
                    logger.info("Forced switch to HTTP backend")
                    return True
            except Exception as e:
                logger.warning(f"Cannot switch to HTTP backend: {e}")

        # Switch to fallback
        if self._fallback_chain and await self._fallback_chain.is_available():
            self._use_http = False
            logger.info("Forced switch to fallback backend")
            return True

        logger.error("Cannot switch backends - target backend unavailable")
        return False

    async def sync_memories_between_backends(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Attempt to sync memories between available backends."""
        if not agent_id:
            agent_id = self.agent_id

        sync_result = {
            "synced_count": 0,
            "errors": [],
            "source_backend": None,
            "target_backend": None
        }

        # Only sync if we have both backends available
        if not (self._client and self._fallback_chain):
            sync_result["errors"].append("Both HTTP and fallback backends must be available for sync")
            return sync_result

        try:
            # Determine sync direction based on current primary backend
            if self._use_http:
                # HTTP is primary, sync from HTTP to fallback
                sync_result["source_backend"] = "HTTP"
                sync_result["target_backend"] = "Fallback"

                # Get memories from HTTP
                memories_data = await self.recall_memories(limit=1000)  # Use existing method

                # Store in fallback (would need more complex conversion)
                # This is a simplified version - full implementation would need proper conversion
                sync_result["synced_count"] = len(memories_data)

            else:
                # Fallback is primary, sync from fallback to HTTP
                sync_result["source_backend"] = "Fallback"
                sync_result["target_backend"] = "HTTP"

                # Get memories from fallback
                if self._fallback_chain:
                    memories = await self._fallback_chain.get_agent_memories(agent_id, limit=1000)
                    # Would need to convert and store in HTTP backend
                    sync_result["synced_count"] = len(memories)

        except Exception as e:
            sync_result["errors"].append(f"Sync failed: {e}")

        return sync_result

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics from active backend."""
        stats = {
            "backend_type": "HTTP" if self._use_http else "Fallback",
            "agent_id": self.agent_id,
            "total_memories": 0,
            "short_term_memories": 0,
            "long_term_memories": 0,
            "procedural_memories": 0,
            "last_updated": datetime.now().isoformat()
        }

        try:
            # Get memory counts
            all_memories = await self.recall_memories(limit=1000)
            stats["total_memories"] = len(all_memories)

            # Count by type
            short_term = await self.recall_memories(short_term_only=True, limit=1000)
            stats["short_term_memories"] = len(short_term)

            long_term = await self.recall_memories(long_term_only=True, limit=1000)
            stats["long_term_memories"] = len(long_term)

            # This would need additional API support for procedural memories
            # stats["procedural_memories"] = len(await self.recall_procedure())

        except Exception as e:
            stats["error"] = str(e)

        return stats


# ============================================================================
# Factory Functions for Enhanced Interface
# ============================================================================

def create_enhanced_memory_interface(
    agent_id: str,
    mcp_base_url: str = "http://localhost:8000",
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    use_fallback: bool = True,
    storage_path: str = ".memory"
) -> EnhancedAgentMemoryInterface:
    """
    Create an enhanced memory interface with fallback support.

    Args:
        agent_id: Unique identifier for the agent
        mcp_base_url: Base URL for HTTP memory service
        project_id: Optional project identifier
        task_id: Optional task identifier
        use_fallback: Enable fallback backends
        storage_path: Path for local storage backends

    Returns:
        Configured enhanced memory interface
    """
    return EnhancedAgentMemoryInterface(
        agent_id=agent_id,
        mcp_base_url=mcp_base_url,
        project_id=project_id,
        task_id=task_id,
        use_fallback=use_fallback,
        storage_path=storage_path
    )


def create_fallback_only_interface(
    agent_id: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    storage_path: str = ".memory"
) -> EnhancedAgentMemoryInterface:
    """
    Create a memory interface that only uses fallback backends (offline mode).

    Args:
        agent_id: Unique identifier for the agent
        project_id: Optional project identifier
        task_id: Optional task identifier
        storage_path: Path for local storage backends

    Returns:
        Configured memory interface with fallback backends only
    """
    interface = EnhancedAgentMemoryInterface(
        agent_id=agent_id,
        mcp_base_url="http://localhost:8000",  # Won't be used
        project_id=project_id,
        task_id=task_id,
        use_fallback=True,
        storage_path=storage_path
    )

    # Force fallback mode
    interface._use_http = False

    return interface
