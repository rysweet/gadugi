---
id: test-agent
name: "Test Agent"
model: inheritdescription: "Simple test agent that outputs hello message"
tools:
  - name: "bash"
    type: "command_line"
events:
  emits:
    - "test-agent.started"
    - "test-agent.completed"
---

# Test Agent

I'm a simple test agent used to validate that the orchestrator works.

## What I Do

I output a hello message and confirm I'm working.

## Usage

```
/agent:test-agent
```

## Implementation

When called, I:
1. Output "Hello from test-agent"
2. Confirm I received any input parameters
3. Return a simple success message

This validates that:
- The orchestrator can start me
- The orchestrator can capture my output
- The basic subprocess execution works

I'm intentionally simple to focus on the orchestrator's core functionality.
