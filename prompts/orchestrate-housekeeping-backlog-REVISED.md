# REVISED: Orchestrate Housekeeping Backlog Tasks - Issue #9

## Critical Update Based on Conflict Analysis

This revised orchestration plan incorporates findings from the ephemeral conflict reviewer agent. Direct parallel execution would cause significant conflicts. Instead, we'll use a phased approach with shared component extraction.

## Execution Phases (Revised for Conflict Avoidance)

### Phase 0: Shared Component Creation (NEW - Sequential)
**Must complete before any parallel execution**

1. **Create Shared Base Classes**
   ```python
   # .claude/shared/base_classes.py
   - SecurityAwareAgent: Input validation, policy enforcement, audit logging
   - PerformanceMonitoredAgent: Execution tracking, resource monitoring
   - LearningEnabledAgent: Historical data, pattern recognition
   ```

2. **Define Common Interfaces**
   ```python
   # .claude/shared/interfaces.py
   - AgentManagerHookInterface: Standardized hook system
   - PerformanceMetricsInterface: Unified metrics collection
   - ConfigurationSchemaInterface: Consistent config management
   - SecurityPolicyInterface: Security policy enforcement
   ```

3. **Extract Utility Libraries**
   ```python
   # .claude/shared/utils/
   - github_integration.py: Issue/PR management, API handling
   - error_handling.py: Retry logic, graceful degradation
   - config_management.py: YAML/JSON handling, validation
   - performance_monitoring.py: Metrics collection, benchmarking
   ```

### Phase 1: Foundation (Sequential - High Conflict Risk)
**Execute these ONE AT A TIME to avoid conflicts**

1. **Memory.md to GitHub Issues Migration**
   - Prompt: `integrate-memory-github-issues.md`
   - Why Sequential: All other tasks will use Memory.md
   - Duration: ~2 hours
   - Critical: Update all subsequent prompts to use new memory format

2. **Orchestrator/WorkflowManager Architecture Analysis**
   - Prompt: `analyze-orchestrator-workflowmaster-architecture.md`
   - Why Sequential: Findings affect multiple other tasks
   - Duration: ~1.5 hours
   - Output: Architecture recommendations for Phase 3

### Phase 2: Core Infrastructure (Limited Parallel - 2 streams)
**Can run 2 parallel streams with careful coordination**

**Stream A: Container Environment**
- Prompt: `setup-container-execution-environment.md`
- Modifications: Creates new container infrastructure
- No conflicts with Stream B

**Stream B: Agent Creation Framework**
- Prompt: `create-systematic-agent-creation-system.md`
- Modifications: New agent creation system
- Uses shared base classes from Phase 0

### Phase 3: Security and Hooks (Sequential due to agent-manager conflicts)
**These CANNOT run in parallel - all modify agent-manager**

1. **XPIA Defense Implementation**
   - Prompt: `implement-xpia-defense-agent.md`
   - Duration: ~3 hours
   - Uses container environment from Phase 2

2. **Claude-Code Hooks Integration**
   - Prompt: `enhance-claude-code-hooks-integration.md`
   - Duration: ~4 hours
   - Must complete after XPIA to avoid hook conflicts

### Phase 4: Agent Enhancements (Full Parallel - 3 streams)
**These can safely run in parallel after previous phases**

**Stream A: Task Analysis**
- Prompt: `enhance-task-decomposition-analyzer.md`
- Uses shared base classes and interfaces

**Stream B: Team Intelligence**
- Prompt: `implement-teamcoach-agent.md`
- Uses agent creation framework from Phase 2

**Stream C: WorkflowManager Robustness**
- Prompt: `fix-workflowmaster-brittleness-issues.md`
- Incorporates architecture analysis from Phase 1

## Orchestrator-Agent Execution Commands

### Phase 0: Shared Components
```bash
# Create shared components first (manual implementation required)
mkdir -p .claude/shared/{base_classes,interfaces,utils}
# Implement shared components based on specifications above
```

### Phase 1: Sequential Foundation
```bash
# Execute Memory.md migration first
/agent:workflow-manager

Task: Execute workflow for /prompts/integrate-memory-github-issues.md
Priority: CRITICAL - All other tasks depend on this

# Wait for completion, then:
/agent:workflow-manager

Task: Execute workflow for /prompts/analyze-orchestrator-workflowmaster-architecture.md
```

### Phase 2: Limited Parallel
```bash
/agent:orchestrator-agent

Execute these prompts in parallel with worktree isolation:
- /prompts/setup-container-execution-environment.md
- /prompts/create-systematic-agent-creation-system.md

Use --max-parallel=2 to limit resource usage
```

### Phase 3: Sequential Security
```bash
# XPIA Defense first
/agent:workflow-manager

Task: Execute workflow for /prompts/implement-xpia-defense-agent.md

# Then hooks integration
/agent:workflow-manager

Task: Execute workflow for /prompts/enhance-claude-code-hooks-integration.md
```

### Phase 4: Full Parallel
```bash
/agent:orchestrator-agent

Execute these prompts in parallel:
- /prompts/enhance-task-decomposition-analyzer.md
- /prompts/implement-teamcoach-agent.md
- /prompts/fix-workflowmaster-brittleness-issues.md

Use worktree isolation for clean parallel execution
```

## Critical Success Factors

### 1. Shared Component Usage
- All agents MUST use shared base classes
- No duplicate implementations of common functionality
- Consistent error handling and logging

### 2. Configuration Management
- Single unified configuration schema
- Namespace separation for different components
- Version control for configuration changes

### 3. Integration Testing
- Test between each phase
- Verify no conflicts before proceeding
- Rollback capability for each phase

### 4. Performance Monitoring
- Track execution time for each phase
- Monitor resource usage during parallel execution
- Ensure <5% performance overhead from integration

## Monitoring and Persistence

### Continuous Monitoring Requirements
1. Check for merge conflicts after each phase
2. Validate all tests passing before next phase
3. Monitor agent-manager modifications carefully
4. Track shared component usage metrics

### Persistence Strategy
- Use git worktrees for isolation
- Checkpoint after each phase completion
- Maintain rollback branches
- Document all integration points

## Risk Mitigation

### High-Risk Areas
1. **Agent-Manager Modifications**: Sequential execution required
2. **Memory.md Format Change**: Must complete first
3. **Hook System Changes**: Coordinate between XPIA and Claude-Code integration
4. **Configuration Conflicts**: Use unified schema

### Mitigation Strategies
1. Create integration tests before implementation
2. Use feature flags for gradual rollout
3. Maintain backward compatibility
4. Document all breaking changes

## Expected Outcomes

### Phase Completion Times
- Phase 0: 4 hours (shared components)
- Phase 1: 3.5 hours (sequential foundation)
- Phase 2: 3 hours (limited parallel)
- Phase 3: 7 hours (sequential security)
- Phase 4: 4 hours (full parallel)
- **Total: ~21.5 hours** (vs 35+ hours sequential)

### Efficiency Gains
- 40% time reduction through intelligent parallelization
- 80% code reuse through shared components
- Zero merge conflicts through careful coordination
- Improved system reliability and maintainability

This revised orchestration plan addresses all conflicts identified by the ephemeral reviewer and provides a safe, efficient path to implementing all Issue #9 requirements.