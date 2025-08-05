#!/usr/bin/env python3
"""
Main Orchestrator Coordinator

This script coordinates the orchestrator-agent workflow when invoked via Claude.
It ties together the task analyzer, worktree manager, and execution engine components.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add the current directory to path so we can import components
sys.path.insert(0, str(Path(__file__).parent))

from components.task_analyzer import TaskAnalyzer
from components.worktree_manager import WorktreeManager
from components.execution_engine import ExecutionEngine
from components.prompt_generator import PromptGenerator, PromptContext


def main():
    """Main orchestrator workflow"""
    print("🎯 OrchestratorAgent Starting...")

    # Parse input from Claude
    if len(sys.argv) < 2:
        print("❌ Error: No prompt files provided")
        print("Usage: orchestrator.py <prompt_file1> <prompt_file2> ...")
        return 1

    prompt_files = sys.argv[1:]
    print(f"📋 Analyzing {len(prompt_files)} prompt files...")

    # Phase 1: Task Analysis
    analyzer = TaskAnalyzer()
    task_data = []

    for prompt_file in prompt_files:
        if not os.path.exists(prompt_file):
            print(f"⚠️  Warning: Prompt file not found: {prompt_file}")
            continue

        try:
            # Analyze the prompt file
            analysis = analyzer.analyze_prompt(prompt_file)

            # Generate unique task ID
            from datetime import datetime
            task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(prompt_file) % 10000:04x}"

            task_info = {
                "task_id": task_id,
                "prompt_file": prompt_file,
                "description": analysis.get("description", Path(prompt_file).stem),
                "dependencies": analysis.get("file_dependencies", []),
                "complexity": analysis.get("complexity", "medium"),
                "can_parallelize": analysis.get("can_parallelize", True)
            }

            task_data.append(task_info)
            print(f"✅ Analyzed: {task_info['description']} (ID: {task_id})")

        except Exception as e:
            print(f"❌ Failed to analyze {prompt_file}: {e}")

    if not task_data:
        print("❌ No valid tasks to execute")
        return 1

    # Phase 2: Environment Setup (Worktrees)
    print(f"\n🌳 Setting up {len(task_data)} worktrees...")
    worktree_manager = WorktreeManager()

    for task in task_data:
        try:
            # Create worktree for the task
            worktree_info = worktree_manager.create_worktree(
                task["task_id"],
                f"feature/{task['task_id']}-{task['description'][:30].replace(' ', '-').lower()}"
            )

            if worktree_info:
                task["worktree_path"] = worktree_info.worktree_path
                print(f"✅ Worktree created: {task['worktree_path']}")
            else:
                print(f"❌ Failed to create worktree for {task['task_id']}")
                task["can_parallelize"] = False

        except Exception as e:
            print(f"❌ Worktree creation failed for {task['task_id']}: {e}")
            task["can_parallelize"] = False

    # Filter out tasks that can be parallelized
    parallel_tasks = [t for t in task_data if t.get("can_parallelize", True) and "worktree_path" in t]
    sequential_tasks = [t for t in task_data if not t.get("can_parallelize", True) or "worktree_path" not in t]

    print(f"\n📊 Task Distribution:")
    print(f"   - Parallel: {len(parallel_tasks)} tasks")
    print(f"   - Sequential: {len(sequential_tasks)} tasks")

    # Phase 3: Parallel Execution
    if parallel_tasks:
        print(f"\n🚀 Executing {len(parallel_tasks)} tasks in parallel...")

        # Create execution engine
        execution_engine = ExecutionEngine(
            max_concurrent=min(len(parallel_tasks), 4),  # Limit to 4 concurrent tasks
            default_timeout=3600  # 1 hour timeout
        )

        try:
            # Execute tasks
            results = execution_engine.execute_tasks_parallel(
                parallel_tasks,
                worktree_manager,
                progress_callback=lambda completed, total, result: print(
                    f"   [{completed}/{total}] {result.task_id}: {result.status}"
                )
            )

            # Save results
            output_file = f"orchestration-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            execution_engine.save_results(output_file)
            print(f"\n✅ Results saved to: {output_file}")

            # Summary
            successful = sum(1 for r in results.values() if r.status == "completed")
            failed = sum(1 for r in results.values() if r.status == "failed")

            print(f"\n📈 Execution Summary:")
            print(f"   - Successful: {successful}")
            print(f"   - Failed: {failed}")

        except Exception as e:
            print(f"❌ Parallel execution failed: {e}")
            return 1

    # Phase 4: Sequential Execution (if needed)
    if sequential_tasks:
        print(f"\n⏭️  Executing {len(sequential_tasks)} tasks sequentially...")
        for task in sequential_tasks:
            print(f"   - {task['task_id']}: {task['description']}")
            # TODO: Implement sequential execution

    # Phase 5: Cleanup
    print("\n🧹 Cleaning up worktrees...")
    for task in task_data:
        if "worktree_path" in task:
            try:
                worktree_manager.remove_worktree(task["task_id"])
                print(f"   - Removed: {task['task_id']}")
            except Exception as e:
                print(f"   - Failed to remove {task['task_id']}: {e}")

    print("\n✅ Orchestration complete!")
    return 0


if __name__ == "__main__":
    exit(main())
