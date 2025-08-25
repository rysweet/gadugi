#!/usr/bin/env python3
"""
ExecutionEngine Component for OrchestratorAgent

Manages parallel execution of Claude CLI instances for multiple tasks,
including process spawning, monitoring, and resource management.

Security Features:
- Resource limits and monitoring to prevent system overload
- Process isolation and secure execution environment
- Input validation for all command parameters
- Timeout enforcement to prevent runaway processes
"""

import asyncio
import json
import logging
import os
import queue

# Set up logging
logger = logging.getLogger(__name__)
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

# Import the PromptGenerator for creating WorkflowMaster prompts
from .prompt_generator import PromptContext, PromptGenerator

# Import ContainerManager for Docker-based execution (CRITICAL FIX #167)
try:
    # Try absolute import first (works when run directly)
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from container_manager import ContainerManager, ContainerConfig, ContainerResult
    CONTAINER_EXECUTION_AVAILABLE = True
except ImportError:
    try:
        # Fallback to relative import (works when imported as module)
        from ..container_manager import ContainerManager, ContainerConfig, ContainerResult
        CONTAINER_EXECUTION_AVAILABLE = True
    except ImportError:
        logging.warning("ContainerManager not available - falling back to subprocess execution")
        CONTAINER_EXECUTION_AVAILABLE = False
        ContainerManager = None
        ContainerConfig = None
        ContainerResult = None

# Security: Define strict resource limits
MAX_CONCURRENT_TASKS = 8
MAX_MEMORY_PER_TASK_GB = 2.0
MAX_CPU_PERCENT = 80.0
MAX_EXECUTION_TIME_HOURS = 4
MIN_AVAILABLE_MEMORY_GB = 1.0
MAX_OUTPUT_SIZE_MB = 100

# Configure secure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class ExecutionResult:
    """Result of a task execution"""
    task_id: str
    task_name: str
    status: str  # 'success', 'failed', 'timeout', 'cancelled'
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]  # seconds
    exit_code: Optional[int]
    stdout: str
    stderr: str
    output_file: Optional[str]
    error_message: Optional[str]
    resource_usage: Dict[str, float]


