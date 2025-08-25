#!/usr/bin/env python3
"""
OrchestratorMain - Central Coordinator for Parallel Workflow Execution

This module implements the main orchestrator that coordinates parallel execution
of WorkflowManager agents, addressing the critical gap identified in Issue #106.

Key Features:
- Coordinates existing components (ExecutionEngine, WorktreeManager, TaskAnalyzer, PromptGenerator)
- Implements process registry for monitoring parallel tasks
- Provides real-time progress tracking and error handling
- Integrates with Enhanced Separation shared modules for reliability
"""

import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import existing orchestrator components
try:
    from .components.execution_engine import ExecutionEngine, ExecutionResult, TaskExecutor
    from .components.worktree_manager import WorktreeManager, WorktreeInfo
    from .components.task_analyzer import TaskAnalyzer, TaskInfo
    from .components.prompt_generator import PromptGenerator, PromptContext
except ImportError:
    # Fallback for direct execution
    from components.execution_engine import ExecutionEngine, ExecutionResult, TaskExecutor
    from components.worktree_manager import WorktreeManager, WorktreeInfo
    from components.task_analyzer import TaskAnalyzer, TaskInfo
    from components.prompt_generator import PromptGenerator, PromptContext

# Import Enhanced Separation shared modules (fallback for development)
class GitHubOperations:
    def __init__(self, task_id=None) -> None: pass
class StateManager:
    def __init__(self) -> None: pass
class CheckpointManager:
    def __init__(self, state_manager) -> None: pass
class ErrorHandler:
    def __init__(self) -> None: pass
class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30.0) -> None: pass
class TaskMetrics:
    def __init__(self) -> None: pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ProcessRegistry will be imported after it's defined
ProcessRegistry = None

# Fallback classes for process management
class ProcessStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessInfo:
    task_id: str
    task_name: str
    status: str
    command: str
    working_directory: str
    created_at: datetime
    prompt_file: str


@dataclass
class OrchestrationConfig:
    """Configuration for orchestration execution"""
    max_parallel_tasks: int = 4
    execution_timeout_hours: int = 2
    monitoring_interval_seconds: int = 30
    enable_checkpoint: bool = True
    fallback_to_sequential: bool = True
    worktrees_dir: str = ".worktrees"
    monitoring_dir: str = ".gadugi/monitoring"


@dataclass
class OrchestrationResult:
    """Result of orchestration execution"""
    task_id: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    execution_time_seconds: float
    parallel_speedup: Optional[float] = None
    task_results: List[ExecutionResult] = None
    error_summary: Optional[str] = None


