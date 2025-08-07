#!/usr/bin/env python3
"""
Team Coach Engine for Gadugi v0.3

Provides intelligent reflection, continuous learning, and performance optimization
for multi-agent development workflows.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""

    agent: str
    action: str
    duration_seconds: float
    success: bool
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class ResourceUsage:
    """Resource usage metrics for a workflow"""

    peak_memory_mb: float
    cpu_time_seconds: float
    disk_io_mb: float
    network_io_mb: float = 0.0


@dataclass
class WorkflowOutcomes:
    """Outcomes and results of a workflow"""

    files_created: int
    tests_written: int
    lines_of_code: int
    success_rate: float
    user_satisfaction: str  # high, medium, low
    errors_encountered: int = 0
    warnings_generated: int = 0


@dataclass
class WorkflowData:
    """Complete workflow execution data"""

    workflow_id: str
    agents_used: List[str]
    task_sequence: List[WorkflowStep]
    resource_usage: ResourceUsage
    outcomes: WorkflowOutcomes
    start_time: datetime
    end_time: datetime
    project_context: str


@dataclass
class Pattern:
    """Identified workflow pattern"""

    pattern_type: str  # success, failure, optimization, bottleneck
    description: str
    frequency: float  # 0.0 to 1.0
    impact: str  # low, medium, high
    confidence: float  # 0.0 to 1.0
    supporting_evidence: List[str]


@dataclass
class Recommendation:
    """Optimization recommendation"""

    type: str  # workflow_optimization, agent_coordination, resource_management
    priority: str  # high, medium, low
    description: str
    expected_improvement: str
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    estimated_impact: Dict[str, float]


@dataclass
class LearningInsight:
    """Learning insight from workflow analysis"""

    insight_type: str  # best_practice, anti_pattern, optimization_opportunity
    description: str
    confidence: float
    supporting_evidence: List[str]
    applicable_contexts: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics for workflows"""

    efficiency_score: float  # 0.0 to 10.0
    speed_score: float
    quality_score: float
    resource_efficiency_score: float
    coordination_score: float
    overall_score: float


@dataclass
class TeamCoachRequest:
    """Request format for team coach analysis"""

    analysis_type: str  # performance, learning, optimization, reflection
    workflow_data: WorkflowData
    historical_context: Dict[str, Any]
    reflection_scope: str  # session, project, system


@dataclass
class TeamCoachResponse:
    """Response format for team coach analysis"""

    success: bool
    analysis_results: Dict[str, Any]
    recommendations: List[Recommendation]
    learning_insights: List[LearningInsight]
    performance_trends: Dict[str, Any]
    patterns_identified: List[Pattern]
    errors: List[str]


