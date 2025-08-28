"""
Comprehensive tests for the Team Coach agent.

These tests validate the Team Coach's core functionality including:
- Session analysis and metric extraction
- Improvement identification and prioritization
- GitHub issue creation (mocked)
- Performance trend calculation
- Pattern learning functionality
- Integration with BaseAgent framework
- Event handling capabilities
"""

import pytest
from datetime import datetime

# Import the Team Coach under test
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", ".claude", "agents", "teamcoach")
)

from team_coach import (  # type: ignore[import]
    TeamCoach,
    SessionMetrics,
    ImprovementType,
)


class TestTeamCoachInitialization:
    """Test Team Coach initialization and setup."""

    def test_team_coach_initialization(self):
        """Test that Team Coach initializes correctly."""
        coach = TeamCoach()

        assert coach.name == "TeamCoach"
        assert coach.performance_analyzer is not None  # type: ignore[union-attr]
        assert coach.capability_assessment is not None  # type: ignore[union-attr]
        assert coach.coaching_engine is not None  # type: ignore[union-attr]
        assert len(coach.session_history) == 0
        assert len(coach.improvement_history) == 0

    def test_team_coach_with_config(self):
        """Test Team Coach initialization with custom config."""
        config = {
            "performance_thresholds": {"max_execution_time": 600},
            "learning_enabled": True,
        }

        coach = TeamCoach(config)
        assert coach.config == config
        assert coach.name == "TeamCoach"

    def test_inherited_capabilities(self):
        """Test that Team Coach inherits IntegratedAgent capabilities."""
        coach = TeamCoach()

        # Check inherited methods exist
        assert hasattr(coach, "validate_input")
        assert hasattr(coach, "start_monitoring")
        assert hasattr(coach, "stop_monitoring")
        assert hasattr(coach, "record_execution")
        assert hasattr(coach, "get_performance_metrics")
        assert hasattr(coach, "get_learning_summary")


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

        assert result["success"] is True  # type: ignore[index]
        assert "metrics" in result
        assert result["metrics"]["session_id"] == "test_session_002"  # type: ignore[index]
        assert result["metrics"]["tasks_completed"] == 2  # type: ignore[index]
        assert result["metrics"]["errors_encountered"] == 0  # type: ignore[index]

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

    def test_datetime_parsing(self):
        """Test datetime parsing functionality."""
        coach = TeamCoach()

        # Test ISO format
        iso_dt = coach._parse_datetime("2025-01-08T10:00:00Z")
        assert isinstance(iso_dt, datetime)

        # Test datetime object
        dt_obj = datetime.now()
        parsed_dt = coach._parse_datetime(dt_obj)
        assert parsed_dt == dt_obj

        # Test invalid input
        invalid_dt = coach._parse_datetime("invalid")
        assert isinstance(invalid_dt, datetime)

        # Test None input
        none_dt = coach._parse_datetime(None)
        assert isinstance(none_dt, datetime)


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
        assert any("performance score" in s.description.lower() for s in suggestions)

    def test_improvement_identification_via_execute(self):
        """Test improvement identification through execute interface."""
        coach = TeamCoach()

        metrics_data = {
            "session_id": "test_session",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "tasks_completed": 0,
            "errors_encountered": 5,
            "test_failures": 2,
            "code_changes": 0,
            "pr_created": False,
            "review_comments": 0,
            "performance_score": 0.2,
        }

        context = {"action": "identify_improvements", "metrics": metrics_data}

        result = coach._execute_core(context)

        assert result["success"] is True  # type: ignore[index]
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0  # type: ignore[index]

        # Check suggestion structure
        suggestion = result["suggestions"][0]
        assert "type" in suggestion
        assert "title" in suggestion
        assert "description" in suggestion
        assert "priority" in suggestion
        assert "estimated_impact" in suggestion
        assert "implementation_steps" in suggestion


class TestPerformanceTrends:
    """Test performance trend analysis."""

    def test_trend_analysis_insufficient_data(self):
        """Test trend analysis with insufficient session history."""
        coach = TeamCoach()

        context = {"action": "track_performance_trends"}
        result = coach._execute_core(context)

        assert result["success"] is True  # type: ignore[index]
        assert result["trends"] == []  # type: ignore[index]
        assert "Insufficient data" in result["message"]  # type: ignore[index]

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

        assert result["success"] is True  # type: ignore[index]
        assert len(result["trends"]) > 0  # type: ignore[index]

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

        assert result["success"] is True  # type: ignore[index]
        assert "issue_url" in result
        assert "github.com" in result["issue_url"]  # type: ignore[index]
        assert "message" in result


