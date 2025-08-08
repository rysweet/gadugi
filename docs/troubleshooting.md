# Troubleshooting Guide

Common issues and solutions when using Gadugi.

## Agent Invocation Issues

### Agent Not Found

**Symptoms**: `/agent:orchestrator-agent` returns "agent not found" error

**Solutions**:
```bash
# Check if agent files exist
ls -la .claude/agents/orchestrator-agent.md

# If missing, restore from main branch
git checkout main -- .claude/agents/orchestrator-agent.md
```

### Agent Timeout

**Symptoms**: Agent starts but never completes, no progress updates

**Solutions**:
```bash
# Kill hung processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Check system resources
df -h   # Disk space
top     # CPU/Memory usage

# Retry with increased timeout
/agent:workflow-manager

[Your task with simpler scope]
```

### Agent Not Executing Tasks

**Symptoms**: Agent responds but doesn't actually do the work

**Possible causes**:
- Incorrect invocation syntax
- Missing prompt file
- Insufficient permissions

**Solutions**:
```bash
# Use correct syntax
/agent:orchestrator-agent

Execute these specific prompts:
- prompt-file-1.md
- prompt-file-2.md

# Check Claude settings
cat .claude/settings.json
```

## Worktree Problems

### Cannot Create Worktree

**Symptoms**: "fatal: cannot create worktree" error

**Solutions**:
```bash
# Clean up existing worktrees
git worktree prune

# Check disk space
df -h

# Remove stuck worktrees
git worktree list
git worktree remove --force .worktrees/stuck-name/

# Try manual creation
git worktree add .worktrees/manual-fix -b fix-branch
```

### Branch Already Exists

**Symptoms**: "fatal: a branch named 'X' already exists"

**Solutions**:
```bash
# Delete local branch
git branch -D branch-name

# Delete remote branch
git push origin --delete branch-name

# Use different branch name
git worktree add .worktrees/task -b feature/unique-name
```

### Worktree Locked

**Symptoms**: "fatal: worktree is locked"

**Solutions**:
```bash
# Unlock worktree
git worktree unlock .worktrees/locked-worktree/

# Force remove if needed
git worktree remove --force .worktrees/locked-worktree/
rm -rf .worktrees/locked-worktree/
```

## Git Conflicts

### Merge Conflicts in PR

**Symptoms**: PR shows merge conflicts

**Solutions**:
```bash
# In worktree
cd .worktrees/issue-X/

# Update from main
git fetch origin
git merge origin/main

# Resolve conflicts
# Edit conflicted files
git add .
git commit -m "resolve: merge conflicts with main"
git push
```

### Diverged Branches

**Symptoms**: "Your branch has diverged"

**Solutions**:
```bash
# Rebase on main
git fetch origin
git rebase origin/main

# If conflicts during rebase
# Fix conflicts, then:
git add .
git rebase --continue

# Force push if needed (careful!)
git push --force-with-lease
```

## UV Environment Issues

### Module Not Found

**Symptoms**: Python import errors despite packages installed

**Solutions**:
```bash
# Always use uv run
uv run python script.py  # ✅ Correct
python script.py         # ❌ Wrong

# Sync environment
uv sync --all-extras

# Verify environment
uv run python -c "import your_module"
```

### UV Command Not Found

**Symptoms**: "uv: command not found"

**Solutions**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

### Virtual Environment Issues

**Symptoms**: ".venv not found" or environment errors

**Solutions**:
```bash
# Recreate environment
rm -rf .venv
uv sync --all-extras

# Check UV project files
ls pyproject.toml uv.lock

# Force environment creation
uv venv
uv sync --all-extras
```

## Testing Failures

### Tests Failing After Changes

**Solutions**:
```bash
# Run tests with verbose output
uv run pytest tests/ -v --tb=short

# Run specific test
uv run pytest tests/test_module.py::test_function -v

# Check test environment
uv run pytest --collect-only
```

### Pre-commit Hooks Failing

**Solutions**:
```bash
# Install/reinstall hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files

# Skip specific hook (temporary)
SKIP=ruff git commit -m "message"

# Update hooks
uv run pre-commit autoupdate
```

## GitHub CLI Issues

### Not Authenticated

**Symptoms**: "gh: not authenticated"

**Solutions**:
```bash
# Authenticate
gh auth login

# Check status
gh auth status

# Use different auth method
gh auth login --with-token < token.txt
```

### API Rate Limits

**Symptoms**: "API rate limit exceeded"

**Solutions**:
```bash
# Check rate limit
gh api rate_limit

# Wait for reset
# Or use authenticated requests
gh auth refresh
```

## Performance Issues

### Slow Execution

**Possible causes**:
- Large repository
- Too many parallel tasks
- System resource constraints

**Solutions**:
```bash
# Reduce parallel tasks
/agent:orchestrator-agent

Execute these tasks sequentially:
- task-1
- task-2

# Clean up repository
git gc --aggressive
git prune

# Check system resources
htop
iotop
```

### Memory Issues

**Solutions**:
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Clean UV cache
uv cache clean

# Reduce parallel execution
# Use sequential workflow-manager instead of orchestrator
```

## Recovery Procedures

### Recover from Failed Workflow

```bash
# Find state files
find . -name "*.state" -o -name ".task"

# Check worktree status
cd .worktrees/failed-task/
git status
git log --oneline -5

# Resume or restart
/agent:workflow-manager

Resume task in .worktrees/failed-task from Phase 5
```

### Clean System State

```bash
# Kill all Claude processes
pkill -f claude

# Clean worktrees
git worktree prune
rm -rf .worktrees/*/

# Reset git state
git reset --hard origin/main

# Clean Python
find . -name "*.pyc" -delete
find . -name __pycache__ -delete

# Reinstall environment
uv sync --all-extras
```

## Debug Techniques

### Enable Verbose Output

```bash
# Git debug
GIT_TRACE=1 git command

# Python debug
PYTHONDEBUG=1 uv run python script.py

# Bash debug
set -x
# commands
set +x
```

### Check Agent Logs

```bash
# Find recent logs
find /tmp -name "*claude*" -mtime -1

# Monitor agent execution
watch -n 1 'ps aux | grep claude'
```

## Getting Help

### Resources

1. **Check documentation**: `/docs` directory
2. **Search issues**: `gh issue list --search "error message"`
3. **Review Memory.md**: Context and recent actions
4. **Agent help**: `/agent:task-analyzer` for guidance

### Reporting Issues

```bash
gh issue create --title "Bug: [description]" --body "
## Description
What happened

## Steps to reproduce
1. Step 1
2. Step 2

## Expected behavior
What should happen

## Actual behavior
What actually happened

## Environment
- OS: [version]
- UV: [version]
- Python: [version]
"
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "agent not found" | Missing agent file | Restore from main branch |
| "worktree locked" | Stuck worktree | Force unlock/remove |
| "module not found" | UV environment issue | Use `uv run` prefix |
| "branch exists" | Name conflict | Use unique branch name |
| "timeout" | Long operation | Increase timeout or simplify |
| "permission denied" | File permissions | Check file ownership |
| "merge conflict" | Diverged branches | Merge or rebase main |
