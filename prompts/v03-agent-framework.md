# Implement Agent Framework for Gadugi v0.3

## Task Description
Fix and complete the Agent Framework implementation with BaseAgent and tool registry.

## Requirements
1. Fix all 8 pyright errors in .claude/framework/
2. Ensure BaseAgent class properly integrates with Event Router
3. Implement complete tool registry functionality
4. Create comprehensive tests for the framework

## Current Issues to Fix
- Import errors between modules
- Type annotation issues
- Event router integration
- Tool registry implementation

## Technical Details
- Framework location: .claude/framework/
- Main components:
  - base_agent.py - BaseAgent class
  - tool_registry.py - Tool registration and management
  - agent_metadata.py - Agent metadata handling
  - agent_response.py - Response structures

## Execution Requirements
- Use `uv run` for all Python commands
- Run `uv run pyright .claude/framework/` to verify fixes
- Create and run tests with `uv run pytest`
- Ensure all imports work correctly

/agent:workflow-manager

Execute complete workflow for Agent Framework implementation
