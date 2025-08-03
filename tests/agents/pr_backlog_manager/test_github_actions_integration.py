"""
Tests for GitHub Actions Integration module.

Tests the GitHubActionsIntegration class and GitHub Actions-specific
functionality including event handling, security validation, and workflow artifacts.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, mock_open

# Add the source directory to the Python path for imports
import sys

source_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".claude",
    "agents",
    "pr-backlog-manager",
)
sys.path.insert(0, source_path)

try:
    from github_actions_integration import (
        GitHubActionsIntegration,
        GitHubContext,
        SecurityConstraints,
        GitHubEventType,
        ProcessingMode,
    )
except ImportError:
    # Fallback for testing without full module setup
    pytest.skip(
        "PR Backlog Manager modules not available for testing", allow_module_level=True
    )


@pytest.fixture
def mock_pr_backlog_manager():
    """Create mock PR backlog manager."""
    mock = Mock()
    mock.process_single_pr.return_value = Mock(
        pr_number=123,
        status=Mock(value="ready"),
        readiness_score=95.0,
        is_ready=True,
        blocking_issues=[],
        resolution_actions=[],
        processing_time=2.5,
    )
    mock.process_backlog.return_value = Mock(
        total_prs=5,
        ready_prs=3,
        blocked_prs=2,
        processing_time=45.0,
        automation_rate=85.0,
        success_rate=90.0,
    )
    return mock


@pytest.fixture
def github_env_vars():
    """Standard GitHub Actions environment variables."""
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_TOKEN": "test-token",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REPOSITORY": "user/test-repo",
        "GITHUB_ACTOR": "test-user",
        "GITHUB_REF": "refs/pull/123/merge",
        "GITHUB_SHA": "abc123",
        "GITHUB_RUN_ID": "456789",
        "GITHUB_RUN_ATTEMPT": "1",
    }


class TestGitHubContext:
    """Test GitHubContext functionality."""

    def test_github_context_creation(self):
        """Test GitHubContext manual creation."""
        context = GitHubContext(
            event_type=GitHubEventType.PULL_REQUEST,
            repository="user/repo",
            pr_number=123,
            actor="developer",
            ref="refs/pull/123/merge",
            sha="abc123",
            workflow_run_id="456789",
            run_attempt=1,
        )

        assert context.event_type == GitHubEventType.PULL_REQUEST
        assert context.repository == "user/repo"
        assert context.pr_number == 123
        assert context.actor == "developer"
        assert context.workflow_run_id == "456789"

    def test_from_environment_pull_request(self):
        """Test GitHubContext creation from environment for pull request."""
        env_vars = {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REPOSITORY": "user/test-repo",
            "GITHUB_ACTOR": "test-user",
            "GITHUB_REF": "refs/pull/123/merge",
            "GITHUB_SHA": "def456",
            "GITHUB_RUN_ID": "789012",
            "GITHUB_RUN_ATTEMPT": "2",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch.object(GitHubContext, "_extract_pr_number", return_value=123),
        ):
            context = GitHubContext.from_environment()

            assert context.event_type == GitHubEventType.PULL_REQUEST
            assert context.repository == "user/test-repo"
            assert context.pr_number == 123
            assert context.actor == "test-user"
            assert context.ref == "refs/pull/123/merge"
            assert context.sha == "def456"
            assert context.workflow_run_id == "789012"
            assert context.run_attempt == 2

    def test_from_environment_schedule(self):
        """Test GitHubContext creation from environment for scheduled event."""
        env_vars = {
            "GITHUB_EVENT_NAME": "schedule",
            "GITHUB_REPOSITORY": "user/scheduled-repo",
            "GITHUB_ACTOR": "github-actions[bot]",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_SHA": "ghi789",
            "GITHUB_RUN_ID": "345678",
            "GITHUB_RUN_ATTEMPT": "1",
        }

        with patch.dict(os.environ, env_vars):
            context = GitHubContext.from_environment()

            assert context.event_type == GitHubEventType.SCHEDULE
            assert context.repository == "user/scheduled-repo"
            assert context.pr_number is None
            assert context.actor == "github-actions[bot]"

    def test_extract_pr_number_from_event(self):
        """Test PR number extraction from GitHub event payload."""
        event_data = {"pull_request": {"number": 456}}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(event_data))),
            patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/path/to/event.json"}),
        ):
            pr_number = GitHubContext._extract_pr_number()
            assert pr_number == 456

    def test_extract_pr_number_from_ref(self):
        """Test PR number extraction from GitHub ref."""
        with (
            patch.dict(os.environ, {"GITHUB_REF": "refs/pull/789/merge"}),
            patch("os.path.exists", return_value=False),
        ):
            pr_number = GitHubContext._extract_pr_number()
            assert pr_number == 789

    def test_extract_pr_number_none(self):
        """Test PR number extraction when not available."""
        with (
            patch.dict(os.environ, {"GITHUB_REF": "refs/heads/main"}, clear=True),
            patch("os.path.exists", return_value=False),
        ):
            pr_number = GitHubContext._extract_pr_number()
            assert pr_number is None


class TestSecurityConstraints:
    """Test SecurityConstraints functionality."""

    def test_security_constraints_creation(self):
        """Test SecurityConstraints manual creation."""
        constraints = SecurityConstraints(
            auto_approve_enabled=True,
            restricted_operations=["delete_repository", "force_push"],
            max_processing_time=300,
            rate_limit_threshold=25,
        )

        assert constraints.auto_approve_enabled is True
        assert "delete_repository" in constraints.restricted_operations
        assert constraints.max_processing_time == 300
        assert constraints.rate_limit_threshold == 25

    def test_from_environment_auto_approve(self):
        """Test SecurityConstraints creation with auto-approve enabled."""
        env_vars = {
            "CLAUDE_AUTO_APPROVE": "true",
            "MAX_PROCESSING_TIME": "600",
            "RATE_LIMIT_THRESHOLD": "30",
        }

        with patch.dict(os.environ, env_vars):
            constraints = SecurityConstraints.from_environment()

            assert constraints.auto_approve_enabled is True
            assert constraints.max_processing_time == 600
            assert constraints.rate_limit_threshold == 30
            assert "delete_repository" in constraints.restricted_operations

    def test_from_environment_no_auto_approve(self):
        """Test SecurityConstraints creation without auto-approve."""
        env_vars = {"CLAUDE_AUTO_APPROVE": "false"}

        with patch.dict(os.environ, env_vars):
            constraints = SecurityConstraints.from_environment()

            assert constraints.auto_approve_enabled is False


class TestGitHubActionsIntegration:
    """Test GitHubActionsIntegration functionality."""

    def test_initialization_valid_environment(
        self, mock_pr_backlog_manager, github_env_vars
    ):
        """Test GitHubActionsIntegration initialization in valid environment."""
        with patch.dict(os.environ, github_env_vars):
            integration = GitHubActionsIntegration(mock_pr_backlog_manager)

            assert integration.pr_backlog_manager == mock_pr_backlog_manager
            assert integration.github_context.event_type == GitHubEventType.PULL_REQUEST
            assert integration.security_constraints.auto_approve_enabled is False

    def test_initialization_invalid_environment(self, mock_pr_backlog_manager):
        """Test GitHubActionsIntegration initialization in invalid environment."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                RuntimeError,
                match="GitHub Actions integration requires GITHUB_ACTIONS=true",
            ):
                GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_initialization_missing_token(self, mock_pr_backlog_manager):
        """Test initialization with missing GitHub token."""
        env_vars = {"GITHUB_ACTIONS": "true"}

        with patch.dict(os.environ, env_vars):
            with pytest.raises(
                RuntimeError, match="GitHub Actions integration requires GITHUB_TOKEN"
            ):
                GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_initialization_auto_approve_validation(
        self, mock_pr_backlog_manager, github_env_vars
    ):
        """Test auto-approve validation during initialization."""
        github_env_vars["CLAUDE_AUTO_APPROVE"] = "true"

        with patch.dict(os.environ, github_env_vars):
            integration = GitHubActionsIntegration(mock_pr_backlog_manager)
            assert integration.security_constraints.auto_approve_enabled is True

    def test_initialization_auto_approve_invalid_event(
        self, mock_pr_backlog_manager, github_env_vars
    ):
        """Test auto-approve validation with invalid event type."""
        github_env_vars.update(
            {"CLAUDE_AUTO_APPROVE": "true", "GITHUB_EVENT_NAME": "push"}
        )

        with patch.dict(os.environ, github_env_vars):
            with pytest.raises(
                RuntimeError, match="Auto-approve not allowed for event type: push"
            ):
                GitHubActionsIntegration(mock_pr_backlog_manager)


