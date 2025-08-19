# Task 3: Implement Agent Framework

## Objective
Create a REAL, working Agent Framework that integrates with the Event Router.

## Requirements
1. Must provide BaseAgent class that actually works
2. Must have Tool registry that functions
3. Must integrate with Event Router for communication
4. Must support async operations
5. Use Recipe Executor to generate from recipe if available

## Technical Details
- Location: `.claude/framework/`
- Integration: Event Router (already working)
- Pattern: Async/await with proper event handling
- Communication: JSON messages via Event Router

## Implementation Components

### 1. BaseAgent (`base_agent.py`)
```python
class BaseAgent:
    - __init__(name, description, tools)
    - async execute(task)
    - async handle_event(event)
    - register_tool(tool)
    - get_capabilities()
```

### 2. Tool Registry (`tool_registry.py`)
```python
class ToolRegistry:
    - register_tool(tool)
    - get_tool(name)
    - list_tools()
    - execute_tool(name, params)
```

### 3. Event Integration (`event_integration.py`)
- Connect to Event Router
- Subscribe to agent events
- Publish agent responses
- Handle async messaging

### 4. Agent Manager (`agent_manager.py`)
- Load agent configurations
- Instantiate agents
- Route tasks to agents
- Monitor agent health

## Example Agent Implementation
Create a sample agent to prove the framework works:
- `sample_agent.py` - Simple agent that uses the framework
- Responds to events
- Uses tools from registry
- Demonstrates async execution

## Success Criteria
- Can create agents by extending BaseAgent
- Tool registry works with real tools
- Agents communicate via Event Router
- Sample agent responds to events
- Framework handles errors gracefully

## Files to Create
- `.claude/framework/base_agent.py`
- `.claude/framework/tool_registry.py`
- `.claude/framework/event_integration.py`
- `.claude/framework/agent_manager.py`
- `.claude/framework/sample_agent.py`
- `.claude/framework/tests/test_framework.py`