class PerformanceAnalyzer:
    """Analyzes workflow performance and identifies optimization opportunities"""

    def __init__(self):
        self.metrics_weights = {
            "speed": 0.25,
            "quality": 0.30,
            "resource_efficiency": 0.25,
            "coordination": 0.20,
        }

    def analyze_workflow_performance(
        self, workflow_data: WorkflowData
    ) -> PerformanceMetrics:
        """Analyze the performance of a workflow"""

        # Calculate individual scores
        speed_score = self._calculate_speed_score(workflow_data)
        quality_score = self._calculate_quality_score(workflow_data)
        resource_score = self._calculate_resource_efficiency_score(workflow_data)
        coordination_score = self._calculate_coordination_score(workflow_data)

        # Calculate overall efficiency score
        overall_score = (
            speed_score * self.metrics_weights["speed"]
            + quality_score * self.metrics_weights["quality"]
            + resource_score * self.metrics_weights["resource_efficiency"]
            + coordination_score * self.metrics_weights["coordination"]
        )

        return PerformanceMetrics(
            efficiency_score=overall_score,
            speed_score=speed_score,
            quality_score=quality_score,
            resource_efficiency_score=resource_score,
            coordination_score=coordination_score,
            overall_score=overall_score,
        )

    def _calculate_speed_score(self, workflow_data: WorkflowData) -> float:
        """Calculate workflow speed score (0-10)"""
        total_duration = (
            workflow_data.end_time - workflow_data.start_time
        ).total_seconds()

        # Baseline expectations (in seconds)
        expected_duration_per_agent = 30  # seconds
        expected_total = len(workflow_data.agents_used) * expected_duration_per_agent

        # Calculate efficiency ratio
        if total_duration <= expected_total * 0.5:
            return 10.0  # Exceptional speed
        elif total_duration <= expected_total:
            return 8.0  # Good speed
        elif total_duration <= expected_total * 1.5:
            return 6.0  # Acceptable speed
        elif total_duration <= expected_total * 2.0:
            return 4.0  # Slow
        else:
            return 2.0  # Very slow

    def _calculate_quality_score(self, workflow_data: WorkflowData) -> float:
        """Calculate workflow quality score (0-10)"""
        outcomes = workflow_data.outcomes

        # Base score from success rate
        base_score = outcomes.success_rate * 10.0

        # Adjust for user satisfaction
        satisfaction_multiplier = {"high": 1.0, "medium": 0.85, "low": 0.6}.get(
            outcomes.user_satisfaction, 0.8
        )

        # Penalize for errors and warnings
        error_penalty = min(outcomes.errors_encountered * 0.5, 2.0)
        warning_penalty = min(outcomes.warnings_generated * 0.1, 1.0)

        # Bonus for comprehensive testing
        test_bonus = (
            min(outcomes.tests_written * 0.1, 2.0) if outcomes.tests_written > 0 else 0
        )

        quality_score = (
            (base_score * satisfaction_multiplier)
            - error_penalty
            - warning_penalty
            + test_bonus
        )

        return max(0.0, min(10.0, quality_score))

    def _calculate_resource_efficiency_score(
        self, workflow_data: WorkflowData
    ) -> float:
        """Calculate resource efficiency score (0-10)"""
        resource_usage = workflow_data.resource_usage

        # Expected resource usage baselines
        expected_memory = 256  # MB
        expected_cpu = 60  # seconds
        expected_disk = 10  # MB

        # Calculate efficiency ratios
        memory_ratio = expected_memory / max(resource_usage.peak_memory_mb, 1)
        cpu_ratio = expected_cpu / max(resource_usage.cpu_time_seconds, 1)
        disk_ratio = expected_disk / max(resource_usage.disk_io_mb, 1)

        # Average the ratios and scale to 0-10
        avg_efficiency = (memory_ratio + cpu_ratio + disk_ratio) / 3

        # Convert to score (closer to 1.0 is better)
        if avg_efficiency >= 1.0:
            return 10.0
        elif avg_efficiency >= 0.8:
            return 8.0 + (avg_efficiency - 0.8) * 10
        elif avg_efficiency >= 0.6:
            return 6.0 + (avg_efficiency - 0.6) * 10
        else:
            return max(2.0, avg_efficiency * 10)

    def _calculate_coordination_score(self, workflow_data: WorkflowData) -> float:
        """Calculate agent coordination score (0-10)"""
        if len(workflow_data.task_sequence) <= 1:
            return 10.0  # Single step workflows are perfectly coordinated

        # Analyze handoff efficiency
        handoff_delays = []
        successful_handoffs = 0

        for i in range(1, len(workflow_data.task_sequence)):
            prev_step = workflow_data.task_sequence[i - 1]
            curr_step = workflow_data.task_sequence[i]

            # Calculate handoff delay
            if hasattr(curr_step, "timestamp") and hasattr(prev_step, "timestamp"):
                delay = (curr_step.timestamp - prev_step.timestamp).total_seconds()
                handoff_delays.append(delay)

                # Consider handoff successful if both steps succeeded
                if prev_step.success and curr_step.success:
                    successful_handoffs += 1

        # Calculate average handoff delay
        avg_delay = statistics.mean(handoff_delays) if handoff_delays else 0

        # Calculate success rate for handoffs
        handoff_success_rate = successful_handoffs / max(len(handoff_delays), 1)

        # Score based on delay and success rate
        delay_score = 10.0 if avg_delay <= 5 else max(5.0, 10 - (avg_delay - 5) * 0.2)
        success_score = handoff_success_rate * 10

        return (delay_score + success_score) / 2


