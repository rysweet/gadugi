# Enhanced Separation Architecture Components
from .shared.github_operations import GitHubOperations
from .shared.state_management import StateManager
from .shared.task_tracking import TaskMetrics
from .shared.error_handling import ErrorHandler, CircuitBreaker
from .shared.interfaces import AgentConfig, TaskResult, PerformanceMetrics

# TeamCoach Core Components
from .teamcoach.phase1 import AgentPerformanceAnalyzer, CapabilityAssessment
from .teamcoach.phase2 import TaskAgentMatcher, TeamCompositionOptimizer
from .teamcoach.phase3 import CoachingEngine, ConflictResolver, WorkflowOptimizer, StrategicPlanner
