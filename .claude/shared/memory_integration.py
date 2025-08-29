"""
Memory System Integration for Gadugi Agents
Provides a simple interface for agents to interact with the memory system
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx


@dataclass
class AgentMemoryInterface:
    """Interface for agents to interact with the memory system."""
    
    agent_id: str
    mcp_base_url: str = "http://localhost:8000"
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    _client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(base_url=self.mcp_base_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    # ========== Short-term Memory ==========
    
    async def remember_short_term(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> str:
        """Store a short-term memory."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
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
    
    # ========== Long-term Memory ==========
    
    async def remember_long_term(
        self,
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        importance: float = 0.7
    ) -> str:
        """Store a long-term memory."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
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
    
    # ========== Memory Retrieval ==========
    
    async def recall_memories(
        self,
        memory_type: Optional[str] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recall memories based on criteria."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
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