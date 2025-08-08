"""Parallel task executor with worktree isolation support."""

import asyncio
import logging
import os
import subprocess
import tempfile
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        from .orchestrator import ExecutionResult
        
        task_id = task.id if hasattr(task, "id") else str(uuid.uuid4())
        result = ExecutionResult(task_id=task_id)
        
        try:
            logger.debug(f"Executing task {task_id}")
            
            # Simulate task execution (replace with actual implementation)
            if hasattr(task, "agent_type") and task.agent_type:
                # Would invoke specific agent here
                await asyncio.sleep(0.1)  # Simulate work
                execution_output = f"Executed by {task.agent_type}"
            else:
                # Generic execution
                await asyncio.sleep(0.1)  # Simulate work
                execution_output = "Task executed successfully"
            
            # Mark as complete
            result.complete(True, result=execution_output)
            self.total_executed += 1
            self.total_succeeded += 1
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            result.complete(False, error=str(e))
            self.total_executed += 1
            self.total_failed += 1
        
        return result
    
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
        try:
            # Change to worktree directory if available
            original_cwd = None
            if worktree and worktree.path.exists():
                original_cwd = os.getcwd()
                os.chdir(worktree.path)
                logger.debug(f"Switched to worktree {worktree.path} for task {task.id}")
            
            # Execute the task
            result = await self._execute_single_task(task)
            
            return result
        
        finally:
            # Restore original directory
            if original_cwd:
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
            result = subprocess.run(
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