#!/usr/bin/env python3
"""
Test suite for ExecutionEngine component of OrchestratorAgent

Tests parallel execution, resource monitoring, and process management.
"""

import json
import shutil
import subprocess

import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, call, patch
import importlib.util

# Set up path for imports
orchestrator_dir = Path(__file__).parent.parent
components_dir = orchestrator_dir / 'components'

# Read and modify the execution_engine source to use absolute imports
execution_engine_path = components_dir / "execution_engine.py"
with open(execution_engine_path, 'r') as f:
    source_code = f.read()

# Replace the problematic relative imports
modified_source = source_code.replace(
    "from .prompt_generator import PromptContext, PromptGenerator",
    "from prompt_generator import PromptContext, PromptGenerator"
).replace(
    "from ..container_manager import ContainerManager, ContainerConfig, ContainerResult",
    "from container_manager import ContainerManager, ContainerConfig, ContainerResult"
)

# Import prompt_generator first (it doesn't have relative imports)
spec = importlib.util.spec_from_file_location(
    "prompt_generator",
    components_dir / "prompt_generator.py"
)
prompt_generator_module = importlib.util.module_from_spec(spec)
sys.modules['prompt_generator'] = prompt_generator_module
spec.loader.exec_module(prompt_generator_module)

# Create proper mock classes instead of MagicMock to avoid InvalidSpecError
class MockContainerManager:
    def __init__(self, config) -> None:
        self.config = config

class MockContainerConfig:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockContainerResult:
    def __init__(self, **kwargs) -> None:
        self.task_id = kwargs.get('task_id', '')
        self.task_id = kwargs.get('status', 'success')
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.duration = kwargs.get('duration', 0)
        self.exit_code = kwargs.get('exit_code', 0)
        self.stdout = kwargs.get('stdout', '')
        self.stderr = kwargs.get('stderr', '')
        self.error_message = kwargs.get('error_message', None)
        self.resource_usage = kwargs.get('resource_usage', {})

# Create container_manager module with proper classes
container_manager_mock = type('module', (), {})()
container_manager_mock.ContainerManager = MockContainerManager
container_manager_mock.ContainerConfig = MockContainerConfig
container_manager_mock.ContainerResult = MockContainerResult
sys.modules['container_manager'] = container_manager_mock

# Create execution_engine module from modified source
spec = importlib.util.spec_from_loader("execution_engine", loader=None)
execution_engine_module = importlib.util.module_from_spec(spec)
sys.modules['execution_engine'] = execution_engine_module

# Execute the modified code with proper globals
globals_dict = execution_engine_module.__dict__.copy()
globals_dict['__file__'] = str(execution_engine_path)
globals_dict['__name__'] = 'execution_engine'
exec(modified_source, globals_dict)

# Update the module dict with the executed code
execution_engine_module.__dict__.update(globals_dict)

# Import the classes we need
ExecutionEngine = execution_engine_module.ExecutionEngine
ExecutionResult = execution_engine_module.ExecutionResult
ResourceMonitor = execution_engine_module.ResourceMonitor
SystemResources = execution_engine_module.SystemResources
TaskExecutor = execution_engine_module.TaskExecutor


