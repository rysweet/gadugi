"""
Tests for WorkflowManager Engine

Comprehensive test suite covering all workflow phases, error handling,
and integration scenarios.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from workflow_manager_engine import (
    WorkflowManagerEngine,
    WorkflowTask,
    WorkflowState,
    WorkflowStatus,
    WorkflowPhase,
    WorkflowStateMachine,
    PhaseExecutor,
    QualityGateValidator,
)


class TestWorkflowTask:
    """Test WorkflowTask data class"""

    def test_task_creation(self):
        """Test basic task creation"""
        task = WorkflowTask(
            task_id="task-123",
            task_type="feature",
            title="Test Feature",
            description="Test description",
            target_files=["src/test.py"],
        )

        assert task.task_id == "task-123"
        assert task.task_type == "feature"
        assert task.title == "Test Feature"
        assert task.dependencies == []
        assert task.priority == "medium"

    def test_task_with_dependencies(self):
        """Test task creation with dependencies"""
        task = WorkflowTask(
            task_id="task-456",
            task_type="bugfix",
            title="Fix Bug",
            description="Fix critical bug",
            target_files=["src/buggy.py"],
            dependencies=["task-123"],
            priority="high",
        )

        assert task.dependencies == ["task-123"]
        assert task.priority == "high"


class TestWorkflowStateMachine:
    """Test workflow state machine logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.task = WorkflowTask(
            task_id="test-task",
            task_type="feature",
            title="Test Task",
            description="Test description",
            target_files=["src/test.py"],
        )

        self.state = WorkflowState(
            task=self.task,
            status=WorkflowStatus.PENDING,
            current_phase=WorkflowPhase.SETUP,
            phases_completed=[],
        )

        self.state_machine = WorkflowStateMachine(self.state)

    def test_initial_state(self):
        """Test initial state machine state"""
        assert self.state.status == WorkflowStatus.PENDING
        assert self.state.current_phase == WorkflowPhase.SETUP
        assert len(self.state.phases_completed) == 0

    def test_can_execute_setup_phase(self):
        """Test can execute setup phase initially"""
        assert self.state_machine.can_execute_phase(WorkflowPhase.SETUP)

    def test_cannot_execute_later_phase_without_dependencies(self):
        """Test cannot execute later phases without dependencies"""
        assert not self.state_machine.can_execute_phase(WorkflowPhase.IMPLEMENTATION)
        assert not self.state_machine.can_execute_phase(WorkflowPhase.PULL_REQUEST)

    def test_can_execute_phase_after_dependencies_completed(self):
        """Test can execute phase after dependencies are completed"""
        # Complete setup phase
        self.state.phases_completed.append(WorkflowPhase.SETUP)

        # Now can execute issue creation
        assert self.state_machine.can_execute_phase(WorkflowPhase.ISSUE_CREATION)

        # But still cannot execute later phases
        assert not self.state_machine.can_execute_phase(WorkflowPhase.IMPLEMENTATION)

    def test_phase_completion_sequence(self):
        """Test proper phase completion sequence"""
        phases_to_complete = [
            WorkflowPhase.SETUP,
            WorkflowPhase.ISSUE_CREATION,
            WorkflowPhase.BRANCH_MANAGEMENT,
            WorkflowPhase.RESEARCH_PLANNING,
        ]

        for phase in phases_to_complete:
            assert self.state_machine.can_execute_phase(phase)
            assert self.state_machine.start_phase(phase)
            self.state_machine.complete_phase(phase)

        # Now should be able to execute implementation
        assert self.state_machine.can_execute_phase(WorkflowPhase.IMPLEMENTATION)

    def test_cannot_execute_already_completed_phase(self):
        """Test cannot execute already completed phase"""
        self.state.phases_completed.append(WorkflowPhase.SETUP)
        assert not self.state_machine.can_execute_phase(WorkflowPhase.SETUP)

    def test_workflow_failure(self):
        """Test workflow failure handling"""
        error_msg = "Test error"
        self.state_machine.fail_workflow(error_msg)

        assert self.state.status == WorkflowStatus.FAILED
        assert self.state.error_message == error_msg
        assert self.state.end_time is not None

    def test_workflow_completion(self):
        """Test workflow completion"""
        self.state_machine.complete_workflow()

        assert self.state.status == WorkflowStatus.COMPLETED
        assert self.state.end_time is not None


