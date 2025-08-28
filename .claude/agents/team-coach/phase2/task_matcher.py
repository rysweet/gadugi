"""
TeamCoach Phase 2: Task-Agent Matching System

This module provides advanced task-agent matching capabilities with intelligent
reasoning and optimization. The TaskAgentMatcher class analyzes task requirements,
agent capabilities, and contextual factors to provide optimal agent recommendations.

Key Features:
- Multi-dimensional task-agent compatibility analysis
- Context-aware matching with workload consideration
- Performance prediction for assignments
- Explanation generation for recommendations
- Dynamic priority and constraint handling
- Collaborative assignment optimization
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import shared modules with absolute path resolution
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

# Import available shared module components
from ...shared.interfaces import OperationResult  # type: ignore
from ...shared.utils.error_handling import ErrorHandler, CircuitBreaker  # type: ignore
from ...shared.state_management import StateManager  # type: ignore

# Define missing classes locally
TaskResult = OperationResult

# Import task tracking if available
try:
    from ...shared.task_tracking import TaskMetrics  # type: ignore[import]
except ImportError:
    class TaskMetrics:
        def __init__(self, *args, **kwargs):
            pass


# Import Phase 1 components (will be available when all imports are fixed)
try:
    from ..phase1.capability_assessment import (
        CapabilityAssessment as Phase1CapabilityAssessment,  # type: ignore[assignment]
        AgentCapabilityProfile as Phase1AgentCapabilityProfile,  # type: ignore[assignment]
        CapabilityDomain as Phase1CapabilityDomain,  # type: ignore[assignment]
        ProficiencyLevel as Phase1ProficiencyLevel)  # type: ignore[assignment]
    from ..phase1.performance_analytics import AgentPerformanceAnalyzer  # type: ignore[attr-defined]
except ImportError:
    # Define minimal stubs if Phase 1 imports fail
    class Phase1CapabilityAssessment:
        pass
    class Phase1AgentCapabilityProfile:
        pass
    class Phase1CapabilityDomain:
        pass
    class Phase1ProficiencyLevel:
        pass
    class AgentPerformanceAnalyzer:
        pass

# Define local aliases to avoid import conflicts
CapabilityAssessment = Phase1CapabilityAssessment  # type: ignore[assignment]
AgentCapabilityProfile = Phase1AgentCapabilityProfile  # type: ignore[assignment]
CapabilityDomain = Phase1CapabilityDomain  # type: ignore[assignment]
ProficiencyLevel = Phase1ProficiencyLevel  # type: ignore[assignment]


class MatchingStrategy(Enum):
    """Strategies for task-agent matching"""

    BEST_FIT = "best_fit"  # Single best agent
    LOAD_BALANCED = "load_balanced"  # Consider current workload
    SKILL_DEVELOPMENT = "skill_development"  # Optimize for learning
    COLLABORATIVE = "collaborative"  # Multi-agent assignments
    RISK_MINIMIZED = "risk_minimized"  # Minimize failure risk


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class TaskUrgency(Enum):
    """Task urgency levels"""

    IMMEDIATE = 4
    URGENT = 3
    NORMAL = 2
    FLEXIBLE = 1


@dataclass
class TaskRequirements:
    """Comprehensive task requirements specification"""

    task_id: str
    task_type: str
    description: str

    # Capability requirements
    required_capabilities: Dict[CapabilityDomain, ProficiencyLevel]
    preferred_capabilities: Dict[CapabilityDomain, ProficiencyLevel] = field(
        default_factory=dict
    )

    # Constraints and preferences
    estimated_duration: Optional[timedelta] = None
    deadline: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    urgency: TaskUrgency = TaskUrgency.NORMAL

    # Collaboration requirements
    requires_collaboration: bool = False
    max_agents: int = 1
    interdependent_tasks: List[str] = field(default_factory=list)

    # Context and constraints
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class AgentAvailability:
    """Agent availability and workload information"""

    agent_id: str
    current_workload: float  # 0.0 to 1.0
    scheduled_tasks: List[str]
    available_from: datetime
    capacity_until: Optional[datetime] = None
    preferred_work_periods: List[Tuple[datetime, datetime]] = field(
        default_factory=list
    )
    blackout_periods: List[Tuple[datetime, datetime]] = field(default_factory=list)


@dataclass
class MatchingScore:
    """Detailed scoring for a task-agent match"""

    agent_id: str
    task_id: str

    # Core scores (0.0 to 1.0)
    capability_match: float
    availability_score: float
    performance_prediction: float
    workload_balance: float

    # Composite scores
    overall_score: float
    confidence_level: float

    # Explanatory factors
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    calculation_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class MatchingRecommendation:
    """Complete recommendation for task assignment"""

    task_id: str
    recommended_agents: List[str]
    assignment_strategy: MatchingStrategy

    # Scoring details
    agent_scores: Dict[str, MatchingScore]
    alternative_options: List[Tuple[str, float]] = field(default_factory=list)

    # Assignment details
    estimated_completion_time: Optional[datetime] = None
    success_probability: float = 0.0
    risk_factors: List[str] = field(default_factory=list)

    # Reasoning
    reasoning: str = ""
    assumptions: List[str] = field(default_factory=list)

    # Monitoring recommendations
    monitoring_points: List[str] = field(default_factory=list)
    fallback_options: List[str] = field(default_factory=list)


class TaskAgentMatcher:
    """
    Advanced task-agent matching system with intelligent reasoning.

    Provides comprehensive analysis of task-agent compatibility considering
    capabilities, performance history, current workload, and contextual factors.
    Generates detailed recommendations with explanations and alternatives.
    """

    def __init__(
        self,
        capability_assessment: Optional[CapabilityAssessment] = None,
        performance_analyzer: Optional[AgentPerformanceAnalyzer] = None,
        task_metrics: Optional[TaskMetrics] = None,
        state_manager: Optional[StateManager] = None,
        error_handler: Optional[ErrorHandler] = None):
        """
        Initialize the task-agent matcher.

        Args:
            capability_assessment: Capability assessment component
            performance_analyzer: Performance analysis component
            task_metrics: Task tracking integration
            state_manager: State management for persistent data
            error_handler: Error handling for robust operation
        """
        self.logger = logging.getLogger(__name__)
        self.capability_assessment = capability_assessment or CapabilityAssessment()
        self.performance_analyzer = performance_analyzer or AgentPerformanceAnalyzer()
        self.task_metrics = task_metrics or TaskMetrics()
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()

        # Circuit breaker for matching operations
        self.matching_circuit_breaker = CircuitBreaker(
            failure_threshold=3, timeout=300, name="task_agent_matching"
        )

        # Agent profiles cache
        self.agent_profiles_cache: Dict[str, AgentCapabilityProfile] = {}
        self.agent_availability_cache: Dict[str, AgentAvailability] = {}

        # Matching configuration
        self.matching_config = {
            "capability_weight": 0.4,
            "performance_weight": 0.3,
            "availability_weight": 0.2,
            "workload_weight": 0.1,
            "confidence_threshold": 0.7,
            "min_capability_match": 0.6,
            "workload_balance_factor": 0.8,
            "recency_weight": 0.2,  # Weight for recent performance
        }

        # Performance prediction models
        self.prediction_models = self._initialize_prediction_models()

        self.logger.info("TaskAgentMatcher initialized")

    @CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    def find_optimal_agent(
        self,
        task_requirements: TaskRequirements,
        available_agents: List[str],
        strategy: MatchingStrategy = MatchingStrategy.BEST_FIT) -> MatchingRecommendation:
        """
        Find the optimal agent(s) for a given task.

        Args:
            task_requirements: Detailed task requirements
            available_agents: List of available agent IDs
            strategy: Matching strategy to use

        Returns:
            MatchingRecommendation: Complete recommendation with reasoning

        Raises:
            MatchingError: If matching process fails
        """
        try:
            self.logger.info(
                f"Finding optimal agent for task {task_requirements.task_id}"
            )

            # Update agent profiles and availability
            self._update_agent_data(available_agents)

            # Score all available agents
            agent_scores = {}
            for agent_id in available_agents:
                score = self._calculate_agent_task_score(
                    agent_id, task_requirements, strategy
                )
                if score.overall_score >= self.matching_config["min_capability_match"]:
                    agent_scores[agent_id] = score

            if not agent_scores:
                raise MatchingError(
                    f"No suitable agents found for task {task_requirements.task_id}"
                )

            # Generate recommendation based on strategy
            recommendation = self._generate_recommendation(
                task_requirements, agent_scores, strategy
            )

            # Add reasoning and explanations
            self._enhance_recommendation_reasoning(
                recommendation, task_requirements, strategy
            )

            self.logger.info(
                f"Generated recommendation for task {task_requirements.task_id}"
            )
            return recommendation

        except Exception as e:
            self.logger.error(
                f"Failed to find optimal agent for task {task_requirements.task_id}: {e}"
            )
            raise MatchingError(
                f"Matching failed for task {task_requirements.task_id}: {e}"
            )

    def _calculate_agent_task_score(
        self,
        agent_id: str,
        task_requirements: TaskRequirements,
        strategy: MatchingStrategy) -> MatchingScore:
        """Calculate comprehensive matching score for an agent-task pair."""
        try:
            # Get agent data
            capability_profile = self._get_agent_capability_profile(agent_id)
            availability = self._get_agent_availability(agent_id)

            # Calculate component scores
            capability_match = self._calculate_capability_match(
                capability_profile, task_requirements
            )

            performance_prediction = self._predict_task_performance(
                agent_id, task_requirements
            )

            availability_score = self._calculate_availability_score(
                availability, task_requirements
            )

            workload_balance = self._calculate_workload_balance_score(
                availability, strategy
            )

            # Apply strategy-specific weights
            weights = self._get_strategy_weights(strategy)

            # Calculate overall score
            overall_score = (
                capability_match * weights["capability"]
                + performance_prediction * weights["performance"]
                + availability_score * weights["availability"]
                + workload_balance * weights["workload"]
            )

            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                capability_profile, agent_id, task_requirements
            )

            # Generate explanatory factors
            strengths, concerns, recommendations = self._analyze_match_factors(
                agent_id,
                capability_profile,
                task_requirements,
                capability_match,
                performance_prediction,
                availability_score)

            return MatchingScore(
                agent_id=agent_id,
                task_id=task_requirements.task_id,
                capability_match=capability_match,
                availability_score=availability_score,
                performance_prediction=performance_prediction,
                workload_balance=workload_balance,
                overall_score=overall_score,
                confidence_level=confidence_level,
                strengths=strengths,
                concerns=concerns,
                recommendations=recommendations,
                calculation_factors={
                    "capability_weight": weights["capability"],
                    "performance_weight": weights["performance"],
                    "availability_weight": weights["availability"],
                    "workload_weight": weights["workload"],
                })

        except Exception as e:
            self.logger.error(f"Failed to calculate agent task score: {e}")
            return MatchingScore(
                agent_id=agent_id,
                task_id=task_requirements.task_id,
                capability_match=0.0,
                availability_score=0.0,
                performance_prediction=0.0,
                workload_balance=0.0,
                overall_score=0.0,
                confidence_level=0.0,
                concerns=[f"Score calculation failed: {e}"])

    def _calculate_capability_match(
        self,
        capability_profile: AgentCapabilityProfile,
        task_requirements: TaskRequirements) -> float:
        """Calculate how well agent capabilities match task requirements."""
        try:
            if not capability_profile.capability_scores:  # type: ignore
                return 0.0

            total_weight = 0.0
            weighted_match = 0.0

            # Evaluate required capabilities
            for (
                domain,
                required_level) in task_requirements.required_capabilities.items():
                if domain in capability_profile.capability_scores:  # type: ignore
                    agent_capability = capability_profile.capability_scores[domain]  # type: ignore

                    # Calculate match score based on proficiency level
                    level_match = min(
                        1.0,
                        agent_capability.proficiency_level.value / required_level.value,  # type: ignore
                    )

                    # Weight by confidence score
                    confidence_weight = agent_capability.confidence_score

                    # Higher weight for required vs preferred capabilities
                    requirement_weight = 2.0

                    weighted_match += (
                        level_match * confidence_weight * requirement_weight
                    )
                    total_weight += requirement_weight
                else:
                    # Agent lacks required capability
                    total_weight += 2.0  # Still count the weight

            # Evaluate preferred capabilities (bonus points)
            for (
                domain,
                preferred_level) in task_requirements.preferred_capabilities.items():
                if domain in capability_profile.capability_scores:  # type: ignore
                    agent_capability = capability_profile.capability_scores[domain]  # type: ignore

                    level_match = min(
                        1.0,
                        agent_capability.proficiency_level.value
                        / preferred_level.value,  # type: ignore
                    )
                    confidence_weight = agent_capability.confidence_score
                    requirement_weight = 1.0  # Lower weight for preferred

                    weighted_match += (
                        level_match * confidence_weight * requirement_weight
                    )
                    total_weight += requirement_weight

            # Calculate final capability match score
            if total_weight > 0:
                capability_match = weighted_match / total_weight
            else:
                capability_match = 0.0

            return min(1.0, capability_match)

        except Exception as e:
            self.logger.error(f"Failed to calculate capability match: {e}")
            return 0.0

    def _predict_task_performance(
        self, agent_id: str, task_requirements: TaskRequirements
    ) -> float:
        """Predict agent performance for the specific task."""
        try:
            # Get historical performance data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)  # Last 30 days

            performance_data = self.performance_analyzer.analyze_agent_performance(  # type: ignore
                agent_id, (start_time, end_time)
            )

            # Base prediction on overall success rate
            base_prediction = performance_data.success_rate

            # Adjust based on task type similarity
            task_type_adjustment = self._calculate_task_type_similarity_adjustment(
                agent_id, task_requirements.task_type
            )

            # Adjust based on recent performance trend
            trend_adjustment = self._calculate_trend_adjustment(performance_data)

            # Adjust based on task complexity
            complexity_adjustment = self._calculate_complexity_adjustment(
                performance_data, task_requirements
            )

            # Combine adjustments
            performance_prediction = base_prediction * (
                1.0
                + (task_type_adjustment * 0.3)
                + (trend_adjustment * 0.2)
                + (complexity_adjustment * 0.1)
            )

            return min(1.0, max(0.0, performance_prediction))

        except Exception as e:
            self.logger.error(f"Failed to predict task performance: {e}")
            return 0.5  # Default moderate prediction

    def _calculate_availability_score(
        self, availability: AgentAvailability, task_requirements: TaskRequirements
    ) -> float:
        """Calculate availability score based on workload and constraints."""
        try:
            # Base score on current workload (inverse relationship)
            workload_score = 1.0 - availability.current_workload

            # Adjust for time constraints
            time_score = 1.0
            if task_requirements.deadline:
                time_to_deadline = (
                    task_requirements.deadline - availability.available_from
                )
                if time_to_deadline.total_seconds() > 0:
                    if task_requirements.estimated_duration:
                        urgency_ratio = (
                            task_requirements.estimated_duration / time_to_deadline
                        )
                        time_score = max(0.0, 1.0 - urgency_ratio)
                else:
                    time_score = 0.0  # Past deadline

            # Combine scores
            availability_score = (workload_score * 0.7) + (time_score * 0.3)

            return min(1.0, max(0.0, availability_score))

        except Exception as e:
            self.logger.error(f"Failed to calculate availability score: {e}")
            return 0.5

    def _calculate_workload_balance_score(
        self, availability: AgentAvailability, strategy: MatchingStrategy
    ) -> float:
        """Calculate workload balance score based on strategy."""
        try:
            if strategy == MatchingStrategy.LOAD_BALANCED:
                # Prefer agents with lower workload
                return 1.0 - availability.current_workload
            elif strategy == MatchingStrategy.BEST_FIT:
                # Workload is less important, focus on capability
                return 0.8  # Neutral score
            elif strategy == MatchingStrategy.SKILL_DEVELOPMENT:
                # Slightly prefer agents with some capacity for learning
                return 0.5 + (0.5 * (1.0 - availability.current_workload))
            else:
                return 1.0 - availability.current_workload

        except Exception as e:
            self.logger.error(f"Failed to calculate workload balance score: {e}")
            return 0.5

    def _calculate_task_type_similarity_adjustment(
        self, agent_id: str, task_type: str
    ) -> float:
        """Calculate adjustment based on agent's experience with similar tasks."""
        try:
            # Get recent task history
            end_time = datetime.now()
            start_time = end_time - timedelta(days=60)

            task_results = self.task_metrics.get_agent_task_results(  # type: ignore
                agent_id, start_time, end_time
            )

            if not task_results:
                return 0.0  # No adjustment if no history

            # Find tasks of similar type
            similar_tasks = [
                result
                for result in task_results
                if hasattr(result, "task_type")
                and self._calculate_task_type_similarity(result.task_type, task_type)
                > 0.7
            ]

            if not similar_tasks:
                return -0.1  # Small penalty for unfamiliar task type

            # Calculate success rate for similar tasks
            similar_success_rate = sum(
                1 for task in similar_tasks if task.success
            ) / len(similar_tasks)

            # Return adjustment factor (-0.3 to +0.3)
            return (similar_success_rate - 0.5) * 0.6

        except Exception as e:
            self.logger.error(
                f"Failed to calculate task type similarity adjustment: {e}"
            )
            return 0.0

    def _calculate_task_type_similarity(self, type1: str, type2: str) -> float:
        """Calculate similarity between two task types."""
        if type1.lower() == type2.lower():
            return 1.0

        # Simple similarity based on common words
        words1 = set(type1.lower().split("_"))
        words2 = set(type2.lower().split("_"))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_trend_adjustment(self, performance_data) -> float:
        """Calculate adjustment based on performance trend."""
        try:
            if (
                not performance_data.performance_trend
                or len(performance_data.performance_trend) < 2
            ):
                return 0.0

            # Calculate trend slope
            recent_trend = performance_data.performance_trend[-3:]  # Last 3 periods
            if len(recent_trend) < 2:
                return 0.0

            # Simple linear trend calculation
            trend_slope = (recent_trend[-1] - recent_trend[0]) / (len(recent_trend) - 1)

            # Return adjustment factor (-0.2 to +0.2)
            return max(-0.2, min(0.2, trend_slope * 2.0))

        except Exception as e:
            self.logger.error(f"Failed to calculate trend adjustment: {e}")
            return 0.0

    def _calculate_complexity_adjustment(
        self, performance_data, task_requirements: TaskRequirements
    ) -> float:
        """Calculate adjustment based on task complexity vs agent experience."""
        try:
            # Estimate task complexity based on requirements
            complexity_score = 0.0

            # Number of required capabilities
            complexity_score += len(task_requirements.required_capabilities) * 0.2

            # Urgency and priority
            complexity_score += task_requirements.urgency.value * 0.1
            complexity_score += task_requirements.priority.value * 0.1

            # Collaboration requirements
            if task_requirements.requires_collaboration:
                complexity_score += 0.3

            # Normalize complexity (0-1 scale)
            complexity_score = min(1.0, complexity_score)

            # Compare with agent's average execution time (proxy for handling complexity)
            if performance_data.avg_execution_time > 0:
                # Agents with faster avg execution might handle complexity better
                time_factor = max(
                    0.1, min(1.0, 300.0 / performance_data.avg_execution_time)
                )
                complexity_adjustment = (time_factor - complexity_score) * 0.1
            else:
                complexity_adjustment = -complexity_score * 0.1

            return max(-0.15, min(0.15, complexity_adjustment))

        except Exception as e:
            self.logger.error(f"Failed to calculate complexity adjustment: {e}")
            return 0.0

    def _calculate_confidence_level(
        self,
        capability_profile: AgentCapabilityProfile,
        agent_id: str,
        task_requirements: TaskRequirements) -> float:
        """Calculate confidence level for the matching recommendation."""
        try:
            confidence_factors = []

            # Capability confidence
            relevant_capabilities = list(
                task_requirements.required_capabilities.keys()
            ) + list(task_requirements.preferred_capabilities.keys())

            capability_confidences = []
            for domain in relevant_capabilities:
                if domain in capability_profile.capability_scores:  # type: ignore
                    capability_confidences.append(
                        capability_profile.capability_scores[domain].confidence_score  # type: ignore
                    )

            if capability_confidences:
                avg_capability_confidence = sum(capability_confidences) / len(
                    capability_confidences
                )
                confidence_factors.append(avg_capability_confidence)

            # Performance history confidence (based on data points)
            performance_data = self.performance_analyzer.analyze_agent_performance(  # type: ignore
                agent_id
            )
            if performance_data.total_tasks > 0:
                # More tasks = higher confidence, plateau at 20 tasks
                task_confidence = min(1.0, performance_data.total_tasks / 20.0)
                confidence_factors.append(task_confidence)

            # Task type familiarity confidence
            familiarity_confidence = self._calculate_task_familiarity_confidence(
                agent_id, task_requirements.task_type
            )
            confidence_factors.append(familiarity_confidence)

            # Overall confidence is the average of all factors
            if confidence_factors:
                overall_confidence = sum(confidence_factors) / len(confidence_factors)
            else:
                overall_confidence = 0.5  # Default moderate confidence

            return min(1.0, max(0.0, overall_confidence))

        except Exception as e:
            self.logger.error(f"Failed to calculate confidence level: {e}")
            return 0.5

    def _calculate_task_familiarity_confidence(
        self, agent_id: str, task_type: str
    ) -> float:
        """Calculate confidence based on agent's familiarity with task type."""
        try:
            # Get task history
            end_time = datetime.now()
            start_time = end_time - timedelta(days=90)

            task_results = self.task_metrics.get_agent_task_results(  # type: ignore
                agent_id, start_time, end_time
            )

            if not task_results:
                return 0.3  # Low confidence with no history

            # Count similar tasks
            similar_tasks = [
                result
                for result in task_results
                if hasattr(result, "task_type")
                and self._calculate_task_type_similarity(result.task_type, task_type)
                > 0.5
            ]

            # Confidence based on number of similar tasks
            familiarity_confidence = min(1.0, len(similar_tasks) / 10.0)

            return familiarity_confidence

        except Exception as e:
            self.logger.error(f"Failed to calculate task familiarity confidence: {e}")
            return 0.3

    def _analyze_match_factors(
        self,
        agent_id: str,
        capability_profile: AgentCapabilityProfile,
        task_requirements: TaskRequirements,
        capability_match: float,
        performance_prediction: float,
        availability_score: float) -> Tuple[List[str], List[str], List[str]]:
        """Analyze and generate explanatory factors for the match."""
        strengths = []
        concerns = []
        recommendations = []

        try:
            # Analyze capability strengths
            if capability_match >= 0.8:
                strengths.append("Excellent capability match for task requirements")
            elif capability_match >= 0.6:
                strengths.append("Good capability match with minor gaps")

            # Check for specific strength alignment
            for domain in capability_profile.primary_strengths:  # type: ignore
                if domain in task_requirements.required_capabilities:
                    strengths.append(f"Primary strength in {domain.value}")

            # Analyze performance strengths
            if performance_prediction >= 0.8:
                strengths.append("High predicted success rate based on history")
            elif performance_prediction >= 0.6:
                strengths.append("Moderate predicted success rate")

            # Analyze availability strengths
            if availability_score >= 0.8:
                strengths.append("Good availability with manageable workload")

            # Identify concerns
            if capability_match < 0.6:
                concerns.append("Below-threshold capability match")

                # Identify specific gaps
                for (
                    domain,
                    required_level) in task_requirements.required_capabilities.items():
                    if domain in capability_profile.capability_scores:  # type: ignore
                        agent_level = capability_profile.capability_scores[  # type: ignore
                            domain
                        ].proficiency_level
                        if agent_level.value < required_level.value:  # type: ignore
                            concerns.append(f"Insufficient {domain.value} capability")  # type: ignore
                    else:
                        concerns.append(f"Missing {domain.value} capability")  # type: ignore

            if performance_prediction < 0.5:
                concerns.append("Below-average predicted performance")

            if availability_score < 0.5:
                concerns.append("Limited availability due to high workload")

            # Generate recommendations
            if capability_match < 0.7:
                recommendations.append(
                    "Consider pairing with agent strong in missing capabilities"
                )

            if performance_prediction < 0.6:
                recommendations.append("Provide additional monitoring and support")

            if availability_score < 0.6:
                recommendations.append(
                    "Consider adjusting timeline or workload distribution"
                )

            # Check for improvement areas that align with task
            for domain in capability_profile.improvement_areas:  # type: ignore
                if domain in task_requirements.required_capabilities:
                    recommendations.append(
                        f"Good opportunity to develop {domain.value} skills"
                    )

        except Exception as e:
            self.logger.error(f"Failed to analyze match factors: {e}")
            concerns.append(f"Analysis failed: {e}")

        return strengths, concerns, recommendations

    def _get_strategy_weights(self, strategy: MatchingStrategy) -> Dict[str, float]:
        """Get scoring weights based on matching strategy."""
        base_weights = {
            "capability": self.matching_config["capability_weight"],
            "performance": self.matching_config["performance_weight"],
            "availability": self.matching_config["availability_weight"],
            "workload": self.matching_config["workload_weight"],
        }

        if strategy == MatchingStrategy.BEST_FIT:
            # Emphasize capability and performance
            return {
                "capability": 0.5,
                "performance": 0.3,
                "availability": 0.15,
                "workload": 0.05,
            }
        elif strategy == MatchingStrategy.LOAD_BALANCED:
            # Emphasize workload balance
            return {
                "capability": 0.3,
                "performance": 0.2,
                "availability": 0.2,
                "workload": 0.3,
            }
        elif strategy == MatchingStrategy.SKILL_DEVELOPMENT:
            # Balance capability with learning opportunities
            return {
                "capability": 0.35,
                "performance": 0.15,
                "availability": 0.25,
                "workload": 0.25,
            }
        elif strategy == MatchingStrategy.RISK_MINIMIZED:
            # Emphasize performance and availability
            return {
                "capability": 0.3,
                "performance": 0.4,
                "availability": 0.25,
                "workload": 0.05,
            }
        else:
            return base_weights

    def _generate_recommendation(
        self,
        task_requirements: TaskRequirements,
        agent_scores: Dict[str, MatchingScore],
        strategy: MatchingStrategy) -> MatchingRecommendation:
        """Generate comprehensive recommendation based on scores and strategy."""
        try:
            # Sort agents by overall score
            sorted_agents = sorted(
                agent_scores.items(), key=lambda x: x[1].overall_score, reverse=True
            )

            # Determine number of agents to recommend
            if task_requirements.requires_collaboration:
                max_agents = min(task_requirements.max_agents, len(sorted_agents))
                recommended_count = min(
                    3, max_agents
                )  # Recommend up to 3 for collaboration
            else:
                recommended_count = 1

            # Select recommended agents
            recommended_agents = [
                agent_id for agent_id, _ in sorted_agents[:recommended_count]
            ]

            # Calculate overall success probability
            if recommended_agents:
                top_scores = [
                    agent_scores[agent_id].overall_score
                    for agent_id in recommended_agents
                ]
                success_probability = sum(top_scores) / len(top_scores)
            else:
                success_probability = 0.0

            # Generate alternative options
            alternative_options = [
                (agent_id, score.overall_score)
                for agent_id, score in sorted_agents[
                    recommended_count : recommended_count + 3
                ]
            ]

            # Estimate completion time
            estimated_completion = self._estimate_completion_time(
                task_requirements, recommended_agents, agent_scores
            )

            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                task_requirements, recommended_agents, agent_scores
            )

            return MatchingRecommendation(
                task_id=task_requirements.task_id,
                recommended_agents=recommended_agents,
                assignment_strategy=strategy,
                agent_scores=agent_scores,
                alternative_options=alternative_options,
                estimated_completion_time=estimated_completion,
                success_probability=success_probability,
                risk_factors=risk_factors)

        except Exception as e:
            self.logger.error(f"Failed to generate recommendation: {e}")
            raise MatchingError(f"Recommendation generation failed: {e}")

    def _enhance_recommendation_reasoning(
        self,
        recommendation: MatchingRecommendation,
        task_requirements: TaskRequirements,
        strategy: MatchingStrategy) -> None:
        """Enhance recommendation with detailed reasoning."""
        try:
            reasoning_parts = []

            # Strategy explanation
            strategy_explanations = {
                MatchingStrategy.BEST_FIT: "Selected agent(s) with highest capability match and performance prediction",
                MatchingStrategy.LOAD_BALANCED: "Balanced recommendation considering current workload distribution",
                MatchingStrategy.SKILL_DEVELOPMENT: "Balanced capability with learning opportunities",
                MatchingStrategy.COLLABORATIVE: "Multi-agent assignment for collaborative task",
                MatchingStrategy.RISK_MINIMIZED: "Conservative selection minimizing failure risk",
            }

            reasoning_parts.append(
                strategy_explanations.get(
                    strategy, "Standard matching algorithm applied"
                )
            )

            # Top recommendation analysis
            if recommendation.recommended_agents:
                top_agent = recommendation.recommended_agents[0]
                top_score = recommendation.agent_scores[top_agent]

                reasoning_parts.append(
                    f"Primary recommendation ({top_agent}) scored {top_score.overall_score:.2f} "
                    f"with {top_score.confidence_level:.2f} confidence"
                )

                # Highlight key strengths
                if top_score.strengths:
                    reasoning_parts.append(
                        f"Key strengths: {', '.join(top_score.strengths[:2])}"
                    )

            # Risk assessment
            if recommendation.risk_factors:
                reasoning_parts.append(
                    f"Risk factors identified: {len(recommendation.risk_factors)}"
                )

            # Alternative options
            if recommendation.alternative_options:
                reasoning_parts.append(
                    f"{len(recommendation.alternative_options)} alternative options available"
                )

            recommendation.reasoning = ". ".join(reasoning_parts)

            # Add assumptions
            recommendation.assumptions = [
                "Agent availability data is current",
                "Capability assessments reflect current skills",
                "Task requirements are accurately specified",
                "Historical performance predicts future results",
            ]

            # Add monitoring points
            recommendation.monitoring_points = [
                "Monitor initial progress for any capability gaps",
                "Track adherence to estimated timeline",
                "Assess collaboration effectiveness if multi-agent",
                "Watch for workload balance issues",
            ]

            # Add fallback options
            if recommendation.alternative_options:
                fallback_agent = recommendation.alternative_options[0][0]
                recommendation.fallback_options = [
                    f"Reassign to {fallback_agent} if primary assignment fails",
                    "Consider collaborative approach if individual assignment struggles",
                    "Provide additional resources or training if needed",
                ]

        except Exception as e:
            self.logger.error(f"Failed to enhance recommendation reasoning: {e}")

    def _estimate_completion_time(
        self,
        task_requirements: TaskRequirements,
        recommended_agents: List[str],
        agent_scores: Dict[str, MatchingScore]) -> Optional[datetime]:
        """Estimate task completion time based on agents and requirements."""
        try:
            if not recommended_agents or not task_requirements.estimated_duration:
                return None

            # Get primary agent's average execution time
            primary_agent = recommended_agents[0]
            performance_data = self.performance_analyzer.analyze_agent_performance(  # type: ignore
                primary_agent
            )

            if performance_data.avg_execution_time > 0:
                # Adjust estimated duration based on agent performance
                agent_efficiency = min(
                    2.0, 300.0 / performance_data.avg_execution_time
                )  # Baseline 5 minutes
                adjusted_duration = (
                    task_requirements.estimated_duration / agent_efficiency
                )
            else:
                adjusted_duration = task_requirements.estimated_duration

            # Adjust for collaboration if multiple agents
            if len(recommended_agents) > 1:
                # Assume some efficiency gain from collaboration, but also coordination overhead
                collaboration_factor = 0.8 + (
                    0.1 * len(recommended_agents)
                )  # 80% base + 10% per additional agent
                adjusted_duration *= collaboration_factor

            # Get agent availability
            availability = self._get_agent_availability(primary_agent)
            completion_time = availability.available_from + adjusted_duration

            return completion_time

        except Exception as e:
            self.logger.error(f"Failed to estimate completion time: {e}")
            return None

    def _identify_risk_factors(
        self,
        task_requirements: TaskRequirements,
        recommended_agents: List[str],
        agent_scores: Dict[str, MatchingScore]) -> List[str]:
        """Identify potential risk factors for the assignment."""
        risk_factors = []

        try:
            for agent_id in recommended_agents:
                score = agent_scores[agent_id]

                # Capability risks
                if score.capability_match < 0.7:
                    risk_factors.append(
                        f"Below-optimal capability match for {agent_id}"
                    )

                # Performance risks
                if score.performance_prediction < 0.6:
                    risk_factors.append(
                        f"Uncertain performance prediction for {agent_id}"
                    )

                # Availability risks
                if score.availability_score < 0.6:
                    risk_factors.append(f"Limited availability for {agent_id}")

                # Confidence risks
                if score.confidence_level < 0.6:
                    risk_factors.append(f"Low confidence in assessment for {agent_id}")

            # Task-specific risks
            if task_requirements.deadline:
                time_to_deadline = task_requirements.deadline - datetime.now()
                if (
                    task_requirements.estimated_duration
                    and time_to_deadline < task_requirements.estimated_duration * 1.2
                ):
                    risk_factors.append("Tight deadline with limited buffer time")

            if (
                task_requirements.requires_collaboration
                and len(recommended_agents) == 1
            ):
                risk_factors.append(
                    "Collaboration required but single agent recommended"
                )

            if task_requirements.priority == TaskPriority.CRITICAL and not any(
                agent_scores[agent_id].overall_score > 0.8
                for agent_id in recommended_agents
            ):
                risk_factors.append("Critical task assigned to non-optimal agent")

        except Exception as e:
            self.logger.error(f"Failed to identify risk factors: {e}")
            risk_factors.append(f"Risk assessment failed: {e}")

        return risk_factors

    def _update_agent_data(self, agent_ids: List[str]) -> None:
        """Update agent profiles and availability data."""
        try:
            for agent_id in agent_ids:
                # Update capability profile if not cached or stale
                if agent_id not in self.agent_profiles_cache or (
                    datetime.now()
                    - self.agent_profiles_cache[agent_id].profile_generated  # type: ignore
                ) > timedelta(hours=24):
                    profile = self.capability_assessment.assess_agent_capabilities(  # type: ignore
                        agent_id
                    )
                    self.agent_profiles_cache[agent_id] = profile

                # Update availability data
                availability = self._fetch_agent_availability(agent_id)
                self.agent_availability_cache[agent_id] = availability

        except Exception as e:
            self.logger.error(f"Failed to update agent data: {e}")

    def _get_agent_capability_profile(self, agent_id: str) -> AgentCapabilityProfile:
        """Get agent capability profile from cache or assessment."""
        if agent_id in self.agent_profiles_cache:
            return self.agent_profiles_cache[agent_id]

        # Fallback: assess capabilities
        profile = self.capability_assessment.assess_agent_capabilities(agent_id)  # type: ignore
        self.agent_profiles_cache[agent_id] = profile
        return profile

    def _get_agent_availability(self, agent_id: str) -> AgentAvailability:
        """Get agent availability from cache or fetch."""
        if agent_id in self.agent_availability_cache:
            return self.agent_availability_cache[agent_id]

        # Fallback: fetch availability
        availability = self._fetch_agent_availability(agent_id)
        self.agent_availability_cache[agent_id] = availability
        return availability

    def _fetch_agent_availability(self, agent_id: str) -> AgentAvailability:
        """Fetch current agent availability and workload."""
        try:
            # This would integrate with actual scheduling/workload systems
            # For now, provide a basic implementation

            # Get current tasks from task metrics
            current_tasks = self.task_metrics.get_agent_active_tasks(agent_id)  # type: ignore
            scheduled_tasks = [
                task.task_id for task in current_tasks if hasattr(task, "task_id")
            ]

            # Calculate workload based on active tasks
            workload = min(
                1.0, len(current_tasks) / 5.0
            )  # Assume 5 tasks = 100% workload

            return AgentAvailability(
                agent_id=agent_id,
                current_workload=workload,
                scheduled_tasks=scheduled_tasks,
                available_from=datetime.now())

        except Exception as e:
            self.logger.error(f"Failed to fetch agent availability for {agent_id}: {e}")
            return AgentAvailability(
                agent_id=agent_id,
                current_workload=0.5,  # Default moderate workload
                scheduled_tasks=[],
                available_from=datetime.now())

    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Initialize performance prediction models."""
        # Placeholder for ML models
        # In a full implementation, this would load trained models
        return {
            "success_rate_model": None,
            "execution_time_model": None,
            "quality_model": None,
        }

    def batch_match_tasks(
        self,
        task_list: List[TaskRequirements],
        available_agents: List[str],
        strategy: MatchingStrategy = MatchingStrategy.BEST_FIT) -> Dict[str, MatchingRecommendation]:
        """
        Perform batch matching for multiple tasks.

        Args:
            task_list: List of tasks to match
            available_agents: Available agents for assignment
            strategy: Matching strategy to use

        Returns:
            Dict mapping task IDs to recommendations
        """
        try:
            recommendations = {}

            # Update agent data once for all tasks
            self._update_agent_data(available_agents)

            # Process each task
            for task_requirements in task_list:
                try:
                    recommendation = self.find_optimal_agent(
                        task_requirements, available_agents, strategy
                    )
                    recommendations[task_requirements.task_id] = recommendation

                    # Update agent availability for next task
                    self._simulate_assignment_impact(recommendation)

                except Exception as e:
                    self.logger.error(
                        f"Failed to match task {task_requirements.task_id}: {e}"
                    )
                    # Continue with other tasks

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to perform batch matching: {e}")
            return {}

    def _simulate_assignment_impact(
        self, recommendation: MatchingRecommendation
    ) -> None:
        """Simulate the impact of assignment on agent availability."""
        try:
            # Update workload for assigned agents
            for agent_id in recommendation.recommended_agents:
                if agent_id in self.agent_availability_cache:
                    availability = self.agent_availability_cache[agent_id]
                    # Increase workload (simplified simulation)
                    availability.current_workload = min(
                        1.0, availability.current_workload + 0.2
                    )

        except Exception as e:
            self.logger.error(f"Failed to simulate assignment impact: {e}")


class MatchingError(Exception):
    """Exception raised when task-agent matching fails."""

    pass
