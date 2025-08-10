# Orchestrator: Execute Gadugi v0.3 Implementation Tasks

## Governance Notice
This orchestration request MUST delegate ALL tasks to WorkflowManager instances via 'claude -p' subprocess invocation as per Issue #148 requirements.

## Tasks for Parallel Execution

### Task 1: Neo4j Setup
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-neo4j-setup.md
- Priority: High (others depend on this)
- Estimated time: 15 minutes

### Task 2: MCP Service Implementation  
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-mcp-service.md
- Dependencies: Task 1 (Neo4j must be running)
- Priority: High
- Estimated time: 20 minutes

### Task 3: Agent Framework Implementation
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-agent-framework.md
- Priority: High (other agents depend on this)
- Estimated time: 20 minutes

## Execution Plan
1. Execute Task 1 (Neo4j Setup) first
2. Execute Tasks 2 and 3 in parallel after Task 1 completes
3. Each task MUST go through complete 11-phase WorkflowManager workflow
4. Use worktree isolation for each task
5. All tasks must pass quality gates (pyright, ruff, pytest)

## Important Requirements
- Each task MUST be delegated to WorkflowManager via `claude -p <prompt_file>`
- NO direct execution - everything through WorkflowManager
- All Python commands must use `uv run` prefix
- Each task creates its own issue, branch, and PR
- Phase 9 must invoke code-reviewer agent

/agent:orchestrator-agent

Execute the three tasks with proper dependencies and parallel execution where possible.