"""Tests for the Task Decomposer Agent."""

import json
import tempfile
from pathlib import Path

import pytest
from typing import Dict, List

# Import from the actual implementation
import sys
import os

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", ".claude", "agents", "task-decomposer"
    ),
)

from task_decomposer import (
    DecompositionResult,
    PatternDatabase,
    SubTask,
    TaskDecomposer,
)


class TestSubTask:
    """Test SubTask dataclass."""

    def test_subtask_creation(self):
        """Test creating a SubTask instance."""
        subtask = SubTask(
            id="test_001",
            name="Test Task",
            description="A test subtask",
            dependencies=["dep_001"],
            estimated_time=60,
            complexity="medium",
            can_parallelize=True,
            resource_requirements={"cpu": 2, "memory": "4GB"},
        )

        assert subtask.id == "test_001"
        assert subtask.name == "Test Task"
        assert subtask.description == "A test subtask"
        assert subtask.dependencies == ["dep_001"]
        assert subtask.estimated_time == 60
        assert subtask.complexity == "medium"
        assert subtask.can_parallelize is True
        assert subtask.resource_requirements == {"cpu": 2, "memory": "4GB"}

    def test_subtask_to_dict(self):
        """Test converting SubTask to dictionary."""
        subtask = SubTask(
            id="test_002",
            name="Another Task",
            description="Another test subtask",
        )

        result = subtask.to_dict()
        assert isinstance(result, dict)
        assert result["id"] == "test_002"
        assert result["name"] == "Another Task"
        assert result["dependencies"] == []
        assert result["can_parallelize"] is True


class TestDecompositionResult:
    """Test DecompositionResult dataclass."""

    def test_decomposition_result_creation(self):
        """Test creating a DecompositionResult."""
        subtasks = [
            SubTask(id="sub_001", name="Task 1", description="First task"),
            SubTask(id="sub_002", name="Task 2", description="Second task"),
        ]

        result = DecompositionResult(
            original_task="Complex task",
            subtasks=subtasks,
            dependency_graph={"sub_002": ["sub_001"]},
            parallelization_score=0.7,
            estimated_total_time=120,
            decomposition_pattern="feature_implementation",
        )

        assert result.original_task == "Complex task"
        assert len(result.subtasks) == 2
        assert result.parallelization_score == 0.7
        assert result.estimated_total_time == 120

    def test_decomposition_result_to_dict(self):
        """Test converting DecompositionResult to dictionary."""
        subtasks = [SubTask(id="sub_001", name="Task 1", description="First task")]

        result = DecompositionResult(
            original_task="Simple task",
            subtasks=subtasks,
            dependency_graph={},
            parallelization_score=1.0,
            estimated_total_time=60,
        )

        dict_result = result.to_dict()
        assert isinstance(dict_result, dict)
        assert dict_result["original_task"] == "Simple task"
        assert len(dict_result["subtasks"]) == 1
        assert dict_result["parallelization_score"] == 1.0


