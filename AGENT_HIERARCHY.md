# Agent Hierarchy for Development Workflows

## Overview

This document explains the proper agent hierarchy for executing development workflows in the Blarify project.

## Agent Hierarchy Diagram

```
┌─────────────────────────┐
│   OrchestratorAgent     │ ← Start here for multiple tasks
│ (Parallel Coordinator)  │
└───────────┬─────────────┘
            │
            ├─── Invokes → TaskAnalyzer (dependency analysis)
            ├─── Invokes → WorktreeManager (git isolation)
            ├─── Invokes → ExecutionMonitor (parallel tracking)
            │
            └─── Spawns multiple ↓
                        
┌─────────────────────────┐
│    WorkflowManager       │ ← Or start here for single tasks
│  (Workflow Executor)    │
└───────────┬─────────────┘
            │
            ├─── Phase 1: Setup
            ├─── Phase 2: Issue Creation
            ├─── Phase 3: Branch Management
            ├─── Phase 4: Research
            ├─── Phase 5: Implementation
            ├─── Phase 6: Testing
            ├─── Phase 7: Documentation
            ├─── Phase 8: PR Creation
            │
            └─── Phase 9: Invokes → CodeReviewer
                                           │
                                           └─── May invoke → CodeReviewResponse
```

## When to Use Each Agent

### Use OrchestratorAgent when:
- You have multiple independent tasks to execute
- Tasks can be parallelized (no file conflicts)
- You want 3-5x speed improvement
- Example: Writing tests for 5 different modules

### Use WorkflowManager when:
- You have a single complex task
- The task requires sequential phases
- No parallelization opportunity
- Example: Implementing a single new feature

### Never manually execute:
- ❌ `gh issue create`
- ❌ `git checkout -b`
- ❌ `gh pr create`
- ❌ Individual workflow phases

## Correct Usage Examples

### Multiple Tasks (Use OrchestratorAgent)
```
/agent:orchestrator-agent

Execute these specific prompts in parallel:
- test-definition-node.md
- test-relationship-creator.md
- fix-documentation-linker.md
```

### Single Task (Use WorkflowManager)
```
/agent:workflow-manager

Task: Execute workflow for /prompts/implement-new-feature.md
```

### Quick Fix (Manual allowed)
```
# For a typo fix or single-line change
git add README.md
git commit -m "fix: typo in README"
git push
```

## Benefits of Using Agents

1. **Automation**: All phases execute automatically
2. **Consistency**: Same workflow every time
3. **State Tracking**: Progress saved and resumable
4. **Code Reviews**: Phase 9 never skipped
5. **Parallelization**: 3-5x faster for multiple tasks
6. **Error Handling**: Graceful recovery from failures

## Common Mistakes

1. **Wrong**: Manually creating issues, branches, and PRs
2. **Wrong**: Using WorkflowManager for multiple independent tasks
3. **Wrong**: Skipping OrchestratorAgent when parallelization is possible
4. **Right**: Let agents handle the entire workflow
5. **Right**: Use OrchestratorAgent first, it will spawn WorkflowManagers