"""
Memory Management Mixin for V03Agent
===================================

This mixin handles all memory-related functionality including:
- Knowledge base loading
- Memory recall and storage
- Learning from outcomes
- Knowledge retrieval and management
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

from ...shared.memory_integration import AgentMemoryInterface

# Forward references for types defined in the main file
if TYPE_CHECKING:
    from .v03_agent import TaskOutcome
    from .whiteboard_collaboration import WhiteboardManager


class MemoryMixinProtocol(Protocol):
    """Protocol defining expected attributes for classes using MemoryMixin."""
    memory: Optional[AgentMemoryInterface]
    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    whiteboard_manager: Optional['WhiteboardManager']
    knowledge_loaded: bool
    learned_patterns: Dict[str, List[Dict[str, Any]]]
    tasks_completed: int
    success_rate: float


class MemoryMixin:
    """
    Mixin providing memory management capabilities for V03Agent.

    This mixin requires the following attributes to be present on the class:
    - memory: Optional[AgentMemoryInterface]
    - agent_id: str
    - agent_type: str
    - current_task_id: Optional[str]
    - whiteboard_manager: Optional[WhiteboardManager]
    - knowledge_loaded: bool
    - learned_patterns: Dict[str, List[Dict]]
    - tasks_completed: int
    - success_rate: float
    """

    # Type hints for attributes expected from the base class
    memory: Optional[AgentMemoryInterface]
    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    whiteboard_manager: Optional['WhiteboardManager']
    knowledge_loaded: bool
    learned_patterns: Dict[str, List[Dict[str, Any]]]
    tasks_completed: int
    success_rate: float

    async def _load_knowledge_base(self) -> None:
        """Load agent's knowledge from MD files."""
        knowledge_dir = Path(f".claude/agents/{self.agent_type}/knowledge")

        if not knowledge_dir.exists():
            # Try alternative path
            knowledge_dir = Path(f".claude/agents/{self.agent_type.replace('-', '_')}/knowledge")

        if knowledge_dir.exists():
            print(f"📚 Loading knowledge base from {knowledge_dir}")
            loaded_count = 0

            for md_file in knowledge_dir.glob("*.md"):
                try:
                    content = md_file.read_text()

                    # Extract title from first # heading if present
                    lines = content.split('\n')
                    title = md_file.stem
                    for line in lines:
                        if line.startswith('# '):
                            title = line[2:].strip()
                            break

                    # Create knowledge node
                    if self.memory:
                        knowledge_id = await self.memory.add_knowledge(
                            concept=title,
                            description=content[:500],  # First 500 chars as description
                            confidence=0.9  # High confidence for pre-loaded knowledge
                        )

                        # Also store as long-term memory for retrieval
                        await self.memory.remember_long_term(
                            content,
                            tags=["knowledge_base", md_file.stem, "foundational"]
                        )

                    loaded_count += 1
                    print(f"  📖 Loaded: {title}")

                except Exception as e:
                    print(f"  ⚠️ Failed to load {md_file.name}: {e}")

            self.knowledge_loaded = True
            print(f"  ✅ Loaded {loaded_count} knowledge files")
        else:
            print(f"  ℹ️ No knowledge directory at {knowledge_dir}")

    async def _recall_recent_context(self, limit: int = 10) -> None:
        """Recall recent memories to establish context."""
        try:
            memories = []
            if self.memory:
                memories = await self.memory.recall_memories(limit=limit)

            if memories:
                print(f"🧠 Recalled {len(memories)} recent memories")

                # Analyze patterns in recent memories
                for memory in memories:
                    if memory.get('memory_type') == 'procedural':
                        task_type = memory.get('metadata', {}).get('task_type')
                        if task_type:
                            if task_type not in self.learned_patterns:
                                self.learned_patterns[task_type] = []
                            self.learned_patterns[task_type].append(memory)
        except Exception as e:
            print(f"  ℹ️ No recent memories available: {e}")

    async def learn_from_outcome(self, outcome: 'TaskOutcome') -> None:
        """Learn from task execution outcome."""
        if outcome.success:
            # Store successful pattern
            if not self.memory:
                return
            procedure_id = await self.memory.learn_procedure(
                procedure_name=f"successful_{outcome.task_type}",
                steps=outcome.steps_taken,
                context=f"Task {outcome.task_id} completed in {outcome.duration_seconds}s"
            )

            # Remember the success
            await self.memory.remember_long_term(
                f"Successfully completed {outcome.task_type}: {outcome.lessons_learned or 'No specific lessons'}",
                tags=["success", outcome.task_type, "learning"],
                importance=0.8
            )

            # Update success rate
            self.tasks_completed += 1
            self.success_rate = (
                (self.success_rate * (self.tasks_completed - 1) + 1.0)
                / self.tasks_completed
            )

            print(f"✅ Learned from success: {outcome.task_type}")
        else:
            # Remember what didn't work
            if self.memory:
                await self.memory.remember_long_term(
                f"Failed {outcome.task_type}: {outcome.error}. Lesson: {outcome.lessons_learned or 'Analyze error'}",
                tags=["failure", outcome.task_type, "learning", "error"],
                importance=0.9  # High importance for failures
            )

            # Update success rate
            self.tasks_completed += 1
            self.success_rate = (
                self.success_rate * (self.tasks_completed - 1)
                / self.tasks_completed
            )

            print(f"📝 Learned from failure: {outcome.task_type}")

    async def find_similar_tasks(self, task_description: str) -> List[Dict[str, Any]]:
        """Find similar tasks from memory."""
        if not self.memory:
            return []
        # Search memories for similar content
        # This is a simplified version - could use embeddings for better similarity
        memories = await self.memory.recall_memories(limit=50)

        similar = []
        task_words = set(task_description.lower().split())

        for memory in memories:
            content = memory.get('content', '').lower()
            content_words = set(content.split())

            # Simple word overlap similarity
            overlap = len(task_words & content_words)
            if overlap > min(3, len(task_words) // 2):
                similar.append(memory)

        return similar[:5]  # Top 5 most relevant

    async def get_relevant_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge for a query."""
        if not self.memory:
            return []
        # Search long-term memories
        memories = await self.memory.recall_memories(
            long_term_only=True,
            limit=20
        )

        # Filter for relevance (simple keyword matching)
        query_words = set(query.lower().split())
        relevant = []

        for memory in memories:
            content = memory.get('content', '').lower()
            if any(word in content for word in query_words):
                relevant.append(memory)

        return relevant

    async def share_expertise(self, topic: str) -> Dict[str, Any]:
        """Share agent's expertise on a topic."""
        knowledge = await self.get_relevant_knowledge(topic)
        procedures = [] if not self.memory else await self.memory.recall_procedure()

        # Filter procedures related to topic
        relevant_procedures = [
            p for p in procedures
            if topic.lower() in p.get('procedure_name', '').lower()
        ]

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "expertise_shared": topic,
            "knowledge_items": len(knowledge),
            "procedures": len(relevant_procedures),
            "confidence": self.success_rate,
            "knowledge": knowledge[:5],  # Top 5 items
            "procedures": relevant_procedures[:3]  # Top 3 procedures
        }

    async def remember_task_start(self, task_description: str) -> None:
        """Remember that a task has started."""
        if self.memory:
            await self.memory.remember_short_term(
                f"Started task: {task_description}",
                tags=["task_start", "event"],
                importance=0.8
            )

    async def remember_shutdown(self) -> None:
        """Remember agent shutdown with metrics."""
        if not self.memory:
            return
        await self.memory.remember_long_term(
            f"Agent {self.agent_id} shutting down. Tasks completed: {self.tasks_completed}, Success rate: {self.success_rate:.2%}",
            tags=["shutdown", "metrics"]
        )