class OrchestratorCoordinator:
    """
    Central coordinator for parallel workflow execution.

    This class implements the missing coordination layer that ties together
    all existing orchestrator components to enable actual parallel execution.
    """

    def __init__(self, config: OrchestrationConfig = None, project_root: str = ".") -> None:
        """Initialize the orchestrator with existing components"""
        self.config = config or OrchestrationConfig()
        self.project_root = Path(project_root).resolve()
        self.orchestration_id = f"orchestration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Initialize directories
        self.monitoring_dir = self.project_root / self.config.monitoring_dir
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        # Initialize existing components
        logger.info("Initializing orchestrator components...")
        self.task_analyzer = TaskAnalyzer(project_root=str(self.project_root))
        self.worktree_manager = WorktreeManager(
            str(self.project_root),
            self.config.worktrees_dir
        )
        self.execution_engine = ExecutionEngine()
        self.prompt_generator = PromptGenerator(str(self.project_root))

        # Initialize process registry
        try:
            try:
                from .process_registry import ProcessRegistry, ProcessStatus, ProcessInfo
            except ImportError:
                from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo

            self.process_registry = ProcessRegistry(
                registry_dir=str(self.monitoring_dir),
                clean_start=True  # Always start fresh for new orchestration
            )
            # Set module-level references for other methods
            globals()['ProcessRegistry'] = ProcessRegistry
            globals()['ProcessStatus'] = ProcessStatus
            globals()['ProcessInfo'] = ProcessInfo
        except ImportError as e:
            logger.error(f"Could not import ProcessRegistry: {e}")
            self.process_registry = None

        # Initialize Enhanced Separation components
        try:
            self.github_ops = GitHubOperations()
            self.state_manager = StateManager()
            self.checkpoint_manager = CheckpointManager(self.state_manager)
            self.error_handler = ErrorHandler()
            self.task_metrics = TaskMetrics()

            # Configure circuit breakers
            self.github_circuit_breaker = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=300.0
            )
            self.execution_circuit_breaker = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=600.0
            )
        except Exception as e:
            logger.warning(f"Enhanced Separation modules not fully available: {e}")
            # Continue with basic functionality

        # State tracking
        self.current_orchestration: Optional[OrchestrationResult] = None
        self._shutdown_requested = False
        self._monitoring_thread: Optional[threading.Thread] = None

        logger.info(f"OrchestratorCoordinator initialized with ID: {self.orchestration_id}")

    def orchestrate(self, prompt_files: List[str]) -> OrchestrationResult:
        """
        Main orchestration method - coordinates parallel execution of prompt files.

        This is the core method that implements the missing orchestration logic.
        """
        start_time = time.time()
        logger.info(f"Starting orchestration of {len(prompt_files)} prompt files")

        # Initialize result tracking
        result = OrchestrationResult(
            task_id=self.orchestration_id,
            total_tasks=len(prompt_files),
            successful_tasks=0,
            failed_tasks=0,
            execution_time_seconds=0.0,
            task_results=[]
        )

        try:
            # Phase 1: Task Analysis and Planning
            logger.info("Phase 1: Analyzing tasks for parallel execution...")
            task_analysis = self._analyze_tasks(prompt_files)

            if not task_analysis:
                raise Exception("Task analysis failed - cannot proceed with orchestration")

            # Phase 2: Environment Setup
            logger.info("Phase 2: Setting up isolated execution environments...")
            worktree_assignments = self._setup_worktrees(task_analysis)

            # Phase 3: Parallel Execution
            logger.info("Phase 3: Executing tasks in parallel...")
            execution_results = self._execute_parallel_tasks(
                task_analysis,
                worktree_assignments
            )

            # Phase 4: Result Integration
            logger.info("Phase 4: Integrating results and cleanup...")
            result.task_results = execution_results
            result.successful_tasks = len([r for r in execution_results if (r.status if r is not None else None) == 'success'])
            result.failed_tasks = len([r for r in execution_results if (r.status if r is not None else None) != 'success'])

            # Calculate performance metrics
            result.execution_time_seconds = time.time() - start_time
            result.parallel_speedup = self._calculate_speedup(
                result.execution_time_seconds,
                len(prompt_files)
            )

            # Phase 5: Cleanup
            self._cleanup_orchestration(worktree_assignments)

            logger.info(f"Orchestration completed: {result.successful_tasks}/{result.total_tasks} successful")
            return result

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            result.error_summary = str(e)
            result.execution_time_seconds = time.time() - start_time

            # Attempt graceful fallback to sequential execution
            if self.config.fallback_to_sequential and not self._shutdown_requested:
                logger.info("Attempting fallback to sequential execution...")
                return self._fallback_sequential_execution(prompt_files, start_time)

            return result

    def _analyze_tasks(self, prompt_files: List[str]) -> List[TaskInfo]:
        """Analyze prompt files for dependencies and parallelization opportunities"""
        logger.info(f"Analyzing {len(prompt_files)} prompt files...")

        try:
            # Use TaskAnalyzer to analyze all prompt files
            task_infos = self.task_analyzer.analyze_prompts(prompt_files)
            logger.info(f"Analyzed {len(task_infos)} valid tasks")

            # Log analysis results
            for task_info in task_infos:
                logger.info(f"Task {task_info.id}: {task_info.task_type.value}, complexity={task_info.complexity.name}")

            return task_infos

        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            return []


    def _setup_worktrees(self, task_infos: List[TaskInfo]) -> Dict[str, WorktreeInfo]:
        """Set up isolated git worktrees for parallel execution"""
        logger.info("Setting up isolated worktrees...")

        worktree_assignments = {}

        for task_info in task_infos:
            try:
                # Create worktree for this task
                worktree_info = self.worktree_manager.create_worktree(
                    task_id=task_info.id,
                    task_name=task_info.name,
                    base_branch="main"
                )

                worktree_assignments[task_info.id] = worktree_info
                logger.info(f"Created worktree for {task_info.id}: {worktree_info.worktree_path}")

            except Exception as e:
                logger.error(f"Failed to create worktree for {task_info.id}: {e}")
                # Continue with other tasks
                continue

        return worktree_assignments

    def _execute_parallel_tasks(
        self,
        task_infos: List[TaskInfo],
        worktree_assignments: Dict[str, WorktreeInfo]
    ) -> List[ExecutionResult]:
        """Execute tasks in parallel using WorkflowManager agents"""
        logger.info("Starting parallel task execution...")

        # Start monitoring thread
        self._start_monitoring()

        # Prepare task executors
        task_executors = []
        for task_info in task_infos:
            if task_info.id not in worktree_assignments:
                logger.warning(f"No worktree for {task_info.id}, skipping")
                continue

            worktree_info = worktree_assignments[task_info.id]

            # Generate WorkflowManager prompt
            prompt_context = PromptContext(
                task_id=task_info.id,
                task_name=task_info.name,
                original_prompt=(task_info.prompt_file if task_info is not None else None),
                dependencies=task_info.dependencies,
                target_files=task_info.target_files
            )

            workflow_prompt = self.prompt_generator.generate_workflow_prompt(
                prompt_context,
                worktree_info.worktree_path
            )

            # Create task executor
            executor = TaskExecutor(
                task_id=task_info.id,
                worktree_path=worktree_info.worktree_path,
                prompt_file=workflow_prompt,
                task_context={
                    'task_name': task_info.name,
                    'working_directory': str(worktree_info.worktree_path),
                    'timeout_seconds': self.config.execution_timeout_hours * 3600
                }
            )

            task_executors.append(executor)

            # Register process for monitoring
            if self.process_registry and ProcessInfo and ProcessStatus:
                process_info = ProcessInfo(
                    task_id=task_info.id,
                    task_name=task_info.name,
                    status=ProcessStatus.QUEUED,
                    command=f"claude /agent:workflow-manager",
                    working_directory=str(worktree_info.worktree_path),
                    created_at=datetime.now(),
                    prompt_file=workflow_prompt
                )
                self.process_registry.register_process(process_info)

        # Execute tasks in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.config.max_parallel_tasks) as executor:
            # Submit all tasks
            future_to_task = {}
            for task_executor in task_executors:
                future = executor.submit(self._execute_single_task, task_executor)
                future_to_task[future] = task_executor
                logger.info(f"Submitted task for execution: {(task_executor.task_id if task_executor is not None else None)}")

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_executor = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Task completed: {(task_executor.task_id if task_executor is not None else None)}, status={(result.status if result is not None else None)}")
                except Exception as e:
                    logger.error(f"Task execution failed: {(task_executor.task_id if task_executor is not None else None)}, error={e}")
                    # Create failed result
                    failed_result = ExecutionResult(
                        task_id=(task_executor.task_id if task_executor is not None else None),
                        task_name=task_executor.task_context.get('task_name', 'Unknown'),
                        status='failed',
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration=0.0,
                        exit_code=1,
                        stdout='',
                        stderr=str(e),
                        output_file=None,
                        error_message=str(e),
                        resource_usage={}
                    )
                    results.append(failed_result)

        # Stop monitoring
        self._stop_monitoring()

        return results

    def _execute_single_task(self, task_executor: TaskExecutor) -> ExecutionResult:
        """Execute a single task using the execution engine"""
        logger.info(f"Executing task: {(task_executor.task_id if task_executor is not None else None)}")

        # Update process status
        if self.process_registry and ProcessStatus:
            self.process_registry.update_process_status(
                (task_executor.task_id if task_executor is not None else None),
                ProcessStatus.RUNNING
            )

        try:
            # Use TaskExecutor directly to run the task
            result = task_executor.execute(timeout=task_executor.task_context.get('timeout_seconds'))

            # Update process status based on result
            if self.process_registry and ProcessStatus:
                if (result.status if result is not None else None) == 'success':
                    self.process_registry.update_process_status(
                        (task_executor.task_id if task_executor is not None else None),
                        ProcessStatus.COMPLETED
                    )
                else:
                    self.process_registry.update_process_status(
                        (task_executor.task_id if task_executor is not None else None),
                        ProcessStatus.FAILED,
                        error_message=result.error_message
                    )

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {(task_executor.task_id if task_executor is not None else None)}, error={e}")

            # Update process status
            if self.process_registry and ProcessStatus:
                self.process_registry.update_process_status(
                    (task_executor.task_id if task_executor is not None else None),
                    ProcessStatus.FAILED,
                    error_message=str(e)
                )

            # Return failed result
            return ExecutionResult(
                task_id=(task_executor.task_id if task_executor is not None else None),
                task_name=task_executor.task_context.get('task_name', 'Unknown'),
                status='failed',
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0.0,
                exit_code=1,
                stdout='',
                stderr=str(e),
                output_file=None,
                error_message=str(e),
                resource_usage={}
            )

    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._shutdown_requested = False
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Started monitoring thread")

    def _stop_monitoring(self):
        """Stop background monitoring thread"""
        self._shutdown_requested = True
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
        logger.info("Stopped monitoring thread")

    def _monitoring_loop(self):
        """Background monitoring loop for process health"""
        while not self._shutdown_requested:
            try:
                # Update process heartbeats and check health
                if self is not None and self.process_registry:
                    self.process_registry.update_heartbeats()

                # Save monitoring status
                status = self._get_orchestration_status()
                status_file = self.monitoring_dir / f"{self.orchestration_id}_status.json"
                with open(status_file, 'w') as f:
                    json.dump(status, f, indent=2, default=str)

                # Sleep until next monitoring cycle
                time.sleep(self.config.monitoring_interval_seconds)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(5)  # Brief pause before retrying

    def _get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status for monitoring"""
        if not self.process_registry:
            return {
                "orchestration_id": self.orchestration_id,
                "timestamp": datetime.now(),
                "total_processes": 0,
                "status_breakdown": {},
                "active_processes": []
            }

        all_processes = self.process_registry.get_all_processes()

        status_counts = {}
        for process in all_processes.values():
            status_name = (process.status if process is not None else None).value
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

        return {
            "orchestration_id": self.orchestration_id,
            "timestamp": datetime.now(),
            "total_processes": len(all_processes),
            "status_breakdown": status_counts,
            "active_processes": [
                {
                    "task_id": (p.task_id if p is not None else None),
                    "task_name": p.task_name,
                    "status": (p.status if p is not None else None).value,
                    "runtime_seconds": (datetime.now() - p.created_at).total_seconds()
                }
                for p in all_processes.values()
                if (p.status if p is not None else None) in [ProcessStatus.RUNNING, ProcessStatus.QUEUED]
            ]
        }

    def _calculate_speedup(self, parallel_time: float, task_count: int) -> float:
        """Calculate theoretical speedup vs sequential execution"""
        # Estimate sequential time (conservative estimate: 10 minutes per task)
        estimated_sequential_time = task_count * 600  # 10 minutes per task

        if parallel_time > 0:
            speedup = estimated_sequential_time / parallel_time
            return min(speedup, task_count)  # Cap at theoretical maximum

        return 1.0

    def _cleanup_orchestration(self, worktree_assignments: Dict[str, WorktreeInfo]):
        """Clean up worktrees and temporary files"""
        logger.info("Cleaning up orchestration resources...")

        for task_id in worktree_assignments.keys():
            try:
                # Clean up worktree
                self.worktree_manager.cleanup_worktree(task_id)
                logger.info(f"Cleaned up worktree for {task_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup worktree for {task_id}: {e}")

        # Archive process registry
        if self is not None and self.process_registry:
            try:
                archive_file = self.monitoring_dir / f"{self.orchestration_id}_final.json"
                self.process_registry.save_to_file(str(archive_file))
                logger.info(f"Saved final process registry to {archive_file}")
            except Exception as e:
                logger.error(f"Failed to save process registry: {e}")

    def _fallback_sequential_execution(
        self,
        prompt_files: List[str],
        start_time: float
    ) -> OrchestrationResult:
        """Fallback to sequential execution if parallel fails"""
        logger.info("Executing fallback sequential execution...")

        result = OrchestrationResult(
            task_id=f"{self.orchestration_id}-fallback",
            total_tasks=len(prompt_files),
            successful_tasks=0,
            failed_tasks=0,
            execution_time_seconds=0.0,
            task_results=[]
        )

        # Execute tasks sequentially as fallback
        for prompt_file in prompt_files:
            try:
                logger.info(f"Executing task sequentially: {prompt_file}")

                # Analyze the task
                task_infos = self._analyze_tasks([prompt_file])
                if not task_infos:
                    logger.error(f"Failed to analyze task: {prompt_file}")
                    result.failed_tasks += 1
                    continue

                task_info = task_infos[0]

                # Check if worktree already exists from earlier phase
                worktree_info = None
                if task_info.id in self.worktree_manager.worktrees:
                    logger.info(f"Using existing worktree for: {task_info.id}")
                    worktree_info = self.worktree_manager.worktrees[task_info.id]
                else:
                    # Set up new worktree if it doesn't exist
                    worktree_assignments = self._setup_worktrees([task_info])
                    if task_info.id not in worktree_assignments:
                        logger.error(f"Failed to setup worktree for: {prompt_file}")
                        result.failed_tasks += 1
                        continue
                    worktree_info = worktree_assignments[task_info.id]

                # Create task executor
                executor = TaskExecutor(
                    task_id=task_info.id,
                    worktree_path=Path(worktree_info.worktree_path),
                    prompt_file=prompt_file,
                    task_context={'name': task_info.name, 'sequential_fallback': True}
                )

                # Execute the task with subprocess fallback
                exec_result = executor.execute(timeout=self.config.execution_timeout_hours * 3600)

                if (exec_result.status if exec_result is not None else None) == 'success':
                    result.successful_tasks += 1
                else:
                    result.failed_tasks += 1

                result.task_results.append(exec_result)

            except Exception as e:
                logger.error(f"Failed to execute task {prompt_file}: {e}")
                result.failed_tasks += 1

        result.execution_time_seconds = time.time() - start_time
        logger.info(f"Fallback execution completed: {result.successful_tasks}/{result.total_tasks} succeeded")
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return self._get_orchestration_status()

    def shutdown(self):
        """Graceful shutdown of orchestrator"""
        logger.info("Shutting down orchestrator...")
        self._shutdown_requested = True
        self._stop_monitoring()

        # Clean up any remaining resources
        try:
            self.worktree_manager.cleanup_all_worktrees()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        logger.info("Orchestrator shutdown complete")


def main():
    """Main entry point for direct execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator Main - Parallel Workflow Coordination")
    parser.add_argument("prompt_files", nargs="+", help="Prompt files to execute in parallel")
    parser.add_argument("--max-parallel", type=int, default=4, help="Maximum parallel tasks")
    parser.add_argument("--timeout", type=int, default=2, help="Execution timeout in hours")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    # Create configuration
    config = OrchestrationConfig(
        max_parallel_tasks=args.max_parallel,
        execution_timeout_hours=args.timeout
    )

    # Initialize and run orchestrator
    orchestrator = OrchestratorCoordinator(config, args.project_root)

    try:
        result = orchestrator.orchestrate(args.prompt_file if args is not None else None)

        # Print results
        print(f"\nOrchestration Results:")
        print(f"  Total tasks: {result.total_tasks}")
        print(f"  Successful: {result.successful_tasks}")
        print(f"  Failed: {result.failed_tasks}")
        print(f"  Execution time: {result.execution_time_seconds:.1f} seconds")
        if result is not None and result.parallel_speedup:
            print(f"  Parallel speedup: {result.parallel_speedup:.1f}x")

        if result is not None and result.error_summary:
            print(f"  Errors: {result.error_summary}")

    except KeyboardInterrupt:
        print("\nShutdown requested...")
        orchestrator.shutdown()

    except Exception as e:
        logger.error(f"Orchestrator execution failed: {e}")
        orchestrator.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