class PatternRecognizer:
    """Recognizes patterns in workflow execution and outcomes"""

    def __init__(self):
        self.pattern_thresholds = {
            "frequency_threshold": 0.3,  # Minimum frequency to consider a pattern
            "confidence_threshold": 0.7,  # Minimum confidence for pattern recognition
        }

    def identify_patterns(self, workflows: List[WorkflowData]) -> List[Pattern]:
        """Identify patterns across multiple workflows"""
        patterns = []

        if not workflows:
            return patterns

        # Identify success patterns
        patterns.extend(self._identify_success_patterns(workflows))

        # Identify failure patterns
        patterns.extend(self._identify_failure_patterns(workflows))

        # Identify optimization opportunities
        patterns.extend(self._identify_optimization_patterns(workflows))

        # Identify bottleneck patterns
        patterns.extend(self._identify_bottleneck_patterns(workflows))

        return patterns

    def _identify_success_patterns(
        self, workflows: List[WorkflowData]
    ) -> List[Pattern]:
        """Identify patterns that lead to successful outcomes"""
        patterns = []
        successful_workflows = [w for w in workflows if w.outcomes.success_rate >= 0.8]

        if len(successful_workflows) < 2:
            return patterns

        # Analyze agent combinations
        agent_combos = {}
        for workflow in successful_workflows:
            combo = tuple(sorted(workflow.agents_used))
            agent_combos[combo] = agent_combos.get(combo, 0) + 1

        total_successful = len(successful_workflows)
        for combo, count in agent_combos.items():
            frequency = count / total_successful
            if frequency >= self.pattern_thresholds["frequency_threshold"]:
                patterns.append(
                    Pattern(
                        pattern_type="success",
                        description=f"Agent combination: {', '.join(combo)}",
                        frequency=frequency,
                        impact="high" if frequency > 0.7 else "medium",
                        confidence=min(frequency * 1.2, 1.0),
                        supporting_evidence=[
                            w.workflow_id
                            for w in successful_workflows
                            if tuple(sorted(w.agents_used)) == combo
                        ],
                    )
                )

        # Analyze task sequence patterns
        sequence_patterns = self._analyze_sequence_patterns(
            successful_workflows, "success"
        )
        patterns.extend(sequence_patterns)

        return patterns

    def _identify_failure_patterns(
        self, workflows: List[WorkflowData]
    ) -> List[Pattern]:
        """Identify patterns that lead to failures"""
        patterns = []
        failed_workflows = [w for w in workflows if w.outcomes.success_rate < 0.5]

        if len(failed_workflows) < 2:
            return patterns

        # Analyze common failure points
        failure_agents = {}
        for workflow in failed_workflows:
            for step in workflow.task_sequence:
                if not step.success:
                    failure_agents[step.agent] = failure_agents.get(step.agent, 0) + 1

        total_failed = len(failed_workflows)
        for agent, count in failure_agents.items():
            frequency = count / total_failed
            if frequency >= self.pattern_thresholds["frequency_threshold"]:
                patterns.append(
                    Pattern(
                        pattern_type="failure",
                        description=f"Frequent failures in {agent} agent",
                        frequency=frequency,
                        impact="high",
                        confidence=frequency,
                        supporting_evidence=[w.workflow_id for w in failed_workflows],
                    )
                )

        return patterns

    def _identify_optimization_patterns(
        self, workflows: List[WorkflowData]
    ) -> List[Pattern]:
        """Identify optimization opportunities"""
        patterns = []

        # Look for resource inefficiencies
        high_resource_workflows = []
        for workflow in workflows:
            if (
                workflow.resource_usage.peak_memory_mb > 512
                or workflow.resource_usage.cpu_time_seconds > 120
            ):
                high_resource_workflows.append(workflow)

        if len(high_resource_workflows) >= 2:
            frequency = len(high_resource_workflows) / len(workflows)
            patterns.append(
                Pattern(
                    pattern_type="optimization",
                    description="High resource usage detected",
                    frequency=frequency,
                    impact="medium",
                    confidence=frequency,
                    supporting_evidence=[
                        w.workflow_id for w in high_resource_workflows
                    ],
                )
            )

        # Look for slow workflows
        slow_workflows = []
        for workflow in workflows:
            duration = (workflow.end_time - workflow.start_time).total_seconds()
            if duration > 180:  # More than 3 minutes
                slow_workflows.append(workflow)

        if len(slow_workflows) >= 2:
            frequency = len(slow_workflows) / len(workflows)
            patterns.append(
                Pattern(
                    pattern_type="optimization",
                    description="Slow workflow execution detected",
                    frequency=frequency,
                    impact="high" if frequency > 0.5 else "medium",
                    confidence=frequency,
                    supporting_evidence=[w.workflow_id for w in slow_workflows],
                )
            )

        return patterns

    def _identify_bottleneck_patterns(
        self, workflows: List[WorkflowData]
    ) -> List[Pattern]:
        """Identify bottleneck patterns in workflows"""
        patterns = []

        # Analyze step durations to find bottlenecks
        agent_durations = {}
        for workflow in workflows:
            for step in workflow.task_sequence:
                if step.agent not in agent_durations:
                    agent_durations[step.agent] = []
                agent_durations[step.agent].append(step.duration_seconds)

        # Find agents with consistently high durations
        for agent, durations in agent_durations.items():
            if len(durations) >= 3:
                avg_duration = statistics.mean(durations)
                if avg_duration > 60:  # More than 1 minute average
                    patterns.append(
                        Pattern(
                            pattern_type="bottleneck",
                            description=f"{agent} agent showing slow performance",
                            frequency=1.0,  # Always present when this agent is used
                            impact="high" if avg_duration > 120 else "medium",
                            confidence=0.8,
                            supporting_evidence=[
                                w.workflow_id
                                for w in workflows
                                if any(s.agent == agent for s in w.task_sequence)
                            ],
                        )
                    )

        return patterns

    def _analyze_sequence_patterns(
        self, workflows: List[WorkflowData], pattern_type: str
    ) -> List[Pattern]:
        """Analyze task sequence patterns"""
        patterns = []

        # Look for common sequences
        sequences = []
        for workflow in workflows:
            if len(workflow.task_sequence) >= 2:
                for i in range(len(workflow.task_sequence) - 1):
                    seq = (
                        workflow.task_sequence[i].agent,
                        workflow.task_sequence[i + 1].agent,
                    )
                    sequences.append(seq)

        # Count sequence frequencies
        sequence_counts = {}
        for seq in sequences:
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

        total_sequences = len(sequences)
        for seq, count in sequence_counts.items():
            frequency = count / total_sequences
            if frequency >= self.pattern_thresholds["frequency_threshold"]:
                patterns.append(
                    Pattern(
                        pattern_type=pattern_type,
                        description=f"Common sequence: {seq[0]} → {seq[1]}",
                        frequency=frequency,
                        impact="medium",
                        confidence=frequency,
                        supporting_evidence=[],
                    )
                )

        return patterns


