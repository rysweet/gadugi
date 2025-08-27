"""
TeamCoach Phase 3: Strategic Planner

Provides long-term strategic planning for multi-agent teams including
capacity planning, skill development roadmaps, and team evolution strategies.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional

from ..phase1.capability_assessment import CapabilityAssessment
from ..phase1.performance_analytics import AgentPerformanceAnalyzer

logger = logging.getLogger(__name__)


class PlanningHorizon(Enum):
    """Time horizons for strategic planning."""

    SHORT_TERM = "short_term"  # 1-4 weeks
    MEDIUM_TERM = "medium_term"  # 1-3 months
    LONG_TERM = "long_term"  # 3-12 months


class StrategyType(Enum):
    """Types of strategic initiatives."""

    CAPACITY_EXPANSION = "capacity_expansion"
    SKILL_DEVELOPMENT = "skill_development"
    PROCESS_IMPROVEMENT = "process_improvement"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    TEAM_RESTRUCTURING = "team_restructuring"
    QUALITY_ENHANCEMENT = "quality_enhancement"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"


class StrategyPriority(Enum):
    """Priority levels for strategic initiatives."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StrategicGoal:
    """Represents a strategic goal for the team."""

    goal_id: str
    title: str
    description: str
    target_metric: str
    current_value: float
    target_value: float
    deadline: datetime
    priority: StrategyPriority
    dependencies: List[str]


@dataclass
class StrategicInitiative:
    """Represents a strategic initiative to achieve goals."""

    initiative_id: str
    type: StrategyType
    title: str
    description: str
    goals_addressed: List[str]
    impact_estimate: Dict[str, float]  # metric -> expected change
    resource_requirements: Dict[str, Any]
    timeline: Dict[str, datetime]  # phase -> date
    implementation_steps: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    owner: Optional[str] = None


@dataclass
class CapacityPlan:
    """Team capacity planning information."""

    current_capacity: Dict[str, float]  # skill -> FTE
    projected_demand: Dict[str, Dict[str, float]]  # timeframe -> skill -> FTE
    gaps: Dict[str, Dict[str, float]]  # timeframe -> skill -> gap
    recommendations: List[str]


@dataclass
class SkillDevelopmentPlan:
    """Plan for developing team skills."""

    skill_gaps: Dict[str, float]  # skill -> gap size
    development_paths: Dict[str, List[Dict[str, Any]]]  # agent -> path
    training_calendar: Dict[datetime, List[str]]  # date -> training events
    investment_required: Dict[str, float]  # resource -> amount


@dataclass
class TeamEvolutionPlan:
    """Comprehensive plan for team evolution."""

    vision: str
    strategic_goals: List[StrategicGoal]
    initiatives: List[StrategicInitiative]
    capacity_plan: CapacityPlan
    skill_plan: SkillDevelopmentPlan
    roadmap: Dict[PlanningHorizon, List[str]]  # horizon -> initiative IDs
    success_metrics: Dict[str, float]
    review_schedule: List[datetime]


