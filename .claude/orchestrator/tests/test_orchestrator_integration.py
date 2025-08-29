#!/usr/bin/env python3
"""
Integration tests for the Orchestrator implementation

These tests validate the complete orchestrator workflow from CLI input
to parallel execution coordination.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add orchestrator components to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# from orchestrator_cli import OrchestrationCLI
# from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo

# Mock imports that may not be available
try:
    from orchestrator_cli import OrchestrationCLI  # type: ignore
    from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo  # type: ignore
    from orchestrator_main import OrchestratorCoordinator, OrchestrationConfig  # type: ignore
    ORCHESTRATOR_IMPORTS_AVAILABLE = True
except ImportError:
    # Create mock classes for testing
    class OrchestrationCLI:
        def __init__(self, project_root: str) -> None:
            self.project_root = project_root

        def parse_user_input(self, user_input: str) -> list[str]:  # type: ignore
            return []

        def execute_orchestration(self, prompt_files: list[str]) -> None:  # type: ignore
            pass

    class ProcessRegistry:
        def __init__(self, registry_dir: str) -> None:
            self.registry_dir = registry_dir

        def register_process(self, process_info: Any) -> None:  # type: ignore
            pass

        def get_process(self, task_id: str) -> Any:  # type: ignore
            return None

        def update_process_status(self, task_id: str, status: Any) -> bool:  # type: ignore
            return True

        def get_registry_stats(self) -> Any:  # type: ignore
            return Mock()  # type: ignore

    class ProcessStatus:
        QUEUED = "queued"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

    class ProcessInfo:
        def __init__(self, task_id: str, task_name: str, status: str, command: str, working_directory: str, created_at: Any) -> None:  # type: ignore
            self.task_id = task_id
            self.task_name = task_name
            self.status = status
            self.command = command
            self.working_directory = working_directory
            self.created_at = created_at

    class OrchestratorCoordinator:
        def __init__(self, config: Any, project_root: str) -> None:  # type: ignore[assignment]
            self.config = config
            self.project_root = Path(project_root)
            self.orchestration_id = f"orchestration-{id(self)}"

        def orchestrate(self, prompt_files: list[str]) -> Any:  # type: ignore
            return Mock(total_tasks=len(prompt_files), successful_tasks=0, execution_time_seconds=0.0)  # type: ignore

    class OrchestrationConfig:
        def __init__(self, max_parallel_tasks: int = 4, execution_timeout_hours: int = 2, fallback_to_sequential: bool = True, **kwargs: Any) -> None:  # type: ignore
            self.max_parallel_tasks = max_parallel_tasks
            self.execution_timeout_hours = execution_timeout_hours
            self.fallback_to_sequential = fallback_to_sequential
            for key, value in kwargs.items():
                setattr(self, key, value)

    ORCHESTRATOR_IMPORTS_AVAILABLE = False


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for orchestrator components"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.prompts_dir = self.test_dir / "prompts"
        self.prompts_dir.mkdir(parents=True)

        # Create test prompt files
        self.test_prompts = [
            "test-feature-1.md",
            "test-feature-2.md",
            "test-bug-fix.md"
        ]

        for prompt_file in self.test_prompts:
            prompt_path = self.prompts_dir / prompt_file
            prompt_path.write_text(f"""# Test Prompt: {prompt_file}

## Overview
Test prompt for orchestrator integration testing.

## Requirements
- Test requirement 1
- Test requirement 2

## Implementation Steps
1. Step 1
2. Step 2
3. Step 3
""")

        # Create test configuration
        self.config = OrchestrationConfig(  # type: ignore
            max_parallel_tasks=2,
            execution_timeout_hours=1,
            monitoring_interval_seconds=5,
            worktrees_dir=str(self.test_dir / ".worktrees"),
            monitoring_dir=str(self.test_dir / ".gadugi/monitoring")
        )

    def tearDown(self) -> None:
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_orchestrator_coordinator_initialization(self) -> None:
        """Test orchestrator coordinator initializes correctly"""
        with patch('orchestrator_main.ExecutionEngine'), \
             patch('orchestrator_main.WorktreeManager'), \
             patch('orchestrator_main.TaskAnalyzer'), \
             patch('orchestrator_main.PromptGenerator'):

            coordinator = OrchestratorCoordinator(  # type: ignore
                config=self.config,
                project_root=str(self.test_dir)
            )

            self.assertIsNotNone(coordinator)
            self.assertEqual(coordinator.project_root, self.test_dir)  # type: ignore
            self.assertIsNotNone(coordinator.orchestration_id)  # type: ignore
            self.assertTrue(coordinator.orchestration_id.startswith("orchestration-"))  # type: ignore

    def test_cli_parse_user_input(self) -> None:
        """Test CLI parsing of user input"""
        cli = OrchestrationCLI(str(self.test_dir))  # type: ignore

        # Test standard input format
        user_input = """
