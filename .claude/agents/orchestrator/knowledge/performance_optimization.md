# Performance Optimization Knowledge Base


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview

This document contains learned strategies and techniques for optimizing parallel task execution performance in the Orchestrator V0.3. It includes dynamic optimization algorithms, resource management strategies, and adaptive performance tuning based on real-time metrics.

## Performance Metrics and Targets

### Key Performance Indicators (KPIs)

#### Throughput Metrics
- **Tasks per minute**: Target > 20 for simple tasks, > 5 for complex tasks
- **Parallel efficiency**: Target > 70% (ideal work / actual time)
- **Resource utilization**: Target > 80% for CPU, > 60% for I/O

#### Latency Metrics
- **Task startup time**: Target < 5 seconds
- **Context switching overhead**: Target < 10% of total execution time
- **Dependency resolution time**: Target < 2 seconds for complex graphs

#### Quality Metrics
- **Success rate**: Target > 85% for all task types
- **Retry rate**: Target < 15% of tasks require retries
- **Rollback rate**: Target < 5% of executions require rollbacks

### Performance Baselines by Task Type

```yaml
performance_baselines:
  implementation_tasks:
    avg_duration: 300s
    success_rate: 0.78
    parallel_efficiency: 0.65
    resource_intensity: "cpu_bound"

  testing_tasks:
    avg_duration: 180s
    success_rate: 0.85
    parallel_efficiency: 0.80
    resource_intensity: "io_bound"

  documentation_tasks:
    avg_duration: 120s
    success_rate: 0.92
    parallel_efficiency: 0.85
    resource_intensity: "mixed"

  analysis_tasks:
    avg_duration: 150s
    success_rate: 0.88
    parallel_efficiency: 0.70
    resource_intensity: "cpu_bound"
```

## Dynamic Resource Allocation

### 1. Adaptive Worker Pool Management

**Dynamic Scaling Algorithm**:
```python
def optimize_worker_count(current_metrics, task_queue):
    cpu_utilization = current_metrics.cpu_usage
    memory_utilization = current_metrics.memory_usage
    queue_length = len(task_queue)
    avg_task_duration = current_metrics.avg_task_duration

    # Calculate optimal worker count
    if cpu_utilization > 0.9 and memory_utilization < 0.7:
        # CPU bound, scale down workers
        optimal_workers = max(2, current_workers - 1)
    elif cpu_utilization < 0.6 and memory_utilization < 0.8:
        # Underutilized, can scale up
        max_beneficial_workers = min(
            queue_length,
            available_cpu_cores * 2,  # For I/O bound tasks
            available_memory // estimated_memory_per_task
        )
        optimal_workers = min(current_workers + 2, max_beneficial_workers)
    else:
        # Maintain current level
        optimal_workers = current_workers

    return optimal_workers

def apply_resource_constraints(tasks, available_resources):
    """Apply resource constraints to task scheduling."""

    # Categorize tasks by resource requirements
    cpu_intensive = [t for t in tasks if classify_resource_type(t) == "cpu_bound"]
    io_intensive = [t for t in tasks if classify_resource_type(t) == "io_bound"]
    memory_intensive = [t for t in tasks if classify_resource_type(t) == "memory_bound"]

    # Calculate resource allocation
    cpu_slots = available_resources.cpu_cores
    io_slots = available_resources.cpu_cores * 3  # I/O can overssubscribe CPU
    memory_budget = available_resources.memory_gb

    # Allocate resources optimally
    schedule = []

    # High priority: memory intensive (limited by memory)
    memory_per_task = estimate_memory_usage(memory_intensive)
    memory_concurrent = min(
        len(memory_intensive),
        int(memory_budget / memory_per_task) if memory_per_task > 0 else len(memory_intensive)
    )
    schedule.extend(memory_intensive[:memory_concurrent])
    memory_budget -= memory_concurrent * memory_per_task

    # Medium priority: CPU intensive (limited by cores)
    cpu_concurrent = min(len(cpu_intensive), cpu_slots - memory_concurrent)
    schedule.extend(cpu_intensive[:cpu_concurrent])
    cpu_slots -= cpu_concurrent

    # Low priority: I/O intensive (can oversubscribe)
    io_concurrent = min(len(io_intensive), io_slots - len(schedule))
    schedule.extend(io_intensive[:io_concurrent])

    return schedule
```