class LearningEngine:
    """Extracts learning insights from workflow analysis"""

    def __init__(self):
        self.insight_confidence_threshold = 0.6

    def extract_learning_insights(
        self, workflows: List[WorkflowData], patterns: List[Pattern]
    ) -> List[LearningInsight]:
        """Extract actionable learning insights from workflow analysis"""
        insights = []

        # Extract best practices from success patterns
        success_patterns = [p for p in patterns if p.pattern_type == "success"]
        for pattern in success_patterns:
            if pattern.confidence >= self.insight_confidence_threshold:
                insight = LearningInsight(
                    insight_type="best_practice",
                    description=f"Best practice identified: {pattern.description}",
                    confidence=pattern.confidence,
                    supporting_evidence=pattern.supporting_evidence,
                    applicable_contexts=["multi_agent_workflows"],
                )
                insights.append(insight)

        # Extract anti-patterns from failure patterns
        failure_patterns = [p for p in patterns if p.pattern_type == "failure"]
        for pattern in failure_patterns:
            if pattern.confidence >= self.insight_confidence_threshold:
                insight = LearningInsight(
                    insight_type="anti_pattern",
                    description=f"Anti-pattern identified: {pattern.description}",
                    confidence=pattern.confidence,
                    supporting_evidence=pattern.supporting_evidence,
                    applicable_contexts=["workflow_planning"],
                )
                insights.append(insight)

        # Extract optimization opportunities
        optimization_patterns = [
            p for p in patterns if p.pattern_type == "optimization"
        ]
        for pattern in optimization_patterns:
            insight = LearningInsight(
                insight_type="optimization_opportunity",
                description=f"Optimization opportunity: {pattern.description}",
                confidence=pattern.confidence,
                supporting_evidence=pattern.supporting_evidence,
                applicable_contexts=["performance_optimization"],
            )
            insights.append(insight)

        # Analyze resource usage trends
        resource_insights = self._extract_resource_insights(workflows)
        insights.extend(resource_insights)

        # Analyze coordination insights
        coordination_insights = self._extract_coordination_insights(workflows)
        insights.extend(coordination_insights)

        return insights

    def _extract_resource_insights(
        self, workflows: List[WorkflowData]
    ) -> List[LearningInsight]:
        """Extract insights about resource usage patterns"""
        insights = []

        if not workflows:
            return insights

        # Analyze memory usage trends
        memory_usages = [w.resource_usage.peak_memory_mb for w in workflows]
        avg_memory = statistics.mean(memory_usages)

        if avg_memory > 512:  # High memory usage
            insight = LearningInsight(
                insight_type="optimization_opportunity",
                description="High memory usage detected across workflows",
                confidence=0.8,
                supporting_evidence=[
                    w.workflow_id
                    for w in workflows
                    if w.resource_usage.peak_memory_mb > 512
                ],
                applicable_contexts=["resource_optimization"],
            )
            insights.append(insight)

        # Analyze CPU usage trends
        cpu_usages = [w.resource_usage.cpu_time_seconds for w in workflows]
        avg_cpu = statistics.mean(cpu_usages)

        if avg_cpu > 90:  # High CPU usage
            insight = LearningInsight(
                insight_type="optimization_opportunity",
                description="High CPU usage detected across workflows",
                confidence=0.7,
                supporting_evidence=[
                    w.workflow_id
                    for w in workflows
                    if w.resource_usage.cpu_time_seconds > 90
                ],
                applicable_contexts=["performance_optimization"],
            )
            insights.append(insight)

        return insights

    def _extract_coordination_insights(
        self, workflows: List[WorkflowData]
    ) -> List[LearningInsight]:
        """Extract insights about agent coordination"""
        insights = []

        # Analyze workflows with multiple agents
        multi_agent_workflows = [w for w in workflows if len(w.agents_used) > 1]

        if not multi_agent_workflows:
            return insights

        # Look for coordination success patterns
        successful_coordination = [
            w for w in multi_agent_workflows if w.outcomes.success_rate >= 0.8
        ]

        if len(successful_coordination) / len(multi_agent_workflows) > 0.7:
            insight = LearningInsight(
                insight_type="best_practice",
                description="Multi-agent coordination is generally successful",
                confidence=0.8,
                supporting_evidence=[w.workflow_id for w in successful_coordination],
                applicable_contexts=["agent_coordination"],
            )
            insights.append(insight)

        return insights


