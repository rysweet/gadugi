"""
TeamCoach Phase 1: Agent Capability Assessment

This module provides comprehensive agent capability evaluation and profiling.
The CapabilityAssessment class analyzes agent strengths, weaknesses, specializations,
and compatibility patterns to enable intelligent task assignment and team formation.

Key Features:
- Skill profiling and capability mapping
- Strength and weakness identification
- Specialization area analysis
- Task-agent compatibility assessment
- Capability evolution tracking
- Performance context analysis
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import shared modules with absolute path resolution
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

# Import available shared module components
from interfaces import AgentConfig, OperationResult
from utils.error_handling import ErrorHandler, CircuitBreaker
from state_management import StateManager

# Define missing classes locally
TaskResult = OperationResult

# Import task tracking if available
try:
    from task_tracking import TaskMetrics
except ImportError:

    class TaskMetrics:
        def __init__(self, *args, **kwargs):
            pass


# Define capability-specific data classes
@dataclass
class CapabilityProfile:
    """Agent capability profile"""

    agent_id: str
    capabilities: Dict[str, float] = field(default_factory=dict)
    specializations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


class CapabilityDomain(Enum):
    """Domains for capability assessment"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    DEBUGGING = "debugging"
    INTEGRATION = "integration"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY = "security"
    DATA_ANALYSIS = "data_analysis"
    PROJECT_MANAGEMENT = "project_management"
    COORDINATION = "coordination"


class ProficiencyLevel(Enum):
    """Proficiency levels for capabilities"""

    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5


@dataclass
class CapabilityScore:
    """Individual capability scoring data"""

    domain: CapabilityDomain
    proficiency_level: ProficiencyLevel
    confidence_score: float  # 0.0 to 1.0
    evidence_count: int
    last_updated: datetime
    recent_performance: List[float] = field(default_factory=list)
    improvement_trend: float = 0.0  # -1.0 to 1.0, negative = declining


@dataclass
class AgentCapabilityProfile:
    """Comprehensive agent capability profile"""

    agent_id: str
    agent_name: str
    profile_generated: datetime

    # Core capabilities
    capability_scores: Dict[CapabilityDomain, CapabilityScore] = field(
        default_factory=dict
    )

    # Derived insights
    primary_strengths: List[CapabilityDomain] = field(default_factory=list)
    secondary_strengths: List[CapabilityDomain] = field(default_factory=list)
    improvement_areas: List[CapabilityDomain] = field(default_factory=list)

    # Specialization analysis
    specialization_areas: List[CapabilityDomain] = field(default_factory=list)
    versatility_score: float = 0.0  # 0.0 to 1.0

    # Performance context
    optimal_task_types: List[str] = field(default_factory=list)
    challenging_task_types: List[str] = field(default_factory=list)
    collaboration_preferences: List[str] = field(default_factory=list)

    # Evolution tracking
    capability_trend: Dict[CapabilityDomain, float] = field(default_factory=dict)
    skill_development_recommendations: List[str] = field(default_factory=list)


@dataclass
class TaskCapabilityRequirement:
    """Required capabilities for a specific task"""

    task_type: str
    required_capabilities: Dict[CapabilityDomain, ProficiencyLevel]
    preferred_capabilities: Dict[CapabilityDomain, ProficiencyLevel] = field(
        default_factory=dict
    )
    collaborative_aspects: List[CapabilityDomain] = field(default_factory=list)
    complexity_level: int = 1  # 1-5 scale