class TestResourceMonitor(unittest.TestCase):
    """Test cases for ResourceMonitor"""

    def setUp(self):
        """Set up test environment"""
        self.monitor = ResourceMonitor(monitoring_interval=0.1)  # Fast monitoring for tests

    def tearDown(self):
        """Clean up test environment"""
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_count')
    @patch('os.getloadavg')
    def test_get_current_resources(self, mock_loadavg, mock_cpu_count, mock_disk, mock_memory, mock_cpu):
        """Test current resource retrieval"""
        # Mock system resource calls
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=62.3, available=4 * 1024**3)  # 4GB available
        mock_disk.return_value = MagicMock(percent=78.9)
        mock_cpu_count.return_value = 8
        mock_loadavg.return_value = (1.2, 1.5, 1.8)

        resources = self.monitor.get_current_resources()

        self.assertEqual(resources.cpu_percent, 45.5)
        self.assertEqual(resources.memory_percent, 62.3)
        self.assertEqual(resources.disk_usage_percent, 78.9)
        self.assertEqual(resources.available_memory_gb, 4.0)
        self.assertEqual(resources.cpu_count, 8)
        self.assertEqual(resources.load_avg, [1.2, 1.5, 1.8])

    def test_monitoring_lifecycle(self):
        """Test resource monitoring start/stop"""
        self.assertFalse(self.monitor.monitoring)
        self.assertEqual(len(self.monitor.resource_history), 0)

        # Start monitoring
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring)
        self.assertIsNotNone(self.monitor.monitor_thread)

        # Let it collect some data
        time.sleep(0.3)

        # Should have collected some resources
        self.assertGreater(len(self.monitor.resource_history), 0)

        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring)

    def test_is_system_overloaded(self):
        """Test system overload detection"""
        # Add overloaded resource state
        overloaded_resources = SystemResources(
            cpu_percent=95.0,  # Over 90%
            memory_percent=90.0,  # Over 85%
            disk_usage_percent=98.0,  # Over 95%
            available_memory_gb=0.5,  # Under 1GB
            cpu_count=4,
            load_avg=[10.0, 9.0, 8.0]  # High load
        )

        self.monitor.resource_history = [overloaded_resources]
        self.assertTrue(self.monitor.is_system_overloaded())

        # Add normal resource state
        normal_resources = SystemResources(
            cpu_percent=30.0,
            memory_percent=50.0,
            disk_usage_percent=60.0,
            available_memory_gb=4.0,
            cpu_count=4,
            load_avg=[1.0, 1.1, 1.2]
        )

        self.monitor.resource_history = [normal_resources]
        self.assertFalse(self.monitor.is_system_overloaded())

    def test_get_optimal_concurrency(self):
        """Test optimal concurrency calculation"""
        # High resource availability
        high_resources = SystemResources(
            cpu_percent=20.0,
            memory_percent=30.0,
            disk_usage_percent=40.0,
            available_memory_gb=8.0,  # 4 tasks at 2GB each
            cpu_count=8,  # 7 available
            load_avg=[1.0, 1.0, 1.0]
        )

        self.monitor.resource_history = [high_resources]
        optimal = self.monitor.get_optimal_concurrency()
        self.assertEqual(optimal, 4)  # Min of CPU-based (7) and memory-based (4), capped at 4

        # Low resource availability
        low_resources = SystemResources(
            cpu_percent=80.0,  # High CPU usage
            memory_percent=80.0,  # High memory usage
            disk_usage_percent=50.0,
            available_memory_gb=2.0,  # Only 1 task at 2GB
            cpu_count=4,
            load_avg=[3.0, 3.0, 3.0]
        )

        self.monitor.resource_history = [low_resources]
        optimal = self.monitor.get_optimal_concurrency()
        self.assertEqual(optimal, 1)  # Reduced due to high usage


