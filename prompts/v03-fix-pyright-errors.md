# Fix All Pyright Errors in v0.3 Components

## Task Description
Fix all remaining pyright errors across v0.3 components to achieve 100% clean code.

## Components to Fix

### Recipe Executor (1 error)
- Location: .claude/agents/recipe-executor/recipe_executor.py
- Errors: 1 pyright error

### Event Router (14 errors)
- Location: .claude/services/event-router/
- Errors: 14 pyright errors across 6 files

### MCP Service (1 error)
- Location: .claude/services/mcp/mcp_service.py
- Errors: 1 pyright error

### Orchestrator (16 errors)
- Location: .claude/agents/orchestrator/
- Errors: 16 pyright errors across 4 files

## Requirements
1. Fix ALL pyright errors - zero tolerance
2. Ensure all imports are correct
3. Fix all type annotations
4. Handle all async/await properly
5. Run `uv run pyright <path>` to verify each fix
6. Do NOT introduce new errors while fixing

## Execution Requirements
- Use `uv run` for all Python commands
- Test each component after fixing
- Ensure no regressions
- Clean up worktree after completion

/agent:workflow-manager

Execute complete workflow to fix all pyright errors