class TestProcessingModeDetection:
    """Test processing mode detection functionality."""

    @pytest.fixture
    def integration(self, mock_pr_backlog_manager, github_env_vars):
        """Create GitHubActionsIntegration instance."""
        with (
            patch.dict(os.environ, github_env_vars),
            patch.object(GitHubContext, "_extract_pr_number", return_value=123),
        ):
            return GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_determine_processing_mode_pull_request(self, integration):
        """Test processing mode determination for pull request event."""
        integration.github_context.event_type = GitHubEventType.PULL_REQUEST
        integration.github_context.pr_number = 123

        mode, config = integration.determine_processing_mode()

        assert mode == ProcessingMode.SINGLE_PR
        assert config["pr_number"] == 123
        assert config["reason"] == "pull_request_event"

    def test_determine_processing_mode_workflow_dispatch_with_pr(self, integration):
        """Test processing mode for workflow_dispatch with PR number."""
        integration.github_context.event_type = GitHubEventType.WORKFLOW_DISPATCH

        event_data = {"inputs": {"pr_number": "456"}}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(event_data))),
            patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/path/to/event.json"}),
        ):
            mode, config = integration.determine_processing_mode()

            assert mode == ProcessingMode.SINGLE_PR
            assert config["pr_number"] == 456
            assert config["reason"] == "manual_dispatch"

    def test_determine_processing_mode_workflow_dispatch_no_pr(self, integration):
        """Test processing mode for workflow_dispatch without PR number."""
        integration.github_context.event_type = GitHubEventType.WORKFLOW_DISPATCH

        event_data = {"inputs": {}}

        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(event_data))),
            patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/path/to/event.json"}),
        ):
            mode, config = integration.determine_processing_mode()

            assert mode == ProcessingMode.FULL_BACKLOG
            assert config["reason"] == "manual_backlog_dispatch"

    def test_determine_processing_mode_schedule(self, integration):
        """Test processing mode determination for scheduled event."""
        integration.github_context.event_type = GitHubEventType.SCHEDULE

        mode, config = integration.determine_processing_mode()

        assert mode == ProcessingMode.FULL_BACKLOG
        assert config["reason"] == "scheduled_backlog_processing"

    def test_determine_processing_mode_unknown(self, integration):
        """Test processing mode determination for unknown event."""
        integration.github_context.event_type = GitHubEventType.UNKNOWN

        mode, config = integration.determine_processing_mode()

        assert mode == ProcessingMode.FULL_BACKLOG
        assert config["reason"] == "unknown_event_unknown"


