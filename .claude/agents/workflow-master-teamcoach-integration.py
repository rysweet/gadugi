#!/usr/bin/env python3
"""
TeamCoach Integration for Enhanced WorkflowMaster

Provides intelligent workflow optimization through TeamCoach agent integration,
including performance analysis, capability assessment, and continuous improvement.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Workflow optimization strategies."""

    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    SPEED = "speed"
    QUALITY = "quality"
    RESOURCE_EFFICIENCY = "resource_efficiency"


@dataclass
class WorkflowOptimization:
    """Workflow optimization recommendation."""

    strategy: OptimizationStrategy
    task_id: str
    recommendation: str
    expected_improvement: float
    confidence: float
    implementation_effort: str
    priority: str
    reasoning: str
    metrics_impact: Dict[str, float]


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""

    task_completion_rate: float
    average_task_duration: float
    error_rate: float
    retry_rate: float
    autonomous_decision_rate: float
    container_execution_success_rate: float
    resource_utilization: Dict[str, float]
    quality_score: float
    user_satisfaction: float
    improvement_trends: Dict[str, List[float]]


class TeamCoachIntegration:
    """
    Integration layer between WorkflowMaster and TeamCoach agent for
    intelligent workflow optimization and continuous improvement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, workflow_master: Any = None) -> None:
        """Initialize TeamCoach integration."""
        self.workflow_master = workflow_master  # Reference to WorkflowMaster instance
        self.config = config or {}

        # Performance tracking
        self.metrics_history = []
        self.optimization_history = []
        self.learning_data = {}

        # Configuration
        self.optimization_enabled = self.config.get("optimization_enabled", True)
        self.learning_enabled = self.config.get("learning_enabled", True)
        self.auto_apply_optimizations = self.config.get(
            "auto_apply_optimizations", False
        )

        logger.info("TeamCoach integration initialized")

    def analyze_workflow_performance(self, workflow_state) -> PerformanceMetrics:
        """Analyze workflow performance using TeamCoach capabilities."""
        try:
            # Calculate current metrics
            completed_tasks = [
                t for t in workflow_state.tasks if (t.status if t is not None else None) == "completed"
            ]
            failed_tasks = [t for t in workflow_state.tasks if (t.status if t is not None else None) == "failed"]
            total_tasks = len(workflow_state.tasks)

            # Task completion rate
            completion_rate = (
                len(completed_tasks) / total_tasks if total_tasks > 0 else 0.0
            )

            # Average task duration
            durations = []
            for task in completed_tasks:
                if task.started_at and task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    durations.append(duration)

            avg_duration = sum(durations) / len(durations) if durations else 0.0

            # Error and retry rates
            error_rate = len(failed_tasks) / total_tasks if total_tasks > 0 else 0.0
            retry_count = sum(task.retry_count for task in workflow_state.tasks)
            retry_rate = retry_count / total_tasks if total_tasks > 0 else 0.0

            # Autonomous decision rate
            autonomous_decisions = len(workflow_state.autonomous_decisions)
            autonomous_decision_rate = (
                autonomous_decisions / total_tasks if total_tasks > 0 else 0.0
            )

            # Container execution success rate
            container_executions = (
                self.workflow_master.execution_stats.get("container_executions", 0)
                if self.workflow_master and hasattr(self.workflow_master, "execution_stats")
                else 0
            )
            container_failures = (
                self.workflow_master.execution_stats.get("container_failures", 0)
                if self.workflow_master and hasattr(self.workflow_master, "execution_stats")
                else 0
            )
            container_success_rate = (
                1.0 - (container_failures / max(container_executions, 1))
                if container_executions > 0 else 1.0
            )

            # Resource utilization (simplified)
            resource_utilization = {
                "cpu": 0.7,  # Would be actual measurements
                "memory": 0.5,
                "disk": 0.3,
                "network": 0.2,
            }

            # Quality score (composite metric)
            quality_score = (
                completion_rate * 0.4
                + (1.0 - error_rate) * 0.3
                + container_success_rate * 0.2
                + (1.0 - retry_rate) * 0.1
            )

            # User satisfaction (based on autonomous decisions and completion)
            user_satisfaction = min(
                completion_rate + (autonomous_decision_rate * 0.2), 1.0
            )

            # Improvement trends (would be calculated from history)
            improvement_trends = {
                "completion_rate": [0.8, 0.85, 0.9, completion_rate],
                "error_rate": [0.2, 0.15, 0.1, error_rate],
                "quality_score": [0.7, 0.75, 0.8, quality_score],
            }

            metrics = PerformanceMetrics(
                task_completion_rate=completion_rate,
                average_task_duration=avg_duration,
                error_rate=error_rate,
                retry_rate=retry_rate,
                autonomous_decision_rate=autonomous_decision_rate,
                container_execution_success_rate=container_success_rate,
                resource_utilization=resource_utilization,
                quality_score=quality_score,
                user_satisfaction=user_satisfaction,
                improvement_trends=improvement_trends,
            )

            # Store metrics for history
            self.metrics_history.append(
                {
                    "timestamp": datetime.now(),
                    "metrics": metrics,
                    "workflow_id": (workflow_state.task_id if workflow_state is not None else None),
                }
            )

            logger.info(
                f"Performance analysis completed - Quality Score: {quality_score:.2f}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            # Return default metrics
            return PerformanceMetrics(
                task_completion_rate=0.0,
                average_task_duration=0.0,
                error_rate=1.0,
                retry_rate=0.0,
                autonomous_decision_rate=0.0,
                container_execution_success_rate=0.0,
                resource_utilization={},
                quality_score=0.0,
                user_satisfaction=0.0,
                improvement_trends={},
            )

    def generate_optimization_recommendations(
        self, workflow_state, metrics: PerformanceMetrics
    ) -> List[WorkflowOptimization]:
        """Generate intelligent optimization recommendations."""
        try:
            recommendations = []

            # Performance optimization
            if metrics.task_completion_rate < 0.8:
                recommendations.append(
                    WorkflowOptimization(
                        strategy=OptimizationStrategy.PERFORMANCE,
                        task_id="performance_improvement",
                        recommendation="Implement parallel task execution for independent tasks",
                        expected_improvement=0.25,
                        confidence=0.8,
                        implementation_effort="medium",
                        priority="high",
                        reasoning=f"Current completion rate {metrics.task_completion_rate:.2f} is below target 0.8",
                        metrics_impact={
                            "completion_rate": 0.25,
                            "duration": -0.3,
                            "resource_efficiency": 0.15,
                        },
                    )
                )

            # Reliability optimization
            if metrics.error_rate > 0.1:
                recommendations.append(
                    WorkflowOptimization(
                        strategy=OptimizationStrategy.RELIABILITY,
                        task_id="error_reduction",
                        recommendation="Increase retry attempts and add circuit breaker timeouts",
                        expected_improvement=0.5,
                        confidence=0.9,
                        implementation_effort="low",
                        priority="high",
                        reasoning=f"Error rate {metrics.error_rate:.2f} exceeds acceptable threshold 0.1",
                        metrics_impact={
                            "error_rate": -0.5,
                            "retry_rate": 0.1,
                            "quality_score": 0.2,
                        },
                    )
                )

            # Speed optimization
            if metrics.average_task_duration > 300:  # 5 minutes
                recommendations.append(
                    WorkflowOptimization(
                        strategy=OptimizationStrategy.SPEED,
                        task_id="speed_improvement",
                        recommendation="Optimize container startup time and cache frequently used images",
                        expected_improvement=0.4,
                        confidence=0.7,
                        implementation_effort="medium",
                        priority="medium",
                        reasoning=f"Average task duration {metrics.average_task_duration:.1f}s exceeds target 300s",
                        metrics_impact={
                            "duration": -0.4,
                            "resource_efficiency": 0.2,
                            "user_satisfaction": 0.15,
                        },
                    )
                )

            # Quality optimization
            if metrics.quality_score < 0.8:
                recommendations.append(
                    WorkflowOptimization(
                        strategy=OptimizationStrategy.QUALITY,
                        task_id="quality_improvement",
                        recommendation="Implement comprehensive validation checks and enhanced testing",
                        expected_improvement=0.3,
                        confidence=0.85,
                        implementation_effort="high",
                        priority="medium",
                        reasoning=f"Quality score {metrics.quality_score:.2f} below target 0.8",
                        metrics_impact={
                            "quality_score": 0.3,
                            "error_rate": -0.2,
                            "user_satisfaction": 0.25,
                        },
                    )
                )

            # Resource efficiency optimization
            max_resource_usage = (
                max(metrics.resource_utilization.values())
                if metrics.resource_utilization
                else 0
            )
            if max_resource_usage > 0.8:
                recommendations.append(
                    WorkflowOptimization(
                        strategy=OptimizationStrategy.RESOURCE_EFFICIENCY,
                        task_id="resource_optimization",
                        recommendation="Implement resource pooling and optimize container resource limits",
                        expected_improvement=0.3,
                        confidence=0.75,
                        implementation_effort="high",
                        priority="low",
                        reasoning=f"Maximum resource usage {max_resource_usage:.2f} exceeds threshold 0.8",
                        metrics_impact={
                            "resource_efficiency": 0.3,
                            "cost": -0.25,
                            "scalability": 0.4,
                        },
                    )
                )

            # Sort recommendations by priority and expected improvement
            recommendations.sort(
                key=lambda x: (
                    {"high": 3, "medium": 2, "low": 1}[x.priority],
                    x.expected_improvement,
                ),
                reverse=True,
            )

            logger.info(
                f"Generated {len(recommendations)} optimization recommendations"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []

    def apply_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ) -> bool:
        """Apply optimization recommendation to workflow."""
        # Record optimization attempt - initialize outside try block
        optimization_record = {
            "timestamp": datetime.now(),
            "optimization": asdict(optimization),
            "workflow_id": (workflow_state.task_id if workflow_state is not None else None),
            "applied": True,
            "result": "pending",
        }
        
        try:
            logger.info(f"Applying optimization: {optimization.strategy.value}")

            # Apply strategy-specific optimizations
            if optimization.strategy == OptimizationStrategy.PERFORMANCE:
                self._apply_performance_optimization(optimization, workflow_state)
            elif optimization.strategy == OptimizationStrategy.RELIABILITY:
                self._apply_reliability_optimization(optimization, workflow_state)
            elif optimization.strategy == OptimizationStrategy.SPEED:
                self._apply_speed_optimization(optimization, workflow_state)
            elif optimization.strategy == OptimizationStrategy.QUALITY:
                self._apply_quality_optimization(optimization, workflow_state)
            elif optimization.strategy == OptimizationStrategy.RESOURCE_EFFICIENCY:
                self._apply_resource_optimization(optimization, workflow_state)

            optimization_record["result"] = "success"
            self.optimization_history.append(optimization_record)

            logger.info(
                f"Optimization {optimization.strategy.value} applied successfully"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to apply optimization {optimization.strategy.value}: {e}"
            )
            optimization_record["result"] = f"failed: {e}"
            self.optimization_history.append(optimization_record)
            return False

    def _apply_performance_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ):
        """Apply performance-specific optimizations."""
        # Identify independent tasks that can be parallelized
        independent_tasks = []
        for task in workflow_state.tasks:
            if not task.dependencies or all(
                (dep_task.status if dep_task is not None else None) == "completed"
                for dep_task in workflow_state.tasks
                if dep_task.id in task.dependencies
            ):
                independent_tasks.append(task)

        # Mark tasks for parallel execution (would be implemented in execution engine)
        for task in independent_tasks:
            if hasattr(task, "execution_mode"):
                task.execution_mode = "parallel"

        logger.info(f"Marked {len(independent_tasks)} tasks for parallel execution")

    def _apply_reliability_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ):
        """Apply reliability-specific optimizations."""
        # Increase retry limits for critical tasks
        for task in workflow_state.tasks:
            if task.priority == "high":
                task.max_retries = min(task.max_retries + 2, 5)
                task.timeout_seconds = min(
                    task.timeout_seconds * 1.5, 900
                )  # Max 15 minutes

        # Update circuit breaker settings
        if self.workflow_master and hasattr(self.workflow_master, "execution_circuit_breaker"):
            self.workflow_master.execution_circuit_breaker.timeout = 900  # 15 minutes

        logger.info("Applied reliability optimizations: increased retries and timeouts")

    def _apply_speed_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ):
        """Apply speed-specific optimizations."""
        # Reduce timeout for non-critical tasks
        for task in workflow_state.tasks:
            if task.priority != "high":
                task.timeout_seconds = max(
                    task.timeout_seconds * 0.8, 60
                )  # Min 1 minute

        # Optimize container policy for faster startup
        for task in workflow_state.tasks:
            if task.container_policy == "development":
                task.container_policy = "standard"  # Faster startup

        logger.info(
            "Applied speed optimizations: reduced timeouts and optimized container policies"
        )

    def _apply_quality_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ):
        """Apply quality-specific optimizations."""
        # Add validation steps for critical tasks
        validation_tasks = []
        for task in workflow_state.tasks:
            if task.priority == "high" and task.name in ["implementation", "testing"]:
                validation_task = {
                    "id": f"{task.id}_validation",
                    "name": f"{task.name}_validation",
                    "description": f"Validation for {getattr(task, 'description', '')}",
                    "phase": getattr(task, "phase", None),
                    "priority": "medium",
                    "dependencies": [task.id],
                    "estimated_minutes": 5,
                }
                validation_tasks.append(validation_task)

        # Add validation tasks to workflow
        workflow_state.tasks.extend(validation_tasks)

        logger.info(
            f"Added {len(validation_tasks)} validation tasks for quality assurance"
        )

    def _apply_resource_optimization(
        self, optimization: WorkflowOptimization, workflow_state
    ):
        """Apply resource efficiency optimizations."""
        # Optimize container policies for resource usage
        for task in workflow_state.tasks:
            if task.container_policy == "development":
                task.container_policy = "minimal"  # Lower resource usage

        # Implement resource pooling (would be implemented in container executor)
        logger.info("Applied resource optimizations: optimized container policies")

    def continuous_learning(
        self,
        workflow_state,
        metrics_before: PerformanceMetrics,
        metrics_after: PerformanceMetrics,
    ):
        """Implement continuous learning from optimization results."""
        try:
            # Calculate improvement deltas
            improvements = {
                "completion_rate": metrics_after.task_completion_rate
                - metrics_before.task_completion_rate,
                "error_rate": metrics_before.error_rate
                - metrics_after.error_rate,  # Reduction is good
                "quality_score": metrics_after.quality_score
                - metrics_before.quality_score,
                "user_satisfaction": metrics_after.user_satisfaction
                - metrics_before.user_satisfaction,
            }

            # Update learning data
            workflow_type = self._categorize_workflow(workflow_state)
            if workflow_type not in self.learning_data:
                self.learning_data[workflow_type] = {
                    "successful_optimizations": [],
                    "failed_optimizations": [],
                    "performance_patterns": [],
                }

            # Record successful optimizations
            for opt_record in self.optimization_history[-5:]:  # Last 5 optimizations
                if opt_record["result"] == "success":
                    self.learning_data[workflow_type][
                        "successful_optimizations"
                    ].append(
                        {
                            "optimization": opt_record["optimization"],
                            "improvements": improvements,
                            "timestamp": opt_record["timestamp"],
                        }
                    )

            # Detect performance patterns
            pattern = {
                "workflow_size": len(workflow_state.tasks),
                "complexity": self._calculate_workflow_complexity(workflow_state),
                "improvements": improvements,
                "timestamp": datetime.now(),
            }
            self.learning_data[workflow_type]["performance_patterns"].append(pattern)

            # Prune old learning data (keep last 100 records)
            for category in self.learning_data[workflow_type]:
                if len(self.learning_data[workflow_type][category]) > 100:
                    self.learning_data[workflow_type][category] = self.learning_data[
                        workflow_type
                    ][category][-100:]

            logger.info(
                f"Continuous learning updated for workflow type: {workflow_type}"
            )

        except Exception as e:
            logger.error(f"Continuous learning failed: {e}")

    def _categorize_workflow(self, workflow_state) -> str:
        """Categorize workflow for learning purposes."""
        task_count = len(workflow_state.tasks)
        if task_count <= 5:
            return "simple"
        elif task_count <= 10:
            return "medium"
        else:
            return "complex"

    def _calculate_workflow_complexity(self, workflow_state) -> float:
        """Calculate workflow complexity score."""
        # Simple complexity calculation based on tasks and dependencies
        task_count = len(workflow_state.tasks)
        dependency_count = sum(len(task.dependencies) for task in workflow_state.tasks)
        error_count = workflow_state.error_count

        complexity = (
            task_count * 0.4 + dependency_count * 0.4 + error_count * 0.2
        ) / 10
        return min(complexity, 1.0)

    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights from optimization history and learning data."""
        try:
            insights = {
                "total_optimizations_applied": len(self.optimization_history),
                "successful_optimizations": len(
                    [
                        opt
                        for opt in self.optimization_history
                        if opt["result"] == "success"
                    ]
                ),
                "most_effective_strategies": self._get_most_effective_strategies(),
                "learning_data_summary": self._summarize_learning_data(),
                "recommendations_for_future": self._generate_future_recommendations(),
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to generate optimization insights: {e}")
            return {}

    def _get_most_effective_strategies(self) -> List[Dict[str, Any]]:
        """Identify most effective optimization strategies."""
        strategy_effectiveness = {}

        for opt_record in self.optimization_history:
            if opt_record["result"] == "success":
                strategy = opt_record["optimization"]["strategy"]
                expected_improvement = opt_record["optimization"][
                    "expected_improvement"
                ]

                if strategy not in strategy_effectiveness:
                    strategy_effectiveness[strategy] = {
                        "count": 0,
                        "total_improvement": 0.0,
                        "average_improvement": 0.0,
                    }

                strategy_effectiveness[strategy]["count"] += 1
                strategy_effectiveness[strategy]["total_improvement"] += (
                    expected_improvement
                )
                strategy_effectiveness[strategy]["average_improvement"] = (
                    strategy_effectiveness[strategy]["total_improvement"]
                    / strategy_effectiveness[strategy]["count"]
                )

        # Sort by average improvement
        sorted_strategies = sorted(
            strategy_effectiveness.items(),
            key=lambda x: x[1]["average_improvement"],
            reverse=True,
        )

        return [
            {
                "strategy": strategy,
                "effectiveness": data["average_improvement"],
                "applications": data["count"],
            }
            for strategy, data in sorted_strategies[:3]  # Top 3
        ]

    def _summarize_learning_data(self) -> Dict[str, Any]:
        """Summarize learning data across workflow types."""
        summary = {}

        for workflow_type, data in self.learning_data.items():
            summary[workflow_type] = {
                "successful_optimizations": len(data["successful_optimizations"]),
                "performance_patterns": len(data["performance_patterns"]),
                "average_improvements": self._calculate_average_improvements(data),
            }

        return summary

    def _calculate_average_improvements(self, learning_data: Dict) -> Dict[str, float]:
        """Calculate average improvements from learning data."""
        if not learning_data["performance_patterns"]:
            return {}

        improvements = learning_data["performance_patterns"]
        avg_improvements = {}

        for metric in [
            "completion_rate",
            "error_rate",
            "quality_score",
            "user_satisfaction",
        ]:
            values = [
                pattern["improvements"].get(metric, 0.0)
                for pattern in improvements
                if "improvements" in pattern
            ]
            avg_improvements[metric] = sum(values) / len(values) if values else 0.0

        return avg_improvements

    def _generate_future_recommendations(self) -> List[str]:
        """Generate recommendations for future optimization."""
        recommendations = []

        # Analyze optimization history
        if len(self.optimization_history) > 0:
            success_rate = len(
                [opt for opt in self.optimization_history if opt["result"] == "success"]
            ) / len(self.optimization_history)

            if success_rate < 0.7:
                recommendations.append(
                    "Consider more conservative optimization parameters to improve success rate"
                )

        # Analyze learning data
        for workflow_type, data in self.learning_data.items():
            if len(data["successful_optimizations"]) > 5:
                recommendations.append(
                    f"Continue applying proven optimization strategies for {workflow_type} workflows"
                )

        if not recommendations:
            recommendations.append(
                "Continue monitoring and collecting performance data"
            )

        return recommendations

    def save_integration_state(self, file_path: str):
        """Save TeamCoach integration state."""
        try:
            state_data = {
                "metrics_history": [
                    {
                        "timestamp": record["timestamp"].isoformat(),
                        "metrics": asdict(record["metrics"]),
                        "workflow_id": record["workflow_id"],
                    }
                    for record in self.metrics_history
                ],
                "optimization_history": [
                    {**record, "timestamp": record["timestamp"].isoformat()}
                    for record in self.optimization_history
                ],
                "learning_data": self.learning_data,
                "config": self.config,
            }

            with open(file_path, "w") as f:
                json.dump(state_data, f, indent=2, default=str)

            logger.info(f"TeamCoach integration state saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save integration state: {e}")

    def load_integration_state(self, file_path: str):
        """Load TeamCoach integration state."""
        try:
            with open(file_path, "r") as f:
                state_data = json.load(f)

            # Restore metrics history
            self.metrics_history = []
            for record in state_data.get("metrics_history", []):
                # Convert timestamp back to datetime
                record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                # Convert metrics dict back to PerformanceMetrics
                metrics_dict = record["metrics"]
                record["metrics"] = PerformanceMetrics(**metrics_dict)
                self.metrics_history.append(record)

            # Restore optimization history
            self.optimization_history = []
            for record in state_data.get("optimization_history", []):
                record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                self.optimization_history.append(record)

            # Restore learning data and config
            self.learning_data = state_data.get("learning_data", {})
            self.config.update(state_data.get("config", {}))

            logger.info(f"TeamCoach integration state loaded from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load integration state: {e}")


# Integration helper functions
def create_teamcoach_integration(
    config: Optional[Dict[str, Any]] = None
):
    """Create TeamCoach integration for WorkflowMaster."""
    return TeamCoachIntegration(config)


def optimize_workflow_with_teamcoach(
    workflow_state, config: Optional[Dict[str, Any]] = None
):
    """Optimize workflow using TeamCoach integration."""
    integration = TeamCoachIntegration(config)

    # Analyze current performance
    metrics_before = integration.analyze_workflow_performance(workflow_state)

    # Generate recommendations
    recommendations = integration.generate_optimization_recommendations(
        workflow_state, metrics_before
    )

    # Apply optimizations (if auto-apply is enabled)
    applied_optimizations = []
    if integration is not None and integration.auto_apply_optimizations:
        for recommendation in recommendations[:3]:  # Apply top 3
            if integration.apply_optimization(recommendation, workflow_state):
                applied_optimizations.append(recommendation)

    # Analyze performance after optimizations
    metrics_after = integration.analyze_workflow_performance(workflow_state)

    # Update learning
    if applied_optimizations:
        integration.continuous_learning(workflow_state, metrics_before, metrics_after)

    return {
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
        "recommendations": recommendations,
        "applied_optimizations": applied_optimizations,
        "insights": integration.get_optimization_insights(),
    }