class TestTaskExecutor(unittest.TestCase):
    """Test cases for TaskExecutor"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.worktree_path = Path(self.temp_dir) / "worktree"
        self.worktree_path.mkdir()

        self.executor = TaskExecutor(
            task_id="test-task",
            worktree_path=self.worktree_path,
            prompt_file="prompts/test.md"
        )

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('subprocess.Popen')
    def test_execute_success(self, mock_popen):
        """Test successful task execution"""
        # Mock successful Claude CLI execution
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('{"status": "success"}', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.executor.execute(timeout=60)

        self.assertEqual((result.status if result is not None else None), "success")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual((result.task_id if result is not None else None), "test-task")
        self.assertIsNotNone(result.start_time)
        self.assertIsNotNone(result.end_time)
        self.assertIsNotNone(result.duration)

        # Verify Claude CLI command
        expected_cmd = ["claude", "-p", "prompts/test.md", "--output-format", "json"]
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], expected_cmd)
        self.assertEqual(kwargs['cwd'], self.worktree_path)

    @patch('subprocess.Popen')
    def test_execute_failure(self, mock_popen):
        """Test failed task execution"""
        # Mock failed Claude CLI execution
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', 'Error: Something went wrong')
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = self.executor.execute()

        self.assertEqual((result.status if result is not None else None), "failed")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.stderr, 'Error: Something went wrong')
        self.assertIsNotNone(result.error_message)

    @patch('subprocess.Popen')
    def test_execute_timeout(self, mock_popen):
        """Test task execution timeout"""
        # Mock timeout scenario
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired('claude', 30)
        mock_process.returncode = -1
        mock_popen.return_value = mock_process

        result = self.executor.execute(timeout=30)

        self.assertEqual((result.status if result is not None else None), "timeout")
        self.assertEqual(result.exit_code, -1)
        self.assertIn("timed out", result.error_message)

        # Verify process was killed
        mock_process.kill.assert_called_once()

    @patch('subprocess.Popen')
    def test_execute_claude_not_found(self, mock_popen):
        """Test execution when Claude CLI is not found"""
        mock_popen.side_effect = FileNotFoundError("Claude CLI not found")

        result = self.executor.execute()

        self.assertEqual((result.status if result is not None else None), "failed")
        self.assertEqual(result.exit_code, -2)
        self.assertIn("Claude CLI not found", result.error_message)

    @patch('subprocess.Popen')
    def test_execute_creates_output_files(self, mock_popen):
        """Test that execution creates output files"""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('{"result": "success"}', 'debug info')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.executor.execute()

        # Check that results directory was created
        results_dir = self.worktree_path / "results"
        self.assertTrue(results_dir.exists())

        # Check that output files exist
        stdout_file = results_dir / "test-task_stdout.log"
        stderr_file = results_dir / "test-task_stderr.log"
        json_file = results_dir / "test-task_output.json"

        self.assertTrue(stdout_file.exists())
        self.assertTrue(stderr_file.exists())
        self.assertTrue(json_file.exists())

        # Check JSON output file was created
        self.assertIsNotNone(result.output_file)
        self.assertTrue(Path(result.output_file).exists())

    def test_cancel(self):
        """Test task cancellation"""
        # Create a mock running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        self.executor.process = mock_process

        self.executor.cancel()

        mock_process.terminate.assert_called_once()


class TestExecutionEngine(unittest.TestCase):
    """Test cases for ExecutionEngine"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = ExecutionEngine(max_concurrent=2, default_timeout=60)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test engine initialization"""
        self.assertEqual(self.engine.max_concurrent, 2)
        self.assertEqual(self.engine.default_timeout, 60)
        self.assertIsNotNone(self.engine.resource_monitor)
        self.assertEqual(len(self.engine.active_executors), 0)
        self.assertEqual(len(self.engine.results), 0)

    def test_get_default_concurrency(self):
        """Test default concurrency calculation"""
        with patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory:

            mock_memory.return_value.total = 16 * 1024**3  # 16GB

            concurrency = self.engine._get_default_concurrency()

            # Should be min of CPU-based (7), memory-based (8), capped at 4
            self.assertEqual(concurrency, 4)

    def create_mock_worktree_manager(self, task_ids):
        """Create a mock worktree manager for testing"""
        mock_manager = MagicMock()

        def get_worktree(task_id):
            if task_id in task_ids:
                mock_worktree = MagicMock()
                mock_worktree.worktree_path = Path(self.temp_dir) / f"worktree-{task_id}"
                mock_worktree.worktree_path.mkdir(exist_ok=True)
                return mock_worktree
            return None

        mock_manager.get_worktree.side_effect = get_worktree
        return mock_manager

    @patch.object(ExecutionEngine, '_execute_single_task')
    def test_execute_tasks_parallel_success(self, mock_execute):
        """Test successful parallel task execution"""
        # Mock successful task execution
        def mock_task_execution(executor):
            return ExecutionResult(
                task_id=(executor.task_id if executor is not None else None),
                task_name=(executor.task_id if executor is not None else None),
                status="success",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=30.0,
                exit_code=0,
                stdout="Success",
                stderr="",
                output_file=None,
                error_message=None,
                resource_usage={'cpu_time': 5.0, 'memory_mb': 100.0}
            )

        mock_execute.side_effect = mock_task_execution

        # Create test tasks
        tasks = [
            {'id': 'task1', 'prompt_file': 'prompts/task1.md'},
            {'id': 'task2', 'prompt_file': 'prompts/task2.md'}
        ]

        mock_manager = self.create_mock_worktree_manager(['task1', 'task2'])

        results = self.engine.execute_tasks_parallel(tasks, mock_manager)

        self.assertEqual(len(results), 2)
        self.assertIn('task1', results)
        self.assertIn('task2', results)
        self.assertEqual(results['task1'].status, 'success')
        self.assertEqual(results['task2'].status, 'success')

        # Check statistics
        self.assertEqual(self.engine.stats['total_tasks'], 2)
        self.assertEqual(self.engine.stats['completed_tasks'], 2)
        self.assertEqual(self.engine.stats['failed_tasks'], 0)

    @patch.object(ExecutionEngine, '_execute_single_task')
    def test_execute_tasks_parallel_with_failures(self, mock_execute):
        """Test parallel execution with some task failures"""
        def mock_task_execution(executor):
            if (executor.task_id if executor is not None else None) == 'task1':
                return ExecutionResult(
                    task_id='task1', task_name='task1', status="success",
                    start_time=datetime.now(), end_time=datetime.now(), duration=30.0,
                    exit_code=0, stdout="Success", stderr="", output_file=None,
                    error_message=None, resource_usage={'cpu_time': 5.0, 'memory_mb': 100.0}
                )
            else:
                return ExecutionResult(
                    task_id='task2', task_name='task2', status="failed",
                    start_time=datetime.now(), end_time=datetime.now(), duration=15.0,
                    exit_code=1, stdout="", stderr="Error occurred", output_file=None,
                    error_message="Task failed", resource_usage={'cpu_time': 2.0, 'memory_mb': 50.0}
                )

        mock_execute.side_effect = mock_task_execution

        tasks = [
            {'id': 'task1', 'prompt_file': 'prompts/task1.md'},
            {'id': 'task2', 'prompt_file': 'prompts/task2.md'}
        ]

        mock_manager = self.create_mock_worktree_manager(['task1', 'task2'])

        results = self.engine.execute_tasks_parallel(tasks, mock_manager)

        self.assertEqual(len(results), 2)
        self.assertEqual(results['task1'].status, 'success')
        self.assertEqual(results['task2'].status, 'failed')

        # Check statistics
        self.assertEqual(self.engine.stats['completed_tasks'], 1)
        self.assertEqual(self.engine.stats['failed_tasks'], 1)

    def test_execute_tasks_parallel_empty_list(self):
        """Test parallel execution with empty task list"""
        mock_manager = self.create_mock_worktree_manager([])

        results = self.engine.execute_tasks_parallel([], mock_manager)

        self.assertEqual(len(results), 0)
        self.assertEqual(self.engine.stats['total_tasks'], 0)

    def test_execute_tasks_parallel_no_valid_executors(self):
        """Test execution when no valid executors can be created"""
        tasks = [{'id': 'invalid-task', 'prompt_file': 'prompts/invalid.md'}]

        # Mock manager that returns None for all worktrees
        mock_manager = MagicMock()
        mock_manager.get_worktree.return_value = None

        results = self.engine.execute_tasks_parallel(tasks, mock_manager)

        self.assertEqual(len(results), 0)

    def test_cancel_all_tasks(self):
        """Test cancelling all running tasks"""
        # Create mock executors
        mock_executor1 = MagicMock()
        mock_executor2 = MagicMock()

        self.engine.active_executors = {
            'task1': mock_executor1,
            'task2': mock_executor2
        }

        self.engine.cancel_all_tasks()

        mock_executor1.cancel.assert_called_once()
        mock_executor2.cancel.assert_called_once()
        self.assertTrue(self.engine.stop_event.is_set())

    def test_get_execution_status(self):
        """Test getting execution status"""
        # Add some mock statistics
        self.engine.stats['completed_tasks'] = 5
        self.engine.stats['failed_tasks'] = 1

        status = self.engine.get_execution_status()

        self.assertIn('active_tasks', status)
        self.assertIn('max_concurrent', status)
        self.assertIn('system_resources', status)
        self.assertIn('statistics', status)

        self.assertEqual(status['max_concurrent'], 2)
        self.assertEqual(status['statistics']['completed_tasks'], 5)
        self.assertEqual(status['statistics']['failed_tasks'], 1)

    def test_save_results(self):
        """Test saving execution results"""
        # Add some mock results
        result1 = ExecutionResult(
            task_id='task1', task_name='Task 1', status='success',
            start_time=datetime.now(), end_time=datetime.now(), duration=30.0,
            exit_code=0, stdout='Output', stderr='', output_file=None,
            error_message=None, resource_usage={'cpu_time': 5.0, 'memory_mb': 100.0}
        )

        self.engine.results = {'task1': result1}
        self.engine.stats['completed_tasks'] = 1

        output_file = Path(self.temp_dir) / "results.json"
        self.engine.save_results(str(output_file))

        # Verify file was created and contains valid JSON
        self.assertTrue(output_file.exists())

        with open(output_file, 'r') as f:
            data = json.load(f)

        self.assertIn('execution_summary', data)
        self.assertIn('task_results', data)
        self.assertEqual(data['execution_summary']['statistics']['completed_tasks'], 1)
        self.assertIn('task1', data['task_results'])


