"""
Unit tests for PhaseEnforcer

Tests the phase enforcement system that guarantees Phase 9 and 10
execution without manual intervention.
"""

import pytest
import os
import json
import time
from unittest.mock import Mock, MagicMock, patch

# Import the module under test

# sys.path manipulation removed to ensure consistent package imports

from claude.shared.phase_enforcer import (
    PhaseEnforcer,
    EnforcementRule,
    EnforcementResult,
    enforce_phase_9,
    enforce_phase_10,
)

# Import workflow engine for WorkflowPhase and WorkflowState
from claude.shared.workflow_engine import WorkflowPhase, WorkflowState


class TestPhaseEnforcer:
    """Test suite for PhaseEnforcer class"""

    def setup_method(self):
        """Setup test environment before each test"""
        self.enforcer = PhaseEnforcer()
        self.test_pr_number = 123

        # Create test workflow state
        self.workflow_state = WorkflowState(
            task_id="test-enforcement",
            prompt_file="test_prompt.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[WorkflowPhase.INIT, WorkflowPhase.BRANCH_CREATION],
            pr_number=self.test_pr_number,
            branch_name="test-branch",  # Add branch_name for branch_pushed condition
        )

    def test_phase_enforcer_initialization(self):
        """Test PhaseEnforcer initialization with default rules"""
        enforcer = PhaseEnforcer()

        # Check default enforcement rules exist
        assert "CODE_REVIEW" in enforcer.enforcement_rules
        assert "REVIEW_RESPONSE" in enforcer.enforcement_rules

        # Check code review rule configuration
        code_review_rule = enforcer.enforcement_rules["CODE_REVIEW"]
        assert code_review_rule.phase == WorkflowPhase.CODE_REVIEW
        assert code_review_rule.max_attempts == 3
        assert code_review_rule.timeout_seconds == 900
        assert "pr_exists" in code_review_rule.required_conditions
        assert "branch_pushed" in code_review_rule.required_conditions

        # Check review response rule configuration
        review_rule = enforcer.enforcement_rules["REVIEW_RESPONSE"]
        assert review_rule.phase == WorkflowPhase.REVIEW_RESPONSE
        assert review_rule.max_attempts == 3
        assert code_review_rule.timeout_seconds == 900
        assert "code_review_completed" in review_rule.required_conditions

        # Check circuit breaker configuration
        assert enforcer.circuit_breaker_threshold == 5
        assert enforcer.circuit_breaker_timeout == 300
        assert enforcer.circuit_breaker_state == {}

        # Check monitoring setup
        assert enforcer.enforcement_log == []
        assert enforcer.performance_metrics == {}

    def test_enforcement_rule_creation(self):
        """Test EnforcementRule creation and properties"""
        rule = EnforcementRule(
            phase=WorkflowPhase.CODE_REVIEW,
            max_attempts=5,
            timeout_seconds=1200,
            retry_delay_seconds=60,
            required_conditions=["pr_exists", "branch_pushed"],
        )

        assert rule.phase == WorkflowPhase.CODE_REVIEW
        assert rule.max_attempts == 5
        assert rule.timeout_seconds == 1200
        assert rule.retry_delay_seconds == 60
        assert rule.required_conditions == ["pr_exists", "branch_pushed"]
        assert rule.enforcement_action is None

    def test_enforcement_result_creation(self):
        """Test EnforcementResult creation and properties"""
        result = EnforcementResult(
            phase=WorkflowPhase.CODE_REVIEW,
            success=True,
            attempts=2,
            total_time=45.5,
            error_message=None,
            details={"method": "claude_agent", "pr_number": 123},
        )

        assert result.phase == WorkflowPhase.CODE_REVIEW
        assert result.success is True
        assert result.attempts == 2
        assert result.total_time == 45.5
        assert result.error_message is None
        assert result.details["method"] == "claude_agent"
        assert result.details["pr_number"] == 123

    def test_check_required_conditions_success(self):
        """Test required conditions checking when all conditions are met"""
        conditions = ["pr_exists", "branch_pushed"]

        # Workflow state with all required conditions
        workflow_state = WorkflowState(
            task_id="test-conditions",
            prompt_file="test.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=123,
            branch_name="feature/test-branch",
        )

        conditions_met, missing = self.enforcer._check_required_conditions(
            conditions, workflow_state, {}
        )

        assert conditions_met is True
        assert missing == []

    def test_check_required_conditions_missing_pr(self):
        """Test required conditions checking when PR is missing"""
        conditions = ["pr_exists", "branch_pushed"]

        # Workflow state without PR number
        workflow_state = WorkflowState(
            task_id="test-no-pr",
            prompt_file="test.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=None,  # Missing PR
            branch_name="feature/test-branch",
        )

        conditions_met, missing = self.enforcer._check_required_conditions(
            conditions, workflow_state, {}
        )

        assert conditions_met is False
        assert "pr_exists" in missing

    def test_check_required_conditions_missing_branch(self):
        """Test required conditions checking when branch is missing"""
        conditions = ["pr_exists", "branch_pushed"]

        # Workflow state without branch name
        workflow_state = WorkflowState(
            task_id="test-no-branch",
            prompt_file="test.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=123,
            branch_name=None,  # Missing branch
        )

        conditions_met, missing = self.enforcer._check_required_conditions(
            conditions, workflow_state, {}
        )

        assert conditions_met is False
        assert "branch_pushed" in missing

    def test_check_required_conditions_code_review_completed(self):
        """Test code review completion condition checking"""
        conditions = ["code_review_completed"]

        # Workflow state with code review completed
        workflow_state = WorkflowState(
            task_id="test-review-complete",
            prompt_file="test.md",
            current_phase=WorkflowPhase.REVIEW_RESPONSE,
            completed_phases=[WorkflowPhase.CODE_REVIEW],  # Code review completed
            pr_number=123,
        )

        conditions_met, missing = self.enforcer._check_required_conditions(
            conditions, workflow_state, {}
        )

        assert conditions_met is True
        assert missing == []

    def test_circuit_breaker_initially_closed(self):
        """Test circuit breaker is initially closed (not open)"""
        is_open = self.enforcer._is_circuit_breaker_open(WorkflowPhase.CODE_REVIEW)
        assert is_open is False

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        phase = WorkflowPhase.CODE_REVIEW

        # Record failures up to threshold
        for _ in range(self.enforcer.circuit_breaker_threshold):
            self.enforcer._record_circuit_breaker_failure(phase)

        # Circuit breaker should now be open
        is_open = self.enforcer._is_circuit_breaker_open(phase)
        assert is_open is True

    def test_circuit_breaker_resets_after_timeout(self):
        """Test circuit breaker resets after timeout period"""
        phase = WorkflowPhase.CODE_REVIEW

        # Record failures to open circuit breaker
        for _ in range(self.enforcer.circuit_breaker_threshold):
            self.enforcer._record_circuit_breaker_failure(phase)

        # Manually set last failure time to simulate timeout
        phase_name = phase.name
        self.enforcer.circuit_breaker_state[phase_name]["last_failure"] = (
            time.time() - self.enforcer.circuit_breaker_timeout - 1
        )

        # Circuit breaker should now be closed (reset)
        is_open = self.enforcer._is_circuit_breaker_open(phase)
        assert is_open is False

    def test_circuit_breaker_reset_on_success(self):
        """Test circuit breaker resets on successful execution"""
        phase = WorkflowPhase.CODE_REVIEW

        # Record some failures
        for _ in range(2):
            self.enforcer._record_circuit_breaker_failure(phase)

        # Reset on success
        self.enforcer._reset_circuit_breaker(phase)

        # Check that failures are reset
        phase_name = phase.name
        assert self.enforcer.circuit_breaker_state[phase_name]["failures"] == 0
        assert self.enforcer.circuit_breaker_state[phase_name]["last_failure"] is None

    @patch("subprocess.run")
    def test_enforce_code_review_claude_agent_success(self, mock_subprocess):
        """Test successful code review enforcement via Claude agent"""
        # Mock successful Claude CLI invocation
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Code review completed successfully", stderr=""
        )

        success, message, details = self.enforcer._enforce_code_review(
            self.workflow_state, {}
        )

        assert success is True
        assert "code review completed" in message.lower()
        assert details["method"] == "claude_agent"
        assert details["pr_number"] == self.test_pr_number

        # Verify Claude CLI was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "claude" in call_args
        assert "-p" in call_args

    @patch("subprocess.run")
    def test_enforce_code_review_script_fallback(self, mock_subprocess):
        """Test code review enforcement fallback to script"""
        # Mock Claude CLI failure, script success
        mock_subprocess.side_effect = [
            Mock(returncode=1, stdout="", stderr="Claude failed"),  # Claude fails
            Mock(returncode=0, stdout="Script success", stderr=""),  # Script succeeds
        ]

        # Mock script file existence
        with patch("os.path.exists", return_value=True):
            success, message, details = self.enforcer._enforce_code_review(
                self.workflow_state, {}
            )

        assert success is True
        assert "enforced via script" in message.lower()
        assert details["method"] == "enforcement_script"

    @patch("subprocess.run")
    def test_enforce_code_review_github_cli_fallback(self, mock_subprocess):
        """Test code review enforcement fallback to GitHub CLI"""
        # Mock all previous methods failing, GitHub CLI succeeding
        # With os.path.exists returning False, script method is skipped, so only 2 calls
        mock_subprocess.side_effect = [
            Mock(returncode=1, stdout="", stderr="Claude failed"),  # Claude fails
            Mock(
                returncode=0, stdout="Review posted", stderr=""
            ),  # GitHub CLI review succeeds (no script call since file doesn't exist)
        ]

        # Mock script file not existing (skips script method)
        with patch("os.path.exists", return_value=False):
            success, message, details = self.enforcer._enforce_code_review(
                self.workflow_state, {}
            )

        assert success is True
        assert "automated code review posted" in message.lower()
        assert details["method"] == "github_cli_review"

    @patch("subprocess.run")
    def test_enforce_code_review_comment_fallback(self, mock_subprocess):
        """Test code review enforcement final fallback to comment"""
        # Mock all methods failing except final comment
        # With os.path.exists returning False, script method is skipped, so only 3 calls
        mock_subprocess.side_effect = [
            Mock(returncode=1, stdout="", stderr="Claude failed"),  # Claude fails
            Mock(
                returncode=1, stdout="", stderr="Review failed"
            ),  # GitHub review fails (no script call since file doesn't exist)
            Mock(returncode=0, stdout="Comment added", stderr=""),  # Comment succeeds
        ]

        with patch("os.path.exists", return_value=False):
            success, message, details = self.enforcer._enforce_code_review(
                self.workflow_state, {}
            )

        assert success is True
        assert "enforcement comment added" in message.lower()
        assert details["method"] == "github_comment"

    @patch("subprocess.run")
    def test_enforce_code_review_all_methods_fail(self, mock_subprocess):
        """Test code review enforcement when all methods fail"""
        # Mock all methods failing
        mock_subprocess.return_value = Mock(
            returncode=1, stdout="", stderr="All failed"
        )

        with patch("os.path.exists", return_value=False):
            success, message, details = self.enforcer._enforce_code_review(
                self.workflow_state, {}
            )

        assert success is False
        assert "all code review enforcement methods failed" in message.lower()

    def test_enforce_code_review_no_pr_number(self):
        """Test code review enforcement when PR number is missing"""
        # Workflow state without PR number
        workflow_state = WorkflowState(
            task_id="test-no-pr",
            prompt_file="test.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=None,
        )

        success, message, details = self.enforcer._enforce_code_review(
            workflow_state, {}
        )

        assert success is False
        assert "no pr number available" in message.lower()

    @patch("subprocess.run")
    def test_enforce_review_response_with_changes_requested(self, mock_subprocess):
        """Test review response enforcement when changes are requested"""
        # Mock GitHub CLI returning reviews with changes requested
        mock_review_data = {
            "reviews": [
                {"state": "APPROVED"},
                {"state": "CHANGES_REQUESTED"},
                {"state": "COMMENTED"},
            ]
        }

        mock_subprocess.side_effect = [
            Mock(
                returncode=0, stdout=json.dumps(mock_review_data), stderr=""
            ),  # gh pr view
            Mock(returncode=0, stdout="Comment posted", stderr=""),  # gh pr comment
        ]

        success, message, details = self.enforcer._enforce_review_response(
            self.workflow_state, {}
        )

        assert success is True
        assert "review response posted" in message.lower()
        assert details["response_method"] == "review_response_comment"
        assert details["addressed_reviews"] == 1  # One CHANGES_REQUESTED review

    @patch("subprocess.run")
    def test_enforce_review_response_no_changes_needed(self, mock_subprocess):
        """Test review response enforcement when no changes are requested"""
        # Mock GitHub CLI returning reviews without changes requested
        mock_review_data = {"reviews": [{"state": "APPROVED"}, {"state": "COMMENTED"}]}

        mock_subprocess.return_value = Mock(
            returncode=0, stdout=json.dumps(mock_review_data), stderr=""
        )

        success, message, details = self.enforcer._enforce_review_response(
            self.workflow_state, {}
        )

        assert success is True
        assert "no review response needed" in message.lower()
        assert details["response_method"] == "none_needed"
        assert details["total_reviews"] == 2

    def test_enforce_review_response_no_pr_number(self):
        """Test review response enforcement when PR number is missing"""
        # Workflow state without PR number
        workflow_state = WorkflowState(
            task_id="test-no-pr",
            prompt_file="test.md",
            current_phase=WorkflowPhase.REVIEW_RESPONSE,
            completed_phases=[],
            pr_number=None,
        )

        success, message, details = self.enforcer._enforce_review_response(
            workflow_state, {}
        )

        assert success is False
        assert "no pr number available" in message.lower()

    def test_enforce_phase_no_rule(self):
        """Test phase enforcement when no rule is defined"""
        # Try to enforce a phase without a rule
        result = self.enforcer.enforce_phase(
            WorkflowPhase.INIT,  # No rule defined for INIT
            self.workflow_state,
        )

        assert result.success is False
        assert "no enforcement rule defined" in result.error_message.lower()
        assert result.attempts == 0

    def test_enforce_phase_circuit_breaker_open(self):
        """Test phase enforcement when circuit breaker is open"""
        phase = WorkflowPhase.CODE_REVIEW

        # Open circuit breaker by recording failures
        for _ in range(self.enforcer.circuit_breaker_threshold):
            self.enforcer._record_circuit_breaker_failure(phase)

        result = self.enforcer.enforce_phase(phase, self.workflow_state)

        assert result.success is False
        assert "circuit breaker open" in result.error_message.lower()
        assert result.attempts == 0

    def test_enforce_phase_missing_conditions(self):
        """Test phase enforcement when required conditions are missing"""
        # Workflow state missing PR number (required for code review)
        workflow_state = WorkflowState(
            task_id="test-missing-conditions",
            prompt_file="test.md",
            current_phase=WorkflowPhase.CODE_REVIEW,
            completed_phases=[],
            pr_number=None,  # Missing required condition
            branch_name="feature/test",
        )

        result = self.enforcer.enforce_phase(WorkflowPhase.CODE_REVIEW, workflow_state)

        assert result.success is False
        assert "required conditions not met" in result.error_message.lower()
        assert "pr_exists" in result.error_message

    @patch("subprocess.run")
    def test_enforce_critical_phases_success(self, mock_subprocess):
        """Test enforcement of all critical phases"""
        # Create workflow state without critical phases completed
        workflow_state = WorkflowState(
            task_id="test-critical",
            prompt_file="test.md",
            current_phase=WorkflowPhase.PR_CREATION,
            completed_phases=[WorkflowPhase.INIT, WorkflowPhase.BRANCH_CREATION],
            pr_number=123,
            branch_name="test-branch",
        )

        # Mock successful subprocess calls for both phases
        mock_subprocess.side_effect = [
            Mock(
                returncode=0, stdout="Code review completed successfully", stderr=""
            ),  # Phase 9
            Mock(returncode=0, stdout='{"reviews": []}', stderr=""),  # Phase 10 check
        ]

        results = self.enforcer.enforce_critical_phases(workflow_state)

        assert len(results) == 2
        result_keys = [k.name if hasattr(k, "name") else k for k in results]
        assert "CODE_REVIEW" in result_keys
        assert "REVIEW_RESPONSE" in result_keys
        assert all(result.success for result in results.values())

    @patch("time.sleep")
    @patch("subprocess.run")
    def test_enforce_critical_phases_failure_stops_chain(
        self, mock_subprocess, mock_sleep
    ):
        """Test that critical phase failure stops dependent phases"""
        # Create workflow state without critical phases completed
        workflow_state = WorkflowState(
            task_id="test-critical-fail",
            prompt_file="test.md",
            current_phase=WorkflowPhase.PR_CREATION,
            completed_phases=[WorkflowPhase.INIT, WorkflowPhase.BRANCH_CREATION],
            pr_number=123,
            branch_name="test-branch",
        )

        # Mock all subprocess calls to fail
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Failed")
        # Mock sleep to prevent timeout
        mock_sleep.return_value = None

        with patch("os.path.exists", return_value=False):
            results = self.enforcer.enforce_critical_phases(workflow_state)

        # Should only have CODE_REVIEW result (REVIEW_RESPONSE not attempted)
        assert len(results) == 1
        result_keys = [k.name if hasattr(k, "name") else k for k in results]
        assert "CODE_REVIEW" in result_keys
        key = next(
            k for k in results if (k.name if hasattr(k, "name") else k) == "CODE_REVIEW"
        )
        assert results[key].success is False
        assert "REVIEW_RESPONSE" not in result_keys

    def test_add_enforcement_rule(self):
        """Test adding custom enforcement rule"""
        custom_rule = EnforcementRule(
            phase=WorkflowPhase.INIT,
            max_attempts=10,
            timeout_seconds=300,
            retry_delay_seconds=15,
            required_conditions=["custom_condition"],
        )

        self.enforcer.add_enforcement_rule(custom_rule)

        assert "INIT" in self.enforcer.enforcement_rules
        added_rule = self.enforcer.enforcement_rules["INIT"]
        assert added_rule.max_attempts == 10
        assert added_rule.timeout_seconds == 300
        assert added_rule.retry_delay_seconds == 15
        assert "custom_condition" in added_rule.required_conditions

    def test_log_enforcement_result(self):
        """Test enforcement result logging"""
        result = EnforcementResult(
            phase=WorkflowPhase.CODE_REVIEW,
            success=True,
            attempts=1,
            total_time=30.5,
            details={"method": "test"},
        )

        initial_log_length = len(self.enforcer.enforcement_log)
        self.enforcer._log_enforcement_result(result, "Test message")

        assert len(self.enforcer.enforcement_log) == initial_log_length + 1

        log_entry = self.enforcer.enforcement_log[-1]
        assert log_entry["phase"] == "CODE_REVIEW"
        assert log_entry["success"] is True
        assert log_entry["attempts"] == 1
        assert log_entry["total_time"] == 30.5
        assert log_entry["message"] == "Test message"
        assert log_entry["details"] == {"method": "test"}
        assert "timestamp" in log_entry

    def test_get_enforcement_statistics_empty(self):
        """Test getting statistics when no enforcement has occurred"""
        stats = self.enforcer.get_enforcement_statistics()

        assert stats["total_enforcements"] == 0
        assert stats["success_rate"] == 0
        assert stats["phase_stats"] == {}
        assert stats["circuit_breaker_state"] == {}

    def test_get_enforcement_statistics_with_data(self):
        """Test getting statistics with enforcement data"""
        # Add some mock log entries
        self.enforcer.enforcement_log = [
            {
                "phase": "CODE_REVIEW",
                "success": True,
                "attempts": 1,
                "total_time": 30.0,
                "message": "Success",
                "details": {},
            },
            {
                "phase": "CODE_REVIEW",
                "success": False,
                "attempts": 3,
                "total_time": 90.0,
                "message": "Failed",
                "details": {},
            },
            {
                "phase": "REVIEW_RESPONSE",
                "success": True,
                "attempts": 1,
                "total_time": 15.0,
                "message": "Success",
                "details": {},
            },
        ]

        stats = self.enforcer.get_enforcement_statistics()

        assert stats["total_enforcements"] == 3
        assert stats["success_rate"] == 2 / 3  # 2 successes out of 3

        # Check phase-specific stats
        assert "CODE_REVIEW" in stats["phase_stats"]
        assert "REVIEW_RESPONSE" in stats["phase_stats"]

        code_review_stats = stats["phase_stats"]["CODE_REVIEW"]
        assert code_review_stats["total"] == 2
        assert code_review_stats["successful"] == 1
        assert code_review_stats["success_rate"] == 0.5
        assert code_review_stats["avg_attempts"] == 2.0  # (1+3)/2
        assert code_review_stats["avg_time"] == 60.0  # (30+90)/2

    def test_export_enforcement_log(self):
        """Test exporting enforcement log to JSON"""
        # Add some mock log entries
        self.enforcer.enforcement_log = [
            {
                "phase": "CODE_REVIEW",
                "success": True,
                "attempts": 1,
                "total_time": 30.0,
                "message": "Success",
                "details": {},
                "timestamp": "2023-01-01T12:00:00",
            }
        ]

        filename = self.enforcer.export_enforcement_log()

        # Check file was created
        assert os.path.exists(filename)

        # Check file content
        with open(filename, "r") as f:
            log_data = json.load(f)

        assert "metadata" in log_data
        assert "statistics" in log_data
        assert "log_entries" in log_data
        assert log_data["metadata"]["total_entries"] == 1
        assert len(log_data["log_entries"]) == 1

        # Cleanup
        os.remove(filename)


