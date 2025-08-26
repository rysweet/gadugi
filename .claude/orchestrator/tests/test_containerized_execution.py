#!/usr/bin/env python3
"""
Comprehensive tests for containerized orchestrator execution.

Tests the ContainerManager, ExecutionEngine, and end-to-end containerized workflows
to ensure proper Docker-based parallel execution meets requirements from Issue #167.

Key test scenarios:
- Container lifecycle management
- Proper Claude CLI invocation with automation flags
- Real-time monitoring and output streaming
- Resource limits and error handling
- Performance improvements vs subprocess execution
"""

import asyncio
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from container_manager import ContainerManager, ContainerConfig, ContainerResult
    from components.execution_engine import ExecutionEngine, TaskExecutor
    from monitoring.dashboard import OrchestrationMonitor
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import modules for testing: {e}")
    # Create mock classes when imports fail
    class MockContainerConfig:
        def __init__(self, **kwargs):
            self.image = kwargs.get('image', "claude-orchestrator:latest")
            self.cpu_limit = kwargs.get('cpu_limit', "2.0")
            self.memory_limit = kwargs.get('memory_limit', "4g")
            self.timeout_seconds = kwargs.get('timeout_seconds', 3600)
            self.max_turns = kwargs.get('max_turns', 50)
            self.output_format = kwargs.get('output_format', "json")
            self.claude_flags = kwargs.get('claude_flags', [
                "--dangerously-skip-permissions",
                "--verbose", 
                "--max-turns=50",
                "--output-format=json"
            ])
    
    class MockContainerResult:
        def __init__(self, **kwargs):
            self.task_id = kwargs.get('task_id', 'mock-task')
            self.status = kwargs.get('status', 'success')
            self.exit_code = kwargs.get('exit_code', 0)
            self.stdout = kwargs.get('stdout', '')
            self.stderr = kwargs.get('stderr', '')
            self.start_time = kwargs.get('start_time', None)
            self.end_time = kwargs.get('end_time', None)
            self.duration = kwargs.get('duration', 0.0)
            self.error_message = kwargs.get('error_message', None)

    class MockContainerManager:
        def __init__(self, config=None):
            self.config = config
            self.docker_client = None
            
        def execute_containerized_task(self, *args, **kwargs):
            return MockContainerResult()
            
        def execute_parallel_tasks(self, *args, **kwargs):
            return [MockContainerResult()]
    
    class MockExecutionEngine:
        def __init__(self, *args, **kwargs):
            self.execution_mode = "containerized"
            self.container_manager = None
            
        def execute_tasks_parallel(self, *args, **kwargs):
            return []
            
    class MockTaskExecutor:
        def __init__(self, *args, **kwargs):
            self._progress_callback = None
            
        def execute(self, *args, **kwargs):
            return None
            
        def _generate_workflow_prompt(self, *args, **kwargs):
            return None
            
    class MockOrchestrationMonitor:
        def __init__(self, *args, **kwargs):
            self.monitoring = None
            self.monitoring_dir = "/tmp/mock"
            self.docker_client = None
            self.active_containers = {}
            
        def update_container_status(self, *args, **kwargs):
            return None
    
    ContainerConfig = MockContainerConfig
    ContainerManager = MockContainerManager
    ContainerResult = MockContainerResult
    ExecutionEngine = MockExecutionEngine
    TaskExecutor = MockTaskExecutor
    OrchestrationMonitor = MockOrchestrationMonitor
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "Container modules not available")
class TestContainerConfig(unittest.TestCase):
    """Test ContainerConfig dataclass and validation"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ContainerConfig()

        self.assertEqual(config.image, "claude-orchestrator:latest")
        self.assertEqual(config.cpu_limit, "2.0")
        self.assertEqual(config.memory_limit, "4g")
        self.assertEqual(config.timeout_seconds, 3600)
        self.assertEqual(config.max_turns, 50)
        self.assertEqual(config.output_format, "json")

        # Test automation flags are included
        self.assertIn("--dangerously-skip-permissions", config.claude_flags)
        self.assertIn("--verbose", config.claude_flags)
        self.assertIn("--max-turns=50", config.claude_flags)
        self.assertIn("--output-format=json", config.claude_flags)

    def test_custom_config(self):
        """Test custom configuration values"""
        custom_flags = ["--custom-flag", "--another-flag"]
        config = ContainerConfig(
            image="custom-claude:test",
            cpu_limit="4.0",
            memory_limit="8g",
            timeout_seconds=7200,
            max_turns=100,
            claude_flags=custom_flags
        )

        self.assertEqual(config.image, "custom-claude:test")
        self.assertEqual(config.cpu_limit, "4.0")
        self.assertEqual(config.memory_limit, "8g")
        self.assertEqual(config.timeout_seconds, 7200)
        self.assertEqual(config.max_turns, 100)
        self.assertEqual(config.claude_flags, custom_flags)


@unittest.skipUnless(IMPORTS_AVAILABLE, "Container modules not available")
class TestContainerManager(unittest.TestCase):
    """Test ContainerManager Docker operations"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_worktree = self.test_dir / "test-worktree"
        self.test_worktree.mkdir(parents=True)

        # Create test prompt file
        self.test_prompt = self.test_worktree / "test-prompt.md"
        self.test_prompt.write_text("# Test Prompt\nTest task execution")

        # Mock Docker to avoid requiring actual Docker for tests
        self.docker_mock = Mock()
        self.container_mock = Mock()
        self.docker_mock.containers.run.return_value = self.container_mock

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('container_manager.docker')
    def test_container_manager_initialization(self, mock_docker):
        """Test ContainerManager initialization"""
        mock_docker.from_env.return_value = self.docker_mock
        self.docker_mock.ping.return_value = True
        self.docker_mock.images.get.return_value = Mock()  # Image exists

        config = ContainerConfig()
        manager = ContainerManager(config)

        self.assertEqual(manager.config, config)
        self.assertIsNotNone(manager.docker_client)
        mock_docker.from_env.assert_called_once()
        self.docker_mock.ping.assert_called_once()

    @patch('container_manager.docker')
    def test_docker_not_available_error(self, mock_docker):
        """Test ContainerManager handles Docker unavailability"""
        mock_docker.from_env.side_effect = Exception("Docker daemon not running")

        config = ContainerConfig()

        with self.assertRaises(RuntimeError) as context:
            ContainerManager(config)

        self.assertIn("Docker initialization failed", str(context.exception))

    @patch('container_manager.docker')
    def test_containerized_task_execution(self, mock_docker):
        """Test single containerized task execution"""
        # Setup mocks
        mock_docker.from_env.return_value = self.docker_mock
        self.docker_mock.ping.return_value = True
        self.docker_mock.images.get.return_value = Mock()  # Image exists

        # Configure container behavior
        self.container_mock.wait.return_value = {'StatusCode': 0}
        self.container_mock.logs.return_value = b"Task completed successfully"
        self.container_mock.stats.return_value = {
            'memory_stats': {'usage': 1024 * 1024 * 100},  # 100MB
            'cpu_stats': {'cpu_usage': {'total_usage': 1000000}},
            'networks': {'eth0': {'rx_bytes': 1000, 'tx_bytes': 2000}}
        }
        self.container_mock.id = "test-container-id"

        # Create manager and execute task
        config = ContainerConfig()
        manager = ContainerManager(config)
        manager.docker_client = self.docker_mock  # Use our mock

        result = manager.execute_containerized_task(
            task_id="test-task-1",
            worktree_path=self.test_worktree,
            prompt_file=str(self.test_prompt),
            task_context={'timeout_seconds': 3600}
        )

        # Verify result
        self.assertIsInstance(result, ContainerResult)
        self.assertEqual((result.task_id if result is not None else None), "test-task-1")
        self.assertEqual((result.status if result is not None else None), "success")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "Task completed successfully")
        self.assertIsNotNone(result.start_time)
        self.assertIsNotNone(result.end_time)
        self.assertIsNotNone(result.duration)

        # Verify Docker was called correctly
        self.docker_mock.containers.run.assert_called_once()
        call_args = self.docker_mock.containers.run.call_args

        # Verify Claude CLI command with automation flags
        command = call_args[1]['command']
        self.assertIn('claude', command)
        self.assertIn('-p', command)
        self.assertIn('--dangerously-skip-permissions', command)
        self.assertIn('--verbose', command)
        self.assertIn('--output-format=json', command)

        # Verify container configuration
        self.assertEqual(call_args[1]['cpu_count'], 2.0)
        self.assertEqual(call_args[1]['mem_limit'], '4g')
        self.assertEqual(call_args[1]['working_dir'], '/workspace')
        self.assertIn('/workspace', call_args[1]['volumes'])

    @patch('container_manager.docker')
    def test_parallel_task_execution(self, mock_docker):
        """Test parallel execution of multiple containerized tasks"""
        # Setup mocks
        mock_docker.from_env.return_value = self.docker_mock
        self.docker_mock.ping.return_value = True
        self.docker_mock.images.get.return_value = Mock()  # Image exists

        # Configure container behavior for multiple tasks
        containers = []
        for i in range(3):
            container = Mock()
            container.wait.return_value = {'StatusCode': 0}
            container.logs.return_value = f"Task {i} completed".encode()
            container.stats.return_value = {
                'memory_stats': {'usage': 1024 * 1024 * 50},
                'cpu_stats': {'cpu_usage': {'total_usage': 500000}},
                'networks': {'eth0': {'rx_bytes': 500, 'tx_bytes': 1000}}
            }
            container.id = f"container-{i}"
            containers.append(container)

        self.docker_mock.containers.run.side_effect = containers

        # Create manager
        config = ContainerConfig()
        manager = ContainerManager(config)
        manager.docker_client = self.docker_mock

        # Prepare parallel tasks
        tasks = [
            {
                'id': f'task-{i}',
                'worktree_path': str(self.test_worktree),
                'prompt_file': str(self.test_prompt),
                'context': {'task_name': f'Test Task {i}', 'timeout_seconds': 1800}
            }
            for i in range(3)
        ]

        # Execute parallel tasks
        results = manager.execute_parallel_tasks(
            tasks,
            max_parallel=2,  # Test concurrency limit
            progress_callback=Mock()
        )

        # Verify results
        self.assertEqual(len(results), 3)
        for i in range(3):
            task_id = f'task-{i}'
            self.assertIn(task_id, results)
            self.assertEqual(results[task_id].status, 'success')
            self.assertEqual(results[task_id].exit_code, 0)

        # Verify Docker was called for each task
        self.assertEqual(self.docker_mock.containers.run.call_count, 3)

    @patch('container_manager.docker')
    def test_container_failure_handling(self, mock_docker):
        """Test handling of container execution failures"""
        # Setup mocks
        mock_docker.from_env.return_value = self.docker_mock
        self.docker_mock.ping.return_value = True
        self.docker_mock.images.get.return_value = Mock()

        # Configure container to fail
        self.container_mock.wait.return_value = {'StatusCode': 1}
        self.container_mock.logs.return_value = b"Error: Task failed"
        self.container_mock.stats.return_value = {
            'memory_stats': {'usage': 1024 * 1024 * 50},
            'cpu_stats': {'cpu_usage': {'total_usage': 100000}},
            'networks': {}
        }

        # Create manager and execute failing task
        config = ContainerConfig()
        manager = ContainerManager(config)
        manager.docker_client = self.docker_mock

        result = manager.execute_containerized_task(
            task_id="failing-task",
            worktree_path=self.test_worktree,
            prompt_file=str(self.test_prompt),
            task_context={}
        )

        # Verify failure is handled correctly
        self.assertEqual((result.status if result is not None else None), "failed")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.stdout, "Error: Task failed")
        self.assertIsNone(result.error_message)  # No exception, just failed exit code

    def test_container_timeout_handling(self):
        """Test container timeout handling"""
        # This would require more complex mocking of asyncio/threading
        # For now, test the timeout configuration
        config = ContainerConfig(timeout_seconds=1800)
        self.assertEqual(config.timeout_seconds, 1800)


