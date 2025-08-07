# Gadugi Agent Definitions

This directory contains the actual agent definitions for the Gadugi system.

## Important Note

These `.md` files are NOT documentation about agents - they ARE the agents themselves.
Each markdown file contains the complete instructions and logic that Claude Code executes when the agent is invoked.

## Agent Organization

Each agent has its own directory with:
- `AgentName.md` - The actual agent definition (the executable instructions)
- `README.md` - Human-readable notes about the agent
- `src/` - (optional) Extracted Python code for very large agents

## Available Agents


### Orchestration

- **[ExecutionMonitor](./ExecutionMonitor/ExecutionMonitor.md)** (`/agent:execution-monitor`) - The execution-monitor agent
- **[OrchestratorAgent](./OrchestratorAgent/OrchestratorAgent.md)** (`/agent:orchestrator-agent`) - The orchestrator-agent agent
- **[TaskAnalyzer](./TaskAnalyzer/TaskAnalyzer.md)** (`/agent:task-analyzer`) - The task-analyzer agent
- **[WorkflowManager](./WorkflowManager/WorkflowManager.md)** (`/agent:workflow-manager`) - The workflow-manager agent

### Development

- **[CodeReviewResponse](./CodeReviewResponse/CodeReviewResponse.md)** (`/agent:code-review-response`) - The code-review-response agent
- **[CodeReviewer](./CodeReviewer/CodeReviewer.md)** (`/agent:code-reviewer`) - The code-reviewer agent
- **[PrBacklogManager](./PrBacklogManager/PrBacklogManager.md)** (`/agent:pr-backlog-manager`) - The pr-backlog-manager agent
- **[ProgramManager](./ProgramManager/ProgramManager.md)** (`/agent:program-manager`) - The program-manager agent
- **[PromptWriter](./PromptWriter/PromptWriter.md)** (`/agent:prompt-writer`) - The prompt-writer agent
- **[SystemDesignReviewer](./SystemDesignReviewer/SystemDesignReviewer.md)** (`/agent:system-design-reviewer`) - The system-design-reviewer agent

### Testing

- **[TestSolver](./TestSolver/TestSolver.md)** (`/agent:test-solver`) - The test-solver agent
- **[TestWriter](./TestWriter/TestWriter.md)** (`/agent:test-writer`) - The test-writer agent

### Infrastructure

- **[AgentUpdater](./AgentUpdater/AgentUpdater.md)** (`/agent:agent-updater`) - The agent-updater agent
- **[ClaudeSettingsUpdate](./ClaudeSettingsUpdate/ClaudeSettingsUpdate.md)** (`/agent:claude-settings-update`) - The claude-settings-update agent
- **[Gadugi](./Gadugi/Gadugi.md)** (`/agent:gadugi`) - The gadugi agent
- **[MemoryManager](./MemoryManager/MemoryManager.md)** (`/agent:memory-manager`) - The memory-manager agent
- **[WorktreeManager](./WorktreeManager/WorktreeManager.md)** (`/agent:worktree-manager`) - The worktree-manager agent

### Planning

- **[TaskBoundsEval](./TaskBoundsEval/TaskBoundsEval.md)** (`/agent:task-bounds-eval`) - The task-bounds-eval agent
- **[TaskDecomposer](./TaskDecomposer/TaskDecomposer.md)** (`/agent:task-decomposer`) - The task-decomposer agent
- **[TaskResearchAgent](./TaskResearchAgent/TaskResearchAgent.md)** (`/agent:task-research-agent`) - The task-research-agent agent

### Documentation

- **[ReadmeAgent](./ReadmeAgent/ReadmeAgent.md)** (`/agent:readme-agent`) - The readme-agent agent

### Support

- **[TeamCoach](./TeamCoach/TeamCoach.md)** (`/agent:team-coach`) - The team-coach agent
- **[TeamcoachAgent](./TeamcoachAgent/TeamcoachAgent.md)** (`/agent:teamcoach-agent`) - The teamcoach-agent agent
- **[XpiaDefenseAgent](./XpiaDefenseAgent/XpiaDefenseAgent.md)** (`/agent:xpia-defense-agent`) - The xpia-defense-agent agent


## How to Use These Agents

1. **Direct Invocation**: Use `/agent:agent-name` to invoke an agent
2. **Reading the Definition**: Open the `.md` file to see exactly what the agent does
3. **Modifying Agents**: Edit the `.md` file directly to change agent behavior
4. **Testing Changes**: Invoke the agent after editing to test your changes

## Agent Definition Format

Each agent follows the Claude Code sub-agent format:

```yaml
---
name: agent-name
description: What the agent does
tools: [List, of, required, tools]
imports: Optional imports or dependencies
---

# Agent instructions in markdown
```

## Development Notes

When creating or modifying agents:
1. Keep instructions clear and specific
2. Use the tools list to declare required capabilities
3. Include error handling instructions
4. Follow the "bricks & studs" philosophy from Guidelines.md
5. Test the agent thoroughly after changes

Remember: These files ARE the agents - they're not documentation, they're executable definitions.