@dataclass
class SystemResources:
    """Current system resource usage"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    available_memory_gb: float
    cpu_count: int
    load_avg: List[float]


class ResourceMonitor:
    """Monitors system resources during execution"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.resource_history: List[SystemResources] = []
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("📊 Started resource monitoring")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        print("📊 Stopped resource monitoring")

    def _monitor_loop(self):
        """Resource monitoring loop"""
        while self.monitoring:
            try:
                resources = self.get_current_resources()
                self.resource_history.append(resources)

                # Keep only last 100 measurements
                if len(self.resource_history) > 100:
                    self.resource_history.pop(0)

            except Exception as e:
                print(f"⚠️  Resource monitoring error: {e}")

            time.sleep(self.monitoring_interval)

    def get_current_resources(self) -> SystemResources:
        """Get current system resource usage"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return SystemResources(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            available_memory_gb=memory.available / (1024**3),
            cpu_count=psutil.cpu_count(),
            load_avg=list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
        )

    def is_system_overloaded(self) -> bool:
        """Check if system is overloaded"""
        if not self.resource_history:
            return False

        current = self.resource_history[-1]

        # Check various overload conditions
        conditions = [
            current.cpu_percent > 90,
            current.memory_percent > 85,
            current.disk_usage_percent > 95,
            current.available_memory_gb < 1.0,
            current.load_avg[0] > current.cpu_count * 2 if current.load_avg else False
        ]

        return any(conditions)

    def get_optimal_concurrency(self) -> int:
        """Calculate optimal concurrency based on system resources"""
        if not self.resource_history:
            resources = self.get_current_resources()
        else:
            resources = self.resource_history[-1]

        # Base concurrency on CPU cores and available memory
        cpu_based = max(1, resources.cpu_count - 1)  # Leave one core free
        memory_based = max(1, int(resources.available_memory_gb / 2))  # 2GB per task

        # Conservative approach - use minimum
        optimal = min(cpu_based, memory_based, 4)  # Cap at 4 for stability

        # Reduce if system is under load
        if resources.cpu_percent > 70:
            optimal = max(1, optimal - 1)

        if resources.memory_percent > 70:
            optimal = max(1, optimal - 1)

        return optimal


class TaskExecutor:
    """Executes individual tasks using containerized execution"""

    def __init__(self, task_id: str, worktree_path: Path, prompt_file: str, task_context: Optional[Dict] = None):
        self.task_id = task_id
        self.worktree_path = worktree_path
        self.prompt_file = prompt_file
        self.task_context = task_context or {}
        self.process: Optional[subprocess.Popen] = None  # Kept for fallback compatibility
        self.start_time: Optional[datetime] = None
        self.result: Optional[ExecutionResult] = None
        self.prompt_generator = PromptGenerator()

        # CRITICAL FIX #167: Initialize ContainerManager for Docker-based execution
        if CONTAINER_EXECUTION_AVAILABLE:
            try:
                container_config = ContainerConfig(
                    image="claude-orchestrator:latest",
                    cpu_limit="2.0",
                    memory_limit="4g",
                    timeout_seconds=self.task_context.get('timeout_seconds', 3600),
                    # CRITICAL: Proper Claude CLI flags with automation support
                    claude_flags=[
                        "--dangerously-skip-permissions",  # Essential for automation
                        "--verbose",
                        f"--max-turns={self.task_context.get('max_turns', 50)}",
                        "--output-format=json"
                    ]
                )
                self.container_manager = ContainerManager(container_config)
            except (RuntimeError, ImportError) as e:
                logger.info(f"Container manager unavailable for task {task_id}: {e}")
                logger.info("Will use subprocess fallback")
                self.container_manager = None
        else:
            self.container_manager = None

    def execute(self, timeout: Optional[int] = None) -> ExecutionResult:
        """Execute the task using REAL subprocess execution with WorkflowManager delegation"""
        self.start_time = datetime.now()

        # CRITICAL FIX: Use real subprocess execution as primary method
        # This ensures proper WorkflowManager delegation and real parallel execution
        print(f"🚀 Starting REAL subprocess task execution: {self.task_id}")
        print(f"📋 Task will be delegated to WorkflowManager for governance compliance")

        # Always use subprocess execution for real WorkflowManager delegation
        return self._execute_subprocess_fallback(timeout)

    def _generate_workflow_prompt(self) -> str:
        """Generate WorkflowManager-specific prompt with full context"""
        try:
            # Create context for prompt generation
            prompt_context = self.prompt_generator.create_context_from_task(
                task={
                    'id': self.task_id,
                    'name': self.task_context.get('name', self.task_id),
                    'dependencies': self.task_context.get('dependencies', []),
                    'target_files': self.task_context.get('target_files', []),
                    'requirements': self.task_context.get('requirements', {})
                },
                original_prompt_path=self.prompt_file,
                phase_focus=self.task_context.get('phase_focus')
            )

            # Generate the workflow prompt in the worktree
            workflow_prompt = self.prompt_generator.generate_workflow_prompt(
                prompt_context,
                self.worktree_path
            )

            print(f"📝 Generated WorkflowManager prompt: {workflow_prompt}")
            return workflow_prompt

        except Exception as e:
            print(f"⚠️  Warning: Failed to generate WorkflowManager prompt: {e}")
            return self.prompt_file

    def _progress_callback(self, task_id: str, result):
        """Progress callback for containerized execution"""
        print(f"📊 Task progress: {task_id}, status={result.status}")

    def _convert_container_result(self, container_result: 'ContainerResult') -> ExecutionResult:
        """Convert ContainerResult to ExecutionResult for compatibility"""
        return ExecutionResult(
            task_id=container_result.task_id,
            task_name=self.task_context.get('name', container_result.task_id),
            status=container_result.status,
            start_time=container_result.start_time,
            end_time=container_result.end_time,
            duration=container_result.duration,
            exit_code=container_result.exit_code,
            stdout=container_result.stdout,
            stderr=container_result.stderr,
            output_file=None,  # ContainerResult doesn't have this field
            error_message=container_result.error_message,
            resource_usage=container_result.resource_usage
        )

    def _execute_subprocess_fallback(self, timeout: Optional[int] = None) -> ExecutionResult:
        """REAL subprocess execution with WorkflowManager delegation (FIXED)"""
        # Prepare output files
        output_dir = self.worktree_path / "results"
        output_dir.mkdir(exist_ok=True)

        stdout_file = output_dir / f"{self.task_id}_stdout.log"
        stderr_file = output_dir / f"{self.task_id}_stderr.log"
        json_output_file = output_dir / f"{self.task_id}_output.json"

        print(f"📄 Setting up WorkflowManager delegation for task: {self.task_id}")

        # CRITICAL FIX: MANDATORY WorkflowManager delegation for governance compliance
        # Create task context file for WorkflowManager
        task_context_file = output_dir / f"{self.task_id}_context.json"
        task_context_data = {
            "task_id": self.task_id,
            "task_name": self.task_context.get('task_name', self.task_id),
            "original_prompt_file": self.prompt_file,
            "worktree_path": str(self.worktree_path),
            "orchestrator_context": {
                "parallel_execution": True,
                "subprocess_mode": True,
                "governance_delegation": True
            },
            "requirements": self.task_context.get('requirements', {})
        }

        with open(task_context_file, 'w') as f:
            json.dump(task_context_data, f, indent=2)

        # FIXED: Proper WorkflowManager delegation command
        # This ensures ALL 11 workflow phases are executed
        claude_cmd = [
            "claude",
            "-p", "/agent:workflow-manager",  # MANDATORY: Delegate to WorkflowManager
            "--dangerously-skip-permissions",  # Enable automation without user confirmation
            "--verbose",  # Verbose output for debugging
            f"--max-turns={self.task_context.get('max_turns', 50)}",  # Sufficient for workflow phases
            "--output-format", "json"  # Structured JSON output for parsing
        ]

        print(f"🚀 Starting REAL subprocess with WorkflowManager delegation: {' '.join(claude_cmd)}")
        print(f"📂 Working directory: {self.worktree_path}")
        print(f"📋 Task context saved to: {task_context_file}")

        stdout_content = ""
        stderr_content = ""
        exit_code = None
        error_message = None

        # Use SubprocessManager for proper subprocess handling
        try:
            from .subprocess_manager import SubprocessManager
        except ImportError:
            from subprocess_manager import SubprocessManager

        subprocess_manager = SubprocessManager(str(self.worktree_path.parent))

        print(f"🔧 Using SubprocessManager for real subprocess execution")

        try:
            # Spawn real WorkflowManager subprocess
            self.process = subprocess_manager.spawn_workflow_manager(
                task_id=self.task_id,
                worktree_path=self.worktree_path,
                original_prompt=self.prompt_file,
                task_context=self.task_context
            )

            print(f"✅ Real subprocess started: PID {self.process.pid}")

            # Wait for completion with timeout using SubprocessManager
            stdout_content, stderr_content, exit_code = subprocess_manager.wait_for_process(
                self.task_id,
                timeout=timeout
            )

            # Check if timeout occurred (SubprocessManager returns -1 for timeout)
            if exit_code == -1 and "timed out" in stderr_content:
                error_message = f"Task timed out after {timeout} seconds"

            # Save outputs to files
            with open(stdout_file, 'w') as f:
                f.write(stdout_content)

            with open(stderr_file, 'w') as f:
                f.write(stderr_content)

            # Try to parse JSON output if available
            output_file_path = None
            if stdout_content.strip():
                try:
                    json_data = json.loads(stdout_content)
                    with open(json_output_file, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    output_file_path = str(json_output_file)
                except json.JSONDecodeError:
                    pass  # Not JSON output, that's okay

        except FileNotFoundError:
            error_message = "Claude CLI not found - please ensure it's installed and in PATH"
            exit_code = -2
            stderr_content = error_message

        except Exception as e:
            error_message = f"Unexpected error during execution: {str(e)}"
            exit_code = -3
            stderr_content = error_message

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Determine status
        if error_message and "timed out" in error_message:
            status = "timeout"
        elif exit_code == 0:
            status = "success"
        elif exit_code is None:
            status = "cancelled"
        else:
            status = "failed"

        # Get resource usage (approximate)
        resource_usage = self._get_resource_usage()

        self.result = ExecutionResult(
            task_id=self.task_id,
            task_name=self.task_id,  # Will be updated by caller
            status=status,
            start_time=self.start_time,
            end_time=end_time,
            duration=duration,
            exit_code=exit_code,
            stdout=stdout_content,
            stderr=stderr_content,
            output_file=output_file_path,
            error_message=error_message,
            resource_usage=resource_usage
        )

        print(f"✅ Subprocess task completed: {self.task_id}, status={status} (exit code: {exit_code})")
        return self.result

    def cancel(self):
        """Cancel the running task"""
        if self.process and self.process.poll() is None:
            print(f"🛑 Cancelling task {self.task_id}")
            try:
                self.process.terminate()
                # Give it a moment to terminate gracefully
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                print(f"⚠️  Error cancelling task {self.task_id}: {e}")

    def _get_resource_usage(self) -> Dict[str, float]:
        """Get approximate resource usage for the task"""
        if not self.process:
            return {'cpu_time': 0.0, 'memory_mb': 0.0}

        try:
            proc = psutil.Process(self.process.pid)
            cpu_times = proc.cpu_times()
            memory_info = proc.memory_info()

            return {
                'cpu_time': cpu_times.user + cpu_times.system,
                'memory_mb': memory_info.rss / (1024 * 1024)
            }
        except (psutil.NoSuchProcess, AttributeError):
            return {'cpu_time': 0.0, 'memory_mb': 0.0}


class ExecutionEngine:
    """Main execution engine for parallel task management with containerized execution"""

    def __init__(self, max_concurrent: Optional[int] = None, default_timeout: int = 3600):
        self.max_concurrent = max_concurrent or self._get_default_concurrency()
        self.default_timeout = default_timeout
        self.resource_monitor = ResourceMonitor()
        self.active_executors: Dict[str, TaskExecutor] = {}
        self.results: Dict[str, ExecutionResult] = {}
        self.execution_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()

        # CRITICAL FIX #167: Initialize ContainerManager for true parallel containerized execution
        if CONTAINER_EXECUTION_AVAILABLE:
            print("🐳 Initializing containerized execution engine...")
            try:
                container_config = ContainerConfig(
                    image="claude-orchestrator:latest",
                    cpu_limit="2.0",
                    memory_limit="4g",
                    timeout_seconds=default_timeout,
                    claude_flags=[
                        "--dangerously-skip-permissions",  # CRITICAL for automation
                        "--verbose",
                        "--max-turns=50",
                        "--output-format=json"
                    ]
                )
                self.container_manager = ContainerManager(container_config)
                self.execution_mode = "containerized"
            except (RuntimeError, ImportError) as e:
                print(f"⚠️  Container manager unavailable: {e}")
                print("⚠️  Using subprocess fallback mode")
                self.container_manager = None
                self.execution_mode = "subprocess"
        else:
            print("⚠️  Docker not available - using subprocess fallback mode")
            self.container_manager = None
            self.execution_mode = "subprocess"

        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_execution_time': 0.0,
            'parallel_execution_time': 0.0,
            'execution_mode': self.execution_mode,  # Track execution mode
            'containerized_tasks': 0,
            'subprocess_tasks': 0
        }

    def _get_default_concurrency(self) -> int:
        """Get default concurrency based on system resources"""
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Conservative defaults
        cpu_based = max(1, cpu_count - 1)
        memory_based = max(1, int(memory_gb / 2))

        return min(cpu_based, memory_based, 4)

    def execute_tasks_parallel(
        self,
        tasks: List[Dict],
        worktree_manager,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ExecutionResult]:
        """Execute multiple tasks in parallel using containerized execution when possible"""

        if not tasks:
            print("📝 No tasks to execute")
            return {}

        print(f"🚀 Starting parallel execution of {len(tasks)} tasks")
        print(f"   Execution mode: {self.execution_mode}")
        print(f"   Max concurrent: {self.max_concurrent}")

        # CRITICAL FIX #167: Use ContainerManager for true parallel containerized execution
        if self.container_manager and CONTAINER_EXECUTION_AVAILABLE:
            print("🐳 Using containerized parallel execution...")
            return self._execute_tasks_containerized(tasks, worktree_manager, progress_callback)
        else:
            print("🔧 Using subprocess parallel execution...")
            return self._execute_tasks_subprocess(tasks, worktree_manager, progress_callback)

    def _execute_tasks_containerized(
        self,
        tasks: List[Dict],
        worktree_manager,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ExecutionResult]:
        """Execute tasks using ContainerManager for true containerized parallel execution"""

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        # Reset statistics
        self.stats['total_tasks'] = len(tasks)
        self.stats['completed_tasks'] = 0
        self.stats['failed_tasks'] = 0
        self.stats['cancelled_tasks'] = 0
        self.stats['containerized_tasks'] = len(tasks)

        execution_start = datetime.now()

        try:
            # Prepare container tasks
            container_tasks = []
            for task in tasks:
                task_id = task['id']
                worktree_info = worktree_manager.get_worktree(task_id)

                if not worktree_info:
                    print(f"❌ No worktree found for task: {task_id}")
                    continue

                container_task = {
                    'id': task_id,
                    'worktree_path': str(worktree_info.worktree_path),
                    'prompt_file': task.get('prompt_file', f"prompts/{task_id}.md"),
                    'context': {
                        'task_name': task.get('name', task_id),
                        'working_directory': str(worktree_info.worktree_path),
                        'timeout_seconds': self.default_timeout,
                        'max_turns': task.get('max_turns', 50)
                    }
                }
                container_tasks.append(container_task)

            if not container_tasks:
                print("❌ No valid container tasks created")
                return {}

            # Execute with ContainerManager
            print(f"🐳 Executing {len(container_tasks)} tasks in containers...")
            container_results = self.container_manager.execute_parallel_tasks(
                container_tasks,
                max_parallel=self.max_concurrent,
                progress_callback=self._container_progress_callback
            )

            # Convert container results to execution results
            results = {}
            for task_id, container_result in container_results.items():
                results[task_id] = self._convert_container_to_execution_result(container_result)

                # Update statistics
                if results[task_id].status == 'success':
                    self.stats['completed_tasks'] += 1
                elif results[task_id].status == 'failed':
                    self.stats['failed_tasks'] += 1
                elif results[task_id].status == 'cancelled':
                    self.stats['cancelled_tasks'] += 1

                # Progress callback
                if progress_callback:
                    progress_callback(self.stats['completed_tasks'] + self.stats['failed_tasks'],
                                    self.stats['total_tasks'], results[task_id])

            # Update statistics
            execution_end = datetime.now()
            self.stats['parallel_execution_time'] = (execution_end - execution_start).total_seconds()

            # Calculate total sequential time estimate
            self.stats['total_execution_time'] = sum(
                result.duration for result in results.values() if result.duration
            )

            # Print summary
            self._print_execution_summary()

            return results

        finally:
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()

    def _execute_tasks_subprocess(
        self,
        tasks: List[Dict],
        worktree_manager,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, ExecutionResult]:
        """Execute tasks using subprocess (original implementation)"""

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        # Reset statistics
        self.stats['total_tasks'] = len(tasks)
        self.stats['completed_tasks'] = 0
        self.stats['failed_tasks'] = 0
        self.stats['cancelled_tasks'] = 0

        execution_start = datetime.now()

        try:
            # Create executors for all tasks
            executors = []
            for task in tasks:
                task_id = task['id']
                worktree_info = worktree_manager.get_worktree(task_id)

                if not worktree_info:
                    print(f"❌ No worktree found for task: {task_id}")
                    continue

                prompt_file = task.get('prompt_file', f"prompts/{task_id}.md")

                executor = TaskExecutor(
                    task_id=task_id,
                    worktree_path=worktree_info.worktree_path,
                    prompt_file=prompt_file,
                    task_context=task  # Pass full task context for prompt generation
                )

                executors.append(executor)
                self.active_executors[task_id] = executor

            if not executors:
                print("❌ No valid executors created")
                return {}

            # Execute tasks with controlled concurrency
            results = self._execute_with_concurrency_control(
                executors, progress_callback
            )

            # Update statistics
            execution_end = datetime.now()
            self.stats['parallel_execution_time'] = (execution_end - execution_start).total_seconds()

            # Calculate total sequential time estimate
            self.stats['total_execution_time'] = sum(
                result.duration for result in results.values() if result.duration
            )

            # Print summary
            self._print_execution_summary()

            return results

        finally:
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()

            # Clean up active executors
            self.active_executors.clear()

    def _execute_with_concurrency_control(
        self,
        executors: List[TaskExecutor],
        progress_callback: Optional[Callable]
    ) -> Dict[str, ExecutionResult]:
        """Execute tasks with REAL subprocess parallel execution"""

        results = {}
        completed = 0
        total = len(executors)

        print(f"🚀 Starting REAL parallel subprocess execution for {total} tasks")
        print(f"🔧 Each task will spawn actual Claude CLI subprocess")

        # Start all subprocess executions in parallel
        running_processes = {}

        for task_executor in executors:
            print(f"🏁 Starting subprocess for task: {task_executor.task_id}")

            # Start the subprocess execution (this is now REAL subprocess spawning)
            try:
                # This will spawn the actual Claude CLI subprocess
                result_future = threading.Thread(
                    target=self._execute_single_task_threaded,
                    args=(task_executor, results, progress_callback, completed, total)
                )
                result_future.start()
                running_processes[task_executor.task_id] = {
                    'thread': result_future,
                    'task_executor': task_executor,
                    'start_time': datetime.now()
                }

            except Exception as e:
                print(f"❌ Failed to start subprocess for task {task_executor.task_id}: {e}")
                results[task_executor.task_id] = self._create_failed_result(task_executor.task_id, str(e))
                self.stats['failed_tasks'] += 1

        # Wait for all subprocesses to complete
        print(f"⏳ Waiting for {len(running_processes)} subprocess executions to complete...")

        for task_id, process_info in running_processes.items():
            try:
                # Wait for thread to complete (which waits for subprocess to complete)
                process_info['thread'].join(timeout=self.default_timeout)

                if process_info['thread'].is_alive():
                    print(f"⏰ Task {task_id} timed out, attempting to cancel...")
                    # Cancel the subprocess if it's still running
                    task_executor = process_info['task_executor']
                    if hasattr(task_executor, 'process') and task_executor.process:
                        task_executor.cancel()

                    # Create timeout result
                    results[task_id] = self._create_timeout_result(task_id)
                    self.stats['failed_tasks'] += 1

            except Exception as e:
                print(f"❌ Error waiting for task {task_id}: {e}")
                results[task_id] = self._create_failed_result(task_id, str(e))
                self.stats['failed_tasks'] += 1

        print(f"✅ All {total} subprocess executions completed")
        return results

    def _execute_single_task_threaded(self, task_executor: TaskExecutor, results: dict,
                                    progress_callback: Optional[Callable], completed: int, total: int):
        """Execute single task in thread (which spawns real subprocess)"""
        try:
            # This calls the REAL subprocess execution method
            result = task_executor.execute(timeout=self.default_timeout)
            results[task_executor.task_id] = result

            # Update statistics
            if result.status == 'success':
                self.stats['completed_tasks'] += 1
            elif result.status == 'failed':
                self.stats['failed_tasks'] += 1
            elif result.status == 'cancelled':
                self.stats['cancelled_tasks'] += 1

            # Progress callback
            if progress_callback:
                progress_callback(len(results), total, result)

            print(f"✅ Task {task_executor.task_id} subprocess completed: {result.status}")

        except Exception as e:
            print(f"❌ Task {task_executor.task_id} subprocess failed: {e}")
            results[task_executor.task_id] = self._create_failed_result(task_executor.task_id, str(e))
            self.stats['failed_tasks'] += 1

    def _create_failed_result(self, task_id: str, error_message: str) -> ExecutionResult:
        """Create a failed execution result"""
        return ExecutionResult(
            task_id=task_id,
            task_name=task_id,
            status='failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            exit_code=-1,
            stdout="",
            stderr=error_message,
            output_file=None,
            error_message=error_message,
            resource_usage={'cpu_time': 0.0, 'memory_mb': 0.0}
        )

    def _create_timeout_result(self, task_id: str) -> ExecutionResult:
        """Create a timeout execution result"""
        return ExecutionResult(
            task_id=task_id,
            task_name=task_id,
            status='timeout',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=float(self.default_timeout),
            exit_code=-1,
            stdout="",
            stderr="Task execution timed out",
            output_file=None,
            error_message="Task execution timed out",
            resource_usage={'cpu_time': 0.0, 'memory_mb': 0.0}
        )

    def _execute_single_task(self, task_executor: TaskExecutor) -> ExecutionResult:
        """Execute a single task (runs in separate process)"""
        try:
            return task_executor.execute(timeout=self.default_timeout)
        except Exception as e:
            # Create error result if execution fails
            return ExecutionResult(
                task_id=task_executor.task_id,
                task_name=task_executor.task_id,
                status='failed',
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0.0,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                output_file=None,
                error_message=str(e),
                resource_usage={'cpu_time': 0.0, 'memory_mb': 0.0}
            )

    def cancel_all_tasks(self):
        """Cancel all running tasks"""
        print("🛑 Cancelling all running tasks...")

        self.stop_event.set()

        for task_id, executor in self.active_executors.items():
            executor.cancel()

        print("✅ All tasks cancelled")

    def get_execution_status(self) -> Dict:
        """Get current execution status"""
        resource_status = self.resource_monitor.get_current_resources()

        return {
            'active_tasks': len(self.active_executors),
            'max_concurrent': self.max_concurrent,
            'system_resources': asdict(resource_status),
            'system_overloaded': self.resource_monitor.is_system_overloaded(),
            'optimal_concurrency': self.resource_monitor.get_optimal_concurrency(),
            'statistics': self.stats.copy()
        }

    def _print_execution_summary(self):
        """Print execution summary"""
        print("\n📊 Execution Summary:")
        print(f"   Total tasks: {self.stats['total_tasks']}")
        print(f"   Completed: {self.stats['completed_tasks']}")
        print(f"   Failed: {self.stats['failed_tasks']}")
        print(f"   Cancelled: {self.stats['cancelled_tasks']}")

        if self.stats['parallel_execution_time'] > 0:
            print(f"   Parallel execution time: {self.stats['parallel_execution_time']:.1f}s")

            if self.stats['total_execution_time'] > 0:
                speedup = self.stats['total_execution_time'] / self.stats['parallel_execution_time']
                print(f"   Estimated sequential time: {self.stats['total_execution_time']:.1f}s")
                print(f"   Speed improvement: {speedup:.2f}x")

        # Resource usage summary
        if self.resource_monitor.resource_history:
            avg_cpu = sum(r.cpu_percent for r in self.resource_monitor.resource_history) / len(self.resource_monitor.resource_history)
            avg_memory = sum(r.memory_percent for r in self.resource_monitor.resource_history) / len(self.resource_monitor.resource_history)
            print(f"   Average CPU usage: {avg_cpu:.1f}%")
            print(f"   Average memory usage: {avg_memory:.1f}%")

    def save_results(self, output_file: str):
        """Save execution results to file"""
        results_data = {
            'execution_summary': {
                'timestamp': datetime.now().isoformat(),
                'statistics': self.stats,
                'system_resources': asdict(self.resource_monitor.get_current_resources()),
                'execution_mode': self.execution_mode
            },
            'task_results': {
                task_id: asdict(result) for task_id, result in self.results.items()
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"💾 Execution results saved to: {output_file}")

    def _container_progress_callback(self, task_id: str, result):
        """Progress callback for containerized execution"""
        print(f"🐳 Container task progress: {task_id}, status={result.status}")

    def _convert_container_to_execution_result(self, container_result: 'ContainerResult') -> ExecutionResult:
        """Convert ContainerResult to ExecutionResult for compatibility"""
        return ExecutionResult(
            task_id=container_result.task_id,
            task_name=container_result.task_id,  # Use task_id as name
            status=container_result.status,
            start_time=container_result.start_time,
            end_time=container_result.end_time,
            duration=container_result.duration,
            exit_code=container_result.exit_code,
            stdout=container_result.stdout,
            stderr=container_result.stderr,
            output_file=None,  # ContainerResult doesn't have this field
            error_message=container_result.error_message,
            resource_usage=container_result.resource_usage
        )


def main():
    """CLI entry point for ExecutionEngine"""
    import argparse

    parser = argparse.ArgumentParser(description="Execute tasks in parallel")
    parser.add_argument("--max-concurrent", type=int, help="Maximum concurrent tasks")
    parser.add_argument("--timeout", type=int, default=3600, help="Task timeout in seconds")
    parser.add_argument("--tasks-file", required=True, help="JSON file containing task definitions")
    parser.add_argument("--output", default="execution_results.json", help="Output file for results")

    args = parser.parse_args()

    # Load tasks
    try:
        with open(args.tasks_file, 'r') as f:
            tasks_data = json.load(f)
            tasks = tasks_data.get('tasks', [])
    except Exception as e:
        print(f"❌ Failed to load tasks file: {e}")
        return 1

    # Create execution engine
    engine = ExecutionEngine(
        max_concurrent=args.max_concurrent,
        default_timeout=args.timeout
    )

    # Mock worktree manager for CLI usage
    class MockWorktreeManager:
        def get_worktree(self, task_id):
            from collections import namedtuple
            WorktreeInfo = namedtuple('WorktreeInfo', ['worktree_path'])
            return WorktreeInfo(worktree_path=Path('.'))

    try:
        # Execute tasks
        results = engine.execute_tasks_parallel(
            tasks,
            MockWorktreeManager(),
            progress_callback=lambda completed, total, result: print(
                f"Progress: {completed}/{total} - {result.task_id}: {result.status}"
            )
        )

        # Save results
        engine.save_results(args.output)

        # Return appropriate exit code
        failed_count = sum(1 for r in results.values() if r.status == 'failed')
        return 1 if failed_count > 0 else 0

    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by user")
        engine.cancel_all_tasks()
        return 130

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
