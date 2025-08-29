# Orchestration & Workflow Management Instructions

## When to Load This File
Load when you need to:
- Manage complex multi-task workflows
- Coordinate parallel execution
- Use orchestrator or WorkflowManager agents
- Handle task dependencies

## Core Orchestration Pattern

### 1. Task Analysis
Break work into discrete, independent tasks that can run in parallel.

### 2. Dependency Detection
- **Parallel**: Different files, no shared dependencies
- **Sequential**: Same files, shared state, import dependencies

### 3. Execution via Orchestrator

#### Create Prompt Files
```bash
# /prompts/fix-bug-issue-256.md
Task: Fix the specific bug
Issue: #256
Requirements: Clear specifications
```

#### Invoke Orchestrator
```
/agent:OrchestratorAgent

Execute these prompts in parallel:
- fix-bug-issue-256.md
- add-feature-issue-257.md
```

## Orchestrator Implementation Details

### Architecture Components
- `orchestrator_main.py`: Central coordination
- `process_registry.py`: Process tracking
- `execution_engine.py`: Spawns subprocesses
- `worktree_manager.py`: Creates isolated worktrees

### Command Structure
```bash
claude \
  -p "Read and follow: /prompts/[task].md" \
  --dangerously-skip-permissions \
  --verbose \
  --max-turns=2000 \
  --output-format json
```

## Workflow Manager Pattern

### 13-Phase Workflow (MANDATORY)
1. Initial Setup
2. Issue Creation
3. Branch Management
4. Research and Planning
5. Implementation
6. Testing (Quality Gates)
7. Documentation
8. Pull Request
9. Code Review
10. Review Response
11. Settings Update
12. Deployment Readiness
13. Team Coach Reflection

### Governance Requirements
- Orchestrator MUST delegate to WorkflowManager
- Direct execution is PROHIBITED
- All phases MUST be executed
- State tracking throughout

## Parallel Execution Patterns

### Shell Script Pattern
```bash
#!/bin/bash
for task in "$@"; do
    (
        WORKTREE=".worktrees/task-${task}"
        git worktree add "$WORKTREE" -b "feature/task-${task}"
        cd "$WORKTREE"
        # Execute workflow
    ) &
    echo $! >> .task_pids
done
wait
```

### Python Pattern
```python
import asyncio
async def execute_task(task_id, description):
    worktree = f".worktrees/task-{task_id}"
    # Create worktree and execute
    
async def execute_parallel(tasks):
    results = await asyncio.gather(*[
        execute_task(t['id'], t['desc']) 
        for t in tasks
    ])
    return results
```

## Emergency Procedures

### Emergency Hotfix Exception
**Only when ALL are true:**
- Production down/compromised
- Immediate security risk
- Fix < 10 lines
- No time for workflow

**Procedure:**
1. Create issue with `emergency` label
2. Work on main (exception)
3. Minimal changes only
4. Clear commit attribution
5. Create follow-up issue
6. Return to normal workflow

## Common Mistakes to Avoid
- ❌ Direct claude invocation without orchestrator
- ❌ Skipping workflow phases
- ❌ Manual file editing
- ❌ Executing without prompt files
- ❌ Bypassing WorkflowManager