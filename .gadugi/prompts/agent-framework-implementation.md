# Agent Framework Implementation

## Task: Create Base Agent Framework (#238)

### Objective
Create the foundational agent framework that provides a standard structure for all agents in the Gadugi platform.

### Requirements

#### System Architecture
- **Location**: `.claude/framework/`
- **Core Components**:
  - BaseAgent abstract class
  - YAML frontmatter parser
  - Event handling system
  - Tool invocation framework
  - Memory integration

#### Core Features to Implement

1. **BaseAgent Class**
   - Lifecycle methods: init(), register(), listen(), process(), cleanup()
   - Event subscription and handling
   - Tool registration and invocation
   - Memory persistence integration
   - State management

2. **YAML Frontmatter Parsing**
   - Parse agent definition files (.md)
   - Extract metadata (name, version, tools, events)
   - Validate agent specifications
   - Generate agent configuration

3. **Protobuf Event Handling**
   - Integration with Event Router
   - Event serialization/deserialization
   - Priority-based event processing
   - Event filtering and routing

4. **MCP Memory Integration**
   - Store agent state and context
   - Retrieve relevant memories
   - Pattern learning from interactions
   - Context persistence across sessions

5. **Tool Invocation Framework**
   - Tool registry management
   - Parameter validation
   - Result handling
   - Error recovery
   - Tool chaining support

6. **Interactive Q&A Support**
   - Handle hasQuestion events
   - Process needsApproval events
   - User interaction patterns
   - Response formatting

7. **Agent Template and Examples**
   - Standard agent template
   - Example implementations
   - Best practices documentation
   - Agent development guide

### Implementation Components

```python
# base_agent.py structure
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

class BaseAgent(ABC):
    def __init__(self, agent_def_path: Path):
        self.metadata = self._parse_frontmatter(agent_def_path)
        self.tools = self._register_tools()
        self.event_router = EventRouterService()
        self.memory_system = MemorySystem()
        self.state = {}

    @abstractmethod
    async def init(self) -> None:
        """Initialize agent resources"""
        pass

    @abstractmethod
    async def register(self) -> None:
        """Register with orchestrator"""
        pass

    @abstractmethod
    async def listen(self) -> None:
        """Start listening for events"""
        pass

    @abstractmethod
    async def process(self, event: Event) -> Response:
        """Process incoming events"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

    async def invoke_tool(self, tool_name: str, params: Dict) -> Any:
        """Invoke a registered tool"""
        pass

    async def ask_question(self, question: str) -> str:
        """Interactive Q&A support"""
        pass

    async def request_approval(self, action: str) -> bool:
        """Request user approval"""
        pass
```

### Agent Template Structure

```yaml
---
name: ExampleAgent
version: 1.0.0
description: Example agent implementation
tools:
  - name: file_reader
    required: true
  - name: code_analyzer
    required: false
events:
  subscribes:
    - code.analysis.requested
    - file.changed
  publishes:
    - analysis.completed
    - error.occurred
settings:
  max_retries: 3
  timeout: 30
---

# Example Agent

## Purpose
Describe the agent's purpose and capabilities.

## Workflow
1. Listen for events
2. Process requests
3. Invoke tools
4. Return results

## Implementation
Actual agent logic and instructions.
```

### Testing Requirements
- Unit tests for BaseAgent class
- Integration tests with Event Router
- Memory persistence tests
- Tool invocation tests
- YAML parsing validation
- Interactive Q&A testing

### Success Criteria
- ✅ BaseAgent class fully implemented
- ✅ YAML frontmatter parsing functional
- ✅ Event handling integrated
- ✅ Memory system connected
- ✅ Tool framework operational
- ✅ Interactive support working
- ✅ Template and examples created
- ✅ All tests passing with uv run pytest
- ✅ Code is pyright clean
- ✅ Code is ruff formatted
