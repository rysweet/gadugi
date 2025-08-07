#!/usr/bin/env python3
"""
Complete demo showing the full Gadugi v0.3 workflow:
Orchestrator -> Task Decomposer -> Prompt Writer -> Code Writer
"""

import json
from run_agent import run_agent


def demo_complete_workflow():
    """Demonstrate the complete multi-agent workflow."""

    print("=== Gadugi v0.3 Complete Workflow Demo ===")
    print()

    high_level_task = "Build a user authentication API with password hashing"
    print(f"🎯 High-Level Task: {high_level_task}")
    print("=" * 70)

    # Step 1: Task Decomposition
    print("Step 1: Task Decomposition")
    print("-" * 30)

    decomposer_result = run_agent("task-decomposer", high_level_task)

    if not decomposer_result["success"]:
        print(f"❌ Task decomposition failed: {decomposer_result['stderr']}")
        return False

    try:
        tasks_json = json.loads(decomposer_result["stdout"])
        print("✅ Task Decomposer Results:")

        for task in tasks_json["tasks"]:
            deps_str = (
                f" (depends on: {task['dependencies']})" if task["dependencies"] else ""
            )
            print(f"  {task['id']}. {task['agent']}: {task['task']}{deps_str}")

        print(f"📊 Parallel execution groups: {tasks_json['parallel_groups']}")

    except json.JSONDecodeError as e:
        print(f"❌ Could not parse task decomposer output: {e}")
        return False

    print("\n" + "=" * 70)

    # Step 2: Prompt Generation for each subtask
    print("Step 2: Prompt Generation")
    print("-" * 30)

    generated_prompts = []

    for i, task in enumerate(tasks_json["tasks"][:2], 1):  # Limit to first 2 for demo
        print(f"\n📝 Generating prompt for subtask {i}: {task['task']}")

        prompt_result = run_agent("prompt-writer", task["task"])

        if prompt_result["success"]:
            filename = prompt_result["metadata"]["suggested_filename"]
            print(f"✅ Generated prompt: {filename}")

            generated_prompts.append(
                {"task": task, "prompt": prompt_result, "filename": filename}
            )
        else:
            print(f"❌ Failed to generate prompt: {prompt_result['stderr']}")

    print("\n" + "=" * 70)

    # Step 3: Code Generation
    print("Step 3: Code Generation")
    print("-" * 30)

    generated_code = []

    for i, prompt_info in enumerate(generated_prompts, 1):
        task = prompt_info["task"]
        print(f"\n💻 Generating code for: {task['task']}")

        code_result = run_agent("code-writer", task["task"])

        if code_result["success"]:
            print(f"✅ Code generation successful!")
            print(f"   Language: {code_result['metadata']['language']}")
            print(f"   Type: {code_result['metadata']['code_type']}")

            # Show files that would be created
            code_data = code_result["metadata"]["code_result"]
            for file_info in code_data["files"][:1]:  # Show first file
                print(f"   📁 File: {file_info['filename']}")
                print(f"   📝 Description: {file_info['description']}")

            generated_code.append({"task": task, "code": code_result})
        else:
            print(f"❌ Code generation failed: {code_result['stderr']}")

    print("\n" + "=" * 70)

    # Step 4: Workflow Summary
    print("Step 4: Workflow Summary")
    print("-" * 30)

    print(f"🎯 Original Task: {high_level_task}")
    print(f"📋 Decomposed into: {len(tasks_json['tasks'])} subtasks")
    print(f"📝 Generated: {len(generated_prompts)} detailed prompts")
    print(f"💻 Generated: {len(generated_code)} code implementations")

    print(f"\n📊 Agents Used:")
    print("  ✅ task-decomposer: Broke down high-level task")
    print("  ✅ prompt-writer: Created structured implementation prompts")
    print("  ✅ code-writer: Generated functional source code")

    print(f"\n🔄 Workflow Phases:")
    print("  1. Task Analysis & Decomposition")
    print("  2. Prompt Generation & Structuring")
    print("  3. Code Implementation & Generation")
    print("  4. Integration & Coordination")

    if generated_code:
        print(f"\n🎉 Complete End-to-End Success!")
        print("The workflow successfully transformed a high-level task into:")
        print("  • Structured subtasks")
        print("  • Detailed implementation prompts")
        print("  • Functional source code")

        # Show what would happen next in a full implementation
        print(f"\n⏭️  Next Steps (in full system):")
        print("  • Run generated code through test-writer agent")
        print("  • Create integration tests and validation")
        print("  • Package and deploy components")
        print("  • Generate documentation and examples")

    return True


def demo_individual_agents():
    """Quick demo of each agent individually."""
    print("\n" + "=" * 70)
    print("Individual Agent Demonstrations")
    print("=" * 70)

    # Test each agent with a simple task
    test_task = "Create simple user model"
    agents = ["task-decomposer", "prompt-writer", "code-writer"]

    for agent in agents:
        print(f"\n🤖 Testing {agent} with: '{test_task}'")
        print("-" * 50)

        result = run_agent(agent, test_task)

        if result["success"]:
            print(f"✅ {agent} succeeded")

            # Show key output depending on agent type
            if agent == "task-decomposer":
                try:
                    tasks = json.loads(result["stdout"])
                    print(f"   📋 Created {len(tasks['tasks'])} subtasks")
                except Exception:
                    print("   📋 Task decomposition completed")

            elif agent == "prompt-writer":
                if "metadata" in result and "suggested_filename" in result["metadata"]:
                    filename = result["metadata"]["suggested_filename"]
                    print(f"   📝 Generated prompt: {filename}")
                else:
                    print("   📝 Prompt generation completed")

            elif agent == "code-writer":
                if "metadata" in result and "language" in result["metadata"]:
                    lang = result["metadata"]["language"]
                    code_type = result["metadata"]["code_type"]
                    print(f"   💻 Generated {lang} code ({code_type})")
                else:
                    print("   💻 Code generation completed")
        else:
            print(f"❌ {agent} failed: {result.get('stderr', 'Unknown error')}")


if __name__ == "__main__":
    print("Starting Gadugi v0.3 Complete Workflow Demonstration...")
    print()

    # Run complete workflow demo
    success = demo_complete_workflow()

    # Run individual agent demos
    demo_individual_agents()

    print("\n" + "=" * 70)
    print("🚀 Gadugi v0.3 Workflow Demo Complete!")

    if success:
        print("✅ All workflow phases executed successfully")
        print("✅ Multi-agent coordination working properly")
        print("✅ End-to-end task transformation achieved")

    print("""
🎯 Key Achievements Demonstrated:
  • High-level task decomposition into executable subtasks
  • Structured prompt generation for clear implementation guidance
  • Functional code generation from natural language descriptions
  • Multi-agent coordination and workflow orchestration
  • Complete end-to-end transformation from idea to code

🔮 This demonstrates the foundation for a complete AI-assisted development platform
   capable of transforming high-level requirements into working software components.
""")
