# Implement Agent Framework

## Objective
Fix pyright errors and implement the agent framework for Gadugi v0.3

## Requirements
1. Fix the 8 pyright errors in .claude/framework/
2. Ensure BaseAgent class integrates with Event Router
3. Create tool registry implementation

## Technical Details
- Agent framework is located in .claude/framework/
- BaseAgent class needs proper Event Router integration
- Tool registry needs to be implemented for agent tool management
- Framework supports multiple agent types

## Error Resolution
- Address all 8 pyright type checking errors in framework
- Ensure proper type annotations
- Fix any circular import issues

## Implementation Tasks
1. Fix pyright errors in BaseAgent and related classes
2. Implement Event Router integration in BaseAgent
3. Create ToolRegistry class with:
   - Tool registration methods
   - Tool discovery mechanisms
   - Tool execution wrapper

## Testing Requirements
- Create unit tests for BaseAgent
- Test Event Router integration
- Test Tool Registry functionality
- Use `uv run pytest` for test execution

## Success Criteria
- All pyright errors resolved
- BaseAgent properly integrated with Event Router
- Tool Registry implemented and functional
- All tests passing
