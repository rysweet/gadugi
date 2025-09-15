# Shared Module Architecture Design

## Overview

This document defines the shared module architecture for the Enhanced Separation approach, providing common utilities for both OrchestratorAgent and WorkflowManager while preserving their specialized capabilities.

## Design Principles

1. **Preserve Specialization**: Maintain distinct agent capabilities and value propositions
2. **Reduce Duplication**: Extract common patterns into reusable utilities
3. **Maintain Performance**: Ensure shared modules don't impact parallel execution benefits
4. **Enable Evolution**: Create foundation for future agent development
5. **Ensure Reliability**: Improve consistency and error handling across agents

## Module Architecture

### Directory Structure
```
.claude/shared/
├── __init__.py
├── github_operations.py     # GitHub CLI integration utilities
├── state_management.py      # Common state management patterns
├── error_handling.py        # Standardized error handling
├── task_tracking.py         # TodoWrite and task progress utilities
├── interfaces.py            # Agent interface definitions
├── config.py               # Shared configuration management
├── monitoring.py           # Common monitoring and metrics
└── utils.py                # General utility functions
```

## Core Modules

### 1. GitHub Operations Module (`github_operations.py`)

#### Purpose
Centralize GitHub CLI operations used by both agents to ensure consistency and reduce duplication.

#### Interface Design
```python
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class IssueConfig:
    title: str
    body: str
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    milestone: Optional[str] = None

@dataclass
class PRConfig:
    title: str
    body: str
    base: str = "main"
    head: Optional[str] = None
    draft: bool = False
    labels: Optional[List[str]] = None

class GitHubOperations:
    """Centralized GitHub CLI operations for agents"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.api_cache = {}

    # Issue Management
    def create_issue(self, config: IssueConfig) -> str:
        """Create GitHub issue and return issue number"""

    def get_issue(self, issue_number: str) -> Dict:
        """Get issue details"""

    def update_issue(self, issue_number: str, updates: Dict) -> bool:
        """Update issue properties"""

    def close_issue(self, issue_number: str, comment: Optional[str] = None) -> bool:
        """Close issue with optional comment"""

    # Pull Request Management
    def create_pr(self, config: PRConfig) -> str:
        """Create pull request and return PR number"""

    def get_pr(self, pr_number: str) -> Dict:
        """Get PR details including reviews and status"""

    def get_pr_reviews(self, pr_number: str) -> List[Dict]:
        """Get PR reviews"""

    def merge_pr(self, pr_number: str, merge_method: str = "squash") -> bool:
        """Merge pull request"""

    # Repository Operations
    def get_repo_info(self) -> Dict:
        """Get repository information"""

    def list_branches(self, pattern: Optional[str] = None) -> List[str]:
        """List repository branches"""

    def get_branch_status(self, branch: str) -> Dict:
        """Get branch status and tracking information"""

    # Caching and Performance
    def clear_cache(self):
        """Clear API response cache"""

    def get_rate_limit_status(self) -> Dict:
        """Get GitHub API rate limit status"""
```

#### Usage Examples
```python
# OrchestratorAgent usage
github = GitHubOperations()
issue_config = IssueConfig(
    title="Parallel Execution Coordination",
    body="Coordinating execution of multiple tasks...",
    labels=["orchestration", "parallel"]
)
issue_number = github.create_issue(issue_config)

# WorkflowManager usage
github = GitHubOperations()
pr_config = PRConfig(
    title="Implement new feature",
    body="Implementation details...\n\nFixes #{issue_number}",
    head="feature/new-feature-123"
)
pr_number = github.create_pr(pr_config)
```

### 2. State Management Module (`state_management.py`)

#### Purpose
Provide common state management patterns while allowing agent-specific implementations.

#### Interface Design
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

class StateManager(ABC):
    """Base state manager with common patterns"""

    def __init__(self, state_dir: Path, task_id: str):
        self.state_dir = Path(state_dir)
        self.task_id = task_id
        self.state_file = self.state_dir / f"{task_id}_state.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_default_state(self) -> Dict[str, Any]:
        """Get default state structure for this agent type"""
        pass

    def save_state(self, state_data: Dict[str, Any]) -> bool:
        """Save state to file with timestamp"""
        try:
            state_data['last_updated'] = datetime.now().isoformat()
            state_data['task_id'] = self.task_id

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return self.get_default_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            return self.get_default_state()

    def update_state(self, updates: Dict[str, Any]) -> bool:
        """Update specific state fields"""
        current_state = self.load_state()
        current_state.update(updates)
        return self.save_state(current_state)

    def cleanup_state(self) -> bool:
        """Clean up state files"""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            return True
        except Exception as e:
            print(f"Error cleaning up state: {e}")
            return False

