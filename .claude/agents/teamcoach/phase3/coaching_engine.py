from datetime import timedelta
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from ..phase1.performance_analytics import (
    AgentPerformanceAnalyzer,
    AgentPerformanceData,
)
from ..phase1.capability_assessment import CapabilityAssessment, AgentCapabilityProfile
from ..phase2.task_matcher import TaskAgentMatcher

"""
TeamCoach Phase 3: Coaching Engine

Provides intelligent coaching recommendations for agent performance improvement,
skill development guidance, and team optimization strategies.
"""


logger = logging.getLogger(__name__)


class CoachingPriority(Enum):
    """Priority levels for coaching recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class CoachingCategory(Enum):
    """Categories of coaching recommendations."""

    PERFORMANCE = "performance"
    CAPABILITY = "capability"
    COLLABORATION = "collaboration"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    SKILL_DEVELOPMENT = "skill_development"
    WORKLOAD = "workload"
    QUALITY = "quality"


@dataclass
class CoachingRecommendation:
    """Individual coaching recommendation."""

    agent_id: str
    category: CoachingCategory
    priority: CoachingPriority
    title: str
    description: str
    specific_actions: List[str]
    expected_impact: str
    metrics_to_track: List[str]
    resources: List[Dict[str, str]]
    timeframe: str
    created_at: datetime
    evidence: Dict[str, Any]


@dataclass
class TeamCoachingPlan:
    """Comprehensive coaching plan for a team."""

    team_id: str
    recommendations: List[CoachingRecommendation]
    team_goals: List[str]
    success_metrics: Dict[str, float]
    timeline: str
    created_at: datetime
    review_date: datetime


class CoachingEngine:
    """
    Provides intelligent coaching recommendations for agents and teams.

    Features:
    - Performance-based coaching
    - Capability development guidance
    - Collaboration improvement strategies
    - Efficiency optimization recommendations
    - Personalized improvement plans
    """

    def __init__(
        self,
        performance_analyzer: AgentPerformanceAnalyzer,
        capability_assessment: CapabilityAssessment,
        task_matcher: TaskAgentMatcher,
    ):
        """Initialize the coaching engine."""
        self.performance_analyzer = performance_analyzer
        self.capability_assessment = capability_assessment
        self.task_matcher = task_matcher

        # Coaching thresholds
        self.performance_thresholds = {
            "critical": 0.5,  # Below 50% success rate
            "concerning": 0.7,  # Below 70% success rate
            "target": 0.85,  # Target 85% success rate
            "excellent": 0.95,  # Above 95% is excellent
        }

        self.efficiency_thresholds = {
            "slow": 2.0,  # 2x slower than average
            "concerning": 1.5,  # 1.5x slower than average
            "target": 1.0,  # Average speed
            "fast": 0.8,  # 20% faster than average
        }

    def generate_agent_coaching(
        self, agent_id: str, performance_window: Optional[int] = 30
    ) -> List[CoachingRecommendation]:
        """
        Generate coaching recommendations for a specific agent.

        Args:
            agent_id: ID of the agent to coach
            performance_window: Days of performance data to analyze

        Returns:
            List of coaching recommendations
        """
        recommendations = []

        # Get agent performance data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=performance_window or 30)
        performance = self.performance_analyzer.analyze_agent_performance(
            agent_id, (start_time, end_time)
        )

        # Get agent capabilities
        capabilities = self.capability_assessment.assess_agent_capabilities(agent_id)

        # Analyze performance issues
        perf_recommendations = self._analyze_performance_issues(
            agent_id, performance, capabilities
        )
        recommendations.extend(perf_recommendations)

        # Analyze capability gaps
        capability_recommendations = self._analyze_capability_gaps(
            agent_id, capabilities, performance
        )
        recommendations.extend(capability_recommendations)

        # Analyze collaboration patterns
        collab_recommendations = self._analyze_collaboration_patterns(
            agent_id, performance
        )
        recommendations.extend(collab_recommendations)

        # Analyze workload balance
        workload_recommendations = self._analyze_workload_balance(agent_id, performance)
        recommendations.extend(workload_recommendations)

        # Sort by priority
        recommendations.sort(
            key=lambda r: self._get_priority_rank(r.priority), reverse=True
        )

        return recommendations

    def generate_team_coaching_plan(
        self, team_id: str, agent_ids: List[str], objectives: Optional[List[str]] = None
    ) -> TeamCoachingPlan:
        """
        Generate a comprehensive coaching plan for a team.

        Args:
            team_id: ID of the team
            agent_ids: List of agent IDs in the team
            objectives: Optional team objectives to align coaching with

        Returns:
            Comprehensive team coaching plan
        """
        all_recommendations = []

        # Generate individual agent recommendations
        for agent_id in agent_ids:
            agent_recommendations = self.generate_agent_coaching(agent_id)
            all_recommendations.extend(agent_recommendations)

        # Add team-level recommendations
        team_recommendations = self._generate_team_recommendations(
            team_id, agent_ids, objectives
        )
        all_recommendations.extend(team_recommendations)

        # Define team goals based on recommendations and objectives
        team_goals = self._define_team_goals(all_recommendations, objectives)

        # Define success metrics
        success_metrics = self._define_success_metrics(all_recommendations, team_goals)

        # Create timeline
        timeline = self._create_coaching_timeline(all_recommendations)

        # Create the plan
        plan = TeamCoachingPlan(
            team_id=team_id,
            recommendations=all_recommendations,
            team_goals=team_goals,
            success_metrics=success_metrics,
            timeline=timeline,
            created_at=datetime.utcnow(),
            review_date=self._calculate_review_date(timeline),
        )

        return plan

    def _analyze_performance_issues(
        self,
        agent_id: str,
        performance: AgentPerformanceData,
        capabilities: AgentCapabilityProfile,
    ) -> List[CoachingRecommendation]:
        """Analyze performance issues and generate recommendations."""
        recommendations = []

        # Check success rate
        if performance.success_rate < self.performance_thresholds["critical"]:
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.PERFORMANCE,
                priority=CoachingPriority.CRITICAL,
                title="Critical Performance Issues",
                description=f"Success rate ({performance.success_rate:.1%}) is critically low",
                specific_actions=[
                    "Review recent failure patterns",
                    "Identify common failure causes",
                    "Implement targeted error handling improvements",
                    "Consider reducing task complexity temporarily",
                    "Pair with high-performing agents for knowledge transfer",
                ],
                expected_impact="Improve success rate to above 70% within 2 weeks",
                metrics_to_track=["success_rate", "error_patterns", "task_complexity"],
                resources=[
                    {"type": "guide", "name": "Error Pattern Analysis Guide"},
                    {"type": "training", "name": "Advanced Error Handling Techniques"},
                ],
                timeframe="2 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_success_rate": performance.success_rate,
                    "recent_failures": performance.failed_tasks,
                    "failure_types": [],  # Placeholder
                },
            )
            recommendations.append(recommendation)

        elif performance.success_rate < self.performance_thresholds["concerning"]:
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.PERFORMANCE,
                priority=CoachingPriority.HIGH,
                title="Performance Below Target",
                description=f"Success rate ({performance.success_rate:.1%}) needs improvement",
                specific_actions=[
                    "Analyze failure patterns for trends",
                    "Implement additional validation checks",
                    "Enhance error recovery mechanisms",
                    "Focus on high-success task types",
                ],
                expected_impact="Improve success rate to above 85% within 30 days",
                metrics_to_track=["success_rate", "error_recovery_rate"],
                resources=[
                    {"type": "best_practice", "name": "Performance Optimization Guide"}
                ],
                timeframe="30 days",
                created_at=datetime.utcnow(),
                evidence={
                    "current_success_rate": performance.success_rate,
                    "target_rate": self.performance_thresholds["target"],
                },
            )
            recommendations.append(recommendation)

        # Check efficiency
        avg_time = performance.avg_execution_time
        if (
            avg_time and avg_time > self.efficiency_thresholds["slow"] * 60
        ):  # Convert to seconds
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.EFFICIENCY,
                priority=CoachingPriority.HIGH,
                title="Execution Efficiency Concerns",
                description=f"Average execution time ({avg_time:.1f}s) is significantly above target",
                specific_actions=[
                    "Profile task execution for bottlenecks",
                    "Implement caching for repeated operations",
                    "Optimize resource-intensive algorithms",
                    "Consider parallel processing where applicable",
                    "Review and optimize external API calls",
                ],
                expected_impact="Reduce average execution time by 40% within 3 weeks",
                metrics_to_track=["average_execution_time", "p95_execution_time"],
                resources=[
                    {"type": "tool", "name": "Performance Profiler"},
                    {"type": "guide", "name": "Optimization Best Practices"},
                ],
                timeframe="3 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_avg_time": avg_time,
                    "target_time": self.efficiency_thresholds["target"] * 60,
                },
            )
            recommendations.append(recommendation)

        return recommendations

    def _analyze_capability_gaps(
        self,
        agent_id: str,
        capabilities: AgentCapabilityProfile,
        performance: AgentPerformanceData,
    ) -> List[CoachingRecommendation]:
        """Analyze capability gaps and generate development recommendations."""
        recommendations = []

        # Find weak capabilities
        weak_capabilities = [
            (domain, score.proficiency_level.value / 5.0)  # Convert to 0-1 scale
            for domain, score in capabilities.capability_scores.items()
            if score.proficiency_level.value
            < 3  # Below intermediate is considered weak
        ]

        if weak_capabilities:
            for domain, score in weak_capabilities[:3]:  # Top 3 weak areas
                recommendation = CoachingRecommendation(
                    agent_id=agent_id,
                    category=CoachingCategory.SKILL_DEVELOPMENT,
                    priority=CoachingPriority.MEDIUM,
                    title=f"Develop {domain.value.replace('_', ' ').title()} Capabilities",
                    description=f"Current {domain.value} capability score ({score:.1%}) indicates development opportunity",
                    specific_actions=[
                        f"Complete {domain.value} training modules",
                        f"Practice with {domain.value}-focused tasks",
                        f"Shadow experts in {domain.value} tasks",
                        "Request gradual increase in task complexity",
                        "Document learnings and create knowledge base",
                    ],
                    expected_impact=f"Improve {domain.value} capability to 80% within 6 weeks",
                    metrics_to_track=[
                        f"{domain.value}_score",
                        f"{domain.value}_task_success_rate",
                    ],
                    resources=[
                        {
                            "type": "training",
                            "name": f"{domain.value.title()} Fundamentals",
                        },
                        {
                            "type": "mentor",
                            "name": f"{domain.value.title()} Expert Agent",
                        },
                    ],
                    timeframe="6 weeks",
                    created_at=datetime.utcnow(),
                    evidence={
                        "current_score": score,
                        "domain": domain,
                        "related_failures": self._get_domain_failures(
                            performance, domain.value
                        ),
                    },
                )
                recommendations.append(recommendation)

        # Check for unutilized strengths
        strong_capabilities = [
            (domain, score.proficiency_level.value / 5.0)  # Convert to 0-1 scale
            for domain, score in capabilities.capability_scores.items()
            if score.proficiency_level.value
            >= 4  # Advanced or expert is considered strong
        ]

        for domain, score in strong_capabilities:
            utilization = self._calculate_capability_utilization(
                agent_id, domain.value, performance
            )
            if utilization < 0.3:  # Less than 30% utilization
                recommendation = CoachingRecommendation(
                    agent_id=agent_id,
                    category=CoachingCategory.CAPABILITY,
                    priority=CoachingPriority.LOW,
                    title=f"Underutilized {domain.value.replace('_', ' ').title()} Strength",
                    description=f"Strong {domain} capability ({score:.1%}) is underutilized ({utilization:.1%})",
                    specific_actions=[
                        f"Increase assignment of {domain} tasks",
                        f"Mentor other agents in {domain}",
                        f"Lead {domain} initiatives",
                        "Document best practices for team",
                    ],
                    expected_impact=f"Increase {domain} utilization to 60% for better ROI",
                    metrics_to_track=[f"{domain}_utilization", f"{domain}_impact"],
                    resources=[
                        {"type": "opportunity", "name": f"Available {domain} Projects"}
                    ],
                    timeframe="2 weeks",
                    created_at=datetime.utcnow(),
                    evidence={
                        "capability_score": score,
                        "current_utilization": utilization,
                    },
                )
                recommendations.append(recommendation)

        return recommendations

    def _analyze_collaboration_patterns(
        self, agent_id: str, performance: AgentPerformanceData
    ) -> List[CoachingRecommendation]:
        """Analyze collaboration patterns and generate recommendations."""
        recommendations = []

        # Check collaboration metrics
        collab_score = performance.collaboration_success_rate

        if collab_score < 0.6:
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.COLLABORATION,
                priority=CoachingPriority.MEDIUM,
                title="Improve Collaboration Effectiveness",
                description=f"Collaboration score ({collab_score:.1%}) indicates room for improvement",
                specific_actions=[
                    "Increase communication frequency with team members",
                    "Provide more detailed status updates",
                    "Actively participate in knowledge sharing",
                    "Respond promptly to collaboration requests",
                    "Document and share learnings proactively",
                ],
                expected_impact="Improve collaboration score to 80% within 4 weeks",
                metrics_to_track=[
                    "collaboration_score",
                    "response_time",
                    "knowledge_contributions",
                ],
                resources=[
                    {"type": "guide", "name": "Effective Team Collaboration"},
                    {"type": "tool", "name": "Communication Templates"},
                ],
                timeframe="4 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_score": collab_score,
                    "interaction_frequency": performance.collaboration_frequency,
                },
            )
            recommendations.append(recommendation)

        return recommendations

    def _analyze_workload_balance(
        self, agent_id: str, performance: AgentPerformanceData
    ) -> List[CoachingRecommendation]:
        """Analyze workload balance and generate recommendations."""
        recommendations = []

        # Check workload metrics
        workload = min(
            1.0, performance.total_tasks / 10.0
        )  # Normalize workload based on task count
        task_variety = 0.5  # Placeholder - would need task type diversity calculation

        if workload > 0.85:  # Overloaded
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.WORKLOAD,
                priority=CoachingPriority.HIGH,
                title="Workload Optimization Needed",
                description=f"Current workload ({workload:.1%}) is unsustainably high",
                specific_actions=[
                    "Delegate or redistribute lower-priority tasks",
                    "Automate repetitive operations",
                    "Improve task estimation accuracy",
                    "Request workload rebalancing from team",
                    "Identify and eliminate inefficiencies",
                ],
                expected_impact="Reduce workload to sustainable 70% within 1 week",
                metrics_to_track=[
                    "workload_score",
                    "burnout_risk",
                    "task_completion_rate",
                ],
                resources=[
                    {"type": "tool", "name": "Task Automation Framework"},
                    {"type": "support", "name": "Workload Management Team"},
                ],
                timeframe="1 week",
                created_at=datetime.utcnow(),
                evidence={
                    "current_workload": workload,
                    "task_count": performance.total_tasks,
                    "overtime_hours": 0,  # Placeholder
                },
            )
            recommendations.append(recommendation)

        elif workload < 0.3:  # Underutilized
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.WORKLOAD,
                priority=CoachingPriority.LOW,
                title="Increase Capacity Utilization",
                description=f"Current workload ({workload:.1%}) indicates available capacity",
                specific_actions=[
                    "Volunteer for additional projects",
                    "Expand skill set to handle more task types",
                    "Mentor other agents",
                    "Take on stretch assignments",
                    "Contribute to process improvements",
                ],
                expected_impact="Increase utilization to optimal 60-70% range",
                metrics_to_track=[
                    "workload_score",
                    "value_contribution",
                    "skill_growth",
                ],
                resources=[
                    {"type": "opportunity", "name": "Available Projects List"},
                    {"type": "development", "name": "Skill Expansion Programs"},
                ],
                timeframe="2 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_workload": workload,
                    "available_capacity": 1.0 - workload,
                },
            )
            recommendations.append(recommendation)

        # Check task variety
        if task_variety < 0.3:
            recommendation = CoachingRecommendation(
                agent_id=agent_id,
                category=CoachingCategory.SKILL_DEVELOPMENT,
                priority=CoachingPriority.LOW,
                title="Diversify Task Portfolio",
                description="Limited task variety may hinder skill development",
                specific_actions=[
                    "Request exposure to different task types",
                    "Cross-train in adjacent skill areas",
                    "Participate in rotation programs",
                    "Shadow agents with diverse portfolios",
                ],
                expected_impact="Increase task variety score to 60% for better growth",
                metrics_to_track=[
                    "task_variety_score",
                    "skill_breadth",
                    "adaptability",
                ],
                resources=[{"type": "program", "name": "Task Rotation Initiative"}],
                timeframe="4 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_variety": task_variety,
                    "task_types": 1,  # Placeholder
                },
            )
            recommendations.append(recommendation)

        return recommendations

    def _generate_team_recommendations(
        self, team_id: str, agent_ids: List[str], objectives: Optional[List[str]]
    ) -> List[CoachingRecommendation]:
        """Generate team-level coaching recommendations."""
        recommendations = []

        # Analyze team composition balance
        team_capabilities = self._analyze_team_capability_balance(agent_ids)

        if team_capabilities["gaps"]:
            recommendation = CoachingRecommendation(
                agent_id=f"team_{team_id}",
                category=CoachingCategory.CAPABILITY,
                priority=CoachingPriority.HIGH,
                title="Address Team Capability Gaps",
                description=f"Team lacks sufficient expertise in: {', '.join(team_capabilities['gaps'])}",
                specific_actions=[
                    "Recruit or train agents in gap areas",
                    "Create cross-training programs",
                    "Establish partnerships with expert teams",
                    "Prioritize skill development in gap areas",
                ],
                expected_impact="Achieve balanced team capabilities within 8 weeks",
                metrics_to_track=["team_capability_coverage", "gap_closure_rate"],
                resources=[
                    {"type": "analysis", "name": "Detailed Capability Gap Report"}
                ],
                timeframe="8 weeks",
                created_at=datetime.utcnow(),
                evidence=team_capabilities,
            )
            recommendations.append(recommendation)

        # Analyze team collaboration
        collab_score = self._calculate_team_collaboration_score(agent_ids)

        if collab_score < 0.7:
            recommendation = CoachingRecommendation(
                agent_id=f"team_{team_id}",
                category=CoachingCategory.COLLABORATION,
                priority=CoachingPriority.MEDIUM,
                title="Enhance Team Collaboration",
                description=f"Team collaboration score ({collab_score:.1%}) needs improvement",
                specific_actions=[
                    "Implement regular team sync meetings",
                    "Create shared knowledge repositories",
                    "Establish clear communication protocols",
                    "Foster psychological safety",
                    "Celebrate collaborative successes",
                ],
                expected_impact="Improve team collaboration to 85% within 6 weeks",
                metrics_to_track=[
                    "team_collaboration_score",
                    "knowledge_sharing_frequency",
                ],
                resources=[
                    {"type": "workshop", "name": "Team Building Workshop"},
                    {"type": "tool", "name": "Collaboration Platform"},
                ],
                timeframe="6 weeks",
                created_at=datetime.utcnow(),
                evidence={
                    "current_score": collab_score,
                    "communication_gaps": self._identify_communication_gaps(agent_ids),
                },
            )
            recommendations.append(recommendation)

        return recommendations

    def _define_team_goals(
        self,
        recommendations: List[CoachingRecommendation],
        objectives: Optional[List[str]],
    ) -> List[str]:
        """Define team goals based on recommendations and objectives."""
        goals = []

        # Add objective-based goals
        if objectives:
            goals.extend(objectives)

        # Add recommendation-based goals
        critical_recs = [
            r for r in recommendations if r.priority == CoachingPriority.CRITICAL
        ]
        high_recs = [r for r in recommendations if r.priority == CoachingPriority.HIGH]

        if critical_recs:
            goals.append("Address all critical performance issues within 2 weeks")

        if high_recs:
            goals.append("Resolve high-priority improvement areas within 30 days")

        # Add standard goals
        goals.extend(
            [
                "Achieve 85% average team success rate",
                "Maintain balanced workload distribution",
                "Foster continuous learning culture",
                "Improve team collaboration score to 80%+",
            ]
        )

        return list(set(goals))  # Remove duplicates

    def _define_success_metrics(
        self, recommendations: List[CoachingRecommendation], goals: List[str]
    ) -> Dict[str, float]:
        """Define success metrics for the coaching plan."""
        metrics = {
            "team_success_rate": 0.85,
            "average_execution_time": 60.0,  # seconds
            "collaboration_score": 0.80,
            "capability_coverage": 0.90,
            "workload_balance": 0.70,
            "skill_growth_rate": 0.15,  # 15% improvement
            "recommendation_completion": 0.80,  # 80% of recommendations implemented
        }

        # Adjust based on critical recommendations
        critical_count = len(
            [r for r in recommendations if r.priority == CoachingPriority.CRITICAL]
        )
        if critical_count > 0:
            metrics["critical_issue_resolution"] = 1.0  # 100% resolution required

        return metrics

    def _create_coaching_timeline(
        self, recommendations: List[CoachingRecommendation]
    ) -> str:
        """Create a timeline for implementing coaching recommendations."""
        # Group by timeframe
        timeframes = {}
        for rec in recommendations:
            if rec.timeframe not in timeframes:
                timeframes[rec.timeframe] = []
            timeframes[rec.timeframe].append(rec)

        # Sort timeframes
        sorted_timeframes = sorted(timeframes.keys(), key=self._parse_timeframe)

        timeline_parts = []
        for tf in sorted_timeframes:
            count = len(timeframes[tf])
            priority_breakdown = self._get_priority_breakdown(timeframes[tf])
            timeline_parts.append(
                f"{tf}: {count} recommendations ({priority_breakdown})"
            )

        return " → ".join(timeline_parts)

    def _calculate_review_date(self, timeline: str) -> datetime:
        """Calculate when the coaching plan should be reviewed."""
        # Extract the longest timeframe from timeline
        timeframes = timeline.split(" → ")
        if timeframes:
            last_timeframe = timeframes[-1].split(":")[0]
            days = self._parse_timeframe_to_days(last_timeframe)
            return datetime.utcnow() + timedelta(days=days)

        # Default to 30 days
        return datetime.utcnow() + timedelta(days=30)

    def _get_priority_rank(self, priority: CoachingPriority) -> int:
        """Get numeric rank for priority sorting."""
        ranks = {
            CoachingPriority.CRITICAL: 5,
            CoachingPriority.HIGH: 4,
            CoachingPriority.MEDIUM: 3,
            CoachingPriority.LOW: 2,
            CoachingPriority.INFORMATIONAL: 1,
        }
        return ranks.get(priority, 0)

    def _get_domain_failures(
        self, performance: AgentPerformanceData, domain: str
    ) -> int:
        """Get failure count related to a specific domain."""
        # This would analyze error patterns related to the domain
        return performance.failed_tasks  # Simplified - return total failures

    def _calculate_capability_utilization(
        self, agent_id: str, domain: str, performance: AgentPerformanceData
    ) -> float:
        """Calculate how much a capability is being utilized."""
        total_tasks = performance.total_tasks
        domain_tasks = total_tasks // 5  # Simplified estimation

        if total_tasks == 0:
            return 0.0

        return domain_tasks / total_tasks

    def _analyze_team_capability_balance(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze team capability balance and identify gaps."""
        all_domains = set()
        domain_coverage = {}

        for agent_id in agent_ids:
            capabilities = self.capability_assessment.assess_agent_capabilities(
                agent_id
            )
            for domain, score in capabilities.capability_scores.items():
                all_domains.add(domain)
                if domain not in domain_coverage:
                    domain_coverage[domain] = []
                if score.proficiency_level.value >= 4:  # Advanced or expert level
                    domain_coverage[domain].append(agent_id)

        # Identify gaps
        gaps = [
            domain for domain in all_domains if len(domain_coverage.get(domain, [])) < 2
        ]

        return {
            "total_domains": len(all_domains),
            "covered_domains": len(
                [d for d in domain_coverage if len(domain_coverage[d]) >= 2]
            ),
            "gaps": gaps,
            "coverage_details": domain_coverage,
        }

    def _calculate_team_collaboration_score(self, agent_ids: List[str]) -> float:
        """Calculate overall team collaboration score."""
        scores = []
        for agent_id in agent_ids:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            performance = self.performance_analyzer.analyze_agent_performance(
                agent_id, (start_time, end_time)
            )
            collab_score = performance.collaboration_success_rate
            scores.append(collab_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _identify_communication_gaps(self, agent_ids: List[str]) -> List[str]:
        """Identify communication gaps in the team."""

        # This would analyze actual communication patterns
        # For now, return example gaps
        return ["Infrequent status updates", "Limited knowledge sharing"]

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to days for sorting."""
        return self._parse_timeframe_to_days(timeframe)

    def _parse_timeframe_to_days(self, timeframe: str) -> int:
        """Convert timeframe string to days."""
        timeframe_lower = timeframe.lower()
        if "week" in timeframe_lower:
            weeks = int("".join(filter(str.isdigit, timeframe_lower)) or 1)
            return weeks * 7
        elif "day" in timeframe_lower:
            return int("".join(filter(str.isdigit, timeframe_lower)) or 1)
        elif "month" in timeframe_lower:
            months = int("".join(filter(str.isdigit, timeframe_lower)) or 1)
            return months * 30
        return 30  # Default

    def _get_priority_breakdown(
        self, recommendations: List[CoachingRecommendation]
    ) -> str:
        """Get priority breakdown string."""
        counts = {}
        for rec in recommendations:
            priority = rec.priority.value
            counts[priority] = counts.get(priority, 0) + 1

        parts = []
        for priority in ["critical", "high", "medium", "low"]:
            if priority in counts:
                parts.append(f"{counts[priority]} {priority}")

        return ", ".join(parts)


# Import timedelta for date calculations
