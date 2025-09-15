# Fix Orchestrator for True Parallel Containerized Execution

## Problem Statement
The current orchestrator is over-engineered but fails at its core purpose: true parallel, observable task execution. It needs to properly analyze tasks, decompose them for parallel execution, and run each workflow in isolated containers using Claude Code CLI with proper flags.

## Requirements

### 1. Container-Based Isolation
- Each task must run in its own Docker container or devcontainer
- Complete isolation between parallel executions
- Resource limits and monitoring per container

### 2. Direct Claude CLI Usage
```bash
claude -p prompt.md \
  --dangerously-skip-permissions \
  --verbose \
  --max-turns 50 \
  --output-format json
```

### 3. True Parallelism
- Launch multiple containers simultaneously
- Proper resource management and scheduling
- Dynamic scaling based on system capacity

### 4. Observable Execution
- Real-time output streaming from each container
- Live monitoring dashboard
- Progress tracking and status updates

### 5. Proper Task Decomposition
- Use TaskAnalyzer agent for intelligent decomposition
- Identify parallelizable vs sequential tasks
- Handle dependencies correctly

## Current Issues to Fix

1. **Subprocess Instead of Containers**: Uses `subprocess.Popen` directly without container isolation
2. **Wrong CLI Invocation**: Uses `/agent:WorkflowManager` instead of `claude -p` with prompt files
3. **Missing Automation Flags**: No `--dangerously-skip-permissions` for automation
4. **ThreadPool Instead of Containers**: Uses ThreadPoolExecutor instead of true parallel containers
5. **No Real-time Monitoring**: Missing output streaming and observability

## Implementation Plan

### Phase 1: Container Infrastructure
- Create Docker/devcontainer configurations
- Set up container management layer
- Implement resource limits and monitoring

### Phase 2: Claude CLI Integration
- Proper CLI invocation with all required flags
- Mount worktrees as container volumes
- Handle authentication and permissions

### Phase 3: Parallel Execution Engine
- Container orchestration with docker-compose or similar
- Real-time output streaming with WebSockets
- Resource monitoring and health checks

### Phase 4: Observability Dashboard
- Web-based monitoring interface
- Real-time task progress tracking
- Log aggregation and error reporting

## Files to Create/Modify

### New Files
- `.claude/orchestrator/container_orchestrator.py` - Container-based orchestrator
- `.claude/orchestrator/container_manager.py` - Docker/devcontainer management
- `.claude/orchestrator/stream_monitor.py` - Real-time output streaming
- `.claude/orchestrator/dashboard/` - Monitoring dashboard
- `.claude/orchestrator/docker/Dockerfile` - Claude CLI container image
- `.claude/orchestrator/docker-compose.yml` - Multi-container orchestration

### Files to Modify
- `.claude/orchestrator/orchestrator_main.py` - Integrate container execution
- `.claude/orchestrator/components/execution_engine.py` - Replace subprocess with containers
- `.claude/agents/OrchestratorAgent.md` - Update documentation

## Success Criteria
- 3-5x speedup for parallel tasks
- Real-time monitoring of all executions
- Complete isolation between tasks
- Proper use of Claude CLI automation flags
- Observable, debuggable execution

## Testing Requirements
- Validate container isolation
- Test resource limits
- Verify parallel execution
- Check monitoring accuracy
- Ensure proper error handling
