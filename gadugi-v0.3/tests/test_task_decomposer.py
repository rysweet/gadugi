#!/usr/bin/env python3
"""
Test the task-decomposer vertical slice.
"""

import json
import sys
from pathlib import Path

# Add the src directory to path for imports
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from orchestrator.run_agent import run_agent


def test_task_decomposer_basic():
    """Test that task-decomposer returns valid JSON."""
    result = run_agent("task-decomposer", "Build a simple web app")

    assert result["success"] is True, f"Decomposer failed: {result['stderr']}"
    assert result["returncode"] == 0, f"Non-zero return code: {result['returncode']}"

    # Parse JSON output
    try:
        tasks_data = json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        assert False, f"Invalid JSON output: {e}\nOutput: {result['stdout']}"

    # Validate required fields
    assert "original_task" in tasks_data
    assert "tasks" in tasks_data
    assert "parallel_groups" in tasks_data

    print("✓ Task decomposer basic test passed")


def test_task_decomposer_api_pattern():
    """Test that API tasks get appropriate decomposition."""
    result = run_agent("task-decomposer", "Build a REST API with authentication")

    assert result["success"] is True
    tasks_data = json.loads(result["stdout"])

    # Should have multiple tasks for API projects
    assert len(tasks_data["tasks"]) >= 3, "API projects should have multiple tasks"

    # Should include code-writer and test-writer agents
    agent_types = [task["agent"] for task in tasks_data["tasks"]]
    assert "code-writer" in agent_types, "Should include code-writer agent"
    assert "test-writer" in agent_types, "Should include test-writer agent"

    print("✓ Task decomposer API pattern test passed")


def test_task_decomposer_dependencies():
    """Test that dependencies are properly structured."""
    result = run_agent("task-decomposer", "Create a todo app")

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
    all_task_ids = set(task["id"] for task in tasks_data["tasks"])
    for group in tasks_data["parallel_groups"]:
        for task_id in group:
            assert task_id in all_task_ids, (
                f"Parallel group references unknown task: {task_id}"
            )

    print("✓ Task decomposer dependencies test passed")


def test_orchestrator_task_decomposer_integration():
    """Test the full orchestrator -> task-decomposer workflow."""

    # This tests the integration that architect recommended
    result = run_agent("task-decomposer", "Build a mobile app")

    assert result["success"] is True, "Integration should work"

    # Should get structured output for downstream processing
    tasks_data = json.loads(result["stdout"])
    assert tasks_data["original_task"] == "Build a mobile app"
    assert len(tasks_data["tasks"]) > 0

    # This validates the "second functional agent" goal
    print("✓ Orchestrator-task-decomposer integration test passed")


def main():
    """Run all tests."""
    print("Testing Gadugi v0.3 task-decomposer...")
    print("=" * 50)

    try:
        test_task_decomposer_basic()
        test_task_decomposer_api_pattern()
        test_task_decomposer_dependencies()
        test_orchestrator_task_decomposer_integration()

        print("=" * 50)
        print("✅ All task-decomposer tests passed!")
        print("\nThis validates the second vertical slice:")
        print("- Orchestrator can run multiple agent types")
        print("- Agents can exchange structured data")
        print("- Multi-agent workflows are possible")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