### 2. Intelligent Task Batching

**Batch Composition Strategies**:
```python
def optimize_batch_composition(ready_tasks, constraints):
    """Create optimal batches considering resource mix and dependencies."""

    batches = []
    remaining_tasks = ready_tasks.copy()

    while remaining_tasks:
        current_batch = []
        cpu_slots = constraints.max_cpu_tasks
        io_slots = constraints.max_io_tasks
        memory_budget = constraints.memory_limit

        # Greedy batch filling with optimization
        for task in list(remaining_tasks):
            resource_type = classify_resource_type(task)
            memory_need = estimate_task_memory(task)

            # Check if task fits in current batch
            can_fit = False
            if resource_type == "cpu_bound" and cpu_slots > 0:
                can_fit = True
                cpu_slots -= 1
            elif resource_type == "io_bound" and io_slots > 0:
                can_fit = True
                io_slots -= 1
            elif resource_type == "mixed" and (cpu_slots > 0 or io_slots > 0):
                can_fit = True
                cpu_slots = max(0, cpu_slots - 1)
                io_slots = max(0, io_slots - 1)

            if can_fit and memory_need <= memory_budget:
                current_batch.append(task)
                remaining_tasks.remove(task)
                memory_budget -= memory_need

                # Stop if batch is full
                if len(current_batch) >= constraints.max_batch_size:
                    break

        if current_batch:
            batches.append(optimize_batch_order(current_batch))
        else:
            # No tasks fit - adjust constraints or force one task
            if remaining_tasks:
                batches.append([remaining_tasks.pop(0)])

    return batches

def optimize_batch_order(batch_tasks):
    """Optimize task order within a batch for better performance."""

    # Sort by multiple criteria
    def task_priority_score(task):
        return (
            task.priority * 0.3 +                    # Explicit priority
            (1.0 / max(task.predicted_duration, 1)) * 0.2 +  # Shorter first
            task.predicted_success_rate * 0.2 +      # More likely to succeed
            dependency_chain_length(task) * 0.3       # Critical path tasks first
        )

    return sorted(batch_tasks, key=task_priority_score, reverse=True)
```

### 3. Load Balancing Strategies

**Dynamic Load Distribution**:
```python
class LoadBalancer:
    def __init__(self):
        self.worker_loads = defaultdict(float)  # worker_id -> current load
        self.worker_capabilities = {}           # worker_id -> capabilities
        self.task_completion_history = []       # Historical performance data

    def assign_task_to_worker(self, task, available_workers):
        """Assign task to optimal worker based on current load and capabilities."""

        best_worker = None
        best_score = float('inf')

        for worker in available_workers:
            # Calculate assignment score (lower is better)
            load_score = self.worker_loads[worker.id]
            capability_score = self.calculate_capability_match(task, worker)
            historical_score = self.get_historical_performance(worker.id, task.task_type)

            total_score = (
                load_score * 0.4 +           # Current workload
                (1.0 - capability_score) * 0.3 +  # Capability mismatch penalty
                (1.0 - historical_score) * 0.3    # Historical performance
            )

            if total_score < best_score:
                best_score = total_score
                best_worker = worker

        # Update load tracking
        if best_worker:
            estimated_load = task.predicted_duration / 60.0  # Convert to minutes
            self.worker_loads[best_worker.id] += estimated_load

        return best_worker

    def task_completed(self, worker_id, task, actual_duration, success):
        """Update load and performance tracking when task completes."""
        estimated_load = task.predicted_duration / 60.0
        self.worker_loads[worker_id] = max(0, self.worker_loads[worker_id] - estimated_load)

        # Record performance for future assignments
        performance_record = {
            "worker_id": worker_id,
            "task_type": task.task_type,
            "predicted_duration": task.predicted_duration,
            "actual_duration": actual_duration,
            "success": success,
            "efficiency": task.predicted_duration / actual_duration if actual_duration > 0 else 0
        }
        self.task_completion_history.append(performance_record)

        # Prune old history (keep last 1000 records)
        if len(self.task_completion_history) > 1000:
            self.task_completion_history = self.task_completion_history[-1000:]
```

## Performance Monitoring and Adaptation

