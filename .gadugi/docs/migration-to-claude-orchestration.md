# Migration Guide: CLAUDE.md-Based Orchestration

## Overview

This guide helps you migrate from the old agent-based orchestration to the new CLAUDE.md-integrated orchestration system.

## Why the Change?

### Previous Architecture Problems
- Complex delegation chains between agents
- Difficult to debug failures
- Unclear execution flow
- Multiple points of failure
- Excessive abstraction

### New Architecture Benefits
- Direct orchestration in CLAUDE.md
- Simpler, more reliable execution
- Clear, linear workflow
- Single source of truth
- Easier to understand and maintain

## What Changes for Users

### Old Workflow (DEPRECATED)
```
User Request → OrchestratorAgent → WorkflowManager → Multiple Sub-agents → Execution
```

### New Workflow (CURRENT)
```
User Request → CLAUDE.md Instructions → Direct Execution with Optional Executor Agents
```

## Step-by-Step Migration Process

### 1. Update Your Workflow

**Old way:**
```
/agent:OrchestratorAgent

Execute these tasks:
- task1.md
- task2.md
```

**New way:**
```
Follow the 11-phase workflow in CLAUDE.md directly:
1. Create issue
2. Create worktree
3. Implement changes
4. Test
5. Create PR
```

### 2. Use Simplified Executors When Needed

Instead of complex agent chains, use single-purpose executors:

**Worktree Operations:**
```
/agent:WorktreeExecutor
Create worktree for issue 305
```

**GitHub Operations:**
```
/agent:GitHubExecutor
Create PR for branch feature/issue-305
```

**Test Execution:**
```
/agent:TestExecutor
Run full test suite
```

**Code Writing:**
```
/agent:CodeExecutor
Create module src/parser.py with Parser class
```

### 3. Handle Parallel Tasks

**Old way:** OrchestratorAgent would coordinate parallel execution

**New way:** Follow parallel execution guidelines in CLAUDE.md:
1. Identify independent tasks
2. Create separate worktrees
3. Execute in parallel using subprocess/threading
4. Aggregate results

## Common Scenarios

### Scenario 1: Single Feature Implementation

**Old:**
```
/agent:WorkflowManager
Implement feature X
```

**New:**
1. Follow 11-phase workflow in CLAUDE.md
2. Create issue, worktree, implement, test, PR
3. Use executor agents only for specific operations

### Scenario 2: Multiple Bug Fixes

**Old:**
```
/agent:OrchestratorAgent
Fix bugs A, B, and C in parallel
```

**New:**
1. Analyze dependencies per CLAUDE.md
2. Create worktrees for each independent fix
3. Execute fixes in parallel
4. Create PRs for each

### Scenario 3: Code Review

**Old:**
```
/agent:CodeReviewer
Review PR #123
```

**New:**
1. Use GitHub's built-in review features
2. Follow review guidelines in CLAUDE.md
3. No separate agent needed

## Troubleshooting

### Issue: "Agent not found" errors
**Solution:** Agent has been deprecated. Use CLAUDE.md instructions directly.

### Issue: Workflow seems unclear
**Solution:** Follow the 11-phase workflow in CLAUDE.md step by step.

### Issue: Need specific operation
**Solution:** Use appropriate executor agent (worktree, github, test, or code).

## Quick Reference

| Task | Old Method | New Method |
|------|------------|------------|
| Create issue | WorkflowManager Phase 2 | `gh issue create` per CLAUDE.md |
| Create worktree | WorktreeManager agent | `git worktree add` or WorktreeExecutor |
| Run tests | WorkflowManager Phase 6 | Direct commands or TestExecutor |
| Create PR | WorkflowManager Phase 8 | `gh pr create` per CLAUDE.md |
| Parallel tasks | OrchestratorAgent | Follow CLAUDE.md parallel guidelines |

## Migration Checklist

- [ ] Read new CLAUDE.md with integrated orchestration
- [ ] Understand 11-phase workflow
- [ ] Learn simplified executor agents
- [ ] Practice direct execution without delegation
- [ ] Update any scripts or automation

## Getting Help

If you encounter issues during migration:
1. Check CLAUDE.md for comprehensive instructions
2. Review executor agent documentation
3. Consult this migration guide
4. Create an issue if something is unclear

Remember: The goal is simplification. When in doubt, follow CLAUDE.md directly rather than looking for an agent to delegate to.