class TestProcessingExecution:
    """Test processing execution functionality."""

    @pytest.fixture
    def integration(self, mock_pr_backlog_manager, github_env_vars):
        """Create GitHubActionsIntegration instance."""
        with patch.dict(os.environ, github_env_vars):
            return GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_execute_single_pr_processing(self, integration, mock_pr_backlog_manager):
        """Test single PR processing execution."""
        mock_assessment = Mock(
            status=Mock(value="ready"),
            readiness_score=95.0,
            is_ready=True,
            blocking_issues=[],
            resolution_actions=[],
            processing_time=2.5,
        )
        mock_pr_backlog_manager.process_single_pr.return_value = mock_assessment

        result = integration._execute_single_pr_processing(123)

        assert result["mode"] == "single_pr"
        assert result["pr_number"] == 123
        assert result["assessment"]["status"] == "ready"
        assert result["assessment"]["readiness_score"] == 95.0
        assert result["assessment"]["is_ready"] is True

        mock_pr_backlog_manager.process_single_pr.assert_called_once_with(123)

    def test_execute_full_backlog_processing(
        self, integration, mock_pr_backlog_manager
    ):
        """Test full backlog processing execution."""
        mock_metrics = Mock(
            total_prs=10,
            ready_prs=7,
            blocked_prs=3,
            processing_time=60.0,
            automation_rate=80.0,
            success_rate=85.0,
        )
        mock_pr_backlog_manager.process_backlog.return_value = mock_metrics

        result = integration._execute_full_backlog_processing()

        assert result["mode"] == "full_backlog"
        assert result["metrics"]["total_prs"] == 10
        assert result["metrics"]["ready_prs"] == 7
        assert result["metrics"]["blocked_prs"] == 3
        assert result["metrics"]["automation_rate"] == 80.0

        mock_pr_backlog_manager.process_backlog.assert_called_once()

    def test_execute_processing_single_pr_success(
        self, integration, mock_pr_backlog_manager
    ):
        """Test full processing execution for single PR."""
        # Mock processing mode detection
        integration.determine_processing_mode = Mock(
            return_value=(
                ProcessingMode.SINGLE_PR,
                {"pr_number": 123, "reason": "test"},
            )
        )

        # Mock artifact creation
        integration._create_workflow_artifacts = Mock()
        integration._generate_workflow_summary = Mock()

        result = integration.execute_processing()

        assert result["success"] is True
        assert result["processing_mode"] == "single_pr"
        assert result["github_context"]["repository"] == "user/test-repo"
        assert "processing_time" in result

        integration._create_workflow_artifacts.assert_called_once()
        integration._generate_workflow_summary.assert_called_once()

    def test_execute_processing_failure(self, integration, mock_pr_backlog_manager):
        """Test processing execution with failure."""
        # Mock processing mode detection to raise exception
        integration.determine_processing_mode = Mock(
            side_effect=Exception("Test error")
        )

        # Mock artifact creation
        integration._create_error_artifacts = Mock()

        result = integration.execute_processing()

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "Exception"

        integration._create_error_artifacts.assert_called_once()


