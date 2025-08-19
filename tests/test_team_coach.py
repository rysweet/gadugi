"""
Test suite for the Team Coach agent.

Tests core functionality including session analysis, improvement identification,
GitHub integration, and BaseAgent framework integration.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

# Import the Team Coach under test
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", ".claude", "agents", "teamcoach")
)

from team_coach import TeamCoach, SessionMetrics, ImprovementSuggestion, ImprovementType


class TestTeamCoachInitialization:
    """Test Team Coach initialization and setup."""

    def test_team_coach_initialization(self):
        """Test that Team Coach initializes correctly."""
        coach = TeamCoach()

        assert coach.name == "TeamCoach"
        assert len(coach.session_history) == 0
        assert len(coach.improvement_history) == 0

    def test_team_coach_with_config(self):
        """Test Team Coach initialization with custom config."""
        config = {"test_config": "value"}
        coach = TeamCoach(config)

        assert coach.config == config
        assert coach.name == "TeamCoach"


class TestSessionAnalysis:
    """Test session analysis functionality."""

    def test_sync_analyze_session_basic(self):
        """Test basic session analysis."""
        coach = TeamCoach()

        session_data = {
            "session_id": "test_session_001",
            "start_time": "2025-01-08T10:00:00Z",
            "end_time": "2025-01-08T12:00:00Z",
            "tasks": ["task1", "task2", "task3"],
            "errors": ["error1"],
            "test_failures": 2,
            "code_changes": 15,
            "pr_created": True,
            "review_comments": 3,
        }

        metrics = coach._sync_analyze_session(session_data)

        assert metrics.session_id == "test_session_001"
        assert metrics.tasks_completed == 3
        assert metrics.errors_encountered == 1
        assert metrics.test_failures == 2
        assert metrics.code_changes == 15
        assert metrics.pr_created is True
        assert metrics.review_comments == 3
        assert 0 <= metrics.performance_score <= 1

    def test_session_analysis_via_execute(self):
        """Test session analysis through execute interface."""
        coach = TeamCoach()

        context = {
            "action": "analyze_session",
            "session_data": {
                "session_id": "test_session_002",
                "tasks": ["task1", "task2"],
                "errors": [],
                "test_failures": 0,
                "pr_created": True,
            },
        }

        result = coach._execute_core(context)

        assert result["success"] is True
        assert "metrics" in result
        assert result["metrics"]["session_id"] == "test_session_002"
        assert result["metrics"]["tasks_completed"] == 2
        assert result["metrics"]["errors_encountered"] == 0

    def test_performance_score_calculation(self):
        """Test performance score calculation logic."""
        coach = TeamCoach()

        # High performance session
        high_perf_data = {
            "tasks": ["task1", "task2", "task3", "task4"],
            "errors": [],
            "test_failures": 0,
            "pr_created": True,
        }

        high_score = coach._calculate_session_performance_score(high_perf_data)

        # Low performance session
        low_perf_data = {
            "tasks": [],
            "errors": ["error1", "error2", "error3"],
            "test_failures": 5,
            "pr_created": False,
        }

        low_score = coach._calculate_session_performance_score(low_perf_data)

        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1


class TestImprovementIdentification:
    """Test improvement identification functionality."""

    def test_identify_improvements_no_tasks(self):
        """Test improvement identification for session with no completed tasks."""
        coach = TeamCoach()

        metrics = SessionMetrics(
            session_id="test_session",
            start_time=datetime.now(),
            end_time=datetime.now(),
            tasks_completed=0,
            errors_encountered=2,
            test_failures=0,
            code_changes=0,
            pr_created=False,
            review_comments=0,
            performance_score=0.1,
        )

        suggestions = coach._sync_identify_improvements(metrics)

        # Should identify no tasks completed issue
        assert len(suggestions) > 0
        assert any(s.type == ImprovementType.PROCESS for s in suggestions)
        assert any("No tasks completed" in s.title for s in suggestions)

    def test_identify_improvements_low_performance(self):
        """Test improvement identification for low performance session."""
        coach = TeamCoach()

        metrics = SessionMetrics(
            session_id="test_session",
            start_time=datetime.now(),
            end_time=datetime.now(),
            tasks_completed=1,
            errors_encountered=0,
            test_failures=0,
            code_changes=5,
            pr_created=True,
            review_comments=0,
            performance_score=0.3,  # Low performance
        )

        suggestions = coach._sync_identify_improvements(metrics)

        # Should identify performance issue
        assert any(s.type == ImprovementType.PERFORMANCE for s in suggestions)
        assert len(suggestions) > 0


class TestPerformanceTrends:
    """Test performance trend analysis."""

    def test_trend_analysis_insufficient_data(self):
        """Test trend analysis with insufficient session history."""
        coach = TeamCoach()

        context = {"action": "track_performance_trends"}
        result = coach._execute_core(context)

        assert result["success"] is True
        assert result["trends"] == []
        assert "Insufficient data" in result["message"]

    def test_trend_analysis_with_data(self):
        """Test trend analysis with sufficient session history."""
        coach = TeamCoach()

        # Add mock session history
        for i in range(10):
            metrics = SessionMetrics(
                session_id=f"session_{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                tasks_completed=i % 3 + 1,
                errors_encountered=i % 2,
                test_failures=0,
                code_changes=10,
                pr_created=True,
                review_comments=0,
                performance_score=0.5 + (i * 0.03),  # Gradually improving
            )
            coach.session_history.append(metrics)

        context = {"action": "track_performance_trends"}
        result = coach._execute_core(context)

        assert result["success"] is True
        assert len(result["trends"]) > 0

        trend = result["trends"][0]
        assert "metric_name" in trend
        assert "trend_direction" in trend
        assert "current_value" in trend
        assert "previous_value" in trend
        assert "change_percentage" in trend


class TestGitHubIntegration:
    """Test GitHub integration functionality."""

    def test_create_improvement_issue_mock(self):
        """Test GitHub issue creation (mocked)."""
        coach = TeamCoach()

        suggestion_data = {
            "title": "Test Improvement",
            "description": "Test description",
            "type": "performance",
            "priority": "high",
        }

        context = {"action": "create_improvement_issue", "suggestion": suggestion_data}

        result = coach._execute_core(context)

        assert result["success"] is True
        assert "issue_url" in result
        assert "github.com" in result["issue_url"]
        assert "message" in result


class TestCoachingReports:
    """Test coaching report generation."""

    def test_generate_coaching_report_empty(self):
        """Test coaching report generation with no session history."""
        coach = TeamCoach()

        context = {"action": "generate_coaching_report"}
        result = coach._execute_core(context)

        assert result["success"] is True
        assert "report" in result

        report = result["report"]
        assert "generated_at" in report
        assert "sessions_analyzed" in report
        assert "average_performance" in report
        assert "recommendations" in report
        assert report["sessions_analyzed"] == 0
        assert report["average_performance"] == 0

    def test_generate_coaching_report_with_data(self):
        """Test coaching report generation with session history."""
        coach = TeamCoach()

        # Add some session history
        for i in range(3):
            metrics = SessionMetrics(
                session_id=f"session_{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                tasks_completed=2,
                errors_encountered=1,
                test_failures=0,
                code_changes=10,
                pr_created=True,
                review_comments=0,
                performance_score=0.7,
            )
            coach.session_history.append(metrics)

        context = {"action": "generate_coaching_report"}
        result = coach._execute_core(context)

        assert result["success"] is True
        report = result["report"]
        assert report["sessions_analyzed"] == 3
        assert (
            abs(report["average_performance"] - 0.7) < 0.01
        )  # Allow for floating point imprecision


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_action(self):
        """Test handling of invalid action."""
        coach = TeamCoach()

        context = {"action": "invalid_action"}
        result = coach._execute_core(context)

        assert result["success"] is False
        assert "Unknown action" in result["error"]
        assert "available_actions" in result

    def test_malformed_session_data(self):
        """Test handling of malformed session data."""
        coach = TeamCoach()

        context = {
            "action": "analyze_session",
            "session_data": None,  # Invalid data
        }

        result = coach._execute_core(context)
        # Should handle gracefully - might succeed or fail depending on implementation
        # The important thing is that it doesn't crash
        assert "success" in result


class TestStatusAndUtilities:
    """Test utility methods and status reporting."""

    def test_get_status_summary(self):
        """Test status summary generation."""
        coach = TeamCoach()

        # Add some test data
        metrics = SessionMetrics(
            session_id="test_session",
            start_time=datetime.now(),
            end_time=datetime.now(),
            tasks_completed=2,
            errors_encountered=0,
            test_failures=0,
            code_changes=10,
            pr_created=True,
            review_comments=0,
            performance_score=0.8,
        )
        coach.session_history.append(metrics)

        summary = coach.get_status_summary()

        assert summary["name"] == "TeamCoach"
        assert summary["sessions_analyzed"] == 1
        assert summary["improvements_identified"] == 0
        assert summary["last_analysis"] == "test_session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
