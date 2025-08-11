#!/usr/bin/env python3
"""
Direct orchestrator execution script to fix remaining pyright errors.
Uses the fixed parallel_executor with --yes flag.
"""

import asyncio
import subprocess
import sys
from pathlib import Path


async def execute_workflow_manager(task_name, prompt_content, worktree_path):
    """Execute WorkflowManager with --yes flag to avoid permission prompts."""

    # Create prompt file
    prompt_file = Path(f"/tmp/{task_name}_prompt.md")
    prompt_file.write_text(prompt_content)

    # Prepare command with permission skip flag
    cmd = ["claude", "--dangerously-skip-permissions", "-p", str(prompt_file)]

    print(f"🚀 Executing {task_name} in {worktree_path}")
    print(f"   Command: {' '.join(cmd)}")

    # Execute in worktree
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(worktree_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Wait for completion
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        print(f"✅ {task_name} completed successfully")
    else:
        print(f"❌ {task_name} failed with return code {process.returncode}")
        if stderr:
            print(f"   Error: {stderr.decode()}")

    return process.returncode == 0


async def main():
    """Main execution function."""

    # Create worktree for fixing pyright errors
    print("📁 Creating worktree for pyright fixes...")
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            ".worktrees/fix-final-pyright-errors",
            "-b",
            "fix/final-pyright-errors",
        ],
        check=False,
    )

    # Prepare prompt for fixing pyright errors
    prompt_content = """
# Fix ALL Remaining Pyright Errors

## Current State
- 1801 pyright errors remaining after partial fixes
- Main issues: imports, optional access, undefined variables

## Requirements
1. Fix ALL pyright errors to achieve ZERO errors
2. Use `uv run pyright` to verify each fix
3. Fix actual issues, don't just suppress
4. Test all components after fixing

## Specific Areas
- Team Coach: 108 errors
- Orchestrator: Remaining import issues
- Framework: Type annotation issues
- Services: Optional access issues

## Execution
Execute complete 11-phase workflow:
1. Create issue for tracking
2. Work in the worktree branch
3. Fix all errors systematically
4. Run tests to verify nothing broken
5. Create PR with fixes

CRITICAL: This is a UV project - use 'uv run' for all Python commands

/agent:workflow-manager

Execute complete workflow to achieve ZERO pyright errors.
"""

    # Execute the task
    success = await execute_workflow_manager(
        "fix-pyright-errors",
        prompt_content,
        Path(".worktrees/fix-final-pyright-errors"),
    )

    if success:
        print("\n🎉 All tasks completed successfully!")
    else:
        print("\n⚠️ Some tasks failed, please check the logs")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
