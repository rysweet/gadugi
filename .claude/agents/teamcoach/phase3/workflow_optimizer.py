"""
TeamCoach Phase 3: Workflow Optimizer

Analyzes and optimizes team workflows to improve efficiency, reduce bottlenecks,
and enhance overall productivity.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """Types of workflow bottlenecks."""

    RESOURCE_CONSTRAINT = "resource_constraint"
    SKILL_GAP = "skill_gap"
    DEPENDENCY_CHAIN = "dependency_chain"
    COMMUNICATION_LAG = "communication_lag"
    PROCESS_INEFFICIENCY = "process_inefficiency"
    CAPACITY_LIMIT = "capacity_limit"
    COORDINATION_OVERHEAD = "coordination_overhead"


class OptimizationType(Enum):
    """Types of workflow optimizations."""

    PARALLELIZATION = "parallelization"
    AUTOMATION = "automation"
    RESEQUENCING = "resequencing"
    RESOURCE_REALLOCATION = "resource_reallocation"
    SKILL_DEVELOPMENT = "skill_development"
    PROCESS_STREAMLINING = "process_streamlining"
    COMMUNICATION_IMPROVEMENT = "communication_improvement"


@dataclass
class WorkflowMetrics:
    """Metrics for workflow performance."""

    total_duration: float  # seconds
    active_time: float  # seconds
    wait_time: float  # seconds
    efficiency_ratio: float  # active_time / total_duration
    throughput: float  # tasks per hour
    bottleneck_impact: float  # percentage of time lost to bottlenecks
    parallel_efficiency: float  # how well parallelization is utilized


@dataclass
class Bottleneck:
    """Represents a workflow bottleneck."""

    bottleneck_id: str
    type: BottleneckType
    location: str  # Where in the workflow
    impact: float  # Percentage impact on efficiency
    affected_agents: List[str]
    affected_tasks: List[str]
    description: str
    evidence: Dict[str, Any]
    detected_at: datetime


@dataclass
class WorkflowOptimization:
    """Represents a workflow optimization recommendation."""

    optimization_id: str
    type: OptimizationType
    priority: str  # high, medium, low
    description: str
    expected_improvement: float  # percentage
    implementation_steps: List[str]
    affected_components: List[str]
    effort_estimate: str  # e.g., "2 days", "1 week"
    prerequisites: List[str]
    risks: List[str]


@dataclass
class WorkflowAnalysis:
    """Comprehensive workflow analysis results."""

    workflow_id: str
    current_metrics: WorkflowMetrics
    bottlenecks: List[Bottleneck]
    optimizations: List[WorkflowOptimization]
    projected_metrics: WorkflowMetrics
    analysis_timestamp: datetime


class WorkflowOptimizer:
    """
    Analyzes and optimizes multi-agent workflows for maximum efficiency.

    Features:
    - Bottleneck detection and analysis
    - Workflow pattern recognition
    - Optimization recommendation generation
    - Impact prediction
    - Implementation guidance
    """

    def __init__(self):
        """Initialize the workflow optimizer."""
        self.workflow_patterns: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Tuple[str, WorkflowOptimization, float]] = []

        # Thresholds for bottleneck detection
        self.bottleneck_thresholds = {
            "wait_time_ratio": 0.3,  # 30% wait time indicates bottleneck
            "resource_utilization": 0.9,  # 90% utilization indicates constraint
            "communication_delay": 300,  # 5 minutes delay is significant
            "rework_rate": 0.15,  # 15% rework indicates process issue
        }

    def analyze_workflow(
        self,
        workflow_data: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
    ) -> WorkflowAnalysis:
        """
        Perform comprehensive workflow analysis.

        Args:
            workflow_data: Current workflow configuration and state
            agent_states: Current state of all agents
            task_history: Historical task execution data

        Returns:
            Complete workflow analysis with optimizations
        """
        workflow_id = workflow_data.get("id", "unknown")

        # Calculate current metrics
        current_metrics = self._calculate_workflow_metrics(
            workflow_data, agent_states, task_history
        )

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(
            workflow_data, agent_states, task_history, current_metrics
        )

        # Generate optimizations
        optimizations = self._generate_optimizations(
            workflow_data, bottlenecks, current_metrics
        )

        # Project improvements
        projected_metrics = self._project_improvements(current_metrics, optimizations)

        # Create analysis
        analysis = WorkflowAnalysis(
            workflow_id=workflow_id,
            current_metrics=current_metrics,
            bottlenecks=bottlenecks,
            optimizations=optimizations,
            projected_metrics=projected_metrics,
            analysis_timestamp=datetime.utcnow(),
        )

        # Store pattern for learning
        self._update_workflow_patterns(workflow_id, analysis)

        return analysis

    def _calculate_workflow_metrics(
        self,
        workflow_data: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
    ) -> WorkflowMetrics:
        """Calculate comprehensive workflow metrics."""

        # Calculate timing metrics from task history
        if not task_history:
            return WorkflowMetrics(
                total_duration=0,
                active_time=0,
                wait_time=0,
                efficiency_ratio=0,
                throughput=0,
                bottleneck_impact=0,
                parallel_efficiency=0,
            )

        # Sort tasks by start time
        sorted_tasks = sorted(task_history, key=lambda t: t.get("start_time", 0))

        # Calculate total duration
        first_start = sorted_tasks[0].get("start_time", 0)
        last_end = max(t.get("end_time", t.get("start_time", 0)) for t in sorted_tasks)
        total_duration = last_end - first_start

        # Calculate active time (sum of all task durations)
        active_time = sum(
            t.get("end_time", t.get("start_time", 0)) - t.get("start_time", 0)
            for t in sorted_tasks
        )

        # Calculate wait time
        wait_time = sum(t.get("wait_time", 0) for t in sorted_tasks)

        # Calculate efficiency ratio
        efficiency_ratio = active_time / total_duration if total_duration > 0 else 0

        # Calculate throughput
        hours = total_duration / 3600 if total_duration > 0 else 1
        throughput = len(sorted_tasks) / hours

        # Calculate bottleneck impact
        bottleneck_time = sum(t.get("blocked_time", 0) for t in sorted_tasks)
        bottleneck_impact = (
            bottleneck_time / total_duration if total_duration > 0 else 0
        )

        # Calculate parallel efficiency
        parallel_efficiency = self._calculate_parallel_efficiency(sorted_tasks)

        return WorkflowMetrics(
            total_duration=total_duration,
            active_time=active_time,
            wait_time=wait_time,
            efficiency_ratio=efficiency_ratio,
            throughput=throughput,
            bottleneck_impact=bottleneck_impact,
            parallel_efficiency=parallel_efficiency,
        )

    def _detect_bottlenecks(
        self,
        workflow_data: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
        metrics: WorkflowMetrics,
    ) -> List[Bottleneck]:
        """Detect bottlenecks in the workflow."""
        bottlenecks = []

        # Check for resource constraints
        resource_bottlenecks = self._detect_resource_bottlenecks(
            workflow_data, agent_states, task_history
        )
        bottlenecks.extend(resource_bottlenecks)

        # Check for skill gaps
        skill_bottlenecks = self._detect_skill_bottlenecks(
            workflow_data, agent_states, task_history
        )
        bottlenecks.extend(skill_bottlenecks)

        # Check for dependency chains
        dependency_bottlenecks = self._detect_dependency_bottlenecks(
            workflow_data, task_history
        )
        bottlenecks.extend(dependency_bottlenecks)

        # Check for communication lags
        communication_bottlenecks = self._detect_communication_bottlenecks(
            agent_states, task_history
        )
        bottlenecks.extend(communication_bottlenecks)

        # Check for process inefficiencies
        process_bottlenecks = self._detect_process_bottlenecks(
            workflow_data, task_history, metrics
        )
        bottlenecks.extend(process_bottlenecks)

        # Sort by impact
        bottlenecks.sort(key=lambda b: b.impact, reverse=True)

        return bottlenecks

    def _generate_optimizations(
        self,
        workflow_data: Dict[str, Any],
        bottlenecks: List[Bottleneck],
        metrics: WorkflowMetrics,
    ) -> List[WorkflowOptimization]:
        """Generate optimization recommendations based on bottlenecks."""
        optimizations = []

        # Generate optimizations for each bottleneck
        for bottleneck in bottlenecks[:5]:  # Focus on top 5 bottlenecks
            if bottleneck.type == BottleneckType.RESOURCE_CONSTRAINT:
                opt = self._generate_resource_optimization(bottleneck, workflow_data)
                if opt:
                    optimizations.append(opt)

            elif bottleneck.type == BottleneckType.DEPENDENCY_CHAIN:
                opt = self._generate_parallelization_optimization(
                    bottleneck, workflow_data
                )
                if opt:
                    optimizations.append(opt)

            elif bottleneck.type == BottleneckType.PROCESS_INEFFICIENCY:
                opt = self._generate_process_optimization(bottleneck, workflow_data)
                if opt:
                    optimizations.append(opt)

            elif bottleneck.type == BottleneckType.SKILL_GAP:
                opt = self._generate_skill_optimization(bottleneck, workflow_data)
                if opt:
                    optimizations.append(opt)

            elif bottleneck.type == BottleneckType.COMMUNICATION_LAG:
                opt = self._generate_communication_optimization(
                    bottleneck, workflow_data
                )
                if opt:
                    optimizations.append(opt)

        # Add general optimizations based on metrics
        if metrics.parallel_efficiency < 0.6:
            opt = self._generate_parallelization_improvement(workflow_data, metrics)
            if opt:
                optimizations.append(opt)

        if metrics.efficiency_ratio < 0.7:
            opt = self._generate_efficiency_improvement(workflow_data, metrics)
            if opt:
                optimizations.append(opt)

        # Prioritize optimizations
        optimizations = self._prioritize_optimizations(optimizations)

        return optimizations

    def _detect_resource_bottlenecks(
        self,
        workflow_data: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
    ) -> List[Bottleneck]:
        """Detect resource constraint bottlenecks."""
        bottlenecks = []

        # Analyze resource utilization
        resource_usage = {}
        resource_waits = {}

        for task in task_history:
            resources = task.get("resources_used", [])
            wait_time = task.get("resource_wait_time", 0)

            for resource in resources:
                if resource not in resource_usage:
                    resource_usage[resource] = 0
                    resource_waits[resource] = 0

                resource_usage[resource] += task.get("duration", 0)
                resource_waits[resource] += wait_time

        # Check for overutilized resources
        total_time = sum(t.get("duration", 0) for t in task_history)

        for resource, usage in resource_usage.items():
            utilization = usage / total_time if total_time > 0 else 0

            if utilization > self.bottleneck_thresholds["resource_utilization"]:
                wait_ratio = resource_waits[resource] / usage if usage > 0 else 0

                bottleneck = Bottleneck(
                    bottleneck_id=f"resource_{resource}_{datetime.utcnow().timestamp()}",
                    type=BottleneckType.RESOURCE_CONSTRAINT,
                    location=f"Resource: {resource}",
                    impact=wait_ratio * 100,  # Percentage of time waiting
                    affected_agents=[
                        str(t.get("agent_id", ""))
                        for t in task_history
                        if resource in t.get("resources_used", [])
                        and t.get("agent_id") is not None
                    ],
                    affected_tasks=[
                        str(t.get("task_id", ""))
                        for t in task_history
                        if resource in t.get("resources_used", [])
                        and t.get("task_id") is not None
                    ],
                    description=f"Resource '{resource}' is overutilized ({utilization:.1%})",
                    evidence={
                        "resource": resource,
                        "utilization": utilization,
                        "total_wait_time": resource_waits[resource],
                        "affected_task_count": len(
                            [
                                t
                                for t in task_history
                                if resource in t.get("resources_used", [])
                            ]
                        ),
                    },
                    detected_at=datetime.utcnow(),
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_skill_bottlenecks(
        self,
        workflow_data: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
    ) -> List[Bottleneck]:
        """Detect skill gap bottlenecks."""
        bottlenecks = []

        # Analyze skill requirements vs availability
        skill_demand = {}
        skill_supply = {}
        skill_delays = {}

        # Calculate demand from task history
        for task in task_history:
            required_skills = task.get("required_skills", [])
            wait_time = task.get("skill_wait_time", 0)

            for skill in required_skills:
                if skill not in skill_demand:
                    skill_demand[skill] = 0
                    skill_delays[skill] = 0

                skill_demand[skill] += 1
                skill_delays[skill] += wait_time

        # Calculate supply from agent capabilities
        for agent_id, state in agent_states.items():
            agent_skills = state.get("skills", [])
            for skill in agent_skills:
                if skill not in skill_supply:
                    skill_supply[skill] = 0
                skill_supply[skill] += 1

        # Find skill gaps
        for skill, demand in skill_demand.items():
            supply = skill_supply.get(skill, 0)

            if supply == 0 or demand / supply > 3:  # High demand/supply ratio
                avg_delay = skill_delays[skill] / demand if demand > 0 else 0

                bottleneck = Bottleneck(
                    bottleneck_id=f"skill_{skill}_{datetime.utcnow().timestamp()}",
                    type=BottleneckType.SKILL_GAP,
                    location=f"Skill: {skill}",
                    impact=(avg_delay / 3600) * 10,  # Impact based on hours of delay
                    affected_agents=list(agent_states.keys()),
                    affected_tasks=[
                        str(t.get("task_id", ""))
                        for t in task_history
                        if skill in t.get("required_skills", [])
                        and t.get("task_id") is not None
                    ],
                    description=f"Insufficient agents with '{skill}' skill (demand: {demand}, supply: {supply})",
                    evidence={
                        "skill": skill,
                        "demand": demand,
                        "supply": supply,
                        "total_delay": skill_delays[skill],
                        "demand_supply_ratio": demand / supply
                        if supply > 0
                        else float("inf"),
                    },
                    detected_at=datetime.utcnow(),
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_dependency_bottlenecks(
        self, workflow_data: Dict[str, Any], task_history: List[Dict[str, Any]]
    ) -> List[Bottleneck]:
        """Detect dependency chain bottlenecks."""
        bottlenecks = []

        # Build dependency graph
        dependencies = {}
        task_durations = {}

        for task in task_history:
            task_id = task.get("task_id")
            deps = task.get("dependencies", [])
            dependencies[task_id] = deps
            task_durations[task_id] = task.get("duration", 0)

        # Find critical path
        critical_path = self._find_critical_path(dependencies, task_durations)

        if critical_path:
            total_duration = sum(task_durations.get(t, 0) for t in critical_path)
            workflow_duration = max(t.get("end_time", 0) for t in task_history) - min(
                t.get("start_time", 0) for t in task_history
            )

            if total_duration / workflow_duration > 0.8:  # Critical path dominates
                bottleneck = Bottleneck(
                    bottleneck_id=f"dependency_{datetime.utcnow().timestamp()}",
                    type=BottleneckType.DEPENDENCY_CHAIN,
                    location="Critical path",
                    impact=(total_duration / workflow_duration - 0.5) * 100,
                    affected_agents=list(
                        set(
                            str(t.get("agent_id", ""))
                            for t in task_history
                            if t.get("task_id") in critical_path
                            and t.get("agent_id") is not None
                        )
                    ),
                    affected_tasks=critical_path,
                    description=f"Long dependency chain limiting parallelization ({len(critical_path)} tasks)",
                    evidence={
                        "critical_path": critical_path,
                        "path_duration": total_duration,
                        "path_percentage": total_duration / workflow_duration
                        if workflow_duration > 0
                        else 0,
                    },
                    detected_at=datetime.utcnow(),
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_communication_bottlenecks(
        self,
        agent_states: Dict[str, Dict[str, Any]],
        task_history: List[Dict[str, Any]],
    ) -> List[Bottleneck]:
        """Detect communication lag bottlenecks."""
        bottlenecks = []

        # Analyze communication delays
        communication_delays = {}

        for task in task_history:
            comm_delay = task.get("communication_delay", 0)
            if comm_delay > self.bottleneck_thresholds["communication_delay"]:
                agents = task.get("communicating_agents", [])
                pair = tuple(sorted(agents)) if len(agents) == 2 else ("general",)

                if pair not in communication_delays:
                    communication_delays[pair] = []
                communication_delays[pair].append(comm_delay)

        # Create bottlenecks for significant delays
        for pair, delays in communication_delays.items():
            avg_delay = sum(delays) / len(delays)
            total_delay = sum(delays)

            if avg_delay > self.bottleneck_thresholds["communication_delay"]:
                bottleneck = Bottleneck(
                    bottleneck_id=f"comm_{'-'.join(pair)}_{datetime.utcnow().timestamp()}",
                    type=BottleneckType.COMMUNICATION_LAG,
                    location=f"Communication between {pair}",
                    impact=(total_delay / 3600) * 5,  # Impact based on hours of delay
                    affected_agents=list(pair)
                    if pair[0] != "general"
                    else list(agent_states.keys()),
                    affected_tasks=[  # type: ignore[assignment]
                        t.get("task_id")
                        for t in task_history
                        if t.get("communication_delay", 0)
                        > self.bottleneck_thresholds["communication_delay"]
                    ],
                    description=f"Communication delays averaging {avg_delay / 60:.1f} minutes",
                    evidence={
                        "agent_pair": pair,
                        "average_delay": avg_delay,
                        "total_delay": total_delay,
                        "occurrence_count": len(delays),
                    },
                    detected_at=datetime.utcnow(),
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_process_bottlenecks(
        self,
        workflow_data: Dict[str, Any],
        task_history: List[Dict[str, Any]],
        metrics: WorkflowMetrics,
    ) -> List[Bottleneck]:
        """Detect process inefficiency bottlenecks."""
        bottlenecks = []

        # Check for high rework rates
        rework_tasks = [t for t in task_history if t.get("is_rework", False)]
        rework_rate = len(rework_tasks) / len(task_history) if task_history else 0

        if rework_rate > self.bottleneck_thresholds["rework_rate"]:
            bottleneck = Bottleneck(
                bottleneck_id=f"process_rework_{datetime.utcnow().timestamp()}",
                type=BottleneckType.PROCESS_INEFFICIENCY,
                location="Quality control process",
                impact=rework_rate * 100,
                affected_agents=[
                    str(t.get("agent_id", ""))
                    for t in rework_tasks
                    if t.get("agent_id") is not None
                ],
                affected_tasks=[
                    str(t.get("task_id", ""))
                    for t in rework_tasks
                    if t.get("task_id") is not None
                ],
                description=f"High rework rate ({rework_rate:.1%}) indicating process issues",
                evidence={
                    "rework_rate": rework_rate,
                    "rework_count": len(rework_tasks),
                    "common_failure_reasons": self._analyze_rework_reasons(
                        rework_tasks
                    ),
                },
                detected_at=datetime.utcnow(),
            )
            bottlenecks.append(bottleneck)

        # Check for inefficient task sequencing
        if metrics.efficiency_ratio < 0.5:
            bottleneck = Bottleneck(
                bottleneck_id=f"process_efficiency_{datetime.utcnow().timestamp()}",
                type=BottleneckType.PROCESS_INEFFICIENCY,
                location="Overall workflow",
                impact=(0.7 - metrics.efficiency_ratio) * 100,
                affected_agents=[
                    str(t.get("agent_id", ""))
                    for t in task_history
                    if t.get("agent_id") is not None
                ],
                affected_tasks=[
                    str(t.get("task_id", ""))
                    for t in task_history
                    if t.get("task_id") is not None
                ],
                description=f"Low workflow efficiency ({metrics.efficiency_ratio:.1%})",
                evidence={
                    "efficiency_ratio": metrics.efficiency_ratio,
                    "wait_time_ratio": metrics.wait_time / metrics.total_duration
                    if metrics.total_duration > 0
                    else 0,
                    "parallel_efficiency": metrics.parallel_efficiency,
                },
                detected_at=datetime.utcnow(),
            )
            bottlenecks.append(bottleneck)

        return bottlenecks

    def _generate_resource_optimization(
        self, bottleneck: Bottleneck, workflow_data: Dict[str, Any]
    ) -> Optional[WorkflowOptimization]:
        """Generate optimization for resource constraints."""
        resource = bottleneck.evidence.get("resource")
        bottleneck.evidence.get("utilization", 0)

        optimization = WorkflowOptimization(
            optimization_id=f"opt_resource_{resource}_{datetime.utcnow().timestamp()}",
            type=OptimizationType.RESOURCE_REALLOCATION,
            priority="high" if bottleneck.impact > 20 else "medium",
            description=f"Optimize allocation of resource '{resource}'",
            expected_improvement=min(
                bottleneck.impact * 0.7, 30
            ),  # Conservative estimate
            implementation_steps=[
                f"1. Analyze current usage patterns for {resource}",
                "2. Identify tasks that can use alternative resources",
                f"3. Implement resource pooling for {resource}",
                "4. Add capacity planning for peak usage times",
                "5. Consider adding additional capacity if needed",
            ],
            affected_components=[resource] + list(bottleneck.affected_agents),  # type: ignore[assignment]
            effort_estimate="3-5 days",
            prerequisites=[
                "Resource usage audit",
                "Alternative resource identification",
            ],
            risks=[
                "Temporary disruption during reallocation",
                "Cost of additional resources",
            ],
        )

        return optimization

    def _generate_parallelization_optimization(
        self, bottleneck: Bottleneck, workflow_data: Dict[str, Any]
    ) -> Optional[WorkflowOptimization]:
        """Generate optimization for dependency chains."""
        critical_path = bottleneck.evidence.get("critical_path", [])

        optimization = WorkflowOptimization(
            optimization_id=f"opt_parallel_{datetime.utcnow().timestamp()}",
            type=OptimizationType.PARALLELIZATION,
            priority="high",
            description="Break dependency chains to enable parallelization",
            expected_improvement=min(bottleneck.impact * 0.6, 40),
            implementation_steps=[
                "1. Analyze task dependencies for unnecessary constraints",
                "2. Identify tasks that can run in parallel",
                "3. Redesign workflow to minimize sequential dependencies",
                "4. Implement task batching where appropriate",
                "5. Add parallel execution capabilities",
            ],
            affected_components=critical_path[:5],  # Top 5 tasks in critical path
            effort_estimate="1-2 weeks",
            prerequisites=["Dependency analysis", "Task independence verification"],
            risks=["Increased complexity", "Potential race conditions"],
        )

        return optimization

    def _generate_process_optimization(
        self, bottleneck: Bottleneck, workflow_data: Dict[str, Any]
    ) -> Optional[WorkflowOptimization]:
        """Generate optimization for process inefficiencies."""
        rework_rate = bottleneck.evidence.get("rework_rate", 0)

        optimization = WorkflowOptimization(
            optimization_id=f"opt_process_{datetime.utcnow().timestamp()}",
            type=OptimizationType.PROCESS_STREAMLINING,
            priority="high" if rework_rate > 0.2 else "medium",
            description="Streamline process to reduce rework and improve quality",
            expected_improvement=min(rework_rate * 100 * 0.8, 25),
            implementation_steps=[
                "1. Analyze root causes of rework",
                "2. Implement quality checks earlier in process",
                "3. Standardize task templates and guidelines",
                "4. Add automated validation where possible",
                "5. Train agents on common failure patterns",
            ],
            affected_components=bottleneck.affected_agents[:10],
            effort_estimate="2-3 weeks",
            prerequisites=["Root cause analysis", "Quality metrics baseline"],
            risks=[
                "Initial slowdown during implementation",
                "Resistance to process change",
            ],
        )

        return optimization

    def _generate_skill_optimization(
        self, bottleneck: Bottleneck, workflow_data: Dict[str, Any]
    ) -> Optional[WorkflowOptimization]:
        """Generate optimization for skill gaps."""
        skill = bottleneck.evidence.get("skill")
        demand_supply_ratio = bottleneck.evidence.get("demand_supply_ratio", 0)

        optimization = WorkflowOptimization(
            optimization_id=f"opt_skill_{skill}_{datetime.utcnow().timestamp()}",
            type=OptimizationType.SKILL_DEVELOPMENT,
            priority="high" if demand_supply_ratio > 5 else "medium",
            description=f"Address skill gap in '{skill}'",
            expected_improvement=min(bottleneck.impact * 0.5, 20),
            implementation_steps=[
                f"1. Identify agents with potential for {skill} development",
                f"2. Create targeted training program for {skill}",
                "3. Implement mentoring/shadowing program",
                "4. Consider hiring/contracting for immediate needs",
                "5. Create knowledge base for skill transfer",
            ],
            affected_components=bottleneck.affected_agents[:5],
            effort_estimate="4-6 weeks",
            prerequisites=["Skill assessment", "Training resources"],
            risks=[
                "Time investment for training",
                "Skill development may take longer than expected",
            ],
        )

        return optimization

    def _generate_communication_optimization(
        self, bottleneck: Bottleneck, workflow_data: Dict[str, Any]
    ) -> Optional[WorkflowOptimization]:
        """Generate optimization for communication issues."""
        bottleneck.evidence.get("average_delay", 0)

        optimization = WorkflowOptimization(
            optimization_id=f"opt_comm_{datetime.utcnow().timestamp()}",
            type=OptimizationType.COMMUNICATION_IMPROVEMENT,
            priority="medium",
            description="Improve inter-agent communication efficiency",
            expected_improvement=min(bottleneck.impact * 0.8, 15),
            implementation_steps=[
                "1. Implement real-time communication channels",
                "2. Standardize communication protocols",
                "3. Add automated status updates",
                "4. Create shared dashboards for visibility",
                "5. Reduce communication overhead with better tools",
            ],
            affected_components=list(bottleneck.evidence.get("agent_pair", [])),
            effort_estimate="1 week",
            prerequisites=["Communication audit", "Tool evaluation"],
            risks=["Tool adoption challenges", "Information overload"],
        )

        return optimization

    def _generate_parallelization_improvement(
        self, workflow_data: Dict[str, Any], metrics: WorkflowMetrics
    ) -> Optional[WorkflowOptimization]:
        """Generate general parallelization improvement."""
        current_efficiency = metrics.parallel_efficiency

        optimization = WorkflowOptimization(
            optimization_id=f"opt_parallel_general_{datetime.utcnow().timestamp()}",
            type=OptimizationType.PARALLELIZATION,
            priority="medium",
            description="Improve overall workflow parallelization",
            expected_improvement=(0.8 - current_efficiency) * 50
            if current_efficiency < 0.8
            else 10,
            implementation_steps=[
                "1. Identify all parallelizable task groups",
                "2. Redesign workflow for maximum parallelism",
                "3. Implement parallel task scheduler",
                "4. Balance workload across parallel paths",
                "5. Monitor and optimize parallel execution",
            ],
            affected_components=["workflow_scheduler", "task_manager"],
            effort_estimate="2 weeks",
            prerequisites=["Task dependency mapping", "Parallel execution capability"],
            risks=["Increased system complexity", "Resource contention"],
        )

        return optimization

    def _generate_efficiency_improvement(
        self, workflow_data: Dict[str, Any], metrics: WorkflowMetrics
    ) -> Optional[WorkflowOptimization]:
        """Generate general efficiency improvement."""
        optimization = WorkflowOptimization(
            optimization_id=f"opt_efficiency_{datetime.utcnow().timestamp()}",
            type=OptimizationType.PROCESS_STREAMLINING,
            priority="high",
            description="Improve overall workflow efficiency",
            expected_improvement=30,  # Target 30% improvement
            implementation_steps=[
                "1. Eliminate unnecessary steps and approvals",
                "2. Automate repetitive tasks",
                "3. Optimize task sequencing",
                "4. Reduce handoffs between agents",
                "5. Implement continuous monitoring",
            ],
            affected_components=["all"],
            effort_estimate="3-4 weeks",
            prerequisites=["Process mapping", "Automation assessment"],
            risks=["Change management challenges", "Initial productivity dip"],
        )

        return optimization

    def _prioritize_optimizations(
        self, optimizations: List[WorkflowOptimization]
    ) -> List[WorkflowOptimization]:
        """Prioritize optimizations based on impact and effort."""

        def score_optimization(opt: WorkflowOptimization) -> float:
            # Score based on improvement vs effort
            effort_days = self._estimate_effort_days(opt.effort_estimate)
            impact_score = opt.expected_improvement
            priority_multiplier = {"high": 3, "medium": 2, "low": 1}.get(
                opt.priority, 1
            )

            return (impact_score * priority_multiplier) / (effort_days + 1)

        # Sort by score (highest first)
        optimizations.sort(key=score_optimization, reverse=True)

        return optimizations

    def _project_improvements(
        self,
        current_metrics: WorkflowMetrics,
        optimizations: List[WorkflowOptimization],
    ) -> WorkflowMetrics:
        """Project workflow metrics after implementing optimizations."""

        # Calculate cumulative improvement
        total_improvement = 0
        for opt in optimizations:
            # Apply diminishing returns
            marginal_improvement = opt.expected_improvement * (
                1 - total_improvement / 100
            )
            total_improvement += marginal_improvement * 0.8  # 80% realization factor

        improvement_factor = 1 + (total_improvement / 100)

        # Project new metrics
        projected = WorkflowMetrics(
            total_duration=current_metrics.total_duration / improvement_factor,
            active_time=current_metrics.active_time,
            wait_time=current_metrics.wait_time / (improvement_factor * 1.5),
            efficiency_ratio=min(
                current_metrics.efficiency_ratio * improvement_factor, 0.95
            ),
            throughput=current_metrics.throughput * improvement_factor,
            bottleneck_impact=current_metrics.bottleneck_impact
            / (improvement_factor * 2),
            parallel_efficiency=min(current_metrics.parallel_efficiency * 1.3, 0.9),
        )

        return projected

    def _calculate_parallel_efficiency(
        self, sorted_tasks: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well parallelization is being utilized."""
        if not sorted_tasks:
            return 0

        # Create timeline slots
        timeline = []
        for task in sorted_tasks:
            start = task.get("start_time", 0)
            end = task.get("end_time", start)

            # Find available slot
            placed = False
            for slot in timeline:
                if slot[-1]["end"] <= start:
                    slot.append({"start": start, "end": end})
                    placed = True
                    break

            if not placed:
                timeline.append([{"start": start, "end": end}])

        # Calculate efficiency
        max_parallel = len(timeline)
        avg_parallel = len(sorted_tasks) / max_parallel if max_parallel > 0 else 1

        return min(avg_parallel / max_parallel, 1.0) if max_parallel > 1 else 0.5

    def _find_critical_path(
        self, dependencies: Dict[str, List[str]], durations: Dict[str, float]
    ) -> List[str]:
        """Find the critical path in the workflow."""
        # Simplified critical path finding
        # In production, would use proper CPM algorithm

        if not dependencies:
            return []

        # Find tasks with no dependencies (start nodes)
        all_tasks = set(dependencies.keys())
        all_deps = set()
        for deps in dependencies.values():
            all_deps.update(deps)

        start_tasks = all_tasks - all_deps

        if not start_tasks:
            # Circular dependency, pick arbitrary start
            start_tasks = {list(all_tasks)[0]}

        # Simple path finding (would be more sophisticated in production)
        longest_path = []
        longest_duration = 0

        for start in start_tasks:
            path = [start]
            current = start
            duration = durations.get(start, 0)

            # Follow longest dependency chain
            while current in dependencies and dependencies[current]:
                next_tasks = dependencies[current]
                if next_tasks:
                    # Pick the one with longest duration
                    next_task = max(next_tasks, key=lambda t: durations.get(t, 0))
                    if next_task not in path:  # Avoid cycles
                        path.append(next_task)
                        duration += durations.get(next_task, 0)
                        current = next_task
                    else:
                        break
                else:
                    break

            if duration > longest_duration:
                longest_duration = duration
                longest_path = path

        return longest_path

    def _analyze_rework_reasons(self, rework_tasks: List[Dict[str, Any]]) -> List[str]:
        """Analyze common reasons for rework."""
        reasons = {}

        for task in rework_tasks:
            reason = task.get("rework_reason", "Unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        # Return top 3 reasons
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        return [reason for reason, count in sorted_reasons[:3]]

    def _estimate_effort_days(self, effort_estimate: str) -> int:
        """Convert effort estimate string to days."""
        effort_lower = effort_estimate.lower()

        if "day" in effort_lower:
            # Extract number
            parts = effort_lower.split()
            for part in parts:
                if part.replace("-", "").replace(".", "").isdigit():
                    return int(float(part))
                elif "-" in part:
                    # Handle ranges like "3-5 days"
                    try:
                        nums = part.split("-")
                        return int(float(nums[1]))  # Use upper bound
                    except Exception:
                        pass
        elif "week" in effort_lower:
            # Convert weeks to days
            parts = effort_lower.split()
            for part in parts:
                if part.replace("-", "").replace(".", "").isdigit():
                    return int(float(part)) * 5  # 5 work days per week
                elif "-" in part:
                    try:
                        nums = part.split("-")
                        return int(float(nums[1])) * 5
                    except Exception:
                        pass

        return 7  # Default to 1 week

    def _update_workflow_patterns(self, workflow_id: str, analysis: WorkflowAnalysis):
        """Update workflow patterns for future learning."""
        if workflow_id not in self.workflow_patterns:
            self.workflow_patterns[workflow_id] = {
                "analyses": [],
                "common_bottlenecks": {},
                "effective_optimizations": [],
            }

        # Store analysis
        self.workflow_patterns[workflow_id]["analyses"].append(
            {
                "timestamp": analysis.analysis_timestamp,
                "metrics": analysis.current_metrics,
                "bottleneck_count": len(analysis.bottlenecks),
                "optimization_count": len(analysis.optimizations),
            }
        )

        # Track common bottlenecks
        for bottleneck in analysis.bottlenecks:
            key = f"{bottleneck.type.value}_{bottleneck.location}"
            if key not in self.workflow_patterns[workflow_id]["common_bottlenecks"]:
                self.workflow_patterns[workflow_id]["common_bottlenecks"][key] = 0
            self.workflow_patterns[workflow_id]["common_bottlenecks"][key] += 1
