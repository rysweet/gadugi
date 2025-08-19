#!/usr/bin/env python3
"""
Direct Executor - Immediate WorkflowManager Subprocess Spawning

This creates real parallel WorkflowManager processes using the successful approach from PRs #278-282.
"""
import os
import subprocess
import sys
import time
from pathlib import Path
import tempfile
import uuid


def create_worktree_and_spawn(task_name, prompt_file):
    """Create worktree and spawn WorkflowManager subprocess"""

    # Generate unique identifiers
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())

    # Create unique branch name
    branch_name = f"orchestrator/{task_name}-{timestamp}"
    worktree_path = f".worktrees/orchestrator-{task_name}-{unique_id}"

    print(f"🌳 Creating worktree for {task_name}")
    print(f"   Branch: {branch_name}")
    print(f"   Path: {worktree_path}")

    # Clean up any existing worktree
    subprocess.run(['git', 'worktree', 'remove', '--force', worktree_path],
                  capture_output=True)

    # Create worktree
    result = subprocess.run([
        'git', 'worktree', 'add', worktree_path,
        '-b', branch_name
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to create worktree: {result.stderr}")
        return None

    # Read prompt content
    if not Path(prompt_file).exists():
        prompt_file = f"prompts/{prompt_file}"
    prompt_content = Path(prompt_file).read_text()

    # Create task context in worktree
    task_dir = Path(worktree_path) / ".task"
    task_dir.mkdir(exist_ok=True)

    context_file = task_dir / "orchestrator_context.md"
    context_file.write_text(f"""# Orchestrator Task: {task_name}

## Task Details
- Task ID: {task_name}
- Unique ID: {unique_id}
- Worktree: {worktree_path}
- Branch: {branch_name}
- Spawned at: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Original Prompt Content

{prompt_content}

## WorkflowManager Instructions

Execute the complete 11-phase WorkflowManager workflow for this task:

1. **Phase 1**: Initial Setup
2. **Phase 2**: Issue Creation
3. **Phase 3**: Branch Management
4. **Phase 4**: Research and Planning
5. **Phase 5**: Implementation
6. **Phase 6**: Testing (MANDATORY - all tests must pass)
7. **Phase 7**: Documentation
8. **Phase 8**: Pull Request
9. **Phase 9**: Review (code-reviewer invocation)
10. **Phase 10**: Review Response
11. **Phase 11**: Settings Update

**CRITICAL**: All phases must be completed. Do not skip any phases.
**CRITICAL**: Phase 6 testing must pass all quality gates before proceeding.
**CRITICAL**: This is a real implementation task - no stubs or placeholders.

Begin workflow execution immediately.
""")

    print(f"✅ Created worktree and context: {worktree_path}")

    # Now spawn WorkflowManager subprocess
    print(f"🚀 Spawning WorkflowManager subprocess for {task_name}")

    process = subprocess.Popen([
        'claude', '-p', '/agent:workflow-manager',
        '--dangerously-skip-permissions',
        '--max-turns', '150',  # High turn limit for complex tasks
        '--verbose'
    ],
    cwd=worktree_path,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
    )

    # Send the context to WorkflowManager
    initial_input = f"""Read the orchestrator context and execute the workflow:

{context_file.read_text()}

Begin Phase 1 (Initial Setup) now.
"""

    try:
        process.stdin.write(initial_input)
        process.stdin.close()
    except Exception as e:
        print(f"⚠️ Error sending input to {task_name}: {e}")

    print(f"✅ Spawned WorkflowManager PID {process.pid} for {task_name}")
    return {
        'task_name': task_name,
        'process': process,
        'worktree_path': worktree_path,
        'branch_name': branch_name,
        'pid': process.pid
    }


def main():
    """Execute tasks in parallel"""
    if len(sys.argv) < 2:
        print("Usage: python direct_executor.py <prompt1.md> [prompt2.md] ...")
        sys.exit(1)

    tasks = []

    # Spawn all processes immediately
    for prompt_file in sys.argv[1:]:
        task_name = Path(prompt_file).stem
        print(f"\n{'='*50}")
        print(f"SPAWNING TASK: {task_name}")
        print(f"{'='*50}")

        task_info = create_worktree_and_spawn(task_name, prompt_file)
        if task_info:
            tasks.append(task_info)
            time.sleep(3)  # Small delay between spawns
        else:
            print(f"❌ Failed to spawn task: {task_name}")

    if not tasks:
        print("❌ No tasks spawned successfully")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"MONITORING {len(tasks)} PARALLEL PROCESSES")
    print(f"{'='*50}")

    for task in tasks:
        print(f"📋 {task['task_name']}: PID {task['pid']}, Worktree: {task['worktree_path']}")

    # Monitor processes
    completed = []
    start_time = time.time()

    while len(completed) < len(tasks):
        for task in tasks:
            if task['task_name'] in completed:
                continue

            process = task['process']
            returncode = process.poll()

            if returncode is not None:
                elapsed = time.time() - start_time
                task_name = task['task_name']

                if returncode == 0:
                    print(f"✅ COMPLETED: {task_name} (PID {task['pid']}) after {elapsed:.1f}s")
                else:
                    print(f"❌ FAILED: {task_name} (PID {task['pid']}) with code {returncode} after {elapsed:.1f}s")

                # Get final output (last bit)
                try:
                    stdout, stderr = process.communicate(timeout=5)
                    if stdout:
                        print(f"📄 Output from {task_name}: ...{stdout[-300:]}")
                except:
                    print(f"⚠️ Could not get output from {task_name}")

                completed.append(task_name)

        if len(completed) < len(tasks):
            time.sleep(15)  # Check every 15 seconds
            print(f"⏳ Still running: {[t['task_name'] for t in tasks if t['task_name'] not in completed]}")

    total_time = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"PARALLEL EXECUTION COMPLETED in {total_time:.1f}s")
    print(f"✅ Completed tasks: {len(completed)}")
    print(f"📋 Tasks: {completed}")
    print(f"{'='*50}")

    return len(completed) == len(tasks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
