#!/usr/bin/env python3
"""
Simple Orchestrator - Real Subprocess Execution for Parallel Workflows

This implements the actual subprocess spawning approach that successfully created PRs #278-282.
"""
import os
import subprocess
import sys
import time
from pathlib import Path
import threading
import queue


class SimpleOrchestrator:
    def __init__(self):
        self.active_processes = {}
        self.completed_tasks = []

    def create_worktree(self, task_name):
        """Create isolated worktree for task"""
        worktree_path = f".worktrees/{task_name}"
        branch_name = f"feature/{task_name}"

        # Clean up existing worktree if it exists
        subprocess.run(['git', 'worktree', 'remove', '--force', worktree_path],
                      capture_output=True)

        # Create new worktree
        result = subprocess.run([
            'git', 'worktree', 'add', worktree_path,
            '-b', branch_name, 'main'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Created worktree: {worktree_path}")
            return worktree_path
        else:
            print(f"❌ Failed to create worktree: {result.stderr}")
            return None

    def spawn_workflow_manager(self, task_name, prompt_file):
        """Spawn real WorkflowManager subprocess with proper delegation"""
        worktree_path = self.create_worktree(task_name)
        if not worktree_path:
            return None

        # Read prompt content
        prompt_content = Path(prompt_file).read_text()

        # Create task context file in worktree
        task_file = Path(worktree_path) / ".task" / "context.md"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(f"""# Task: {task_name}

{prompt_content}

## Orchestrator Context
- Task ID: {task_name}
- Worktree: {worktree_path}
- Spawned by: SimpleOrchestrator
- Workflow Manager Delegation: MANDATORY
- All 11 phases must be executed

Execute the full WorkflowManager workflow for this task.
""")

        print(f"🚀 Spawning WorkflowManager subprocess for: {task_name}")

        # Spawn WorkflowManager with increased turn limit
        process = subprocess.Popen([
            'claude', '-p', '/agent:workflow-manager',
            '--dangerously-skip-permissions',
            '--max-turns', '100',  # Increased for complex workflows
            '--verbose'
        ],
        cwd=worktree_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

        # Send initial prompt to WorkflowManager
        initial_prompt = f"""Execute complete WorkflowManager workflow for task: {task_name}

Task Context: {task_file.read_text()}

CRITICAL: Execute all 11 phases of the WorkflowManager workflow:
1. Initial Setup
2. Issue Creation
3. Branch Management
4. Research and Planning
5. Implementation
6. Testing
7. Documentation
8. Pull Request
9. Review
10. Review Response
11. Settings Update

Begin workflow execution now.
"""

        # Start input thread to send prompt
        def send_input():
            try:
                process.stdin.write(initial_prompt)
                process.stdin.close()
            except:
                pass

        input_thread = threading.Thread(target=send_input)
        input_thread.start()

        self.active_processes[task_name] = {
            'process': process,
            'worktree': worktree_path,
            'started_at': time.time()
        }

        print(f"✅ Spawned process PID {process.pid} for {task_name}")
        return process

    def monitor_processes(self):
        """Monitor all active processes"""
        print(f"\n🔄 Monitoring {len(self.active_processes)} parallel processes...")

        completed = []

        while self.active_processes:
            for task_name, info in list(self.active_processes.items()):
                process = info['process']

                # Check if process completed
                returncode = process.poll()
                if returncode is not None:
                    runtime = time.time() - info['started_at']

                    if returncode == 0:
                        print(f"✅ Task {task_name} completed successfully in {runtime:.1f}s")
                        self.completed_tasks.append(task_name)
                    else:
                        print(f"❌ Task {task_name} failed with code {returncode} after {runtime:.1f}s")

                    # Get final output
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                        if stdout:
                            print(f"📋 {task_name} output: {stdout[-200:]}")  # Last 200 chars
                    except subprocess.TimeoutExpired:
                        print(f"⚠️ Timeout getting output from {task_name}")

                    completed.append(task_name)
                    del self.active_processes[task_name]

            if self is not None and self.active_processes:
                time.sleep(10)  # Check every 10 seconds

        return self.completed_tasks

    def execute_tasks(self, task_prompts):
        """Execute multiple tasks in parallel"""
        print(f"🎯 Starting parallel execution of {len(task_prompts)} tasks")

        # Spawn all processes
        for task_name, prompt_file in task_prompts.items():
            self.spawn_workflow_manager(task_name, prompt_file)
            time.sleep(2)  # Small delay between spawns

        # Monitor until completion
        completed = self.monitor_processes()

        print(f"\n🎉 Parallel execution completed!")
        print(f"✅ Successful tasks: {len(completed)}")
        print(f"📋 Tasks: {completed}")

        return completed


def main():
    """Main orchestrator entry point"""
    if len(sys.argv) < 2:
        print("Usage: python simple_orchestrator.py <prompt1.md> [prompt2.md] ...")
        sys.exit(1)

    # Parse prompt files from command line
    task_prompts = {}
    for prompt_file in sys.argv[1:]:
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            prompt_path = Path("prompts") / prompt_file
            if not prompt_path.exists():
                print(f"❌ Prompt file not found: {prompt_file}")
                continue

        task_name = prompt_path.stem
        task_prompts[task_name] = str(prompt_path)

    if not task_prompts:
        print("❌ No valid prompt files found")
        sys.exit(1)

    print(f"🎯 Found {len(task_prompts)} tasks to execute:")
    for task_name in task_prompts:
        print(f"  - {task_name}")

    # Execute tasks
    orchestrator = SimpleOrchestrator()
    completed = orchestrator.execute_tasks(task_prompts)

    if len(completed) == len(task_prompts):
        print("\n🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {len(task_prompts) - len(completed)} tasks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
