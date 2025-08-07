#!/usr/bin/env python3
"""Demonstration of the Gadugi v0.3 multi-agent workflow.
Shows orchestrator -> task-decomposer -> multiple agents pattern.
"""

import json
import sys

from run_agent import run_agent


def demo_multi_agent_workflow(high_level_task: str) -> bool:
    """Demonstrate the full workflow:
    1. High-level task comes in
    2. Orchestrator uses task-decomposer to break it down
    3. Orchestrator could then run each subtask (future enhancement).
    """
    # Step 1: Use orchestrator to run task-decomposer
    decomposer_result = run_agent("task-decomposer", high_level_task)

    if not decomposer_result["success"]:
        return False

    # Parse the JSON response
    try:
        tasks_json = json.loads(decomposer_result["stdout"])

        for task in tasks_json["tasks"]:
            (f" (depends on: {task['dependencies']})" if task["dependencies"] else "")

    except json.JSONDecodeError:
        return False

    # Demonstrate what could happen next
    for _group_num, group in enumerate(tasks_json["parallel_groups"], 1):
        if len(group) == 1:
            task_id = group[0]
            task = next(t for t in tasks_json["tasks"] if t["id"] == task_id)
        else:
            for task_id in group:
                task = next(t for t in tasks_json["tasks"] if t["id"] == task_id)

    return True


def main() -> None:
    """Command line interface for the demo."""
    if len(sys.argv) < 2:
        sys.exit(1)

    high_level_task = " ".join(sys.argv[1:])
    demo_multi_agent_workflow(high_level_task)


if __name__ == "__main__":
    main()
