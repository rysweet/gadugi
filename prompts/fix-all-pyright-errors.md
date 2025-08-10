# Fix All Pyright Errors in v0.3 Components

Fix all remaining pyright errors across v0.3 components to achieve 100% clean code.

## Components to Fix

### Recipe Executor (1 error)
- Location: .claude/agents/recipe-executor/recipe_executor.py

### Event Router (14 errors)  
- Location: .claude/services/event-router/

### MCP Service (1 error)
- Location: .claude/services/mcp/mcp_service.py

### Orchestrator (16 errors)
- Location: .claude/agents/orchestrator/

## Requirements
- Fix ALL pyright errors - zero tolerance
- Run `uv run pyright <path>` to verify each fix
- Do NOT introduce new errors while fixing
- Test each component after fixing