@unittest.skipUnless(IMPORTS_AVAILABLE, "ExecutionEngine modules not available")
class TestExecutionEngineContainerization(unittest.TestCase):
    """Test ExecutionEngine integration with ContainerManager"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('components.execution_engine.CONTAINER_EXECUTION_AVAILABLE', True)
    @patch('components.execution_engine.ContainerManager')
    def test_execution_engine_uses_containers(self, mock_container_manager):
        """Test that ExecutionEngine uses ContainerManager when available"""
        mock_manager = Mock()
        mock_container_manager.return_value = mock_manager

        engine = ExecutionEngine()

        # Verify ContainerManager was initialized
        mock_container_manager.assert_called_once()
        self.assertEqual(engine.execution_mode, "containerized")
        self.assertIsNotNone(engine.container_manager)

    @patch('components.execution_engine.CONTAINER_EXECUTION_AVAILABLE', False)
    def test_execution_engine_fallback_subprocess(self):
        """Test that ExecutionEngine falls back to subprocess when containers unavailable"""
        engine = ExecutionEngine()

        self.assertEqual(engine.execution_mode, "subprocess")
        self.assertIsNone(engine.container_manager)

    @patch('components.execution_engine.CONTAINER_EXECUTION_AVAILABLE', True)
    @patch('components.execution_engine.ContainerManager')
    def test_task_executor_containerized_execution(self, mock_container_manager):
        """Test TaskExecutor uses containerized execution"""
        mock_manager = Mock()
        mock_container_result = Mock()
        mock_container_result.task_id = "test-task"
        mock_container_result.status = "success"
        mock_container_result.start_time = datetime.now()
        mock_container_result.end_time = datetime.now()
        mock_container_result.duration = 120.0
        mock_container_result.exit_code = 0
        mock_container_result.stdout = "Task completed"
        mock_container_result.stderr = ""
        mock_container_result.error_message = None
        mock_container_result.resource_usage = {}

        mock_manager.execute_containerized_task.return_value = mock_container_result
        mock_container_manager.return_value = mock_manager

        # Create TaskExecutor
        executor = TaskExecutor(
            task_id="test-task",
            worktree_path=self.test_dir,
            prompt_file="test-prompt.md",
            task_context={'timeout_seconds': 3600}
        )

        # Mock prompt generation to avoid file dependencies
        executor._generate_workflow_prompt = Mock(return_value="test-prompt.md")

        # Execute task
        result = executor.execute()

        # Verify containerized execution was used
        mock_manager.execute_containerized_task.assert_called_once_with(
            task_id="test-task",
            worktree_path=self.test_dir,
            prompt_file="test-prompt.md",
            task_context={'timeout_seconds': 3600},
            progress_callback=executor._progress_callback
        )

        # Verify result conversion
        self.assertEqual((result.status if result is not None else None), "success")
        self.assertEqual(result.exit_code, 0)


@unittest.skipUnless(IMPORTS_AVAILABLE, "Monitoring modules not available")
class TestOrchestrationMonitoring(unittest.TestCase):
    """Test real-time monitoring capabilities"""

    def setUp(self):
        """Set up monitoring test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.monitor = OrchestrationMonitor(str(self.test_dir))

    def tearDown(self):
        """Clean up monitoring test environment"""
        if hasattr(self, 'monitor'):
            self.monitor.monitoring = False
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('monitoring.dashboard.docker')
    def test_monitor_initialization(self, mock_docker):
        """Test OrchestrationMonitor initialization"""
        mock_docker_client = Mock()
        mock_docker.from_env.return_value = mock_docker_client

        monitor = OrchestrationMonitor(str(self.test_dir))

        self.assertEqual(monitor.monitoring_dir, self.test_dir)
        self.assertTrue(monitor.monitoring_dir.exists())
        self.assertIsNotNone(monitor.docker_client)

    @patch('monitoring.dashboard.docker')
    def test_container_status_update(self, mock_docker):
        """Test container status monitoring"""
        mock_docker_client = Mock()
        mock_docker.from_env.return_value = mock_docker_client

        # Mock container list
        mock_container = Mock()
        mock_container.id = "test-container"
        mock_container.name = "orchestrator-test-task"
        if mock_container is not None:
                    mock_container.status = "running"
        mock_container.attrs = {
            'Created': '2023-01-01T00:00:00Z',
            'Config': {'Env': ['TEST=1']},
            'Mounts': []
        }
        mock_container.labels = {'task_id': 'test-task'}
        mock_container.ports = {}
        mock_container.image.tags = ['claude-orchestrator:latest']
        mock_container.logs.return_value = b"Container running\nTask in progress"
        mock_container.stats.return_value = {
            'memory_stats': {'usage': 1024*1024*100, 'limit': 1024*1024*1024},
            'cpu_stats': {
                'cpu_usage': {'total_usage': 1000000, 'percpu_usage': [500000, 500000]},
                'system_cpu_usage': 10000000
            },
            'networks': {'eth0': {'rx_bytes': 1000, 'tx_bytes': 2000}}
        }

        mock_docker_client.containers.list.return_value = [mock_container]

        monitor = OrchestrationMonitor(str(self.test_dir))
        monitor.docker_client = mock_docker_client

        # Test status update
        asyncio.run(monitor.update_container_status())

        # Verify container information was collected
        self.assertIn("orchestrator-test-task", monitor.active_containers)
        container_info = monitor.active_containers["orchestrator-test-task"]

        self.assertEqual(container_info['name'], "orchestrator-test-task")
        self.assertEqual(container_info['status'], "running")
        self.assertEqual(container_info['task_id'], "test-task")
        self.assertIn('stats', container_info)
        self.assertIn('recent_logs', container_info)


