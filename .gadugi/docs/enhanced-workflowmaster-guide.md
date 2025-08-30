# Enhanced WorkflowMaster - Comprehensive Guide

## Overview

The Enhanced WorkflowMaster represents a major evolution in Gadugi's workflow orchestration capabilities, providing robust, containerized execution with autonomous decision making and comprehensive state management. This implementation addresses the brittleness and shell dependencies of the original WorkflowMaster while maintaining full compatibility with the Enhanced Separation architecture.

## Key Improvements

### 🔒 Container Execution Integration
- **Secure Isolation**: All operations execute in secure containers
- **Policy-Based Security**: Multiple security policies from minimal to paranoid
- **Resource Management**: CPU, memory, disk, and network limits
- **Audit Logging**: Comprehensive execution trail with integrity verification

### 🤖 Autonomous Operation
- **Intelligent Decision Making**: Reduces approval requirements through smart defaults
- **Error Pattern Analysis**: Learns from failures to make better decisions
- **Workflow Progress Assessment**: Considers overall progress in decisions
- **System Health Monitoring**: Adapts decisions based on system state

### 📊 Advanced State Management
- **Enhanced Persistence**: JSON-based state with compression and validation
- **Automatic Recovery**: Detects and resumes orphaned workflows
- **Checkpoint System**: Critical milestone preservation
- **State Consistency**: Validation and repair mechanisms

### 🚀 Performance Optimization
- **TeamCoach Integration**: Intelligent workflow optimization
- **Performance Analytics**: Real-time metrics and trend analysis
- **Continuous Learning**: Improves decisions based on historical data
- **Resource Efficiency**: Optimized container policies and execution

## Architecture

```
Enhanced WorkflowMaster
├── Core Engine
│   ├── EnhancedWorkflowMaster (main orchestrator)
│   ├── TaskInfo (enhanced task metadata)
│   ├── WorkflowState (comprehensive state tracking)
│   └── WorkflowDecision (autonomous decision enum)
├── Container Integration
│   ├── AgentContainerExecutor (secure execution)
│   ├── Security Policies (minimal to paranoid)
│   └── Resource Management (limits and monitoring)
├── TeamCoach Integration
│   ├── PerformanceMetrics (comprehensive analytics)
│   ├── WorkflowOptimization (intelligent recommendations)
│   └── Continuous Learning (pattern recognition)
└── Enhanced Separation
    ├── GitHubOperations (robust API integration)
    ├── StateManager (persistence and recovery)
    ├── ErrorHandler (circuit breakers and retry)
    └── TaskTracker (metrics and monitoring)
```

## Installation and Setup

### Prerequisites

1. **Container Runtime**: Docker or compatible container runtime
2. **Enhanced Separation Modules**: All shared modules must be available
3. **GitHub Access**: Valid GitHub credentials for repository operations
4. **Python Dependencies**: All required packages installed

### Installation Steps

1. **Install Container Runtime**:
   ```bash
   # Ensure Docker is installed and running
   docker --version
   docker info
   ```

2. **Verify Shared Modules**:
   ```bash
   # Test shared module imports
   python3 -c "
   from .claude.shared.github_operations import GitHubOperations
   from .claude.shared.state_management import StateManager
   from .claude.shared.error_handling import ErrorHandler
   print('Shared modules available')
   "
   ```

3. **Configure Container Security**:
   ```bash
   # Create security policies directory
   mkdir -p container_runtime/config

   # Copy security policies (if not already present)
   cp container_runtime/config/security_policies.yaml.example \
      container_runtime/config/security_policies.yaml
   ```

4. **Initialize WorkflowMaster**:
   ```python
   from .claude.agents.workflow_master_enhanced import EnhancedWorkflowMaster

   # Basic configuration
   config = {
       'autonomous_mode': True,
       'security_policy': 'standard',
       'optimization_enabled': True
   }

   wm = EnhancedWorkflowMaster(config)
   ```

## Usage Guide

### Basic Workflow Execution

