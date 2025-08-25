
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

## Problem Solving Loop

The problem solving loop is at the core of the Orchestration Agent. It is a loop that runs until the problem is solved or the agent is stopped. The loop consists of the following steps:
- Problem Identification: The agent identifies the problem it is trying to solve.
- Information Gathering: The agent gathers information about the problem, including any relevant documents, knowledge, and memories.
- Analysis: The agent analyzes the information it has gathered to understand the problem better.
- Solution Design: The agent designs a solution to the problem based on its analysis.
- Refinement: The agent refines its solution based on feedback from the system or other agents.
- Implementation: The agent implements the solution, which may involve invoking other agents or tools.

## Generating New Agents

The Orchestration Agent or other agents can also generate new agents on the fly to handle specific tasks or problems. This involves:
- Identifying the need for a new agent based on the current workflow or problem space.
- Defining the capabilities and responsibilities of the new agent.
- Instantiating the new agent and integrating it into the existing workflow.
- New agents can be reusable (ie they now become part of the agent team) or ephemeral - they are used for a specific task and then discarded.

## Reflection Loop

Agent sessions end with a reflection loop that uses a Team Coach agent to reflect on the session using a special template. It collects information about the session, what went well, what could be improved, and any lessons learned. It then can suggest improvements to the agents prompts, improvements to the tools, additions to the agents memories, or new agents that can be created to solve specifc problems.

## Events:

- location: /repo/events
- Events are the communication mechanism between agents
- Events are defined in protobuf
- Events can be emitted by agents or the system
- Events can be listened to by the event router and then handed to agents
- Events can be used to trigger agent workflows
- Event has:
  - id
  - type ({agentname}.{eventname})
  - payload
- Known Events: 
  - started (input)
  - stopped (output)
  - hasQuestion (question)
  - needsApproval (command)
  - cancel (agent.id)

## Workflows:

- location: /repo/agents/{agent}/workflows/
- Workflows are ToDoLists in Markdown that define the steps an agent should take to complete a task.
- A workflow could also be a decision-making defined in schema-less XML (interpreted by the LLM) with process with tool calls for evals
- A workflow can be in code if it is wrapped in a workflow-tool call (but then the code lives /src/agents/{agent}/workflows/)

## Event Router:

- location: /repo/src/event-router
- Event router is the central hub for all events in the system
- Event router listens for events and invokes agents based on the events
- Event router is a service that runs in a container (as claude -p --json --dangerously-allow)
- Event router has a fast append-only store for agent events

## Graph Database:

- location: /repo/src/db
- graph database (containerized neo4j)
- runs as a service
- stores agent shared memory 

## MCP Service

- based on https://github.com/neo4j-contrib/mcp-neo4j/tree/main/servers/mcp-neo4j-memory
- sits in front of the graph database
- has operations from 

## Gadugi Agent:

- Gadugi agent(s)
- starts event router and graph db service 
- can invoke other agents directly (but they still emit events to event router)
- tries to remember (store) which agents are running
- is the installer and bootstrap point - starts/stops/installs/updates the Gadugi agents and the rest of the system
- reports on agent activity
- can stream filter of agent events 
- can send cancel events

## LLM Provider Proxy

- runs in a container
- uses https://github.com/fuergaosi233/claude-code-proxy
- sits in front of the LLM provider (Claude, OpenAI, etc.)
- provides a unified interface for LLM calls
- can be used to route calls to different LLM providers
- Agent processes are started with the env vars from the docs that configure them to use the proxy
- Future extension point for prompt rewriting/optimization/accounting/etc

## Design Patterns Library

- Location: /repo/design-patterns
- The system contains a library of design patterns that can be used by agents
- These design patterns are "recipes" for reusable components that can be used to solve common problems
- Design patterns are defined in a structured JSON format 
- A specific "recipe tool" can be used to generate code for each recipe.
- Here is a version of the recipe-tool: https://github.com/microsoft/recipe-tool that you can use
- That repo has examples of recipes in the /recipes directory
