# Agent Implementation Guide

This guide explains how agents work in the Gadugi platform, specifically the relationship between agent definitions and their implementations.

## Agent Architecture

Gadugi agents consist of two parts:

1. **Agent Definition** (`.claude/agents/[agent-name].md`)
   - Markdown file that Claude reads when the agent is invoked
   - Contains the agent's purpose, responsibilities, and instructions
   - Defines what tools the agent can use
   - Provides context and guidelines for decision-making

2. **Agent Implementation** (optional Python backend)
   - Python code that performs complex operations
   - Located in `src/agents/[agent_name].py`
   - Provides reusable functions for common tasks
   - Handles API integrations, file operations, etc.

## How Agents Work

### 1. Simple Agents (Definition Only)
Many agents only need a definition file:

```
/agent:CodeReviewer

Task: Review PR #123
```

Claude reads `.claude/agents/CodeReviewer.md` and uses built-in tools (Read, Write, Bash, etc.) to complete the task.

### 2. Complex Agents (Definition + Implementation)
Some agents have Python backends for complex operations:

```
/agent:ProgramManager

Task: Triage all unlabeled issues
```

Claude:
1. Reads `.claude/agents/ProgramManager.md` for instructions
2. Imports `src/agents/program_manager.py`
3. Calls appropriate functions (e.g., `triage_unlabeled_issues()`)
4. Reports results back to the user

## Agent Types in Gadugi

### Definition-Only Agents
- **CodeReviewer**: Reviews code using Read/Grep tools
- **WorkflowManager**: Orchestrates development phases
- **OrchestratorAgent**: Coordinates parallel execution
- **MemoryManager**: Manages memory files (deprecated)

### Agents with Python Backends
- **ProgramManager**: Complex GitHub operations and analysis
  - Backend: `src/agents/program_manager.py`
  - Handles issue triage, priority management, README updates

- **PrBacklogManager**: PR delegation and coordination
  - Backend: `src/agents/pr_backlog_manager/`
  - Complex state management and delegation logic

## Creating a New Agent

### Step 1: Create Agent Definition
Create `.claude/agents/my-agent.md`:

```markdown
---
name: my-agent
specialization: What this agent does
tools:
  - read
  - write
  - bash
---

You are the My Agent, responsible for...

## Core Responsibilities
- Task 1
- Task 2

## How to Invoke This Agent
\```
/agent:my-agent

Task: Do something specific
\```
```

### Step 2: Create Python Backend (if needed)
Create `src/agents/my_agent.py` for complex operations:

```python
class MyAgent:
    def __init__(self):
        self.memory = AgentMemoryInterface("agent-001", "my-agent")

    def perform_complex_task(self):
        # Implementation here
        pass
```

### Step 3: Test the Agent
1. Unit tests for Python backend: `tests/test_my_agent.py`
2. Integration test by invoking: `/agent:my-agent`

## Best Practices

### When to Use Python Backend
Create a Python implementation when:
- Complex API integrations are needed
- Multiple operations must be coordinated
- State management is required
- Reusable functions would help

### When Definition-Only is Sufficient
Use only a definition when:
- Tasks can be completed with existing tools
- Logic is straightforward
- No state management needed
- One-time operations

### Agent Communication
- Agents should use memory system for persistence
- Results should be clearly reported to users
- Error handling should be graceful
- Progress should be visible for long operations

## Example: Program Manager

The Program Manager demonstrates the full pattern:

**Definition** (`.claude/agents/ProgramManager.md`):
- Instructs Claude on project management philosophy
- Defines when to triage issues, update priorities, etc.
- Specifies how to invoke the agent

**Implementation** (`src/agents/program_manager.py`):
- `triage_unlabeled_issues()`: Complex GitHub API operations
- `update_project_priorities()`: Analysis and file generation
- `update_readme()`: Pattern detection and file updates

**Invocation**:
```
/agent:ProgramManager

Task: Run full project maintenance
```

Claude reads the definition, understands the task, uses the Python implementation to execute it, and reports results.

## Summary

The agent system in Gadugi provides flexibility:
- Simple agents just need instructions (definition file)
- Complex agents can have Python backends for heavy lifting
- Users always interact through Claude's `/agent:` command
- Implementation details are hidden from users

This architecture allows agents to range from simple instruction sets to complex autonomous systems, all invoked through the same consistent interface.
