#!/usr/bin/env python3
"""
Team Coach Integration Module

This module provides the main integration class for the Team Coach agent,
coordinating all functionality across Phase 1-3 implementations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Phase 1 imports
from .phase1.performance_analytics import AgentPerformanceAnalyzer
from .phase1.capability_assessment import CapabilityAssessment
from .phase1.metrics_collector import MetricsCollector
from .phase1.reporting import ReportingSystem

# Phase 2 imports
from .phase2.task_matcher import TaskAgentMatcher
from .phase2.team_optimizer import TeamCompositionOptimizer
from .phase2.recommendation_engine import RecommendationEngine
from .phase2.realtime_assignment import RealtimeAssignment

# Phase 3 imports
from .phase3.coaching_engine import CoachingEngine
from .phase3.conflict_resolver import ConflictResolver
from .phase3.workflow_optimizer import WorkflowOptimizer
from .phase3.strategic_planner import StrategicPlanner


class TeamCoach:
    """
    Main Team Coach integration class that coordinates all functionality
    across Phase 1-3 implementations.

    Provides intelligent analysis of development sessions, identifies improvement
    opportunities, and creates actionable coaching recommendations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Team Coach with all phase components.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize Phase 1 components
        self.performance_analyzer = AgentPerformanceAnalyzer(self.config.get('performance', {}))
        self.capability_assessment = CapabilityAssessment(self.config.get('capability', {}))
        self.metrics_collector = MetricsCollector(self.config.get('metrics', {}))
        self.reporting_system = ReportingSystem(self.config.get('reporting', {}))

        # Initialize Phase 2 components
        self.task_matcher = TaskAgentMatcher(self.config.get('task_matching', {}))
        self.team_optimizer = TeamCompositionOptimizer(self.config.get('team_optimization', {}))
        self.recommendation_engine = RecommendationEngine(self.config.get('recommendations', {}))
        self.realtime_assignment = RealtimeAssignment(self.config.get('realtime', {}))

        # Initialize Phase 3 components
        self.coaching_engine = CoachingEngine(self.config.get('coaching', {}))
        self.conflict_resolver = ConflictResolver(self.config.get('conflict_resolution', {}))
        self.workflow_optimizer = WorkflowOptimizer(self.config.get('workflow', {}))
        self.strategic_planner = StrategicPlanner(self.config.get('strategic', {}))

        self.logger.info("Team Coach initialized with all phase components")

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Team Coach action based on the request.

        Args:
            request: Action request with 'action' and relevant parameters

        Returns:
            Dictionary containing the action result
        """
        action = request.get('action')

        if not action:
            return {"error": "No action specified"}

        try:
            if action == "analyze_session":
                return self._analyze_session(request.get('session_data', {}))
            elif action == "identify_improvements":
                return self._identify_improvements(request.get('metrics', {}))
            elif action == "track_performance_trends":
                return self._track_performance_trends(request.get('period_days', 30))
            elif action == "generate_coaching_report":
                return self._generate_coaching_report(request.get('agents', []))
            elif action == "optimize_task_assignment":
                return self._optimize_task_assignment(request.get('task', {}), request.get('agents', []))
            elif action == "form_project_team":
                return self._form_project_team(request.get('project', {}), request.get('available_agents', []))
            elif action == "resolve_conflicts":
                return self._resolve_conflicts(request.get('conflicts', []))
            elif action == "optimize_workflow":
                return self._optimize_workflow(request.get('workflow_data', {}))
            elif action == "strategic_planning":
                return self._strategic_planning(request.get('team_data', {}))
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {str(e)}")
            return {"error": f"Action execution failed: {str(e)}"}

    def _analyze_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a development session and extract metrics."""
        try:
            # Use metrics collector to gather session data
            raw_metrics = self.metrics_collector.collect_session_metrics(session_data)

            # Use performance analyzer to process metrics
            performance_analysis = self.performance_analyzer.analyze_performance(raw_metrics)

            # Calculate performance score
            score = self._calculate_performance_score(session_data)

            metrics = {
                "session_id": session_data.get("session_id", f"session_{datetime.now().isoformat()}"),
                "timestamp": datetime.now().isoformat(),
                "tasks_completed": len(session_data.get("tasks", [])),
                "errors_encountered": len(session_data.get("errors", [])),
                "test_failures": session_data.get("test_failures", 0),
                "pr_created": session_data.get("pr_created", False),
                "performance_score": score,
                "duration_minutes": session_data.get("duration_minutes", 0),
                "analysis": performance_analysis
            }

            return {"metrics": metrics, "status": "success"}

        except Exception as e:
            self.logger.error(f"Session analysis failed: {str(e)}")
            return {"error": f"Session analysis failed: {str(e)}"}

    def _identify_improvements(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Identify improvement opportunities based on session metrics."""
        try:
            improvements = []

            # Use coaching engine to identify improvements
            coaching_recommendations = self.coaching_engine.generate_recommendations(metrics)

            # Convert to improvement suggestions
            for rec in coaching_recommendations:
                improvement = {
                    "category": rec.get("category", "general"),
                    "description": rec.get("description", ""),
                    "impact": rec.get("impact", "medium"),
                    "effort": rec.get("effort", "medium"),
                    "priority": rec.get("priority", 50)
                }
                improvements.append(improvement)

            # Add workflow-specific improvements
            workflow_improvements = self.workflow_optimizer.identify_bottlenecks(metrics)
            for bottleneck in workflow_improvements:
                improvement = {
                    "category": "workflow",
                    "description": f"Optimize {bottleneck.get('type', 'unknown')} bottleneck",
                    "impact": "high",
                    "effort": "medium",
                    "priority": 70
                }
                improvements.append(improvement)

            return {"improvements": improvements, "status": "success"}

        except Exception as e:
            self.logger.error(f"Improvement identification failed: {str(e)}")
            return {"error": f"Improvement identification failed: {str(e)}"}

    def _track_performance_trends(self, period_days: int = 30) -> Dict[str, Any]:
        """Track performance trends over the specified period."""
        try:
            # Use performance analyzer to get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            trends = self.performance_analyzer.analyze_trends(start_date, end_date)

            return {"trends": trends, "period_days": period_days, "status": "success"}

        except Exception as e:
            self.logger.error(f"Performance trend tracking failed: {str(e)}")
            return {"error": f"Performance trend tracking failed: {str(e)}"}

    def _generate_coaching_report(self, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive coaching report."""
        try:
            # Use reporting system to generate report
            report = self.reporting_system.generate_comprehensive_report(agents)

            return {"report": report, "status": "success"}

        except Exception as e:
            self.logger.error(f"Coaching report generation failed: {str(e)}")
            return {"error": f"Coaching report generation failed: {str(e)}"}

    def _optimize_task_assignment(self, task: Dict[str, Any], agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize task assignment to the best available agent."""
        try:
            # Use task matcher to find optimal assignment
            assignment = self.task_matcher.find_optimal_assignment(task, agents)

            return {"assignment": assignment, "status": "success"}

        except Exception as e:
            self.logger.error(f"Task assignment optimization failed: {str(e)}")
            return {"error": f"Task assignment optimization failed: {str(e)}"}

    def _form_project_team(self, project: Dict[str, Any], available_agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Form an optimal team for a project."""
        try:
            # Use team optimizer to form optimal team
            team = self.team_optimizer.optimize_team_formation(project, available_agents)

            return {"team": team, "status": "success"}

        except Exception as e:
            self.logger.error(f"Project team formation failed: {str(e)}")
            return {"error": f"Project team formation failed: {str(e)}"}

    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve coordination conflicts."""
        try:
            resolutions = []

            for conflict in conflicts:
                resolution = self.conflict_resolver.resolve_conflict(conflict)
                resolutions.append(resolution)

            return {"resolutions": resolutions, "status": "success"}

        except Exception as e:
            self.logger.error(f"Conflict resolution failed: {str(e)}")
            return {"error": f"Conflict resolution failed: {str(e)}"}

    def _optimize_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow based on analysis."""
        try:
            optimization = self.workflow_optimizer.optimize_workflow(workflow_data)

            return {"optimization": optimization, "status": "success"}

        except Exception as e:
            self.logger.error(f"Workflow optimization failed: {str(e)}")
            return {"error": f"Workflow optimization failed: {str(e)}"}

    def _strategic_planning(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic planning recommendations."""
        try:
            plan = self.strategic_planner.generate_strategic_plan(team_data)

            return {"plan": plan, "status": "success"}

        except Exception as e:
            self.logger.error(f"Strategic planning failed: {str(e)}")
            return {"error": f"Strategic planning failed: {str(e)}"}

    def _calculate_performance_score(self, session_data: Dict[str, Any]) -> float:
        """Calculate a performance score for a session."""
        try:
            score = 100.0

            # Deduct for errors
            errors = len(session_data.get("errors", []))
            score -= errors * 5

            # Deduct for test failures
            test_failures = session_data.get("test_failures", 0)
            score -= test_failures * 3

            # Bonus for PR creation
            if session_data.get("pr_created", False):
                score += 10

            # Normalize to 0-100 range
            score = max(0.0, min(100.0, score))

            return score

        except Exception as e:
            self.logger.error(f"Performance score calculation failed: {str(e)}")
            return 0.0

    async def execute_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version of execute method.

        Args:
            request: Action request with 'action' and relevant parameters

        Returns:
            Dictionary containing the action result
        """
        # For now, just wrap the sync version
        return self.execute(request)


# Example usage and test data
def example_usage():
    """Demonstrate Team Coach usage with example data."""
    # Initialize Team Coach
    coach = TeamCoach()

    # Example session data
    session_data = {
        "session_id": "example_session_001",
        "tasks": ["implement-auth", "add-tests", "update-docs"],
        "errors": [],
        "test_failures": 0,
        "pr_created": True,
        "duration_minutes": 120
    }

    # Analyze session
    result = coach.execute({
        "action": "analyze_session",
        "session_data": session_data
    })
    print("Session Analysis Result:", json.dumps(result, indent=2))

    # Identify improvements
    if result.get("status") == "success":
        improvements = coach.execute({
            "action": "identify_improvements",
            "metrics": result["metrics"]
        })
        print("Improvements Identified:", json.dumps(improvements, indent=2))

    # Track performance trends
    trends = coach.execute({
        "action": "track_performance_trends",
        "period_days": 30
    })
    print("Performance Trends:", json.dumps(trends, indent=2))


if __name__ == "__main__":
    example_usage()
