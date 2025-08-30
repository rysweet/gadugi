# Orchestrator Governance Requirements (Issue #148)

## Overview

The Orchestrator agent MUST delegate ALL task execution to WorkflowManager instances to ensure proper 11-phase workflow execution. Direct task execution by the orchestrator is strictly prohibited.

## Governance Requirements

### Mandatory Delegation

All tasks processed by the orchestrator must be:

1. **Assigned to a dedicated worktree** for isolation
2. **Delegated to WorkflowManager** via `claude -p` subprocess invocation
3. **Executed through the complete 11-phase workflow**
4. **Monitored for successful completion** of all phases

### The 11-Phase Workflow

Every task MUST go through these phases via WorkflowManager:

1. **Phase 1: Initial Setup** - Environment preparation and validation
2. **Phase 2: Issue Creation** - GitHub issue for tracking
3. **Phase 3: Branch Management** - Feature branch creation
4. **Phase 4: Research and Planning** - Analysis and planning
5. **Phase 5: Implementation** - Code changes
6. **Phase 6: Testing** - Test execution and validation
7. **Phase 7: Documentation** - Documentation updates
8. **Phase 8: Pull Request** - PR creation
9. **Phase 9: Code Review** - Invoke CodeReviewer agent
10. **Phase 10: Review Response** - Handle review feedback
11. **Phase 11: Settings Update** - Final configurations

## Implementation Details

### Orchestrator Architecture

```
┌─────────────────┐
│   Orchestrator  │
│                 │
│  Coordinates    │
│  & Monitors     │
└────────┬────────┘
         │
         ▼ Delegates via 'claude -p'
┌─────────────────────────────────────┐
│                                     │
│    WorkflowManager Instances        │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Worker 1 │  │ Worker 2 │  ...  │
│  │          │  │          │       │
│  │ Worktree │  │ Worktree │       │
│  │   Task   │  │   Task   │       │
│  └──────────┘  └──────────┘       │
│                                     │
└─────────────────────────────────────┘
```

### Task Delegation Flow

1. **Task Receipt**: Orchestrator receives task definition
2. **Worktree Creation**: Create isolated git worktree for task
3. **Prompt Generation**: Create WorkflowManager prompt file
4. **Subprocess Invocation**: Execute `claude -p <prompt_file>`
5. **Phase Execution**: WorkflowManager executes all 11 phases
6. **Result Collection**: Orchestrator collects results
7. **Worktree Cleanup**: Remove worktree after completion

### Code Structure

#### parallel_executor.py

```python
async def _execute_single_task(self, task: Any) -> Any:
    """Execute a single task.
<<<<<<< HEAD

=======

>>>>>>> feature/gadugi-v0.3-regeneration
    GOVERNANCE REQUIREMENT: All tasks MUST be delegated to WorkflowManager
    to ensure complete 11-phase workflow execution (Issue #148).
    """
    # MANDATORY: Delegate ALL tasks to WorkflowManager
    workflow_result = await self._invoke_workflow_manager(task)
    # Process results...

async def _invoke_workflow_manager(self, task: Any) -> Dict[str, Any]:
    """Invoke WorkflowManager for task execution via claude -p.
<<<<<<< HEAD

=======

>>>>>>> feature/gadugi-v0.3-regeneration
    GOVERNANCE: This is the MANDATORY delegation point.
    """
    # Create prompt file for WorkflowManager
    prompt_content = self._create_workflow_prompt(task)
    prompt_file = Path(f"/tmp/orchestrator_task_{task_id}.md")
    prompt_file.write_text(prompt_content)
<<<<<<< HEAD

=======

>>>>>>> feature/gadugi-v0.3-regeneration
    # Execute via claude subprocess
    workflow_cmd = ["claude", "-p", str(prompt_file)]
    process = await asyncio.create_subprocess_exec(*workflow_cmd, ...)
    # Process results...
```

## Governance Validation

### Validation Module

The `governance_validator.py` module provides:

- **GovernanceValidator**: Validates task execution compliance
- **GovernanceReport**: Reports compliance status
- **Violation Detection**: Identifies governance violations
- **Enforcement**: Ensures compliance in execution

### Running Validation

```bash
# Run governance compliance check
python -m claude.agents.orchestrator.governance_validator

# Run tests
pytest tests/test_orchestrator_governance.py -v
```

### Validation Criteria

✅ **Compliant Execution**:
- WorkflowManager invoked for all tasks
- All 11 phases completed
- Proper subprocess isolation
- Complete audit trail

❌ **Governance Violations**:
- Direct task execution
- Bypassing WorkflowManager
- Incomplete phase execution
- Missing audit trail

## Monitoring and Enforcement

### Automatic Detection

The governance validator automatically detects:

1. **Direct Execution**: Tasks executed without WorkflowManager
2. **Incomplete Phases**: Workflows missing required phases
3. **Code Violations**: Source code bypassing delegation
4. **Missing Invocations**: No WorkflowManager calls detected

### Enforcement Mechanisms

1. **Code Review**: Automated checks in PR reviews
2. **Runtime Validation**: Real-time compliance checking
3. **Audit Logging**: Complete execution history
4. **Violation Reporting**: Immediate notification of violations

## Benefits

### Quality Assurance

- **Consistent Workflow**: Every task follows the same process
- **Complete Testing**: Phase 6 ensures all tests pass
- **Code Review**: Phase 9 ensures quality review
- **Documentation**: Phase 7 maintains documentation

### Traceability

- **Issue Tracking**: Every task has a GitHub issue
- **Branch Management**: Proper git workflow
- **PR History**: Complete change history
- **Audit Trail**: Full execution logs

### Reliability

- **Error Recovery**: WorkflowManager handles failures
- **State Persistence**: Workflows can resume
- **Timeout Protection**: Prevents hanging tasks
- **Health Monitoring**: System stability checks

## Migration Guide

### For Existing Code

If you have code that directly executes tasks:

1. **Identify Direct Execution**: Look for `await asyncio.sleep` or similar
2. **Replace with Delegation**: Use `_invoke_workflow_manager()`
3. **Update Tests**: Ensure tests validate delegation
4. **Run Validation**: Check compliance with validator

### For New Features

When adding new orchestrator features:

1. **Always Delegate**: Never execute tasks directly
2. **Use WorkflowManager**: All work goes through 11 phases
3. **Add Validation**: Include governance checks
4. **Document Changes**: Update this documentation

## Troubleshooting

### Common Issues

#### "WorkflowManager not found"

**Solution**: Ensure WorkflowManager agent is properly installed and accessible.

#### "Phases incomplete"

**Solution**: Check WorkflowManager logs for phase execution issues.

#### "Governance violation detected"

**Solution**: Review execution logs and ensure proper delegation.

### Debug Commands

```bash
# Check orchestrator logs
tail -f logs/orchestrator.log

# Validate governance compliance
python -m claude.agents.orchestrator.governance_validator

# Test specific task delegation
python -c "
from claude.agents.orchestrator import Orchestrator
orchestrator = Orchestrator()
# Test task execution...
"
```

## References

- Issue #148: Enforce orchestrator governance requirements
- WorkflowManager Documentation: `.claude/agents/WorkflowManager.md`
- Orchestrator Implementation: `.claude/agents/orchestrator/`
- Governance Validator: `.claude/agents/orchestrator/governance_validator.py`
<<<<<<< HEAD
- Test Suite: `tests/test_orchestrator_governance.py`
=======
- Test Suite: `tests/test_orchestrator_governance.py`
>>>>>>> feature/gadugi-v0.3-regeneration
