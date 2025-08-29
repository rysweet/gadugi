# Gadugi V0.3 - Simplified Executor Architecture

## Overview

Gadugi V0.3 represents a fundamental architectural simplification, moving from complex agent delegation chains to simple, single-purpose executors coordinated directly by CLAUDE.md.

## Architecture

### Old Architecture (Complex Delegation)
```
OrchestratorAgent → WorkflowManager → TaskAnalyzer → WorktreeManager → CodeWriter → TestRunner
```

### New Architecture (Simple Executors)
```
CLAUDE.md → execute('worktree') → execute('code') → execute('test') → execute('github')
```

## Directory Structure

```
.claude/
├── executors/           # Single-purpose executors
│   ├── base_executor.py     # Abstract base class
│   ├── code_executor.py     # File operations
│   ├── test_executor.py     # Test execution
│   ├── github_executor.py   # GitHub operations
│   └── worktree_executor.py # Git worktree management
├── engines/            # Migrated Python implementations
├── services/           # Service layer (unchanged)
├── tests/             # Integration tests
└── agents/            # Agent specifications (being deprecated)
```

## Core Principles

### 1. NO DELEGATION
Executors MUST NOT call or delegate to other agents. All operations use direct tools only.

### 2. SINGLE PURPOSE
Each executor has exactly one responsibility:
- **Code Executor**: File operations (write/read/edit)
- **Test Executor**: Test execution (pytest/unittest/jest/mocha)
- **GitHub Executor**: GitHub operations (issues/PRs)
- **Worktree Executor**: Git worktree management

### 3. DIRECT ORCHESTRATION
All workflow coordination happens in CLAUDE.md, not in agents.

### 4. STRUCTURED RESULTS
All executors return consistent result dictionaries for easy orchestration.

## Usage

### Basic Usage

```python
from .claude.executors import execute

# Write a file
result = execute('code', {
    'action': 'write',
    'file_path': 'hello.py',
    'content': 'print("Hello, World!")'
})

# Run tests
result = execute('test', {
    'test_framework': 'pytest',
    'test_path': 'tests/'
})

# Create GitHub issue
result = execute('github', {
    'operation': 'create_issue',
    'title': 'Bug report',
    'body': 'Description...'
})

# Create worktree
result = execute('worktree', {
    'operation': 'create',
    'task_id': '123',
    'branch_name': 'fix/bug-123'
})
```

### Orchestration Example

```python
# Complete workflow orchestration
def execute_task(task_id, description):
    # 1. Create isolated worktree
    worktree = execute('worktree', {
        'operation': 'create',
        'task_id': task_id
    })

    # 2. Write code in worktree
    code_result = execute('code', {
        'action': 'write',
        'file_path': f"{worktree['worktree_path']}/solution.py",
        'content': '# Implementation here'
    })

    # 3. Run tests
    test_result = execute('test', {
        'test_framework': 'pytest',
        'working_dir': worktree['worktree_path']
    })

    # 4. Create PR if tests pass
    if test_result['success']:
        pr = execute('github', {
            'operation': 'create_pr',
            'title': f'Fix: {description}',
            'body': 'All tests passing'
        })

    return {'task_id': task_id, 'success': test_result['success']}
```

## Migration Guide

### For Users of Old Architecture

Instead of using agent delegation:
```python
# OLD WAY - Don't use this
/agent:OrchestratorAgent
Execute workflow for task-123.md
```

Use direct executor orchestration:
```python
# NEW WAY - Use this
from .claude.executors import execute

# Direct orchestration of executors
worktree = execute('worktree', {'operation': 'create', 'task_id': '123'})
execute('code', {'action': 'write', 'file_path': '...', 'content': '...'})
execute('test', {'test_framework': 'pytest', 'working_dir': worktree['worktree_path']})
```

### Key Changes

1. **No More Agent Chains**: Replace delegation with direct executor calls
2. **CLAUDE.md Orchestration**: All workflow logic in main instructions
3. **Single Entry Points**: Each executor has one `execute()` method
4. **Explicit Control**: You control the exact sequence of operations

## Executor Reference

### Code Executor

**Purpose**: File operations

**Operations**:
- `write`: Create new file
- `read`: Read file contents
- `edit`: Modify existing file

**Example**:
```python
execute('code', {
    'action': 'write',
    'file_path': 'src/app.py',
    'content': 'def main():\n    pass'
})
```

### Test Executor

**Purpose**: Run tests

**Frameworks**: pytest, unittest, jest, mocha

**Features**:
- Automatic UV project detection
- Coverage support
- Parallel test execution

**Example**:
```python
execute('test', {
    'test_framework': 'pytest',
    'test_path': 'tests/',
    'options': {'coverage': True}
})
```

### GitHub Executor

**Purpose**: GitHub operations via gh CLI

**Operations**:
- `create_issue`: Create new issue
- `create_pr`: Create pull request
- `list_issues`: List issues
- `merge_pr`: Merge PR (requires user approval)
- `pr_status`: Check PR status

**Example**:
```python
execute('github', {
    'operation': 'create_pr',
    'title': 'Feature: Add logging',
    'body': 'This PR adds comprehensive logging'
})
```

### Worktree Executor

**Purpose**: Git worktree management

**Operations**:
- `create`: Create new worktree
- `remove`: Remove worktree
- `list`: List all worktrees
- `status`: Check worktree status
- `cleanup`: Remove old worktrees

**Example**:
```python
execute('worktree', {
    'operation': 'create',
    'task_id': '456',
    'branch_name': 'feature/new-feature'
})
```

## Testing

Run integration tests:
```bash
cd .claude
python -m pytest tests/test_executors.py -v
```

Test coverage:
- 17 test cases
- Validates NO DELEGATION principle
- Tests all executor operations
- Verifies orchestration interface

## Benefits of V0.3 Architecture

1. **Simplicity**: No complex delegation chains
2. **Reliability**: Fewer points of failure
3. **Testability**: Each executor tested in isolation
4. **Maintainability**: Clear, single-purpose components
5. **Performance**: Direct execution without overhead
6. **Debuggability**: Easy to trace execution flow

## Deprecated Components

The following components are deprecated in V0.3:
- `OrchestratorAgent.md` - Use CLAUDE.md orchestration
- `WorkflowManager.md` - Use direct phase execution
- Agent delegation patterns - Use executor calls

See `.claude/agents/DEPRECATED_AGENTS.md` for migration details.

## Contributing

When adding new executors:
1. Inherit from `BaseExecutor`
2. Implement single `execute()` method
3. Use only direct tool calls (no agent delegation)
4. Return structured result dictionary
5. Add comprehensive tests
6. Update this documentation

## Support

For questions or issues with the V0.3 migration:
1. Check `MIGRATION_STATUS.md` for current status
2. Review `MIGRATION_PLAN_V0.3.md` for details
3. See `DEPRECATED_AGENTS.md` for old pattern migration

---

*Gadugi V0.3 - Simplified, Reliable, Maintainable*