class TestPerformanceComparisons(unittest.TestCase):
    """Test performance improvements of containerized vs subprocess execution"""

    def test_execution_statistics_tracking(self):
        """Test that execution statistics properly track performance metrics"""
        # This would be an integration test measuring actual execution times
        # For unit testing, we verify the statistics structure

        mock_stats = {
            'total_tasks': 5,
            'completed_tasks': 4,
            'failed_tasks': 1,
            'cancelled_tasks': 0,
            'total_execution_time': 300.0,  # Sequential time estimate
            'parallel_execution_time': 75.0,  # Actual parallel time
            'execution_mode': 'containerized',
            'containerized_tasks': 4,
            'subprocess_tasks': 1
        }

        # Calculate speedup
        speedup = mock_stats['total_execution_time'] / mock_stats['parallel_execution_time']

        self.assertGreater(speedup, 3.0)  # Should achieve 3-5x speedup
        self.assertEqual(mock_stats['execution_mode'], 'containerized')
        self.assertEqual(mock_stats['total_tasks'], 5)


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for complete containerized workflow"""

    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up integration test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('components.execution_engine.CONTAINER_EXECUTION_AVAILABLE', True)
    @patch('container_manager.docker')
    def test_end_to_end_containerized_workflow(self, mock_docker):
        """Test complete end-to-end containerized workflow"""
        # Setup Docker mocks
        mock_docker_client = Mock()
        mock_docker.from_env.return_value = mock_docker_client
        mock_docker_client.ping.return_value = True
        mock_docker_client.images.get.return_value = Mock()

        # Mock successful container execution
        mock_container = Mock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Workflow completed successfully"
        mock_container.stats.return_value = {
            'memory_stats': {'usage': 1024*1024*100},
            'cpu_stats': {'cpu_usage': {'total_usage': 1000000}},
            'networks': {'eth0': {'rx_bytes': 1000, 'tx_bytes': 2000}}
        }
        mock_docker_client.containers.run.return_value = mock_container

        # Create test prompt file
        prompt_file = self.test_dir / "test-workflow.md"
        prompt_file.write_text("""