```python
from .claude.agents.workflow_master_enhanced import EnhancedWorkflowMaster

# Initialize WorkflowMaster
wm = EnhancedWorkflowMaster({
    'autonomous_mode': True,
    'security_policy': 'development'
})

# Initialize workflow
workflow = wm.initialize_workflow('/prompts/feature.md')

# Execute workflow
success = wm.execute_workflow(workflow)

# Get execution statistics
stats = wm.get_execution_statistics()
print(f"Workflow completed: {success}")
print(f"Statistics: {stats}")
```

### Advanced Configuration

```python
# Advanced configuration options
advanced_config = {
    # Autonomous operation
    'autonomous_mode': True,
    'auto_apply_optimizations': False,

    # Security settings
    'security_policy': 'hardened',
    'audit_enabled': True,

    # Performance tuning
    'optimization_enabled': True,
    'learning_enabled': True,
    'max_parallel_tasks': 4,

    # Error handling
    'circuit_breaker_threshold': 5,
    'max_retry_attempts': 3,
    'retry_backoff_strategy': 'exponential',

    # Resource limits
    'default_timeout_seconds': 300,
    'max_memory_mb': 1024,
    'max_cpu_cores': 2
}

wm = EnhancedWorkflowMaster(advanced_config)
```

### TeamCoach Integration

```python
from .claude.agents.workflow_master_teamcoach_integration import (
    TeamCoachIntegration, optimize_workflow_with_teamcoach
)

# Create TeamCoach integration
integration = TeamCoachIntegration(wm, {
    'optimization_enabled': True,
    'auto_apply_optimizations': True,
    'learning_enabled': True
})

# Analyze workflow performance
metrics = integration.analyze_workflow_performance(workflow)
print(f"Quality Score: {metrics.quality_score:.2f}")

# Generate optimization recommendations
recommendations = integration.generate_optimization_recommendations(workflow, metrics)
for rec in recommendations:
    print(f"Recommendation: {rec.recommendation}")
    print(f"Expected Improvement: {rec.expected_improvement:.1%}")

# Apply optimizations
for rec in recommendations[:3]:  # Apply top 3
    integration.apply_optimization(rec, workflow)
```

### State Management and Recovery

```python
# Check for orphaned workflows
orphaned = wm.detect_orphaned_workflows()
if orphaned:
    print(f"Found {len(orphaned)} orphaned workflows")

    for workflow in orphaned:
        if wm.should_resume_workflow(workflow):
            print(f"Resuming workflow {workflow.task_id}")
            resumed = wm.resume_workflow(workflow.task_id)
            wm.execute_workflow(resumed)

# Manual state management
workflow_state = WorkflowState(
    task_id="manual-task-123",
    prompt_file="/prompts/custom.md"
)

# Save state
wm.save_workflow_state(workflow_state)

# Load state
loaded_state = wm.deserialize_workflow_state(state_data)
```

## Configuration Reference

### Core Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `autonomous_mode` | bool | `True` | Enable autonomous decision making |
| `security_policy` | str | `"standard"` | Container security policy |
| `optimization_enabled` | bool | `True` | Enable TeamCoach optimization |
| `learning_enabled` | bool | `True` | Enable continuous learning |
| `auto_apply_optimizations` | bool | `False` | Automatically apply optimizations |

### Security Policies

| Policy | Description | Use Case |
|--------|-------------|----------|
| `minimal` | Minimal restrictions | Simple scripts, trusted code |
| `standard` | Balanced security/functionality | General development |
| `hardened` | Enhanced security | Production environments |
| `paranoid` | Maximum security | Untrusted code execution |
| `development` | Development-optimized | Local development |
| `testing` | Testing-optimized | CI/CD pipelines |

### Performance Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_parallel_tasks` | int | `3` | Maximum concurrent tasks |
| `default_timeout_seconds` | int | `300` | Default task timeout |
| `circuit_breaker_threshold` | int | `3` | Failure threshold for circuit breakers |
| `max_retry_attempts` | int | `3` | Maximum retry attempts per task |
| `retry_backoff_strategy` | str | `"exponential"` | Retry backoff strategy |

## Migration Guide

### From Original WorkflowMaster

#### 1. Update Import Statements

**Before**:
```python
from .claude.agents.workflow_master import WorkflowMaster
```

**After**:
```python
from .claude.agents.workflow_master_enhanced import EnhancedWorkflowMaster
```

#### 2. Update Configuration

