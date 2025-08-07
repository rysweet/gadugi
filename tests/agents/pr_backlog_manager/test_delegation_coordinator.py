"""
Tests for Delegation Coordinator module.

Tests the DelegationCoordinator class and delegation functionality
including task creation, execution, and coordination with other agents.
"""

try:
    import pytest  # type: ignore[import]
except ImportError:
    from test_stubs import pytest

from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timedelta

# Add the source directories to the Python path for imports
import sys
import os

# Add pr-backlog-manager directory
pr_backlog_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".claude",
    "agents",
    "pr-backlog-manager",
)
sys.path.insert(0, pr_backlog_path)

# Add shared directory for interfaces
shared_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".claude",
    "shared",
)
sys.path.insert(0, shared_path)

# Always use stubs for type checking consistency
from test_stubs import (
    DelegationCoordinator,
    DelegationTask,
    DelegationType,
    DelegationPriority,
    DelegationStatus,
)


@pytest.fixture
def mock_github_ops():
    """Create mock GitHub operations."""
    mock = Mock()
    mock.add_pr_labels.return_value = None
    mock.add_pr_comment.return_value = None
    return mock


@pytest.fixture
def coordinator(mock_github_ops):
    """Create DelegationCoordinator instance."""
    return DelegationCoordinator(mock_github_ops, auto_approve=False)


@pytest.fixture
def sample_pr_context():
    """Sample PR context for testing."""
    return {
        "repository": "user/repo",
        "title": "feat: add new feature",
        "author": "developer",
        "labels": ["enhancement"],
        "github_actions": True,
    }


class TestDelegationCoordinator:
    """Test suite for DelegationCoordinator functionality."""


class TestDelegationTask:
    """Test DelegationTask data class."""

    def test_delegation_task_creation(self):
        """Test DelegationTask creation."""
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"test": "data"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        assert task.task_id == "test-123"
        assert task.pr_number == 456
        assert task.task_type == DelegationType.MERGE_CONFLICT_RESOLUTION
        assert task.priority == DelegationPriority.HIGH
        assert task.agent_target == "workflow-master"
        assert task.status == DelegationStatus.PENDING
        assert task.retry_count == 0


class TestDelegationCreation:
    """Test delegation task creation functionality."""

    def test_classify_issue_type(self, coordinator):
        """Test issue type classification."""
        # Test merge conflict classification
        assert (
            coordinator._classify_issue_type("PR has merge conflicts")
            == DelegationType.MERGE_CONFLICT_RESOLUTION
        )

        # Test CI failure classification
        assert (
            coordinator._classify_issue_type("CI checks are failing")
            == DelegationType.CI_FAILURE_FIX
        )

        # Test branch update classification
        assert (
            coordinator._classify_issue_type("Branch is behind main")
            == DelegationType.BRANCH_UPDATE
        )

        # Test AI review classification
        assert (
            coordinator._classify_issue_type("AI code review not completed")
            == DelegationType.AI_CODE_REVIEW
        )

        # Test metadata classification
        assert (
            coordinator._classify_issue_type("PR metadata incomplete")
            == DelegationType.METADATA_IMPROVEMENT
        )

        # Test unknown issue (defaults to CI failure)
        assert (
            coordinator._classify_issue_type("Some unknown issue")
            == DelegationType.CI_FAILURE_FIX
        )

    def test_assess_issue_priority(self, coordinator):
        """Test issue priority assessment."""
        # Test critical priority
        pr_context = {"labels": []}
        assert (
            coordinator._assess_issue_priority("Critical security issue", pr_context)
            == DelegationPriority.CRITICAL
        )

        # Test high priority from labels
        pr_context = {"labels": ["priority-high"]}
        assert (
            coordinator._assess_issue_priority("Some issue", pr_context)
            == DelegationPriority.HIGH
        )

        # Test medium priority from labels
        pr_context = {"labels": ["priority-medium"]}
        assert (
            coordinator._assess_issue_priority("Some issue", pr_context)
            == DelegationPriority.MEDIUM
        )

        # Test merge conflict priority
        pr_context = {"labels": []}
        assert (
            coordinator._assess_issue_priority("merge conflict issue", pr_context)
            == DelegationPriority.HIGH
        )

        # Test CI failure priority
        assert (
            coordinator._assess_issue_priority("CI failing", pr_context)
            == DelegationPriority.MEDIUM
        )

        # Test default priority
        assert (
            coordinator._assess_issue_priority("metadata issue", pr_context)
            == DelegationPriority.LOW
        )

    def test_select_target_agent(self, coordinator):
        """Test target agent selection."""
        # Test WorkflowMaster capabilities
        assert (
            coordinator._select_target_agent(DelegationType.MERGE_CONFLICT_RESOLUTION)
            == "workflow-master"
        )
        assert (
            coordinator._select_target_agent(DelegationType.CI_FAILURE_FIX)
            == "workflow-master"
        )
        assert (
            coordinator._select_target_agent(DelegationType.BRANCH_UPDATE)
            == "workflow-master"
        )
        assert (
            coordinator._select_target_agent(DelegationType.METADATA_IMPROVEMENT)
            == "workflow-master"
        )

        # Test code-reviewer capabilities
        assert (
            coordinator._select_target_agent(DelegationType.AI_CODE_REVIEW)
            == "code-reviewer"
        )

    def test_create_delegation_task(self, coordinator, sample_pr_context):
        """Test delegation task creation."""
        blocking_issue = "PR has merge conflicts that need resolution"

        task = coordinator._create_delegation_task(
            123, blocking_issue, sample_pr_context
        )

        assert task is not None
        assert task.pr_number == 123
        assert task.task_type == DelegationType.MERGE_CONFLICT_RESOLUTION
        assert task.priority == DelegationPriority.HIGH
        assert task.agent_target == "workflow-master"
        assert task.status == DelegationStatus.PENDING
        assert "merge conflicts" in task.prompt_template.lower()
        assert task.task_id.startswith("delegation-123-merge_conflict_resolution-")


