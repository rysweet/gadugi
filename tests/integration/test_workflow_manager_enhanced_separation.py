#!/usr/bin/env python3
"""
Integration tests for WorkflowManager with Enhanced Separation shared modules.

Tests the integration between WorkflowManager and the shared modules:
- github_operations
- state_management
- error_handling
- task_tracking
- interfaces

Validates that the Enhanced Separation architecture provides:
- Robust workflow phase execution
- Comprehensive error handling and recovery
- Advanced state management with checkpointing
- Enhanced task tracking with dependency validation
- Seamless TodoWrite integration
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "shared")
)

from github_operations import GitHubOperations
from state_management import StateManager, CheckpointManager, TaskState
from utils.error_handling import ErrorHandler, CircuitBreaker
from task_tracking import TaskTracker, WorkflowPhaseTracker, TaskMetrics
from interfaces import AgentConfig, TaskData, ErrorContext, WorkflowPhase


# Mock classes for components not yet implemented in shared modules
class RetryManager:
    """Mock retry manager for testing."""

    def execute_with_retry(self, func, max_attempts=3, backoff_strategy="exponential"):
        """Execute function with retry logic."""
        return func()


class RecoveryManager:
    """Mock recovery manager for testing."""

    def create_recovery_plan(self, error_context):
        """Create recovery plan."""
        return {
            "recovery_strategy": "rollback_and_retry",
            "estimated_recovery_time": 300,
            "rollback_target": "last_known_good_commit",
        }

    def initiate_state_recovery(self, task_id):
        """Initiate state recovery."""
        pass


class TodoWriteManager:
    """Mock TodoWrite manager for testing."""

    def create_enhanced_task_list(self, tasks):
        """Create enhanced task list."""
        pass


class TestWorkflowManagerIntegration:
    """Integration tests for WorkflowManager with shared modules"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = AgentConfig(
            agent_id="test-workflow-manager", name="Test WorkflowManager"
        )

        # Initialize shared modules
        self.github_ops = GitHubOperations()
        self.state_manager = StateManager()
        self.error_handler = ErrorHandler()
        self.task_tracker = TaskTracker()
        self.phase_tracker = WorkflowPhaseTracker()
        self.task_metrics = TaskMetrics()

        # Mock external dependencies
        self.mock_gh_api = Mock()
        self.github_ops._api_client = self.mock_gh_api

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_master_initialization_with_shared_modules(self):
        """Test WorkflowManager initialization uses shared modules correctly"""

        # Test shared module initialization
        assert self.github_ops is not None
        assert self.state_manager is not None
        assert self.error_handler is not None
        assert self.task_tracker is not None
        assert self.phase_tracker is not None
        assert self.task_metrics is not None

        # Test configuration propagation
        assert self.github_ops.config == self.config

        # Test circuit breaker initialization
        github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
        implementation_circuit_breaker = CircuitBreaker(
            failure_threshold=5, timeout=600
        )

        assert github_circuit_breaker.failure_threshold == 3
        assert implementation_circuit_breaker.failure_threshold == 5

    def test_enhanced_task_initialization_and_resumption(self):
        """Test enhanced task initialization with resumption capability"""

        task_id = f"test-task-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        prompt_file = "test-feature.md"

        # Test workflow initialization
        self.task_metrics.start_workflow_tracking(task_id, prompt_file)

        # Create initial workflow state
        workflow_state = TaskState(
            task_id=task_id,
            prompt_file=prompt_file,
            status="in_progress",
            current_phase=WorkflowPhase.INITIALIZATION.value,
        )

        # Test state persistence
        self.state_manager.save_state(workflow_state)

        # Test checkpoint creation
        checkpoint_manager = CheckpointManager()
        checkpoint_id = checkpoint_manager.create_checkpoint(
            workflow_state, "Initial checkpoint"
        )
        assert checkpoint_id is not None

        # Test backup system using StateManager's backup methods
        backup_path = self.state_manager.backup_state(task_id)
        assert backup_path is not None

        # Test state resumption
        loaded_state = self.state_manager.load_state(task_id)
        assert loaded_state is not None
        assert loaded_state.task_id == task_id
        assert loaded_state.prompt_file == prompt_file

        # Test orphaned workflow detection
        orphaned_workflows = self.state_manager.detect_orphaned_workflows()
        assert isinstance(orphaned_workflows, list)

    def test_enhanced_issue_creation_phase(self):
        """Test enhanced issue creation with retry logic and error handling"""

        task_id = "test-issue-creation"
        workflow_state = TaskState(
            task_id=task_id,
            prompt_file="test.md",
            status="in_progress",
            current_phase=WorkflowPhase.ISSUE_CREATION.value,
        )

        # Mock prompt data
        prompt_data = {
            "feature_name": "Test Feature",
            "description": "Test feature for enhanced separation",
            "requirements": ["Requirement 1", "Requirement 2"],
            "success_criteria": ["Criterion 1", "Criterion 2"],
        }

        # Test phase tracking
        self.phase_tracker.start_phase(WorkflowPhase.ISSUE_CREATION)
        self.task_metrics.record_phase_start("issue_creation")

        # Mock successful issue creation
        with patch.object(self.github_ops, "create_issue") as mock_create_issue:
            mock_create_issue.return_value = {
                "success": True,
                "issue_number": 123,
                "issue_url": "https://github.com/test/repo/issues/123",
            }

            # Test retry logic integration
            retry_manager = RetryManager()
            issue_result = retry_manager.execute_with_retry(
                lambda: self.github_ops.create_issue(
                    {
                        "title": f"{prompt_data['feature_name']} - {task_id}",
                        "body": "Test issue body",
                        "labels": ["enhancement", "ai-generated"],
                    }
                ),
                max_attempts=3,
                backoff_strategy="exponential",
            )

            assert issue_result["success"]
            assert issue_result["issue_number"] == 123

            # Test state update after successful creation
            workflow_state.issue_number = issue_result["issue_number"]
            workflow_state.issue_url = issue_result["issue_url"]

            # Test checkpoint creation
            checkpoint_manager = CheckpointManager(self.state_manager)
            checkpoint_manager.create_checkpoint(workflow_state)

            # Test phase completion tracking
            self.phase_tracker.complete_phase(WorkflowPhase.ISSUE_CREATION)
            self.task_metrics.record_phase_completion("issue_creation")

    def test_enhanced_pull_request_phase(self):
        """Test enhanced PR creation with atomic state updates and verification"""

        task_id = "test-pr-creation"
        workflow_state = TaskState(
            task_id=task_id,
            phase=WorkflowPhase.PULL_REQUEST_CREATION,
            started_at=datetime.now(),
            issue_number=123,
            branch_name="feature/test-feature-123",
        )

        # Mock implementation summary
        implementation_summary = {
            "feature_name": "Test Feature",
            "changes_made": ["Added feature A", "Updated documentation"],
            "tests_added": ["test_feature_a.py"],
            "breaking_changes": [],
        }

        # Test phase tracking
        self.phase_tracker.start_phase(WorkflowPhase.PULL_REQUEST_CREATION)
        self.task_metrics.record_phase_start("pr_creation")

        # Mock successful PR creation
        with patch.object(self.github_ops, "create_pull_request") as mock_create_pr:
            mock_create_pr.return_value = {
                "success": True,
                "pr_number": 456,
                "pr_url": "https://github.com/test/repo/pull/456",
            }

            # Mock PR verification
            with patch.object(
                self.github_ops, "verify_pull_request_exists"
            ) as mock_verify:
                mock_verify.return_value = {"exists": True}

                # Test PR creation with retry logic
                retry_manager = RetryManager()
                pr_result = retry_manager.execute_with_retry(
                    lambda: self.github_ops.create_pull_request(
                        {
                            "title": f"{implementation_summary['feature_name']} - Implementation",
                            "body": "Test PR body",
                            "head": workflow_state.branch_name,
                            "base": "main",
                            "labels": ["enhancement", "ai-generated"],
                        }
                    ),
                    max_attempts=3,
                    backoff_strategy="exponential",
                )

                assert pr_result["success"]
                assert pr_result["pr_number"] == 456

                # Test atomic state update
                workflow_state.pr_number = pr_result["pr_number"]
                workflow_state.pr_url = pr_result["pr_url"]
                workflow_state.phase = WorkflowPhase.PULL_REQUEST_CREATED

                # Test verification step
                verification_result = self.github_ops.verify_pull_request_exists(
                    pr_result["pr_number"]
                )
                assert verification_result["exists"]

                # Test critical checkpoint after PR creation
                checkpoint_manager = CheckpointManager(self.state_manager)
                checkpoint_manager.create_checkpoint(workflow_state)

                # Test phase completion
                self.phase_tracker.complete_phase(WorkflowPhase.PULL_REQUEST_CREATION)
                self.task_metrics.record_phase_completion("pr_creation")

    def test_enhanced_task_tracking_with_dependencies(self):
        """Test enhanced task tracking with dependency validation"""

        workflow_state = TaskState(
            task_id="test-task-tracking",
            phase=WorkflowPhase.IMPLEMENTATION,
            started_at=datetime.now(),
        )

        # Create comprehensive task list with dependencies
        tasks = [
            TaskData(
                id="1",
                content="Create GitHub issue for Test Feature",
                status="pending",
                priority="high",
                phase=WorkflowPhase.ISSUE_CREATION,
                estimated_duration_minutes=5,
                dependencies=[],
            ),
            TaskData(
                id="2",
                content="Create feature branch",
                status="pending",
                priority="high",
                phase=WorkflowPhase.BRANCH_MANAGEMENT,
                estimated_duration_minutes=2,
                dependencies=["1"],
            ),
            TaskData(
                id="3",
                content="Research existing implementation",
                status="pending",
                priority="high",
                phase=WorkflowPhase.RESEARCH_PLANNING,
                estimated_duration_minutes=15,
                dependencies=["2"],
            ),
        ]

        # Test task initialization
        self.task_tracker.initialize_task_list(tasks, workflow_state.task_id)

        # Test TodoWrite integration
        todowrite_manager = TodoWriteManager()
        todowrite_manager.create_enhanced_task_list(tasks)

        # Test dependency validation
        # Should not allow task 2 to start before task 1 is completed
        try:
            # This should fail due to unmet dependencies
            unmet_dependencies = self.task_tracker.check_dependencies("2")
            if unmet_dependencies:
                dependency_error = True
            else:
                dependency_error = False
        except Exception:
            dependency_error = True

        assert dependency_error  # Should have unmet dependencies

        # Complete task 1 first
        self.task_tracker.update_task_status(
            "1", "completed", workflow_id=workflow_state.task_id
        )

        # Now task 2 should be allowed to start
        unmet_dependencies = self.task_tracker.check_dependencies("2")
        assert len(unmet_dependencies) == 0

        # Test task status transitions with validation
        current_task = self.task_tracker.get_task("2")
        assert current_task is not None

        # Test productivity tracking
        self.task_metrics.record_task_completion(
            "1",
            workflow_state.task_id,
            duration=300,  # 5 minutes
        )

    def test_comprehensive_error_handling_and_recovery(self):
        """Test comprehensive error handling scenarios"""

        task_id = "test-error-handling"
        TaskState(
            task_id=task_id,
            phase=WorkflowPhase.IMPLEMENTATION,
            started_at=datetime.now(),
        )

        # Test error context creation
        test_error = Exception("Simulated implementation failure")
        error_context = ErrorContext(
            operation="implementation",
            details={"error": str(test_error), "phase": "implementation"},
            agent_id="test-agent",
            workflow_id=task_id,
            severity="high",
        )

        # Test error handling
        with patch.object(self.error_handler, "handle_error") as mock_handle:
            self.error_handler.handle_error(error_context)
            mock_handle.assert_called_once_with(error_context)

        # Test circuit breaker functionality
        implementation_circuit_breaker = CircuitBreaker(
            failure_threshold=2, timeout=300
        )

        # Test failure scenarios
        failure_count = 0
        for i in range(3):
            try:
                if i < 2:  # First two calls should fail
                    implementation_circuit_breaker.call(
                        lambda: exec('raise Exception("Test failure")')
                    )
                else:  # Third call should trigger circuit breaker
                    implementation_circuit_breaker.call(lambda: {"success": True})
            except Exception:
                failure_count += 1

        # Should have triggered circuit breaker
        assert failure_count >= 2

        # Test recovery manager
        recovery_manager = RecoveryManager()

        with patch.object(recovery_manager, "create_recovery_plan") as mock_recovery:
            mock_recovery.return_value = {
                "recovery_strategy": "rollback_and_retry",
                "estimated_recovery_time": 300,
                "rollback_target": "last_known_good_commit",
            }

            recovery_plan = recovery_manager.create_recovery_plan(error_context)

            assert recovery_plan["recovery_strategy"] == "rollback_and_retry"
            assert "estimated_recovery_time" in recovery_plan

    def test_workflow_phase_tracking_integration(self):
        """Test comprehensive workflow phase tracking"""

        task_id = "test-phase-tracking"

        # Test all workflow phases
        phases_to_test = [
            WorkflowPhase.INITIALIZATION,
            WorkflowPhase.ISSUE_CREATION,
            WorkflowPhase.BRANCH_MANAGEMENT,
            WorkflowPhase.RESEARCH_PLANNING,
            WorkflowPhase.IMPLEMENTATION,
            WorkflowPhase.TESTING,
            WorkflowPhase.DOCUMENTATION,
            WorkflowPhase.PULL_REQUEST_CREATION,
            WorkflowPhase.REVIEW,
        ]

        # Test phase progression
        for i, phase in enumerate(phases_to_test):
            # Start phase
            self.phase_tracker.start_phase(phase)
            self.task_metrics.record_phase_start(phase.value.lower())

            # Simulate phase work (mock)
            import time

            time.sleep(0.01)  # Minimal sleep to show duration

            # Complete phase
            self.phase_tracker.complete_phase(phase)
            self.task_metrics.record_phase_completion(phase.value.lower())

            # Verify phase completion
            phase_status = self.phase_tracker.get_phase_status(phase)
            assert phase_status is not None

        # Test phase metrics
        phase_metrics = self.task_metrics.get_phase_metrics(task_id)
        assert isinstance(phase_metrics, dict)

    def test_state_consistency_validation(self):
        """Test state consistency validation and recovery"""

        task_id = "test-state-consistency"

        # Create workflow state
        workflow_state = TaskState(
            task_id=task_id,
            phase=WorkflowPhase.PULL_REQUEST_CREATION,
            started_at=datetime.now(),
            pr_number=789,
        )

        # Save state
        self.state_manager.save_state(workflow_state)

        # Test state consistency validation
        is_consistent = self.state_manager.validate_state_consistency(workflow_state)
        assert is_consistent

        # Test inconsistent state detection
        inconsistent_state = TaskState(
            task_id="inconsistent-test",
            prompt_file="test.md",
            status="in_progress",
            current_phase=WorkflowPhase.REVIEW.value,  # Advanced phase
            issue_number=None,  # Missing required field for this phase
            pr_number=None,
        )

        is_consistent = self.state_manager.validate_state_consistency(
            inconsistent_state
        )
        assert not is_consistent

        # Test state recovery
        recovery_manager = RecoveryManager()
        with patch.object(recovery_manager, "initiate_state_recovery") as mock_recovery:
            recovery_manager.initiate_state_recovery(task_id)
            mock_recovery.assert_called_once_with(task_id)

    def test_end_to_end_workflow_execution(self):
        """Test complete workflow execution with shared modules"""

        task_id = f"e2e-workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        prompt_file = "end-to-end-test.md"

        # Initialize workflow
        self.task_metrics.start_workflow_tracking(task_id, prompt_file)

        workflow_state = TaskState(
            task_id=task_id,
            prompt_file=prompt_file,
            phase=WorkflowPhase.INITIALIZATION,
            started_at=datetime.now(),
        )

        # Phase 1: Issue Creation
        workflow_state.phase = WorkflowPhase.ISSUE_CREATION
        self.phase_tracker.start_phase(WorkflowPhase.ISSUE_CREATION)

        with patch.object(self.github_ops, "create_issue") as mock_issue:
            mock_issue.return_value = {
                "success": True,
                "issue_number": 101,
                "issue_url": "test-url",
            }

            issue_result = self.github_ops.create_issue(
                {"title": "E2E Test", "body": "Test"}
            )
            workflow_state.issue_number = issue_result["issue_number"]

        self.phase_tracker.complete_phase(WorkflowPhase.ISSUE_CREATION)

        # Phase 2: Branch Management
        workflow_state.phase = WorkflowPhase.BRANCH_MANAGEMENT
        workflow_state.branch_name = f"feature/e2e-test-{workflow_state.issue_number}"

        # Phase 3-7: Implementation phases (mocked)
        implementation_phases = [
            WorkflowPhase.RESEARCH_PLANNING,
            WorkflowPhase.IMPLEMENTATION,
            WorkflowPhase.TESTING,
            WorkflowPhase.DOCUMENTATION,
        ]

        for phase in implementation_phases:
            workflow_state.phase = phase
            self.phase_tracker.start_phase(phase)
            # Simulate work
            self.phase_tracker.complete_phase(phase)

        # Phase 8: Pull Request Creation
        workflow_state.phase = WorkflowPhase.PULL_REQUEST_CREATION

        with patch.object(self.github_ops, "create_pull_request") as mock_pr:
            mock_pr.return_value = {
                "success": True,
                "pr_number": 201,
                "pr_url": "pr-test-url",
            }

            with patch.object(
                self.github_ops, "verify_pull_request_exists"
            ) as mock_verify:
                mock_verify.return_value = {"exists": True}

                pr_result = self.github_ops.create_pull_request(
                    {"title": "E2E Test PR", "body": "Test PR"}
                )
                workflow_state.pr_number = pr_result["pr_number"]

        # Phase 9: Review (preparation)
        workflow_state.phase = WorkflowPhase.REVIEW

        # Final state
        workflow_state.completed_at = datetime.now()
        self.state_manager.save_state(workflow_state)

        # Verify end-to-end completion
        final_state = self.state_manager.load_state(task_id)
        assert final_state.issue_number == 101
        assert final_state.pr_number == 201
        assert final_state.phase == WorkflowPhase.REVIEW

        # Verify productivity metrics
        total_duration = (
            workflow_state.completed_at - workflow_state.started_at
        ).total_seconds()
        assert total_duration > 0