class TestPhaseExecutor:
    """Test individual phase execution"""

    def setup_method(self):
        """Set up test fixtures"""
        self.task = WorkflowTask(
            task_id="test-task",
            task_type="feature",
            title="Test Feature",
            description="Implement test feature",
            target_files=["src/feature.py"],
        )

        self.state = WorkflowState(
            task=self.task,
            status=WorkflowStatus.PENDING,
            current_phase=WorkflowPhase.SETUP,
            phases_completed=[],
        )

        self.state_machine = WorkflowStateMachine(self.state)
        self.executor = PhaseExecutor(self.state_machine)

    @pytest.mark.asyncio
    async def test_setup_phase_execution(self):
        """Test setup phase execution"""
        with patch.object(self.executor, "_validate_prerequisites") as mock_validate:
            mock_validate.return_value = {"valid": True, "errors": []}

            result = await self.executor.execute_phase(WorkflowPhase.SETUP)

            assert result
            assert WorkflowPhase.SETUP in self.state.phases_completed
            assert self.state.branch_name is not None
            assert "task-" in self.state.branch_name

    @pytest.mark.asyncio
    async def test_setup_phase_failure_on_invalid_prerequisites(self):
        """Test setup phase failure when prerequisites are invalid"""
        with patch.object(self.executor, "_validate_prerequisites") as mock_validate:
            mock_validate.return_value = {"valid": False, "errors": ["Git not found"]}

            result = await self.executor.execute_phase(WorkflowPhase.SETUP)

            assert not result
            assert self.state.status == WorkflowStatus.FAILED
            assert "Prerequisites not met" in self.state.error_message

    @pytest.mark.asyncio
    async def test_issue_creation_phase(self):
        """Test issue creation phase"""
        # Complete setup first
        self.state.phases_completed.append(WorkflowPhase.SETUP)

        with patch.object(self.executor, "_create_github_issue") as mock_create:
            mock_create.return_value = 1234

            result = await self.executor.execute_phase(WorkflowPhase.ISSUE_CREATION)

            assert result
            assert WorkflowPhase.ISSUE_CREATION in self.state.phases_completed
            assert self.state.issue_number == 1234

    @pytest.mark.asyncio
    async def test_branch_management_phase(self):
        """Test branch management phase"""
        # Complete prerequisites
        self.state.phases_completed.extend(
            [WorkflowPhase.SETUP, WorkflowPhase.ISSUE_CREATION]
        )
        self.state.branch_name = "feature/test-branch"

        with patch.object(self.executor, "_create_feature_branch") as mock_create:
            mock_create.return_value = True

            result = await self.executor.execute_phase(WorkflowPhase.BRANCH_MANAGEMENT)

            assert result
            assert WorkflowPhase.BRANCH_MANAGEMENT in self.state.phases_completed

    @pytest.mark.asyncio
    async def test_implementation_phase(self):
        """Test implementation phase"""
        # Complete prerequisites
        self.state.phases_completed.extend(
            [
                WorkflowPhase.SETUP,
                WorkflowPhase.ISSUE_CREATION,
                WorkflowPhase.BRANCH_MANAGEMENT,
                WorkflowPhase.RESEARCH_PLANNING,
            ]
        )

        with patch.object(self.executor, "_implement_changes") as mock_implement:
            mock_implement.return_value = {
                "success": True,
                "files_modified": ["src/feature.py"],
                "lines_added": 100,
                "lines_deleted": 10,
            }

            result = await self.executor.execute_phase(WorkflowPhase.IMPLEMENTATION)

            assert result
            assert WorkflowPhase.IMPLEMENTATION in self.state.phases_completed

    @pytest.mark.asyncio
    async def test_testing_phase(self):
        """Test testing phase execution"""
        # Complete prerequisites
        self.state.phases_completed.extend(
            [
                WorkflowPhase.SETUP,
                WorkflowPhase.ISSUE_CREATION,
                WorkflowPhase.BRANCH_MANAGEMENT,
                WorkflowPhase.RESEARCH_PLANNING,
                WorkflowPhase.IMPLEMENTATION,
            ]
        )

        with patch.object(self.executor, "_run_tests") as mock_tests:
            mock_tests.return_value = {
                "passed": True,
                "total_tests": 20,
                "coverage": 95.0,
                "duration": 15.2,
            }

            result = await self.executor.execute_phase(WorkflowPhase.TESTING)

            assert result
            assert WorkflowPhase.TESTING in self.state.phases_completed

    @pytest.mark.asyncio
    async def test_pull_request_phase(self):
        """Test pull request creation phase"""
        # Complete prerequisites
        self.state.phases_completed.extend(
            [
                WorkflowPhase.SETUP,
                WorkflowPhase.ISSUE_CREATION,
                WorkflowPhase.BRANCH_MANAGEMENT,
                WorkflowPhase.RESEARCH_PLANNING,
                WorkflowPhase.IMPLEMENTATION,
                WorkflowPhase.TESTING,
                WorkflowPhase.DOCUMENTATION,
            ]
        )
        self.state.issue_number = 1234

        with patch.object(self.executor, "_create_pull_request") as mock_pr:
            mock_pr.return_value = 567

            result = await self.executor.execute_phase(WorkflowPhase.PULL_REQUEST)

            assert result
            assert WorkflowPhase.PULL_REQUEST in self.state.phases_completed
            assert self.state.pr_number == 567

    @pytest.mark.asyncio
    async def test_phase_execution_error_handling(self):
        """Test phase execution error handling"""
        # Complete setup
        self.state.phases_completed.append(WorkflowPhase.SETUP)

        with patch.object(self.executor, "_create_github_issue") as mock_create:
            mock_create.side_effect = Exception("GitHub API error")

            result = await self.executor.execute_phase(WorkflowPhase.ISSUE_CREATION)

            assert not result
            assert self.state.status == WorkflowStatus.FAILED
            assert "GitHub API error" in self.state.error_message

    def test_generate_issue_body(self):
        """Test issue body generation"""
        self.state.task.dependencies = ["task-456"]
        body = self.executor._generate_issue_body()

        assert self.state.task.title not in body  # Title is separate
        assert self.state.task.description in body
        assert self.state.task.task_id in body
        assert "src/feature.py" in body
        assert "task-456" in body

    def test_generate_pr_body(self):
        """Test PR body generation"""
        self.state.issue_number = 1234
        body = self.executor._generate_pr_body()

        assert self.state.task.description in body
        assert str(self.state.issue_number) in body
        assert self.state.task.task_id in body
        assert "WorkflowManager Agent" in body

    def test_get_issue_labels(self):
        """Test issue label generation"""
        labels = self.executor._get_issue_labels()

        assert "gadugi-v0.3" in labels
        assert "workflow-manager" in labels
        assert "enhancement" in labels  # for feature type

    def test_get_issue_labels_for_bugfix(self):
        """Test issue labels for bugfix task"""
        self.state.task.task_type = "bugfix"
        self.state.task.priority = "high"

        labels = self.executor._get_issue_labels()

        assert "bug" in labels
        assert "priority-high" in labels


