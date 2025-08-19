from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Tuple  # type: ignore
)

import asyncio
import json
import logging
import os
import subprocess
import uuid
                        import re

"""Parallel task executor with worktree isolation support."""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    """Execution mode for tasks."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DISTRIBUTED = "distributed"

@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    id: str
    path: Path
    branch: str
    created: bool = False

    def cleanup(self) -> None:
        """Clean up the worktree."""
        if self.created and self.path.exists():
            try:
                subprocess.run(
                    ["git", "worktree", "remove", str(self.path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                logger.debug(f"Cleaned up worktree at {self.path}")
            except Exception as e:
                logger.error(f"Failed to clean up worktree: {e}")

class ParallelExecutor:
    """Executor for parallel task execution with isolation."""

    def __init__(
        self,
        max_workers: int = 4,
        enable_worktrees: bool = True,
        use_processes: bool = False,
    ):
        """Initialize the parallel executor.

        Args:
            max_workers: Maximum parallel workers
            enable_worktrees: Whether to use git worktrees for isolation
            use_processes: Use process pool instead of thread pool
        """
        self.max_workers = max_workers
        self.enable_worktrees = enable_worktrees
        self.use_processes = use_processes

        # Executor pool
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Worktree management
        self.worktrees: Dict[str, WorktreeInfo] = {}
        self.worktree_base = Path(".worktrees")

        # Execution metrics
        self.total_executed = 0
        self.total_succeeded = 0
        self.total_failed = 0

    async def initialize(self) -> None:
        """Initialize the executor."""
        # Create worktree base directory if needed
        if self.enable_worktrees:
            self.worktree_base.mkdir(exist_ok=True)
            logger.info(f"Initialized worktree base at {self.worktree_base}")

    async def execute_batch(
        self,
        tasks: List[Any],
        mode: ExecutionMode = ExecutionMode.PARALLEL,
    ) -> List[Any]:
        """Execute a batch of tasks.

        Args:
            tasks: List of tasks to execute
            mode: Execution mode

        Returns:
            List of execution results
        """
        if mode == ExecutionMode.SEQUENTIAL:
            return await self._execute_sequential(tasks)
        elif mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(tasks)
        else:
            # Distributed mode would require additional infrastructure
            logger.warning(f"Mode {mode} not fully implemented, falling back to parallel")
            return await self._execute_parallel(tasks)

    async def _execute_sequential(self, tasks: List[Any]) -> List[Any]:
        """Execute tasks sequentially."""
        results = []

        for task in tasks:
            result = await self._execute_single_task(task)
            results.append(result)

            # Stop on critical failure
            if hasattr(result, "success") and not result.success:
                if hasattr(result, "retries") and result.retries >= 3:
                    logger.error(f"Critical failure in task {task.id}, stopping sequential execution")
                    break

        return results

    async def _execute_parallel(self, tasks: List[Any]) -> List[Any]:
        """Execute tasks in parallel."""
        # Create async tasks for parallel execution
        async_tasks = []

        for task in tasks:
            # Create isolated environment if needed
            worktree = None
            if self.enable_worktrees and hasattr(task, "id"):
                worktree = await self._create_worktree(task.id)

            # Create async task
            async_task = asyncio.create_task(
                self._execute_with_isolation(task, worktree)
            )
            async_tasks.append(async_task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {tasks[i].id if hasattr(tasks[i], 'id') else i} failed with exception: {result}")
                # Create error result
                from .orchestrator import ExecutionResult
                error_result = ExecutionResult(
                    task_id=tasks[i].id if hasattr(tasks[i], "id") else str(i),
                    success=False,
                    error=str(result),
                )
                error_result.complete(False, error=str(result))
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_single_task(self, task: Any) -> Any:
        """Execute a single task.

        GOVERNANCE REQUIREMENT: All tasks MUST be delegated to WorkflowManager
        to ensure complete 11-phase workflow execution (Issue #148).

        Args:
            task: Task to execute

        Returns:
            Execution result
        """

        task_id = task.id if hasattr(task, "id") else str(uuid.uuid4())
        result = ExecutionResult(task_id=task_id)  # type: ignore

        try:
            logger.debug(f"Delegating task {task_id} to WorkflowManager")

            # MANDATORY: Delegate ALL tasks to WorkflowManager
            # This ensures proper 11-phase workflow execution
            workflow_result = await self._invoke_workflow_manager(task)

            if workflow_result["success"]:
                result.complete(True, result=workflow_result)
                self.total_executed += 1
                self.total_succeeded += 1
                logger.info(f"Task {task_id} completed successfully via WorkflowManager")
            else:
                error_msg = workflow_result.get("error", "WorkflowManager execution failed")
                result.complete(False, error=error_msg)
                self.total_executed += 1
                self.total_failed += 1
                logger.error(f"Task {task_id} failed: {error_msg}")

        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {e}")
            result.complete(False, error=str(e))
            self.total_executed += 1
            self.total_failed += 1

        return result

    async def _invoke_workflow_manager(self, task: Any) -> Dict[str, Any]:
        """Invoke WorkflowManager for task execution via claude -p.

        GOVERNANCE: This is the MANDATORY delegation point to ensure
        all tasks go through the complete 11-phase workflow using proper
        Claude subprocess invocation.

        Args:
            task: Task to execute via WorkflowManager

        Returns:
            Dictionary with execution results
        """
        task_id = task.id if hasattr(task, "id") else str(uuid.uuid4())

        # Create prompt file for WorkflowManager invocation
        prompt_content = self._create_workflow_prompt(task)
        prompt_file = Path(f"/tmp/orchestrator_task_{task_id}.md")

        try:
            # Write prompt file for claude -p invocation
            prompt_file.write_text(prompt_content)

            # Prepare claude -p command for WorkflowManager
            # Use --dangerously-skip-permissions flag to avoid permission prompts
            workflow_cmd = [
                "claude", "--dangerously-skip-permissions", "-p", str(prompt_file)
            ]

            # Execute WorkflowManager via claude subprocess
            logger.info(f"Invoking WorkflowManager for task {task_id} via 'claude -p'")
            logger.debug(f"Command: {' '.join(workflow_cmd)}")
            logger.debug(f"Prompt file: {prompt_file}")

            # Run in subprocess to ensure proper isolation
            process = await asyncio.create_subprocess_exec(
                *workflow_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.worktrees[task_id].path) if task_id in self.worktrees else None,
            )

            # Wait for completion with timeout
            timeout = getattr(task, "timeout_seconds", 300)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"WorkflowManager timed out after {timeout} seconds",
                    "task_id": task_id,
                }

            # Parse results
            if process.returncode == 0:
                # Success - parse output for details
                output = stdout.decode("utf-8")

                # Extract key information from output
                pr_number = None
                issues_created = []
                phases_completed = []

                for line in output.split("\n"):
                    if "PR #" in line or "Pull request #" in line:
                        # Extract PR number
                        match = re.search(r"#(\d+)", line)
                        if match:
                            pr_number = match.group(1)
                    elif "Issue #" in line:
                        # Extract issue number
                        match = re.search(r"#(\d+)", line)
                        if match:
                            issues_created.append(match.group(1))
                    elif "Phase" in line and "completed" in line.lower():
                        phases_completed.append(line.strip())

                return {
                    "success": True,
                    "task_id": task_id,
                    "pr_number": pr_number,
                    "issues_created": issues_created,
                    "phases_completed": phases_completed,
                    "output": output,
                    "workflow_manager_invoked": True,
                    "all_phases_executed": len(phases_completed) >= 11,
                }
            else:
                # Failure
                error_output = stderr.decode("utf-8")
                return {
                    "success": False,
                    "error": f"WorkflowManager failed: {error_output}",
                    "task_id": task_id,
                    "returncode": process.returncode,
                    "workflow_manager_invoked": True,
                }

        except Exception as e:
            logger.error(f"Failed to invoke WorkflowManager: {e}")
            return {
                "success": False,
                "error": f"Failed to invoke WorkflowManager: {str(e)}",
                "task_id": task_id,
                "workflow_manager_invoked": False,
            }

    def _create_workflow_prompt(self, task: Any) -> str:
        """Create a prompt file for WorkflowManager invocation.

        GOVERNANCE: This ensures proper delegation to WorkflowManager
        with all required context for 11-phase workflow execution.

        Args:
            task: Task to create prompt for

        Returns:
            Prompt content for WorkflowManager
        """
        task_id = task.id if hasattr(task, "id") else str(uuid.uuid4())
        task_name = getattr(task, "name", "Unnamed Task")
        task_description = getattr(task, "description", "No description provided")

        # Build prompt content
        prompt_lines = [
            "# WorkflowManager Task Execution Request",
            "",
            "## GOVERNANCE NOTICE",
            "This task has been delegated by the Orchestrator to ensure proper 11-phase workflow execution.",
            "ALL phases MUST be completed as per Issue #148 requirements.",
            "",
            f"## Task ID: {task_id}",
            f"## Task Name: {task_name}",
            "",
            "## Task Description",
            task_description,
            "",
            "## Required Actions",
            "Execute the complete 11-phase workflow for this task:",
            "1. Phase 1: Initial Setup",
            "2. Phase 2: Issue Creation",
            "3. Phase 3: Branch Management",
            "4. Phase 4: Research and Planning",
            "5. Phase 5: Implementation",
            "6. Phase 6: Testing",
            "7. Phase 7: Documentation",
            "8. Phase 8: Pull Request Creation",
            "9. Phase 9: Code Review (invoke code-reviewer agent)",
            "10. Phase 10: Review Response",
            "11. Phase 11: Settings Update",
            "",
        ]

        # Add task parameters if available
        if hasattr(task, "parameters") and task.parameters:
            prompt_lines.extend([
                "## Task Parameters",
                "```json",
                json.dumps(task.parameters, indent=2),
                "```",
                "",
            ])

            # Special handling for prompt files
            if "prompt_file" in task.parameters:
                prompt_lines.extend([
                    "## Source Prompt File",
                    f"Execute workflow for: {task.parameters['prompt_file']}",
                    "",
                ])

        # Add worktree information if available
        if task_id in self.worktrees:
            worktree = self.worktrees[task_id]
            prompt_lines.extend([
                "## Worktree Information",
                f"Worktree Path: {worktree.path}",
                f"Branch: {worktree.branch}",
                "",
                "Please execute all workflow phases within this worktree for proper isolation.",
                "",
            ])

        # Add execution requirements
        prompt_lines.extend([
            "## Execution Requirements",
            "- Create GitHub issue for tracking",
            "- Create feature branch in worktree",
            "- Implement all required changes",
            "- Run all tests and quality checks",
            "- Create pull request with detailed description",
            "- Invoke code-reviewer agent for Phase 9",
            "- Respond to review feedback in Phase 10",
            "- Update settings and complete workflow in Phase 11",
            "",
            "## Important",
            "This is a MANDATORY workflow execution delegated by the Orchestrator.",
            "Failure to complete all 11 phases is a governance violation.",
            "",
            "/agent:workflow-manager",
            "",
            f"Execute complete workflow for task {task_id}",
        ])

        return "\n".join(prompt_lines)

    async def _execute_with_isolation(
        self,
        task: Any,
        worktree: Optional[WorktreeInfo],
    ) -> Any:
        """Execute task with isolation.

        Args:
            task: Task to execute
            worktree: Optional worktree for isolation

        Returns:
            Execution result
        """
        try:  # type: ignore
            original_cwd = None
            # Change to worktree directory if available
            if worktree and worktree.path.exists():  # type: ignore
                original_cwd = os.getcwd()
                os.chdir(worktree.path)
                logger.debug(f"Switched to worktree {worktree.path} for task {task.id}")

            # Execute the task
            result = await self._execute_single_task(task)

            return result

        finally:  # type: ignore
            # Restore original directory
            if original_cwd:  # type: ignore
                os.chdir(original_cwd)

            # Clean up worktree
            if worktree:
                worktree.cleanup()
                if hasattr(task, "id") and task.id in self.worktrees:
                    del self.worktrees[task.id]

    async def _create_worktree(self, task_id: str) -> WorktreeInfo:
        """Create a git worktree for task isolation.

        Args:
            task_id: Task ID

        Returns:
            Worktree information
        """
        worktree_id = f"task_{task_id}_{uuid.uuid4().hex[:8]}"
        worktree_path = self.worktree_base / worktree_id
        branch_name = f"task/{task_id}"

        try:
            # Create worktree
            _result = subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                capture_output=True,
                text=True,
                check=True,
            )

            worktree = WorktreeInfo(
                id=worktree_id,
                path=worktree_path,
                branch=branch_name,
                created=True,
            )

            self.worktrees[task_id] = worktree
            logger.debug(f"Created worktree at {worktree_path} for task {task_id}")

            return worktree

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e}")
            # Return non-created worktree
            return WorktreeInfo(
                id=worktree_id,
                path=worktree_path,
                branch=branch_name,
                created=False,
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            "total_executed": self.total_executed,
            "total_succeeded": self.total_succeeded,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_succeeded / self.total_executed
                if self.total_executed > 0
                else 0.0
            ),
            "active_worktrees": len(self.worktrees),
            "max_workers": self.max_workers,
        }

    async def cleanup(self) -> None:
        """Clean up executor resources."""
        # Clean up any remaining worktrees
        for worktree in list(self.worktrees.values()):
            worktree.cleanup()
        self.worktrees.clear()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info(f"Executor cleanup complete. Metrics: {self.get_metrics()}")