### 1. Real-Time Performance Tracking

**Performance Metrics Collection**:
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "throughput": RollingAverage(window_size=50),
            "latency": RollingAverage(window_size=50),
            "success_rate": RollingAverage(window_size=100),
            "resource_utilization": {},
            "bottleneck_analysis": []
        }
        self.alert_thresholds = {
            "low_throughput": 5.0,    # tasks per minute
            "high_latency": 600.0,    # seconds
            "low_success_rate": 0.7   # 70%
        }

    def record_task_completion(self, task, start_time, end_time, success):
        duration = (end_time - start_time).total_seconds()

        # Update metrics
        self.metrics["throughput"].add_sample(1.0 / duration * 60)  # tasks per minute
        self.metrics["latency"].add_sample(duration)
        self.metrics["success_rate"].add_sample(1.0 if success else 0.0)

        # Check for performance alerts
        self.check_performance_alerts()

    def check_performance_alerts(self):
        current_throughput = self.metrics["throughput"].average()
        current_latency = self.metrics["latency"].average()
        current_success_rate = self.metrics["success_rate"].average()

        alerts = []

        if current_throughput < self.alert_thresholds["low_throughput"]:
            alerts.append(f"Low throughput: {current_throughput:.1f} tasks/min")

        if current_latency > self.alert_thresholds["high_latency"]:
            alerts.append(f"High latency: {current_latency:.1f}s average")

        if current_success_rate < self.alert_thresholds["low_success_rate"]:
            alerts.append(f"Low success rate: {current_success_rate:.1%}")

        if alerts:
            self.trigger_performance_optimization(alerts)

    def trigger_performance_optimization(self, alerts):
        """Trigger automatic performance optimizations based on alerts."""

        optimization_actions = []

        for alert in alerts:
            if "low throughput" in alert.lower():
                optimization_actions.append("increase_parallelism")
            elif "high latency" in alert.lower():
                optimization_actions.append("optimize_task_scheduling")
            elif "low success rate" in alert.lower():
                optimization_actions.append("review_task_decomposition")

        return optimization_actions
```

### 2. Adaptive Algorithm Tuning

**Self-Tuning Parameters**:
```python
class AdaptiveOptimizer:
    def __init__(self):
        self.parameters = {
            "max_parallel_tasks": 8,
            "batch_size": 4,
            "dependency_confidence_threshold": 0.6,
            "retry_backoff_factor": 2.0,
            "resource_oversubscription_factor": 1.5
        }
        self.performance_history = []
        self.tuning_experiments = []

    def adapt_parameters(self, recent_performance):
        """Adapt parameters based on recent performance trends."""

        # Analyze performance trends
        if len(recent_performance) < 10:
            return  # Need more data

        success_rate_trend = self.calculate_trend([p.success_rate for p in recent_performance])
        throughput_trend = self.calculate_trend([p.throughput for p in recent_performance])
        efficiency_trend = self.calculate_trend([p.parallel_efficiency for p in recent_performance])

        # Adapt based on trends
        if success_rate_trend < -0.05:  # Success rate declining
            # Be more conservative
            self.parameters["dependency_confidence_threshold"] *= 0.9
            self.parameters["max_parallel_tasks"] = max(2, self.parameters["max_parallel_tasks"] - 1)

        elif success_rate_trend > 0.05 and throughput_trend > 0:
            # Performance improving, can be more aggressive
            self.parameters["dependency_confidence_threshold"] *= 1.05
            self.parameters["max_parallel_tasks"] = min(16, self.parameters["max_parallel_tasks"] + 1)

        if efficiency_trend < -0.1:  # Parallel efficiency declining
            # Reduce batch size to improve coordination
            self.parameters["batch_size"] = max(2, self.parameters["batch_size"] - 1)

        elif efficiency_trend > 0.1:
            # Efficiency improving, can handle larger batches
            self.parameters["batch_size"] = min(8, self.parameters["batch_size"] + 1)

        # Clamp parameters to safe ranges
        self.clamp_parameters()

    def clamp_parameters(self):
        """Ensure parameters stay within safe ranges."""
        self.parameters["max_parallel_tasks"] = max(1, min(32, self.parameters["max_parallel_tasks"]))
        self.parameters["batch_size"] = max(1, min(16, self.parameters["batch_size"]))
        self.parameters["dependency_confidence_threshold"] = max(0.1, min(0.9, self.parameters["dependency_confidence_threshold"]))
        self.parameters["retry_backoff_factor"] = max(1.1, min(5.0, self.parameters["retry_backoff_factor"]))
        self.parameters["resource_oversubscription_factor"] = max(1.0, min(3.0, self.parameters["resource_oversubscription_factor"]))
