#!/usr/bin/env python3
"""
Orchestrator Parallel Execution for v0.3 Critical Tasks

This script orchestrates the parallel execution of three critical tasks:
1. Fix Final Pyright Errors
2. Complete Testing Suite
3. Final Integration Check
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Task definitions
TASKS = [
    {
        "id": "fix-final-pyright-errors",
        "prompt": "fix-final-pyright-errors.md",
        "description": "Fix Final Pyright Errors - Achieve ZERO errors",
        "worktree": ".worktrees/task-fix-final-pyright-errors",
        "branch": "feature/fix-final-pyright-errors",
    },
    {
        "id": "complete-testing-suite",
        "prompt": "complete-testing-suite.md",
        "description": "Complete Testing Suite - Full Coverage",
        "worktree": ".worktrees/task-complete-testing-suite",
        "branch": "feature/complete-testing-suite",
    },
    {
        "id": "final-integration-check",
        "prompt": "final-integration-check.md",
        "description": "Final Integration Check - System Validation",
        "worktree": ".worktrees/task-final-integration-check",
        "branch": "feature/final-integration-check",
    },
]


class OrchestratorExecutor:
    """Orchestrates parallel task execution with worktree isolation."""

    def __init__(self, base_path: Path = Path.cwd()):
        """Initialize the orchestrator."""
        self.base_path = base_path
        self.prompts_dir = base_path / "prompts"
        self.worktrees_base = base_path / ".worktrees"
        self.tasks_completed = []
        self.tasks_failed = []

    async def setup_worktree(self, task: Dict) -> bool:
        """Set up a git worktree for a task."""
        worktree_path = self.base_path / task["worktree"]

        if worktree_path.exists():
            logger.info(f"✓ Worktree already exists: {worktree_path}")
            return True

        logger.info(f"Creating worktree: {worktree_path}")

        # Create worktree
        cmd = ["git", "worktree", "add", str(worktree_path), "-b", task["branch"]]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_path)

        if result.returncode != 0:
            # Try without -b if branch exists
            cmd = ["git", "worktree", "add", str(worktree_path), task["branch"]]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.base_path
            )

            if result.returncode != 0:
                logger.error(f"Failed to create worktree: {result.stderr}")
                return False

        # Set up UV environment
        logger.info(f"Setting up UV environment for {task['id']}")
        uv_cmd = ["uv", "sync", "--all-extras"]
        uv_result = subprocess.run(
            uv_cmd, capture_output=True, text=True, cwd=worktree_path
        )

        if uv_result.returncode != 0:
            logger.warning(f"UV sync failed: {uv_result.stderr}")
            # Continue anyway - might not be critical

        return True

    async def execute_workflow_manager(self, task: Dict) -> Dict:
        """Execute a task via WorkflowManager with proper delegation."""
        task_id = task["id"]
        worktree_path = self.base_path / task["worktree"]
        prompt_file = self.prompts_dir / task["prompt"]

        logger.info(f"🚀 Executing task: {task_id}")

        # Create WorkflowManager invocation prompt
        invocation_prompt = f"""# WorkflowManager Task Execution

## Task: {task["description"]}

## Source Prompt
Execute the workflow for: prompts/{task["prompt"]}

## Worktree Information
- Path: {worktree_path}
- Task ID: {task_id}

## Requirements
Execute the complete 11-phase workflow:
1. Phase 1: Initial Setup
2. Phase 2: Issue Creation
3. Phase 3: Branch Management
4. Phase 4: Research and Planning
5. Phase 5: Implementation
6. Phase 6: Testing (MUST pass all tests)
7. Phase 7: Documentation
8. Phase 8: Pull Request Creation
9. Phase 9: Code Review (invoke code-reviewer)
10. Phase 10: Review Response
11. Phase 11: Settings Update

## Critical Requirements
- This is a UV project - use 'uv run' for ALL Python commands
- All tests MUST pass before PR creation
- Execute all work in the specified worktree
- Use --dangerously-skip-permissions flag for automation

/agent:workflow-manager

