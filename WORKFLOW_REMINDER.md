# Workflow Compliance Reminder

## CRITICAL: Check Before ANY Work

### Pre-Work Checklist
Before starting ANY development task, ask yourself:
1. ❓ Have I created a GitHub issue? (Phase 2)
2. ❓ Have I created a worktree? (Phase 3)
3. ❓ Am I in the worktree directory?
4. ❓ Have I researched and planned? (Phase 4)

### Red Flags - STOP if you're about to:
- 🚫 Use Task tool without workflow setup
- 🚫 Edit files directly in main repository
- 🚫 Fix code without creating an issue first
- 🚫 Jump to implementation without planning

### Correct Pattern
```bash
# 1. Create issue
gh issue create --title "..." --body "..."

# 2. Create worktree
git worktree add .worktrees/issue-XXX -b branch-name

# 3. Enter worktree
cd .worktrees/issue-XXX

# 4. NOW you can start work
```

## Why This Matters
- **Audit Trail**: Every change is tracked
- **Isolation**: Work doesn't affect main repo
- **Quality**: All phases ensure proper testing
- **Governance**: Compliance with project standards

## Mental Checkpoint
Before using ANY tool that modifies code:
"Am I in a worktree with an issue number?"

If NO → STOP and follow the 11-phase workflow
If YES → Proceed with implementation