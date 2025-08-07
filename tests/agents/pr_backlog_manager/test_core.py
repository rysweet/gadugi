"""
Tests for PR Backlog Manager core functionality.

Tests the main PRBacklogManager class including PR discovery, assessment,
and overall backlog management workflows.
"""

try:
    import pytest  # type: ignore[import]
except ImportError:
    from .test_stubs import pytest

import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add the source directories to the Python path for imports
import sys

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
from .test_stubs import (
    PRBacklogManager,
    PRAssessment,
    PRStatus,
    ReadinessCriteria,
    BacklogMetrics,
    GadugiError,
    AgentConfig,
)


class TestPRBacklogManager:
    """Test suite for PRBacklogManager core functionality."""

    @pytest.fixture
    def mock_github_ops(self):
        """Create mock GitHub operations."""
        mock = Mock()
        mock.get_prs.return_value = []
        mock.get_pr_details.return_value = {
            "number": 123,
            "title": "feat: test PR",
            "body": "Test PR description",
            "labels": [],
            "mergeable": True,
            "mergeable_state": "clean",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "base": {"sha": "base123"},
            "head": {"sha": "head123"},
        }
        mock.get_pr_status_checks.return_value = []
        mock.get_pr_reviews.return_value = []
        mock.get_pr_comments.return_value = []
        mock.compare_commits.return_value = {"behind_by": 0, "ahead_by": 1}
        mock.add_pr_labels.return_value = None
        mock.add_pr_comment.return_value = None
        return mock

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        mock = Mock()
        mock.save_state.return_value = None
        mock.load_state.return_value = None
        return mock

    @pytest.fixture
    def mock_task_tracker(self):
        """Create mock task tracker."""
        mock = Mock()
        return mock

    @pytest.fixture
    def pr_backlog_manager(
        self, mock_github_ops, mock_state_manager, mock_task_tracker
    ):
        """Create PRBacklogManager instance with mocked dependencies."""
        with (
            patch("core.GitHubOperations", return_value=mock_github_ops),
            patch("core.StateManager", return_value=mock_state_manager),
            patch("core.TaskTracker", return_value=mock_task_tracker),
        ):
            config = AgentConfig(
                agent_id="test-pr-backlog", name="Test PR Backlog Manager"
            )
            manager = PRBacklogManager(config=config, auto_approve=False)
            return manager

    @pytest.fixture
    def sample_pr_data(self):
        """Sample PR data for testing."""
        return {
            "number": 123,
            "title": "feat: add new feature",
            "body": "This PR adds a new feature to the system",
            "labels": [{"name": "enhancement"}],
            "draft": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:30:00Z",
            "base": {"sha": "base123"},
            "head": {"sha": "head123"},
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        }

    def test_initialization(self, pr_backlog_manager):
        """Test PRBacklogManager initialization."""
        assert pr_backlog_manager.config.agent_id == "test-pr-backlog"
        assert pr_backlog_manager.auto_approve is False
        assert pr_backlog_manager.session_id.startswith("pr-backlog-")
        assert isinstance(pr_backlog_manager.metrics, BacklogMetrics)

    def test_detect_auto_approve_context(self):
        """Test auto-approve context detection."""
        with patch.dict(
            os.environ, {"GITHUB_ACTIONS": "true", "CLAUDE_AUTO_APPROVE": "true"}
        ):
            manager = PRBacklogManager()
            assert manager.auto_approve is True

        with patch.dict(os.environ, {}, clear=True):
            manager = PRBacklogManager()
            assert manager.auto_approve is False

    def test_validate_auto_approve_safety_success(self, pr_backlog_manager):
        """Test auto-approve safety validation success."""
        pr_backlog_manager.auto_approve = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_ACTIONS": "true",
                "CLAUDE_AUTO_APPROVE": "true",
                "GITHUB_EVENT_NAME": "pull_request",
            },
        ):
            # Should not raise exception
            pr_backlog_manager.validate_auto_approve_safety()

    def test_validate_auto_approve_safety_failures(self, pr_backlog_manager):
        """Test auto-approve safety validation failures."""
        pr_backlog_manager.auto_approve = True

        # Test missing GITHUB_ACTIONS
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                GadugiError, match="Auto-approve only allowed in GitHub Actions"
            ):
                pr_backlog_manager.validate_auto_approve_safety()

        # Test missing CLAUDE_AUTO_APPROVE
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with pytest.raises(
                GadugiError, match="Auto-approve not explicitly enabled"
            ):
                pr_backlog_manager.validate_auto_approve_safety()

        # Test invalid event type
        with patch.dict(
            os.environ,
            {
                "GITHUB_ACTIONS": "true",
                "CLAUDE_AUTO_APPROVE": "true",
                "GITHUB_EVENT_NAME": "push",
            },
        ):
            with pytest.raises(GadugiError, match="Auto-approve not allowed for event"):
                pr_backlog_manager.validate_auto_approve_safety()

    def test_should_process_pr(self, pr_backlog_manager, sample_pr_data):
        """Test PR processing eligibility determination."""
        # Normal PR should be processed
        assert pr_backlog_manager._should_process_pr(sample_pr_data) is True

        # Draft PR should not be processed
        draft_pr = sample_pr_data.copy()
        draft_pr["draft"] = True
        assert pr_backlog_manager._should_process_pr(draft_pr) is False

        # PR with ready-seeking-human label should not be processed
        labeled_pr = sample_pr_data.copy()
        labeled_pr["labels"] = [{"name": "ready-seeking-human"}]
        assert pr_backlog_manager._should_process_pr(labeled_pr) is False

        # Very recent PR should not be processed
        recent_pr = sample_pr_data.copy()
        recent_pr["created_at"] = datetime.now().isoformat() + "Z"
        assert pr_backlog_manager._should_process_pr(recent_pr) is False

    def test_prioritize_prs(self, pr_backlog_manager):
        """Test PR prioritization logic."""
        # Create test PRs with different characteristics
        old_pr = {
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "labels": [],
        }

        recent_pr = {
            "created_at": "2024-01-10T12:00:00Z",
            "updated_at": datetime.now().isoformat() + "Z",
            "labels": [],
        }

        high_priority_pr = {
            "created_at": "2024-01-05T12:00:00Z",
            "updated_at": "2024-01-05T12:00:00Z",
            "labels": [{"name": "priority-high"}],
        }

        prs = [old_pr, recent_pr, high_priority_pr]
        prioritized = pr_backlog_manager._prioritize_prs(prs)

        # High priority PR should be first
        assert prioritized[0] == high_priority_pr
        assert len(prioritized) == 3

    def test_evaluate_readiness_criteria(self, pr_backlog_manager, sample_pr_data):
        """Test readiness criteria evaluation."""
        # Mock the individual check methods
        pr_backlog_manager._check_merge_conflicts = Mock(return_value=True)
        pr_backlog_manager._check_ci_status = Mock(return_value=True)
        pr_backlog_manager._check_branch_sync = Mock(return_value=True)
        pr_backlog_manager._check_human_review = Mock(return_value=True)
        pr_backlog_manager._check_ai_review = Mock(return_value=True)
        pr_backlog_manager._check_metadata = Mock(return_value=True)

        criteria = pr_backlog_manager._evaluate_readiness_criteria(sample_pr_data)

        assert len(criteria) == 6
        assert all(criteria.values())  # All should be True
        assert ReadinessCriteria.NO_MERGE_CONFLICTS in criteria
        assert ReadinessCriteria.CI_PASSING in criteria
        assert ReadinessCriteria.UP_TO_DATE in criteria
        assert ReadinessCriteria.HUMAN_REVIEW_COMPLETE in criteria
        assert ReadinessCriteria.AI_REVIEW_COMPLETE in criteria
        assert ReadinessCriteria.METADATA_COMPLETE in criteria

    def test_check_merge_conflicts(self, pr_backlog_manager):
        """Test merge conflict detection."""
        # Clean merge
        clean_pr = {"mergeable": True, "mergeable_state": "clean"}
        assert pr_backlog_manager._check_merge_conflicts(clean_pr) is True

        # Conflicted merge
        conflicted_pr = {"mergeable": False, "mergeable_state": "dirty"}
        assert pr_backlog_manager._check_merge_conflicts(conflicted_pr) is False

        # Unknown state
        unknown_pr = {"mergeable": None, "mergeable_state": "unknown"}
        assert pr_backlog_manager._check_merge_conflicts(unknown_pr) is False

    def test_check_ci_status(self, pr_backlog_manager, mock_github_ops):
        """Test CI status checking."""
        pr_details = {"number": 123}

        # All checks passing
        mock_github_ops.get_pr_status_checks.return_value = [
            {"state": "success", "context": "ci/test"},
            {"state": "success", "context": "ci/build"},
        ]
        assert pr_backlog_manager._check_ci_status(pr_details) is True

        # Some checks failing
        mock_github_ops.get_pr_status_checks.return_value = [
            {"state": "success", "context": "ci/test"},
            {"state": "failure", "context": "ci/build"},
        ]
        assert pr_backlog_manager._check_ci_status(pr_details) is False

    def test_check_human_review(self, pr_backlog_manager, mock_github_ops):
        """Test human review checking."""
        pr_details = {"number": 123}

        # Approved human review
        mock_github_ops.get_pr_reviews.return_value = [
            {"user": {"login": "human-reviewer"}, "state": "APPROVED"},
            {"user": {"login": "bot[bot]"}, "state": "APPROVED"},
        ]
        assert pr_backlog_manager._check_human_review(pr_details) is True

        # No human reviews
        mock_github_ops.get_pr_reviews.return_value = [
            {"user": {"login": "bot[bot]"}, "state": "APPROVED"}
        ]
        assert pr_backlog_manager._check_human_review(pr_details) is False

        # Human review with changes requested
        mock_github_ops.get_pr_reviews.return_value = [
            {"user": {"login": "human-reviewer"}, "state": "CHANGES_REQUESTED"}
        ]
        assert pr_backlog_manager._check_human_review(pr_details) is False

    def test_check_ai_review(self, pr_backlog_manager, mock_github_ops):
        """Test AI review checking."""
        pr_details = {"number": 123}

        # AI review comment present
        mock_github_ops.get_pr_comments.return_value = [
            {"body": "This PR looks good. Code-reviewer approved."},
            {"body": "Some other comment"},
        ]
        assert pr_backlog_manager._check_ai_review(pr_details) is True

        # No AI review comments
        mock_github_ops.get_pr_comments.return_value = [
            {"body": "Human comment"},
            {"body": "Another human comment"},
        ]
        assert pr_backlog_manager._check_ai_review(pr_details) is False

    def test_check_metadata(self, pr_backlog_manager):
        """Test metadata completeness checking."""
        # Complete metadata
        complete_pr = {
            "title": "feat: add new feature",
            "body": "This is a comprehensive description of the changes",
            "labels": [{"name": "enhancement"}],
        }
        assert pr_backlog_manager._check_metadata(complete_pr) is True

        # Missing conventional title
        no_prefix_pr = {
            "title": "add new feature",
            "body": "This is a comprehensive description",
            "labels": [{"name": "enhancement"}],
        }
        assert pr_backlog_manager._check_metadata(no_prefix_pr) is False

        # Missing description
        no_description_pr = {
            "title": "feat: add new feature",
            "body": "",
            "labels": [{"name": "enhancement"}],
        }
        assert pr_backlog_manager._check_metadata(no_description_pr) is False

        # Missing labels
        no_labels_pr = {
            "title": "feat: add new feature",
            "body": "This is a comprehensive description",
            "labels": [],
        }
        assert pr_backlog_manager._check_metadata(no_labels_pr) is False

    def test_identify_blocking_issues(self, pr_backlog_manager):
        """Test blocking issue identification."""
        criteria_met = {
            ReadinessCriteria.NO_MERGE_CONFLICTS: False,
            ReadinessCriteria.CI_PASSING: True,
            ReadinessCriteria.UP_TO_DATE: False,
            ReadinessCriteria.HUMAN_REVIEW_COMPLETE: True,
            ReadinessCriteria.AI_REVIEW_COMPLETE: False,
            ReadinessCriteria.METADATA_COMPLETE: True,
        }

        blocking_issues = pr_backlog_manager._identify_blocking_issues(criteria_met)

        assert len(blocking_issues) == 3
        assert any("merge conflicts" in issue.lower() for issue in blocking_issues)
        assert any("behind main" in issue.lower() for issue in blocking_issues)
        assert any("ai code review" in issue.lower() for issue in blocking_issues)

    def test_generate_resolution_actions(self, pr_backlog_manager):
        """Test resolution action generation."""
        blocking_issues = [
            "PR has merge conflicts that need resolution",
            "CI checks are failing and need to be fixed",
            "Branch is behind main and needs to be updated",
            "AI code review (Phase 9) not completed",
        ]

        actions = pr_backlog_manager._generate_resolution_actions(123, blocking_issues)

        assert len(actions) == 4
        assert any("WorkflowMaster" in action for action in actions)
        assert any("merge conflict" in action.lower() for action in actions)
        assert any("CI" in action for action in actions)
        assert any("code-reviewer" in action for action in actions)

    def test_process_single_pr_success(
        self, pr_backlog_manager, sample_pr_data, mock_github_ops
    ):
        """Test successful single PR processing."""
        mock_github_ops.get_pr_details.return_value = sample_pr_data

        # Mock all readiness checks to pass
        pr_backlog_manager._evaluate_readiness_criteria = Mock(
            return_value={
                ReadinessCriteria.NO_MERGE_CONFLICTS: True,
                ReadinessCriteria.CI_PASSING: True,
                ReadinessCriteria.UP_TO_DATE: True,
                ReadinessCriteria.HUMAN_REVIEW_COMPLETE: True,
                ReadinessCriteria.AI_REVIEW_COMPLETE: True,
                ReadinessCriteria.METADATA_COMPLETE: True,
            }
        )

        pr_backlog_manager._apply_ready_label = Mock()
        pr_backlog_manager._save_assessment = Mock()

        assessment = pr_backlog_manager.process_single_pr(123)

        assert assessment.pr_number == 123
        assert assessment.status == PRStatus.READY
        assert assessment.is_ready is True
        assert assessment.readiness_score == 100.0
        assert len(assessment.blocking_issues) == 0

        pr_backlog_manager._apply_ready_label.assert_called_once_with(123)

    def test_process_single_pr_with_blocking_issues(
        self, pr_backlog_manager, sample_pr_data, mock_github_ops
    ):
        """Test single PR processing with blocking issues."""
        mock_github_ops.get_pr_details.return_value = sample_pr_data

        # Mock some readiness checks to fail
        pr_backlog_manager._evaluate_readiness_criteria = Mock(
            return_value={
                ReadinessCriteria.NO_MERGE_CONFLICTS: False,
                ReadinessCriteria.CI_PASSING: False,
                ReadinessCriteria.UP_TO_DATE: True,
                ReadinessCriteria.HUMAN_REVIEW_COMPLETE: True,
                ReadinessCriteria.AI_REVIEW_COMPLETE: True,
                ReadinessCriteria.METADATA_COMPLETE: True,
            }
        )

        pr_backlog_manager._delegate_issue_resolution = Mock()
        pr_backlog_manager._save_assessment = Mock()

        assessment = pr_backlog_manager.process_single_pr(123)

        assert assessment.pr_number == 123
        assert assessment.status == PRStatus.BLOCKED
        assert assessment.is_ready is False
        assert assessment.readiness_score < 100.0
        assert len(assessment.blocking_issues) > 0

        pr_backlog_manager._delegate_issue_resolution.assert_called_once()

    def test_discover_prs_for_processing(self, pr_backlog_manager, mock_github_ops):
        """Test PR discovery for processing."""
        sample_prs = [
            {
                "number": 123,
                "draft": False,
                "labels": [],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "number": 124,
                "draft": True,  # Should be filtered out
                "labels": [],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "number": 125,
                "draft": False,
                "labels": [{"name": "ready-seeking-human"}],  # Should be filtered out
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
        ]

        mock_github_ops.get_prs.return_value = sample_prs

        discovered_prs = pr_backlog_manager.discover_prs_for_processing()

        # Only the first PR should be included
        assert len(discovered_prs) == 1
        assert discovered_prs[0]["number"] == 123

    def test_apply_ready_label(self, pr_backlog_manager, mock_github_ops):
        """Test applying ready-seeking-human label."""
        pr_backlog_manager._apply_ready_label(123)

        mock_github_ops.add_pr_labels.assert_called_once_with(
            123, ["ready-seeking-human"]
        )
        mock_github_ops.add_pr_comment.assert_called_once()

        # Check comment content
        call_args = mock_github_ops.add_pr_comment.call_args
        comment = call_args[0][1]
        assert "✅ **PR Ready for Human Review**" in comment
        assert "No merge conflicts" in comment
        assert "CI/CD passing" in comment

    def test_save_assessment(self, pr_backlog_manager, mock_state_manager):
        """Test assessment state saving."""
        assessment = PRAssessment(
            pr_number=123,
            status=PRStatus.READY,
            criteria_met={ReadinessCriteria.NO_MERGE_CONFLICTS: True},
            blocking_issues=[],
            resolution_actions=[],
            last_updated=datetime.now(),
            processing_time=1.5,
        )

        pr_backlog_manager._save_assessment(assessment)

        mock_state_manager.save_state.assert_called_once()
        call_args = mock_state_manager.save_state.call_args
        state_key = call_args[0][0]
        state_data = call_args[0][1]

        assert state_key == "pr-assessment-123"
        assert state_data["pr_number"] == 123
        assert state_data["status"] == "ready"
        assert state_data["readiness_score"] == 100.0

    def test_process_backlog_empty(self, pr_backlog_manager, mock_github_ops):
        """Test backlog processing with no PRs."""
        mock_github_ops.get_prs.return_value = []

        metrics = pr_backlog_manager.process_backlog()

        assert metrics.total_prs == 0
        assert metrics.ready_prs == 0
        assert metrics.blocked_prs == 0
        assert metrics.processing_time >= 0

    def test_process_backlog_with_prs(self, pr_backlog_manager, mock_github_ops):
        """Test backlog processing with multiple PRs."""
        # Mock PR discovery
        pr_backlog_manager.discover_prs_for_processing = Mock(
            return_value=[{"number": 123}, {"number": 124}, {"number": 125}]
        )

        # Mock individual PR processing
        ready_assessment = PRAssessment(
            pr_number=123,
            status=PRStatus.READY,
            criteria_met={},
            blocking_issues=[],
            resolution_actions=[],
            last_updated=datetime.now(),
            processing_time=1.0,
        )
        blocked_assessment = PRAssessment(
            pr_number=124,
            status=PRStatus.BLOCKED,
            criteria_met={},
            blocking_issues=["test issue"],
            resolution_actions=[],
            last_updated=datetime.now(),
            processing_time=1.0,
        )

        pr_backlog_manager.process_single_pr = Mock(
            side_effect=[ready_assessment, blocked_assessment, ready_assessment]
        )
        pr_backlog_manager._generate_backlog_report = Mock()

        metrics = pr_backlog_manager.process_backlog()

        assert metrics.total_prs == 3
        assert metrics.ready_prs == 2
        assert metrics.blocked_prs == 1
        assert metrics.automation_rate > 0
        assert metrics.success_rate == 100.0  # All processed successfully


class TestPRAssessment:
    """Test suite for PRAssessment data class."""

    def test_pr_assessment_creation(self):
        """Test PRAssessment creation and properties."""
        criteria_met = {
            ReadinessCriteria.NO_MERGE_CONFLICTS: True,
            ReadinessCriteria.CI_PASSING: True,
            ReadinessCriteria.UP_TO_DATE: False,
            ReadinessCriteria.HUMAN_REVIEW_COMPLETE: True,
            ReadinessCriteria.AI_REVIEW_COMPLETE: False,
            ReadinessCriteria.METADATA_COMPLETE: True,
        }

        assessment = PRAssessment(
            pr_number=123,
            status=PRStatus.PROCESSING,
            criteria_met=criteria_met,
            blocking_issues=["Branch behind main", "AI review missing"],
            resolution_actions=["Update branch", "Invoke code-reviewer"],
            last_updated=datetime.now(),
            processing_time=2.5,
        )

        assert assessment.pr_number == 123
        assert assessment.status == PRStatus.PROCESSING
        assert assessment.is_ready is False  # Not all criteria met
        assert abs(assessment.readiness_score - 66.67) < 0.01  # 4 out of 6 criteria met
        assert len(assessment.blocking_issues) == 2
        assert len(assessment.resolution_actions) == 2

    def test_pr_assessment_ready_state(self):
        """Test PRAssessment in ready state."""
        criteria_met = {criteria: True for criteria in ReadinessCriteria}

        assessment = PRAssessment(
            pr_number=456,
            status=PRStatus.READY,
            criteria_met=criteria_met,
            blocking_issues=[],
            resolution_actions=[],
            last_updated=datetime.now(),
            processing_time=1.0,
        )

        assert assessment.is_ready is True
        assert assessment.readiness_score == 100.0
        assert len(assessment.blocking_issues) == 0


class TestBacklogMetrics:
    """Test suite for BacklogMetrics data class."""

    def test_backlog_metrics_creation(self):
        """Test BacklogMetrics creation."""
        metrics = BacklogMetrics(
            total_prs=10,
            ready_prs=7,
            blocked_prs=2,
            processing_time=45.5,
            automation_rate=85.0,
            success_rate=90.0,
            timestamp=datetime.now(),
        )

        assert metrics.total_prs == 10
        assert metrics.ready_prs == 7
        assert metrics.blocked_prs == 2
        assert metrics.processing_time == 45.5
        assert metrics.automation_rate == 85.0
        assert metrics.success_rate == 90.0
        assert isinstance(metrics.timestamp, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
