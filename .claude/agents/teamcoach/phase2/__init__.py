"""
TeamCoach Phase 2: Intelligent Task Assignment

This phase implements intelligent task assignment capabilities for optimal
agent-task matching and team composition optimization:

- TaskAgentMatcher: Advanced task-agent matching with reasoning
- TeamCompositionOptimizer: Dynamic team formation for projects
- RecommendationEngine: Intelligent recommendations with explanations
- RealtimeAssignment: Real-time task assignment optimization

These components build on Phase 1 analytics to provide intelligent
coordination and assignment capabilities.
"""

from .task_matcher import TaskAgentMatcher
from .team_optimizer import TeamCompositionOptimizer
from .recommendation_engine import RecommendationEngine
from .realtime_assignment import RealtimeAssignment

__all__ = [
    "TaskAgentMatcher",
    "TeamCompositionOptimizer",
    "RecommendationEngine",
    "RealtimeAssignment"
]