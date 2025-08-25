from datetime import timedelta
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

# Import shared modules
from ...shared.task_tracking import TaskMetrics
from ...shared.utils.error_handling import ErrorHandler, CircuitBreaker
from ...shared.state_management import StateManager

"""
TeamCoach Phase 1: Metrics Collection Infrastructure

This module provides comprehensive data collection infrastructure for agent and team
performance metrics. The MetricsCollector class manages real-time data gathering,
storage, aggregation, and retrieval for performance analysis and coaching.

Key Features:
- Real-time metrics collection
- Multi-source data aggregation
- Efficient storage and retrieval
- Data validation and cleaning
- Performance monitoring hooks
- Extensible metric definitions
"""


# Import shared modules


class MetricType(Enum):
    """Types of metrics collected"""

    PERFORMANCE = "performance"
    RESOURCE = "resource"
    QUALITY = "quality"
    COLLABORATION = "collaboration"
    TIMING = "timing"
    SYSTEM = "system"


class MetricSource(Enum):
    """Sources of metric data"""

    AGENT_DIRECT = "agent_direct"
    TASK_TRACKING = "task_tracking"
    SYSTEM_MONITOR = "system_monitor"
    USER_FEEDBACK = "user_feedback"
    COLLABORATION_TRACKER = "collaboration_tracker"
    EXTERNAL_API = "external_api"


