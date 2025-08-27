# Git & Worktree Management Instructions

## When to Load This File
Load when you need to:
- Create or manage git worktrees
- Handle branching strategies
- Perform git operations safely
- Recover from git issues

## Worktree Lifecycle

### 1. Creation
```bash
ISSUE_NUMBER="123"
BRANCH_NAME="feature/issue-${ISSUE_NUMBER}-description"
WORKTREE_DIR=".worktrees/issue-${ISSUE_NUMBER}"

# Clean up if exists
git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true

# Create new worktree
git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" origin/main

# Initialize metadata
mkdir -p "$WORKTREE_DIR/.task"
echo '{"issue": '${ISSUE_NUMBER}', "created": "'$(date -Iseconds)'"}' > \
     "$WORKTREE_DIR/.task/metadata.json"
```

### 2. Development
```bash
cd .worktrees/issue-123/
# All work happens in isolation
# Changes don't affect main repo
```

### 3. PR Creation
```bash
git push -u origin feature/issue-123-description
gh pr create --base main \
  --title "feat: description (#123)" \
  --body "Closes #123"
```

### 4. Cleanup
```bash
# After merge
git worktree remove .worktrees/issue-123/
git branch -d feature/issue-123-description
```

## Git Safety Procedures

### Before ANY Branch Operations
```bash
git status  # ALWAYS first
```

### Preserve Uncommitted Files
```bash
# If uncommitted files exist
git stash push -m "Preserving work"
git checkout new-branch
git stash pop
```

### Recovery from Missing Files
```bash
# Find when file existed
git log --all --full-history -- <file>
# Restore from commit
git checkout <commit> -- <file>
```

## Worktree Best Practices

1. **One Issue = One Worktree**
2. **Always start from latest main**
3. **Regular commits within worktree**
4. **Use `.task/` for metadata**
5. **Clean up after PR merge**

## Parallel Worktree Management

### Creating Multiple Worktrees
```bash
#!/bin/bash
create_worktrees() {
    for task_id in "$@"; do
        (
            WORKTREE=".worktrees/task-${task_id}"
            BRANCH="feature/task-${task_id}"
            
            git worktree add "$WORKTREE" -b "$BRANCH" origin/main
            
            mkdir -p "$WORKTREE/.task"
            echo '{"task_id": "'${task_id}'"}' > "$WORKTREE/.task/metadata.json"
        ) &
    done
    wait
}
```

## Common Worktree Issues

### Cannot Create Worktree
```bash
# Check and clean
git worktree list
git worktree prune
df -h  # Check disk space
```

### Branch Already Exists
```bash
# Clean up
git push origin --delete branch-name
git branch -D branch-name
git worktree prune
```

### Worktree Locked
```bash
# Force unlock
git worktree unlock .worktrees/stuck/
git worktree remove --force .worktrees/stuck/
```

## Commit Message Standards

### Format
```
type(scope): description

- Detail 1
- Detail 2

Fixes: #issue-number
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Testing
- `refactor`: Code restructure
- `chore`: Maintenance

### AI Attribution
```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Emergency Git Recovery

### Reset to Clean State
```bash
git fetch origin
git reset --hard origin/main
```

### Recover Deleted Branch
```bash
git reflog
git checkout -b recovered <commit>
```

### Fix Diverged History
```bash
git rebase origin/main
# or
git merge origin/main
```