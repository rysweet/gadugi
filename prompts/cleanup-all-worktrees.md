# Clean Up All Worktrees

Clean up all existing worktrees and add automatic cleanup to workflow.

## Worktrees to Clean
- .worktrees/task-fix-remaining-pyright-errors
- .worktrees/task-implement-agent-framework
- .worktrees/task-implement-mcp-service
- .worktrees/task-setup-neo4j-gadugi
- .worktrees/task-task-1-neo4j-setup
- .worktrees/task-task-2-mcp-service
- .worktrees/task-task-3-agent-framework

## Requirements
- Use `git worktree remove` for each
- Run `git worktree prune` after cleanup
- Verify cleanup with `git worktree list`
- Add cleanup phase to WorkflowManager for future