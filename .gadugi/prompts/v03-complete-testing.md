# Complete Testing and Quality Assurance for v0.3

## Task Description
Run comprehensive testing and quality checks on all v0.3 components.

## Testing Requirements

### 1. Unit Tests
- Run `uv run pytest` on all components
- Ensure all tests pass
- Add missing tests where needed
- Achieve minimum 80% coverage

### 2. Integration Tests
- Test Neo4j connectivity
- Test MCP Service endpoints
- Test Event Router messaging
- Test Orchestrator parallel execution
- Test Recipe Executor generation

### 3. Quality Checks
- Run `uv run ruff format .claude/`
- Run `uv run ruff check .claude/`
- Run `uv run pyright .claude/`
- Ensure all pass with 0 issues

### 4. End-to-End Testing
- Test complete workflow from prompt to PR
- Verify orchestrator delegates to WorkflowManager
- Ensure all 11 phases execute properly
- Verify worktree cleanup

## Components to Test
1. Recipe Executor
2. Event Router
3. MCP Service
4. Neo4j Service
5. Agent Framework
6. Orchestrator
7. Task Decomposer
8. Team Coach

## Execution Requirements
- Use `uv run` for all commands
- Document all test results
- Fix any failing tests
- Clean up worktree after completion

/agent:WorkflowManager

Execute complete workflow for testing and quality assurance