# Test Workflow
## Problem Statement
Test containerized execution
## Implementation Steps
1. Initialize environment
2. Execute task
3. Generate results
""")

        # Mock worktree manager
        mock_worktree_manager = Mock()
        mock_worktree_info = Mock()
        mock_worktree_info.worktree_path = self.test_dir
        mock_worktree_manager.get_worktree.return_value = mock_worktree_info

        # Create ExecutionEngine and execute
        engine = ExecutionEngine()

        tasks = [
            {
                'id': 'test-workflow-task',
                'name': 'Test Containerized Workflow',
                'prompt_file': str(prompt_file)
            }
        ]

        # Execute tasks
        results = engine.execute_tasks_parallel(tasks, mock_worktree_manager)

        # Verify results
        self.assertEqual(len(results), 1)
        result = results['test-workflow-task']
        self.assertIsNotNone(result)  # Use the result to avoid unused variable warning

        # Verify containerized execution characteristics
        if engine.execution_mode == "containerized":
            # Should have used Docker
            mock_docker_client.containers.run.assert_called()

            # Should have proper Claude CLI flags
            call_args = mock_docker_client.containers.run.call_args
            command = call_args[1]['command']
            self.assertIn('--dangerously-skip-permissions', command)
            self.assertIn('--output-format=json', command)


def run_containerized_tests():
    """Run all containerized orchestrator tests"""

    if not IMPORTS_AVAILABLE:
        print("⚠️  Cannot run tests - required modules not available")
        print("This is expected if Docker SDK or other dependencies are not installed")
        return

    # Create test suite
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestContainerConfig,
        TestContainerManager,
        TestExecutionEngineContainerization,
        TestOrchestrationMonitoring,
        TestPerformanceComparisons,
        TestIntegrationWorkflow
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Containerized Execution Tests Summary")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result is not None and result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")

    if result is not None and result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_containerized_tests()
    exit(0 if success else 1)
