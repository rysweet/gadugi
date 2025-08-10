# Orchestrator Parallel Execution Request

## Tasks to Execute in Parallel

### Task 1: Fix All Pyright Errors
- **Prompt File**: prompts/fix-all-pyright-errors.md
- **Description**: Fix all remaining pyright errors across v0.3 components
- **Components**: Recipe Executor, Event Router, MCP Service, Orchestrator
- **Priority**: High
- **Dependencies**: None (can run independently)

### Task 2: Complete Team Coach Implementation
- **Prompt File**: prompts/complete-team-coach-implementation.md
- **Description**: Implement the Team Coach agent for session analysis
- **Components**: Team Coach agent creation and integration
- **Priority**: High
- **Dependencies**: None (can run independently)

### Task 3: Clean Up All Worktrees
- **Prompt File**: prompts/cleanup-all-worktrees.md
- **Description**: Clean up all existing worktrees and add automatic cleanup
- **Components**: Worktree management system
- **Priority**: Medium
- **Dependencies**: None (can run independently)

## Execution Strategy

All three tasks are independent and can be executed in parallel:
- Each task will get its own worktree
- Each task will be delegated to a WorkflowManager instance
- All tasks will follow the complete 11-phase workflow
- Expected speedup: 3x (running in parallel vs sequential)

## Success Criteria

- All pyright errors fixed (0 errors remaining)
- Team Coach agent fully implemented and tested
- All worktrees cleaned up and automatic cleanup added
- All tasks pass Phase 6 testing requirements
- Clean PRs created for each task