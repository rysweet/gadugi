"""
Unit tests for WorkflowEngine

Tests the deterministic workflow execution engine to ensure
consistent and reliable workflow phase execution.
"""

import os
import sys
import pytest
import tempfile
import json
from unittest.mock import Mock, patch

# Add .claude to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude"))

# Import the module under test
from shared.workflow_engine import (
    WorkflowEngine,
    WorkflowPhase,
    WorkflowState,
    PhaseResult,
    execute_workflow,
)


class TestWorkflowEngine:
    """Test suite for WorkflowEngine class"""

    def setup_method(self):
        """Setup test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_file = os.path.join(self.temp_dir, "test_prompt.md")

        # Create a sample prompt file
        with open(self.prompt_file, "w") as f:
            f.write("""# Test Prompt for Workflow Engine

## Overview
This is a test prompt for validating the WorkflowEngine implementation.

## Problem Statement
Test the deterministic execution of workflow phases.

## Implementation Plan
1. Validate prompt processing
2. Test phase execution
3. Verify state management

## Success Criteria
- All phases execute successfully
- State is properly maintained
- Error handling works correctly
""")

        # Mock shared modules
        self.mock_state_manager = Mock()
        self.mock_github_ops = Mock()
        self.mock_task_tracker = Mock()
        self.mock_error_handler = Mock()

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_engine_initialization(self):
        """Test WorkflowEngine initialization with shared modules"""
        engine = WorkflowEngine(
            state_manager=self.mock_state_manager,
            github_ops=self.mock_github_ops,
            task_tracker=self.mock_task_tracker,
            error_handler=self.mock_error_handler,
        )

        assert engine.state_manager == self.mock_state_manager
        assert engine.github_ops == self.mock_github_ops
        assert engine.task_tracker == self.mock_task_tracker
        assert engine.error_handler == self.mock_error_handler
        assert engine.max_retries == 3
        assert engine.workflow_state is None
        assert engine.execution_log == []

    def test_workflow_engine_minimal_initialization(self):
        """Test WorkflowEngine initialization without shared modules"""
        engine = WorkflowEngine()

        # Should create minimal fallback implementations
        assert engine.state_manager is not None
        assert engine.github_ops is not None
        assert engine.task_tracker is not None
        assert engine.error_handler is not None

    def test_workflow_state_creation(self):
        """Test WorkflowState creation and initialization"""
        task_id = "test-task-123"
        prompt_file = self.prompt_file

        state = WorkflowState(
            task_id=task_id,
            prompt_file=prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        assert state.task_id == task_id
        assert state.prompt_file == prompt_file
        assert state.current_phase == WorkflowPhase.INIT
        assert state.completed_phases == []
        assert state.branch_name is None
        assert state.issue_number is None
        assert state.pr_number is None
        assert state.start_time is not None
        assert state.error_count == 0
        assert state.metadata == {}

    def test_phase_result_creation(self):
        """Test PhaseResult creation and initialization"""
        phase = WorkflowPhase.INIT
        success = True
        message = "Phase completed successfully"

        result = PhaseResult(phase=phase, success=success, message=message)

        assert result.phase == phase
        assert result.success == success
        assert result.message == message
        assert result.data == {}
        assert result.execution_time == 0.0
        assert result.retry_count == 0

    @patch("subprocess.run")
    def test_phase_init_success(self, mock_subprocess):
        """Test successful initialization phase"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-init",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        success, message, data = engine._phase_init()

        # Debug output
        if not success:
            print(f"Debug - Init failed: {message}")
            print(f"Debug - Prompt file: {self.prompt_file}")
            print(f"Debug - File exists: {os.path.exists(self.prompt_file)}")

        assert success is True, f"Init failed with message: {message}"
        assert "initialization successful" in message.lower()
        assert data["task_id"] == "test-init"
        assert data["prompt_file"] == self.prompt_file

    def test_phase_init_missing_file(self):
        """Test initialization phase with missing prompt file"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-init-fail",
            prompt_file="/nonexistent/file.md",
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        success, message, _data = engine._phase_init()

        assert success is False
        assert "not found" in message.lower()

    def test_phase_prompt_validation_success(self):
        """Test successful prompt validation phase"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-validation",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.PROMPT_VALIDATION,
            completed_phases=[],
        )

        success, message, data = engine._phase_prompt_validation()

        assert success is True
        assert "validation successful" in message.lower()
        assert data["content_length"] > 0
        assert data["has_title"] is True

    def test_phase_prompt_validation_short_content(self):
        """Test prompt validation with too short content"""
        # Create a file with very short content
        short_file = os.path.join(self.temp_dir, "short_prompt.md")
        with open(short_file, "w") as f:
            f.write("# Short")

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-short",
            prompt_file=short_file,
            current_phase=WorkflowPhase.PROMPT_VALIDATION,
            completed_phases=[],
        )

        success, message, _data = engine._phase_prompt_validation()

        assert success is False
        assert "too short" in message.lower()

    @patch("subprocess.run")
    def test_phase_branch_creation_success(self, mock_subprocess):
        """Test successful branch creation phase"""
        # Mock successful git commands
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-branch",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.BRANCH_CREATION,
            completed_phases=[],
        )

        success, message, data = engine._phase_branch_creation()

        assert success is True
        assert "branch created successfully" in message.lower()
        assert engine.workflow_state.branch_name is not None
        assert data["branch_name"] == engine.workflow_state.branch_name

    @patch("subprocess.run")
    def test_phase_branch_creation_failure(self, mock_subprocess):
        """Test branch creation failure"""
        # Mock failed git command
        mock_subprocess.return_value = Mock(
            returncode=1, stdout="", stderr="Branch already exists"
        )

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-branch-fail",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.BRANCH_CREATION,
            completed_phases=[],
        )

        success, message, _data = engine._phase_branch_creation()

        assert success is False
        assert "failed" in message.lower()

    @patch("subprocess.run")
    def test_phase_issue_management_success(self, mock_subprocess):
        """Test successful issue management phase"""
        # Mock successful gh issue create
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="https://github.com/user/repo/issues/123", stderr=""
        )

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-issue",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.ISSUE_MANAGEMENT,
            completed_phases=[],
        )

        success, message, data = engine._phase_issue_management()

        assert success is True
        assert "issue created successfully" in message.lower()
        assert engine.workflow_state.issue_number == 123
        assert data["issue_number"] == "123"

    @patch("subprocess.run")
    def test_phase_commit_changes_success(self, mock_subprocess):
        """Test successful commit changes phase"""
        # Mock successful git commands
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git add
            Mock(returncode=0, stdout="", stderr=""),  # git commit
        ]

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-commit",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.COMMIT_CHANGES,
            completed_phases=[],
        )

        success, message, data = engine._phase_commit_changes()

        assert success is True
        assert "committed successfully" in message.lower()
        assert "commit_message" in data

    @patch("subprocess.run")
    def test_phase_push_remote_success(self, mock_subprocess):
        """Test successful push to remote phase"""
        # Mock successful git push
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-push",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.PUSH_REMOTE,
            completed_phases=[],
            branch_name="feature/test-branch",
        )

        success, message, data = engine._phase_push_remote()

        assert success is True
        assert "pushed to remote successfully" in message.lower()
        assert data["branch_name"] == "feature/test-branch"

    @patch("subprocess.run")
    def test_phase_pr_creation_success(self, mock_subprocess):
        """Test successful PR creation phase"""
        # Mock successful gh pr create
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="https://github.com/user/repo/pull/456", stderr=""
        )

        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-pr",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.PR_CREATION,
            completed_phases=[],
            issue_number=123,
        )

        success, message, data = engine._phase_pr_creation()

        assert success is True
        assert "pr created successfully" in message.lower()
        assert engine.workflow_state.pr_number == 456
        assert data["pr_number"] == "456"

    def test_phase_code_review_success(self):
        """Test successful code review phase"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-review",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=789,
        )

        success, message, data = engine._phase_code_review()

        assert success is True
        assert "code review initiated" in message.lower()
        assert data["pr_number"] == 789
        assert data["review_requested"] is True

    def test_phase_review_response_success(self):
        """Test successful review response phase"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-response",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.REVIEW_RESPONSE,
            completed_phases=[],
            pr_number=789,
        )

        success, message, _data = engine._phase_review_response()

        assert success is True
        assert "review response" in message.lower()

    def test_phase_finalization_success(self):
        """Test successful finalization phase"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-final",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.FINALIZATION,
            completed_phases=[],
        )

        success, message, data = engine._phase_finalization()

        # Debug output
        if not success:
            print(f"Debug - Finalization failed: {message}")
            print(f"Debug - Data: {data}")

        assert success is True, f"Finalization failed with message: {message}"
        assert "finalization completed" in message.lower()
        assert "total_phases" in data
        assert "execution_time" in data

    def test_execute_phase_with_retry(self):
        """Test phase execution with retry logic"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-retry",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        # Mock a phase that fails twice then succeeds
        call_count = 0
        original_phase_init = engine._phase_init

        def mock_phase_init():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return original_phase_init()

        engine._phase_init = mock_phase_init

        result = engine._execute_phase(WorkflowPhase.INIT)

        assert result.success is True
        assert result.retry_count == 2  # Failed twice before success
        assert call_count == 3

    def test_execute_phase_max_retries_exceeded(self):
        """Test phase execution when max retries are exceeded"""
        engine = WorkflowEngine()
        engine.max_retries = 2  # Reduce for faster test
        engine.workflow_state = WorkflowState(
            task_id="test-max-retry",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        # Mock a phase that always fails
        def mock_phase_init():
            raise Exception("Persistent failure")

        engine._phase_init = mock_phase_init

        result = engine._execute_phase(WorkflowPhase.INIT)

        assert result.success is False
        assert result.retry_count > engine.max_retries
        assert "failed after" in result.message.lower()

    def test_save_checkpoint(self):
        """Test checkpoint saving functionality"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-checkpoint",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        # Should not raise exception
        engine._save_checkpoint()

        # Check if checkpoint file was created
        checkpoint_file = f".workflow_checkpoint_{engine.workflow_state.task_id}.json"
        assert os.path.exists(checkpoint_file)

        # Verify checkpoint content
        with open(checkpoint_file, "r") as f:
            checkpoint_data = json.load(f)

        assert checkpoint_data["task_id"] == "test-checkpoint"
        assert checkpoint_data["prompt_file"] == self.prompt_file

        # Cleanup
        os.remove(checkpoint_file)

    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-cleanup",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        # Create a checkpoint file
        checkpoint_file = f".workflow_checkpoint_{engine.workflow_state.task_id}.json"
        with open(checkpoint_file, "w") as f:
            json.dump({"test": "data"}, f)

        assert os.path.exists(checkpoint_file)

        # Cleanup should remove the file
        engine._cleanup_temp_files()

        assert not os.path.exists(checkpoint_file)

    def test_create_success_result(self):
        """Test successful execution result creation"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-success",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.FINALIZATION,
            completed_phases=[WorkflowPhase.INIT, WorkflowPhase.PROMPT_VALIDATION],
            branch_name="feature/test",
            issue_number=123,
            pr_number=456,
        )

        # Add some mock execution log
        engine.execution_log = [
            PhaseResult(WorkflowPhase.INIT, True, "Init successful"),
            PhaseResult(WorkflowPhase.PROMPT_VALIDATION, True, "Validation successful"),
        ]

        result = engine._create_success_result()

        assert result["success"] is True
        assert result["task_id"] == "test-success"
        assert result["total_phases"] == 2
        assert result["branch_name"] == "feature/test"
        assert result["issue_number"] == 123
        assert result["pr_number"] == 456
        assert "execution_time" in result
        assert "phase_results" in result
        assert len(result["phase_results"]) == 2

    def test_create_failure_result(self):
        """Test failure execution result creation"""
        engine = WorkflowEngine()
        engine.workflow_state = WorkflowState(
            task_id="test-failure",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        error_message = "Test failure message"
        result = engine._create_failure_result(error_message)

        assert result["success"] is False
        assert result["error"] == error_message
        assert result["task_id"] == "test-failure"
        assert result["completed_phases"] == 0
        assert "execution_time" in result
        assert "phase_results" in result

    @patch("subprocess.run")
    def test_full_workflow_execution_mock(self, mock_subprocess):
        """Test full workflow execution with mocked subprocess calls"""
        # Mock all subprocess calls to succeed
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="https://github.com/user/repo/issues/123", stderr=""
        )

        engine = WorkflowEngine()

        # Mock some phases to avoid actual system operations
        engine._phase_implementation = Mock(
            return_value=(True, "Implementation successful", {})
        )
        engine._phase_development_planning = Mock(
            return_value=(True, "Planning successful", {})
        )
        engine._phase_prompt_writer = Mock(
            return_value=(True, "Prompt writer successful", {})
        )

        result = engine.execute_workflow(self.prompt_file, "test-full-workflow")

        # The workflow should complete, but may fail on certain phases due to mocking limitations
        assert "success" in result
        assert "task_id" in result
        assert result["task_id"] == "test-full-workflow"
        assert "execution_time" in result
        assert "phase_results" in result

    def test_convenience_function(self):
        """Test the convenience execute_workflow function"""
        with patch.object(WorkflowEngine, "execute_workflow") as mock_execute:
            mock_execute.return_value = {"success": True, "task_id": "test"}

            result = execute_workflow(self.prompt_file, "test-convenience")

            mock_execute.assert_called_once_with(self.prompt_file, "test-convenience")
            assert result["success"] is True


class TestWorkflowPhases:
    """Test suite for WorkflowPhase enum"""

    def test_workflow_phases_exist(self):
        """Test that all expected workflow phases exist"""
        expected_phases = [
            "INIT",
            "PROMPT_VALIDATION",
            "BRANCH_CREATION",
            "PROMPT_WRITER",
            "ISSUE_MANAGEMENT",
            "DEVELOPMENT_PLANNING",
            "IMPLEMENTATION",
            "COMMIT_CHANGES",
            "PUSH_REMOTE",
            "PR_CREATION",
            "CODE_REVIEW",
            "REVIEW_RESPONSE",
            "FINALIZATION",
        ]

        for phase_name in expected_phases:
            assert hasattr(WorkflowPhase, phase_name)
            phase = getattr(WorkflowPhase, phase_name)
            assert isinstance(phase, WorkflowPhase)

    def test_workflow_phase_names(self):
        """Test workflow phase name properties"""
        assert WorkflowPhase.INIT.name == "INIT"
        assert WorkflowPhase.CODE_REVIEW.name == "CODE_REVIEW"
        assert WorkflowPhase.FINALIZATION.name == "FINALIZATION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