class RecommendationEngine:
    """Generates optimization recommendations based on analysis"""

    def __init__(self):
        self.recommendation_thresholds = {
            "high_priority": 0.8,
            "medium_priority": 0.5,
            "low_priority": 0.3,
        }

    def generate_recommendations(
        self,
        performance_metrics: PerformanceMetrics,
        patterns: List[Pattern],
        insights: List[LearningInsight],
    ) -> List[Recommendation]:
        """Generate optimization recommendations"""
        recommendations = []

        # Performance-based recommendations
        recommendations.extend(
            self._generate_performance_recommendations(performance_metrics)
        )

        # Pattern-based recommendations
        recommendations.extend(self._generate_pattern_recommendations(patterns))

        # Insight-based recommendations
        recommendations.extend(self._generate_insight_recommendations(insights))

        # Sort by priority and expected impact
        recommendations.sort(
            key=lambda r: (
                {"high": 3, "medium": 2, "low": 1}[r.priority],
                sum(r.estimated_impact.values()) if r.estimated_impact else 0,
            ),
            reverse=True,
        )

        return recommendations

    def _generate_performance_recommendations(
        self, metrics: PerformanceMetrics
    ) -> List[Recommendation]:
        """Generate recommendations based on performance metrics"""
        recommendations = []

        # Speed recommendations
        if metrics.speed_score < 6.0:
            recommendations.append(
                Recommendation(
                    type="workflow_optimization",
                    priority="high" if metrics.speed_score < 4.0 else "medium",
                    description="Optimize workflow execution speed",
                    expected_improvement=f"{(10 - metrics.speed_score) * 10:.0f}% faster execution",
                    implementation_effort="medium",
                    risk_level="low",
                    estimated_impact={"speed": 10 - metrics.speed_score},
                )
            )

        # Quality recommendations
        if metrics.quality_score < 7.0:
            recommendations.append(
                Recommendation(
                    type="workflow_optimization",
                    priority="high",
                    description="Improve workflow output quality",
                    expected_improvement=f"{(10 - metrics.quality_score) * 5:.0f}% quality improvement",
                    implementation_effort="low",
                    risk_level="low",
                    estimated_impact={"quality": 10 - metrics.quality_score},
                )
            )

        # Resource efficiency recommendations
        if metrics.resource_efficiency_score < 6.0:
            recommendations.append(
                Recommendation(
                    type="resource_management",
                    priority="medium",
                    description="Optimize resource usage",
                    expected_improvement=f"{(10 - metrics.resource_efficiency_score) * 8:.0f}% resource savings",
                    implementation_effort="medium",
                    risk_level="low",
                    estimated_impact={
                        "resource_efficiency": 10 - metrics.resource_efficiency_score
                    },
                )
            )

        # Coordination recommendations
        if metrics.coordination_score < 7.0:
            recommendations.append(
                Recommendation(
                    type="agent_coordination",
                    priority="high" if metrics.coordination_score < 5.0 else "medium",
                    description="Improve agent coordination",
                    expected_improvement=f"{(10 - metrics.coordination_score) * 7:.0f}% better coordination",
                    implementation_effort="high",
                    risk_level="medium",
                    estimated_impact={"coordination": 10 - metrics.coordination_score},
                )
            )

        return recommendations

    def _generate_pattern_recommendations(
        self, patterns: List[Pattern]
    ) -> List[Recommendation]:
        """Generate recommendations based on identified patterns"""
        recommendations = []

        for pattern in patterns:
            if pattern.pattern_type == "bottleneck" and pattern.impact == "high":
                recommendations.append(
                    Recommendation(
                        type="workflow_optimization",
                        priority="high",
                        description=f"Address bottleneck: {pattern.description}",
                        expected_improvement="20-30% speed improvement",
                        implementation_effort="medium",
                        risk_level="low",
                        estimated_impact={"speed": 2.5, "efficiency": 2.0},
                    )
                )

            elif pattern.pattern_type == "optimization" and pattern.frequency > 0.5:
                recommendations.append(
                    Recommendation(
                        type="resource_management",
                        priority="medium",
                        description=f"Optimize based on pattern: {pattern.description}",
                        expected_improvement="15-25% efficiency improvement",
                        implementation_effort="medium",
                        risk_level="low",
                        estimated_impact={"resource_efficiency": 2.0},
                    )
                )

        return recommendations

    def _generate_insight_recommendations(
        self, insights: List[LearningInsight]
    ) -> List[Recommendation]:
        """Generate recommendations based on learning insights"""
        recommendations = []

        for insight in insights:
            if (
                insight.insight_type == "optimization_opportunity"
                and insight.confidence > 0.7
            ):
                recommendations.append(
                    Recommendation(
                        type="workflow_optimization",
                        priority="medium",
                        description=f"Apply insight: {insight.description}",
                        expected_improvement="10-20% overall improvement",
                        implementation_effort="low",
                        risk_level="low",
                        estimated_impact={"overall": 1.5},
                    )
                )

        return recommendations