class TestQualityGateValidator:
    """Test quality gate validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = QualityGateValidator()

    def test_default_config(self):
        """Test default configuration"""
        config = self.validator._default_config()

        assert config["min_test_coverage"] == 90
        assert config["require_documentation"]
        assert config["enforce_code_style"]

    def test_validate_implementation_success(self):
        """Test successful implementation validation"""
        result = {"success": True, "files_modified": ["src/test.py"]}

        assert self.validator.validate_implementation(result)

    def test_validate_implementation_failure(self):
        """Test failed implementation validation"""
        result = {"success": False, "error": "Compilation failed"}

        assert not self.validator.validate_implementation(result)

    def test_validate_tests_success(self):
        """Test successful test validation"""
        result = {"passed": True, "coverage": 95.0, "total_tests": 20}

        assert self.validator.validate_tests(result)

    def test_validate_tests_low_coverage(self):
        """Test test validation with low coverage"""
        result = {
            "passed": True,
            "coverage": 85.0,  # Below minimum of 90%
            "total_tests": 20,
        }

        assert not self.validator.validate_tests(result)

    def test_validate_tests_failing(self):
        """Test test validation with failing tests"""
        result = {"passed": False, "coverage": 95.0, "total_tests": 20}

        assert not self.validator.validate_tests(result)


class TestWorkflowManagerEngine:
    """Test main workflow manager engine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = WorkflowManagerEngine()
        self.task = WorkflowTask(
            task_id="engine-test-task",
            task_type="feature",
            title="Engine Test Feature",
            description="Test the engine",
            target_files=["src/engine_test.py"],
        )

    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self):
        """Test complete workflow execution"""
        # Mock all external dependencies
        with (
            patch("subprocess.run") as mock_subprocess,
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(self.engine, "_save_checkpoint") as mock_checkpoint,
        ):
            # Configure mocks
            mock_exists.return_value = True  # .git directory exists
            mock_subprocess.return_value = Mock(returncode=0)  # Git commands succeed
            mock_checkpoint.return_value = None

            result = await self.engine.execute_workflow(self.task)

            # Verify result structure
            assert result.task_id == self.task.task_id
            assert result.status == "completed"
            assert len(result.phases_completed) == 11  # All phases completed
            assert result.current_phase == 11  # Final phase
            assert result.test_results["passed"]
            assert "implementation_files" in result.artifacts
            assert "duration_seconds" in result.metrics

    @pytest.mark.asyncio
    async def test_workflow_execution_with_failure(self):
        """Test workflow execution with failure"""
        with (
            patch("subprocess.run") as mock_subprocess,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            # Configure mocks for failure scenario
            mock_exists.return_value = False  # No .git directory
            mock_subprocess.return_value = Mock(returncode=1)

            result = await self.engine.execute_workflow(self.task)

            # Verify failure handling
            assert result.status == "failed"
            assert result.error_message is not None
            assert len(result.phases_completed) < 11  # Not all phases completed

    @pytest.mark.asyncio
    async def test_checkpoint_saving(self):
        """Test checkpoint saving functionality"""
        state = WorkflowState(
            task=self.task,
            status=WorkflowStatus.IN_PROGRESS,
            current_phase=WorkflowPhase.IMPLEMENTATION,
            phases_completed=[WorkflowPhase.SETUP, WorkflowPhase.ISSUE_CREATION],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for test
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                await self.engine._save_checkpoint(state)

                # Verify checkpoint file was created
                checkpoint_file = (
                    Path(".gadugi/checkpoints") / f"{self.task.task_id}.json"
                )
                assert checkpoint_file.exists()

                # Verify checkpoint content
                with open(checkpoint_file) as f:
                    data = json.load(f)

                assert data["task_id"] == self.task.task_id
                assert data["status"] == "in_progress"
                assert data["current_phase"] == WorkflowPhase.IMPLEMENTATION.value
                assert len(data["phases_completed"]) == 2

            finally:
                os.chdir(original_cwd)

    def test_result_generation(self):
        """Test workflow result generation"""
        state = WorkflowState(
            task=self.task,
            status=WorkflowStatus.COMPLETED,
            current_phase=WorkflowPhase.SETTINGS_UPDATE,
            phases_completed=list(WorkflowPhase),
            issue_number=1234,
            pr_number=567,
            branch_name="feature/test-branch",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        # Add some checkpoint data
        state.checkpoint_data = {
            "test_result": {"passed": True, "coverage": 95.0, "test_count": 25},
            "implementation_result": {"lines_added": 150, "lines_deleted": 30},
        }

        result = self.engine._generate_result(state)

        assert result.task_id == self.task.task_id
        assert result.status == "completed"
        assert len(result.phases_completed) == 11
        assert result.issue_number == 1234
        assert result.pr_number == 567
        assert result.branch_name == "feature/test-branch"
        assert result.test_results["passed"]
        assert result.test_results["coverage"] == 95.0
        assert result.metrics["lines_added"] == 150
        assert result.metrics["lines_deleted"] == 30


class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios"""

    @pytest.mark.asyncio
    async def test_feature_development_workflow(self):
        """Test complete feature development workflow"""
        task = WorkflowTask(
            task_id="feature-test",
            task_type="feature",
            title="New Feature",
            description="Implement new feature with tests",
            target_files=["src/new_feature.py", "tests/test_new_feature.py"],
            priority="high",
        )

        engine = WorkflowManagerEngine()

        # Mock external dependencies
        with (
            patch("subprocess.run") as mock_subprocess,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_subprocess.return_value = Mock(returncode=0)

            result = await engine.execute_workflow(task)

            # Verify feature workflow specifics
            assert result.task_id == "feature-test"
            assert "new_feature.py" in str(result.artifacts["implementation_files"])
            assert result.test_results["passed"]

    @pytest.mark.asyncio
    async def test_bugfix_workflow(self):
        """Test bugfix workflow"""
        task = WorkflowTask(
            task_id="bugfix-test",
            task_type="bugfix",
            title="Fix Critical Bug",
            description="Fix memory leak in processor",
            target_files=["src/processor.py"],
            priority="critical",
        )

        engine = WorkflowManagerEngine()

        with (
            patch("subprocess.run") as mock_subprocess,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_subprocess.return_value = Mock(returncode=0)

            result = await engine.execute_workflow(task)

            # Verify bugfix workflow
            assert result.task_id == "bugfix-test"
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self):
        """Test workflow execution with task dependencies"""
        task = WorkflowTask(
            task_id="dependent-task",
            task_type="enhancement",
            title="Enhancement with Dependencies",
            description="Enhance feature that depends on other tasks",
            target_files=["src/enhanced_feature.py"],
            dependencies=["feature-task-1", "bugfix-task-2"],
        )

        engine = WorkflowManagerEngine()

        with (
            patch("subprocess.run") as mock_subprocess,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True
            mock_subprocess.return_value = Mock(returncode=0)

            result = await engine.execute_workflow(task)

            # Dependencies should be recorded in issue/PR
            assert result.task_id == "dependent-task"
            assert len(task.dependencies) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