@dataclass
class MetricDefinition:
    """Definition of a collectible metric"""

    name: str
    metric_type: MetricType
    source: MetricSource
    unit: str
    description: str
    collection_frequency: timedelta
    aggregation_method: str = "avg"  # avg, sum, count, max, min
    retention_period: Optional[timedelta] = field(default_factory=lambda: timedelta(days=90))
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricDataPoint:
    """Individual metric data point"""

    metric_name: str
    agent_id: str
    timestamp: datetime
    value: Union[float, int, str, bool]
    source: MetricSource
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric data"""

    metric_name: str
    agent_id: str
    aggregation_period: Tuple[datetime, datetime]
    aggregated_value: float
    data_point_count: int
    aggregation_method: str
    confidence_score: float = 1.0


class MetricsCollector:
    """
    Comprehensive metrics collection infrastructure.

    Manages real-time collection, storage, and retrieval of performance metrics
    from multiple sources. Provides hooks for real-time monitoring and alerting.
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        task_metrics: Optional[TaskMetrics] = None,
        error_handler: Optional[ErrorHandler] = None,
        enable_real_time: bool = True,
    ):
        """
        Initialize the metrics collector.

        Args:
            state_manager: State management for persistent storage
            task_metrics: Task tracking integration
            error_handler: Error handling for robust operation
            enable_real_time: Enable real-time collection
        """
        self.logger = logging.getLogger(__name__)
        self.state_manager = state_manager or StateManager()
        self.task_metrics = task_metrics or TaskMetrics()
        self.error_handler = error_handler or ErrorHandler()
        self.enable_real_time = enable_real_time

        # Circuit breaker for collection operations
        self.collection_circuit_breaker = CircuitBreaker(
            failure_threshold=5, timeout=300, name="metrics_collection"
        )

        # Metric definitions
        self.metric_definitions: Dict[str, MetricDefinition] = {}

        # Data storage
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.aggregated_data: Dict[str, List[AggregatedMetric]] = defaultdict(list)

        # Collection infrastructure
        self.collection_hooks: Dict[MetricSource, List[Callable]] = defaultdict(list)
        self.collection_threads: Dict[str, threading.Thread] = {}
        self.stop_collection = threading.Event()

        # Performance tracking
        self.collection_stats = {
            "total_collected": 0,
            "collection_errors": 0,
            "last_collection": None,
            "collection_rate": 0.0,
        }

        # Initialize default metrics
        self._initialize_default_metrics()

        # Start real-time collection if enabled
        if self is not None and self.enable_real_time:
            self._start_real_time_collection()

        self.logger.info("MetricsCollector initialized")

    def _initialize_default_metrics(self) -> None:
        """Initialize default metric definitions."""
        default_metrics = [
            # Performance metrics
            MetricDefinition(
                name="task_success_rate",
                metric_type=MetricType.PERFORMANCE,
                source=MetricSource.TASK_TRACKING,
                unit="percentage",
                description="Percentage of successfully completed tasks",
                collection_frequency=timedelta(minutes=5),
            ),
            MetricDefinition(
                name="task_execution_time",
                metric_type=MetricType.TIMING,
                source=MetricSource.TASK_TRACKING,
                unit="seconds",
                description="Time taken to complete tasks",
                collection_frequency=timedelta(minutes=1),
            ),
            MetricDefinition(
                name="code_quality_score",
                metric_type=MetricType.QUALITY,
                source=MetricSource.TASK_TRACKING,
                unit="score",
                description="Quality score of generated code",
                collection_frequency=timedelta(minutes=10),
            ),
            # Resource metrics
            MetricDefinition(
                name="memory_usage",
                metric_type=MetricType.RESOURCE,
                source=MetricSource.SYSTEM_MONITOR,
                unit="MB",
                description="Memory usage during task execution",
                collection_frequency=timedelta(seconds=30),
            ),
            MetricDefinition(
                name="cpu_usage",
                metric_type=MetricType.RESOURCE,
                source=MetricSource.SYSTEM_MONITOR,
                unit="percentage",
                description="CPU usage during task execution",
                collection_frequency=timedelta(seconds=30),
            ),
            # Collaboration metrics
            MetricDefinition(
                name="collaboration_frequency",
                metric_type=MetricType.COLLABORATION,
                source=MetricSource.COLLABORATION_TRACKER,
                unit="count",
                description="Number of collaborative interactions",
                collection_frequency=timedelta(minutes=15),
            ),
            MetricDefinition(
                name="communication_effectiveness",
                metric_type=MetricType.COLLABORATION,
                source=MetricSource.COLLABORATION_TRACKER,
                unit="score",
                description="Effectiveness of agent communication",
                collection_frequency=timedelta(minutes=30),
            ),
        ]

        for metric in default_metrics:
            self.register_metric(metric)

    def register_metric(self, metric_definition: MetricDefinition) -> None:
        """
        Register a new metric for collection.

        Args:
            metric_definition: Definition of the metric to collect
        """
        try:
            self.metric_definitions[metric_definition.name] = metric_definition
            self.logger.info(f"Registered metric: {metric_definition.name}")

            # Initialize storage for the metric
            if metric_definition.name not in self.metric_data:
                self.metric_data[metric_definition.name] = deque(maxlen=10000)

        except Exception as e:
            self.logger.error(
                f"Failed to register metric {metric_definition.name}: {e}"
            )

    @ErrorHandler.with_circuit_breaker
    def collect_metric(
        self,
        metric_name: str,
        agent_id: str,
        value: Union[float, int, str, bool],
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Collect a single metric data point.

        Args:
            metric_name: Name of the metric
            agent_id: Agent the metric is for
            value: Metric value
            context: Additional context data
            timestamp: When the metric was recorded (default: now)

        Returns:
            bool: True if collection succeeded
        """
        try:
            if metric_name not in self.metric_definitions:
                self.logger.warning(f"Unknown metric: {metric_name}")
                return False

            metric_def = self.metric_definitions[metric_name]

            # Validate the metric value
            if not self._validate_metric_value(metric_def, value):
                self.logger.warning(f"Invalid value for metric {metric_name}: {value}")
                return False

            # Create data point
            data_point = MetricDataPoint(
                metric_name=metric_name,
                agent_id=agent_id,
                timestamp=timestamp or datetime.now(),
                value=value,
                source=metric_def.source,
                context=context or {},
                metadata={
                    "collected_at": datetime.now().isoformat(),
                    "collector_version": "1.0.0",
                },
            )

            # Store the data point
            self.metric_data[metric_name].append(data_point)

            # Update collection stats
            self.collection_stats["total_collected"] += 1
            self.collection_stats["last_collection"] = datetime.now()

            # Trigger real-time hooks if enabled
            if self is not None and self.enable_real_time:
                self._trigger_real_time_hooks(data_point)

            self.logger.debug(
                f"Collected metric {metric_name} for agent {agent_id}: {value}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to collect metric {metric_name}: {e}")
            self.collection_stats["collection_errors"] += 1
            return False

    def collect_metrics_batch(
        self,
        metrics: List[Tuple[str, str, Union[float, int, str, bool], Dict[str, Any]]],
    ) -> int:
        """
        Collect multiple metrics in a batch.

        Args:
            metrics: List of (metric_name, agent_id, value, context) tuples

        Returns:
            int: Number of successfully collected metrics
        """
        try:
            success_count = 0

            for metric_name, agent_id, value, context in metrics:
                if self.collect_metric(metric_name, agent_id, value, context):
                    success_count += 1

            self.logger.info(f"Batch collected {success_count}/{len(metrics)} metrics")
            return success_count

        except Exception as e:
            self.logger.error(f"Failed to collect metrics batch: {e}")
            return 0

    def get_metric_data(
        self,
        metric_name: str,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[MetricDataPoint]:
        """
        Retrieve metric data points.

        Args:
            metric_name: Name of the metric
            agent_id: Filter by agent ID (optional)
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            limit: Maximum number of data points (optional)

        Returns:
            List[MetricDataPoint]: Matching data points
        """
        try:
            if metric_name not in self.metric_data:
                return []

            data_points = list(self.metric_data[metric_name])

            # Apply filters
            if agent_id:
                data_points = [dp for dp in data_points if dp.agent_id == agent_id]

            if start_time:
                data_points = [dp for dp in data_points if dp.timestamp >= start_time]

            if end_time:
                data_points = [dp for dp in data_points if dp.timestamp <= end_time]

            # Sort by timestamp
            data_points.sort(key=lambda dp: dp.timestamp)

            # Apply limit
            if limit:
                data_points = data_points[-limit:]

            return data_points

        except Exception as e:
            self.logger.error(f"Failed to get metric data for {metric_name}: {e}")
            return []

    def aggregate_metric(
        self,
        metric_name: str,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        aggregation_method: Optional[str] = None,
    ) -> Optional[AggregatedMetric]:
        """
        Aggregate metric data over a time period.

        Args:
            metric_name: Name of the metric
            agent_id: Filter by agent ID (optional)
            start_time: Start of aggregation period
            end_time: End of aggregation period
            aggregation_method: Method to use (avg, sum, count, max, min)

        Returns:
            AggregatedMetric: Aggregated result
        """
        try:
            if metric_name not in self.metric_definitions:
                return None

            metric_def = self.metric_definitions[metric_name]
            method = aggregation_method or metric_def.aggregation_method

            # Get data points
            data_points = self.get_metric_data(
                metric_name, agent_id, start_time, end_time
            )

            if not data_points:
                return None

            # Extract numeric values
            values = []
            for dp in data_points:
                if isinstance(dp.value, (int, float)):
                    values.append(float(dp.value))

            if not values:
                return None

            # Calculate aggregated value
            if method == "avg":
                aggregated_value = sum(values) / len(values)
            elif method == "sum":
                aggregated_value = sum(values)
            elif method == "count":
                aggregated_value = len(values)
            elif method == "max":
                aggregated_value = max(values)
            elif method == "min":
                aggregated_value = min(values)
            else:
                aggregated_value = sum(values) / len(values)  # Default to average

            # Calculate confidence score based on data point count
            confidence_score = min(1.0, len(data_points) / 10.0)

            # Determine time period
            if start_time and end_time:
                period = (start_time, end_time)
            elif data_points:
                period = (data_points[0].timestamp, data_points[-1].timestamp)
            else:
                period = (datetime.now(), datetime.now())

            return AggregatedMetric(
                metric_name=metric_name,
                agent_id=agent_id or "all_agents",
                aggregation_period=period,
                aggregated_value=aggregated_value,
                data_point_count=len(data_points),
                aggregation_method=method,
                confidence_score=confidence_score,
            )

        except Exception as e:
            self.logger.error(f"Failed to aggregate metric {metric_name}: {e}")
            return None

    def get_agent_metrics_summary(
        self, agent_id: str, time_period: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary for an agent.

        Args:
            agent_id: Agent to get summary for
            time_period: Time window for analysis

        Returns:
            Dict: Metrics summary
        """
        try:
            if time_period:
                start_time, end_time = time_period
            else:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)

            summary = {
                "agent_id": agent_id,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "metrics": {},
            }

            # Aggregate all metrics for the agent
            for metric_name in self.metric_definitions:
                aggregated = self.aggregate_metric(
                    metric_name, agent_id, start_time, end_time
                )

                if aggregated:
                    summary["metrics"][metric_name] = {
                        "value": aggregated.aggregated_value,
                        "data_points": aggregated.data_point_count,
                        "confidence": aggregated.confidence_score,
                        "method": aggregated.aggregation_method,
                    }

            return summary

        except Exception as e:
            self.logger.error(
                f"Failed to get metrics summary for agent {agent_id}: {e}"
            )
            return {}

    def register_collection_hook(
        self, source: MetricSource, hook_function: Callable[[MetricDataPoint], None]
    ) -> None:
        """
        Register a hook for real-time metric collection.

        Args:
            source: Metric source to hook into
            hook_function: Function to call when metrics are collected
        """
        try:
            self.collection_hooks[source].append(hook_function)
            self.logger.info(f"Registered collection hook for source {source.value}")

        except Exception as e:
            self.logger.error(f"Failed to register collection hook: {e}")

    def _validate_metric_value(
        self, metric_def: MetricDefinition, value: Union[float, int, str, bool]
    ) -> bool:
        """Validate a metric value against its definition rules."""
        try:
            validation_rules = metric_def.validation_rules

            # Type validation
            if "type" in validation_rules:
                expected_type = validation_rules["type"]
                if not isinstance(value, expected_type):
                    return False

            # Range validation for numeric values
            if isinstance(value, (int, float)):
                if (
                    "min_value" in validation_rules
                    and value < validation_rules["min_value"]
                ):
                    return False
                if (
                    "max_value" in validation_rules
                    and value > validation_rules["max_value"]
                ):
                    return False

            # String validation
            if isinstance(value, str):
                if (
                    "max_length" in validation_rules
                    and len(value) > validation_rules["max_length"]
                ):
                    return False
                if (
                    "allowed_values" in validation_rules
                    and value not in validation_rules["allowed_values"]
                ):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate metric value: {e}")
            return False

    def _trigger_real_time_hooks(self, data_point: MetricDataPoint) -> None:
        """Trigger real-time hooks for a collected data point."""
        try:
            hooks = self.collection_hooks.get(data_point.source, [])
            for hook in hooks:
                try:
                    hook(data_point)
                except Exception as e:
                    self.logger.error(f"Hook execution failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to trigger real-time hooks: {e}")

    def _start_real_time_collection(self) -> None:
        """Start real-time metric collection threads."""
        try:
            # Start collection thread for each metric source
            for source in MetricSource:
                thread_name = f"collector_{source.value}"
                if thread_name not in self.collection_threads:
                    thread = threading.Thread(
                        target=self._collection_worker,
                        args=(source,),
                        name=thread_name,
                        daemon=True,
                    )
                    thread.start()
                    self.collection_threads[thread_name] = thread

            self.logger.info("Started real-time metric collection")

        except Exception as e:
            self.logger.error(f"Failed to start real-time collection: {e}")

    def _collection_worker(self, source: MetricSource) -> None:
        """Worker thread for collecting metrics from a specific source."""
        try:
            while not self.stop_collection.is_set():
                try:
                    # Collection logic would be implemented here based on source
                    if source == MetricSource.TASK_TRACKING:
                        self._collect_task_tracking_metrics()
                    elif source == MetricSource.SYSTEM_MONITOR:
                        self._collect_system_metrics()
                    elif source == MetricSource.COLLABORATION_TRACKER:
                        self._collect_collaboration_metrics()

                    # Sleep based on the shortest collection frequency for this source
                    sleep_time = self._get_min_collection_frequency(source)
                    self.stop_collection.wait(sleep_time.total_seconds())

                except Exception as e:
                    self.logger.error(
                        f"Error in collection worker for {source.value}: {e}"
                    )
                    self.stop_collection.wait(60)  # Wait 1 minute on error

        except Exception as e:
            self.logger.error(f"Collection worker {source.value} failed: {e}")

    def _collect_task_tracking_metrics(self) -> None:
        """Collect metrics from task tracking system."""
        try:
            # This would integrate with the task tracking system
            # For now, just a placeholder implementation
            pass

        except Exception as e:
            self.logger.error(f"Failed to collect task tracking metrics: {e}")

    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # This would collect system metrics like CPU, memory usage
            # For now, just a placeholder implementation
            pass

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    def _collect_collaboration_metrics(self) -> None:
        """Collect collaboration metrics."""
        try:
            # This would collect collaboration and communication metrics
            # For now, just a placeholder implementation
            pass

        except Exception as e:
            self.logger.error(f"Failed to collect collaboration metrics: {e}")

    def _get_min_collection_frequency(self, source: MetricSource) -> timedelta:
        """Get the minimum collection frequency for a source."""
        min_frequency = timedelta(minutes=5)  # Default 5 minutes

        for metric_def in self.metric_definitions.values():
            if metric_def.source == source:
                if metric_def.collection_frequency < min_frequency:
                    min_frequency = metric_def.collection_frequency

        return min_frequency

    def cleanup_old_data(self, retention_period: Optional[timedelta] = None) -> int:
        """
        Clean up old metric data points.

        Args:
            retention_period: Data older than this will be removed

        Returns:
            int: Number of data points removed
        """
        try:
            if retention_period is None:
                retention_period = timedelta(days=90)

            cutoff_time = datetime.now() - retention_period
            removed_count = 0

            for metric_name, data_deque in self.metric_data.items():
                # Convert to list for processing
                data_list = list(data_deque)
                filtered_data = [dp for dp in data_list if dp.timestamp >= cutoff_time]

                removed = len(data_list) - len(filtered_data)
                removed_count += removed

                # Update deque
                data_deque.clear()
                data_deque.extend(filtered_data)

            self.logger.info(f"Cleaned up {removed_count} old data points")
            return removed_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0

    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get metrics collection statistics."""
        try:
            stats = self.collection_stats.copy()
            stats["active_metrics"] = len(self.metric_definitions)
            stats["stored_data_points"] = sum(
                len(data) for data in self.metric_data.values()
            )
            stats["collection_threads"] = len(self.collection_threads)

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get collection statistics: {e}")
            return {}

    def stop_collection(self) -> None:
        """Stop all metric collection."""
        try:
            self.stop_collection.set()

            # Wait for threads to finish
            for thread in self.collection_threads.values():
                thread.join(timeout=5.0)

            self.logger.info("Stopped metric collection")

        except Exception as e:
            self.logger.error(f"Failed to stop collection: {e}")

    def __del__(self):
        """Cleanup when collector is destroyed."""
        try:
            self.stop_collection()
        except Exception:
            pass  # Ignore errors during cleanup
