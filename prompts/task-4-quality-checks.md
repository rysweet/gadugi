# Task 4: Run Quality Checks

## Objective
Run comprehensive quality checks on all Gadugi v0.3 components and fix any issues found.

## Requirements
1. Run type checking with pyright
2. Run formatting with ruff format
3. Run linting with ruff check
4. Run all tests with pytest
5. Fix ALL issues found - no skipping

## Components to Check
1. **Recipe Executor** (`.claude/agents/recipe-executor/`)
2. **Event Router** (`.claude/services/event-router/`)
3. **Orchestrator** (`.claude/orchestrator/`)
4. **Neo4j Service** (`.claude/services/neo4j/`)
5. **MCP Service** (`.claude/services/mcp/`)
6. **Agent Framework** (`.claude/framework/`)

## Quality Check Commands
```bash
# Type checking
uv run pyright .claude/agents/recipe-executor/
uv run pyright .claude/services/event-router/
uv run pyright .claude/orchestrator/
uv run pyright .claude/services/mcp/
uv run pyright .claude/framework/

# Formatting
uv run ruff format .claude/

# Linting
uv run ruff check .claude/ --fix

# Testing
uv run pytest .claude/agents/recipe-executor/tests/
uv run pytest .claude/services/event-router/tests/
uv run pytest .claude/orchestrator/tests/
uv run pytest .claude/services/mcp/tests/
uv run pytest .claude/framework/tests/
```

## Issues to Fix
- Type errors
- Import errors
- Formatting inconsistencies
- Linting violations
- Test failures
- Missing docstrings
- Unused imports

## Success Criteria
- All pyright checks pass with no errors
- All code properly formatted
- No linting violations
- All tests pass
- Coverage > 80% for new code

## Files to Create/Modify
- Fix any files with issues
- Create missing test files
- Update type hints
- Add missing docstrings