# Agent Hierarchy for Development Workflows

## Overview

This document explains the proper agent hierarchy for executing development workflows in the Gadugi multi-agent orchestration platform.

## Agent Hierarchy Diagram

```
┌─────────────────────────┐
│   Program Manager       │ ← Maintains project health
│ (Project Orchestrator)  │
└───────────┬─────────────┘
            │
            ├─── Manages → Issue Pipeline (triage, labeling)
            ├─── Updates → Project Priorities (.memory)
            ├─── Maintains → README & Documentation
            │
            └─── Coordinates with ↓

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
│    WorkflowManager      │ ← Or start here for single tasks
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

### Use Program Manager when:
- Running regular project maintenance (manually or via cron)
- Triaging unlabeled issues
- Updating project priorities
- Keeping documentation current
- Example: `python src/agents/program_manager.py full`

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

1. **Project Health**: Program Manager maintains issue hygiene and priorities
2. **Automation**: All phases execute automatically
3. **Consistency**: Same workflow every time
4. **State Tracking**: Progress saved and resumable
5. **Code Reviews**: Phase 9 never skipped
6. **Parallelization**: 3-5x faster for multiple tasks
7. **Error Handling**: Graceful recovery from failures
8. **Documentation**: README and docs stay current automatically

## Program Manager Details

The Program Manager is responsible for:

### Issue Pipeline Management
- **Triage**: Automatically labels unlabeled issues based on content
- **Pipeline**: Moves issues through lifecycle stages (idea → draft → ready)
- **Hygiene**: Ensures single lifecycle label per issue
- **Classification**: Detects bugs, well-structured drafts, and raw ideas

### Project Coordination
- **Priorities**: Maintains `.memory/project/priorities.md` with top 5 priorities
- **Milestones**: Tracks milestone progress and deadlines
- **Recommendations**: Identifies bottlenecks and stale issues
- **Metrics**: Provides pipeline status and velocity insights

### Documentation
- **README**: Detects new features from PRs and updates README
- **Agents**: Identifies new agents not documented
- **Automation**: Can run via cron for continuous maintenance

## Common Mistakes

1. **Wrong**: Manually creating issues, branches, and PRs
2. **Wrong**: Using WorkflowManager for multiple independent tasks
3. **Wrong**: Skipping OrchestratorAgent when parallelization is possible
4. **Wrong**: Manually triaging issues when Program Manager can automate
5. **Right**: Let agents handle the entire workflow
6. **Right**: Use OrchestratorAgent first, it will spawn WorkflowManagers
7. **Right**: Run Program Manager regularly for project health

## Understanding Agent Implementation

Agents in Gadugi work through Claude's `/agent:` command. Some agents are purely instruction-based (just a `.claude/agents/*.md` file), while others have Python backends for complex operations. Users never need to run Python scripts directly - Claude handles all the implementation details.

For detailed information about how agents are implemented, see [AGENT_IMPLEMENTATION_GUIDE.md](docs/AGENT_IMPLEMENTATION_GUIDE.md).