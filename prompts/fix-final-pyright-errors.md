# Fix ALL Remaining Pyright Errors

Fix all 447 remaining pyright errors to achieve ZERO errors.

Focus areas:
1. Team Coach (108 errors) - .claude/agents/team-coach/
2. Event Router (26 errors) - .claude/services/event-router/
3. Orchestrator (16 errors) - .claude/agents/orchestrator/
4. MCP Service (11 errors) - .claude/services/mcp/
5. Agent Framework (8 errors) - .claude/framework/
6. Recipe Executor (4 errors) - .claude/agents/recipe-executor/

Requirements:
- Fix actual issues, not just suppress
- Use `uv run pyright` to verify
- Achieve ZERO errors
- Create PR when complete
- This is a UV project - use `uv run` for all Python commands
