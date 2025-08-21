#!/usr/bin/env python3
"""Test the TaskDecomposer vertical slice."""

import json
import sys
from pathlib import Path

# Add the src directory to path for imports
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from orchestrator.run_agent import run_agent  # noqa: E402


def test_task_decomposer_basic() -> None:
    """Test that TaskDecomposer returns valid JSON."""
    result = run_agent("TaskDecomposer", "Build a simple web app")

    assert result["success"] is True, f"Decomposer failed: {result['stderr']}"
    assert result["returncode"] == 0, f"Non-zero return code: {result['returncode']}"

    # Parse JSON output
    try:
        tasks_data = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON output: {e}\nOutput: {result['stdout']}"
        raise AssertionError(msg)

    # Validate required fields
    assert "original_task" in tasks_data
    assert "tasks" in tasks_data
    assert "parallel_groups" in tasks_data


def test_task_decomposer_api_pattern() -> None:
    """Test that API tasks get appropriate decomposition."""
    result = run_agent("TaskDecomposer", "Build a REST API with authentication")

    assert result["success"] is True
    tasks_data = json.loads(result["stdout"])

    # Should have multiple tasks for API projects
    assert len(tasks_data["tasks"]) >= 3, "API projects should have multiple tasks"

    # Should include CodeWriter and TestWriter agents
    agent_types = [task["agent"] for task in tasks_data["tasks"]]
    assert "CodeWriter" in agent_types, "Should include CodeWriter agent"
    assert "TestWriter" in agent_types, "Should include TestWriter agent"


def test_task_decomposer_dependencies() -> None:
    """Test that dependencies are properly structured."""
    result = run_agent("TaskDecomposer", "Create a todo app")

    assert result["success"] is True
    tasks_data = json.loads(result["stdout"])

    # Validate task structure
    for task in tasks_data["tasks"]:
        assert "id" in task
        assert "agent" in task
        assert "task" in task
        assert "dependencies" in task
        assert isinstance(task["dependencies"], list)

        # Task descriptions should be specific
        assert len(task["task"]) > 10, f"Task too vague: {task['task']}"

    # Validate parallel groups reference actual task IDs
    all_task_ids = {task["id"] for task in tasks_data["tasks"]}
    for group in tasks_data["parallel_groups"]:
        for task_id in group:
            assert task_id in all_task_ids, f"Parallel group references unknown task: {task_id}"


def test_orchestrator_task_decomposer_integration() -> None:
    """Test the full orchestrator -> TaskDecomposer workflow."""
    # This tests the integration that architect recommended
    result = run_agent("TaskDecomposer", "Build a mobile app")

    assert result["success"] is True, "Integration should work"

    # Should get structured output for downstream processing
    tasks_data = json.loads(result["stdout"])
    assert tasks_data["original_task"] == "Build a mobile app"
    assert len(tasks_data["tasks"]) > 0

    # This validates the "second functional agent" goal


def main() -> None:
    """Run all tests."""
    try:
        test_task_decomposer_basic()
        test_task_decomposer_api_pattern()
        test_task_decomposer_dependencies()
        test_orchestrator_task_decomposer_integration()

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