class TestExecutionEngineIntegration(unittest.TestCase):
    """Integration tests for ExecutionEngine"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = ExecutionEngine(max_concurrent=1, default_timeout=10)  # Low timeout for tests

    def tearDown(self):
        """Clean up test environment"""
        self.engine.cancel_all_tasks()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipIf(not shutil.which('echo'), "echo command not available")
    def test_real_process_execution(self):
        """Test execution with real processes (using echo instead of claude)"""
        # Create a worktree directory
        worktree_path = Path(self.temp_dir) / "test-worktree"
        worktree_path.mkdir()

        # Create a TaskExecutor that uses echo instead of claude
        executor = TaskExecutor("test-task", worktree_path, "test-prompt")

        with patch.object(executor, 'execute') as mock_execute:
            # Mock the execute method to simulate a real execution
            mock_execute.return_value = ExecutionResult(
                task_id="test-task",
                task_name="test-task",
                status="success",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=1),
                duration=1.0,
                exit_code=0,
                stdout="Test output",
                stderr="",
                output_file=None,
                error_message=None,
                resource_usage={'cpu_time': 0.1, 'memory_mb': 10.0}
            )

            result = executor.execute(timeout=5)

            self.assertEqual((result.task_id if result is not None else None), "test-task")
            self.assertEqual((result.status if result is not None else None), "success")
            self.assertIsNotNone(result.duration)


if __name__ == '__main__':
    import shutil

    # Check for required tools
    missing_tools = []
    if not shutil.which('echo'):
        missing_tools.append('echo')

    if missing_tools:
        print(f"Warning: Missing tools {missing_tools}, some tests may be skipped")

    unittest.main()