class OrchestratorStateManager(StateManager):
    """State manager for OrchestratorAgent"""

    def get_default_state(self) -> Dict[str, Any]:
        return {
            'execution_phase': 'initialization',
            'tasks': {},
            'worktrees': {},
            'execution_stats': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'start_time': None,
                'end_time': None
            },
            'resource_usage': {}
        }

class WorkflowStateManager(StateManager):
    """State manager for WorkflowManager"""

    def get_default_state(self) -> Dict[str, Any]:
        return {
            'current_phase': 1,
            'completed_phases': [],
            'workflow_data': {
                'issue_number': None,
                'branch_name': None,
                'pr_number': None
            },
            'task_list': [],
            'checkpoints': {}
        }
```

### 3. Error Handling Module (`error_handling.py`)

#### Purpose
Standardize error handling patterns across agents with specialized recovery strategies.

#### Interface Design
```python
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging
import traceback
from datetime import datetime

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    GITHUB_API = "github_api"
    FILE_SYSTEM = "file_system"
    PROCESS_EXECUTION = "process_execution"
    STATE_MANAGEMENT = "state_management"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = None

class ErrorHandler:
    """Centralized error handling with agent-specific strategies"""

    def __init__(self, agent_type: str, logger: Optional[logging.Logger] = None):
        self.agent_type = agent_type
        self.logger = logger or self._setup_logger()
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_default_strategies()

    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        attempt_recovery: bool = True
    ) -> ErrorContext:
        """Handle error with optional recovery attempt"""

        error_context = ErrorContext(
            error_id=f"{self.agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            category=category,
            severity=severity,
            message=str(exception),
            details=context or {},
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc()
        )

        # Log error
        self._log_error(error_context)

        # Store in history
        self.error_history.append(error_context)

        # Attempt recovery if requested and strategy exists
        if attempt_recovery and category in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[category](error_context)
                if recovery_result:
                    self.logger.info(f"Successfully recovered from error: {error_context.error_id}")
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed for error {error_context.error_id}: {recovery_error}")

        return error_context

    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable[[ErrorContext], bool]
    ):
        """Register custom recovery strategy for error category"""
        self.recovery_strategies[category] = strategy

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff]

        return {
            'total_errors': len(recent_errors),
            'by_category': self._group_by_category(recent_errors),
            'by_severity': self._group_by_severity(recent_errors),
            'most_recent': recent_errors[-1] if recent_errors else None
        }