class TeamCoachEngine:
    """Main engine that orchestrates team coaching operations"""

    def __init__(self):
        self.performance_analyzer = PerformanceAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        self.learning_engine = LearningEngine()
        self.recommendation_engine = RecommendationEngine()
        self.historical_workflows = []

    def process_request(self, request: TeamCoachRequest) -> TeamCoachResponse:
        """Process a team coach analysis request"""
        try:
            # Store workflow data for historical analysis
            self.historical_workflows.append(request.workflow_data)

            # Analyze performance
            performance_metrics = (
                self.performance_analyzer.analyze_workflow_performance(
                    request.workflow_data
                )
            )

            # Identify patterns (using historical context)
            historical_workflows = self._get_relevant_historical_workflows(request)
            patterns = self.pattern_recognizer.identify_patterns(historical_workflows)

            # Extract learning insights
            insights = self.learning_engine.extract_learning_insights(
                historical_workflows, patterns
            )

            # Generate recommendations
            recommendations = self.recommendation_engine.generate_recommendations(
                performance_metrics, patterns, insights
            )

            # Calculate performance trends
            trends = self._calculate_performance_trends(historical_workflows)

            # Build analysis results
            analysis_results = {
                "performance_score": performance_metrics.overall_score,
                "efficiency_metrics": {
                    "workflow_speed": self._score_to_label(
                        performance_metrics.speed_score
                    ),
                    "resource_efficiency": self._score_to_label(
                        performance_metrics.resource_efficiency_score
                    ),
                    "coordination_quality": self._score_to_label(
                        performance_metrics.coordination_score
                    ),
                    "output_quality": self._score_to_label(
                        performance_metrics.quality_score
                    ),
                },
                "workflow_duration": (
                    request.workflow_data.end_time - request.workflow_data.start_time
                ).total_seconds(),
                "agents_utilized": len(request.workflow_data.agents_used),
                "success_rate": request.workflow_data.outcomes.success_rate,
            }

            return TeamCoachResponse(
                success=True,
                analysis_results=analysis_results,
                recommendations=recommendations,
                learning_insights=insights,
                performance_trends=trends,
                patterns_identified=patterns,
                errors=[],
            )

        except Exception as e:
            return TeamCoachResponse(
                success=False,
                analysis_results={},
                recommendations=[],
                learning_insights=[],
                performance_trends={},
                patterns_identified=[],
                errors=[f"Team coach analysis error: {str(e)}"],
            )

    def _get_relevant_historical_workflows(
        self, request: TeamCoachRequest
    ) -> List[WorkflowData]:
        """Get historical workflows relevant to the current analysis"""
        relevant_workflows = [request.workflow_data]  # Include current workflow

        # Add historical workflows based on scope
        if request.reflection_scope == "session":
            # Last few workflows from same session
            relevant_workflows.extend(self.historical_workflows[-10:])
        elif request.reflection_scope == "project":
            # Workflows from same project context
            project_workflows = [
                w
                for w in self.historical_workflows
                if w.project_context == request.workflow_data.project_context
            ]
            relevant_workflows.extend(project_workflows[-20:])
        else:  # system scope
            # All historical workflows
            relevant_workflows.extend(self.historical_workflows[-50:])

        return relevant_workflows

    def _calculate_performance_trends(
        self, workflows: List[WorkflowData]
    ) -> Dict[str, Any]:
        """Calculate performance trends from historical workflows"""
        if len(workflows) < 2:
            return {"insufficient_data": True}

        # Sort by start time
        sorted_workflows = sorted(workflows, key=lambda w: w.start_time)

        # Calculate trend metrics
        success_rates = [w.outcomes.success_rate for w in sorted_workflows]
        durations = [
            (w.end_time - w.start_time).total_seconds() for w in sorted_workflows
        ]

        # Calculate improvement rates
        if len(success_rates) >= 3:
            recent_success = statistics.mean(success_rates[-3:])
            earlier_success = statistics.mean(success_rates[:3])
            success_improvement = (recent_success - earlier_success) / max(
                earlier_success, 0.1
            )
        else:
            success_improvement = 0.0

        if len(durations) >= 3:
            recent_duration = statistics.mean(durations[-3:])
            earlier_duration = statistics.mean(durations[:3])
            speed_improvement = (earlier_duration - recent_duration) / max(
                earlier_duration, 1
            )
        else:
            speed_improvement = 0.0

        return {
            "improvement_rate": (success_improvement + speed_improvement) / 2,
            "success_trend": success_improvement,
            "speed_trend": speed_improvement,
            "total_workflows_analyzed": len(workflows),
            "regression_indicators": [],  # TODO: Implement regression detection
            "emerging_patterns": [],  # TODO: Implement emerging pattern detection
        }

    def _score_to_label(self, score: float) -> str:
        """Convert numeric score to descriptive label"""
        if score >= 8.0:
            return "excellent"
        elif score >= 6.0:
            return "good"
        elif score >= 4.0:
            return "fair"
        else:
            return "poor"


