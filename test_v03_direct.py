#!/usr/bin/env python3
"""
Test V0.3 Agent with Direct SQLite Backend (no server required)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / ".claude"))

# Import SQLite backend directly
from services.memory.sqlite_memory_backend import SQLiteMemoryBackend


class DirectMemoryInterface:
    """Direct memory interface using SQLite (no HTTP needed)."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.backend = SQLiteMemoryBackend(db_path=".claude/data/v03_test.db")
        self.current_task_id = None

    async def __aenter__(self):
        await self.backend.initialize()
        return self

    async def __aexit__(self, *args):
        pass

    async def remember_short_term(self, content: str, tags=None, importance=0.5):
        return await self.backend.store_memory(
            self.agent_id,
            content,
            "short_term",
            task_id=self.current_task_id,
            importance_score=importance,
            metadata={"tags": tags} if tags else None,
        )

    async def remember_long_term(self, content: str, tags=None, importance=0.7):
        return await self.backend.store_memory(
            self.agent_id,
            content,
            "long_term",
            importance_score=importance,
            metadata={"tags": tags} if tags else None,
        )

    async def recall_memories(self, limit=10, memory_types=None):
        return await self.backend.get_memories(
            self.agent_id, memory_type=memory_types[0] if memory_types else None, limit=limit
        )

    async def start_task(self, description: str):
        import hashlib

        task_hash = hashlib.md5(f"{description}{datetime.now().isoformat()}".encode()).hexdigest()[
            :8
        ]
        self.current_task_id = f"task_{task_hash}"
        await self.backend.create_whiteboard(self.current_task_id, self.agent_id)
        return self.current_task_id

    async def write_to_whiteboard(self, key: str, value: dict):
        await self.backend.update_whiteboard(self.current_task_id, content={key: value})

    async def add_knowledge(self, concept: str, description: str, confidence=0.8):
        return await self.backend.add_knowledge_node(
            self.agent_id, concept, description, confidence
        )

    async def store_procedure(self, procedure_name: str, steps: list, context: str):
        return await self.backend.store_procedure(self.agent_id, procedure_name, steps, context)

    async def recall_procedures(self):
        return await self.backend.get_procedures(self.agent_id)


class SimpleV03Agent:
    """Simplified V0.3 agent for testing."""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory = DirectMemoryInterface(agent_id)
        self.knowledge_loaded = False
        self.success_rate = 0.0
        self.tasks_completed = 0

    async def initialize(self):
        """Initialize agent with memory."""
        await self.memory.__aenter__()
        await self._load_knowledge_base()
        print(f"✅ {self.agent_type} agent initialized")

    async def _load_knowledge_base(self):
        """Load knowledge from MD files."""
        knowledge_dir = Path(f".claude/agents/{self.agent_type}/knowledge")

        if knowledge_dir.exists():
            print(f"📚 Loading knowledge from {knowledge_dir}")

            for md_file in knowledge_dir.glob("*.md"):
                try:
                    content = md_file.read_text()

                    # Extract title
                    title = md_file.stem
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break

                    # Store as knowledge
                    await self.memory.add_knowledge(
                        title,
                        content[:500],  # First 500 chars
                        confidence=0.9,
                    )

                    # Also store as long-term memory
                    await self.memory.remember_long_term(
                        content, tags=["knowledge_base", md_file.stem]
                    )

                    print(f"  📖 Loaded: {title}")

                except Exception as e:
                    print(f"  ⚠️ Failed to load {md_file.name}: {e}")

            self.knowledge_loaded = True

    async def execute_task(self, description: str):
        """Execute a task with memory."""
        # Start task
        task_id = await self.memory.start_task(description)
        print(f"\n📋 Task {task_id}: {description}")

        # Check for similar past tasks
        memories = await self.memory.recall_memories(limit=20)
        similar = [m for m in memories if description.lower() in m.get("content", "").lower()]

        if similar:
            print(f"  💡 Found {len(similar)} similar past experiences")

        # Simulate task execution
        steps = [
            "Analyzing requirements",
            "Planning approach",
            "Implementing solution",
            "Testing",
            "Documenting",
        ]

        for step in steps:
            print(f"  ▶️ {step}")
            await self.memory.remember_short_term(f"{step}: {description}")
            await asyncio.sleep(0.1)

        # Store success
        await self.memory.remember_long_term(
            f"Successfully completed: {description}", tags=["success", "completed"]
        )

        # Update whiteboard
        await self.memory.write_to_whiteboard("status", {"completed": True, "steps": len(steps)})

        # Store procedure
        await self.memory.store_procedure(
            f"procedure_{self.tasks_completed}", steps, f"Context: {description}"
        )

        # Update metrics
        self.tasks_completed += 1
        self.success_rate = (
            (self.success_rate * (self.tasks_completed - 1)) + 1.0
        ) / self.tasks_completed

        print(f"  ✅ Task completed (Success rate: {self.success_rate:.1%})")

        return True