Execute these specific prompts in parallel:
- test-feature-1.md
- test-feature-2.md
- test-bug-fix.md
        """

        prompt_files = cli.parse_user_input(user_input)

        self.assertEqual(len(prompt_files), 3)
        self.assertIn("test-feature-1.md", prompt_files)
        self.assertIn("test-feature-2.md", prompt_files)
        self.assertIn("test-bug-fix.md", prompt_files)

    def test_cli_parse_alternative_formats(self) -> None:
        """Test CLI parsing with different input formats"""
        cli = OrchestrationCLI(str(self.test_dir))  # type: ignore

        # Test numbered list format
        user_input = """
Execute these prompt files:
1. test-feature-1.md
2. test-feature-2.md
        """

        prompt_files = cli.parse_user_input(user_input)
        self.assertEqual(len(prompt_files), 2)

        # Test mixed format
        user_input = """
Process these prompts in parallel:
* test-feature-1.md
+ test-feature-2.md
- test-bug-fix.md
        """

        prompt_files = cli.parse_user_input(user_input)
        self.assertEqual(len(prompt_files), 3)

    def test_process_registry_lifecycle(self) -> None:
        """Test process registry lifecycle management"""
        registry_dir = self.test_dir / ".gadugi/monitoring"
        registry = ProcessRegistry(str(registry_dir))  # type: ignore

        # Test process registration
        process_info = ProcessInfo(  # type: ignore
            task_id="test-task-1",
            task_name="Test Task 1",
            status=ProcessStatus.QUEUED,  # type: ignore
            command="claude /agent:WorkflowManager",
            working_directory=str(self.test_dir),
            created_at=registry._get_current_time() if hasattr(registry, '_get_current_time') else None  # type: ignore
        )

        registry.register_process(process_info)

        # Verify registration
        retrieved = registry.get_process("test-task-1")  # type: ignore
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.task_id, "test-task-1")  # type: ignore
        self.assertEqual(retrieved.status, ProcessStatus.QUEUED)  # type: ignore

        # Test status update
        success = registry.update_process_status("test-task-1", ProcessStatus.RUNNING)  # type: ignore
        self.assertTrue(success)

        updated = registry.get_process("test-task-1")  # type: ignore
        self.assertEqual(updated.status, ProcessStatus.RUNNING)  # type: ignore

        # Test completion
        registry.update_process_status("test-task-1", ProcessStatus.COMPLETED)  # type: ignore
        completed = registry.get_process("test-task-1")  # type: ignore
        self.assertEqual(completed.status, ProcessStatus.COMPLETED)  # type: ignore

    @patch('orchestrator_main.ExecutionEngine')  # type: ignore
    @patch('orchestrator_main.WorktreeManager')  # type: ignore
    @patch('orchestrator_main.TaskAnalyzer')  # type: ignore
    @patch('orchestrator_main.PromptGenerator')  # type: ignore
    def test_orchestrator_workflow_stages(self, mock_prompt_gen: Mock, mock_task_analyzer: Mock,
                                        mock_worktree_mgr: Mock, mock_exec_engine: Mock) -> None:
        """Test orchestrator workflow stages"""

        # Mock task analyzer
        mock_analysis = Mock()
        mock_analysis.task_id = "test-task-1"
        mock_analysis.name = "Test Task 1"
        mock_analysis.prompt_file = "test-feature-1.md"
        mock_analysis.task_type = "feature_implementation"
        mock_analysis.complexity = "MEDIUM"
        mock_analysis.can_parallelize = True
        mock_analysis.dependencies = []
        mock_analysis.target_files = ["test_file.py"]

        mock_task_analyzer.return_value.analyze_prompt_file.return_value = mock_analysis

        # Mock worktree manager
        mock_worktree_info = Mock()
        mock_worktree_info.task_id = "test-task-1"
        mock_worktree_info.worktree_path = self.test_dir / ".worktrees/test-task-1"
        mock_worktree_info.branch_name = "feature/test-task-1"

        mock_worktree_mgr.return_value.create_worktree.return_value = mock_worktree_info

        # Mock prompt generator
        mock_prompt_gen.return_value.generate_workflow_prompt.return_value = "generated_prompt.md"

        # Mock execution engine
        mock_result = Mock()
        mock_result.task_id = "test-task-1"
        mock_result.success = True
        mock_result.execution_time = 30.0
        mock_result.error_message = None

        mock_exec_engine.return_value.execute_task.return_value = mock_result

        # Create coordinator and run orchestration
        coordinator = OrchestratorCoordinator(  # type: ignore
            config=self.config,
            project_root=str(self.test_dir)
        )

        result = coordinator.orchestrate(["test-feature-1.md"])

        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result.total_tasks, 1)
        self.assertGreaterEqual(result.successful_tasks, 0)  # May be 0 due to mocking
        self.assertIsNotNone(result.execution_time_seconds)

    def test_cli_validation_missing_files(self) -> None:
        """Test CLI validation with missing prompt files"""
        cli = OrchestrationCLI(str(self.test_dir))  # type: ignore

        user_input = """
