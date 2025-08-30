"""
Shared base classes for Gadugi multi-agent system.
These base classes provide common functionality to avoid duplication across agents.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all Gadugi agents."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"gadugi.agents.{name}")
        self.start_time = None
        self.metrics = {}

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary task."""
        pass

    def log_info(self, message: str):
        """Log informational message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str, exception: Optional[Exception] = None):
        """Log error message."""
        self.logger.error(f"[{self.name}] {message}", exc_info=exception)


class SecurityAwareAgent(BaseAgent):
    """Base class for agents that require security awareness."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.security_policies = self.config.get("security_policies", {})
        self.audit_log = []

    def validate_input(self, input_data: Any) -> bool:
        """Validate input against security policies."""
        # Basic input validation - can be extended by subclasses
        if input_data is None:
            return False

        # Check for potential injection patterns
        if isinstance(input_data, str):
            dangerous_patterns = self.security_policies.get(
                "dangerous_patterns",
                [
                    "<script",
                    "javascript:",
                    "onerror=",
                    "onclick=",
                    "; DROP TABLE",
                    "UNION SELECT",
                    "../..",
                    "\\x00",
                ],
            )
            for pattern in dangerous_patterns:
                if pattern.lower() in input_data.lower():
                    self.audit_security_event(
                        "dangerous_pattern_detected",
                        {"pattern": pattern, "input_preview": input_data[:100]},
                    )
                    return False

        return True

    def enforce_policy(self, action: str, context: Dict[str, Any]) -> bool:
        """Enforce security policy for given action."""
        allowed_actions = self.security_policies.get("allowed_actions", [])
        if allowed_actions and action not in allowed_actions:
            self.audit_security_event(
                "policy_violation", {"action": action, "context": context}
            )
            return False
        return True

    def audit_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for audit trail."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "event_type": event_type,
            "details": details,
        }
        self.audit_log.append(event)
        self.log_info(f"Security event: {event_type} - {json.dumps(details)}")

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Retrieve security audit log."""
        return self.audit_log.copy()


class PerformanceMonitoredAgent(BaseAgent):
    """Base class for agents with performance monitoring capabilities."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.execution_times = []
        self.resource_metrics = []
        self.performance_thresholds = self.config.get(
            "performance_thresholds",
            {
                "max_execution_time": 300,  # 5 minutes
                "max_memory_mb": 1024,  # 1GB
                "max_cpu_percent": 80,  # 80%
            },
        )

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.metrics["start_memory"] = self._get_memory_usage()

    def stop_monitoring(self):
        """Stop monitoring and record metrics."""
        if self.start_time:
            execution_time = time.time() - self.start_time
            self.execution_times.append(execution_time)
            self.metrics["execution_time"] = execution_time
            self.metrics["end_memory"] = self._get_memory_usage()
            self.metrics["memory_delta"] = (
                self.metrics["end_memory"] - self.metrics["start_memory"]
            )

            # Check thresholds
            if execution_time > self.performance_thresholds["max_execution_time"]:
                self.log_info(
                    f"Performance warning: Execution time {execution_time}s exceeds threshold"
                )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        # Simplified - in production would use psutil or similar
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        if not self.execution_times:
            return {}

        return {
            "average_execution_time": sum(self.execution_times)
            / len(self.execution_times),
            "max_execution_time": max(self.execution_times),
            "min_execution_time": min(self.execution_times),
            "total_executions": len(self.execution_times),
            "last_metrics": self.metrics.copy(),
        }

    def benchmark(self, func, *args, **kwargs):
        """Benchmark a function execution."""
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        self.log_info(f"Benchmark: {func.__name__} took {duration:.4f}s")
        return result


class LearningEnabledAgent(BaseAgent):
    """Base class for agents that can learn and adapt."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.history = []
        self.patterns = {}
        self.adaptations = {}
        self.learning_enabled = self.config.get("learning_enabled", True)

    def record_execution(self, context: Dict[str, Any], result: Dict[str, Any]):
        """Record execution for learning."""
        if not self.learning_enabled:
            return

        execution_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
            "result": result,
            "success": result.get("success", False),
        }
        self.history.append(execution_record)

        # Trigger pattern recognition after sufficient history
        if len(self.history) % 10 == 0:
            self.recognize_patterns()

    def recognize_patterns(self):
        """Analyze history to recognize patterns."""
        if len(self.history) < 5:
            return

        # Simple pattern recognition - count success rates by context features
        success_by_feature = {}

        for record in self.history[-100:]:  # Last 100 executions
            if record["success"]:
                for key, value in record["context"].items():
                    feature = f"{key}={value}"
                    success_by_feature[feature] = success_by_feature.get(feature, 0) + 1

        # Identify high-success patterns
        total_recent = min(100, len(self.history))
        for feature, success_count in success_by_feature.items():
            success_rate = success_count / total_recent
            if success_rate > 0.8:  # 80% success rate
                self.patterns[feature] = success_rate

    def adapt_behavior(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt behavior based on learned patterns."""
        if not self.learning_enabled or not self.patterns:
            return {}

        adaptations = {}

        # Check if current context matches successful patterns
        for key, value in context.items():
            feature = f"{key}={value}"
            if feature in self.patterns:
                adaptations[f"boost_{key}"] = self.patterns[feature]

        self.adaptations = adaptations
        return adaptations

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns and adaptations."""
        return {
            "total_executions": len(self.history),
            "recognized_patterns": len(self.patterns),
            "top_patterns": sorted(
                self.patterns.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "current_adaptations": self.adaptations,
        }


class IntegratedAgent(
    SecurityAwareAgent, PerformanceMonitoredAgent, LearningEnabledAgent
):
    """Fully integrated agent with all capabilities."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        # Multiple inheritance initialization
        SecurityAwareAgent.__init__(self, name, config)
        PerformanceMonitoredAgent.__init__(self, name, config)
        LearningEnabledAgent.__init__(self, name, config)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with full monitoring, security, and learning."""
        # Security validation
        if not self.validate_input(context.get("input")):
            return {"success": False, "error": "Security validation failed"}

        # Performance monitoring
        self.start_monitoring()

        # Adaptive behavior
        adaptations = self.adapt_behavior(context)
        if adaptations:
            context["adaptations"] = adaptations

        try:
            # Actual execution (to be implemented by subclasses)
            result = self._execute_core(context)

            # Record for learning
            self.record_execution(context, result)

            return result

        except Exception as e:
            self.log_error(f"Execution failed: {str(e)}", e)
            return {"success": False, "error": str(e)}

        finally:
            self.stop_monitoring()

    @abstractmethod
    def _execute_core(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution logic to be implemented by subclasses."""
        pass