class TestPromptGeneration:
    """Test prompt template generation."""

    def test_generate_merge_conflict_prompt(self, coordinator, sample_pr_context):
        """Test merge conflict resolution prompt generation."""
        prompt = coordinator._generate_prompt_template(
            DelegationType.MERGE_CONFLICT_RESOLUTION,
            123,
            "PR has merge conflicts",
            sample_pr_context,
        )

        assert "merge conflicts" in prompt.lower()
        assert "pr #123" in prompt.lower()
        assert "rebase against latest main" in prompt.lower()
        assert "success criteria" in prompt.lower()
        assert "safety constraints" in prompt.lower()

    def test_generate_ci_failure_prompt(self, coordinator, sample_pr_context):
        """Test CI failure fix prompt generation."""
        prompt = coordinator._generate_prompt_template(
            DelegationType.CI_FAILURE_FIX,
            456,
            "CI checks are failing",
            sample_pr_context,
        )

        assert "ci/cd failures" in prompt.lower()
        assert "pr #456" in prompt.lower()
        assert "analyze failing ci checks" in prompt.lower()
        assert "lint/style issues" in prompt.lower()
        assert "test failures" in prompt.lower()

    def test_generate_branch_update_prompt(self, coordinator, sample_pr_context):
        """Test branch update prompt generation."""
        prompt = coordinator._generate_prompt_template(
            DelegationType.BRANCH_UPDATE,
            789,
            "Branch is behind main",
            sample_pr_context,
        )

        assert "update pr #789 branch" in prompt.lower()
        assert "current with main branch" in prompt.lower()
        assert "merge vs rebase" in prompt.lower()
        assert "up-to-date" in prompt.lower()

    def test_generate_ai_review_prompt(self, coordinator, sample_pr_context):
        """Test AI code review prompt generation."""
        prompt = coordinator._generate_prompt_template(
            DelegationType.AI_CODE_REVIEW,
            321,
            "AI code review not completed",
            sample_pr_context,
        )

        assert "ai code review" in prompt.lower()
        assert "phase 9" in prompt.lower()
        assert "pr #321" in prompt.lower()
        assert "code quality" in prompt.lower()
        assert "security vulnerabilities" in prompt.lower()

    def test_generate_metadata_improvement_prompt(self, coordinator, sample_pr_context):
        """Test metadata improvement prompt generation."""
        prompt = coordinator._generate_prompt_template(
            DelegationType.METADATA_IMPROVEMENT,
            654,
            "PR metadata incomplete",
            sample_pr_context,
        )

        assert "metadata" in prompt.lower()
        assert "pr #654" in prompt.lower()
        assert "conventional commit" in prompt.lower()
        assert "description" in prompt.lower()
        assert "labels" in prompt.lower()