class TestConvenienceFunctions:
    """Test suite for convenience functions"""

    @patch("subprocess.run")
    def test_enforce_phase_9_success(self, mock_subprocess):
        """Test enforce_phase_9 convenience function success"""
        # Mock successful Claude CLI
        mock_subprocess.return_value = Mock(
            returncode=0, stdout="Code review completed successfully", stderr=""
        )

        result = enforce_phase_9(123)

        assert result is True

    @patch("time.sleep")
    @patch("subprocess.run")
    def test_enforce_phase_9_failure(self, mock_subprocess, mock_sleep):
        """Test enforce_phase_9 convenience function failure"""
        # Mock all methods failing
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Failed")
        # Mock sleep to prevent timeout
        mock_sleep.return_value = None

        with patch("os.path.exists", return_value=False):
            result = enforce_phase_9(123)

        assert result is False

    @patch("subprocess.run")
    def test_enforce_phase_10_success(self, mock_subprocess):
        """Test enforce_phase_10 convenience function success"""
        # Mock successful GitHub CLI returning no changes requested
        mock_review_data = {"reviews": [{"state": "APPROVED"}]}
        mock_subprocess.return_value = Mock(
            returncode=0, stdout=json.dumps(mock_review_data), stderr=""
        )

        result = enforce_phase_10(123)

        assert result is True

    @patch("time.sleep")
    @patch("subprocess.run")
    def test_enforce_phase_10_failure(self, mock_subprocess, mock_sleep):
        """Test enforce_phase_10 convenience function failure"""
        # Mock GitHub CLI failure
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Failed")
        # Mock sleep to prevent timeout
        mock_sleep.return_value = None

        result = enforce_phase_10(123)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