class StrategicPlanner:
    """
    Provides strategic planning capabilities for multi-agent teams.

    Features:
    - Long-term goal setting and tracking
    - Capacity planning and forecasting
    - Skill development roadmaps
    - Strategic initiative planning
    - Team evolution guidance
    """

    def __init__(
        self,
        performance_analyzer: AgentPerformanceAnalyzer,
        capability_assessment: CapabilityAssessment,
    ):
        """Initialize the strategic planner."""
        self.performance_analyzer = performance_analyzer
        self.capability_assessment = capability_assessment

        # Strategic planning parameters
        self.planning_horizons = {
            PlanningHorizon.SHORT_TERM: timedelta(weeks=4),
            PlanningHorizon.MEDIUM_TERM: timedelta(weeks=12),
            PlanningHorizon.LONG_TERM: timedelta(weeks=52),
        }

        self.skill_importance_weights = {
            "critical": 3.0,
            "important": 2.0,
            "useful": 1.0,
            "optional": 0.5,
        }

    def create_team_evolution_plan(
        self,
        team_id: str,
        agent_ids: List[str],
        business_objectives: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> TeamEvolutionPlan:
        """
        Create a comprehensive team evolution plan.

        Args:
            team_id: ID of the team
            agent_ids: List of agent IDs in the team
            business_objectives: High-level business objectives
            constraints: Optional constraints (budget, timeline, etc.)

        Returns:
            Comprehensive team evolution plan
        """
        # Define vision based on objectives
        vision = self._define_team_vision(business_objectives)

        # Translate business objectives to strategic goals
        strategic_goals = self._create_strategic_goals(business_objectives, agent_ids)

        # Analyze current state
        current_state = self._analyze_current_state(agent_ids)

        # Create capacity plan
        capacity_plan = self._create_capacity_plan(
            agent_ids, strategic_goals, current_state
        )

        # Create skill development plan
        skill_plan = self._create_skill_development_plan(
            agent_ids, strategic_goals, current_state
        )

        # Generate strategic initiatives
        initiatives = self._generate_strategic_initiatives(
            strategic_goals, capacity_plan, skill_plan, constraints
        )

        # Create roadmap
        roadmap = self._create_strategic_roadmap(initiatives, strategic_goals)

        # Define success metrics
        success_metrics = self._define_success_metrics(strategic_goals)

        # Create review schedule
        review_schedule = self._create_review_schedule(roadmap)

        # Create the plan
        plan = TeamEvolutionPlan(
            vision=vision,
            strategic_goals=strategic_goals,
            initiatives=initiatives,
            capacity_plan=capacity_plan,
            skill_plan=skill_plan,
            roadmap=roadmap,
            success_metrics=success_metrics,
            review_schedule=review_schedule,
        )

        return plan

    def _define_team_vision(self, business_objectives: List[Dict[str, Any]]) -> str:
        """Define team vision based on business objectives."""
        if not business_objectives:
            return "Achieve operational excellence through continuous improvement"

        # Extract key themes from objectives
        themes = []
        for obj in business_objectives:
            if "efficiency" in obj.get("description", "").lower():
                themes.append("maximum efficiency")
            if "quality" in obj.get("description", "").lower():
                themes.append("exceptional quality")
            if "innovation" in obj.get("description", "").lower():
                themes.append("continuous innovation")
            if "scale" in obj.get("description", "").lower():
                themes.append("scalable operations")

        if themes:
            return f"Build a world-class team delivering {', '.join(set(themes))}"
        else:
            return (
                "Create a high-performing, adaptable team ready for future challenges"
            )

    def _create_strategic_goals(
        self, business_objectives: List[Dict[str, Any]], agent_ids: List[str]
    ) -> List[StrategicGoal]:
        """Create strategic goals from business objectives."""
        goals = []

        for i, obj in enumerate(business_objectives):
            # Create goal from objective
            goal = StrategicGoal(
                goal_id=f"goal_{i + 1}",
                title=obj.get("title", f"Strategic Goal {i + 1}"),
                description=obj.get("description", ""),
                target_metric=obj.get("metric", "performance_score"),
                current_value=self._get_current_metric_value(
                    obj.get("metric", "performance_score"), agent_ids
                ),
                target_value=obj.get("target", 0.85),
                deadline=datetime.utcnow()
                + timedelta(days=obj.get("timeline_days", 90)),
                priority=StrategyPriority(obj.get("priority", "medium")),
                dependencies=obj.get("dependencies", []),
            )
            goals.append(goal)

        # Add default goals if none provided
        if not goals:
            goals.extend(self._create_default_strategic_goals(agent_ids))

        return goals

    def _create_default_strategic_goals(
        self, agent_ids: List[str]
    ) -> List[StrategicGoal]:
        """Create default strategic goals."""
        current_performance = self._calculate_team_performance(agent_ids)

        return [
            StrategicGoal(
                goal_id="goal_efficiency",
                title="Improve Team Efficiency",
                description="Achieve 25% improvement in overall team efficiency",
                target_metric="efficiency_ratio",
                current_value=current_performance.get("efficiency", 0.6),
                target_value=0.85,
                deadline=datetime.utcnow() + timedelta(weeks=12),
                priority=StrategyPriority.HIGH,
                dependencies=[],
            ),
            StrategicGoal(
                goal_id="goal_quality",
                title="Enhance Quality Standards",
                description="Achieve 95% success rate across all operations",
                target_metric="success_rate",
                current_value=current_performance.get("success_rate", 0.75),
                target_value=0.95,
                deadline=datetime.utcnow() + timedelta(weeks=16),
                priority=StrategyPriority.HIGH,
                dependencies=[],
            ),
            StrategicGoal(
                goal_id="goal_scalability",
                title="Build Scalable Operations",
                description="Develop capability to handle 3x current workload",
                target_metric="capacity_multiplier",
                current_value=1.0,
                target_value=3.0,
                deadline=datetime.utcnow() + timedelta(weeks=26),
                priority=StrategyPriority.MEDIUM,
                dependencies=["goal_efficiency"],
            ),
        ]

    def _analyze_current_state(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze current team state."""
        state = {
            "performance_metrics": {},
            "capability_coverage": {},
            "skill_distribution": {},
            "workload_distribution": {},
            "collaboration_patterns": {},
        }

        # Aggregate performance metrics
        for _ in agent_ids:
            # Mock performance data
            performance_data = {"success_rate": 0.8, "efficiency": 0.7, "quality_score": 0.85}
            for metric, value in performance_data.items():
                if metric not in state["performance_metrics"]:
                    state["performance_metrics"][metric] = []
                state["performance_metrics"][metric].append(value)

        # Average the metrics
        for metric, values in state["performance_metrics"].items():
            state["performance_metrics"][metric] = (
                sum(values) / len(values) if values else 0
            )

        # Analyze capability coverage
        all_skills = set()
        skill_counts = {}

        for _ in agent_ids:
            # Mock capabilities data
            domain_scores = {"python": 0.8, "testing": 0.6, "debugging": 0.9, "devops": 0.5}
            for skill, score in domain_scores.items():
                all_skills.add(skill)
                if score > 0.7:  # Competent level
                    if skill not in skill_counts:
                        skill_counts[skill] = 0
                    skill_counts[skill] += 1

        state["capability_coverage"] = {
            skill: count / len(agent_ids) for skill, count in skill_counts.items()
        }

        # Add missing skills
        for skill in all_skills:
            if skill not in state["capability_coverage"]:
                state["capability_coverage"][skill] = 0

        return state

    def _create_capacity_plan(
        self,
        agent_ids: List[str],
        goals: List[StrategicGoal],
        current_state: Dict[str, Any],
    ) -> CapacityPlan:
        """Create capacity plan based on goals and current state."""

        # Calculate current capacity
        current_capacity = self._calculate_current_capacity(agent_ids)

        # Project demand based on goals
        projected_demand = self._project_capacity_demand(goals, current_state)

        # Calculate gaps
        gaps = self._calculate_capacity_gaps(current_capacity, projected_demand)

        # Generate recommendations
        recommendations = self._generate_capacity_recommendations(gaps)

        return CapacityPlan(
            current_capacity=current_capacity,
            projected_demand=projected_demand,
            gaps=gaps,
            recommendations=recommendations,
        )

    def _create_skill_development_plan(
        self,
        agent_ids: List[str],
        goals: List[StrategicGoal],
        current_state: Dict[str, Any],
    ) -> SkillDevelopmentPlan:
        """Create skill development plan."""

        # Identify skill gaps
        skill_gaps = self._identify_skill_gaps(goals, current_state)

        # Create development paths for each agent
        development_paths = {}
        for agent_id in agent_ids:
            development_paths[agent_id] = self._create_agent_development_path(
                agent_id, skill_gaps
            )

        # Create training calendar
        training_calendar = self._create_training_calendar(
            development_paths, skill_gaps
        )

        # Calculate investment required
        investment_required = self._calculate_training_investment(
            development_paths, training_calendar
        )

        return SkillDevelopmentPlan(
            skill_gaps=skill_gaps,
            development_paths=development_paths,
            training_calendar=training_calendar,
            investment_required=investment_required,
        )

    def _generate_strategic_initiatives(
        self,
        goals: List[StrategicGoal],
        capacity_plan: CapacityPlan,
        skill_plan: SkillDevelopmentPlan,
        constraints: Optional[Dict[str, Any]],
    ) -> List[StrategicInitiative]:
        """Generate strategic initiatives to achieve goals."""
        initiatives = []

        # Generate capacity initiatives
        if capacity_plan.gaps:
            for timeframe, gaps in capacity_plan.gaps.items():
                if any(gap > 0.5 for gap in gaps.values()):
                    initiative = StrategicInitiative(
                        initiative_id=f"init_capacity_{timeframe}",
                        type=StrategyType.CAPACITY_EXPANSION,
                        title=f"Expand Team Capacity - {timeframe}",
                        description=f"Address capacity gaps in {', '.join(gaps.keys())}",
                        goals_addressed=[
                            g.goal_id for g in goals if "scale" in g.title.lower()
                        ],
                        impact_estimate={"capacity": sum(gaps.values())},
                        resource_requirements={
                            "new_agents": int(sum(gaps.values())),
                            "onboarding_time": "2 weeks per agent",
                        },
                        timeline={
                            "planning": datetime.utcnow() + timedelta(weeks=1),
                            "execution": datetime.utcnow() + timedelta(weeks=4),
                            "completion": datetime.utcnow() + timedelta(weeks=8),
                        },
                        risks=[
                            {
                                "risk": "Talent availability",
                                "mitigation": "Start recruiting early",
                            },
                            {
                                "risk": "Onboarding overhead",
                                "mitigation": "Prepare training materials",
                            },
                        ],
                        success_criteria=[
                            "All capacity gaps filled",
                            "New agents performing at 80% within 4 weeks",
                        ],
                        owner=None,
                    )
                    initiatives.append(initiative)

        # Generate skill development initiatives
        if skill_plan.skill_gaps:
            critical_gaps = {k: v for k, v in skill_plan.skill_gaps.items() if v > 0.3}
            if critical_gaps:
                initiative = StrategicInitiative(
                    initiative_id="init_skill_development",
                    type=StrategyType.SKILL_DEVELOPMENT,
                    title="Comprehensive Skill Development Program",
                    description=f"Address skill gaps in {', '.join(critical_gaps.keys())}",
                    goals_addressed=[
                        g.goal_id for g in goals if "quality" in g.title.lower()
                    ],
                    impact_estimate={
                        "skill_coverage": 0.5,  # 50% improvement
                        "quality_improvement": 0.2,  # 20% quality boost
                    },
                    resource_requirements={
                        "training_hours": len(skill_plan.development_paths) * 40,
                        "external_training": skill_plan.investment_required.get(
                            "external_training", 0
                        ),
                    },
                    timeline={
                        "planning": datetime.utcnow() + timedelta(weeks=2),
                        "execution": datetime.utcnow() + timedelta(weeks=4),
                        "completion": datetime.utcnow() + timedelta(weeks=16),
                    },
                    risks=[
                        {
                            "risk": "Training time impact",
                            "mitigation": "Stagger training schedules",
                        },
                        {
                            "risk": "Skill retention",
                            "mitigation": "Implement practice projects",
                        },
                    ],
                    success_criteria=[
                        "80% of agents complete training",
                        "Skill assessment scores improve by 30%",
                    ],
                    owner=None,
                )
                initiatives.append(initiative)

        # Generate process improvement initiatives
        if any(g.target_metric == "efficiency_ratio" for g in goals):
            initiative = StrategicInitiative(
                initiative_id="init_process_optimization",
                type=StrategyType.PROCESS_IMPROVEMENT,
                title="Workflow Optimization Initiative",
                description="Streamline processes for maximum efficiency",
                goals_addressed=[
                    g.goal_id for g in goals if "efficiency" in g.title.lower()
                ],
                impact_estimate={
                    "efficiency_ratio": 0.25,  # 25% improvement
                    "throughput": 0.3,  # 30% throughput increase
                },
                resource_requirements={
                    "analysis_time": "2 weeks",
                    "implementation_time": "4 weeks",
                },
                timeline={
                    "planning": datetime.utcnow() + timedelta(weeks=1),
                    "execution": datetime.utcnow() + timedelta(weeks=3),
                    "completion": datetime.utcnow() + timedelta(weeks=8),
                },
                risks=[
                    {
                        "risk": "Change resistance",
                        "mitigation": "Involve agents in design",
                    },
                    {"risk": "Temporary disruption", "mitigation": "Phased rollout"},
                ],
                success_criteria=[
                    "Process cycle time reduced by 25%",
                    "Error rate reduced by 40%",
                ],
                owner=None,
            )
            initiatives.append(initiative)

        # Sort by priority and impact
        initiatives.sort(key=lambda i: sum(i.impact_estimate.values()), reverse=True)

        return initiatives

    def _create_strategic_roadmap(
        self, initiatives: List[StrategicInitiative], goals: List[StrategicGoal]
    ) -> Dict[PlanningHorizon, List[str]]:
        """Create strategic roadmap organizing initiatives by timeline."""
        roadmap = {
            PlanningHorizon.SHORT_TERM: [],
            PlanningHorizon.MEDIUM_TERM: [],
            PlanningHorizon.LONG_TERM: [],
        }

        now = datetime.utcnow()

        for initiative in initiatives:
            completion = initiative.timeline.get("completion", now)
            days_to_complete = (completion - now).days

            if days_to_complete <= 28:  # 4 weeks
                roadmap[PlanningHorizon.SHORT_TERM].append(initiative.initiative_id)
            elif days_to_complete <= 84:  # 12 weeks
                roadmap[PlanningHorizon.MEDIUM_TERM].append(initiative.initiative_id)
            else:
                roadmap[PlanningHorizon.LONG_TERM].append(initiative.initiative_id)

        return roadmap

    def _define_success_metrics(self, goals: List[StrategicGoal]) -> Dict[str, float]:
        """Define success metrics based on strategic goals."""
        metrics = {}

        for goal in goals:
            metrics[goal.target_metric] = goal.target_value

        # Add standard metrics
        if "team_satisfaction" not in metrics:
            metrics["team_satisfaction"] = 0.8  # 80% satisfaction
        if "innovation_index" not in metrics:
            metrics["innovation_index"] = 0.7  # 70% innovation score

        return metrics

    def _create_review_schedule(
        self, roadmap: Dict[PlanningHorizon, List[str]]
    ) -> List[datetime]:
        """Create review schedule for the strategic plan."""
        schedule = []
        now = datetime.utcnow()

        # Monthly reviews for short-term initiatives
        if roadmap[PlanningHorizon.SHORT_TERM]:
            for i in range(3):
                schedule.append(now + timedelta(weeks=4 * (i + 1)))

        # Quarterly reviews for medium-term
        if roadmap[PlanningHorizon.MEDIUM_TERM]:
            for i in range(4):
                schedule.append(now + timedelta(weeks=12 * (i + 1)))

        # Semi-annual reviews for long-term
        if roadmap[PlanningHorizon.LONG_TERM]:
            for i in range(2):
                schedule.append(now + timedelta(weeks=26 * (i + 1)))

        # Remove duplicates and sort
        schedule = sorted(list(set(schedule)))

        return schedule

    def _get_current_metric_value(self, metric: str, agent_ids: List[str]) -> float:
        """Get current value for a specific metric."""
        values = []

        for _ in agent_ids:
            # Mock performance data lookup
            performance_data = {"success_rate": 0.8, "efficiency": 0.7, "quality_score": 0.85}
            if metric in performance_data:
                values.append(performance_data[metric])

        return sum(values) / len(values) if values else 0.0

    def _calculate_team_performance(self, agent_ids: List[str]) -> Dict[str, float]:
        """Calculate overall team performance metrics."""
        metrics = {
            "efficiency": 0.6,
            "success_rate": 0.75,
            "throughput": 10.0,
            "quality_score": 0.8,
        }

        # Aggregate from individual agents
        for _ in agent_ids:
            # Mock performance aggregation
            agent_success_rate = 0.8  # Mock individual success rate
            metrics["success_rate"] = (
                metrics["success_rate"] + agent_success_rate
            ) / 2

        return metrics

    def _calculate_current_capacity(self, agent_ids: List[str]) -> Dict[str, float]:
        """Calculate current team capacity by skill."""
        capacity = {}

        for _ in agent_ids:
            # Mock capabilities data
            domain_scores = {"python": 0.8, "testing": 0.6, "debugging": 0.9, "devops": 0.5}
            for skill, score in domain_scores.items():
                if score > 0.6:  # Capable enough to contribute
                    if skill not in capacity:
                        capacity[skill] = 0
                    capacity[skill] += score  # FTE equivalent

        return capacity

    def _project_capacity_demand(
        self, goals: List[StrategicGoal], current_state: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Project future capacity demand based on goals."""
        demand = {"short_term": {}, "medium_term": {}, "long_term": {}}

        # Base demand on current workload
        current_capacity = current_state.get("capability_coverage", {})

        for skill, coverage in current_capacity.items():
            # Assume 20% growth short term, 50% medium, 100% long term
            demand["short_term"][skill] = coverage * 1.2
            demand["medium_term"][skill] = coverage * 1.5
            demand["long_term"][skill] = coverage * 2.0

        # Adjust based on goals
        for goal in goals:
            if goal.target_value > goal.current_value * 1.5:
                # Significant growth goal - increase demand
                for timeframe in demand:
                    for skill in demand[timeframe]:
                        demand[timeframe][skill] *= 1.2

        return demand

    def _calculate_capacity_gaps(
        self, current: Dict[str, float], demand: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate capacity gaps."""
        gaps = {}

        for timeframe, timeframe_demand in demand.items():
            gaps[timeframe] = {}
            for skill, required in timeframe_demand.items():
                current_capacity = current.get(skill, 0)
                gap = max(0, required - current_capacity)
                if gap > 0:
                    gaps[timeframe][skill] = gap

        return gaps

    def _generate_capacity_recommendations(
        self, gaps: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """Generate recommendations for capacity planning."""
        recommendations = []

        # Check short-term gaps
        if "short_term" in gaps and gaps["short_term"]:
            total_gap = sum(gaps["short_term"].values())
            recommendations.append(
                f"Immediate action needed: {total_gap:.1f} FTE capacity gap in short term"
            )
            recommendations.append(
                "Consider temporary contractors or overtime for immediate needs"
            )

        # Check medium-term gaps
        if "medium_term" in gaps and gaps["medium_term"]:
            skills_needed = list(gaps["medium_term"].keys())
            recommendations.append(f"Plan hiring for: {', '.join(skills_needed[:3])}")
            recommendations.append("Initiate recruiting process within 4 weeks")

        # General recommendations
        recommendations.append("Implement cross-training to improve flexibility")
        recommendations.append("Consider automation to reduce capacity needs")

        return recommendations

    def _identify_skill_gaps(
        self, goals: List[StrategicGoal], current_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Identify skill gaps based on goals."""
        skill_gaps = {}

        # Get current coverage
        current_coverage = current_state.get("capability_coverage", {})

        # Determine required coverage based on goals
        for skill, coverage in current_coverage.items():
            # High-performing teams need 80% coverage minimum
            required_coverage = 0.8

            # Adjust based on goals
            for goal in goals:
                if "quality" in goal.title.lower() and coverage < 0.9:
                    required_coverage = 0.9
                elif "scale" in goal.title.lower() and coverage < 0.7:
                    required_coverage = 0.7

            gap = max(0, required_coverage - coverage)
            if gap > 0:
                skill_gaps[skill] = gap

        return skill_gaps

    def _create_agent_development_path(
        self, agent_id: str, skill_gaps: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Create development path for an individual agent."""
        path = []

        # Get agent's current capabilities (mock data)
        domain_scores = {"python": 0.8, "testing": 0.6, "debugging": 0.9, "devops": 0.5}

        # Identify skills to develop
        for skill, gap in skill_gaps.items():
            current_score = domain_scores.get(skill, 0)

            if current_score < 0.8 and gap > 0.2:
                path.append(
                    {
                        "skill": skill,
                        "current_level": current_score,
                        "target_level": 0.8,
                        "training_type": "intensive"
                        if current_score < 0.4
                        else "moderate",
                        "duration_weeks": 4 if current_score < 0.4 else 2,
                        "resources": [
                            f"{skill} fundamentals course",
                            f"{skill} hands-on practice",
                            f"{skill} mentorship",
                        ],
                    }
                )

        # Sort by importance
        path.sort(key=lambda p: skill_gaps.get(p["skill"], 0), reverse=True)

        return path[:3]  # Focus on top 3 skills

    def _create_training_calendar(
        self,
        development_paths: Dict[str, List[Dict[str, Any]]],
        skill_gaps: Dict[str, float],
    ) -> Dict[datetime, List[str]]:
        """Create training calendar."""
        calendar = {}

        # Schedule training events
        start_date = datetime.utcnow() + timedelta(weeks=2)

        # Group by skill
        skill_groups = {}
        for agent_id, path in development_paths.items():
            for skill_item in path:
                skill = skill_item["skill"]
                if skill not in skill_groups:
                    skill_groups[skill] = []
                skill_groups[skill].append(agent_id)

        # Schedule group training
        current_date = start_date
        for skill, agents in skill_groups.items():
            if len(agents) >= 2:  # Group training
                calendar[current_date] = [
                    f"Group training: {skill} ({len(agents)} agents)"
                ]
                current_date += timedelta(weeks=1)

        return calendar

    def _calculate_training_investment(
        self,
        development_paths: Dict[str, List[Dict[str, Any]]],
        training_calendar: Dict[datetime, List[str]],
    ) -> Dict[str, float]:
        """Calculate investment required for training."""
        investment = {
            "training_hours": 0,
            "external_training": 0,
            "lost_productivity": 0,
            "materials": 0,
        }

        # Calculate training hours
        for path in development_paths.values():
            for skill_item in path:
                hours = skill_item["duration_weeks"] * 10  # 10 hours per week
                investment["training_hours"] += hours

        # Calculate external training cost
        investment["external_training"] = (
            len(training_calendar) * 2000
        )  # $2k per session

        # Calculate lost productivity (training hours * hourly rate)
        investment["lost_productivity"] = (
            investment["training_hours"] * 100
        )  # $100/hour

        # Materials and resources
        investment["materials"] = len(development_paths) * 500  # $500 per agent

        return investment
