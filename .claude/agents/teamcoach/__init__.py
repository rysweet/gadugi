"""
TeamCoach Agent - Intelligent Multi-Agent Team Coordination and Optimization

This package provides intelligent coordination, guidance, and optimization for multi-agent
development teams. The TeamCoach agent analyzes team performance, identifies optimization
opportunities, and provides coaching for improved collaboration and productivity.

Core Capabilities:
- Performance Analytics: Comprehensive agent and team performance analysis
- Intelligent Task Assignment: Optimal task-agent matching with reasoning
- Team Composition Optimization: Dynamic team formation for projects
- Coaching and Recommendations: Performance coaching and optimization guidance
- Conflict Resolution: Detection and resolution of agent coordination issues
- Learning and Adaptation: Continuous improvement through outcome analysis

Architecture:
- Phase 1: Performance Analytics Foundation
- Phase 2: Intelligent Task Assignment
- Phase 3: Coaching and Optimization
- Phase 4: Learning and Adaptation
"""

from .phase1.performance_analytics import AgentPerformanceAnalyzer
from .phase1.capability_assessment import CapabilityAssessment
from .phase1.metrics_collector import MetricsCollector
from .phase1.reporting import ReportingSystem

from .phase2.task_matcher import TaskAgentMatcher
from .phase2.team_optimizer import TeamCompositionOptimizer
from .phase2.recommendation_engine import RecommendationEngine
from .phase2.realtime_assignment import RealtimeAssignment

from .phase3.coaching_engine import CoachingEngine
from .phase3.conflict_resolver import AgentConflictResolver
from .phase3.workflow_optimizer import WorkflowOptimizer
from .phase3.strategic_planner import StrategicTeamPlanner

# Phase 4 imports temporarily commented out until implementation is complete
# from .phase4.performance_learner import TeamPerformanceLearner
# from .phase4.adaptive_manager import AdaptiveTeamManager
# from .phase4.ml_models import MLModels
# from .phase4.continuous_improvement import ContinuousImprovement

__version__ = "1.0.0"
__author__ = "Claude Code AI Agent"

__all__ = [
    # Phase 1 - Performance Analytics Foundation
    "AgentPerformanceAnalyzer",
    "CapabilityAssessment",
    "MetricsCollector",
    "ReportingSystem",
    # Phase 2 - Intelligent Task Assignment
    "TaskAgentMatcher",
    "TeamCompositionOptimizer",
    "RecommendationEngine",
    "RealtimeAssignment",
    # Phase 3 - Coaching and Optimization
    "CoachingEngine",
    "AgentConflictResolver",
    "WorkflowOptimizer",
    "StrategicTeamPlanner",
    # Phase 4 - Learning and Adaptation (temporarily disabled until implementation complete)
    # "TeamPerformanceLearner",
    # "AdaptiveTeamManager",
    # "MLModels",
    # "ContinuousImprovement"
]
