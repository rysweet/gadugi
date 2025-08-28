# Gadugi V0.3 Migration Plan

## Executive Summary
This plan details the migration of Gadugi v0.3 Python implementations to comply with the new simplified architecture where CLAUDE.md handles orchestration directly and agents are single-purpose executors that cannot delegate to other agents.

## Current State Analysis

### 1. gadugi-v0.3/ Directory Structure
- **25 Python engine files** in `src/orchestrator/` implementing agent logic
- **5 service implementations** in `services/` directory
- **19 test files** in `tests/` directory
- **16 agent specifications** in `agents/` directory (markdown format)

### 2. .claude/ Directory Structure
- **New executor agents** created: code-executor, github-executor, test-executor, worktree-executor
- **Python orchestrator code** in `.claude/agents/orchestrator/`
- **Legacy agents** still present (orchestrator-agent.md, workflow-manager.md, etc.)

### 3. Key Architecture Changes Required
- **Remove all agent-to-agent delegation** - agents cannot call other agents
- **Simplify to single-purpose executors** - each agent does one thing only
- **Move orchestration to CLAUDE.md** - all workflow control in main instructions
- **Consolidate duplicated implementations** - merge v0.3 and .claude implementations

## Migration Strategy

### Phase 1: Code Organization and Consolidation

#### 1.1 Create Unified Python Structure
```
.claude/
├── agents/           # Agent markdown specifications
├── engines/          # Python implementations (migrated from gadugi-v0.3/src/orchestrator/)
├── services/         # Service implementations (migrated from gadugi-v0.3/services/)
├── executors/        # New single-purpose executor implementations
└── tests/            # Consolidated test suite
```

#### 1.2 Migration Mapping
| Source File | Target Location | Notes |
|------------|-----------------|-------|
| gadugi-v0.3/src/orchestrator/*.py | .claude/engines/ | Remove delegation logic |
| gadugi-v0.3/services/* | .claude/services/ | Keep as-is (services don't delegate) |
| gadugi-v0.3/tests/* | .claude/tests/ | Update imports |
| .claude/agents/orchestrator/*.py | .claude/executors/ | Refactor for single-purpose |

### Phase 2: Agent Refactoring

#### 2.1 Remove Delegation Pattern
Each agent must be refactored to:
- Remove all calls to other agents
- Use direct tool invocations only
- Return results for CLAUDE.md to coordinate

#### 2.2 Agent Transformation Examples

**BEFORE (with delegation):**
```python
class WorkflowManagerEngine:
    def execute_workflow(self, prompt):
        # Delegate to task decomposer
        tasks = self.task_decomposer.decompose(prompt)
        
        # Delegate to worktree manager
        worktree = self.worktree_manager.create()
        
        # Delegate to code writer
        code = self.code_writer.write(tasks)
```

**AFTER (single-purpose):**
```python
class CodeExecutor:
    def write_file(self, path, content):
        # Direct tool usage only
        with open(path, 'w') as f:
            f.write(content)
        return {"success": True, "path": path}
```

#### 2.3 Agent Categories and Responsibilities

**Pure Executors (NEW):**
- `code-executor`: File writing and editing only
- `test-executor`: Test execution only  
- `github-executor`: GitHub operations only
- `worktree-executor`: Git worktree operations only

**Analysis Agents (keep single-purpose):**
- `task-analyzer`: Analyze task dependencies only
- `architect`: Design architecture only
- `code-reviewer`: Review code only

**Generator Agents (keep single-purpose):**
- `agent-generator`: Generate agent templates only
- `prompt-writer`: Write prompts only
- `test-writer`: Write tests only
- `readme-agent`: Generate documentation only

### Phase 3: Service Integration

Services remain largely unchanged as they don't involve agent delegation:

1. **Event Router Service** - Keep as-is
2. **Neo4j Graph Service** - Keep as-is
3. **MCP Service** - Keep as-is
4. **LLM Proxy Service** - Keep as-is
5. **Gadugi CLI Service** - Update to work with new executor pattern

### Phase 4: Update Agent Specifications

#### 4.1 Update Markdown Files
Each `.md` file in `.claude/agents/` needs:
- Remove references to delegating to other agents
- Add explicit "NO DELEGATION" warning
- Update function signatures to be single-purpose
- Remove complex workflow logic

#### 4.2 Template for Updated Agent Spec
```markdown
# [Agent Name] Executor

## Purpose
Single-responsibility executor for [specific task]. This agent performs direct operations without delegating to other agents.

## CRITICAL: No Delegation
This agent MUST NOT call or delegate to other agents. All operations must be direct tool usage only.

## Available Tools
- [List of tools this agent can use directly]

## Functions
[Single-purpose functions with direct tool usage]
```

### Phase 5: Testing Strategy

#### 5.1 Test Migration
- Move all tests to `.claude/tests/`
- Update import paths
- Remove tests for delegation patterns
- Add tests for single-purpose operations

#### 5.2 New Test Requirements
- Verify no agent delegation occurs
- Test single-purpose execution
- Validate direct tool usage
- Ensure results are returned for coordination

### Phase 6: Documentation Updates

1. Update README.md with new architecture
2. Create ARCHITECTURE.md explaining no-delegation principle
3. Update each agent's documentation
4. Create migration guide for users

## Implementation Order

### Week 1: Foundation
1. Create new directory structure in .claude/
2. Migrate services (no changes needed)
3. Set up test framework

### Week 2: Core Executors
1. Implement code-executor from code_writer_engine.py
2. Implement test-executor from test_agent_engine.py
3. Implement github-executor (new)
4. Implement worktree-executor from worktree_manager_engine.py

### Week 3: Analysis Agents
1. Refactor task-analyzer (remove delegation)
2. Refactor architect (single-purpose)
3. Refactor code-reviewer (single-purpose)

### Week 4: Generator Agents
1. Refactor agent-generator
2. Refactor prompt-writer
3. Refactor test-writer
4. Refactor readme-agent

### Week 5: Integration and Testing
1. Update all tests
2. Integration testing
3. Documentation updates
4. Final validation

## Success Criteria

1. **No Agent Delegation**: Zero instances of agents calling other agents
2. **Single Purpose**: Each agent has one clear responsibility
3. **Direct Tool Usage**: All agents use tools directly, not through other agents
4. **CLAUDE.md Orchestration**: All workflow coordination in main instructions
5. **Tests Pass**: All migrated tests pass
6. **Documentation Complete**: All agents documented with new pattern

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: Keep original code in gadugi-v0.3/ until migration validated

### Risk 2: Complex Workflows Broken
**Mitigation**: Ensure CLAUDE.md has complete orchestration logic for all workflows

### Risk 3: Performance Degradation
**Mitigation**: Benchmark before and after migration

### Risk 4: Missing Functionality
**Mitigation**: Create checklist of all current capabilities, verify each works post-migration

## Validation Checklist

- [ ] All Python engines migrated to .claude/engines/
- [ ] All services migrated to .claude/services/
- [ ] All agents refactored to remove delegation
- [ ] All agent specs updated with NO DELEGATION warning
- [ ] All tests migrated and passing
- [ ] CLAUDE.md contains complete orchestration logic
- [ ] Documentation updated
- [ ] No references to agent delegation remain
- [ ] Integration tests confirm single-purpose execution
- [ ] Performance benchmarks acceptable

## Next Steps

1. Review this plan with architect agent
2. Get approval from user
3. Begin implementation in order specified
4. Track progress with regular updates
5. Validate each phase before proceeding

---

*Migration Plan Version: 1.0*
*Created: 2025-01-23*
*Target Completion: 5 weeks from approval*