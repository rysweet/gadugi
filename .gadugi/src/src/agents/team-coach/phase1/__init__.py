"""
TeamCoach Phase 1: Performance Analytics Foundation

This phase implements the foundational components for agent and team performance analysis:
- AgentPerformanceAnalyzer: Comprehensive agent performance monitoring and analysis
- CapabilityAssessment: Agent capability evaluation and profiling
- MetricsCollector: Data collection infrastructure for performance metrics
- ReportingSystem: Performance reporting and visualization system

These components provide the data foundation for intelligent team coordination.
"""

from .performance_analytics import AgentPerformanceAnalyzer
from .capability_assessment import CapabilityAssessment
from .metrics_collector import MetricsCollector
from .reporting import ReportingSystem

__all__ = [
    "AgentPerformanceAnalyzer",
    "CapabilityAssessment",
    "MetricsCollector",
    "ReportingSystem",
]
