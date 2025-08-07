#!/usr/bin/env python3
"""Simple task decomposer for testing orchestrator workflow.
This is a minimal implementation to validate the vertical slice.
"""

import sys


def decompose_task(task_description: str) -> dict:
    """Simple task decomposition logic.
    For the minimal vertical slice, we'll create some basic patterns.
    """
    # Simple pattern matching for common task types
    task_lower = task_description.lower()

    if "api" in task_lower or "rest" in task_lower or "backend" in task_lower:
        return {
            "original_task": task_description,
            "tasks": [
                {
                    "id": "1",
                    "agent": "code-writer",
                    "task": "Set up project structure and dependencies",
                    "dependencies": [],
                },
                {
                    "id": "2",
                    "agent": "code-writer",
                    "task": "Create data models",
                    "dependencies": ["1"],
                },
                {
                    "id": "3",
                    "agent": "code-writer",
                    "task": "Implement API endpoints",
                    "dependencies": ["2"],
                },
                {
                    "id": "4",
                    "agent": "test-writer",
                    "task": "Write API tests",
                    "dependencies": ["3"],
                },
            ],
            "parallel_groups": [["1"], ["2"], ["3"], ["4"]],
        }

    if "todo" in task_lower or "app" in task_lower:
        return {
            "original_task": task_description,
            "tasks": [
                {
                    "id": "1",
                    "agent": "code-writer",
                    "task": "Create basic UI layout",
                    "dependencies": [],
                },
                {
                    "id": "2",
                    "agent": "code-writer",
                    "task": "Implement add/remove todo functionality",
                    "dependencies": ["1"],
                },
                {
                    "id": "3",
                    "agent": "test-writer",
                    "task": "Write UI tests",
                    "dependencies": ["2"],
                },
            ],
            "parallel_groups": [["1"], ["2"], ["3"]],
        }

    # Default generic decomposition
    return {
        "original_task": task_description,
        "tasks": [
            {
                "id": "1",
                "agent": "code-writer",
                "task": f"Analyze requirements for: {task_description}",
                "dependencies": [],
            },
            {
                "id": "2",
                "agent": "code-writer",
                "task": f"Implement solution for: {task_description}",
                "dependencies": ["1"],
            },
            {
                "id": "3",
                "agent": "test-writer",
                "task": f"Test solution for: {task_description}",
                "dependencies": ["2"],
            },
        ],
        "parallel_groups": [["1"], ["2"], ["3"]],
    }


def main() -> None:
    """Command line interface for testing."""
    if len(sys.argv) < 2:
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    decompose_task(task)

    # Output JSON only (for orchestrator integration)


if __name__ == "__main__":
    main()