```

### 3. Bottleneck Detection and Resolution

**Automated Bottleneck Analysis**:
```python
def detect_performance_bottlenecks(execution_metrics):
    """Detect and classify performance bottlenecks."""

    bottlenecks = []

    # CPU Bottleneck Detection
    if execution_metrics.avg_cpu_utilization > 0.95:
        bottlenecks.append({
            "type": "cpu_bottleneck",
            "severity": "high",
            "description": "CPU utilization consistently above 95%",
            "suggested_actions": [
                "Reduce CPU-intensive task concurrency",
                "Optimize algorithm complexity",
                "Consider distributed processing"
            ]
        })

    # Memory Bottleneck Detection
    if execution_metrics.avg_memory_utilization > 0.9:
        bottlenecks.append({
            "type": "memory_bottleneck",
            "severity": "high",
            "description": "Memory utilization above 90%",
            "suggested_actions": [
                "Reduce memory-intensive task concurrency",
                "Implement memory pooling",
                "Add memory cleanup between tasks"
            ]
        })

    # I/O Bottleneck Detection
    if execution_metrics.avg_io_wait_time > 0.3:
        bottlenecks.append({
            "type": "io_bottleneck",
            "severity": "medium",
            "description": f"High I/O wait time: {execution_metrics.avg_io_wait_time:.1%}",
            "suggested_actions": [
                "Increase I/O task concurrency",
                "Implement async I/O patterns",
                "Add I/O caching layer"
            ]
        })

    # Dependency Bottleneck Detection
    if execution_metrics.avg_dependency_wait_time > execution_metrics.avg_task_duration * 0.5:
        bottlenecks.append({
            "type": "dependency_bottleneck",
            "severity": "high",
            "description": "Tasks spending too much time waiting for dependencies",
            "suggested_actions": [
                "Review dependency accuracy",
                "Optimize task decomposition",
                "Implement dependency caching"
            ]
        })

    # Context Switching Bottleneck
    if execution_metrics.context_switch_overhead > 0.15:
        bottlenecks.append({
            "type": "context_switching_bottleneck",
            "severity": "medium",
            "description": f"High context switching overhead: {execution_metrics.context_switch_overhead:.1%}",
            "suggested_actions": [
                "Reduce task concurrency",
                "Increase task granularity",
                "Implement task affinity"
            ]
        })

    return bottlenecks

def resolve_bottlenecks(bottlenecks, current_config):
    """Automatically resolve detected bottlenecks."""

    resolution_actions = []

    for bottleneck in bottlenecks:
        if bottleneck["type"] == "cpu_bottleneck":
            # Reduce CPU task concurrency
            new_cpu_limit = max(1, current_config.max_cpu_tasks - 2)
            resolution_actions.append({
                "action": "reduce_cpu_concurrency",
                "old_value": current_config.max_cpu_tasks,
                "new_value": new_cpu_limit
            })

        elif bottleneck["type"] == "memory_bottleneck":
            # Reduce memory-intensive task concurrency
            new_memory_limit = max(1, current_config.max_memory_tasks - 1)
            resolution_actions.append({
                "action": "reduce_memory_concurrency",
                "old_value": current_config.max_memory_tasks,
                "new_value": new_memory_limit
            })

        elif bottleneck["type"] == "io_bottleneck":
            # Increase I/O task concurrency
            new_io_limit = min(current_config.max_io_tasks + 2, current_config.max_total_tasks)
            resolution_actions.append({
                "action": "increase_io_concurrency",
                "old_value": current_config.max_io_tasks,
                "new_value": new_io_limit
            })

        elif bottleneck["type"] == "dependency_bottleneck":
            # Reduce dependency confidence threshold
            new_threshold = max(0.3, current_config.dependency_threshold - 0.1)
            resolution_actions.append({
                "action": "reduce_dependency_threshold",
                "old_value": current_config.dependency_threshold,
                "new_value": new_threshold
            })

    return resolution_actions
