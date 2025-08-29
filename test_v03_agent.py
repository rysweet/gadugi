#!/usr/bin/env python3
"""
Test the V0.3 Agent with Memory Integration
"""

import asyncio
import sys
from pathlib import Path

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "agents" / "base"))
sys.path.insert(0, str(Path(__file__).parent / ".claude"))

from agents.base.v03_agent import V03Agent, AgentCapabilities, TaskOutcome


class TestWorkflowAgent(V03Agent):
    """Test implementation of workflow-manager with v0.3 memory."""

    def __init__(self):
        capabilities = AgentCapabilities(
            can_create_prs=True,
            can_parallelize=True,
            expertise_areas=["git", "workflow", "pr_management"],
            max_parallel_tasks=5,
        )
        super().__init__(
            agent_id="workflow_test_001", agent_type="workflow-manager", capabilities=capabilities
        )

    async def execute_task(self, task: dict) -> TaskOutcome:
        """Execute a workflow task with memory."""
        import datetime

        start = datetime.datetime.now()

        task_type = task.get("type", "workflow")
        description = task.get("description", "Unknown task")

        try:
            # Check if we've done this before
            similar = await self.find_similar_tasks(description)
            if similar:
                print(f"  💡 Found {len(similar)} similar past tasks")
                # Could adapt approach based on past success

            # Simulate workflow phases
            steps = []

            # Access our knowledge base
            pr_knowledge = await self.get_relevant_knowledge("PR best practices")
            if pr_knowledge:
                print(f"  📚 Using knowledge: Found {len(pr_knowledge)} relevant items")
                steps.append("Applied PR best practices from knowledge base")

            workflow_knowledge = await self.get_relevant_knowledge("workflow phases")
            if workflow_knowledge:
                print(f"  📚 Using knowledge: Found {len(workflow_knowledge)} workflow patterns")
                steps.append("Following standard workflow phases")

            # Execute workflow
            phases = [
                "Requirements analysis",
                "Task decomposition",
                "Implementation",
                "Testing",
                "PR creation",
            ]

            for phase in phases:
                print(f"  ▶️ Executing: {phase}")
                await self.memory.remember_short_term(f"Executing {phase} for {description}")
                steps.append(f"Completed {phase}")
                await asyncio.sleep(0.1)  # Simulate work

            # Collaborate via whiteboard
            await self.collaborate(
                f"Workflow complete for {description}", decision="Ready for review"
            )

            duration = (datetime.datetime.now() - start).total_seconds()

            return TaskOutcome(
                success=True,
                task_id=self.current_task_id or "test",
                task_type=task_type,
                steps_taken=steps,
                duration_seconds=duration,
                lessons_learned="Successfully used knowledge base to inform approach",
            )

        except Exception as e:
            duration = (datetime.datetime.now() - start).total_seconds()
            return TaskOutcome(
                success=False,
                task_id=self.current_task_id or "test",
                task_type=task_type,
                steps_taken=steps,
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Error encountered: {e}",
            )


async def main():
    """Test the V0.3 agent system."""
    print("\n" + "=" * 70)
    print("🧪 Testing V0.3 Agent with Knowledge Base and Memory")
    print("=" * 70)

    # Create agent
    agent = TestWorkflowAgent()

    # Check if memory system is running
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Memory system is running")
            else:
                print("⚠️  Memory system not responding properly")
    except Exception:
        print("\n⚠️  Memory system not running!")
        print("   To test with memory, run: .claude/services/memory/start_local.sh")
        print("   Continuing with mock memory...\n")

        # Could use mock memory for testing
        class MockMemory:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def remember_short_term(self, *args, **kwargs):
                return "mock_id"

            async def remember_long_term(self, *args, **kwargs):
                return "mock_id"

            async def recall_memories(self, **kwargs):
                return []

            async def add_knowledge(self, *args, **kwargs):
                return "mock_id"

            async def store_procedure(self, *args, **kwargs):
                return "mock_id"

            async def start_task(self, *args):
                pass

            async def write_to_whiteboard(self, *args, **kwargs):
                pass

            async def recall_procedures(self):
                return []

        # Monkey-patch for testing without server
        agent.memory = MockMemory()
        await agent.memory.__aenter__()

    try:
        # Initialize agent (loads knowledge base)
        await agent.initialize()

        print("\n" + "-" * 70)
        print("📋 TEST 1: Execute Task with Knowledge")
        print("-" * 70)

        # Start a task
        task_id = await agent.start_task("Create PR for memory integration feature")
        print(f"Started task: {task_id}")

        # Execute task
        outcome = await agent.execute_task(
            {
                "type": "workflow",
                "description": "Create PR for memory integration feature",
                "branch": "feature/memory-integration",
            }
        )

        if outcome.success:
            print(f"✅ Task completed successfully in {outcome.duration_seconds:.2f}s")
            print(f"   Steps: {len(outcome.steps_taken)}")
            print(f"   Lesson: {outcome.lessons_learned}")
        else:
            print(f"❌ Task failed: {outcome.error}")

        # Learn from outcome
        await agent.learn_from_outcome(outcome)
        print(f"📝 Agent learned from outcome (success rate: {agent.success_rate:.1%})")

        print("\n" + "-" * 70)
        print("📋 TEST 2: Share Expertise")
        print("-" * 70)

        expertise = await agent.share_expertise("workflow")
        print("Sharing expertise on 'workflow':")
        print(f"  Knowledge items: {expertise['knowledge_items']}")
        print(f"  Procedures: {expertise['procedures']}")
        print(f"  Confidence: {expertise['confidence']:.1%}")

        print("\n" + "-" * 70)
        print("📋 TEST 3: Second Task (Should Use Learning)")
        print("-" * 70)

        # Execute similar task - should find past experience
        await agent.start_task("Create PR for another feature")
        outcome2 = await agent.execute_task(
            {"type": "workflow", "description": "Create PR for another feature"}
        )

        if outcome2.success:
            print(f"✅ Second task completed in {outcome2.duration_seconds:.2f}s")

        # Learn from this too
        await agent.learn_from_outcome(outcome2)
        print(f"📝 Success rate now: {agent.success_rate:.1%}")

        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)

        print("\n📊 Final Statistics:")
        print(f"  Tasks completed: {agent.tasks_completed}")
        print(f"  Success rate: {agent.success_rate:.1%}")
        print(f"  Knowledge loaded: {agent.knowledge_loaded}")
        print(f"  Learned patterns: {len(agent.learned_patterns)} types")

    finally:
        # Clean shutdown
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