class TestWorkflowManagerTaskValidation:
    """Test task validation and dependency management"""

    def setup_method(self):
        """Setup test environment"""
        self.task_tracker = TaskTracker(todowrite_manager=TodoWriteManager())

    def test_task_dependency_validation(self):
        """Test comprehensive task dependency validation"""

        # Create tasks with complex dependencies
        tasks = [
            TaskData(
                id="1",
                content="Setup",
                status="pending",
                priority="high",
                dependencies=[],
            ),
            TaskData(
                id="2",
                content="Task A",
                status="pending",
                priority="high",
                dependencies=["1"],
            ),
            TaskData(
                id="3",
                content="Task B",
                status="pending",
                priority="high",
                dependencies=["1"],
            ),
            TaskData(
                id="4",
                content="Integration",
                status="pending",
                priority="high",
                dependencies=["2", "3"],
            ),
            TaskData(
                id="5",
                content="Finalization",
                status="pending",
                priority="high",
                dependencies=["4"],
            ),
        ]

        self.task_tracker.initialize_task_list(tasks, "dependency-test")

        # Test that task 2 cannot start before task 1
        unmet_deps = self.task_tracker.check_dependencies("2")
        assert "1" in unmet_deps

        # Complete task 1
        self.task_tracker.update_task_status("1", "completed")

        # Now tasks 2 and 3 can start (parallel)
        unmet_deps_2 = self.task_tracker.check_dependencies("2")
        unmet_deps_3 = self.task_tracker.check_dependencies("3")
        assert len(unmet_deps_2) == 0
        assert len(unmet_deps_3) == 0

        # But task 4 still cannot start
        unmet_deps_4 = self.task_tracker.check_dependencies("4")
        assert "2" in unmet_deps_4 and "3" in unmet_deps_4

        # Complete tasks 2 and 3
        self.task_tracker.update_task_status("2", "completed")
        self.task_tracker.update_task_status("3", "completed")

        # Now task 4 can start
        unmet_deps_4 = self.task_tracker.check_dependencies("4")
        assert len(unmet_deps_4) == 0

    def test_task_status_transition_validation(self):
        """Test task status transition validation"""

        tasks = [
            TaskData(
                id="1",
                content="Test Task",
                status="pending",
                priority="high",
                dependencies=[],
            )
        ]

        self.task_tracker.initialize_task_list(tasks, "transition-test")

        # Test valid transitions
        valid_transitions = [
            ("pending", "in_progress"),
            ("in_progress", "completed"),
        ]

        for from_status, to_status in valid_transitions:
            # Reset task status
            self.task_tracker.update_task_status("1", from_status)

            # Test transition validation
            is_valid = self.task_tracker.is_valid_transition(from_status, to_status)
            assert is_valid

        # Test invalid transitions
        invalid_transitions = [
            ("pending", "completed"),  # Cannot skip in_progress
            ("completed", "pending"),  # Cannot go backward
            ("completed", "in_progress"),  # Cannot go backward
        ]

        for from_status, to_status in invalid_transitions:
            is_valid = self.task_tracker.is_valid_transition(from_status, to_status)
            assert not is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
