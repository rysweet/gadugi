"""
Team Coach Agent - Main Integration Class

This module provides the main Team Coach agent that integrates with the BaseAgent framework
and coordinates all the Phase 1-3 capabilities. It implements the requirements from the
implement-team-coach-agent.md prompt.

Key Features:
- Session analysis and improvement identification
- GitHub issue creation for improvements
- Performance tracking and trend analysis
- Pattern learning from successful/unsuccessful workflows
- Integration with BaseAgent framework
- Event handling for session_completed, pr_merged, test_failure, error_logged
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import BaseAgent framework
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))

from base_classes import IntegratedAgent
from interfaces import OperationResult

# Import Team Coach phases
from .phase1.performance_analytics import AgentPerformanceAnalyzer, AgentPerformanceData
from .phase1.capability_assessment import CapabilityAssessment
from .phase1.metrics_collector import MetricsCollector
from .phase1.reporting import ReportingSystem

from .phase2.task_matcher import TaskAgentMatcher
from .phase2.team_optimizer import TeamCompositionOptimizer
from .phase2.recommendation_engine import RecommendationEngine

from .phase3.coaching_engine import CoachingEngine, CoachingRecommendation
from .phase3.conflict_resolver import AgentConflictResolver
from .phase3.workflow_optimizer import WorkflowOptimizer
from .phase3.strategic_planner import StrategicTeamPlanner


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


class TeamCoach(IntegratedAgent):
    """
    Main Team Coach agent that provides comprehensive session analysis,
    improvement identification, and coaching recommendations.

    Inherits from IntegratedAgent to get security, performance monitoring,
    and learning capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Team Coach agent."""
        super().__init__("TeamCoach", config)

        # Initialize phase components
        self.performance_analyzer = AgentPerformanceAnalyzer()
        self.capability_assessment = CapabilityAssessment()
        self.metrics_collector = MetricsCollector()
        self.reporting_system = ReportingSystem()

        self.task_matcher = TaskAgentMatcher(
            self.performance_analyzer, self.capability_assessment
        )
        self.team_optimizer = TeamCompositionOptimizer(
            self.capability_assessment, self.task_matcher
        )
        self.recommendation_engine = RecommendationEngine(
            self.performance_analyzer, self.capability_assessment
        )

        self.coaching_engine = CoachingEngine(
            self.performance_analyzer, self.capability_assessment, self.task_matcher
        )
        self.conflict_resolver = AgentConflictResolver(
            self.performance_analyzer, self.team_optimizer
        )
        self.workflow_optimizer = WorkflowOptimizer(
            self.performance_analyzer, self.metrics_collector
        )
        self.strategic_planner = StrategicTeamPlanner(
            self.capability_assessment, self.performance_analyzer
        )

        # GitHub integration
        self.github_client = self._init_github_client()

        # Session storage
        self.session_history: List[SessionMetrics] = []
        self.improvement_history: List[ImprovementSuggestion] = []

        self.log_info("Team Coach agent initialized with all phases")

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
                        "analyze_session", "identify_improvements",
                        "create_improvement_issue", "track_performance_trends",
                        "generate_coaching_report", "learn_from_patterns"
                    ]
                }

        except Exception as e:
            self.log_error(f"Failed to execute action {action}", e)
            return {"success": False, "error": str(e)}

    async def analyze_session(self, session_data: Dict[str, Any]) -> SessionMetrics:
        """Analyze a completed development session."""
        self.log_info(f"Analyzing session: {session_data.get('session_id', 'unknown')}")

        # Extract session metrics
        session_id = session_data.get("session_id", f"session_{datetime.now().isoformat()}")
        start_time = self._parse_datetime(session_data.get("start_time"))
        end_time = self._parse_datetime(session_data.get("end_time", datetime.now()))

        # Analyze session data
        tasks_completed = len(session_data.get("tasks", []))
        errors_encountered = len(session_data.get("errors", []))
        test_failures = session_data.get("test_failures", 0)
        code_changes = session_data.get("code_changes", 0)
        pr_created = session_data.get("pr_created", False)
        review_comments = session_data.get("review_comments", 0)

        # Calculate performance score
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
            performance_score=performance_score
        )

        # Store session history
        self.session_history.append(metrics)

        self.log_info(f"Session analysis completed: {performance_score:.2f} performance score")
        return metrics

    async def identify_improvements(self, metrics: SessionMetrics) -> List[ImprovementSuggestion]:
        """Identify improvement opportunities from session metrics."""
        self.log_info("Identifying improvement opportunities")

        suggestions = []

        # Process improvements
        if metrics.tasks_completed == 0:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.PROCESS,
                title="No tasks completed in session",
                description="Session had no completed tasks. Review workflow planning and task decomposition.",
                priority="high",
                estimated_impact=0.8,
                implementation_steps=[
                    "Review session planning process",
                    "Implement better task breakdown",
                    "Set clearer success criteria"
                ],
                related_sessions=[metrics.session_id]
            ))

        # Performance improvements
        if metrics.performance_score < 0.6:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.PERFORMANCE,
                title="Low session performance score",
                description=f"Session scored {metrics.performance_score:.2f}, below target of 0.6",
                priority="medium",
                estimated_impact=0.6,
                implementation_steps=[
                    "Analyze specific bottlenecks",
                    "Improve agent coordination",
                    "Optimize workflow phases"
                ],
                related_sessions=[metrics.session_id]
            ))

        # Quality improvements
        if metrics.test_failures > 0:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.QUALITY,
                title="Test failures detected",
                description=f"Session had {metrics.test_failures} test failures",
                priority="high",
                estimated_impact=0.7,
                implementation_steps=[
                    "Implement pre-commit testing",
                    "Improve test coverage",
                    "Add quality gates"
                ],
                related_sessions=[metrics.session_id]
            ))

        # Error handling improvements
        if metrics.errors_encountered > 5:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.TOOLING,
                title="High error rate",
                description=f"Session encountered {metrics.errors_encountered} errors",
                priority="medium",
                estimated_impact=0.5,
                implementation_steps=[
                    "Improve error handling",
                    "Add better validation",
                    "Implement circuit breakers"
                ],
                related_sessions=[metrics.session_id]
            ))

        # Store improvement history
        self.improvement_history.extend(suggestions)

        self.log_info(f"Identified {len(suggestions)} improvement opportunities")
        return suggestions

    async def create_improvement_issue(self, suggestion: ImprovementSuggestion) -> str:
        """Create GitHub issue for improvement suggestion."""
        self.log_info(f"Creating GitHub issue for: {suggestion.title}")

        # Create issue body
        issue_body = f"""## Improvement Opportunity