```

## Optimization Strategies by Task Type

### 1. CPU-Intensive Tasks

**Optimization Techniques**:
```python
cpu_intensive_optimizations = {
    "concurrency_limiting": {
        "description": "Limit to number of CPU cores",
        "max_concurrent": "cpu_cores",
        "effectiveness": 0.9
    },
    "cpu_affinity": {
        "description": "Pin tasks to specific CPU cores",
        "implementation": "process_affinity",
        "effectiveness": 0.7
    },
    "algorithm_optimization": {
        "description": "Optimize algorithmic complexity",
        "techniques": ["caching", "memoization", "pruning"],
        "effectiveness": 0.8
    }
}
```

### 2. I/O-Intensive Tasks

**Optimization Techniques**:
```python
io_intensive_optimizations = {
    "async_operations": {
        "description": "Use async I/O patterns",
        "concurrency_multiplier": 3.0,
        "effectiveness": 0.9
    },
    "connection_pooling": {
        "description": "Reuse database/API connections",
        "pool_size": "10-50",
        "effectiveness": 0.8
    },
    "caching_layer": {
        "description": "Cache frequently accessed data",
        "cache_types": ["memory", "redis", "file"],
        "effectiveness": 0.9
    },
    "batch_operations": {
        "description": "Batch multiple I/O operations",
        "batch_size": "10-100",
        "effectiveness": 0.7
    }
}
```

### 3. Memory-Intensive Tasks

**Optimization Techniques**:
```python
memory_intensive_optimizations = {
    "memory_limits": {
        "description": "Set strict memory limits per task",
        "limit_per_task": "available_memory / concurrent_tasks",
        "effectiveness": 0.9
    },
    "streaming_processing": {
        "description": "Process data in chunks",
        "chunk_size": "adaptive based on available memory",
        "effectiveness": 0.8
    },
    "garbage_collection": {
        "description": "Aggressive GC between tasks",
        "gc_strategy": "generational with forced collection",
        "effectiveness": 0.6
    }
}
```

## Advanced Performance Techniques

### 1. Predictive Scaling

**Machine Learning-Based Resource Prediction**:
```python
class PredictiveScaler:
    def __init__(self):
        self.feature_history = []
        self.performance_history = []
        self.model = None

    def predict_resource_needs(self, upcoming_tasks):
        """Predict resource requirements for upcoming tasks."""

        if not self.model or len(self.feature_history) < 50:
            # Fallback to heuristic-based prediction
            return self.heuristic_prediction(upcoming_tasks)

        # Extract features from upcoming tasks
        features = self.extract_task_features(upcoming_tasks)

        # Predict resource requirements
        predicted_resources = self.model.predict([features])[0]

        return {
            "cpu_cores_needed": predicted_resources[0],
            "memory_gb_needed": predicted_resources[1],
            "io_capacity_needed": predicted_resources[2],
            "predicted_duration": predicted_resources[3]
        }

    def update_model(self, task_features, actual_performance):
        """Update prediction model with new data."""
        self.feature_history.append(task_features)
        self.performance_history.append(actual_performance)

        # Retrain model periodically
        if len(self.feature_history) % 100 == 0:
            self.retrain_model()

    def extract_task_features(self, tasks):
        """Extract features for machine learning model."""
        return [
            len(tasks),                                    # Number of tasks
            sum(t.predicted_duration for t in tasks),     # Total duration
            len([t for t in tasks if t.task_type == "implementation"]), # Implementation tasks
            len([t for t in tasks if t.task_type == "testing"]),       # Testing tasks
            max((t.priority for t in tasks), default=0),  # Max priority
            sum(len(t.dependencies) for t in tasks),      # Total dependencies
        ]