class TestCoachingReports:
    """Test coaching report generation."""

    def test_generate_coaching_report_empty(self):
        """Test coaching report generation with no session history."""
        coach = TeamCoach()

        context = {"action": "generate_coaching_report"}
        result = coach._execute_core(context)

        assert result["success"] is True  # type: ignore[index]
        assert "report" in result

        report = result["report"]
        assert "generated_at" in report
        assert "sessions_analyzed" in report
        assert "average_performance" in report
        assert "recommendations" in report
        assert report["sessions_analyzed"] == 0  # type: ignore[index]
        assert report["average_performance"] == 0  # type: ignore[index]

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

        assert result["success"] is True  # type: ignore[index]
        report = result["report"]
        assert report["sessions_analyzed"] == 3  # type: ignore[index]
        assert report["average_performance"] == 0.7  # type: ignore[index]


class TestPatternLearning:
    """Test pattern learning functionality."""

    def test_pattern_learning_basic(self):
        """Test basic pattern learning."""
        coach = TeamCoach()

        # Create test sessions
        test_sessions = []
        for i in range(5):
            metrics = SessionMetrics(
                session_id=f"session_{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                tasks_completed=i + 1,
                errors_encountered=0 if i % 2 == 0 else 2,
                test_failures=0,
                code_changes=10,
                pr_created=True,
                review_comments=0,
                performance_score=0.9 if i % 2 == 0 else 0.3,
            )
            test_sessions.append(metrics)

        coach.session_history = test_sessions

        context = {"action": "learn_from_patterns", "sessions": test_sessions}

        result = coach._execute_core(context)

        assert result["success"] is True  # type: ignore[index]
        assert "patterns" in result

        patterns = result["patterns"]
        assert "successful_sessions" in patterns
        assert "unsuccessful_sessions" in patterns
        assert "insights" in patterns


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_action(self):
        """Test handling of invalid action."""
        coach = TeamCoach()

        context = {"action": "invalid_action"}
        result = coach._execute_core(context)

        assert result["success"] is False  # type: ignore[index]
        assert "Unknown action" in result["error"]  # type: ignore[index]
        assert "available_actions" in result

    def test_malformed_session_data(self):
        """Test handling of malformed session data."""
        coach = TeamCoach()

        context = {
            "action": "analyze_session",
            "session_data": None,  # Invalid data
        }

        result = coach._execute_core(context)
        # Should handle gracefully and create default session
        assert result["success"] is True  # type: ignore[index]

    def test_empty_metrics_for_improvements(self):
        """Test improvement identification with minimal metrics."""
        coach = TeamCoach()

        context = {
            "action": "identify_improvements",
            "metrics": {
                "session_id": "test",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "tasks_completed": 5,  # Good performance
                "errors_encountered": 0,
                "test_failures": 0,
                "code_changes": 20,
                "pr_created": True,
                "review_comments": 0,
                "performance_score": 0.9,
            },
        }

        result = coach._execute_core(context)

        assert result["success"] is True  # type: ignore[index]
        # Should have minimal or no suggestions for good performance
        assert "suggestions" in result


class TestIntegrationWithBaseAgent:
    """Test integration with BaseAgent framework."""

    def test_security_validation(self):
        """Test security validation from SecurityAwareAgent."""
        coach = TeamCoach()

        # Test valid input
        valid_input = {"action": "analyze_session", "data": "clean"}
        assert coach.validate_input(valid_input) is True

        # Test potentially dangerous input
        dangerous_input = "<script>alert('xss')</script>"
        assert coach.validate_input(dangerous_input) is False

    def test_performance_monitoring(self):
        """Test performance monitoring from PerformanceMonitoredAgent."""
        coach = TeamCoach()

        coach.start_monitoring()
        assert coach.start_time is not None  # type: ignore[union-attr]

        coach.stop_monitoring()
        assert len(coach.execution_times) > 0

    def test_learning_capabilities(self):
        """Test learning capabilities from LearningEnabledAgent."""
        coach = TeamCoach()

        context = {"action": "analyze_session", "test": "data"}
        result = {"success": True, "learned": "something"}

        coach.record_execution(context, result)
        assert len(coach.history) == 1

        learning_summary = coach.get_learning_summary()
        assert "total_executions" in learning_summary

    def test_full_execute_with_monitoring(self):
        """Test full execute cycle with monitoring and learning."""
        coach = TeamCoach()

        context = {
            "input": {"action": "analyze_session"},  # Valid input for security
            "action": "analyze_session",
            "session_data": {
                "session_id": "integration_test",
                "tasks": ["task1"],
                "errors": [],
                "pr_created": True,
            },
        }

        result = coach.execute(context)

        # Should succeed with full monitoring
        assert result["success"] is True  # type: ignore[index]
        assert len(coach.execution_times) > 0
        assert len(coach.history) > 0


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

        assert summary["name"] == "TeamCoach"  # type: ignore[index]
        assert summary["sessions_analyzed"] == 1  # type: ignore[index]
        assert summary["improvements_identified"] == 0  # type: ignore[index]
        assert summary["last_analysis"] == "test_session"  # type: ignore[index]
        assert "performance_metrics" in summary
        assert "learning_summary" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
