# Deprecated Agents - V0.3 Migration

## Overview
These agents are DEPRECATED as of V0.3 migration. They used complex delegation patterns that have been replaced by the simplified executor architecture.

## Deprecated Agents

### 1. orchestrator-agent.md
- **Reason**: Complex delegation to WorkflowManager
- **Replacement**: Direct orchestration in CLAUDE.md using executors
- **Migration**: Use execute() calls to coordinate executors

### 2. workflow-manager.md
- **Reason**: Multi-phase workflow with agent delegation
- **Replacement**: Direct phase execution in CLAUDE.md
- **Migration**: Implement phases using executor calls

### 3. workflow-manager-phase9-enforcement.md
- **Reason**: Enforcement via delegation
- **Replacement**: Direct enforcement in CLAUDE.md
- **Migration**: Use GitHub executor for PR checks

### 4. agent-updater.md
- **Reason**: Updates via agent delegation
- **Replacement**: Direct file operations via code executor
- **Migration**: Use code executor for updates

## Migration Pattern

### Old Pattern (Delegation)
```
OrchestratorAgent 
  → delegates to WorkflowManager
    → delegates to TaskAnalyzer
    → delegates to WorktreeManager
    → delegates to CodeWriter
    → delegates to TestRunner
```

### New Pattern (Direct Orchestration)
```
CLAUDE.md orchestration:
  → execute('worktree', {create})
  → execute('code', {write})
  → execute('test', {run})
  → execute('github', {create_pr})
```

## How to Use New Architecture

Instead of invoking these deprecated agents, use the executor pattern:

```python
# Instead of: /agent:orchestrator-agent
# Use direct executor orchestration:

from .claude.executors import execute

# Create worktree
worktree = execute('worktree', {'operation': 'create', 'task_id': '123'})

# Write code
execute('code', {
    'action': 'write',
    'file_path': f"{worktree['worktree_path']}/file.py",
    'content': '...'
})

# Run tests
result = execute('test', {
    'test_framework': 'pytest',
    'working_dir': worktree['worktree_path']
})

# Create PR
if result['success']:
    execute('github', {
        'operation': 'create_pr',
        'title': 'Feature implementation'
    })
```

## Important Notes

1. **NO DELEGATION**: New executors cannot call other agents
2. **SINGLE PURPOSE**: Each executor does one thing only
3. **DIRECT ORCHESTRATION**: All coordination happens in CLAUDE.md
4. **SIMPLER ARCHITECTURE**: Fewer points of failure

## Files to Remove After Full Migration

Once migration is complete and validated, these files can be removed:
- .claude/agents/orchestrator-agent.md
- .claude/agents/workflow-manager.md
- .claude/agents/workflow-manager-phase9-enforcement.md
- .claude/agents/workflow-manager-simplified.md
- .claude/agents/agent-updater.md

Keep this file as documentation of the migration.