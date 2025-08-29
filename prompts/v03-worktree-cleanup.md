# Add Worktree Cleanup to Workflow

## Task Description
Add automatic worktree cleanup as a standard part of the workflow process.

## Requirements
1. Add cleanup phase to WorkflowManager (Phase 12)
2. Ensure worktrees are removed after PR merge
3. Add cleanup verification
4. Handle cleanup failures gracefully

## Implementation Details

### WorkflowManager Updates
- Add Phase 12: Cleanup
- After PR creation/merge, clean up worktree
- Use `git worktree remove`
- Verify cleanup succeeded

### Cleanup Commands
```bash
# List worktrees
git worktree list

# Remove specific worktree
git worktree remove .worktrees/task-name/

# Prune stale worktrees
git worktree prune
```

### Safety Checks
- Ensure all changes are committed
- Verify PR was created
- Check branch was pushed
- Only cleanup after confirmation

## Current Worktrees to Clean
- .worktrees/task-setup-neo4j-gadugi
- .worktrees/task-implement-mcp-service
- .worktrees/task-implement-agent-framework
- Any other stale worktrees

## Execution Requirements
- Update WorkflowManager to include cleanup phase
- Clean up all existing worktrees
- Test cleanup process
- Document in workflow documentation

/agent:WorkflowManager

Execute complete workflow to add worktree cleanup and clean existing worktrees
