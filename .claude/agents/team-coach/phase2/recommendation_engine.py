"""
TeamCoach Phase 2: Recommendation Engine

This module provides intelligent recommendations with detailed explanations
for task assignments, team formations, and optimization strategies.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ...shared.utils.error_handling import ErrorHandler
from .task_matcher import TaskAgentMatcher, MatchingRecommendation
from .team_optimizer import TeamCompositionOptimizer, OptimizationResult


class RecommendationType(Enum):
    """Types of recommendations"""

    TASK_ASSIGNMENT = "task_assignment"
    TEAM_FORMATION = "team_formation"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"


@dataclass
class Recommendation:
    """Intelligent recommendation with explanations"""

    recommendation_id: str
    recommendation_type: RecommendationType
    title: str
    description: str

    # Core recommendation
    primary_action: str
    alternative_actions: List[str] = field(default_factory=list)

    # Supporting evidence
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    confidence_level: float = 0.0

    # Implementation guidance
    implementation_steps: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)

    # Context
    generated_at: datetime = field(default_factory=datetime.now)
    applicable_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecommendationEngine:
    """
    Intelligent recommendation system with detailed explanations.

    Generates actionable recommendations for task assignments, team formations,
    and performance optimizations with comprehensive reasoning and implementation guidance.
    """

    def __init__(
        self,
        task_matcher: Optional[TaskAgentMatcher] = None,
        team_optimizer: Optional[TeamCompositionOptimizer] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """Initialize the recommendation engine."""
        self.logger = logging.getLogger(__name__)
        self.task_matcher = task_matcher or TaskAgentMatcher()
        self.team_optimizer = team_optimizer or TeamCompositionOptimizer()
        self.error_handler = error_handler or ErrorHandler()

        self.logger.info("RecommendationEngine initialized")

    def generate_task_assignment_recommendation(
        self, matching_result: MatchingRecommendation
    ) -> Recommendation:
        """Generate recommendation from task matching result."""
        try:
            primary_agent = (
                matching_result.recommended_agents[0]
                if matching_result.recommended_agents
                else "N/A"
            )

            recommendation = Recommendation(
                recommendation_id=f"task_assign_{matching_result.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                recommendation_type=RecommendationType.TASK_ASSIGNMENT,
                title=f"Task Assignment Recommendation for {matching_result.task_id}",
                description=f"Assign task to {primary_agent} based on capability analysis",
                primary_action=f"Assign task {matching_result.task_id} to agent {primary_agent}",
                reasoning=matching_result.reasoning,
                confidence_level=matching_result.success_probability,
                metadata={
                    "task_id": matching_result.task_id,
                    "strategy": matching_result.assignment_strategy.value,
                },
            )

            # Add alternative actions
            for alt_agent, score in matching_result.alternative_options:
                recommendation.alternative_actions.append(
                    f"Alternative: Assign to {alt_agent} (score: {score:.2f})"
                )

            # Add implementation steps
            recommendation.implementation_steps = [
                f"Notify {primary_agent} of task assignment",
                "Provide task requirements and context",
                "Set up monitoring and checkpoints",
                "Begin task execution",
            ]

            # Add expected outcomes
            recommendation.expected_outcomes = [
                f"Estimated success probability: {matching_result.success_probability:.1%}",
                f"Estimated completion: {matching_result.estimated_completion_time.isoformat() if matching_result.estimated_completion_time else 'TBD'}",
            ]

            return recommendation

        except Exception as e:
            self.logger.error(f"Failed to generate task assignment recommendation: {e}")
            raise

    def generate_team_formation_recommendation(
        self, optimization_result: OptimizationResult
    ) -> Recommendation:
        """Generate recommendation from team optimization result."""
        try:
            optimal_team = optimization_result.optimal_composition
            team_members = ", ".join(optimal_team.agents)

            recommendation = Recommendation(
                recommendation_id=f"team_form_{optimization_result.project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                recommendation_type=RecommendationType.TEAM_FORMATION,
                title=f"Team Formation Recommendation for {optimization_result.project_id}",
                description=f"Form team with {len(optimal_team.agents)} members for optimal project execution",
                primary_action=f"Form team with: {team_members}",
                reasoning=optimization_result.reasoning,
                confidence_level=optimization_result.confidence_level,
                metadata={
                    "project_id": optimization_result.project_id,
                    "team_size": len(optimal_team.agents),
                },
            )

            # Add alternatives
            for alt_comp in optimization_result.alternative_compositions:
                alt_members = ", ".join(alt_comp.agents)
                recommendation.alternative_actions.append(
                    f"Alternative: {alt_members} (score: {alt_comp.overall_score:.2f})"
                )

            # Add implementation steps
            recommendation.implementation_steps = [
                "Confirm agent availability for project timeline",
                "Conduct team formation meeting",
                "Establish communication protocols",
                "Define roles and responsibilities",
                "Begin project execution",
            ]

            # Add expected outcomes
            recommendation.expected_outcomes = [
                f"Predicted success rate: {optimal_team.predicted_success_rate:.1%}",
                f"Estimated completion: {optimal_team.predicted_completion_time}",
                f"Team collaboration score: {optimal_team.collaboration_score:.2f}",
            ]

            return recommendation

        except Exception as e:
            self.logger.error(f"Failed to generate team formation recommendation: {e}")
            raise


class RecommendationError(Exception):
    """Exception raised when recommendation generation fails."""

    pass