**Before**:
```bash
# Shell-based configuration
export TASK_ID="task-123"
export SECURITY_POLICY="standard"
```

**After**:
```python
# Python-based configuration
config = {
    'security_policy': 'standard',
    'autonomous_mode': True
}
wm = EnhancedWorkflowMaster(config)
```

#### 3. Replace Shell Scripts

**Before**:
```bash
#!/bin/bash
# Shell-based task execution
execute_task() {
    local task_id="$1"
    echo "Executing $task_id"
    # Shell logic
}
```

**After**:
```python
# Container-based task execution
def execute_task(self, task: TaskInfo, workflow: WorkflowState) -> bool:
    result = self.container_executor.execute_python_code(
        code=task_code,
        security_policy=task.container_policy,
        timeout=task.timeout_seconds
    )
    return result['success']
```

#### 4. Update State Management

**Before**:
```bash
# Shell-based state files
STATE_FILE=".github/WorkflowMasterState.md"
echo "Task completed" >> "$STATE_FILE"
```

**After**:
```python
# JSON-based state management
workflow.status = "completed"
workflow.updated_at = datetime.now()
self.save_workflow_state(workflow)
```

#### 5. Enable Autonomous Operation

**Before**: Manual approval required for all decisions

**After**:
```python
# Configure autonomous decision making
config = {
    'autonomous_mode': True,
    'auto_apply_optimizations': True
}

# Decisions are made automatically based on:
# - Task priority and retry count
# - Error pattern analysis
# - Workflow progress assessment
# - System health evaluation
```

### Breaking Changes

1. **Task ID Format**: Changed from shell variables to Python-generated IDs
2. **State File Format**: Changed from Markdown to JSON
3. **Execution Environment**: Changed from shell to containers
4. **Configuration Method**: Changed from environment variables to Python config

### Compatibility Layer

For backward compatibility during migration:

```python
class CompatibilityWorkflowMaster:
    """Compatibility layer for legacy WorkflowMaster usage."""

    def __init__(self):
        self.enhanced_wm = EnhancedWorkflowMaster({
            'autonomous_mode': False,  # Disable for compatibility
            'security_policy': 'standard'
        })

    def execute_legacy_workflow(self, prompt_file: str):
        """Execute workflow with legacy behavior."""
        workflow = self.enhanced_wm.initialize_workflow(prompt_file)

        # Disable autonomous decisions for compatibility
        for task in workflow.tasks:
            task.max_retries = 1  # No automatic retries

        return self.enhanced_wm.execute_workflow(workflow)
```

## Troubleshooting

### Common Issues

#### 1. Container Execution Failures

**Symptoms**: Tasks fail with container errors
**Solutions**:
- Verify Docker is running: `docker info`
- Check security policy compatibility
- Review container logs: `docker logs <container_id>`
- Try more permissive security policy

#### 2. GitHub API Rate Limiting

**Symptoms**: GitHub operations fail with rate limit errors
**Solutions**:
- Verify GitHub token has sufficient permissions
- Check rate limit status: `gh api rate_limit`
- Wait for rate limit reset
- Use circuit breaker protection

#### 3. State Corruption

**Symptoms**: Workflow state loading fails
**Solutions**:
- Check state file format: JSON validation
- Review state consistency
- Restore from backup if available
- Initialize new workflow if necessary

#### 4. Performance Issues

**Symptoms**: Slow workflow execution
**Solutions**:
- Enable TeamCoach optimization
- Review container startup time
- Check resource utilization
- Optimize security policy

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enhanced WorkflowMaster will provide detailed logs
wm = EnhancedWorkflowMaster(config)
```

#### Inspect Workflow State

```python
# Get detailed workflow status
workflow = wm.initialize_workflow(prompt_file)
print(f"Workflow ID: {workflow.task_id}")
print(f"Status: {workflow.status}")
print(f"Tasks: {len(workflow.tasks)}")

for task in workflow.tasks:
    print(f"Task {task.id}: {task.status} ({task.priority})")
