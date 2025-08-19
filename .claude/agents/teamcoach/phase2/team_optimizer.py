from typing import Any, Dict, List, Optional, Tuple

from ..shared.state_management import StateManager
from ..shared.error_handling import ErrorHandler
import logging
import itertools

"""
TeamCoach Phase 2: Team Composition Optimizer

This module provides advanced team composition optimization for complex projects
and collaborative tasks. The TeamCompositionOptimizer analyzes project requirements
and generates optimal team formations with detailed reasoning.

Key Features:
- Multi-objective team optimization
- Skill complementarity analysis
- Workload distribution optimization
- Collaboration compatibility assessment
- Dynamic team scaling recommendations
- Performance prediction for team compositions
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

# Import shared modules and dependencies
from ...shared.utils.error_handling import ErrorHandler, CircuitBreaker
from ...shared.state_management import StateManager
from ..phase1.capability_assessment import (
    CapabilityAssessment,
    AgentCapabilityProfile,
    CapabilityDomain,
    ProficiencyLevel,
)
from ..phase1.performance_analytics import AgentPerformanceAnalyzer
from .task_matcher import TaskAgentMatcher, TaskRequirements

class OptimizationObjective(Enum):
    """Optimization objectives for team formation"""

    MAXIMIZE_CAPABILITY = "maximize_capability"
    MINIMIZE_RISK = "minimize_risk"
    BALANCE_WORKLOAD = "balance_workload"
    OPTIMIZE_COLLABORATION = "optimize_collaboration"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_LEARNING = "maximize_learning"

@dataclass
class ProjectRequirements:
    """Comprehensive project requirements for team optimization"""

    project_id: str
    project_name: str
    description: str

    # Capability requirements
    required_capabilities: Dict[CapabilityDomain, ProficiencyLevel]
    preferred_capabilities: Dict[CapabilityDomain, ProficiencyLevel] = field(
        default_factory=dict
    )

    # Project constraints
    timeline: Tuple[datetime, datetime]  # type: ignore
    max_team_size: int = 10
    min_team_size: int = 1
    budget_constraints: Optional[float] = None

    # Task breakdown
    task_list: List[TaskRequirements] = field(default_factory=list)
    critical_path_tasks: List[str] = field(default_factory=list)

    # Collaboration requirements
    requires_coordination: bool = False
    cross_functional_needs: List[CapabilityDomain] = field(default_factory=list)

    # Success criteria
    success_metrics: Dict[str, float] = field(default_factory=dict)
    quality_requirements: Dict[str, float] = field(default_factory=dict)

@dataclass
class TeamComposition:
    """Represents a potential team composition"""

    composition_id: str
    project_id: str
    agents: List[str]

    # Capability coverage
    capability_coverage: Dict[CapabilityDomain, float]
    capability_gaps: List[CapabilityDomain] = field(default_factory=list)
    capability_redundancy: Dict[CapabilityDomain, int] = field(default_factory=dict)

    # Performance predictions
    predicted_success_rate: float = 0.0
    predicted_completion_time: Optional[timedelta] = None
    risk_score: float = 0.0

    # Team dynamics
    collaboration_score: float = 0.0
    workload_balance_score: float = 0.0
    communication_complexity: float = 0.0

    # Optimization scores
    objective_scores: Dict[OptimizationObjective, float] = field(default_factory=dict)
    overall_score: float = 0.0

    # Analysis details
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class OptimizationResult:
    """Result of team optimization process"""

    project_id: str
    optimization_objectives: List[OptimizationObjective]

    # Recommended compositions
    optimal_composition: TeamComposition
    alternative_compositions: List[TeamComposition] = field(default_factory=list)

    # Analysis summary
    total_compositions_evaluated: int = 0
    optimization_time: float = 0.0
    confidence_level: float = 0.0

    # Detailed reasoning
    reasoning: str = ""
    trade_offs: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    # Monitoring recommendations
    success_indicators: List[str] = field(default_factory=list)
    risk_mitigation: List[str] = field(default_factory=list)

class TeamCompositionOptimizer:
    """
    Advanced team composition optimization system.

    Analyzes project requirements and generates optimal team formations
    considering multiple objectives and constraints. Provides detailed
    analysis and recommendations for team performance optimization.
    """

    def __init__(
        self,
        capability_assessment: Optional[CapabilityAssessment] = None,
        performance_analyzer: Optional[AgentPerformanceAnalyzer] = None,
        task_matcher: Optional[TaskAgentMatcher] = None,
        state_manager: Optional[StateManager] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """
        Initialize the team composition optimizer.

        Args:
            capability_assessment: Capability assessment component
            performance_analyzer: Performance analysis component
            task_matcher: Task matching component
            state_manager: State management for persistent data
            error_handler: Error handling for robust operation
        """
        self.logger = logging.getLogger(__name__)
        self.capability_assessment = capability_assessment or CapabilityAssessment()
        self.performance_analyzer = performance_analyzer or AgentPerformanceAnalyzer()
        self.task_matcher = task_matcher or TaskAgentMatcher()
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()

        # Circuit breaker for optimization operations
        self.optimization_circuit_breaker = CircuitBreaker(
            failure_threshold=3, timeout=600, name="team_optimization"
        )

        # Optimization configuration
        self.optimization_config = {
            "max_combinations_to_evaluate": 10000,
            "capability_coverage_threshold": 0.8,
            "collaboration_weight": 0.25,
            "performance_weight": 0.3,
            "workload_weight": 0.2,
            "risk_weight": 0.25,
            "min_confidence_threshold": 0.6,
        }

        # Agent profiles cache
        self.agent_profiles_cache: Dict[str, AgentCapabilityProfile] = {}

        self.logger.info("TeamCompositionOptimizer initialized")

    @ErrorHandler.with_circuit_breaker
    def optimize_team_for_project(
        self,
        project_requirements: ProjectRequirements,
        available_agents: List[str],
        objectives: List[OptimizationObjective] = None,
    ) -> OptimizationResult:
        """
        Optimize team composition for a specific project.

        Args:
            project_requirements: Detailed project requirements
            available_agents: List of available agent IDs
            objectives: Optimization objectives (default: maximize capability)

        Returns:
            OptimizationResult: Complete optimization result with recommendations

        Raises:
            OptimizationError: If optimization process fails
        """
        try:
            start_time = datetime.now()
            objectives = objectives or [OptimizationObjective.MAXIMIZE_CAPABILITY]

            self.logger.info(
                f"Optimizing team composition for project {project_requirements.project_id}"
            )

            # Update agent profiles
            self._update_agent_profiles(available_agents)

            # Generate candidate compositions
            candidate_compositions = self._generate_candidate_compositions(
                project_requirements, available_agents
            )

            if not candidate_compositions:
                raise OptimizationError("No valid team compositions found")

            # Evaluate each composition
            evaluated_compositions = []
            for composition in candidate_compositions:
                self._evaluate_team_composition(
                    composition, project_requirements, objectives
                )
                evaluated_compositions.append(composition)

            # Select optimal and alternative compositions
            optimal_composition = max(
                evaluated_compositions, key=lambda c: c.overall_score
            )

            # Get top alternatives (exclude optimal)
            alternatives = sorted(
                [
                    c
                    for c in evaluated_compositions
                    if c.composition_id != optimal_composition.composition_id
                ],
                key=lambda c: c.overall_score,
                reverse=True,
            )[:3]

            # Calculate optimization metrics
            optimization_time = (datetime.now() - start_time).total_seconds()
            confidence_level = self._calculate_optimization_confidence(
                optimal_composition, project_requirements
            )

            # Generate result
            result = OptimizationResult(
                project_id=project_requirements.project_id,
                optimization_objectives=objectives,
                optimal_composition=optimal_composition,
                alternative_compositions=alternatives,
                total_compositions_evaluated=len(evaluated_compositions),
                optimization_time=optimization_time,
                confidence_level=confidence_level,
            )

            # Enhance with detailed analysis
            self._enhance_optimization_result(result, project_requirements, objectives)

            self.logger.info(f"Team optimization completed in {optimization_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(
                f"Failed to optimize team for project {project_requirements.project_id}: {e}"
            )
            raise OptimizationError(f"Team optimization failed: {e}")

    def _generate_candidate_compositions(
        self, project_requirements: ProjectRequirements, available_agents: List[str]
    ) -> List[TeamComposition]:
        """Generate candidate team compositions to evaluate."""
        try:
            compositions = []

            # Determine feasible team sizes
            min_size = max(1, project_requirements.min_team_size)
            max_size = min(len(available_agents), project_requirements.max_team_size)

            # Limit combinations for performance
            max_combinations = self.optimization_config["max_combinations_to_evaluate"]
            combinations_generated = 0

            # Generate compositions of different sizes
            for team_size in range(min_size, max_size + 1):
                if combinations_generated >= max_combinations:
                    break

                # Generate all combinations of this size
                for agent_combination in itertools.combinations(
                    available_agents, team_size
                ):
                    if combinations_generated >= max_combinations:
                        break

                    # Quick feasibility check
                    if self._is_feasible_composition(
                        list(agent_combination), project_requirements
                    ):
                        composition_id = f"{project_requirements.project_id}_comp_{combinations_generated}"

                        composition = TeamComposition(  # type: ignore
                            composition_id=composition_id,
                            project_id=project_requirements.project_id,
                            agents=list(agent_combination),
                        )

                        compositions.append(composition)
                        combinations_generated += 1

            self.logger.info(f"Generated {len(compositions)} candidate compositions")
            return compositions

        except Exception as e:
            self.logger.error(f"Failed to generate candidate compositions: {e}")
            return []

    def _is_feasible_composition(
        self, agents: List[str], project_requirements: ProjectRequirements
    ) -> bool:
        """Quick feasibility check for a team composition."""
        try:
            # Check minimum capability coverage
            covered_capabilities = set()

            for agent_id in agents:
                if agent_id in self.agent_profiles_cache:
                    profile = self.agent_profiles_cache[agent_id]
                    for domain in profile.primary_strengths:
                        covered_capabilities.add(domain)

            # Check if critical capabilities are covered
            required_capabilities = set(
                project_requirements.required_capabilities.keys()
            )
            coverage_ratio = len(
                covered_capabilities.intersection(required_capabilities)
            ) / len(required_capabilities)

            return coverage_ratio >= 0.5  # At least 50% coverage for feasibility

        except Exception as e:
            self.logger.error(f"Failed to check composition feasibility: {e}")
            return True  # Default to feasible if check fails

    def _evaluate_team_composition(
        self,
        composition: TeamComposition,
        project_requirements: ProjectRequirements,
        objectives: List[OptimizationObjective],
    ) -> None:
        """Comprehensive evaluation of a team composition."""
        try:
            # Calculate capability coverage
            self._calculate_capability_coverage(composition, project_requirements)

            # Predict performance metrics
            self._predict_composition_performance(composition, project_requirements)

            # Assess team dynamics
            self._assess_team_dynamics(composition)

            # Calculate objective-specific scores
            for objective in objectives:
                score = self._calculate_objective_score(
                    composition, objective, project_requirements
                )
                composition.objective_scores[objective] = score

            # Calculate overall composite score
            composition.overall_score = self._calculate_overall_score(
                composition, objectives
            )

            # Generate strengths, weaknesses, and recommendations
            self._analyze_composition_factors(composition, project_requirements)

        except Exception as e:
            self.logger.error(
                f"Failed to evaluate team composition {composition.composition_id}: {e}"
            )
            composition.overall_score = 0.0

    def _calculate_capability_coverage(
        self, composition: TeamComposition, project_requirements: ProjectRequirements
    ) -> None:
        """Calculate capability coverage for the team composition."""
        try:
            capability_coverage = {}
            capability_redundancy = {}

            # Analyze each required capability
            for (
                domain,
                required_level,
            ) in project_requirements.required_capabilities.items():
                agent_capabilities = []

                for agent_id in composition.agents:
                    if agent_id in self.agent_profiles_cache:
                        profile = self.agent_profiles_cache[agent_id]
                        if domain in profile.capability_scores:
                            capability_score = profile.capability_scores[domain]
                            agent_capabilities.append(
                                capability_score.proficiency_level.value
                            )

                if agent_capabilities:
                    # Coverage is the highest capability level available
                    max_capability = max(agent_capabilities)
                    coverage = min(1.0, max_capability / required_level.value)
                    capability_coverage[domain] = coverage

                    # Redundancy is the number of agents with this capability
                    capable_agents = sum(
                        1
                        for level in agent_capabilities
                        if level >= required_level.value * 0.8
                    )
                    capability_redundancy[domain] = capable_agents
                else:
                    capability_coverage[domain] = 0.0
                    capability_redundancy[domain] = 0

            # Identify gaps
            capability_gaps = [
                domain
                for domain, coverage in capability_coverage.items()
                if coverage < self.optimization_config["capability_coverage_threshold"]
            ]

            composition.capability_coverage = capability_coverage
            composition.capability_gaps = capability_gaps
            composition.capability_redundancy = capability_redundancy

        except Exception as e:
            self.logger.error(f"Failed to calculate capability coverage: {e}")

    def _predict_composition_performance(
        self, composition: TeamComposition, project_requirements: ProjectRequirements
    ) -> None:
        """Predict performance metrics for the team composition."""
        try:
            # Predict success rate based on individual agent performance
            individual_success_rates = []
            individual_completion_times = []

            for agent_id in composition.agents:
                performance_data = self.performance_analyzer.analyze_agent_performance(
                    agent_id
                )
                individual_success_rates.append(performance_data.success_rate)
                individual_completion_times.append(performance_data.avg_execution_time)

            if individual_success_rates:
                # Team success rate is not just average - consider collaboration effects
                avg_success_rate = sum(individual_success_rates) / len(
                    individual_success_rates
                )
                team_size_factor = 1.0 - (
                    0.05 * (len(composition.agents) - 1)
                )  # Small penalty for coordination
                composition.predicted_success_rate = max(
                    0.0, avg_success_rate * team_size_factor
                )

            # Predict completion time
            if individual_completion_times and project_requirements.task_list:
                avg_completion_time = sum(individual_completion_times) / len(
                    individual_completion_times
                )
                # Assume some parallelization benefit but coordination overhead
                parallelization_factor = 0.7 + (0.3 / len(composition.agents))
                estimated_total_time = (
                    len(project_requirements.task_list)
                    * avg_completion_time
                    * parallelization_factor
                )
                composition.predicted_completion_time = timedelta(
                    seconds=estimated_total_time
                )

            # Calculate risk score
            composition.risk_score = self._calculate_team_risk_score(
                composition, project_requirements
            )

        except Exception as e:
            self.logger.error(f"Failed to predict composition performance: {e}")

    def _assess_team_dynamics(self, composition: TeamComposition) -> None:
        """Assess team dynamics and collaboration potential."""
        try:
            # Collaboration score based on complementary skills
            collaboration_score = self._calculate_collaboration_score(composition)
            composition.collaboration_score = collaboration_score

            # Workload balance score
            workload_balance = self._calculate_workload_balance(composition)
            composition.workload_balance_score = workload_balance

            # Communication complexity (increases with team size)
            team_size = len(composition.agents)
            # Communication paths = n(n-1)/2
            communication_paths = team_size * (team_size - 1) / 2
            max_comfortable_paths = 10  # Assume 10 is manageable
            composition.communication_complexity = min(
                1.0, communication_paths / max_comfortable_paths
            )

        except Exception as e:
            self.logger.error(f"Failed to assess team dynamics: {e}")

    def _calculate_collaboration_score(self, composition: TeamComposition) -> float:
        """Calculate how well the team agents collaborate together."""
        try:
            if len(composition.agents) == 1:
                return 1.0  # No collaboration needed for single agent

            collaboration_factors = []

            # Skill complementarity
            skill_coverage = set()
            for agent_id in composition.agents:
                if agent_id in self.agent_profiles_cache:
                    profile = self.agent_profiles_cache[agent_id]
                    skill_coverage.update(profile.primary_strengths)
                    skill_coverage.update(profile.secondary_strengths)

            # More diverse skills = better collaboration potential
            skill_diversity = len(skill_coverage) / len(CapabilityDomain)
            collaboration_factors.append(skill_diversity)

            # Collaboration preferences
            collaborative_agents = 0
            for agent_id in composition.agents:
                if agent_id in self.agent_profiles_cache:
                    profile = self.agent_profiles_cache[agent_id]
                    if profile.collaboration_preferences:
                        collaborative_agents += 1

            collaboration_preference = collaborative_agents / len(composition.agents)
            collaboration_factors.append(collaboration_preference)

            # Team size factor (not too small, not too large)
            optimal_size = 4
            size_factor = (
                1.0 - abs(len(composition.agents) - optimal_size) / optimal_size
            )
            collaboration_factors.append(max(0.0, size_factor))

            return sum(collaboration_factors) / len(collaboration_factors)

        except Exception as e:
            self.logger.error(f"Failed to calculate collaboration score: {e}")
            return 0.5

    def _calculate_workload_balance(self, composition: TeamComposition) -> float:
        """Calculate workload balance across team members."""
        try:
            # This would integrate with actual workload data
            # For now, assume balanced workload for teams and check individual capacities

            workload_scores = []
            for agent_id in composition.agents:
                # Get agent availability (this would be from actual scheduling system)
                # For now, use a simplified calculation
                availability = self.task_matcher._get_agent_availability(agent_id)
                workload_score = 1.0 - availability.current_workload
                workload_scores.append(workload_score)

            if not workload_scores:
                return 0.0

            # Balance is better when workloads are similar
            avg_workload = sum(workload_scores) / len(workload_scores)
            workload_variance = sum(
                (score - avg_workload) ** 2 for score in workload_scores
            ) / len(workload_scores)

            # Convert variance to balance score (lower variance = better balance)
            balance_score = max(0.0, 1.0 - workload_variance * 4)  # Scale variance

            return balance_score

        except Exception as e:
            self.logger.error(f"Failed to calculate workload balance: {e}")
            return 0.5

    def _calculate_team_risk_score(
        self, composition: TeamComposition, project_requirements: ProjectRequirements
    ) -> float:
        """Calculate overall risk score for the team composition."""
        try:
            risk_factors = []

            # Capability gap risk
            capability_gap_risk = len(composition.capability_gaps) / len(
                project_requirements.required_capabilities
            )
            risk_factors.append(capability_gap_risk)

            # Single point of failure risk
            spof_risk = 0.0
            for domain in project_requirements.required_capabilities:
                if composition.capability_redundancy.get(domain, 0) <= 1:
                    spof_risk += 1.0
            spof_risk /= len(project_requirements.required_capabilities)
            risk_factors.append(spof_risk)

            # Team size risk (too small or too large)
            optimal_size_range = (2, 6)
            team_size = len(composition.agents)
            if team_size < optimal_size_range[0]:
                size_risk = (optimal_size_range[0] - team_size) / optimal_size_range[0]
            elif team_size > optimal_size_range[1]:
                size_risk = (team_size - optimal_size_range[1]) / team_size
            else:
                size_risk = 0.0
            risk_factors.append(size_risk)

            # Communication complexity risk
            risk_factors.append(composition.communication_complexity)

            return sum(risk_factors) / len(risk_factors)

        except Exception as e:
            self.logger.error(f"Failed to calculate team risk score: {e}")
            return 0.5

    def _calculate_objective_score(
        self,
        composition: TeamComposition,
        objective: OptimizationObjective,
        project_requirements: ProjectRequirements,
    ) -> float:
        """Calculate score for a specific optimization objective."""
        try:
            if objective == OptimizationObjective.MAXIMIZE_CAPABILITY:
                # Score based on capability coverage
                if composition.capability_coverage:
                    return sum(composition.capability_coverage.values()) / len(
                        composition.capability_coverage
                    )
                return 0.0

            elif objective == OptimizationObjective.MINIMIZE_RISK:
                # Inverse of risk score
                return 1.0 - composition.risk_score

            elif objective == OptimizationObjective.BALANCE_WORKLOAD:
                return composition.workload_balance_score

            elif objective == OptimizationObjective.OPTIMIZE_COLLABORATION:
                return composition.collaboration_score

            elif objective == OptimizationObjective.MAXIMIZE_LEARNING:
                # Score based on skill development opportunities
                learning_score = 0.0
                for agent_id in composition.agents:
                    if agent_id in self.agent_profiles_cache:
                        profile = self.agent_profiles_cache[agent_id]
                        # Agents with improvement areas that align with project needs
                        aligned_improvements = len(
                            set(profile.improvement_areas).intersection(
                                set(project_requirements.required_capabilities.keys())
                            )
                        )
                        learning_score += aligned_improvements

                max_possible_learning = len(composition.agents) * len(
                    project_requirements.required_capabilities
                )
                return (
                    learning_score / max_possible_learning
                    if max_possible_learning > 0
                    else 0.0
                )

            elif objective == OptimizationObjective.MINIMIZE_COST:
                # Simplified cost model - smaller teams cost less
                max_team_size = project_requirements.max_team_size
                return 1.0 - (len(composition.agents) / max_team_size)

            else:
                return 0.5  # Default neutral score

        except Exception as e:
            self.logger.error(
                f"Failed to calculate objective score for {objective}: {e}"
            )
            return 0.0

    def _calculate_overall_score(
        self, composition: TeamComposition, objectives: List[OptimizationObjective]
    ) -> float:
        """Calculate overall composite score for the composition."""
        try:
            if not objectives or not composition.objective_scores:
                return 0.0

            # Equal weight for all objectives (could be made configurable)
            objective_weight = 1.0 / len(objectives)

            total_score = 0.0
            for objective in objectives:
                if objective in composition.objective_scores:
                    total_score += (
                        composition.objective_scores[objective] * objective_weight
                    )

            return total_score

        except Exception as e:
            self.logger.error(f"Failed to calculate overall score: {e}")
            return 0.0

    def _analyze_composition_factors(
        self, composition: TeamComposition, project_requirements: ProjectRequirements
    ) -> None:
        """Analyze strengths, weaknesses, and generate recommendations."""
        try:
            strengths = []
            weaknesses = []
            recommendations = []

            # Analyze capability coverage
            strong_capabilities = [
                domain.value
                for domain, coverage in composition.capability_coverage.items()
                if coverage >= 0.9
            ]
            if strong_capabilities:
                strengths.append(
                    f"Strong coverage in: {', '.join(strong_capabilities[:3])}"
                )

            if composition.capability_gaps:
                gap_names = [domain.value for domain in composition.capability_gaps]
                weaknesses.append(f"Capability gaps in: {', '.join(gap_names[:3])}")
                recommendations.append(
                    "Consider adding agents with missing capabilities"
                )

            # Analyze team dynamics
            if composition.collaboration_score >= 0.8:
                strengths.append("Excellent collaboration potential")
            elif composition.collaboration_score < 0.5:
                weaknesses.append("Limited collaboration synergy")
                recommendations.append(
                    "Focus on team building and communication protocols"
                )

            # Analyze performance prediction
            if composition.predicted_success_rate >= 0.8:
                strengths.append("High predicted success rate")
            elif composition.predicted_success_rate < 0.6:
                weaknesses.append("Below-average predicted success rate")
                recommendations.append("Provide additional support and monitoring")

            # Analyze risk factors
            if composition.risk_score < 0.3:
                strengths.append("Low risk profile")
            elif composition.risk_score > 0.7:
                weaknesses.append("High risk factors identified")
                recommendations.append("Implement risk mitigation strategies")

            # Team size analysis
            team_size = len(composition.agents)
            if team_size == 1:
                if project_requirements.requires_coordination:
                    weaknesses.append("Single agent for collaborative project")
                    recommendations.append(
                        "Consider expanding team for better coverage"
                    )
                else:
                    strengths.append("Efficient single-agent solution")
            elif team_size > 6:
                weaknesses.append("Large team may have coordination challenges")
                recommendations.append(
                    "Establish clear communication and coordination protocols"
                )

            composition.strengths = strengths
            composition.weaknesses = weaknesses
            composition.recommendations = recommendations

        except Exception as e:
            self.logger.error(f"Failed to analyze composition factors: {e}")

    def _calculate_optimization_confidence(
        self,
        optimal_composition: TeamComposition,
        project_requirements: ProjectRequirements,
    ) -> float:
        """Calculate confidence level for the optimization result."""
        try:
            confidence_factors = []

            # Capability coverage confidence
            if optimal_composition.capability_coverage:
                avg_coverage = sum(
                    optimal_composition.capability_coverage.values()
                ) / len(optimal_composition.capability_coverage)
                confidence_factors.append(avg_coverage)

            # Performance prediction confidence
            confidence_factors.append(optimal_composition.predicted_success_rate)

            # Risk confidence (inverse of risk)
            confidence_factors.append(1.0 - optimal_composition.risk_score)

            # Team size confidence
            optimal_size_range = (2, 6)
            team_size = len(optimal_composition.agents)
            if optimal_size_range[0] <= team_size <= optimal_size_range[1]:
                size_confidence = 1.0
            else:
                size_confidence = 0.7
            confidence_factors.append(size_confidence)

            return sum(confidence_factors) / len(confidence_factors)

        except Exception as e:
            self.logger.error(f"Failed to calculate optimization confidence: {e}")
            return 0.5

    def _enhance_optimization_result(
        self,
        result: OptimizationResult,
        project_requirements: ProjectRequirements,
        objectives: List[OptimizationObjective],
    ) -> None:
        """Enhance optimization result with detailed analysis."""
        try:
            # Generate reasoning
            reasoning_parts = []

            objective_names = [
                obj.value.replace("_", " ").title() for obj in objectives
            ]
            reasoning_parts.append(
                f"Optimization focused on: {', '.join(objective_names)}"
            )

            optimal = result.optimal_composition
            reasoning_parts.append(
                f"Selected {len(optimal.agents)}-agent team with {optimal.overall_score:.2f} overall score"
            )

            if optimal.strengths:
                reasoning_parts.append(f"Key strengths: {optimal.strengths[0]}")

            result.reasoning = ". ".join(reasoning_parts)

            # Identify trade-offs
            trade_offs = []
            if len(optimal.agents) > 4:
                trade_offs.append(
                    "Larger team provides better coverage but increases coordination complexity"
                )
            if optimal.capability_gaps:
                trade_offs.append(
                    "Some capability gaps accepted to optimize other objectives"
                )
            if optimal.risk_score > 0.5:
                trade_offs.append(
                    "Higher risk accepted for better performance/capability match"
                )

            result.trade_offs = trade_offs

            # Add assumptions
            result.assumptions = [
                "Agent capability assessments are current and accurate",
                "Project requirements are stable and complete",
                "Team members will be available for project duration",
                "Collaboration effectiveness matches predictions",
            ]

            # Success indicators
            result.success_indicators = [
                "Team meets capability coverage requirements",
                "Performance metrics track to predictions",
                "Collaboration proceeds smoothly",
                "Timeline adherence within acceptable variance",
            ]

            # Risk mitigation
            risk_mitigation = []
            if optimal.capability_gaps:
                risk_mitigation.append(
                    "Monitor capability gaps and provide training/support"
                )
            if optimal.risk_score > 0.6:
                risk_mitigation.append("Implement enhanced monitoring and checkpoints")
            if len(optimal.agents) > 5:
                risk_mitigation.append(
                    "Establish clear communication protocols and coordination structure"
                )

            result.risk_mitigation = risk_mitigation

        except Exception as e:
            self.logger.error(f"Failed to enhance optimization result: {e}")

    def _update_agent_profiles(self, agent_ids: List[str]) -> None:
        """Update agent capability profiles."""
        try:
            for agent_id in agent_ids:
                if agent_id not in self.agent_profiles_cache:
                    profile = self.capability_assessment.assess_agent_capabilities(
                        agent_id
                    )
                    self.agent_profiles_cache[agent_id] = profile

        except Exception as e:
            self.logger.error(f"Failed to update agent profiles: {e}")

    def compare_team_compositions(
        self, compositions: List[TeamComposition], criteria: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple team compositions across specified criteria.

        Args:
            compositions: List of team compositions to compare
            criteria: Comparison criteria (default: standard metrics)

        Returns:
            Dict containing detailed comparison analysis
        """
        try:
            if not compositions:
                return {}

            criteria = criteria or [
                "overall_score",
                "predicted_success_rate",
                "collaboration_score",
                "risk_score",
                "team_size",
            ]

            comparison = {
                "compositions": len(compositions),
                "criteria_analysis": {},
                "rankings": {},
                "summary": {},
            }

            # Analyze each criterion
            for criterion in criteria:
                values = []
                for comp in compositions:
                    if criterion == "team_size":
                        values.append(len(comp.agents))
                    else:
                        values.append(getattr(comp, criterion, 0.0))

                comparison["criteria_analysis"][criterion] = {
                    "values": values,
                    "best": max(values) if criterion != "risk_score" else min(values),
                    "worst": min(values) if criterion != "risk_score" else max(values),
                    "average": sum(values) / len(values),
                    "range": max(values) - min(values),
                }

            # Generate rankings
            for criterion in criteria:
                if criterion == "risk_score":
                    # Lower is better for risk
                    ranked = sorted(
                        compositions, key=lambda c: getattr(c, criterion, 1.0)
                    )
                else:
                    # Higher is better for other criteria
                    ranked = sorted(
                        compositions,
                        key=lambda c: getattr(c, criterion, 0.0),
                        reverse=True,
                    )

                comparison["rankings"][criterion] = [
                    comp.composition_id for comp in ranked
                ]

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to compare team compositions: {e}")
            return {}

class OptimizationError(Exception):
    """Exception raised when team optimization fails."""

    pass
