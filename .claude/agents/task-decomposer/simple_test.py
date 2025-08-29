"""
Simple test for Task Decomposer v0.3 Agent
"""

import asyncio
from datetime import datetime
from task_decomposer_v03 import TaskDecomposerV03, ExecutionFeedback


class MockMemoryInterface:
    """Mock memory interface for testing."""

    def __init__(self):
        self.memories = []
        self.procedures = []
        self.knowledge = []
        self.whiteboard = {}
        self.current_task = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def remember_short_term(self, content, tags=None):
        self.memories.append({
            'content': content,
            'tags': tags or [],
            'type': 'short_term',
            'timestamp': datetime.now().isoformat()
        })

    async def remember_long_term(self, content, tags=None, importance=0.5):
        self.memories.append({
            'content': content,
            'tags': tags or [],
            'type': 'long_term',
            'importance': importance,
            'timestamp': datetime.now().isoformat()
        })

    async def recall_memories(self, memory_types=None, limit=10):
        relevant_memories = []
        for memory in self.memories:
            if memory_types is None or memory['type'] in memory_types:
                relevant_memories.append(memory)
        return relevant_memories[-limit:]

    async def store_procedure(self, procedure_name, steps, context=""):
        procedure = {
            'procedure_name': procedure_name,
            'steps': steps,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.procedures.append(procedure)
        return f"proc_{len(self.procedures)}"

    async def recall_procedure(self):
        return self.procedures

    async def add_knowledge(self, concept, description, confidence=0.7):
        knowledge = {
            'concept': concept,
            'description': description,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        self.knowledge.append(knowledge)
        return f"knowledge_{len(self.knowledge)}"

    async def start_task(self, task_description):
        self.current_task = {
            'description': task_description,
            'start_time': datetime.now().isoformat()
        }

    async def write_to_whiteboard(self, key, value):
        self.whiteboard[key] = value


async def test_task_decomposer():
    """Test the enhanced task decomposer."""
    print("\n" + "="*60)
    print("Testing Task Decomposer v0.3 with Learning")
    print("="*60)

    # Create and setup decomposer with mock
    decomposer = TaskDecomposerV03()
    decomposer.memory = MockMemoryInterface()
    await decomposer.memory.__aenter__()
    await decomposer._initialize_default_strategies()
    decomposer.knowledge_loaded = True

    try:
        print(f"🧠 Loaded {len(decomposer.strategies)} learned decomposition strategies")

        # Test 1: Basic decomposition
        print(f"\n📋 Test 1: Basic task decomposition")
        task = "Implement user authentication with OAuth2 and JWT tokens"
        result = await decomposer.decompose_task(task)

        print(f"✅ Decomposed task into {len(result.subtasks)} subtasks")
        print(f"📊 Parallelization score: {result.parallelization_score:.2f}")
        print(f"⏱️  Estimated time: {result.estimated_total_time} minutes")
        print(f"🔧 Strategy used: {result.strategy_used}")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")

        print("\nSubtasks:")
        for i, subtask in enumerate(result.subtasks[:5]):  # Show first 5
            deps = f" (deps: {len(subtask.dependencies)})" if subtask.dependencies else ""
            parallel = " [||]" if subtask.can_parallelize else " [->]"
            agent = f" [{subtask.agent_hint}]" if subtask.agent_hint else ""
            print(f"  {i+1}. {subtask.name[:50]}...{parallel}{deps}{agent}")
            print(f"     {subtask.complexity} complexity, {subtask.estimated_time}min")

        if len(result.subtasks) > 5:
            print(f"  ... and {len(result.subtasks) - 5} more subtasks")

        # Test 2: Different task patterns
        print(f"\n📋 Test 2: Strategy selection")
        test_tasks = [
            ("Fix authentication bug in login flow", "bug_fix_workflow"),
            ("Refactor database access layer for performance", "refactoring_workflow"),
            ("Create comprehensive test suite for API", "testing_workflow")
        ]

        for task_desc, expected_strategy in test_tasks:
            result = await decomposer.decompose_task(task_desc)
            print(f"  Task: {task_desc[:40]}...")
            print(f"  Strategy: {result.strategy_used} (expected: {expected_strategy})")
            print(f"  Subtasks: {len(result.subtasks)}, Parallelization: {result.parallelization_score:.2f}")

        # Test 3: Learning from execution
        print(f"\n📋 Test 3: Learning from execution feedback")
        feedback = ExecutionFeedback(
            decomposition_id="test_123",
            actual_completion_time=150.0,
            success_rate=0.9,
            parallelization_achieved=0.7,
            bottlenecks=["database_setup", "oauth_integration"],
            improvements=["parallel_testing", "automated_deployment"],
            agent_performance={
                "code-writer": 0.85,
                "test-writer": 0.92,
                "code-reviewer": 0.88
            }
        )

        await decomposer.learn_from_execution(feedback)
        print(f"✅ Learned from execution feedback")

        # Test 4: Get insights
        print(f"\n📋 Test 4: Performance insights")
        insights = await decomposer.get_decomposition_insights()
        print(f"  Total decompositions: {insights['performance_metrics']['total_decompositions']}")
        print(f"  Success rate: {insights['performance_metrics']['success_rate']:.1%}")
        print(f"  Avg parallelization: {insights['performance_metrics']['avg_parallelization_achieved']:.2f}")
        print(f"  Strategies learned: {insights['capabilities']['strategies_learned']}")

        # Test 5: Complex task with optimization suggestions
        print(f"\n📋 Test 5: Complex task with optimization suggestions")
        complex_task = "Build microservices-based e-commerce platform with user management, inventory, payments, and analytics"
        result = await decomposer.decompose_task(complex_task)

        print(f"✅ Complex task decomposition:")
        print(f"  Subtasks: {len(result.subtasks)}")
        print(f"  Parallelization: {result.parallelization_score:.2f}")
        print(f"  Strategy: {result.strategy_used}")
        print(f"  Optimization suggestions: {len(result.optimization_suggestions)}")

        for suggestion in result.optimization_suggestions[:3]:
            print(f"    💡 {suggestion}")

        # Test 6: Execute task interface
        print(f"\n📋 Test 6: Execute task interface")
        task_spec = {
            "description": "Create integration tests for payment processing module",
            "context": {
                "time_constraint": "2 weeks",
                "team_size": 3,
                "parallel_capable": True
            }
        }

        outcome = await decomposer.execute_task(task_spec)
        print(f"✅ Task execution: {'SUCCESS' if outcome.success else 'FAILED'}")
        print(f"  Duration: {outcome.duration_seconds:.2f}s")
        print(f"  Steps: {len(outcome.steps_taken)}")
        print(f"  Lesson: {outcome.lessons_learned}")

        print(f"\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await decomposer.memory.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_task_decomposer())