```

### 4. Task Tracking Module (`task_tracking.py`)

#### Purpose
Standardize TodoWrite integration and task progress tracking across agents.

#### Interface Design
```python
from typing import List, Dict, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Task:
    id: str
    content: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskTracker:
    """Unified task tracking with TodoWrite integration"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.tasks: Dict[str, Task] = {}
        self.todo_write_integration = True

    def create_task(
        self,
        task_id: str,
        content: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create new task"""
        task = Task(
            id=task_id,
            content=content,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        self.tasks[task_id] = task
        self._sync_to_todowrite()
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.now()
            self._sync_to_todowrite()
            return True
        return False

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status"""
        return [task for task in self.tasks.values() if task.status == status]

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get task progress summary"""
        total = len(self.tasks)
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        in_progress = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        pending = len(self.get_tasks_by_status(TaskStatus.PENDING))

        return {
            'total_tasks': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'completion_rate': completed / total if total > 0 else 0
        }

    def _sync_to_todowrite(self):
        """Sync tasks to TodoWrite format"""
        if self.todo_write_integration:
            todo_tasks = []
            for task in self.tasks.values():
                todo_tasks.append({
                    'id': task.id,
                    'content': task.content,
                    'status': task.status.value,
                    'priority': task.priority.value
                })
            # TodoWrite integration would be called here
            # todowrite(todo_tasks)
```

### 5. Agent Interfaces Module (`interfaces.py`)

#### Purpose
Define standard interfaces for agent coordination and communication.

#### Interface Design
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentCapabilities:
    """Describes what an agent can do"""
    name: str
    description: str
    supported_operations: List[str]
    required_tools: List[str]
    performance_characteristics: Dict[str, Any]

@dataclass
class ExecutionContext:
    """Context passed between agents"""
    task_id: str
    workflow_type: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    constraints: Dict[str, Any]

@dataclass
class ExecutionResult:
    """Result returned by agent execution"""
    success: bool
    task_id: str
    outputs: Dict[str, Any]
    metrics: Dict[str, Any]
    error_info: Optional[Dict[str, Any]] = None

class Agent(ABC):
    """Base agent interface"""

    @abstractmethod
    def get_capabilities(self) -> AgentCapabilities:
        """Return agent capabilities"""
        pass

    @abstractmethod
    def validate_context(self, context: ExecutionContext) -> bool:
        """Validate if agent can handle the given context"""
        pass

    @abstractmethod
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute task with given context"""
        pass

    @abstractmethod
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status for a task"""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel running task"""
        pass

class WorkflowAgent(Agent):
    """Interface for workflow execution agents"""

    @abstractmethod
    def execute_workflow(self, prompt_file: str, context: ExecutionContext) -> ExecutionResult:
        """Execute complete workflow from prompt"""
        pass

    @abstractmethod
    def resume_workflow(self, task_id: str) -> ExecutionResult:
        """Resume interrupted workflow"""
        pass

class CoordinationAgent(Agent):
    """Interface for coordination/orchestration agents"""

    @abstractmethod
    def analyze_dependencies(self, tasks: List[ExecutionContext]) -> Dict[str, List[str]]:
        """Analyze task dependencies"""
        pass

    @abstractmethod
    def execute_parallel(self, tasks: List[ExecutionContext]) -> Dict[str, ExecutionResult]:
        """Execute tasks in parallel"""
        pass

    @abstractmethod
    def monitor_execution(self, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Monitor parallel execution progress"""
        pass
```

## Integration Strategy

### Phase 1: Foundation Setup
1. Create shared module directory structure
2. Implement core utility classes with comprehensive tests
3. Create compatibility layer for existing agents
4. Set up monitoring and validation frameworks

### Phase 2: Agent Integration
1. Update OrchestratorAgent to use shared utilities
2. Update WorkflowManager to use shared utilities
3. Maintain parallel execution with both old and new implementations
4. Validate performance and functionality parity

### Phase 3: Optimization and Enhancement
1. Optimize shared utilities based on usage patterns
2. Add advanced features and capabilities
3. Implement comprehensive monitoring and metrics
4. Create documentation and usage guidelines

### Phase 4: Ecosystem Expansion
1. Use shared modules as foundation for new agents
2. Create agent development toolkit
3. Implement advanced coordination patterns
4. Build comprehensive agent ecosystem

## Testing Strategy

### Unit Testing
```python
# Example test structure
class TestGitHubOperations:
    def test_create_issue(self):
        # Test issue creation
        pass

    def test_create_pr(self):
        # Test PR creation
        pass

    def test_error_handling(self):
        # Test error scenarios
        pass

class TestStateManager:
    def test_save_load_state(self):
        # Test state persistence
        pass

    def test_state_updates(self):
        # Test state modification
        pass
```

### Integration Testing
```python
class TestAgentIntegration:
    def test_orchestrator_with_shared_modules(self):
        # Test OrchestratorAgent integration
        pass

    def test_workflowmaster_with_shared_modules(self):
        # Test WorkflowManager integration
        pass

    def test_agent_coordination(self):
        # Test inter-agent communication
        pass
```

### Performance Testing
```python
class TestPerformance:
    def test_shared_module_overhead(self):
        # Measure performance impact
        pass

    def test_parallel_execution_performance(self):
        # Validate parallel execution benefits maintained
        pass
```

## Success Metrics

### Quantitative Metrics
- **Code Duplication Reduction**: Target >70% reduction in duplicated utilities
- **Test Coverage**: Maintain >95% coverage for shared modules
- **Performance Impact**: <2% overhead from shared utilities
- **Error Rate**: <1% error rate in shared module operations

### Qualitative Metrics
- **Developer Experience**: Improved consistency and ease of use
- **Maintainability**: Reduced maintenance overhead for common operations
- **Extensibility**: Easier development of new agents
- **Reliability**: More consistent error handling and recovery

## Future Considerations

### Planned Enhancements
1. **Advanced Monitoring**: Real-time metrics and alerting
2. **Configuration Management**: Centralized configuration system
3. **Plugin Architecture**: Extensible module system
4. **Performance Optimization**: Advanced caching and optimization
5. **Agent Marketplace**: Ecosystem for sharing specialized agents

### Architectural Evolution
The shared module architecture provides a foundation for:
- **Multi-agent workflows**: Complex coordination between specialized agents
- **Agent composition**: Building complex capabilities from simple agents
- **Dynamic scaling**: Adaptive resource allocation and task distribution
- **AI-driven optimization**: Machine learning for performance optimization

## Conclusion

The shared module architecture provides a solid foundation for the Enhanced Separation approach, delivering:

- **Reduced code duplication** through common utilities
- **Improved consistency** across agent implementations
- **Enhanced maintainability** through centralized common operations
- **Better extensibility** for future agent development
- **Preserved performance** with parallel execution capabilities

This design enables evolution of the agent ecosystem while maintaining the proven benefits of the current architecture.

---

*This design document was created as part of the comprehensive architecture analysis workflow.*
