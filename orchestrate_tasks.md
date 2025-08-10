# Orchestrator Task Execution Plan

## Overview
Execute three independent tasks in parallel using isolated worktrees and WorkflowManager delegation.

## Tasks to Execute

### Task 1: Fix All Pyright Errors
- **ID**: fix-pyright-errors
- **Prompt**: prompts/fix-all-pyright-errors.md
- **Priority**: HIGH
- **Requirements**:
  - Fix ALL pyright errors across v0.3 components
  - Achieve zero errors
  - Test each component after fixing

### Task 2: Complete Team Coach Implementation  
- **ID**: complete-team-coach
- **Prompt**: prompts/complete-team-coach-implementation.md
- **Priority**: HIGH
- **Requirements**:
  - Implement full Team Coach agent
  - Must be pyright clean
  - Include comprehensive tests

### Task 3: Clean Up All Worktrees
- **ID**: cleanup-worktrees
- **Prompt**: prompts/cleanup-all-worktrees.md
- **Priority**: MEDIUM
- **Requirements**:
  - Clean up all existing worktrees
  - Add automatic cleanup to workflow
  - Verify cleanup with git worktree list

## Execution Strategy

### Phase 1: Worktree Creation
Create isolated worktrees for each task:
```bash
git worktree add -b task/fix-pyright-errors .worktrees/task-fix-pyright-errors
git worktree add -b task/complete-team-coach .worktrees/task-complete-team-coach  
git worktree add -b task/cleanup-worktrees .worktrees/task-cleanup-worktrees
```

### Phase 2: UV Environment Setup
For each worktree (UV project):
```bash
cd .worktrees/task-{id}
uv sync --all-extras
```

### Phase 3: Parallel WorkflowManager Invocation
Execute all three tasks simultaneously via WorkflowManager:

#### Task 1 WorkflowManager Command:
```
/agent:workflow-manager

Execute workflow for: prompts/fix-all-pyright-errors.md
Worktree: .worktrees/task-fix-pyright-errors
Requirements: Fix ALL pyright errors to achieve zero errors
```

#### Task 2 WorkflowManager Command:
```
/agent:workflow-manager

Execute workflow for: prompts/complete-team-coach-implementation.md
Worktree: .worktrees/task-complete-team-coach
Requirements: Complete Team Coach implementation with tests
```

#### Task 3 WorkflowManager Command:
```
/agent:workflow-manager

Execute workflow for: prompts/cleanup-all-worktrees.md
Worktree: .worktrees/task-cleanup-worktrees
Requirements: Clean up all worktrees and add automation
```

### Phase 4: Monitoring
Monitor all three executions until 100% complete:
- Track 11-phase workflow completion for each
- Ensure all tests pass
- Verify PR creation

### Phase 5: Result Integration
After all tasks complete:
- Merge PRs in appropriate order
- Clean up worktrees
- Document results

## Success Criteria
✅ All three tasks complete successfully
✅ Zero pyright errors across all components
✅ Team Coach fully implemented and tested
✅ All worktrees cleaned up
✅ All 11 workflow phases executed for each task
✅ All PRs created and ready for merge

## Governance Compliance
⚠️ ALL tasks MUST be delegated to WorkflowManager
⚠️ Direct execution is PROHIBITED (Issue #148)
⚠️ Each task must complete all 11 phases
⚠️ Test validation is MANDATORY