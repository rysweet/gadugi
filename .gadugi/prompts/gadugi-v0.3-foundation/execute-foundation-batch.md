# Execute Gadugi v0.3 Foundation Tasks

/agent:OrchestratorAgent

Execute these foundation tasks for Gadugi v0.3 implementation in parallel:

## Task 1: QA Framework Setup (Issue #242)
Set up comprehensive quality assurance framework:
- Configure UV for Python dependency management (all commands must use `uv run` prefix)
- Set up ruff for formatting (line length 100) and linting
- Configure pyright for strict type checking
- Set up pytest with coverage reporting
- Create pre-commit hooks for all quality checks
- Document the QA framework usage

## Task 2: Create Recipe Definitions (Issue #234)
Create recipe structure in `.claude/recipes/` directory:
- Create directories for: event-system, memory-system, agent-framework, orchestrator, TaskDecomposer, TeamCoach
- Each component needs: requirements.md, design.md, dependencies.json
- Focus on NEW v0.3 requirements, not current implementation
- Define clear interfaces and dependencies between components

## Task 3: Define Protobuf Schemas
Create protobuf definitions in `.claude/protos/`:
- common.proto with shared types (Timestamp, Metadata, Priority, Error)
- agent_events.proto (AgentStarted, AgentStopped, AgentHasQuestion, AgentNeedsApproval, AgentResponse)
- task_events.proto (TaskStarted, TaskProgress, TaskCompleted, TaskFailed)
- Generate Python bindings in generated/python/
- Create usage examples

## Task 4: Neo4j Database Setup
Set up Neo4j graph database:
- Create docker-compose.yml with Neo4j 5 Community Edition
- Define schema for Agent, Memory, Knowledge, Task nodes
- Create relationships: DELEGATES_TO, CREATES, EXECUTES, KNOWS, etc.
- Implement Python client with connection pooling
- Create initialization and test scripts

## Requirements
- All tasks can run in parallel (no dependencies)
- Focus on NEW v0.3 design, not preserving current code
- All Python code must use UV environment
- Code must be pyright clean and ruff formatted
- All tests must pass before completion
- Create proper documentation for each component

Please execute these tasks in parallel using separate worktrees for maximum efficiency.
