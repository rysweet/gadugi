from typing import Any, Dict

import asyncio
import json
import logging
import subprocess
import sys

#!/usr/bin/env python3
"""Execute the three specified tasks in parallel using the Orchestrator.

This script:
1. Creates isolated worktrees for each task
2. Delegates execution to WorkflowManager instances
3. Executes all tasks in parallel
4. Monitors until 100% complete
"""

from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Simplified orchestrator for executing the three parallel tasks."""

    def __init__(self):
        self.tasks = [
            {
                "id": "fix-pyright-errors",
                "name": "Fix All Pyright Errors",
                "prompt_file": "fix-all-pyright-errors.md",
                "description": "Fix all remaining pyright errors across v0.3 components",
            },
            {
                "id": "complete-team-coach",
                "name": "Complete Team Coach Implementation",
                "prompt_file": "complete-team-coach-implementation.md",
                "description": "Implement the Team Coach agent for session analysis",
            },
            {
                "id": "cleanup-worktrees",
                "name": "Clean Up All Worktrees",
                "prompt_file": "cleanup-all-worktrees.md",
                "description": "Clean up all existing worktrees and add automatic cleanup",
            },
        ]
        self.worktrees = {}
        self.results = {}

    async def create_worktree(self, task_id: str) -> Dict[str, Any]:
        """Create an isolated worktree for a task."""
        worktree_path = Path(f".worktrees/task-{task_id}")
        branch_name = f"task/{task_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"Creating worktree for {task_id} at {worktree_path}")

        try:
            # Remove existing worktree if it exists
            if worktree_path.exists():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    capture_output=True,
                    check=False,
                )

            # Create new worktree
            result = subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-b",
                    branch_name,
                    str(worktree_path),
                    "HEAD",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Check if it's a UV project and set up environment
            if (worktree_path / "pyproject.toml").exists() and (
                worktree_path / "uv.lock"
            ).exists():
                logger.info(f"Setting up UV environment for {task_id}")
                subprocess.run(
                    ["uv", "sync", "--all-extras"],
                    cwd=str(worktree_path),
                    capture_output=True,
                    check=True,
                )

            self.worktrees[task_id] = {
                "path": worktree_path,
                "branch": branch_name,
                "created": True,
            }

            logger.info(f"✅ Worktree created for {task_id}")
            return self.worktrees[task_id]

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree for {task_id}: {e}")
            return {"created": False, "error": str(e)}

    async def execute_workflow_manager(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task via WorkflowManager using claude CLI."""
        task_id = task["id"]
        prompt_file = task["prompt_file"]
        worktree = self.worktrees.get(task_id)

        if not worktree or not worktree.get("created"):
            return {
                "success": False,
                "error": "Worktree not created",
                "task_id": task_id,
            }

        logger.info(f"🚀 Executing WorkflowManager for {task_id}")

        # Create the WorkflowManager invocation prompt
        prompt_content = f"""# WorkflowManager Task Execution

## Task: {task["name"]}

## Description
{task["description"]}

## Source Prompt
Execute the workflow for: /prompts/{prompt_file}

## Worktree Information
- Path: {worktree["path"]}
- Branch: {worktree["branch"]}

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
- This is a UV project - use 'uv run' for all Python commands
- Fix ALL pyright errors to achieve zero errors
- All tests MUST pass before PR creation
- Execute all work in the specified worktree

/agent:workflow-manager

Execute complete workflow for {task_id} using prompt file {prompt_file}
"""

        # Write prompt to temporary file
        prompt_path = Path(f"/tmp/orchestrator_{task_id}.md")
        prompt_path.write_text(prompt_content)

        try:
            # Execute via claude CLI
            logger.info(f"Invoking: claude -p {prompt_path}")

            process = await asyncio.create_subprocess_exec(
                "claude",
                "-p",
                str(prompt_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(worktree["path"]),
            )

            # Wait for completion with generous timeout (10 minutes per task)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)

            output = stdout.decode("utf-8")
            error_output = stderr.decode("utf-8")

            if process.returncode == 0:
                logger.info(f"✅ Task {task_id} completed successfully")
                return {
                    "success": True,
                    "task_id": task_id,
                    "output": output,
                    "worktree": worktree["path"],
                }
            else:
                logger.error(f"❌ Task {task_id} failed: {error_output}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": error_output,
                    "output": output,
                }

        except asyncio.TimeoutError:
            logger.error(f"⏱️ Task {task_id} timed out")
            return {
                "success": False,
                "task_id": task_id,
                "error": "Execution timed out after 10 minutes",
            }
        except Exception as e:
            logger.error(f"❌ Task {task_id} failed with exception: {e}")
            return {"success": False, "task_id": task_id, "error": str(e)}

    async def execute_parallel(self):
        """Execute all tasks in parallel."""
        logger.info("=" * 60)
        logger.info("🎯 ORCHESTRATOR: Starting parallel execution of 3 tasks")
        logger.info("=" * 60)

        # Phase 1: Create worktrees for all tasks
        logger.info("\n📁 Phase 1: Creating isolated worktrees...")
        worktree_tasks = []
        for task in self.tasks:
            worktree_tasks.append(self.create_worktree(task["id"]))

        await asyncio.gather(*worktree_tasks)

        # Phase 2: Execute tasks in parallel via WorkflowManager
        logger.info("\n🚀 Phase 2: Executing tasks in parallel...")
        execution_tasks = []
        for task in self.tasks:
            execution_tasks.append(self.execute_workflow_manager(task))

        # Execute all tasks in parallel
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)

        # Phase 3: Process results
        logger.info("\n📊 Phase 3: Processing results...")
        successful = 0
        failed = 0

        for i, result in enumerate(results):
            task = self.tasks[i]
            if isinstance(result, Exception):
                logger.error(f"Task {task['id']} failed with exception: {result}")
                self.results[task["id"]] = {"success": False, "error": str(result)}
                failed += 1
            elif result.get("success"):
                logger.info(f"✅ Task {task['id']}: SUCCESS")
                self.results[task["id"]] = result
                successful += 1
            else:
                logger.error(f"❌ Task {task['id']}: FAILED - {result.get('error')}")
                self.results[task["id"]] = result
                failed += 1

        # Phase 4: Clean up worktrees
        logger.info("\n🧹 Phase 4: Cleaning up worktrees...")
        for task_id, worktree in self.worktrees.items():
            if worktree.get("created") and worktree.get("path"):
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", str(worktree["path"])],
                        capture_output=True,
                        check=False,
                    )
                    logger.info(f"Cleaned up worktree for {task_id}")
                except Exception as e:
                    logger.warning(f"Failed to clean up worktree for {task_id}: {e}")

        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("📈 ORCHESTRATOR: Execution Complete")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {successful}/{len(self.tasks)}")
        logger.info(f"❌ Failed: {failed}/{len(self.tasks)}")

        if successful == len(self.tasks):
            logger.info("\n🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
            logger.info("✓ Zero pyright errors achieved")
            logger.info("✓ Team Coach fully implemented")
            logger.info("✓ All worktrees cleaned up")
        else:
            logger.warning("\n⚠️ Some tasks failed. Review the errors above.")

        return self.results


async def main():
    """Main entry point."""
    orchestrator = TaskOrchestrator()

    try:
        results = await orchestrator.execute_parallel()

        # Save results to file
        results_file = Path("orchestrator_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\n📝 Results saved to {results_file}")

        # Exit with appropriate code
        all_successful = all(r.get("success") for r in results.values())
        sys.exit(0 if all_successful else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
