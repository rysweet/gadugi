# Gadugi Multi-Agent Framework for Coding and Systems

# Concepts:

## Agents

- location: /repo/agents
- Agents are not bound to a specific host/framework (can be used in Roo or GH Copilot or Claude)
- Agents are started as subprocesses by the event-router (usually in containers)
- Use Claude Code directory and yaml format
- Agents have
  - id 
  - names(namespace)
  - descriptions 
  - job descriptions (the prompt)
  - events that they care about (listen to)
  - events that they emit
    - started (input)
    - stopped (output)
    - hasQuestion (question)
    - needsApproval (command)
  - events are defined in protobuf
  - workflows
  - tools (incl entry for mcp service)
  - if needs source rather than prompts only can build workflows in src that live in /src/agents/{agent}/workflows/
  - knowledge - these are specific documents about subject matter that the agent can use to answer questions or perform tasks
  - memories - these are shared memories that the agent can use to remember things across sessions
  - docs on what the agent is for, how to use it
  - if an agent needs interactive answers it will publish hasQuestion or needsApproval and listen for Response event

## Orchestration Agent

The Orchestration Agent is responsible for managing the overall workflow of the system. It coordinates the activities of other agents and ensures that they work together effectively to solve complex problems. The Orchestration Agent is aware of the capabilities and limitations of each agent and can allocate tasks accordingly.

The Orchestration Agent delegates aspects of the workflow to sub-agents, which are specialized agents that handle specific tasks or domains. These sub-agents can be invoked by the Orchestration Agent to perform tasks such as code generation, testing, deployment, and more.

Some invocations of sub-agents will be done directly and synchronously, while others will be done through the event router, which allows for asynchronous communication and coordination between agents.

The Orchestration Agent should use sub-agents to analyze a task and decompose it into sub-tasks, and then run those sub-tasks in parallel where possible to reduce total execution time.