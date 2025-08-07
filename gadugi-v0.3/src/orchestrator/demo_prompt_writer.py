#!/usr/bin/env python3
"""
Demo showing the prompt-writer integration with orchestrator.
"""

import json
from demo_workflow import demo_multi_agent_workflow
from run_agent import run_agent


def demo_prompt_writer():
    """Demonstrate the prompt-writer agent capabilities."""

    print("=== Gadugi v0.3 Prompt Writer Agent Demo ===")
    print()

    # Test 1: Generate a prompt for a simple task
    print("Test 1: Generate prompt for 'Add user authentication'")
    print("-" * 50)

    result = run_agent("prompt-writer", "Add user authentication")

    if result["success"]:
        print("✅ Prompt generation successful!")
        print(f"Suggested filename: {result['metadata']['suggested_filename']}")
        print("\nGenerated prompt preview (first 500 chars):")
        print(
            result["stdout"][:500] + "..."
            if len(result["stdout"]) > 500
            else result["stdout"]
        )
    else:
        print(f"❌ Failed: {result['stderr']}")

    print("\n" + "=" * 70)

    # Test 2: Show integration with task decomposition
    print("Test 2: Multi-agent workflow with prompt generation")
    print("-" * 50)

    high_level_task = "Build a todo list application with user authentication"
    print(f"High-level task: {high_level_task}")
    print()

    # First, decompose the task
    decomposer_result = run_agent("task-decomposer", high_level_task)

    if decomposer_result["success"]:
        try:
            tasks_json = json.loads(decomposer_result["stdout"])
            print("📋 Task Decomposer Results:")

            for task in tasks_json["tasks"]:
                print(f"  {task['id']}. {task['agent']}: {task['task']}")

            print(f"\n🧾 Parallel groups: {tasks_json['parallel_groups']}")

            # Now generate prompts for each subtask
            print("\n📝 Generating prompts for each subtask:")
            print("-" * 40)

            for i, task in enumerate(tasks_json["tasks"][:2], 1):  # Limit to 2 for demo
                print(f"\nSubtask {i}: {task['task']}")
                prompt_result = run_agent("prompt-writer", task["task"])

                if prompt_result["success"]:
                    filename = prompt_result["metadata"]["suggested_filename"]
                    print(f"✅ Generated: {filename}")

                    # Show a snippet of the generated prompt
                    lines = prompt_result["stdout"].split("\n")
                    title_line = next(
                        (line for line in lines if line.startswith("# ")), "No title"
                    )
                    overview_start = None
                    for j, line in enumerate(lines):
                        if line.startswith("## Overview"):
                            overview_start = j + 1
                            break

                    if overview_start and overview_start < len(lines):
                        overview_line = (
                            lines[overview_start] if overview_start < len(lines) else ""
                        )
                        print(f"   Title: {title_line}")
                        print(f"   Overview: {overview_line}")

                else:
                    print(f"❌ Failed to generate prompt: {prompt_result['stderr']}")

        except json.JSONDecodeError:
            print("❌ Could not parse task decomposer output")
    else:
        print(f"❌ Task decomposition failed: {decomposer_result['stderr']}")

    print("\n" + "=" * 70)
    print("🎯 Demo complete! The prompt-writer agent can:")
    print("✅ Generate structured prompts from task descriptions")
    print("✅ Integrate with the orchestrator and task-decomposer")
    print("✅ Create prompts with proper requirements and workflow steps")
    print("✅ Support different task types (features, bugs, enhancements)")
    print("✅ Provide suggested filenames for generated prompts")

    return True


if __name__ == "__main__":
    demo_prompt_writer()
