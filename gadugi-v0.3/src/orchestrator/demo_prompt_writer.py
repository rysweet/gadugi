#!/usr/bin/env python3
"""Demo showing the prompt-writer integration with orchestrator."""

import json

from run_agent import run_agent


def demo_prompt_writer() -> bool:
    """Demonstrate the prompt-writer agent capabilities."""
    # Test 1: Generate a prompt for a simple task

    result = run_agent("prompt-writer", "Add user authentication")

    if result["success"]:
        pass
    else:
        pass

    # Test 2: Show integration with task decomposition

    high_level_task = "Build a todo list application with user authentication"

    # First, decompose the task
    decomposer_result = run_agent("task-decomposer", high_level_task)

    if decomposer_result["success"]:
        try:
            tasks_json = json.loads(decomposer_result["stdout"])

            for task in tasks_json["tasks"]:
                pass

            # Now generate prompts for each subtask

            for _i, task in enumerate(tasks_json["tasks"][:2], 1):  # Limit to 2 for demo
                prompt_result = run_agent("prompt-writer", task["task"])

                if prompt_result["success"]:
                    prompt_result["metadata"]["suggested_filename"]

                    # Show a snippet of the generated prompt
                    lines = prompt_result["stdout"].split("\n")
                    next(
                        (line for line in lines if line.startswith("# ")),
                        "No title",
                    )
                    overview_start = None
                    for j, line in enumerate(lines):
                        if line.startswith("## Overview"):
                            overview_start = j + 1
                            break

                    if overview_start and overview_start < len(lines):
                        (lines[overview_start] if overview_start < len(lines) else "")

                else:
                    pass

        except json.JSONDecodeError:
            pass
    else:
        pass

    return True


if __name__ == "__main__":
    demo_prompt_writer()
