#!/usr/bin/env python3
"""Complete demo showing the full Gadugi v0.3 workflow:
Orchestrator -> Task Decomposer -> Prompt Writer -> Code Writer.
"""

import contextlib
import json

from run_agent import run_agent


def demo_complete_workflow() -> bool:
    """Demonstrate the complete multi-agent workflow."""
    high_level_task = "Build a user authentication API with password hashing"

    # Step 1: Task Decomposition

    decomposer_result = run_agent("task-decomposer", high_level_task)

    if not decomposer_result["success"]:
        return False

    try:
        tasks_json = json.loads(decomposer_result["stdout"])

        for task in tasks_json["tasks"]:
            (f" (depends on: {task['dependencies']})" if task["dependencies"] else "")

    except json.JSONDecodeError:
        return False

    # Step 2: Prompt Generation for each subtask

    generated_prompts = []

    for _i, task in enumerate(tasks_json["tasks"][:2], 1):  # Limit to first 2 for demo
        prompt_result = run_agent("prompt-writer", task["task"])

        if prompt_result["success"]:
            filename = prompt_result["metadata"]["suggested_filename"]

            generated_prompts.append(
                {"task": task, "prompt": prompt_result, "filename": filename},
            )
        else:
            pass

    # Step 3: Code Generation

    generated_code = []

    for _i, prompt_info in enumerate(generated_prompts, 1):
        task = prompt_info["task"]

        code_result = run_agent("code-writer", task["task"])

        if code_result["success"]:
            # Show files that would be created
            code_data = code_result["metadata"]["code_result"]
            for _file_info in code_data["files"][:1]:  # Show first file
                pass

            generated_code.append({"task": task, "code": code_result})
        else:
            pass

    # Step 4: Workflow Summary

    if generated_code:
        # Show what would happen next in a full implementation
        pass

    return True


def demo_individual_agents() -> None:
    """Quick demo of each agent individually."""
    # Test each agent with a simple task
    test_task = "Create simple user model"
    agents = ["task-decomposer", "prompt-writer", "code-writer"]

    for agent in agents:
        result = run_agent(agent, test_task)

        if result["success"]:
            # Show key output depending on agent type
            if agent == "task-decomposer":
                with contextlib.suppress(Exception):
                    json.loads(result["stdout"])

            elif agent == "prompt-writer":
                if "metadata" in result and "suggested_filename" in result["metadata"]:
                    result["metadata"]["suggested_filename"]
                else:
                    pass

            elif agent == "code-writer":
                if "metadata" in result and "language" in result["metadata"]:
                    result["metadata"]["language"]
                    result["metadata"]["code_type"]
                else:
                    pass
        else:
            pass


if __name__ == "__main__":
    # Run complete workflow demo
    success = demo_complete_workflow()

    # Run individual agent demos
    demo_individual_agents()

    if success:
        pass