class TestPatternDatabase:
    """Test PatternDatabase functionality."""

    def test_pattern_database_initialization(self):
        """Test PatternDatabase initialization with default patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            db = PatternDatabase(storage_path=db_path)

            assert "feature_implementation" in db.patterns
            assert "bug_fix" in db.patterns
            assert "refactoring" in db.patterns

    def test_find_matching_pattern(self):
        """Test pattern matching based on triggers."""
        db = PatternDatabase()

        # Test feature implementation pattern
        assert (
            db.find_matching_pattern("implement new authentication")
            == "feature_implementation"
        )
        assert (
            db.find_matching_pattern("create user dashboard")
            == "feature_implementation"
        )

        # Test bug fix pattern
        assert db.find_matching_pattern("fix login issue") == "bug_fix"
        assert db.find_matching_pattern("resolve memory leak") == "bug_fix"

        # Test refactoring pattern
        assert db.find_matching_pattern("refactor database layer") == "refactoring"
        assert db.find_matching_pattern("optimize query performance") == "refactoring"

        # Test no match
        assert db.find_matching_pattern("unknown task type") is None

    def test_update_pattern_metrics(self):
        """Test updating pattern success metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            db = PatternDatabase(storage_path=db_path)

            initial_rate = db.patterns["feature_implementation"]["success_rate"]
            initial_parallel = db.patterns["feature_implementation"][
                "avg_parallelization"
            ]

            # Update with success
            db.update_pattern_metrics(
                "feature_implementation", success=True, parallelization_score=0.8
            )

            # Check metrics were updated
            new_rate = db.patterns["feature_implementation"]["success_rate"]
            new_parallel = db.patterns["feature_implementation"]["avg_parallelization"]

            assert new_rate != initial_rate
            assert new_parallel != initial_parallel

    def test_save_and_load_patterns(self):
        """Test saving and loading patterns from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            db = PatternDatabase(storage_path=db_path)

            # Modify patterns
            db.patterns["test_pattern"] = {
                "triggers": ["test"],
                "subtasks": ["setup", "run", "teardown"],
                "avg_parallelization": 0.5,
                "success_rate": 0.9,
            }

            # Save patterns
            db.save_patterns()
            assert db_path.exists()

            # Load patterns in new instance
            db2 = PatternDatabase(storage_path=db_path)
            assert "test_pattern" in db2.patterns
            assert db2.patterns["test_pattern"]["triggers"] == ["test"]


class TestTaskDecomposer:
    """Test TaskDecomposer functionality."""

    @pytest.fixture
    def decomposer(self):
        """Create a TaskDecomposer instance for testing."""
        return TaskDecomposer()

    def test_generate_subtask_id(self, decomposer):
        """Test subtask ID generation."""
        id1 = decomposer._generate_subtask_id("task1")
        id2 = decomposer._generate_subtask_id("task2")
        id3 = decomposer._generate_subtask_id("task1")

        # IDs should be unique
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

        # IDs should have expected format
        assert id1.startswith("subtask_")
        assert "_001" in id1

    @pytest.mark.asyncio
    async def test_decompose_task_with_pattern(self, decomposer):
        """Test decomposing a task that matches a pattern."""
        task = "implement user authentication system"
        result = await decomposer.decompose_task(task)

        assert isinstance(result, DecompositionResult)
        assert result.original_task == task
        assert len(result.subtasks) > 0
        assert result.decomposition_pattern == "feature_implementation"

        # Check subtasks match pattern
        subtask_names = [st.name.lower() for st in result.subtasks]
        assert any("design" in name for name in subtask_names)
        assert any("implement" in name for name in subtask_names)
        assert any("test" in name for name in subtask_names)

    @pytest.mark.asyncio
    async def test_decompose_task_without_pattern(self, decomposer):
        """Test decomposing a task with no matching pattern."""
        task = "analyze quarterly metrics and prepare report"
        result = await decomposer.decompose_task(task)

        assert isinstance(result, DecompositionResult)
        assert result.original_task == task
        assert len(result.subtasks) > 0
        assert result.decomposition_pattern is None

        # Should use default decomposition
        subtask_names = [st.name.lower() for st in result.subtasks]
        assert any("analysis" in name for name in subtask_names)
        assert any("implementation" in name for name in subtask_names)

    @pytest.mark.asyncio
    async def test_analyze_dependencies(self, decomposer):
        """Test dependency analysis between subtasks."""
        subtasks = [
            SubTask(id="sub_001", name="Design API", description="Design the API"),
            SubTask(
                id="sub_002", name="Implement API", description="Implement the API"
            ),
            SubTask(id="sub_003", name="Test API", description="Test the API"),
            SubTask(id="sub_004", name="Document API", description="Document the API"),
        ]

        dependencies = await decomposer.analyze_dependencies(subtasks)

        assert isinstance(dependencies, dict)
        # Test tasks should depend on implementation
        assert "sub_002" in dependencies["sub_003"]
        # Documentation should have no dependencies (can run in parallel)
        assert len(dependencies["sub_004"]) == 0

    @pytest.mark.asyncio
    async def test_estimate_parallelization(self, decomposer):
        """Test parallelization score estimation."""
        # Fully parallel tasks (no dependencies)
        parallel_tasks = [
            SubTask(
                id="p1",
                name="Task 1",
                description="",
                estimated_time=60,
                can_parallelize=True,
            ),
            SubTask(
                id="p2",
                name="Task 2",
                description="",
                estimated_time=60,
                can_parallelize=True,
            ),
            SubTask(
                id="p3",
                name="Task 3",
                description="",
                estimated_time=60,
                can_parallelize=True,
            ),
        ]
        parallel_deps: Dict[str, List[str]] = {"p1": [], "p2": [], "p3": []}

        parallel_score = await decomposer.estimate_parallelization(
            parallel_tasks, parallel_deps
        )
        assert parallel_score > 0.7  # Should be high for parallel tasks

        # Sequential tasks
        sequential_tasks = [
            SubTask(
                id="s1",
                name="Task 1",
                description="",
                estimated_time=60,
                can_parallelize=False,
            ),
            SubTask(
                id="s2",
                name="Task 2",
                description="",
                estimated_time=60,
                can_parallelize=False,
            ),
            SubTask(
                id="s3",
                name="Task 3",
                description="",
                estimated_time=60,
                can_parallelize=False,
            ),
        ]
        sequential_deps = {"s1": [], "s2": ["s1"], "s3": ["s2"]}

        sequential_score = await decomposer.estimate_parallelization(
            sequential_tasks, sequential_deps
        )
        assert sequential_score < 0.3  # Should be low for sequential tasks

        # Mixed dependencies
        mixed_tasks = [
            SubTask(id="m1", name="Task 1", description="", estimated_time=60),
            SubTask(id="m2", name="Task 2", description="", estimated_time=60),
            SubTask(id="m3", name="Task 3", description="", estimated_time=60),
            SubTask(id="m4", name="Task 4", description="", estimated_time=60),
        ]
        mixed_deps = {"m1": [], "m2": [], "m3": ["m1", "m2"], "m4": ["m3"]}

        mixed_score = await decomposer.estimate_parallelization(mixed_tasks, mixed_deps)
        assert 0.3 < mixed_score < 0.8  # Should be moderate for mixed

    @pytest.mark.asyncio
    async def test_find_critical_path(self, decomposer):
        """Test critical path calculation."""
        tasks = [
            SubTask(id="t1", name="Task 1", description="", estimated_time=30),
            SubTask(id="t2", name="Task 2", description="", estimated_time=60),
            SubTask(id="t3", name="Task 3", description="", estimated_time=45),
            SubTask(id="t4", name="Task 4", description="", estimated_time=30),
        ]

        # t1 -> t3 -> t4 (total: 105)
        # t2 -> t4 (total: 90)
        # Critical path should be t1 -> t3 -> t4 = 105
        deps = {"t1": [], "t2": [], "t3": ["t1"], "t4": ["t2", "t3"]}

        critical_length = await decomposer._find_critical_path_length(tasks, deps)
        assert critical_length == 105

    @pytest.mark.asyncio
    async def test_learn_pattern(self, decomposer):
        """Test learning new patterns from successful executions."""
        result = DecompositionResult(
            original_task="optimize database queries",
            subtasks=[
                SubTask(id="s1", name="Analyze queries", description=""),
                SubTask(id="s2", name="Optimize queries", description=""),
                SubTask(id="s3", name="Test performance", description=""),
            ],
            dependency_graph={"s1": [], "s2": ["s1"], "s3": ["s2"]},
            parallelization_score=0.3,
            estimated_total_time=180,
            decomposition_pattern=None,
        )

        success_metrics = {"success": True, "execution_time": 150}

        # Learn from this successful decomposition
        await decomposer.learn_pattern(result, success_metrics)

        # Check if a new pattern was learned
        # Note: The pattern name will be dynamic based on hash
        pattern_count = len(decomposer.patterns_db.patterns)
        assert (
            pattern_count >= 5
        )  # Should have default patterns plus potentially new ones

    @pytest.mark.asyncio
    async def test_find_similar_patterns(self, decomposer):
        """Test finding similar patterns for a task."""
        similar = await decomposer.find_similar_patterns(
            "implement new feature with tests"
        )

        assert isinstance(similar, list)
        assert len(similar) <= 3  # Should return top 3 at most
        if similar:
            assert "feature_implementation" in similar or "testing" in similar

    @pytest.mark.asyncio
    async def test_complex_task_decomposition(self, decomposer):
        """Test decomposing a complex, multi-faceted task."""
        complex_task = (
            "Implement a machine learning pipeline with data preprocessing, "
            "model training, evaluation, and deployment to production"
        )

        result = await decomposer.decompose_task(complex_task)

        assert len(result.subtasks) >= 4  # Should have multiple subtasks
        assert result.parallelization_score > 0  # Some parallelization possible
        assert result.estimated_total_time > 0

        # Check for reasonable dependencies
        assert len(result.dependency_graph) > 0

        # Verify subtasks have reasonable properties
        for subtask in result.subtasks:
            assert subtask.id
            assert subtask.name
            assert subtask.description
            assert subtask.complexity in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_edge_cases(self, decomposer):
        """Test edge cases and error handling."""
        # Empty task
        result = await decomposer.decompose_task("")
        assert result.subtasks  # Should still generate default subtasks

        # Very short task
        result = await decomposer.decompose_task("test")
        assert result.subtasks

        # Task with context
        context = {"priority": "high", "team_size": 3}
        result = await decomposer.decompose_task("build system", context)
        assert result.subtasks

    def test_time_calculation(self, decomposer):
        """Test total time calculation with parallelization."""
        tasks = [
            SubTask(id="t1", name="Task 1", description="", estimated_time=60),
            SubTask(id="t2", name="Task 2", description="", estimated_time=60),
        ]

        # Fully parallel (score = 1.0)
        parallel_deps: Dict[str, List[str]] = {"t1": [], "t2": []}
        time_parallel = decomposer._calculate_total_time(tasks, parallel_deps, 1.0)
        assert time_parallel < 120  # Should be less than sequential time

        # Fully sequential (score = 0.0)
        sequential_deps = {"t1": [], "t2": ["t1"]}
        time_sequential = decomposer._calculate_total_time(tasks, sequential_deps, 0.0)
        assert time_sequential == 120  # Should be sum of all tasks

        # Partial parallelization (score = 0.5)
        time_partial = decomposer._calculate_total_time(tasks, sequential_deps, 0.5)
        assert time_parallel < time_partial < time_sequential


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from task to decomposition."""
        # Create decomposer with custom pattern database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_patterns.json"
            patterns_db = PatternDatabase(storage_path=db_path)
            decomposer = TaskDecomposer(patterns_db=patterns_db)

            # Decompose multiple tasks
            tasks = [
                "implement REST API for user management",
                "fix memory leak in background worker",
                "refactor authentication module",
                "write unit tests for payment service",
            ]

            results = []
            for task in tasks:
                result = await decomposer.decompose_task(task)
                results.append(result)

                # Learn from each decomposition
                await decomposer.learn_pattern(result, {"success": True})

            # Verify results
            assert len(results) == 4
            assert all(isinstance(r, DecompositionResult) for r in results)

            # Check patterns were used
            assert results[0].decomposition_pattern == "feature_implementation"
            assert results[1].decomposition_pattern == "bug_fix"
            assert results[2].decomposition_pattern == "refactoring"
            assert results[3].decomposition_pattern == "testing"

            # Verify patterns were saved
            assert db_path.exists()
            saved_data = json.loads(db_path.read_text())
            assert "feature_implementation" in saved_data

    @pytest.mark.asyncio
    async def test_pattern_evolution(self):
        """Test how patterns evolve with learning."""
        decomposer = TaskDecomposer()

        # Initial decomposition
        task = "implement caching layer"
        result1 = await decomposer.decompose_task(task)
        initial_score = result1.parallelization_score

        # Simulate successful execution with high parallelization
        await decomposer.learn_pattern(result1, {"success": True})

        # Update pattern metrics
        if result1.decomposition_pattern:
            decomposer.patterns_db.update_pattern_metrics(
                result1.decomposition_pattern, success=True, parallelization_score=0.9
            )

        # Decompose similar task
        result2 = await decomposer.decompose_task("implement logging layer")

        # Pattern should be reused
        assert result2.decomposition_pattern == result1.decomposition_pattern

        # Check that pattern metrics were updated
        pattern = decomposer.patterns_db.patterns.get(result1.decomposition_pattern)
        if pattern:
            assert pattern["avg_parallelization"] != initial_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