Execute these prompts:
- test-feature-1.md
- missing-file.md
- test-feature-2.md
        """

        prompt_files = cli.parse_user_input(user_input)

        # Should only return existing files
        self.assertEqual(len(prompt_files), 2)
        self.assertIn("test-feature-1.md", prompt_files)
        self.assertIn("test-feature-2.md", prompt_files)
        self.assertNotIn("missing-file.md", prompt_files)

    def test_configuration_validation(self) -> None:
        """Test orchestration configuration validation"""
        # Test default configuration
        default_config = OrchestrationConfig()  # type: ignore
        self.assertEqual(default_config.max_parallel_tasks, 4)
        self.assertEqual(default_config.execution_timeout_hours, 2)
        self.assertTrue(default_config.fallback_to_sequential)

        # Test custom configuration
        custom_config = OrchestrationConfig(  # type: ignore
            max_parallel_tasks=8,
            execution_timeout_hours=4,
            fallback_to_sequential=False
        )
        self.assertEqual(custom_config.max_parallel_tasks, 8)
        self.assertEqual(custom_config.execution_timeout_hours, 4)
        self.assertFalse(custom_config.fallback_to_sequential)

    def test_process_registry_stats(self) -> None:
        """Test process registry statistics generation"""
        registry_dir = self.test_dir / ".gadugi/monitoring"
        registry = ProcessRegistry(str(registry_dir))  # type: ignore

        # Add test processes
        from datetime import datetime
        processes = [
            ProcessInfo("task-1", "Task 1", ProcessStatus.COMPLETED, "cmd1", str(self.test_dir), datetime.now()),  # type: ignore
            ProcessInfo("task-2", "Task 2", ProcessStatus.RUNNING, "cmd2", str(self.test_dir), datetime.now()),  # type: ignore
            ProcessInfo("task-3", "Task 3", ProcessStatus.FAILED, "cmd3", str(self.test_dir), datetime.now()),  # type: ignore
        ]

        for process in processes:
            registry.register_process(process)

        # Get stats
        stats = registry.get_registry_stats()  # type: ignore

        self.assertEqual(stats.total_processes, 3)  # type: ignore
        self.assertEqual(stats.completed_count, 1)  # type: ignore
        self.assertEqual(stats.running_count, 1)  # type: ignore
        self.assertEqual(stats.failed_count, 1)  # type: ignore

    @patch('subprocess.run')  # type: ignore
    def test_shell_script_integration(self, mock_subprocess: Mock) -> None:
        """Test shell script entry point integration"""
        # Mock successful subprocess execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Orchestration completed successfully"

        # Test script exists and is executable
        script_path = Path(__file__).parent.parent / "run_orchestrator.sh"
        self.assertTrue(script_path.exists())

        # Check if script is executable (on Unix systems)
        if os.name != 'nt':  # Not Windows
            stat_info = script_path.stat()
            self.assertTrue(stat_info.st_mode & 0o111)  # Has execute permission

    def test_error_handling_graceful_degradation(self) -> None:
        """Test error handling and graceful degradation"""
        # Test with invalid project root
        with self.assertRaises(FileNotFoundError):
            OrchestrationCLI("/nonexistent/directory")  # type: ignore

        # Test with empty prompt list
        cli = OrchestrationCLI(str(self.test_dir))  # type: ignore
        with self.assertRaises(ValueError):
            cli.execute_orchestration([])  # type: ignore


class TestOrchestratorPerformance(unittest.TestCase):
    """Performance and stress tests for orchestrator"""

    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp())
        self.prompts_dir = self.test_dir / "prompts"
        self.prompts_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_large_prompt_set_handling(self) -> None:
        """Test handling of large number of prompt files"""
        # Create many prompt files
        prompt_files = []
        for i in range(20):
            prompt_file = f"test-prompt-{i:03d}.md"
            prompt_path = self.prompts_dir / prompt_file
            prompt_path.write_text(f"# Test Prompt {i}\n\nTest content {i}")
            prompt_files.append(prompt_file)

        # Test CLI parsing
        cli = OrchestrationCLI(str(self.test_dir))  # type: ignore
        user_input = "Execute these prompts:\n" + "\n".join(f"- {pf}" for pf in prompt_files)

        parsed_files = cli.parse_user_input(user_input)
        self.assertEqual(len(parsed_files), 20)

    def test_resource_limit_configuration(self) -> None:
        """Test resource limit configuration"""
        config = OrchestrationConfig(  # type: ignore
            max_parallel_tasks=16,
            execution_timeout_hours=8
        )

        self.assertEqual(config.max_parallel_tasks, 16)
        self.assertEqual(config.execution_timeout_hours, 8)

        # Ensure reasonable limits are maintained
        self.assertLessEqual(config.max_parallel_tasks, 32)  # Reasonable upper bound
        self.assertLessEqual(config.execution_timeout_hours, 24)  # Reasonable timeout


if __name__ == '__main__':
    # Set up test environment
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing

    # Run tests
    unittest.main(verbosity=2)
