# Deprecated Agents - V0.3 Migration


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview
These agents are DEPRECATED as of V0.3 migration. They used complex delegation patterns that have been replaced by the simplified executor architecture.

## Removed Agents (as of latest update)

### 1. OrchestratorAgent.md (REMOVED)
- **Reason**: Agents can no longer invoke other agents via Task tool
- **Replacement**: Use Task tool directly for parallel execution
- **Migration**: Spawn multiple Claude instances via Task tool

### 2. WorkflowManager.md (REMOVED)
- **Reason**: Agents can no longer invoke other agents
- **Replacement**: 13-phase workflow integrated into CLAUDE.md
- **Migration**: Developers follow workflow phases themselves

### 3. WorkflowManagerPhase9Enforcement.md (REMOVED)
- **Reason**: Part of WorkflowManager which is now removed
- **Replacement**: Phase 9 enforcement in CLAUDE.md workflow
- **Migration**: Follow the review phase in the 13-phase workflow

### 4. WorkflowManagerSimplified.md (REMOVED)
- **Reason**: Variant of WorkflowManager, no longer needed
- **Replacement**: 13-phase workflow in CLAUDE.md
- **Migration**: Follow CLAUDE.md instructions

### 5. .claude/agents/orchestrator/ directory (REMOVED)
- **Reason**: Agent-based orchestrator no longer viable
- **Replacement**: Infrastructure remains in .claude/orchestrator/
- **Migration**: Use orchestrator infrastructure, not agent

### 6. .claude/agents/workflow-manager/ directory (REMOVED)
- **Reason**: Agent-based workflow manager no longer viable
- **Replacement**: Workflow instructions in CLAUDE.md
- **Migration**: Follow 13-phase workflow manually

### 4. AgentUpdater.md
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
# Instead of: /agent:OrchestratorAgent
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
- .claude/agents/OrchestratorAgent.md
- .claude/agents/WorkflowManager.md
- .claude/agents/WorkflowManagerPhase9Enforcement.md
- .claude/agents/WorkflowManagerSimplified.md
- .claude/agents/AgentUpdater.md

Keep this file as documentation of the migration.