```

#### Monitor Performance

```python
# Get execution statistics
stats = wm.get_execution_statistics()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Completed: {stats['completed_tasks']}")
print(f"Failed: {stats['failed_tasks']}")
print(f"Container executions: {stats['container_executions']}")
```

## Best Practices

### 1. Security

- Use appropriate security policies for different environments
- Enable audit logging for production deployments
- Regularly review container images for vulnerabilities
- Implement resource limits to prevent abuse

### 2. Performance

- Enable TeamCoach optimization for long-running workflows
- Use parallel execution for independent tasks
- Monitor and optimize container startup time
- Set appropriate timeouts for different task types

### 3. Reliability

- Enable autonomous mode for better error recovery
- Configure circuit breakers for external dependencies
- Implement comprehensive retry strategies
- Use state checkpointing for critical workflows

### 4. Monitoring

- Enable comprehensive metrics collection
- Monitor workflow success rates and execution times
- Track autonomous decision effectiveness
- Review optimization recommendations regularly

## API Reference

### EnhancedWorkflowMaster

#### Constructor
```python
EnhancedWorkflowMaster(config: Optional[Dict[str, Any]] = None)
```

#### Methods
- `generate_task_id() -> str`: Generate unique task ID
- `initialize_workflow(prompt_file: str, task_id: str) -> WorkflowState`: Initialize new workflow
- `execute_workflow(workflow: WorkflowState) -> bool`: Execute complete workflow
- `save_workflow_state(workflow: WorkflowState)`: Save workflow state
- `detect_orphaned_workflows() -> List[WorkflowState]`: Find orphaned workflows
- `resume_workflow(task_id: str) -> WorkflowState`: Resume existing workflow
- `get_execution_statistics() -> Dict[str, Any]`: Get performance statistics

### TeamCoachIntegration

#### Constructor
```python
TeamCoachIntegration(workflow_master, config: Optional[Dict[str, Any]] = None)
```

#### Methods
- `analyze_workflow_performance(workflow_state) -> PerformanceMetrics`: Analyze performance
- `generate_optimization_recommendations(workflow_state, metrics) -> List[WorkflowOptimization]`: Generate recommendations
- `apply_optimization(optimization, workflow_state) -> bool`: Apply optimization
- `get_optimization_insights() -> Dict[str, Any]`: Get insights

### WorkflowState

#### Properties
- `task_id: str`: Unique workflow identifier
- `prompt_file: str`: Source prompt file
- `status: str`: Current workflow status
- `tasks: List[TaskInfo]`: List of workflow tasks
- `issue_number: int`: GitHub issue number
- `pr_number: int`: GitHub PR number
- `autonomous_decisions: List[Dict]`: Record of autonomous decisions

### TaskInfo

#### Properties
- `id: str`: Unique task identifier
- `name: str`: Task name
- `description: str`: Task description
- `status: str`: Current task status
- `priority: str`: Task priority (high/medium/low)
- `dependencies: List[str]`: Task dependencies
- `container_policy: str`: Security policy for execution
- `retry_count: int`: Current retry count
- `max_retries: int`: Maximum retry attempts

## Contributing

### Development Setup

1. **Clone Repository**:
   ```bash
   git clone <repository_url>
   cd gadugi
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/test_enhanced_workflow_master.py -v
   ```

4. **Run Benchmarks**:
   ```bash
   python tests/test_enhanced_workflow_master.py
   ```

### Adding New Features

1. **Task Execution Methods**: Add new `execute_*_task` methods
2. **Optimization Strategies**: Extend `OptimizationStrategy` enum
3. **Security Policies**: Add new policies to configuration
4. **Metrics**: Extend `PerformanceMetrics` for new measurements

### Testing Guidelines

- Write comprehensive unit tests for new features
- Include integration tests for complex workflows
- Test error conditions and recovery scenarios
- Benchmark performance impact of changes
- Validate security policy compliance

## Support

For support and questions:

1. **Documentation**: Review this guide and API reference
2. **Issues**: Search existing GitHub issues
3. **Testing**: Run comprehensive test suite
4. **Debugging**: Enable debug logging for detailed information

## Version History

### v2.0.0 (Current)
- Container execution integration
- Autonomous decision making
- Advanced state management
- TeamCoach optimization
- Comprehensive test suite

### v1.0.0 (Legacy)
- Original shell-based implementation
- Manual approval requirements
- Basic state management
- Limited error handling
