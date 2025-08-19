"""
Team Coach Agent - Main Integration Class

This module provides the main Team Coach agent that integrates with the BaseAgent framework.
It's designed to work independently of the phase implementations for testing purposes.

Key Features:
- Session analysis and improvement identification
- GitHub issue creation for improvements
- Performance tracking and trend analysis
- Pattern learning from successful/unsuccessful workflows
- Integration with BaseAgent framework
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Import BaseAgent framework
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

try:
    from base_classes import IntegratedAgent

    base_agent_available = True
except ImportError:
    # Fallback for testing when base classes aren't available
    base_agent_available = False

    class IntegratedAgent:
        def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
            self.name = name
            self.config = config or {}
            self.logger = logging.getLogger(f"test.{name}")
            self.execution_times = []
            self.history = []

        def log_info(self, message: str):
            self.logger.info(message)

        def log_error(self, message: str, exception: Optional[Exception] = None):
            self.logger.error(message, exc_info=exception)

        def validate_input(self, input_data: Any) -> bool:
            return True

        def start_monitoring(self):
            pass

        def stop_monitoring(self):
            pass

        def record_execution(self, context: Dict[str, Any], result: Dict[str, Any]):
            self.history.append({"context": context, "result": result})

        def get_performance_metrics(self) -> Dict[str, Any]:
            return {"executions": len(self.history)}

        def get_learning_summary(self) -> Dict[str, Any]:
            return {"total_executions": len(self.history)}

        def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
            result = self._execute_core(context)
            self.record_execution(context, result)
            return result

        def _execute_core(self, context: Dict[str, Any]) -> Dict[str, Any]:
            raise NotImplementedError


class ImprovementType(Enum):
    """Types of improvements the Team Coach can identify."""

    PROCESS = "process"
    TOOLING = "tooling"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    QUALITY = "quality"


@dataclass
class SessionMetrics:
    """Metrics collected from a completed development session."""

    session_id: str
    start_time: datetime
    end_time: datetime
    tasks_completed: int
    errors_encountered: int
    test_failures: int
    code_changes: int
    pr_created: bool
    review_comments: int
    performance_score: float


@dataclass
class ImprovementSuggestion:
    """Suggestion for process/tooling improvement."""

    type: ImprovementType
    title: str
    description: str
    priority: str  # high, medium, low
    estimated_impact: float  # 0-1 scale
    implementation_steps: List[str]
    related_sessions: List[str] = field(default_factory=list)


@dataclass
class PerformanceTrend:
    """Performance trend analysis result."""

    metric_name: str
    trend_direction: str  # improving, declining, stable
    current_value: float
    previous_value: float
    change_percentage: float
    time_period: str


class TeamCoach(IntegratedAgent):  # type: ignore[misc]
    """
    Main Team Coach agent that provides comprehensive session analysis,
    improvement identification, and coaching recommendations.

    This is a standalone implementation that works without the phase modules
    for testing and initial deployment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Team Coach agent."""
        super().__init__("TeamCoach", config)

        # Session storage
        self.session_history: List[SessionMetrics] = []
        self.improvement_history: List[ImprovementSuggestion] = []

        # GitHub integration (mock for now)
        self.github_client = None

        self.log_info("Team Coach agent initialized (standalone mode)")

    def _execute_core(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution logic for Team Coach agent."""
        action = context.get("action", "analyze_session")

        try:
            if action == "analyze_session":
                return self._handle_session_analysis(context)
            elif action == "identify_improvements":
                return self._handle_improvement_identification(context)
            elif action == "create_improvement_issue":
                return self._handle_issue_creation(context)
            elif action == "track_performance_trends":
                return self._handle_trend_analysis(context)
            elif action == "generate_coaching_report":
                return self._handle_coaching_report(context)
            elif action == "learn_from_patterns":
                return self._handle_pattern_learning(context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "analyze_session",
                        "identify_improvements",
                        "create_improvement_issue",
                        "track_performance_trends",
                        "generate_coaching_report",
                        "learn_from_patterns",
                    ],
                }

        except Exception as e:
            self.log_error(f"Failed to execute action {action}", e)
            return {"success": False, "error": str(e)}

    def _handle_session_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session analysis request."""
        try:
            session_data = context.get("session_data", {})
            metrics = self._sync_analyze_session(session_data)

            return {
                "success": True,
                "metrics": {
                    "session_id": metrics.session_id,
                    "performance_score": metrics.performance_score,
                    "tasks_completed": metrics.tasks_completed,
                    "errors_encountered": metrics.errors_encountered,
                    "test_failures": metrics.test_failures,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sync_analyze_session(self, session_data: Dict[str, Any]) -> SessionMetrics:
        """Analyze a completed development session synchronously."""
        session_id = session_data.get(
            "session_id", f"session_{datetime.now().isoformat()}"
        )
        start_time = self._parse_datetime(session_data.get("start_time"))
        end_time = self._parse_datetime(session_data.get("end_time", datetime.now()))

        tasks_completed = len(session_data.get("tasks", []))
        errors_encountered = len(session_data.get("errors", []))
        test_failures = session_data.get("test_failures", 0)
        code_changes = session_data.get("code_changes", 0)
        pr_created = session_data.get("pr_created", False)
        review_comments = session_data.get("review_comments", 0)

        performance_score = self._calculate_session_performance_score(session_data)

        metrics = SessionMetrics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            tasks_completed=tasks_completed,
            errors_encountered=errors_encountered,
            test_failures=test_failures,
            code_changes=code_changes,
            pr_created=pr_created,
            review_comments=review_comments,
            performance_score=performance_score,
        )

        # Store in history
        self.session_history.append(metrics)

        return metrics

    def _handle_improvement_identification(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle improvement identification request."""
        try:
            metrics_data = context.get("metrics", {})
            # Convert dict back to SessionMetrics
            metrics = SessionMetrics(**metrics_data)

            suggestions = self._sync_identify_improvements(metrics)

            return {
                "success": True,
                "suggestions": [
                    {
                        "type": s.type.value,
                        "title": s.title,
                        "description": s.description,
                        "priority": s.priority,
                        "estimated_impact": s.estimated_impact,
                        "implementation_steps": s.implementation_steps,
                    }
                    for s in suggestions
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sync_identify_improvements(
        self, metrics: SessionMetrics
    ) -> List[ImprovementSuggestion]:
        """Identify improvement opportunities from session metrics."""
        suggestions = []

        # Process improvements for no tasks completed
        if metrics.tasks_completed == 0:
            suggestions.append(
                ImprovementSuggestion(
                    type=ImprovementType.PROCESS,
                    title="No tasks completed in session",
                    description="Session had no completed tasks. Review workflow planning and task decomposition.",
                    priority="high",
                    estimated_impact=0.8,
                    implementation_steps=[
                        "Review session planning process",
                        "Implement better task breakdown",
                        "Set clearer success criteria",
                    ],
                    related_sessions=[metrics.session_id],
                )
            )

        # Performance improvements for low performance scores
        if metrics.performance_score < 0.6:
            suggestions.append(
                ImprovementSuggestion(
                    type=ImprovementType.PERFORMANCE,
                    title="Low session performance score",
                    description=f"Session scored {metrics.performance_score:.2f}, below target of 0.6",
                    priority="medium",
                    estimated_impact=0.6,
                    implementation_steps=[
                        "Analyze specific bottlenecks",
                        "Improve agent coordination",
                        "Optimize workflow phases",
                    ],
                    related_sessions=[metrics.session_id],
                )
            )

        # Quality improvements for test failures
        if metrics.test_failures > 0:
            suggestions.append(
                ImprovementSuggestion(
                    type=ImprovementType.QUALITY,
                    title="Test failures detected",
                    description=f"Session had {metrics.test_failures} test failures",
                    priority="high",
                    estimated_impact=0.7,
                    implementation_steps=[
                        "Implement pre-commit testing",
                        "Improve test coverage",
                        "Add quality gates",
                    ],
                    related_sessions=[metrics.session_id],
                )
            )

        # Tooling improvements for high error rates
        if metrics.errors_encountered > 5:
            suggestions.append(
                ImprovementSuggestion(
                    type=ImprovementType.TOOLING,
                    title="High error rate",
                    description=f"Session encountered {metrics.errors_encountered} errors",
                    priority="medium",
                    estimated_impact=0.5,
                    implementation_steps=[
                        "Improve error handling",
                        "Add better validation",
                        "Implement circuit breakers",
                    ],
                    related_sessions=[metrics.session_id],
                )
            )

        # Store in improvement history
        self.improvement_history.extend(suggestions)

        return suggestions

    def _handle_issue_creation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub issue creation request."""
        try:
            suggestion_data = context.get("suggestion", {})

            # Mock issue creation for now
            issue_url = f"https://github.com/repo/issues/{hash(suggestion_data.get('title', '')) % 1000}"

            return {
                "success": True,
                "issue_url": issue_url,
                "message": f"Created issue: {suggestion_data.get('title', 'Unknown')}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_trend_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance trend analysis request."""
        try:
            if len(self.session_history) < 2:
                return {
                    "success": True,
                    "trends": [],
                    "message": "Insufficient data for trend analysis",
                }

            # Simple trend calculation
            recent_scores = [s.performance_score for s in self.session_history[-5:]]
            avg_recent = sum(recent_scores) / len(recent_scores)

            previous_scores = [
                s.performance_score for s in self.session_history[-10:-5]
            ]
            avg_previous = (
                sum(previous_scores) / len(previous_scores)
                if previous_scores
                else avg_recent
            )

            change_pct = (
                ((avg_recent - avg_previous) / avg_previous) * 100
                if avg_previous > 0
                else 0
            )

            return {
                "success": True,
                "trends": [
                    {
                        "metric_name": "performance_score",
                        "trend_direction": "improving"
                        if change_pct > 5
                        else "declining"
                        if change_pct < -5
                        else "stable",
                        "current_value": avg_recent,
                        "previous_value": avg_previous,
                        "change_percentage": change_pct,
                        "time_period": "last_sessions",
                    }
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_coaching_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coaching report generation request."""
        try:
            recent_sessions = self.session_history[-5:] if self.session_history else []

            avg_performance = (
                sum(s.performance_score for s in recent_sessions) / len(recent_sessions)
                if recent_sessions
                else 0
            )

            return {
                "success": True,
                "report": {
                    "generated_at": datetime.now().isoformat(),
                    "sessions_analyzed": len(recent_sessions),
                    "average_performance": avg_performance,
                    "recommendations": [
                        "Continue monitoring session performance",
                        "Focus on error reduction",
                        "Improve task completion rates",
                    ],
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_pattern_learning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern learning request."""
        try:
            sessions = context.get("sessions", self.session_history)

            successful_count = len([s for s in sessions if s.performance_score > 0.8])
            unsuccessful_count = len([s for s in sessions if s.performance_score < 0.4])

            return {
                "success": True,
                "patterns": {
                    "successful_sessions": successful_count,
                    "unsuccessful_sessions": unsuccessful_count,
                    "insights": [
                        "High task completion correlates with success",
                        "Error reduction improves performance",
                    ],
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_session_performance_score(
        self, session_data: Dict[str, Any]
    ) -> float:
        """Calculate a performance score for the session."""
        tasks_completed = len(session_data.get("tasks", []))
        errors_encountered = len(session_data.get("errors", []))
        test_failures = session_data.get("test_failures", 0)
        pr_created = session_data.get("pr_created", False)

        # Simple scoring algorithm
        score = 0.0

        # Task completion contributes positively
        if tasks_completed > 0:
            score += min(0.4, tasks_completed * 0.1)

        # PR creation is a strong positive signal
        if pr_created:
            score += 0.3

        # Errors and test failures reduce score
        error_penalty = min(0.3, errors_encountered * 0.05)
        test_penalty = min(0.2, test_failures * 0.1)

        score -= error_penalty + test_penalty

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def _parse_datetime(self, dt_input: Any) -> datetime:
        """Parse datetime from various input formats."""
        if isinstance(dt_input, datetime):
            return dt_input
        elif isinstance(dt_input, str):
            try:
                return datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()
        else:
            return datetime.now()

    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary of the Team Coach."""
        return {
            "name": self.name,
            "sessions_analyzed": len(self.session_history),
            "improvements_identified": len(self.improvement_history),
            "last_analysis": self.session_history[-1].session_id
            if self.session_history
            else None,
            "performance_metrics": self.get_performance_metrics(),
            "learning_summary": self.get_learning_summary(),
        }

    # Async interface for compatibility with the prompt requirements
    async def analyze_session(self, session_data: Dict[str, Any]) -> SessionMetrics:
        """Async wrapper for session analysis."""
        return self._sync_analyze_session(session_data)

    async def identify_improvements(
        self, metrics: SessionMetrics
    ) -> List[ImprovementSuggestion]:
        """Async wrapper for improvement identification."""
        return self._sync_identify_improvements(metrics)

    async def create_improvement_issue(self, suggestion: ImprovementSuggestion) -> str:
        """Async wrapper for issue creation."""
        result = self._handle_issue_creation(
            {
                "suggestion": {
                    "title": suggestion.title,
                    "description": suggestion.description,
                    "type": suggestion.type.value,
                    "priority": suggestion.priority,
                }
            }
        )
        if result["success"]:
            return result["issue_url"]
        else:
            raise Exception(result["error"])

    async def track_performance_trends(self) -> List[PerformanceTrend]:
        """Async wrapper for trend analysis."""
        result = self._handle_trend_analysis({})
        if result["success"]:
            trends = []
            for trend_data in result["trends"]:
                trends.append(PerformanceTrend(**trend_data))
            return trends
        else:
            raise Exception(result["error"])

    async def generate_coaching_report(self) -> Dict[str, Any]:
        """Async wrapper for coaching report generation."""
        result = self._handle_coaching_report({})
        if result["success"]:
            return result["report"]
        else:
            raise Exception(result["error"])

    async def learn_from_patterns(self, sessions: List[SessionMetrics]):
        """Async wrapper for pattern learning."""
        return self._handle_pattern_learning({"sessions": sessions})