Execute complete workflow for task {task_id} using prompt file {task["prompt"]} in worktree {worktree_path}
"""

        # Write invocation prompt to temp file
        temp_prompt = Path(f"/tmp/orchestrator_{task_id}.md")
        temp_prompt.write_text(invocation_prompt)

        # Execute via claude CLI with --dangerously-skip-permissions
        cmd = ["claude", "--dangerously-skip-permissions", "-p", str(temp_prompt)]

        logger.info(f"Executing: {' '.join(cmd)}")

        # Run in subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=worktree_path,
        )

        stdout, stderr = await process.communicate()

        result = {
            "task_id": task_id,
            "success": process.returncode == 0,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
            "returncode": process.returncode,
        }

        # Save output to log file
        log_file = Path(f"/tmp/{task_id}_output.log")
        log_file.write_text(result["stdout"] + "\n" + result["stderr"])

        if result["success"]:
            logger.info(f"✅ Task {task_id} completed successfully")
            self.tasks_completed.append(task_id)
        else:
            logger.error(f"❌ Task {task_id} failed with code {result['returncode']}")
            self.tasks_failed.append(task_id)

        return result

    async def run_parallel(self) -> None:
        """Run all tasks in parallel."""
        logger.info("=" * 60)
        logger.info("🎯 ORCHESTRATOR: Starting Parallel Task Execution")
        logger.info("=" * 60)

        # Phase 1: Setup worktrees
        logger.info("\n📁 Phase 1: Setting up worktrees...")
        setup_tasks = []
        for task in TASKS:
            setup_tasks.append(self.setup_worktree(task))

        setup_results = await asyncio.gather(*setup_tasks)

        if not all(setup_results):
            logger.error("Failed to set up some worktrees. Aborting.")
            sys.exit(1)

        # Phase 2: Execute tasks in parallel
        logger.info("\n🚀 Phase 2: Launching parallel WorkflowManager executions...")

        execution_tasks = []
        for task in TASKS:
            execution_tasks.append(self.execute_workflow_manager(task))

        # Execute all tasks in parallel
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)

        # Phase 3: Report results
        logger.info("\n📊 Phase 3: Results Summary")
        logger.info("=" * 60)

        for i, result in enumerate(results):
            task = TASKS[i]
            if isinstance(result, Exception):
                logger.error(f"Task {task['id']} raised exception: {result}")
            elif result["success"]:
                logger.info(f"✅ {task['id']}: SUCCESS")
            else:
                logger.error(f"❌ {task['id']}: FAILED")

        # Generate summary report
        self.generate_report(results)

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ORCHESTRATOR: Parallel Execution Complete!")
        logger.info("=" * 60)

        if self.tasks_completed:
            logger.info(f"\n✅ Completed tasks: {', '.join(self.tasks_completed)}")
        if self.tasks_failed:
            logger.error(f"\n❌ Failed tasks: {', '.join(self.tasks_failed)}")

        logger.info("\nNext steps:")
        logger.info("1. Review the PRs created for each task")
        logger.info("2. Merge PRs after approval")
        logger.info("3. Clean up worktrees with: git worktree prune")

        # Exit with appropriate code
        sys.exit(0 if not self.tasks_failed else 1)

    def generate_report(self, results: List[Dict]) -> None:
        """Generate execution report."""
        report_path = self.base_path / "ORCHESTRATOR_PARALLEL_EXECUTION_REPORT.md"

        report = f"""# Orchestrator Parallel Execution Report

## Execution Date
{datetime.now().isoformat()}

## Tasks Executed
"""

        for i, task in enumerate(TASKS):
            result = results[i] if i < len(results) else None
            status = "✅ SUCCESS" if result and result.get("success") else "❌ FAILED"

            report += f"""
### {i + 1}. {task["description"]}
- **Task ID**: {task["id"]}
- **Prompt**: {task["prompt"]}
- **Worktree**: {task["worktree"]}
- **Status**: {status}
- **Log**: /tmp/{task["id"]}_output.log
"""

        report += f"""
## Summary
- **Total Tasks**: {len(TASKS)}
- **Completed**: {len(self.tasks_completed)}
- **Failed**: {len(self.tasks_failed)}

## Log Files
"""

        for task in TASKS:
            report += f"- {task['id']}: `/tmp/{task['id']}_output.log`\n"

        report += """
## Next Steps
1. Review pull requests created by each task
2. Merge approved PRs
3. Clean up worktrees with `git worktree prune`
4. Update Memory.md with completion status
"""

        report_path.write_text(report)
        logger.info(f"Report saved to: {report_path}")


async def main():
    """Main entry point."""
    orchestrator = OrchestratorExecutor()
    await orchestrator.run_parallel()


if __name__ == "__main__":
    asyncio.run(main())