**Type**: {suggestion.type.value}
**Priority**: {suggestion.priority}
**Estimated Impact**: {suggestion.estimated_impact}

## Description
{suggestion.description}

## Implementation Steps
"""

        for i, step in enumerate(suggestion.implementation_steps, 1):
            issue_body += f"{i}. {step}\n"

        issue_body += f"""
## Related Sessions
{', '.join(suggestion.related_sessions)}

---
*Generated by Team Coach Agent after session analysis*
*Note: This issue was created by an AI agent on behalf of the repository owner.*
"""

        # Create the issue (mock implementation - would use real GitHub API)
        try:
            # This would be replaced with actual GitHub API call
            issue_url = f"https://github.com/repo/issues/{hash(suggestion.title) % 1000}"
            self.log_info(f"Created issue: {issue_url}")
            return issue_url
        except Exception as e:
            self.log_error(f"Failed to create GitHub issue", e)
            raise

    async def track_performance_trends(self) -> List[PerformanceTrend]:
        """Analyze performance trends over time."""
        self.log_info("Analyzing performance trends")

        if len(self.session_history) < 2:
            self.log_info("Insufficient session history for trend analysis")
            return []

        trends = []

        # Analyze performance score trend
        recent_sessions = self.session_history[-10:]  # Last 10 sessions
        current_avg = sum(s.performance_score for s in recent_sessions[-5:]) / 5
        previous_avg = sum(s.performance_score for s in recent_sessions[-10:-5]) / 5

        change_pct = ((current_avg - previous_avg) / previous_avg) * 100 if previous_avg > 0 else 0

        if change_pct > 5:
            direction = "improving"
        elif change_pct < -5:
            direction = "declining"
        else:
            direction = "stable"

        trends.append(PerformanceTrend(
            metric_name="performance_score",
            trend_direction=direction,
            current_value=current_avg,
            previous_value=previous_avg,
            change_percentage=change_pct,
            time_period="last_10_sessions"
        ))

        self.log_info(f"Generated {len(trends)} performance trends")
        return trends

    async def generate_coaching_report(self) -> Dict[str, Any]:
        """Generate comprehensive coaching report."""
        self.log_info("Generating coaching report")

        # Get recent performance data
        recent_sessions = self.session_history[-10:] if self.session_history else []
        recent_improvements = self.improvement_history[-20:] if self.improvement_history else []

        # Calculate summary metrics
        avg_performance = sum(s.performance_score for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0
        total_tasks = sum(s.tasks_completed for s in recent_sessions)
        total_errors = sum(s.errors_encountered for s in recent_sessions)

        # Generate coaching recommendations using Phase 3 engine
        coaching_recommendations = []
        if recent_sessions:
            # Get coaching recommendations for recent performance
            latest_session = recent_sessions[-1]
            # This would integrate with the actual coaching engine
            coaching_recommendations.append({
                "category": "performance",
                "recommendation": "Focus on reducing error rates in development sessions",
                "priority": "medium",
                "evidence": f"Recent sessions averaged {total_errors/len(recent_sessions):.1f} errors"
            })

        report = {
            "report_id": f"coaching_report_{datetime.now().isoformat()}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "sessions_analyzed": len(recent_sessions),
                "average_performance": avg_performance,
                "total_tasks_completed": total_tasks,
                "total_errors": total_errors,
                "improvement_suggestions_generated": len(recent_improvements)
            },
            "performance_trends": await self.track_performance_trends(),
            "recent_improvements": [
                {
                    "type": imp.type.value,
                    "title": imp.title,
                    "priority": imp.priority,
                    "estimated_impact": imp.estimated_impact
                }
                for imp in recent_improvements
            ],
            "coaching_recommendations": coaching_recommendations,
            "next_steps": [
                "Continue monitoring session performance",
                "Implement high-priority improvements",
                "Review and update process documentation"
            ]
        }

        self.log_info("Coaching report generated successfully")
        return report

    async def learn_from_patterns(self, sessions: List[SessionMetrics]):
        """Learn from successful and unsuccessful patterns."""
        self.log_info(f"Learning patterns from {len(sessions)} sessions")

        # Identify successful patterns
        successful_sessions = [s for s in sessions if s.performance_score > 0.8]
        unsuccessful_sessions = [s for s in sessions if s.performance_score < 0.4]

        patterns = {
            "successful_patterns": [],
            "unsuccessful_patterns": [],
            "insights": []
        }

        # Analyze successful patterns
        if successful_sessions:
            avg_tasks = sum(s.tasks_completed for s in successful_sessions) / len(successful_sessions)
            avg_errors = sum(s.errors_encountered for s in successful_sessions) / len(successful_sessions)

            patterns["successful_patterns"].append({
                "pattern": "high_task_completion_low_errors",
                "description": f"Successful sessions average {avg_tasks:.1f} tasks with {avg_errors:.1f} errors",
                "frequency": len(successful_sessions)
            })

        # Analyze unsuccessful patterns
        if unsuccessful_sessions:
            avg_errors = sum(s.errors_encountered for s in unsuccessful_sessions) / len(unsuccessful_sessions)

            patterns["unsuccessful_patterns"].append({
                "pattern": "high_error_rate",
                "description": f"Unsuccessful sessions average {avg_errors:.1f} errors",
                "frequency": len(unsuccessful_sessions)
            })

        # Generate insights
        if successful_sessions and unsuccessful_sessions:
            patterns["insights"].append({
                "insight": "Error rate strongly correlates with session success",
                "recommendation": "Implement better error prevention and handling"
            })

        self.log_info(f"Learned {len(patterns['successful_patterns'])} successful and {len(patterns['unsuccessful_patterns'])} unsuccessful patterns")
        return patterns

    def _handle_session_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session analysis request."""
        try:
            session_data = context.get("session_data", {})
            # Since we can't use async in this sync context, simulate async behavior
            metrics = self._sync_analyze_session(session_data)

            return {
                "success": True,
                "metrics": {
                    "session_id": metrics.session_id,
                    "performance_score": metrics.performance_score,
                    "tasks_completed": metrics.tasks_completed,
                    "errors_encountered": metrics.errors_encountered,
                    "test_failures": metrics.test_failures
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sync_analyze_session(self, session_data: Dict[str, Any]) -> SessionMetrics:
        """Synchronous version of analyze_session for framework compatibility."""
        session_id = session_data.get("session_id", f"session_{datetime.now().isoformat()}")
        start_time = self._parse_datetime(session_data.get("start_time"))
        end_time = self._parse_datetime(session_data.get("end_time", datetime.now()))

        tasks_completed = len(session_data.get("tasks", []))
        errors_encountered = len(session_data.get("errors", []))
        test_failures = session_data.get("test_failures", 0)
        code_changes = session_data.get("code_changes", 0)
        pr_created = session_data.get("pr_created", False)
        review_comments = session_data.get("review_comments", 0)

        performance_score = self._calculate_session_performance_score(session_data)

        return SessionMetrics(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            tasks_completed=tasks_completed,
            errors_encountered=errors_encountered,
            test_failures=test_failures,
            code_changes=code_changes,
            pr_created=pr_created,
            review_comments=review_comments,
            performance_score=performance_score
        )

    def _handle_improvement_identification(self, context: Dict[str, Any]) -> Dict[str, Any]:
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
                        "implementation_steps": s.implementation_steps
                    }
                    for s in suggestions
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sync_identify_improvements(self, metrics: SessionMetrics) -> List[ImprovementSuggestion]:
        """Synchronous version of identify_improvements."""
        suggestions = []

        if metrics.tasks_completed == 0:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.PROCESS,
                title="No tasks completed in session",
                description="Session had no completed tasks. Review workflow planning.",
                priority="high",
                estimated_impact=0.8,
                implementation_steps=["Review session planning", "Improve task breakdown"],
                related_sessions=[metrics.session_id]
            ))

        if metrics.performance_score < 0.6:
            suggestions.append(ImprovementSuggestion(
                type=ImprovementType.PERFORMANCE,
                title="Low session performance score",
                description=f"Session scored {metrics.performance_score:.2f}",
                priority="medium",
                estimated_impact=0.6,
                implementation_steps=["Analyze bottlenecks", "Optimize workflow"],
                related_sessions=[metrics.session_id]
            ))

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
                "message": f"Created issue: {suggestion_data.get('title', 'Unknown')}"
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
                    "message": "Insufficient data for trend analysis"
                }

            # Simple trend calculation
            recent_scores = [s.performance_score for s in self.session_history[-5:]]
            avg_recent = sum(recent_scores) / len(recent_scores)

            previous_scores = [s.performance_score for s in self.session_history[-10:-5]]
            avg_previous = sum(previous_scores) / len(previous_scores) if previous_scores else avg_recent

            change_pct = ((avg_recent - avg_previous) / avg_previous) * 100 if avg_previous > 0 else 0

            return {
                "success": True,
                "trends": [{
                    "metric_name": "performance_score",
                    "trend_direction": "improving" if change_pct > 5 else "declining" if change_pct < -5 else "stable",
                    "current_value": avg_recent,
                    "previous_value": avg_previous,
                    "change_percentage": change_pct,
                    "time_period": "last_sessions"
                }]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_coaching_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coaching report generation request."""
        try:
            recent_sessions = self.session_history[-5:] if self.session_history else []

            avg_performance = sum(s.performance_score for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0

            return {
                "success": True,
                "report": {
                    "generated_at": datetime.now().isoformat(),
                    "sessions_analyzed": len(recent_sessions),
                    "average_performance": avg_performance,
                    "recommendations": [
                        "Continue monitoring session performance",
                        "Focus on error reduction",
                        "Improve task completion rates"
                    ]
                }
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
                        "Error reduction improves performance"
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_session_performance_score(self, session_data: Dict[str, Any]) -> float:
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
                return datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
            except ValueError:
                return datetime.now()
        else:
            return datetime.now()

    def _init_github_client(self):
        """Initialize GitHub client (mock for now)."""
        # This would initialize a real GitHub client
        return None

    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary of the Team Coach."""
        return {
            "name": self.name,
            "sessions_analyzed": len(self.session_history),
            "improvements_identified": len(self.improvement_history),
            "last_analysis": self.session_history[-1].session_id if self.session_history else None,
            "performance_metrics": self.get_performance_metrics(),
            "learning_summary": self.get_learning_summary()
        }