```

### 2. Adaptive Retry Strategies

**Smart Retry Logic**:
```python
class AdaptiveRetryManager:
    def __init__(self):
        self.retry_patterns = {}
        self.failure_analysis = defaultdict(list)

    def should_retry_task(self, task, failure_info, retry_count):
        """Determine if and how to retry a failed task."""

        # Analyze failure type
        failure_type = self.classify_failure(failure_info)

        # Check historical success rate for this failure type
        historical_data = self.failure_analysis[failure_type]
        if len(historical_data) > 5:
            retry_success_rate = sum(h.retry_succeeded for h in historical_data) / len(historical_data)
            if retry_success_rate < 0.3:
                return False, "Low retry success rate for this failure type"

        # Determine retry strategy
        if failure_type == "timeout":
            # Increase timeout for retry
            new_timeout = task.timeout_seconds * (1.5 ** retry_count)
            return True, f"Retry with increased timeout: {new_timeout}s"

        elif failure_type == "resource_exhaustion":
            # Retry with reduced resource requirements
            return True, "Retry with reduced parallelism"

        elif failure_type == "dependency_failure":
            # Check if dependencies are now resolved
            deps_resolved = self.check_dependency_status(task.dependencies)
            return deps_resolved, "Retry after dependency resolution" if deps_resolved else "Dependencies still failing"

        elif failure_type == "transient_error":
            # Exponential backoff retry
            backoff_delay = min(300, 5 * (2 ** retry_count))  # Cap at 5 minutes
            return True, f"Retry after {backoff_delay}s backoff"

        else:
            # Unknown failure type - conservative retry
            return retry_count < 2, "Conservative retry for unknown failure"
```

### 3. Performance Regression Detection

**Automated Performance Regression Detection**:
```python
class RegressionDetector:
    def __init__(self):
        self.baseline_metrics = {}
        self.recent_metrics = []
        self.alert_sensitivity = 0.15  # 15% regression triggers alert

    def check_for_regressions(self, current_metrics):
        """Check if current performance shows regression."""

        regressions = []

        for metric_name, current_value in current_metrics.items():
            if metric_name in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric_name]

                # Calculate percentage change
                if baseline_value > 0:
                    change_ratio = (current_value - baseline_value) / baseline_value

                    # Check for regression (performance degradation)
                    is_regression = False
                    if metric_name in ["throughput", "success_rate", "parallel_efficiency"]:
                        # Higher is better - regression if significantly lower
                        is_regression = change_ratio < -self.alert_sensitivity
                    elif metric_name in ["latency", "error_rate", "retry_rate"]:
                        # Lower is better - regression if significantly higher
                        is_regression = change_ratio > self.alert_sensitivity

                    if is_regression:
                        regressions.append({
                            "metric": metric_name,
                            "baseline": baseline_value,
                            "current": current_value,
                            "change_percent": change_ratio * 100,
                            "severity": "high" if abs(change_ratio) > 0.3 else "medium"
                        })

        return regressions

    def update_baseline(self, metrics, force_update=False):
        """Update baseline metrics with recent good performance."""

        # Only update baseline if performance is stable and good
        if (force_update or
            (metrics.get("success_rate", 0) > 0.85 and
             metrics.get("parallel_efficiency", 0) > 0.7)):

            # Exponential moving average update
            alpha = 0.1  # Learning rate
            for metric_name, value in metrics.items():
                if metric_name in self.baseline_metrics:
                    self.baseline_metrics[metric_name] = (
                        (1 - alpha) * self.baseline_metrics[metric_name] +
                        alpha * value
                    )
                else:
                    self.baseline_metrics[metric_name] = value
```

## Best Practices and Guidelines

### 1. Resource Management
- Monitor resource utilization continuously
- Set conservative limits initially, then optimize
- Implement graceful degradation under resource pressure
- Use resource pooling for expensive operations

### 2. Task Scheduling
- Balance task granularity (not too small, not too large)
- Consider both duration and resource requirements
- Prioritize tasks on critical path
- Implement fair scheduling to prevent starvation

### 3. Error Handling and Recovery
- Implement circuit breakers for external dependencies
- Use exponential backoff for retries
- Provide fallback strategies for critical tasks
- Log detailed failure information for analysis

### 4. Monitoring and Alerting
- Set up proactive alerts for performance degradation
- Track trends, not just point-in-time metrics
- Correlate performance with resource usage
- Implement automated performance optimization triggers

### 5. Continuous Improvement
- Regularly review and update optimization strategies
- A/B test different optimization approaches
- Learn from both successes and failures
- Keep optimization logic simple and explainable

This performance optimization knowledge base is continuously refined based on real-world execution results and emerging optimization techniques.
