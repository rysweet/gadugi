#!/usr/bin/env python3
"""
Demonstration of the Gadugi v0.3 multi-agent workflow.
Shows orchestrator -> task-decomposer -> multiple agents pattern.
"""

import json
import sys
from run_agent import run_agent


def demo_multi_agent_workflow(high_level_task: str):
    """
    Demonstrate the full workflow:
    1. High-level task comes in
    2. Orchestrator uses task-decomposer to break it down  
    3. Orchestrator could then run each subtask (future enhancement)
    """
    
    print(f"=== Gadugi v0.3 Multi-Agent Workflow Demo ===")
    print(f"High-level task: {high_level_task}")
    print("=" * 60)
    
    # Step 1: Use orchestrator to run task-decomposer
    print("Step 1: Running task-decomposer via orchestrator...")
    decomposer_result = run_agent("task-decomposer", high_level_task)
    
    if not decomposer_result["success"]:
        print(f"❌ Task decomposition failed: {decomposer_result['stderr']}")
        return False
    
    # Parse the JSON response
    try:
        tasks_json = json.loads(decomposer_result["stdout"])
        print("✅ Task decomposition successful!")
        print(f"Original task: {tasks_json['original_task']}")
        print(f"Broken into {len(tasks_json['tasks'])} subtasks:")
        
        for task in tasks_json["tasks"]:
            deps_str = f" (depends on: {task['dependencies']})" if task['dependencies'] else ""
            print(f"  {task['id']}. {task['agent']}: {task['task']}{deps_str}")
            
        print(f"Parallel execution groups: {tasks_json['parallel_groups']}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Could not parse task decomposer output as JSON: {e}")
        print(f"Raw output: {decomposer_result['stdout']}")
        return False
    
    print("\n" + "=" * 60)
    print("Step 2: Could now execute subtasks with orchestrator...")
    print("(This would be the next vertical slice to implement)")
    
    # Demonstrate what could happen next
    print("\nPotential execution plan:")
    for group_num, group in enumerate(tasks_json['parallel_groups'], 1):
        if len(group) == 1:
            task_id = group[0]
            task = next(t for t in tasks_json['tasks'] if t['id'] == task_id)
            print(f"  Phase {group_num}: Run {task['agent']} - {task['task']}")
        else:
            print(f"  Phase {group_num}: Run in parallel:")
            for task_id in group:
                task = next(t for t in tasks_json['tasks'] if t['id'] == task_id)
                print(f"    - {task['agent']}: {task['task']}")
    
    print("\n✅ Multi-agent workflow demonstration complete!")
    return True


def main():
    """Command line interface for the demo."""
    if len(sys.argv) < 2:
        print("Usage: python demo_workflow.py <high_level_task>")
        print("\nExample:")
        print('  python demo_workflow.py "Build a todo list app"')
        print('  python demo_workflow.py "Create a REST API with authentication"')
        sys.exit(1)
    
    high_level_task = " ".join(sys.argv[1:])
    demo_multi_agent_workflow(high_level_task)


if __name__ == "__main__":
    main()