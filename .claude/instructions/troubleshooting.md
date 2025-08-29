# Troubleshooting Instructions

## When to Load This File
Load when encountering:
- Orchestrator failures
- Worktree issues
- Agent system problems
- Recovery scenarios

## Orchestrator Failures

### Agent Not Found
```bash
# Check files exist
ls -la .claude/agents/OrchestratorAgent.md
ls -la src/orchestrator/

# Restore from main if missing
git checkout main -- .claude/agents/OrchestratorAgent.md
git checkout main -- src/orchestrator/
```

### Orchestrator Hangs
```bash
# Kill hung processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Check resources
df -h   # Disk space
free -h # Memory

# Restart with logging
/agent:OrchestratorAgent
```

### Task Analysis Fails
**Fallback to WorkflowManager:**
```
/agent:WorkflowManager

Task: Execute workflow for /prompts/single-task.md
Emergency fallback: orchestrator failure
```

## Worktree Failures

### Creation Fails
```bash
# Clean up and retry
git worktree list
git worktree prune
df -h  # Check disk space
ls -la .worktrees/

# Manual creation
git worktree add .worktrees/manual-$(date +%s) -b fix-branch
```

### Branch Conflicts
```bash
# List and clean
git branch -a
git push origin --delete conflicting-branch
git branch -D conflicting-branch
git worktree prune
```

### Cleanup Issues
```bash
# Force unlock
git worktree unlock .worktrees/stuck/

# Force remove
git worktree remove --force .worktrees/stuck/

# Manual cleanup
rm -rf .worktrees/stuck/
git worktree prune
```

## Recovery Procedures

### State Recovery
```bash
# Find state files
find . -name "*.orchestrator.state" -o -name "*.workflow.state"

# Check progress
cat .task/progress.json

# Clean up partial work
git worktree list
```

### Resource Recovery
```bash
# Clean processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Clean temp files
find /tmp -name "*orchestrator*" -mtime +1 -delete
find /tmp -name "*worktree*" -mtime +1 -delete

# Prune worktrees
git worktree prune
```

### System Health Check
```bash
# Check resources
df -h                  # Disk space
ps aux | grep claude   # Processes
git status            # Repository
git worktree list     # Worktrees

# Test basic functionality
/agent:TaskAnalyzer
Simple test task
```

## Fallback Strategies

### Level 1: Use WorkflowManager
When orchestrator fails completely:
```
/agent:WorkflowManager
Task: [specific task]
Fallback from orchestrator failure
```

### Level 2: Manual Workflow
When all agents fail:
1. Create emergency issue
2. Work in feature branch
3. Follow manual workflow
4. Tag as `emergency`

### Level 3: System Failure
For complete agent failure:
1. Document system failure
2. Manual procedures only
3. Document all steps
4. Restore agents first
5. Conduct post-mortem

## Common Error Patterns

### "Module not found" in UV Projects
```bash
# Always use uv run
uv run python script.py  # ✅
python script.py         # ❌

# Ensure synced
uv sync --all-extras
```

### Type Errors After Changes
```bash
# Quick check
uv run pyright --outputjson | grep errorCount

# Parallel fix strategy
# Launch multiple Task instances for different directories
```

### Test Failures
```bash
# Run with verbose output
uv run pytest tests/ -v --tb=short

# Run specific test
uv run pytest tests/test_specific.py::TestClass::test_method
```

## Prevention Measures

### Regular Maintenance
- Weekly: `git worktree prune`
- Before large ops: Check disk space
- Keep agents updated

### Monitoring
- Watch for repeated failures
- Document failure patterns
- Monitor resource usage

### Backup Strategies
- Keep known-good agent versions
- Document manual procedures
- Test fallback procedures

## Escalation Triggers

Escalate when:
- Same failure occurs > 3 times
- Worktree system unusable
- Agent files corrupted
- Resource issues prevent operation
- Manual fallbacks also fail