class TestArtifactCreation:
    """Test workflow artifact creation functionality."""

    @pytest.fixture
    def integration(self, mock_pr_backlog_manager, github_env_vars):
        """Create GitHubActionsIntegration instance."""
        with patch.dict(os.environ, github_env_vars):
            return GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_create_workflow_artifacts(self, integration):
        """Test workflow artifact creation."""
        result = {
            "success": True,
            "processing_mode": "single_pr",
            "results": {"pr_number": 123, "assessment": {"status": "ready"}},
        }

        with (
            patch("os.makedirs") as mock_makedirs,
            patch("builtins.open", mock_open()) as mock_file,
        ):
            integration._create_workflow_artifacts(result)

            mock_makedirs.assert_called_once()
            assert mock_file.call_count == 2  # JSON and text files

            # Check JSON artifact
            json_calls = [
                call for call in mock_file.call_args_list if "json" in str(call)
            ]
            assert len(json_calls) == 1

            # Check text artifact
            txt_calls = [
                call for call in mock_file.call_args_list if "txt" in str(call)
            ]
            assert len(txt_calls) == 1

    def test_create_error_artifacts(self, integration):
        """Test error artifact creation."""
        error_result = {
            "success": False,
            "error": "Test error",
            "error_type": "Exception",
        }

        with (
            patch("os.makedirs") as mock_makedirs,
            patch("builtins.open", mock_open()) as mock_file,
        ):
            integration._create_error_artifacts(error_result)

            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()

            # Check that error file was created
            call_args = mock_file.call_args
            assert "error" in call_args[0][0]

    def test_generate_workflow_summary(self, integration):
        """Test GitHub Actions workflow summary generation."""
        result = {
            "success": True,
            "processing_mode": "single_pr",
            "processing_time": 5.5,
            "results": {
                "pr_number": 123,
                "assessment": {
                    "status": "ready",
                    "readiness_score": 95.0,
                    "is_ready": True,
                },
                "blocking_issues": [],
                "resolution_actions": [],
            },
        }

        with (
            patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": "/tmp/summary.md"}),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            integration._generate_workflow_summary(result)

            mock_file.assert_called_once_with("/tmp/summary.md", "a")

            # Check summary content
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            assert "🤖 PR Backlog Manager Results" in written_content
            assert "✅ Success" in written_content
            assert "single_pr" in written_content
            assert "PR Number:** #123" in written_content

    def test_set_github_outputs_single_pr(self, integration):
        """Test GitHub Actions outputs for single PR processing."""
        result = {
            "success": True,
            "processing_mode": "single_pr",
            "processing_time": 3.2,
            "results": {
                "pr_number": 456,
                "assessment": {
                    "is_ready": True,
                    "readiness_score": 88.5,
                    "blocking_issues_count": 0,
                },
            },
        }

        with (
            patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/outputs.txt"}),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            integration.set_github_outputs(result)

            mock_file.assert_called_once_with("/tmp/outputs.txt", "a")

            # Check output content
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            assert "success=true" in written_content
            assert "processing_mode=single_pr" in written_content
            assert "pr_number=456" in written_content
            assert "pr_ready=true" in written_content
            assert "readiness_score=88.5" in written_content

    def test_set_github_outputs_full_backlog(self, integration):
        """Test GitHub Actions outputs for full backlog processing."""
        result = {
            "success": True,
            "processing_mode": "full_backlog",
            "processing_time": 45.8,
            "results": {
                "metrics": {"total_prs": 8, "ready_prs": 5, "automation_rate": 75.0}
            },
        }

        with (
            patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/outputs.txt"}),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            integration.set_github_outputs(result)

            mock_file.assert_called_once_with("/tmp/outputs.txt", "a")

            # Check output content
            written_content = "".join(
                call.args[0] for call in mock_file().write.call_args_list
            )
            assert "success=true" in written_content
            assert "processing_mode=full_backlog" in written_content
            assert "total_prs=8" in written_content
            assert "ready_prs=5" in written_content
            assert "automation_rate=75.0" in written_content


class TestSummaryFormatting:
    """Test summary formatting functionality."""

    @pytest.fixture
    def integration(self, mock_pr_backlog_manager, github_env_vars):
        """Create GitHubActionsIntegration instance."""
        with patch.dict(os.environ, github_env_vars):
            return GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_format_github_summary_single_pr_success(self, integration):
        """Test GitHub summary formatting for successful single PR."""
        result = {
            "success": True,
            "processing_mode": "single_pr",
            "processing_time": 2.5,
            "results": {
                "pr_number": 123,
                "assessment": {
                    "status": "ready",
                    "readiness_score": 95.0,
                    "is_ready": True,
                },
                "blocking_issues": [],
                "resolution_actions": [],
            },
        }

        summary = integration._format_github_summary(result)

        assert "## 🤖 PR Backlog Manager Results" in summary
        assert "**Status:** ✅ Success" in summary
        assert "**Mode:** single_pr" in summary
        assert "**PR Number:** #123" in summary
        assert "**Ready for Review:** ✅ Yes" in summary
        assert "**Readiness Score:** 95.0%" in summary

    def test_format_github_summary_single_pr_with_issues(self, integration):
        """Test GitHub summary formatting for single PR with blocking issues."""
        result = {
            "success": True,
            "processing_mode": "single_pr",
            "processing_time": 3.8,
            "results": {
                "pr_number": 456,
                "assessment": {
                    "status": "blocked",
                    "readiness_score": 65.0,
                    "is_ready": False,
                },
                "blocking_issues": ["PR has merge conflicts", "CI checks are failing"],
                "resolution_actions": ["Delegate to WorkflowMaster", "Fix CI issues"],
            },
        }

        summary = integration._format_github_summary(result)

        assert "**Ready for Review:** ❌ No" in summary
        assert "**Readiness Score:** 65.0%" in summary
        assert "**Blocking Issues:**" in summary
        assert "- PR has merge conflicts" in summary
        assert "- CI checks are failing" in summary
        assert "**Resolution Actions:**" in summary
        assert "- Delegate to WorkflowMaster" in summary

    def test_format_github_summary_full_backlog(self, integration):
        """Test GitHub summary formatting for full backlog processing."""
        result = {
            "success": True,
            "processing_mode": "full_backlog",
            "processing_time": 45.0,
            "results": {
                "metrics": {
                    "total_prs": 12,
                    "ready_prs": 8,
                    "blocked_prs": 4,
                    "automation_rate": 75.0,
                    "success_rate": 90.0,
                }
            },
        }

        summary = integration._format_github_summary(result)

        assert "### Backlog Processing Results" in summary
        assert "**Total PRs Processed:** 12" in summary
        assert "**Ready PRs:** 8" in summary
        assert "**Blocked PRs:** 4" in summary
        assert "**Automation Rate:** 75.0%" in summary
        assert "**Success Rate:** 90.0%" in summary

    def test_format_github_summary_failure(self, integration):
        """Test GitHub summary formatting for failure."""
        result = {
            "success": False,
            "processing_mode": "single_pr",
            "processing_time": 1.2,
            "error": "Test error message",
            "error_type": "TestException",
        }

        summary = integration._format_github_summary(result)

        assert "**Status:** ❌ Failed" in summary
        assert "### Error Details" in summary
        assert "**Error Type:** TestException" in summary
        assert "**Error Message:** Test error message" in summary

    def test_format_text_summary(self, integration):
        """Test plain text summary formatting."""
        result = {
            "success": True,
            "processing_mode": "full_backlog",
            "processing_time": 30.5,
            "github_context": {
                "event_type": "schedule",
                "repository": "user/repo",
                "workflow_run_id": "123456",
            },
            "results": {
                "metrics": {
                    "total_prs": 5,
                    "ready_prs": 3,
                    "blocked_prs": 2,
                    "automation_rate": 80.0,
                    "success_rate": 90.0,
                }
            },
        }

        summary = integration._format_text_summary(result)

        assert "PR Backlog Manager Results" in summary
        assert "Event Type: schedule" in summary
        assert "Repository: user/repo" in summary
        assert "Processing Mode: full_backlog" in summary
        assert "Processing Time: 30.50s" in summary
        assert "Success: True" in summary
        assert "Total PRs: 5" in summary
        assert "Ready PRs: 3" in summary
        assert "Blocked PRs: 2" in summary


class TestRateLimitHandling:
    """Test rate limit handling functionality."""

    @pytest.fixture
    def integration(self, mock_pr_backlog_manager, github_env_vars):
        """Create GitHubActionsIntegration instance."""
        with patch.dict(os.environ, github_env_vars):
            return GitHubActionsIntegration(mock_pr_backlog_manager)

    def test_check_rate_limits(self, integration):
        """Test rate limit checking."""
        # Since this is a placeholder implementation, just verify it returns data
        rate_limits = integration.check_rate_limits()

        assert isinstance(rate_limits, dict)
        assert "core" in rate_limits
        assert "search" in rate_limits
        assert "graphql" in rate_limits

    def test_should_throttle_processing_no_throttling(self, integration):
        """Test throttling decision when rate limits are good."""
        # Mock rate limits to show plenty remaining
        integration.check_rate_limits = Mock(
            return_value={"core": {"remaining": 4000, "limit": 5000}}
        )

        should_throttle = integration.should_throttle_processing()

        assert should_throttle is False

    def test_should_throttle_processing_with_throttling(self, integration):
        """Test throttling decision when rate limits are low."""
        # Mock rate limits to show low remaining
        integration.check_rate_limits = Mock(
            return_value={"core": {"remaining": 10, "limit": 5000}}
        )

        should_throttle = integration.should_throttle_processing()

        assert should_throttle is True

    def test_should_throttle_processing_error_handling(self, integration):
        """Test throttling decision with rate limit check error."""
        # Mock rate limit check to raise exception
        integration.check_rate_limits = Mock(side_effect=Exception("API error"))

        should_throttle = integration.should_throttle_processing()

        # Should not throttle if we can't check (conservative approach)
        assert should_throttle is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
