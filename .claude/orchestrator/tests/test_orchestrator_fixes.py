from unittest.mock import Mock, patch, MagicMock, AsyncMock
#!/usr/bin/env python3
"""
Test Suite for OrchestratorAgent → WorkflowManager Implementation Fixes

This test suite validates the critical fixes for issue #1 where OrchestratorAgent
orchestration worked but WorkflowManagers failed to create actual implementation files.

Key areas tested:
1. Claude CLI command construction (agent invocation vs generic prompt)
2. PromptGenerator creates WorkflowManager-specific prompts
3. Context passing to TaskExecutors
4. End-to-end workflow execution validation
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path to import components
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.execution_engine import ExecutionEngine, TaskExecutor
from components.prompt_generator import PromptContext, PromptGenerator
from components.worktree_manager import WorktreeManager


class TestClaudeCLICommandFix(unittest.TestCase):
    """Test the critical Claude CLI command construction fix"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.task_id = "test-task-001"
        self.prompt_file = "test-prompt.md"
        self.task_context = {
            'id': self.task_id,
            'name': 'Test Task',
            'dependencies': [],
            'target_files': ['test_file.py'],
            'requirements': {'type': 'implementation'}
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('components.execution_engine.subprocess.Popen')
    @patch('components.execution_engine.psutil.Process')
    def test_claude_cli_uses_workflow_master_agent(self, mock_psutil_process, mock_popen):
        """Test that Claude CLI command uses /agent:workflow-manager instead of -p"""

        # Create mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('{"result": "success"}', '')
        mock_process.returncode = 0
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock psutil.Process for resource monitoring
        mock_proc = MagicMock()
        mock_proc.cpu_times.return_value = MagicMock(user=1.0, system=0.5)
        mock_proc.memory_info.return_value = MagicMock(rss=1024*1024)
        mock_psutil_process.return_value = mock_proc

        # Create TaskExecutor
        executor = TaskExecutor(
            task_id=self.task_id,
            worktree_path=self.temp_dir,
            prompt_file=self.prompt_file,
            task_context=self.task_context
        )

        # Execute task
        result = executor.execute(timeout=10)

        # Verify Claude CLI command construction
        self.assertTrue(mock_popen.called, "subprocess.Popen should be called")

        # Get the command that was used
        call_args = mock_popen.call_args[0][0]  # First positional argument (the command list)

        # Critical assertions
        self.assertEqual(call_args[0], "claude", "Should use claude CLI")
        self.assertEqual(call_args[1], "/agent:workflow-manager", "Should use WorkflowManager agent")
        self.assertIn("Execute the complete workflow", call_args[2], "Should include workflow instruction")
        self.assertIn("--output-format", call_args, "Should include output format")
        self.assertIn("json", call_args, "Should use JSON output format")

        # Ensure it does NOT use the old broken pattern
        self.assertNotIn("-p", call_args, "Should NOT use -p flag (old broken pattern)")

        # Verify successful execution
        self.assertEqual(result.status, "success")
        self.assertEqual(result.task_id, self.task_id)

    def test_old_command_pattern_detection(self):
        """Test that we can detect the old broken command pattern"""

        # Old broken pattern
        old_cmd = ["claude", "-p", "prompt.md", "--output-format", "json"]

        # New fixed pattern
        new_cmd = ["claude", "/agent:workflow-manager", "Execute the complete workflow for prompt.md", "--output-format", "json"]

        # Verify old pattern is detected as broken
        self.assertIn("-p", old_cmd, "Old pattern should contain -p flag")
        self.assertNotIn("/agent:", " ".join(old_cmd), "Old pattern should not contain agent invocation")

        # Verify new pattern is correct
        self.assertNotIn("-p", new_cmd, "New pattern should not contain -p flag")
        self.assertIn("/agent:workflow-manager", new_cmd, "New pattern should contain agent invocation")


class TestPromptGenerator(unittest.TestCase):
    """Test the PromptGenerator component"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = PromptGenerator(str(self.temp_dir))

        # Create test prompt file
        self.test_prompt = self.temp_dir / "prompts" / "test-prompt.md"
        self.test_prompt.parent.mkdir(parents=True, exist_ok=True)

        self.test_prompt.write_text("""# Test Implementation Task

## Requirements
- Implement test functionality
- Create unit tests
- Update documentation

## Technical Analysis
The implementation requires:
- Python class creation
- Test coverage
- API integration

## Implementation Plan
1. Create main module
2. Add test cases
3. Update docs

## Success Criteria
- All tests pass
- 90% coverage
- Documentation complete
""")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prompt_context_creation(self):
        """Test creating PromptContext from task definition"""

        task = {
            'id': 'test-001',
            'name': 'Test Task',
            'dependencies': ['dep1', 'dep2'],
            'target_files': ['file1.py', 'file2.py'],
            'requirements': {'type': 'implementation'}
        }

        context = self.generator.create_context_from_task(
            task,
            "test-prompt.md",
            phase_focus="Implementation"
        )

        self.assertEqual(context.task_id, 'test-001')
        self.assertEqual(context.task_name, 'Test Task')
        self.assertEqual(context.original_prompt, 'test-prompt.md')
        self.assertEqual(context.phase_focus, 'Implementation')
        self.assertEqual(context.dependencies, ['dep1', 'dep2'])
        self.assertEqual(context.target_files, ['file1.py', 'file2.py'])

    def test_workflow_prompt_generation(self):
        """Test generating WorkflowManager workflow prompts"""

        context = PromptContext(
            task_id="test-001",
            task_name="Test Task",
            original_prompt=str(self.test_prompt),
            phase_focus="Implementation",
            dependencies=["dep1"],
            target_files=["output.py"]
        )

        # Generate workflow prompt
        worktree_path = self.temp_dir / "worktree"
        worktree_path.mkdir()

        prompt_file = self.generator.generate_workflow_prompt(context, worktree_path)

        # Verify prompt file was created
        self.assertTrue(Path(prompt_file).exists(), "Workflow prompt file should be created")

        # Read and validate content
        with open(prompt_file, 'r') as f:
            content = f.read()

        # Critical validations
        self.assertIn("WorkflowManager Task Execution", content, "Should be WorkflowManager task")
        self.assertIn("test-001", content, "Should include task ID")
        self.assertIn("Test Task", content, "Should include task name")
        self.assertIn("Implementation", content, "Should include phase focus")
        self.assertIn("CREATE ACTUAL FILES", content, "Should emphasize file creation")
        self.assertIn("Complete All 9 Phases", content, "Should mention all 9 phases")
        self.assertIn("output.py", content, "Should include target files")

        # Verify original prompt content is included
        self.assertIn("Test Implementation Task", content, "Should include original prompt")
        self.assertIn("Implement test functionality", content, "Should include requirements")

    def test_prompt_validation(self):
        """Test prompt validation functionality"""

        # Create a valid prompt
        valid_prompt = self.temp_dir / "valid.md"
        valid_prompt.write_text("""# WorkflowManager Task Execution

## Task Information
Task details here

## Implementation Requirements
Requirements here

## Execution Instructions
CREATE ACTUAL FILES - this is critical
Complete WorkflowManager workflow

## Original Prompt Content
Original content here
""")

        # Validate the prompt
        issues = self.generator.validate_prompt_content(str(valid_prompt))
        self.assertEqual(len(issues), 0, "Valid prompt should have no issues")

        # Create an invalid prompt
        invalid_prompt = self.temp_dir / "invalid.md"
        invalid_prompt.write_text("""# Incomplete Prompt
Missing required sections
""")

        # Validate the invalid prompt
        issues = self.generator.validate_prompt_content(str(invalid_prompt))
        self.assertGreater(len(issues), 0, "Invalid prompt should have issues")

        # Check for specific issues
        issue_text = " ".join(issues)
        self.assertIn("Missing required section", issue_text, "Should detect missing sections")


class TestExecutionEngineIntegration(unittest.TestCase):
    """Test ExecutionEngine integration with fixes"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = ExecutionEngine(max_concurrent=1, default_timeout=10)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_task_executor_creation_with_context(self):
        """Test that TaskExecutor is created with proper context"""

        # Mock worktree manager
        mock_worktree_manager = MagicMock()
        mock_worktree_info = MagicMock()
        mock_worktree_info.worktree_path = self.temp_dir
        mock_worktree_manager.get_worktree.return_value = mock_worktree_info

        # Test task with context
        tasks = [{
            'id': 'test-001',
            'name': 'Test Task',
            'prompt_file': 'test.md',
            'dependencies': ['dep1'],
            'target_files': ['output.py'],
            'requirements': {'type': 'implementation'}
        }]

        # Temporarily store original method
        original_method = self.engine._execute_with_concurrency_control

        # Track executors created
        created_executors = []

        def capture_executors(executors, progress_callback):
            """Capture executors without executing them"""
            created_executors.extend(executors)
            return {}

        # Mock the execution to prevent actual Claude CLI calls
        with patch.object(self.engine, '_execute_with_concurrency_control', side_effect=capture_executors):
            # Execute tasks
            self.engine.execute_tasks_parallel(tasks, mock_worktree_manager)

            # Verify TaskExecutor was created
            self.assertEqual(len(created_executors), 1, "Should create one executor")

            # Get the executor
            executor = created_executors[0]

            # Verify context was passed
            self.assertEqual(executor.task_id, 'test-001')
            self.assertEqual(executor.task_context['name'], 'Test Task')
            self.assertEqual(executor.task_context['dependencies'], ['dep1'])
            self.assertEqual(executor.task_context['target_files'], ['output.py'])


class TestEndToEndWorkflowValidation(unittest.TestCase):
    """Test end-to-end workflow validation"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()

        # Initialize git repo
        os.system(f"cd {self.project_root} && git init")
        os.system(f"cd {self.project_root} && git config user.email 'test@test.com'")
        os.system(f"cd {self.project_root} && git config user.name 'Test User'")

        # Create initial commit
        (self.project_root / "README.md").write_text("# Test Project")
        os.system(f"cd {self.project_root} && git add . && git commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_worktree_prompt_generation_integration(self):
        """Test integration between WorktreeManager and PromptGenerator"""

        # Create WorktreeManager
        worktree_manager = WorktreeManager(str(self.project_root))

        # Create worktree
        task_id = "test-001"
        worktree_info = worktree_manager.create_worktree(task_id, "Test Task")

        # Create PromptGenerator
        generator = PromptGenerator(str(self.project_root))

        # Create test prompt
        prompt_content = """# Test Task Implementation

## Requirements
- Create test module
- Add documentation

## Implementation Plan
1. Create module
2. Add tests
3. Update docs
"""

        original_prompt = self.project_root / "prompts" / "test.md"
        original_prompt.parent.mkdir(exist_ok=True)
        original_prompt.write_text(prompt_content)

        # Generate workflow prompt
        context = PromptContext(
            task_id=task_id,
            task_name="Test Task",
            original_prompt="prompts/test.md"
        )

        workflow_prompt = generator.generate_workflow_prompt(context, worktree_info.worktree_path)

        # Verify prompt was created in worktree
        self.assertTrue(Path(workflow_prompt).exists(), "Workflow prompt should exist")
        self.assertTrue(str(workflow_prompt).startswith(str(worktree_info.worktree_path)),
                       "Prompt should be in worktree directory")

        # Verify content
        with open(workflow_prompt, 'r') as f:
            content = f.read()

        self.assertIn("WorkflowManager Task Execution", content)
        self.assertIn("CREATE ACTUAL FILES", content)
        self.assertIn("Test Task Implementation", content)

        # Cleanup
        worktree_manager.cleanup_worktree(task_id, force=True)


class TestRegressionPrevention(unittest.TestCase):
    """Test suite to prevent regression of the original issue"""

    def test_command_pattern_regression_detection(self):
        """Ensure the old broken pattern is never reintroduced"""

        # Read the current ExecutionEngine code
        engine_file = Path(__file__).parent.parent / "components" / "execution_engine.py"

        with open(engine_file, 'r') as f:
            code_content = f.read()

        # Ensure the fix is still in place
        self.assertIn("/agent:workflow-manager", code_content,
                     "ExecutionEngine should use WorkflowManager agent invocation")

        # Ensure the old broken pattern is not present
        self.assertNotIn('"-p", self.prompt_file', code_content,
                        "Should not use old -p prompt_file pattern")

        # Ensure PromptGenerator import is present
        self.assertIn("from .prompt_generator import", code_content,
                     "Should import PromptGenerator")

    def test_prompt_generator_exists(self):
        """Ensure PromptGenerator component exists and is functional"""

        generator_file = Path(__file__).parent.parent / "components" / "prompt_generator.py"
        self.assertTrue(generator_file.exists(), "PromptGenerator component should exist")

        # Test basic instantiation
        from components.prompt_generator import PromptGenerator
        generator = PromptGenerator()
        self.assertIsNotNone(generator, "PromptGenerator should be instantiable")

    def test_workflow_master_agent_availability(self):
        """Test that WorkflowManager agent is available"""

        # Check if WorkflowManager agent file exists
        agent_file = Path(__file__).parent.parent.parent.parent / ".claude" / "agents" / "workflow-master.md"
        self.assertTrue(agent_file.exists(), "WorkflowManager agent should exist")

        # Read agent content
        with open(agent_file, 'r') as f:
            agent_content = f.read()

        # Verify key components
        self.assertIn("workflow-master", agent_content, "Should be WorkflowManager agent")
        self.assertIn("Phase 5: Implementation", agent_content, "Should have implementation phase")
        self.assertIn("CREATE", agent_content.upper(), "Should mention file creation")


def run_test_suite():
    """Run the complete test suite"""

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestClaudeCLICommandFix,
        TestPromptGenerator,
        TestExecutionEngineIntegration,
        TestEndToEndWorkflowValidation,
        TestRegressionPrevention
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running OrchestratorAgent → WorkflowManager Fix Test Suite")
    print("=" * 70)

    success = run_test_suite()

    if success:
        print("\n✅ All tests passed! The fixes are working correctly.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        exit(1)