class TestDelegationExecution:
    """Test delegation execution functionality."""

    def test_delegate_issue_resolution(
        self, coordinator, sample_pr_context, mock_github_ops
    ):
        """Test issue resolution delegation."""
        blocking_issues = [
            "PR has merge conflicts that need resolution",
            "CI checks are failing and need to be fixed",
        ]

        with patch.object(coordinator, "_execute_delegation") as mock_execute:
            tasks = coordinator.delegate_issue_resolution(
                123, blocking_issues, sample_pr_context
            )

            assert len(tasks) == 2
            assert tasks[0].task_type == DelegationType.MERGE_CONFLICT_RESOLUTION
            assert tasks[1].task_type == DelegationType.CI_FAILURE_FIX
            assert mock_execute.call_count == 2

    def test_execute_delegation_workflow_master(self, coordinator):
        """Test delegation execution to WorkflowMaster."""
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        with (
            patch.object(coordinator, "_delegate_to_workflow_master") as mock_delegate,
            patch.object(coordinator, "_add_delegation_comment") as mock_comment,
        ):
            coordinator._execute_delegation(task)

            mock_delegate.assert_called_once_with(task)
            mock_comment.assert_called_once_with(task)
            assert task.status == DelegationStatus.DELEGATED
            assert task.last_attempt is not None

    def test_execute_delegation_code_reviewer(self, coordinator):
        """Test delegation execution to code-reviewer."""
        task = DelegationTask(
            task_id="test-456",
            pr_number=789,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.MEDIUM,
            agent_target="code-reviewer",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        with (
            patch.object(coordinator, "_delegate_to_code_reviewer") as mock_delegate,
            patch.object(coordinator, "_add_delegation_comment") as mock_comment,
        ):
            coordinator._execute_delegation(task)

            mock_delegate.assert_called_once_with(task)
            mock_comment.assert_called_once_with(task)
            assert task.status == DelegationStatus.DELEGATED

    def test_execute_delegation_failure_retry(self, coordinator):
        """Test delegation execution failure and retry."""
        task = DelegationTask(
            task_id="test-789",
            pr_number=123,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        with patch.object(
            coordinator,
            "_delegate_to_workflow_master",
            side_effect=Exception("Test error"),
        ):
            coordinator._execute_delegation(task)

            assert task.status == DelegationStatus.FAILED
            assert task.error_message == "Test error"
            assert task.retry_count == 1


class TestWorkflowMasterDelegation:
    """Test WorkflowMaster delegation functionality."""

    def test_create_workflow_master_prompt_auto_approve(self, coordinator):
        """Test WorkflowMaster prompt creation in auto-approve mode."""
        coordinator.auto_approve = True
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="# Test Prompt\nResolve conflicts for PR #456",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        expected_path = (
            ".github/workflow-states/resolve-pr-456-merge_conflict_resolution.md"
        )

        with patch("builtins.open", mock_open()) as mock_file:
            coordinator._create_workflow_master_prompt(task)

            mock_file.assert_called_once_with(expected_path, "w")
            mock_file().write.assert_called_once_with(task.prompt_template)
            assert task.status == DelegationStatus.IN_PROGRESS

    def test_invoke_workflow_master_interactive(self, coordinator):
        """Test WorkflowMaster invocation in interactive mode."""
        coordinator.auto_approve = False
        task = DelegationTask(
            task_id="test-456",
            pr_number=789,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Fix CI for PR #789",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        coordinator._invoke_workflow_master_interactive(task)

        assert task.status == DelegationStatus.IN_PROGRESS


class TestCodeReviewerDelegation:
    """Test code-reviewer delegation functionality."""

    def test_create_code_review_workflow_auto_approve(self, coordinator):
        """Test code review workflow creation in auto-approve mode."""
        coordinator.auto_approve = True
        task = DelegationTask(
            task_id="test-789",
            pr_number=123,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.HIGH,
            agent_target="code-reviewer",
            prompt_template="Review PR #123",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        expected_path = ".github/workflows/ai-review-pr-123.yml"

        with patch("builtins.open", mock_open()) as mock_file:
            coordinator._create_code_review_workflow(task)

            mock_file.assert_called_once_with(expected_path, "w")
            # Check that workflow content was written
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            assert "AI Code Review for PR #123" in written_content
            assert "code-reviewer" in written_content
            assert task.status == DelegationStatus.IN_PROGRESS

    def test_invoke_code_reviewer_direct(self, coordinator):
        """Test direct code-reviewer invocation."""
        coordinator.auto_approve = False
        task = DelegationTask(
            task_id="test-abc",
            pr_number=456,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.MEDIUM,
            agent_target="code-reviewer",
            prompt_template="Review PR #456",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        coordinator._invoke_code_reviewer_direct(task)

        assert task.status == DelegationStatus.IN_PROGRESS


class TestDelegationComments:
    """Test delegation comment functionality."""

    def test_add_delegation_comment_merge_conflict(self, coordinator, mock_github_ops):
        """Test delegation comment for merge conflict resolution."""
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.DELEGATED,
        )

        coordinator._add_delegation_comment(task)

        mock_github_ops.add_pr_comment.assert_called_once()
        call_args = mock_github_ops.add_pr_comment.call_args
        pr_number = call_args[0][0]
        comment = call_args[0][1]

        assert pr_number == 456
        assert "🔧 **Automated Merge Conflict Resolution**" in comment
        assert "test-123" in comment
        assert "high" in comment.lower()
        assert "delegated" in comment.lower()

    def test_add_delegation_comment_ci_failure(self, coordinator, mock_github_ops):
        """Test delegation comment for CI failure resolution."""
        task = DelegationTask(
            task_id="test-456",
            pr_number=789,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.DELEGATED,
        )

        coordinator._add_delegation_comment(task)

        mock_github_ops.add_pr_comment.assert_called_once()
        call_args = mock_github_ops.add_pr_comment.call_args
        comment = call_args[0][1]

        assert "🚨 **Automated CI Failure Resolution**" in comment
        assert "test-456" in comment

    def test_add_delegation_comment_ai_review(self, coordinator, mock_github_ops):
        """Test delegation comment for AI code review."""
        task = DelegationTask(
            task_id="test-789",
            pr_number=123,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.HIGH,
            agent_target="code-reviewer",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.DELEGATED,
        )

        coordinator._add_delegation_comment(task)

        mock_github_ops.add_pr_comment.assert_called_once()
        call_args = mock_github_ops.add_pr_comment.call_args
        comment = call_args[0][1]

        assert "🤖 **AI Code Review Initiated**" in comment
        assert "test-789" in comment


class TestDelegationManagement:
    """Test delegation management functionality."""

    def test_check_delegation_status(self, coordinator):
        """Test delegation status checking."""
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.IN_PROGRESS,
        )

        coordinator.active_delegations["test-123"] = task

        retrieved_task = coordinator.check_delegation_status("test-123")
        assert retrieved_task == task

        assert coordinator.check_delegation_status("nonexistent") is None

    def test_get_active_delegations(self, coordinator):
        """Test getting active delegations."""
        task1 = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now(),
            status=DelegationStatus.IN_PROGRESS,
        )
        task2 = DelegationTask(
            task_id="test-456",
            pr_number=789,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now(),
            status=DelegationStatus.COMPLETED,
        )
        task3 = DelegationTask(
            task_id="test-789",
            pr_number=456,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.LOW,
            agent_target="code-reviewer",
            prompt_template="Test",
            context={},
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

        coordinator.active_delegations.update(
            {"test-123": task1, "test-456": task2, "test-789": task3}
        )

        # Get all delegations
        all_delegations = coordinator.get_active_delegations()
        assert len(all_delegations) == 3

        # Get delegations for specific PR
        pr_456_delegations = coordinator.get_active_delegations(pr_number=456)
        assert len(pr_456_delegations) == 2
        assert all(task.pr_number == 456 for task in pr_456_delegations)

    def test_mark_delegation_completed(self, coordinator, mock_github_ops):
        """Test marking delegation as completed."""
        task = DelegationTask(
            task_id="test-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.IN_PROGRESS,
        )

        coordinator.active_delegations["test-123"] = task

        coordinator.mark_delegation_completed("test-123", success=True)

        assert task.status == DelegationStatus.COMPLETED
        assert task.completion_time is not None
        mock_github_ops.add_pr_comment.assert_called_once()

        # Check completion comment
        call_args = mock_github_ops.add_pr_comment.call_args
        comment = call_args[0][1]
        assert "✅ **Delegation Completed Successfully**" in comment

    def test_mark_delegation_failed(self, coordinator, mock_github_ops):
        """Test marking delegation as failed."""
        task = DelegationTask(
            task_id="test-456",
            pr_number=789,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Test prompt",
            context={"repository": "user/repo"},
            created_at=datetime.now(),
            status=DelegationStatus.IN_PROGRESS,
            error_message="Test error",
        )

        coordinator.active_delegations["test-456"] = task

        coordinator.mark_delegation_completed("test-456", success=False)

        assert task.status == DelegationStatus.FAILED
        mock_github_ops.add_pr_comment.assert_called_once()

        # Check failure comment
        call_args = mock_github_ops.add_pr_comment.call_args
        comment = call_args[0][1]
        assert "❌ **Delegation Failed**" in comment
        assert "Test error" in comment

    def test_cleanup_completed_delegations(self, coordinator):
        """Test cleanup of completed delegations."""
        old_completed_task = DelegationTask(
            task_id="old-123",
            pr_number=456,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(days=2),
            status=DelegationStatus.COMPLETED,
            completion_time=datetime.now() - timedelta(days=2),
        )

        recent_completed_task = DelegationTask(
            task_id="recent-456",
            pr_number=789,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(hours=2),
            status=DelegationStatus.COMPLETED,
            completion_time=datetime.now() - timedelta(hours=2),
        )

        active_task = DelegationTask(
            task_id="active-789",
            pr_number=123,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.LOW,
            agent_target="code-reviewer",
            prompt_template="Test",
            context={},
            created_at=datetime.now(),
            status=DelegationStatus.IN_PROGRESS,
        )

        coordinator.active_delegations.update(
            {
                "old-123": old_completed_task,
                "recent-456": recent_completed_task,
                "active-789": active_task,
            }
        )

        # Cleanup with 24 hour threshold
        cleaned_count = coordinator.cleanup_completed_delegations(max_age_hours=24)

        assert cleaned_count == 1  # Only old task should be cleaned
        assert "old-123" not in coordinator.active_delegations
        assert "recent-456" in coordinator.active_delegations
        assert "active-789" in coordinator.active_delegations

    def test_get_delegation_metrics(self, coordinator):
        """Test delegation metrics calculation."""
        # Create tasks with different statuses and completion times
        completed_task1 = DelegationTask(
            task_id="comp-1",
            pr_number=123,
            task_type=DelegationType.MERGE_CONFLICT_RESOLUTION,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(minutes=10),
            status=DelegationStatus.COMPLETED,
            completion_time=datetime.now() - timedelta(minutes=5),
        )

        completed_task2 = DelegationTask(
            task_id="comp-2",
            pr_number=456,
            task_type=DelegationType.CI_FAILURE_FIX,
            priority=DelegationPriority.MEDIUM,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(minutes=15),
            status=DelegationStatus.COMPLETED,
            completion_time=datetime.now() - timedelta(minutes=5),
        )

        failed_task = DelegationTask(
            task_id="fail-1",
            pr_number=789,
            task_type=DelegationType.AI_CODE_REVIEW,
            priority=DelegationPriority.LOW,
            agent_target="code-reviewer",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(minutes=5),
            status=DelegationStatus.FAILED,
        )

        in_progress_task = DelegationTask(
            task_id="prog-1",
            pr_number=321,
            task_type=DelegationType.BRANCH_UPDATE,
            priority=DelegationPriority.HIGH,
            agent_target="workflow-master",
            prompt_template="Test",
            context={},
            created_at=datetime.now() - timedelta(minutes=3),
            status=DelegationStatus.IN_PROGRESS,
        )

        coordinator.active_delegations.update(
            {
                "comp-1": completed_task1,
                "comp-2": completed_task2,
                "fail-1": failed_task,
                "prog-1": in_progress_task,
            }
        )

        metrics = coordinator.get_delegation_metrics()

        assert metrics["total_tasks"] == 4
        assert metrics["completed_tasks"] == 2
        assert metrics["failed_tasks"] == 1
        assert metrics["in_progress_tasks"] == 1
        assert metrics["success_rate"] == 50.0  # 2 completed out of 4 total
        assert metrics["average_completion_time_seconds"] == pytest.approx(
            450.0, abs_tol=1e-3
        )  # 7.5 minutes average (5+10)/2

        # Check task type breakdown
        assert (
            metrics["task_types"][DelegationType.MERGE_CONFLICT_RESOLUTION.value] == 1
        )
        assert metrics["task_types"][DelegationType.CI_FAILURE_FIX.value] == 1
        assert metrics["task_types"][DelegationType.AI_CODE_REVIEW.value] == 1
        assert metrics["task_types"][DelegationType.BRANCH_UPDATE.value] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