async def main():
    """Test V0.3 agent with direct SQLite backend."""

    print("\n" + "=" * 70)
    print("🧪 Testing V0.3 Agent with Direct Memory Backend")
    print("=" * 70)
    print("No server required - using SQLite directly")
    print("=" * 70)

    # Test workflow-manager agent
    print("\n📤 Testing workflow-manager agent...")
    workflow_agent = SimpleV03Agent("workflow_001", "workflow-manager")
    await workflow_agent.initialize()

    # Execute tasks
    await workflow_agent.execute_task("Create PR for feature X")
    await workflow_agent.execute_task("Fix type errors in codebase")
    await workflow_agent.execute_task("Update documentation")

    # Test orchestrator agent
    print("\n📤 Testing orchestrator agent...")
    orchestrator_agent = SimpleV03Agent("orchestrator_001", "orchestrator")
    await orchestrator_agent.initialize()

    await orchestrator_agent.execute_task("Parallelize test execution")
    await orchestrator_agent.execute_task("Decompose large feature")

    # Show memory stats
    print("\n" + "=" * 70)
    print("📊 Memory System Statistics")
    print("=" * 70)

    backend = workflow_agent.memory.backend
    stats = await backend.get_stats()

    print(f"Total memories: {stats.get('total_memories', 0)}")
    print(f"Knowledge nodes: {stats.get('total_knowledge_nodes', 0)}")
    print(f"Whiteboards: {stats.get('total_whiteboards', 0)}")
    print(f"Procedures: {stats.get('total_procedures', 0)}")

    if "memory_types" in stats:
        print("\nMemory breakdown:")
        for mem_type, count in stats["memory_types"].items():
            print(f"  {mem_type}: {count}")

    # Test memory recall
    print("\n" + "=" * 70)
    print("🧠 Testing Memory Recall")
    print("=" * 70)

    # Recall workflow agent's memories
    memories = await workflow_agent.memory.recall_memories(limit=5)
    print(f"\nWorkflow agent memories ({len(memories)} most recent):")
    for mem in memories[:3]:
        content = mem.get("content", "")[:60]
        print(f"  - {content}...")

    # Recall procedures
    procedures = await workflow_agent.memory.recall_procedures()
    print(f"\nWorkflow agent procedures: {len(procedures)}")
    for proc in procedures[:2]:
        print(f"  - {proc.get('procedure_name')}: {len(proc.get('steps', []))} steps")

    print("\n" + "=" * 70)
    print("✅ V0.3 Agent Test Complete!")
    print("=" * 70)
    print("\nKey achievements:")
    print("  • Agents loaded knowledge from MD files")
    print("  • Tasks executed with memory persistence")
    print("  • Procedures stored for future use")
    print("  • Whiteboards created for collaboration")
    print("  • Direct SQLite backend (no server needed)")
    print("\nThe agents are now memory-enabled and ready for v0.3!")


if __name__ == "__main__":
    asyncio.run(main())