def run_team_coach(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for team coach operations"""
    try:
        # Parse request data into proper objects
        workflow_data = _parse_workflow_data(request_data.get("workflow_data", {}))

        request = TeamCoachRequest(
            analysis_type=request_data.get("analysis_type", "performance"),
            workflow_data=workflow_data,
            historical_context=request_data.get("historical_context", {}),
            reflection_scope=request_data.get("reflection_scope", "session"),
        )

        # Process request
        engine = TeamCoachEngine()
        response = engine.process_request(request)

        # Convert response to dictionary format
        return {
            "success": response.success,
            "analysis_results": response.analysis_results,
            "recommendations": [
                _recommendation_to_dict(r) for r in response.recommendations
            ],
            "learning_insights": [
                _insight_to_dict(i) for i in response.learning_insights
            ],
            "performance_trends": response.performance_trends,
            "patterns_identified": [
                _pattern_to_dict(p) for p in response.patterns_identified
            ],
            "errors": response.errors,
        }

    except Exception as e:
        return {
            "success": False,
            "analysis_results": {},
            "recommendations": [],
            "learning_insights": [],
            "performance_trends": {},
            "patterns_identified": [],
            "errors": [f"Team coach error: {str(e)}"],
        }


def _parse_workflow_data(data: Dict[str, Any]) -> WorkflowData:
    """Parse dictionary data into WorkflowData object"""
    # Parse task sequence
    task_sequence = []
    for step_data in data.get("task_sequence", []):
        task_sequence.append(
            WorkflowStep(
                agent=step_data.get("agent", "unknown"),
                action=step_data.get("action", "unknown"),
                duration_seconds=step_data.get("duration_seconds", 0),
                success=step_data.get("success", True),
                metadata=step_data.get("metadata", {}),
                timestamp=datetime.now(),  # Default to now if not provided
            )
        )

    # Parse resource usage
    resource_data = data.get("resource_usage", {})
    resource_usage = ResourceUsage(
        peak_memory_mb=resource_data.get("peak_memory_mb", 256),
        cpu_time_seconds=resource_data.get("cpu_time_seconds", 30),
        disk_io_mb=resource_data.get("disk_io_mb", 10),
        network_io_mb=resource_data.get("network_io_mb", 0),
    )

    # Parse outcomes
    outcome_data = data.get("outcomes", {})
    outcomes = WorkflowOutcomes(
        files_created=outcome_data.get("files_created", 0),
        tests_written=outcome_data.get("tests_written", 0),
        lines_of_code=outcome_data.get("lines_of_code", 0),
        success_rate=outcome_data.get("success_rate", 1.0),
        user_satisfaction=outcome_data.get("user_satisfaction", "high"),
        errors_encountered=outcome_data.get("errors_encountered", 0),
        warnings_generated=outcome_data.get("warnings_generated", 0),
    )

    return WorkflowData(
        workflow_id=data.get(
            "workflow_id", f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ),
        agents_used=data.get("agents_used", []),
        task_sequence=task_sequence,
        resource_usage=resource_usage,
        outcomes=outcomes,
        start_time=datetime.now() - timedelta(seconds=60),  # Default values
        end_time=datetime.now(),
        project_context=data.get("project_context", "default"),
    )


def _recommendation_to_dict(recommendation: Recommendation) -> Dict[str, Any]:
    """Convert Recommendation object to dictionary"""
    return {
        "type": recommendation.type,
        "priority": recommendation.priority,
        "description": recommendation.description,
        "expected_improvement": recommendation.expected_improvement,
        "implementation_effort": recommendation.implementation_effort,
        "risk_level": recommendation.risk_level,
        "estimated_impact": recommendation.estimated_impact,
    }


def _insight_to_dict(insight: LearningInsight) -> Dict[str, Any]:
    """Convert LearningInsight object to dictionary"""
    return {
        "insight_type": insight.insight_type,
        "description": insight.description,
        "confidence": insight.confidence,
        "supporting_evidence": insight.supporting_evidence,
        "applicable_contexts": insight.applicable_contexts,
    }


def _pattern_to_dict(pattern: Pattern) -> Dict[str, Any]:
    """Convert Pattern object to dictionary"""
    return {
        "pattern_type": pattern.pattern_type,
        "description": pattern.description,
        "frequency": pattern.frequency,
        "impact": pattern.impact,
        "confidence": pattern.confidence,
        "supporting_evidence": pattern.supporting_evidence,
    }


if __name__ == "__main__":
    # Example usage
    sample_workflow_data = {
        "workflow_id": "test_workflow_001",
        "agents_used": ["orchestrator", "task-decomposer", "code-writer"],
        "task_sequence": [
            {
                "agent": "orchestrator",
                "action": "coordinate_tasks",
                "duration_seconds": 15,
                "success": True,
                "metadata": {"tasks_created": 3},
            },
            {
                "agent": "task-decomposer",
                "action": "decompose_task",
                "duration_seconds": 25,
                "success": True,
                "metadata": {"subtasks_created": 4},
            },
            {
                "agent": "code-writer",
                "action": "generate_code",
                "duration_seconds": 45,
                "success": True,
                "metadata": {"files_created": 2, "lines_written": 150},
            },
        ],
        "resource_usage": {
            "peak_memory_mb": 512,
            "cpu_time_seconds": 85,
            "disk_io_mb": 15,
        },
        "outcomes": {
            "files_created": 2,
            "tests_written": 8,
            "lines_of_code": 150,
            "success_rate": 1.0,
            "user_satisfaction": "high",
        },
        "project_context": "gadugi_v0.3_development",
    }

    request_data = {
        "analysis_type": "performance",
        "workflow_data": sample_workflow_data,
        "historical_context": {},
        "reflection_scope": "session",
    }

    result = run_team_coach(request_data)
    print(json.dumps(result, indent=2))