class CapabilityAssessment:
    """
    Comprehensive agent capability evaluation system.

    Analyzes agent capabilities across multiple domains, tracks evolution over time,
    and provides insights for optimal task assignment and team formation.
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        task_metrics: Optional[TaskMetrics] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """
        Initialize the capability assessment system.

        Args:
            state_manager: State management for persistent profiles
            task_metrics: Task tracking integration for evidence
            error_handler: Error handling for robust operation
        """
        self.logger = logging.getLogger(__name__)
        self.state_manager = state_manager or StateManager()
        self.task_metrics = task_metrics or TaskMetrics()
        self.error_handler = error_handler or ErrorHandler()

        # Circuit breaker for assessment operations
        self.assessment_circuit_breaker = CircuitBreaker(
            failure_threshold=3, timeout=300, name="capability_assessment"
        )

        # Capability profiles cache
        self.capability_profiles: Dict[str, AgentCapabilityProfile] = {}

        # Task capability requirements database
        self.task_requirements: Dict[str, TaskCapabilityRequirement] = {}

        # Assessment configuration
        self.assessment_config = {
            "min_evidence_count": 3,
            "confidence_threshold": 0.7,
            "trend_analysis_window": timedelta(days=30),
            "proficiency_thresholds": {
                ProficiencyLevel.NOVICE: 0.2,
                ProficiencyLevel.BEGINNER: 0.4,
                ProficiencyLevel.INTERMEDIATE: 0.6,
                ProficiencyLevel.ADVANCED: 0.8,
                ProficiencyLevel.EXPERT: 0.9,
            },
        }

        # Initialize task capability mappings
        self._initialize_task_capability_mappings()

        self.logger.info("CapabilityAssessment initialized")

    @CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    def assess_agent_capabilities(
        self, agent_id: str, force_refresh: bool = False
    ) -> AgentCapabilityProfile:
        """
        Perform comprehensive capability assessment for an agent.

        Args:
            agent_id: Unique identifier for the agent
            force_refresh: Force fresh assessment ignoring cache

        Returns:
            AgentCapabilityProfile: Comprehensive capability profile

        Raises:
            ValueError: If agent_id is invalid
            AssessmentError: If capability assessment fails
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        # Check cache if not forcing refresh
        if not force_refresh and agent_id in self.capability_profiles:
            profile = self.capability_profiles[agent_id]
            # Refresh if profile is older than 7 days
            if (datetime.now() - profile.profile_generated) < timedelta(days=7):
                self.logger.debug(
                    f"Returning cached capability profile for agent {agent_id}"
                )
                return profile

        try:
            self.logger.info(f"Assessing capabilities for agent {agent_id}")

            # Get agent configuration
            agent_config = self._get_agent_config(agent_id)

            # Initialize capability profile
            profile = AgentCapabilityProfile(
                agent_id=agent_id,
                agent_name=agent_config.name if agent_config else agent_id,
                profile_generated=datetime.now(),
            )

            # Assess capabilities across all domains
            self._assess_domain_capabilities(profile)

            # Identify strengths and weaknesses
            self._identify_capability_patterns(profile)

            # Analyze specialization areas
            self._analyze_specializations(profile)

            # Determine optimal task types
            self._determine_optimal_tasks(profile)

            # Assess collaboration preferences
            self._assess_collaboration_preferences(profile)

            # Track capability evolution
            self._track_capability_evolution(profile)

            # Generate development recommendations
            self._generate_development_recommendations(profile)

            # Cache the profile
            self.capability_profiles[agent_id] = profile

            # Persist to state management
            self._persist_capability_profile(profile)

            self.logger.info(f"Capability assessment completed for agent {agent_id}")
            return profile

        except Exception as e:
            self.logger.error(
                f"Failed to assess capabilities for agent {agent_id}: {e}"
            )
            raise AssessmentError(
                f"Capability assessment failed for agent {agent_id}: {e}"
            )

    def _assess_domain_capabilities(self, profile: AgentCapabilityProfile) -> None:
        """Assess capabilities across all domains."""
        try:
            # Get task history for the agent
            end_time = datetime.now()
            start_time = end_time - self.assessment_config["trend_analysis_window"]

            task_results = self.task_metrics.get_agent_task_results(
                profile.agent_id, start_time, end_time
            )

            if not task_results:
                self.logger.warning(
                    f"No task results found for agent {profile.agent_id}"
                )
                return

            # Group tasks by capability domain
            domain_tasks = self._group_tasks_by_domain(task_results)

            # Assess each domain
            for domain in CapabilityDomain:
                if domain in domain_tasks:
                    capability_score = self._assess_domain_capability(
                        domain, domain_tasks[domain], profile.agent_id
                    )
                    profile.capability_scores[domain] = capability_score
                else:
                    # No evidence for this domain
                    profile.capability_scores[domain] = CapabilityScore(
                        domain=domain,
                        proficiency_level=ProficiencyLevel.NOVICE,
                        confidence_score=0.0,
                        evidence_count=0,
                        last_updated=datetime.now(),
                    )

            self.logger.debug(
                f"Assessed {len(profile.capability_scores)} capability domains"
            )

        except Exception as e:
            self.logger.error(f"Failed to assess domain capabilities: {e}")

    def _assess_domain_capability(
        self, domain: CapabilityDomain, tasks: List[TaskResult], agent_id: str
    ) -> CapabilityScore:
        """Assess capability in a specific domain."""
        try:
            if not tasks:
                return CapabilityScore(
                    domain=domain,
                    proficiency_level=ProficiencyLevel.NOVICE,
                    confidence_score=0.0,
                    evidence_count=0,
                    last_updated=datetime.now(),
                )

            # Calculate performance metrics
            success_rates = [1.0 if task.success else 0.0 for task in tasks]
            quality_scores = [
                task.quality_score for task in tasks if task.quality_score is not None
            ]
            execution_times = [
                task.execution_time for task in tasks if task.execution_time is not None
            ]

            # Calculate domain performance score
            performance_score = np.mean(success_rates) if success_rates else 0.0

            # Adjust for quality if available
            if quality_scores:
                quality_factor = np.mean(quality_scores) / 100.0
                performance_score = (performance_score + quality_factor) / 2.0

            # Adjust for efficiency if available
            if execution_times:
                # Normalize execution times (lower is better)
                avg_time = np.mean(execution_times)
                efficiency_factor = min(
                    1.0, 300.0 / max(1.0, avg_time)
                )  # 5 minutes as baseline
                performance_score = (performance_score * 0.8) + (
                    efficiency_factor * 0.2
                )

            # Determine proficiency level
            proficiency_level = self._determine_proficiency_level(performance_score)

            # Calculate confidence based on evidence count and consistency
            confidence_score = self._calculate_confidence(success_rates, len(tasks))

            # Calculate improvement trend
            improvement_trend = self._calculate_improvement_trend(tasks)

            return CapabilityScore(
                domain=domain,
                proficiency_level=proficiency_level,
                confidence_score=confidence_score,
                evidence_count=len(tasks),
                last_updated=datetime.now(),
                recent_performance=[performance_score],
                improvement_trend=improvement_trend,
            )

        except Exception as e:
            self.logger.error(f"Failed to assess domain capability for {domain}: {e}")
            return CapabilityScore(
                domain=domain,
                proficiency_level=ProficiencyLevel.NOVICE,
                confidence_score=0.0,
                evidence_count=0,
                last_updated=datetime.now(),
            )

    def _group_tasks_by_domain(
        self, tasks: List[TaskResult]
    ) -> Dict[CapabilityDomain, List[TaskResult]]:
        """Group tasks by their primary capability domain."""
        domain_tasks = {domain: [] for domain in CapabilityDomain}

        for task in tasks:
            # Determine primary domain based on task type or content
            primary_domain = self._determine_task_domain(task)
            if primary_domain:
                domain_tasks[primary_domain].append(task)

        return domain_tasks

    def _determine_task_domain(self, task: TaskResult) -> Optional[CapabilityDomain]:
        """Determine the primary capability domain for a task."""
        # This would analyze task type, description, etc. to determine domain
        # For now, use basic heuristics based on task type
        task_type = getattr(task, "task_type", "").lower()

        domain_keywords = {
            CapabilityDomain.CODE_GENERATION: [
                "implement",
                "create",
                "build",
                "develop",
                "code",
            ],
            CapabilityDomain.CODE_REVIEW: ["review", "analyze", "inspect", "evaluate"],
            CapabilityDomain.TESTING: ["test", "verify", "validate", "check"],
            CapabilityDomain.DOCUMENTATION: ["document", "readme", "guide", "doc"],
            CapabilityDomain.ARCHITECTURE: [
                "design",
                "architecture",
                "structure",
                "pattern",
            ],
            CapabilityDomain.DEBUGGING: ["debug", "fix", "resolve", "troubleshoot"],
            CapabilityDomain.INTEGRATION: ["integrate", "merge", "combine", "connect"],
            CapabilityDomain.PERFORMANCE_OPTIMIZATION: [
                "optimize",
                "performance",
                "speed",
                "efficiency",
            ],
            CapabilityDomain.SECURITY: ["security", "secure", "auth", "permission"],
            CapabilityDomain.DATA_ANALYSIS: ["analyze", "data", "metrics", "report"],
            CapabilityDomain.PROJECT_MANAGEMENT: [
                "manage",
                "coordinate",
                "plan",
                "organize",
            ],
            CapabilityDomain.COORDINATION: [
                "coordinate",
                "orchestrate",
                "team",
                "workflow",
            ],
        }

        for domain, keywords in domain_keywords.items():
            if any(keyword in task_type for keyword in keywords):
                return domain

        # Default to code generation if no specific match
        return CapabilityDomain.CODE_GENERATION

    def _determine_proficiency_level(
        self, performance_score: float
    ) -> ProficiencyLevel:
        """Determine proficiency level based on performance score."""
        thresholds = self.assessment_config["proficiency_thresholds"]

        if performance_score >= thresholds[ProficiencyLevel.EXPERT]:
            return ProficiencyLevel.EXPERT
        elif performance_score >= thresholds[ProficiencyLevel.ADVANCED]:
            return ProficiencyLevel.ADVANCED
        elif performance_score >= thresholds[ProficiencyLevel.INTERMEDIATE]:
            return ProficiencyLevel.INTERMEDIATE
        elif performance_score >= thresholds[ProficiencyLevel.BEGINNER]:
            return ProficiencyLevel.BEGINNER
        else:
            return ProficiencyLevel.NOVICE

    def _calculate_confidence(
        self, success_rates: List[float], evidence_count: int
    ) -> float:
        """Calculate confidence score based on evidence consistency and count."""
        if not success_rates or evidence_count == 0:
            return 0.0

        # Base confidence on evidence count
        count_factor = min(1.0, evidence_count / 10.0)  # Max confidence at 10+ tasks

        # Adjust for consistency
        if len(success_rates) > 1:
            consistency = 1.0 - np.std(success_rates)
            consistency_factor = max(0.0, consistency)
        else:
            consistency_factor = 0.5  # Moderate confidence for single data point

        confidence = (count_factor * 0.6) + (consistency_factor * 0.4)
        return min(1.0, confidence)

    def _calculate_improvement_trend(self, tasks: List[TaskResult]) -> float:
        """Calculate improvement trend from task results."""
        if len(tasks) < 2:
            return 0.0

        # Sort tasks by date
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t.completed_at
            if hasattr(t, "completed_at")
            else datetime.now(),
        )

        # Calculate performance over time
        performances = []
        for task in sorted_tasks:
            performance = 1.0 if task.success else 0.0
            if hasattr(task, "quality_score") and task.quality_score is not None:
                performance = (performance + task.quality_score / 100.0) / 2.0
            performances.append(performance)

        # Calculate trend using linear regression slope
        if len(performances) >= 2:
            x = np.arange(len(performances))
            slope = np.polyfit(x, performances, 1)[0]
            return max(-1.0, min(1.0, slope * 10))  # Normalize to -1 to 1 range

        return 0.0

    def _identify_capability_patterns(self, profile: AgentCapabilityProfile) -> None:
        """Identify strength and weakness patterns."""
        try:
            # Sort capabilities by proficiency and confidence
            sorted_capabilities = sorted(
                profile.capability_scores.items(),
                key=lambda x: (x[1].proficiency_level.value, x[1].confidence_score),
                reverse=True,
            )

            # Identify primary strengths (top 3 with high confidence)
            for domain, score in sorted_capabilities[:3]:
                if (
                    score.proficiency_level.value >= 3
                    and score.confidence_score
                    >= self.assessment_config["confidence_threshold"]
                ):
                    profile.primary_strengths.append(domain)

            # Identify secondary strengths (next 3 with moderate confidence)
            for domain, score in sorted_capabilities[3:6]:
                if score.proficiency_level.value >= 2 and score.confidence_score >= 0.5:
                    profile.secondary_strengths.append(domain)

            # Identify improvement areas (lowest scoring with sufficient evidence)
            for domain, score in reversed(sorted_capabilities):
                if (
                    score.evidence_count >= self.assessment_config["min_evidence_count"]
                    and score.proficiency_level.value <= 2
                ):
                    profile.improvement_areas.append(domain)
                    if len(profile.improvement_areas) >= 3:
                        break

            self.logger.debug(
                f"Identified {len(profile.primary_strengths)} primary strengths"
            )

        except Exception as e:
            self.logger.error(f"Failed to identify capability patterns: {e}")

    def _analyze_specializations(self, profile: AgentCapabilityProfile) -> None:
        """Analyze agent specialization areas."""
        try:
            # Calculate versatility score
            high_proficiency_count = sum(
                1
                for score in profile.capability_scores.values()
                if score.proficiency_level.value >= 3
                and score.confidence_score
                >= self.assessment_config["confidence_threshold"]
            )

            total_domains = len(CapabilityDomain)
            profile.versatility_score = high_proficiency_count / total_domains

            # Identify specialization areas (exceptional capabilities)
            for domain, score in profile.capability_scores.items():
                if (
                    score.proficiency_level.value >= 4
                    and score.confidence_score >= 0.8
                    and score.evidence_count
                    >= self.assessment_config["min_evidence_count"]
                ):
                    profile.specialization_areas.append(domain)

            self.logger.debug(f"Versatility score: {profile.versatility_score:.2f}")

        except Exception as e:
            self.logger.error(f"Failed to analyze specializations: {e}")

    def _determine_optimal_tasks(self, profile: AgentCapabilityProfile) -> None:
        """Determine optimal and challenging task types for the agent."""
        try:
            # Map capabilities to task types
            for domain in profile.primary_strengths:
                task_types = self._get_task_types_for_domain(domain)
                profile.optimal_task_types.extend(task_types)

            for domain in profile.improvement_areas:
                task_types = self._get_task_types_for_domain(domain)
                profile.challenging_task_types.extend(task_types)

            # Remove duplicates
            profile.optimal_task_types = list(set(profile.optimal_task_types))
            profile.challenging_task_types = list(set(profile.challenging_task_types))

        except Exception as e:
            self.logger.error(f"Failed to determine optimal tasks: {e}")

    def _assess_collaboration_preferences(
        self, profile: AgentCapabilityProfile
    ) -> None:
        """Assess collaboration preferences and patterns."""
        try:
            # Analyze collaboration domains
            collaboration_domains = [
                CapabilityDomain.COORDINATION,
                CapabilityDomain.PROJECT_MANAGEMENT,
                CapabilityDomain.CODE_REVIEW,
                CapabilityDomain.ARCHITECTURE,
            ]

            for domain in collaboration_domains:
                if domain in profile.capability_scores:
                    score = profile.capability_scores[domain]
                    if (
                        score.proficiency_level.value >= 3
                        and score.confidence_score >= 0.6
                    ):
                        profile.collaboration_preferences.append(domain.value)

        except Exception as e:
            self.logger.error(f"Failed to assess collaboration preferences: {e}")

    def _track_capability_evolution(self, profile: AgentCapabilityProfile) -> None:
        """Track capability evolution trends."""
        try:
            for domain, score in profile.capability_scores.items():
                profile.capability_trend[domain] = score.improvement_trend

        except Exception as e:
            self.logger.error(f"Failed to track capability evolution: {e}")

    def _generate_development_recommendations(
        self, profile: AgentCapabilityProfile
    ) -> None:
        """Generate skill development recommendations."""
        try:
            recommendations = []

            # Recommendations for improvement areas
            for domain in profile.improvement_areas:
                recommendations.append(
                    f"Focus on {domain.value} tasks to build proficiency"
                )

            # Recommendations for emerging strengths
            for domain, score in profile.capability_scores.items():
                if score.proficiency_level.value == 3 and score.improvement_trend > 0.1:
                    recommendations.append(
                        f"Continue developing {domain.value} - showing strong improvement"
                    )

            # Versatility recommendations
            if profile.versatility_score < 0.3:
                recommendations.append(
                    "Consider expanding into new capability domains for increased versatility"
                )

            profile.skill_development_recommendations = recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate development recommendations: {e}")

    def _get_task_types_for_domain(self, domain: CapabilityDomain) -> List[str]:
        """Get task types associated with a capability domain."""
        domain_task_types = {
            CapabilityDomain.CODE_GENERATION: [
                "implementation",
                "feature_development",
                "bug_fix",
            ],
            CapabilityDomain.CODE_REVIEW: [
                "code_review",
                "security_review",
                "performance_review",
            ],
            CapabilityDomain.TESTING: [
                "unit_testing",
                "integration_testing",
                "test_automation",
            ],
            CapabilityDomain.DOCUMENTATION: [
                "documentation",
                "api_docs",
                "user_guides",
            ],
            CapabilityDomain.ARCHITECTURE: [
                "system_design",
                "architecture_review",
                "pattern_implementation",
            ],
            CapabilityDomain.DEBUGGING: [
                "bug_investigation",
                "performance_debugging",
                "error_resolution",
            ],
            CapabilityDomain.INTEGRATION: [
                "api_integration",
                "service_integration",
                "data_integration",
            ],
            CapabilityDomain.PERFORMANCE_OPTIMIZATION: [
                "performance_tuning",
                "optimization",
                "profiling",
            ],
            CapabilityDomain.SECURITY: [
                "security_audit",
                "vulnerability_assessment",
                "secure_coding",
            ],
            CapabilityDomain.DATA_ANALYSIS: [
                "data_analysis",
                "reporting",
                "metrics_analysis",
            ],
            CapabilityDomain.PROJECT_MANAGEMENT: [
                "project_planning",
                "task_coordination",
                "resource_management",
            ],
            CapabilityDomain.COORDINATION: [
                "team_coordination",
                "workflow_management",
                "cross_team_collaboration",
            ],
        }

        return domain_task_types.get(domain, [])

    def _initialize_task_capability_mappings(self) -> None:
        """Initialize task capability requirement mappings."""
        # This would be loaded from configuration or learned from data
        # For now, provide basic mappings
        self.task_requirements = {
            "implementation": TaskCapabilityRequirement(
                task_type="implementation",
                required_capabilities={
                    CapabilityDomain.CODE_GENERATION: ProficiencyLevel.INTERMEDIATE
                },
                preferred_capabilities={
                    CapabilityDomain.TESTING: ProficiencyLevel.BEGINNER,
                    CapabilityDomain.DOCUMENTATION: ProficiencyLevel.BEGINNER,
                },
            ),
            "code_review": TaskCapabilityRequirement(
                task_type="code_review",
                required_capabilities={
                    CapabilityDomain.CODE_REVIEW: ProficiencyLevel.ADVANCED
                },
                preferred_capabilities={
                    CapabilityDomain.SECURITY: ProficiencyLevel.INTERMEDIATE,
                    CapabilityDomain.PERFORMANCE_OPTIMIZATION: ProficiencyLevel.INTERMEDIATE,
                },
            ),
            # Additional mappings would be added here
        }

    def _get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration from state manager."""
        try:
            config_data = self.state_manager.get_agent_config(agent_id)
            if config_data:
                return AgentConfig(**config_data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get agent config for {agent_id}: {e}")
            return None

    def _persist_capability_profile(self, profile: AgentCapabilityProfile) -> None:
        """Persist capability profile to state management."""
        try:
            profile_data = {
                "agent_id": profile.agent_id,
                "agent_name": profile.agent_name,
                "profile_generated": profile.profile_generated.isoformat(),
                "capability_scores": {
                    domain.value: {
                        "proficiency_level": score.proficiency_level.value,
                        "confidence_score": score.confidence_score,
                        "evidence_count": score.evidence_count,
                        "last_updated": score.last_updated.isoformat(),
                        "improvement_trend": score.improvement_trend,
                    }
                    for domain, score in profile.capability_scores.items()
                },
                "primary_strengths": [
                    domain.value for domain in profile.primary_strengths
                ],
                "secondary_strengths": [
                    domain.value for domain in profile.secondary_strengths
                ],
                "improvement_areas": [
                    domain.value for domain in profile.improvement_areas
                ],
                "specialization_areas": [
                    domain.value for domain in profile.specialization_areas
                ],
                "versatility_score": profile.versatility_score,
                "optimal_task_types": profile.optimal_task_types,
                "challenging_task_types": profile.challenging_task_types,
                "collaboration_preferences": profile.collaboration_preferences,
                "skill_development_recommendations": profile.skill_development_recommendations,
            }

            self.state_manager.save_agent_capability_profile(
                profile.agent_id, profile_data
            )

        except Exception as e:
            self.logger.error(
                f"Failed to persist capability profile for {profile.agent_id}: {e}"
            )

    def get_capability_match_score(
        self, agent_id: str, task_requirements: TaskCapabilityRequirement
    ) -> float:
        """
        Calculate how well an agent matches task capability requirements.

        Args:
            agent_id: Agent to evaluate
            task_requirements: Required capabilities for the task

        Returns:
            float: Match score from 0.0 to 1.0
        """
        try:
            profile = self.assess_agent_capabilities(agent_id)

            if not profile.capability_scores:
                return 0.0

            # Calculate required capability match
            required_score = 0.0
            for (
                domain,
                required_level,
            ) in task_requirements.required_capabilities.items():
                if domain in profile.capability_scores:
                    agent_score = profile.capability_scores[domain]
                    level_match = min(
                        1.0, agent_score.proficiency_level.value / required_level.value
                    )
                    confidence_weight = agent_score.confidence_score
                    required_score += level_match * confidence_weight

            if task_requirements.required_capabilities:
                required_score /= len(task_requirements.required_capabilities)

            # Calculate preferred capability bonus
            preferred_score = 0.0
            if task_requirements.preferred_capabilities:
                for (
                    domain,
                    preferred_level,
                ) in task_requirements.preferred_capabilities.items():
                    if domain in profile.capability_scores:
                        agent_score = profile.capability_scores[domain]
                        level_match = min(
                            1.0,
                            agent_score.proficiency_level.value / preferred_level.value,
                        )
                        confidence_weight = agent_score.confidence_score
                        preferred_score += level_match * confidence_weight

                preferred_score /= len(task_requirements.preferred_capabilities)
                preferred_score *= 0.3  # Weight preferred capabilities at 30%

            # Combine scores
            final_score = (required_score * 0.7) + preferred_score

            return min(1.0, final_score)

        except Exception as e:
            self.logger.error(f"Failed to calculate capability match score: {e}")
            return 0.0


class AssessmentError(Exception):
    """Exception raised when capability assessment fails."""

    pass
