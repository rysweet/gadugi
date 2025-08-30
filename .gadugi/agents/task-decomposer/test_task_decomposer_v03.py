"""
Test suite for Task Decomposer v0.3 Agent
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional

from task_decomposer_v03 import (
    TaskDecomposerV03,
    ExecutionFeedback,
)
from ...shared.memory_integration import AgentMemoryInterface


class MockMemoryInterface(AgentMemoryInterface):
    """Mock memory interface for testing."""

    def __init__(self):
        # Initialize parent with agent_id
        super().__init__(agent_id="test_agent", mcp_base_url="http://localhost:8000")
        # Mock state
        self.memories = []
        self.procedures = []
        self.knowledge = []
        self.whiteboard = {}
        self.current_task = None
        self._client = None

    async def __aenter__(self):
        # Don't actually create a client in tests
        self._client = "mock_client"  # type: ignore
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._client = None

    async def remember_short_term(
        self, content: str, tags: Optional[List[str]] = None, importance: float = 0.5
    ) -> str:
        self.memories.append(
            {
                "content": content,
                "tags": tags or [],
                "type": "short_term",
                "timestamp": datetime.now().isoformat(),
            }
        )
        return f"memory_{len(self.memories)}"

    async def remember_long_term(
        self,
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        importance: float = 0.7,
    ) -> str:
        self.memories.append(
            {
                "content": content,
                "tags": tags or [],
                "type": "long_term",
                "memory_type": memory_type,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return f"memory_{len(self.memories)}"

    async def recall_memories(
        self,
        memory_type: Optional[str] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        relevant_memories = []
        for memory in self.memories:
            if short_term_only and memory["type"] != "short_term":
                continue
            if long_term_only and memory["type"] != "long_term":
                continue
            if memory_type and memory.get("memory_type") != memory_type:
                continue
            relevant_memories.append(memory)
        return relevant_memories[-limit:]

    async def store_procedure(
        self,
        procedure_name: str,
        steps: List[str],
        context: str = "",
        tags: Optional[List[str]] = None,
    ) -> str:
        procedure = {
            "procedure_name": procedure_name,
            "steps": steps,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.procedures.append(procedure)
        return f"proc_{len(self.procedures)}"

    async def recall_procedure(
        self,
        procedure_name: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        return self.procedures

    async def add_knowledge(
        self, concept: str, description: str, confidence: float = 1.0
    ) -> str:
        knowledge = {
            "concept": concept,
            "description": description,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        self.knowledge.append(knowledge)
        return f"knowledge_{len(self.knowledge)}"

    async def start_task(self, task_description: str) -> str:
        self.current_task = {
            "description": task_description,
            "start_time": datetime.now().isoformat(),
        }
        return "task_001"

    async def write_to_whiteboard(self, section: str, content: Dict[str, Any]) -> None:
        self.whiteboard[section] = content


async def create_test_decomposer():
    """Create a task decomposer with mock memory."""
    decomposer = TaskDecomposerV03()

    # Override memory with mock
    decomposer.memory = MockMemoryInterface()
    await decomposer.memory.__aenter__()

    # Initialize strategies manually (since we're skipping full initialization)
    await decomposer._initialize_default_strategies()
    decomposer.knowledge_loaded = True

    return decomposer


async def test_basic_decomposition():
    """Test basic task decomposition functionality."""
    decomposer = await create_test_decomposer()
    task_description = (
        "Implement user authentication system with login and registration"
    )

    result = await decomposer.decompose_task(task_description)

    assert result.original_task == task_description
    assert len(result.subtasks) > 0
    assert result.parallelization_score >= 0.0
    assert result.parallelization_score <= 1.0
    assert result.estimated_total_time > 0
    assert (
        result.strategy_used in decomposer.strategies
        or result.strategy_used == "adaptive"
    )


@pytest.mark.asyncio
async def test_strategy_selection(decomposer):
    """Test strategy selection based on task patterns."""
    # Test feature implementation pattern
    feature_task = "Implement new payment processing feature"
    result = await decomposer.decompose_task(feature_task)
    assert result.strategy_used == "feature_implementation"

    # Test bug fix pattern
    bug_task = "Fix login authentication bug"
    result = await decomposer.decompose_task(bug_task)
    assert result.strategy_used == "bug_fix_workflow"

    # Test refactoring pattern
    refactor_task = "Refactor database access layer"
    result = await decomposer.decompose_task(refactor_task)
    assert result.strategy_used == "refactoring_workflow"


@pytest.mark.asyncio
async def test_complexity_analysis(decomposer):
    """Test complexity analysis functionality."""
    # High complexity task
    complex_task = "Implement distributed microservices architecture with service mesh"
    complexity = await decomposer._analyze_task_complexity(complex_task, None)
    assert complexity["level"] in ["medium", "high"]

    # Low complexity task
    simple_task = "Fix typo in documentation"
    complexity = await decomposer._analyze_task_complexity(simple_task, None)
    assert complexity["level"] in ["low", "medium"]


@pytest.mark.asyncio
async def test_dependency_analysis(decomposer):
    """Test dependency analysis between subtasks."""
    task_description = "Create REST API with database integration"
    result = await decomposer.decompose_task(task_description)

    # Check that dependencies are properly established
    assert len(result.dependency_graph) == len(result.subtasks)

    # Verify logical dependencies (testing should depend on implementation)
    implementation_tasks = [
        st for st in result.subtasks if "implement" in st.name.lower()
    ]
    testing_tasks = [st for st in result.subtasks if "test" in st.name.lower()]

    if implementation_tasks and testing_tasks:
        test_task_id = testing_tasks[0].id
        impl_task_id = implementation_tasks[0].id
        # Test task should have implementation as dependency
        assert any(
            impl_task_id in result.dependency_graph.get(test_task_id, [])
            for impl_task_id in [impl.id for impl in implementation_tasks]
        )


@pytest.mark.asyncio
async def test_parallelization_estimation(decomposer):
    """Test parallelization score calculation."""
    task_description = "Build web application with frontend and backend"
    result = await decomposer.decompose_task(task_description)

    # Should have reasonable parallelization (web apps can be quite parallel)
    assert result.parallelization_score > 0.3
    assert result.parallelization_score <= 1.0

    # Check that parallelizable tasks are identified
    parallelizable_tasks = [st for st in result.subtasks if st.can_parallelize]
    assert len(parallelizable_tasks) > 0


@pytest.mark.asyncio
async def test_learning_from_execution(decomposer):
    """Test learning from execution feedback."""
    # First, decompose a task
    task_description = "Implement user profile management"
    result = await decomposer.decompose_task(task_description)

    # Simulate execution feedback
    feedback = ExecutionFeedback(
        decomposition_id="test_decomp_123",
        actual_completion_time=150.0,
        success_rate=0.9,
        parallelization_achieved=0.6,
        bottlenecks=["database_setup"],
        improvements=["parallel_testing"],
        agent_performance={"code-writer": 0.85, "TestWriter": 0.90},
    )

    initial_decompositions = decomposer.total_decompositions
    await decomposer.learn_from_execution(feedback)

    # Check that learning was recorded
    assert len(decomposer.memory.memories) > 0

    # Check that feedback influenced metrics
    assert decomposer.avg_parallelization_achieved >= 0.0


@pytest.mark.asyncio
async def test_execution_task_interface(decomposer):
    """Test the execute_task interface."""
    task = {
        "description": "Create unit tests for authentication module",
        "context": {"time_constraint": "1 week", "team_size": 2},
    }

    outcome = await decomposer.execute_task(task)

    assert outcome.success == True
    assert outcome.task_type == "decomposition"
    assert len(outcome.steps_taken) > 0
    assert outcome.duration_seconds >= 0
    assert outcome.lessons_learned is not None


@pytest.mark.asyncio
async def test_optimization_suggestions(decomposer):
    """Test generation of optimization suggestions."""
    task_description = "Build complex data processing pipeline"
    result = await decomposer.decompose_task(task_description)

    # Should have some optimization suggestions for complex tasks
    assert isinstance(result.optimization_suggestions, list)


@pytest.mark.asyncio
async def test_insights_generation(decomposer):
    """Test insights generation functionality."""
    # Generate some activity first
    await decomposer.decompose_task("Test task 1")
    await decomposer.decompose_task("Test task 2")

    insights = await decomposer.get_decomposition_insights()

    assert "performance_metrics" in insights
    assert "strategy_performance" in insights
    assert "capabilities" in insights
    assert insights["performance_metrics"]["total_decompositions"] >= 2


@pytest.mark.asyncio
async def test_can_handle_task(decomposer):
    """Test task capability assessment."""
    # Should be able to handle decomposition requests
    assert await decomposer.can_handle_task("decompose this complex task")
    assert await decomposer.can_handle_task("break down this workflow")

    # Should be able to handle complex tasks that benefit from decomposition
    assert await decomposer.can_handle_task("implement comprehensive system")
    assert await decomposer.can_handle_task("build microservices platform")


@pytest.mark.asyncio
async def test_adaptive_decomposition(decomposer):
    """Test adaptive decomposition for unknown patterns."""
    # Use a task that doesn't match any specific pattern
    unusual_task = "Perform quantum computing analysis for blockchain optimization"
    result = await decomposer.decompose_task(unusual_task)

    # Should fall back to adaptive strategy
    assert result.strategy_used == "adaptive"
    assert len(result.subtasks) > 0
    assert result.parallelization_score >= 0.0


@pytest.mark.asyncio
async def test_agent_suggestions(decomposer):
    """Test agent assignment suggestions."""
    task_description = "Implement and test new API endpoints"
    result = await decomposer.decompose_task(task_description)

    # Should suggest appropriate agents for different subtasks
    agent_hints = [st.agent_hint for st in result.subtasks if st.agent_hint]

    # Should have some agent suggestions
    assert len(agent_hints) > 0

    # Should suggest appropriate agents
    suggested_agents = set(agent_hints)
    expected_agents = {"code-writer", "TestWriter", "CodeReviewer", "ReadmeAgent"}
    assert len(suggested_agents & expected_agents) > 0


if __name__ == "__main__":
    # Run a simple test
    async def simple_test():
        print("Running simple Task Decomposer v0.3 test...")

        decomposer = TaskDecomposerV03()
        decomposer.memory = MockMemoryInterface()
        await decomposer.memory.__aenter__()
        await decomposer._initialize_default_strategies()
        decomposer.knowledge_loaded = True

        try:
            # Test basic decomposition
            task = "Implement user authentication with OAuth2 and JWT tokens"
            result = await decomposer.decompose_task(task)

            print(f"✅ Decomposed task into {len(result.subtasks)} subtasks")
            print(f"📊 Parallelization score: {result.parallelization_score:.2f}")
            print(f"⏱️  Estimated time: {result.estimated_total_time} minutes")
            print(f"🔧 Strategy used: {result.strategy_used}")

            print("\nSubtasks:")
            for i, subtask in enumerate(result.subtasks):
                deps = (
                    f" (depends on: {', '.join(subtask.dependencies)})"
                    if subtask.dependencies
                    else ""
                )
                parallel_marker = " [PARALLEL]" if subtask.can_parallelize else ""
                print(f"  {i+1}. {subtask.name}{parallel_marker}{deps}")
                print(
                    f"     Complexity: {subtask.complexity}, Time: {subtask.estimated_time}min"
                )
                if subtask.agent_hint:
                    print(f"     Suggested agent: {subtask.agent_hint}")

            print("\n✅ Test completed successfully!")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
        finally:
            await decomposer.memory.__aexit__(None, None, None)

    # Run the simple test
    asyncio.run(simple_test())
