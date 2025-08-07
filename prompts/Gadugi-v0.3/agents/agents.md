# Gadugi Agent Team

## Overview

The Gadugi system employs a comprehensive team of specialized AI agents, each designed to handle specific aspects of the development workflow. These agents work together to provide intelligent automation, coordination, and assistance throughout the software development lifecycle.

## Agent Categories

### Architecture

- **[SystemDesignReviewer](./SystemDesignReviewer/SystemDesignReviewer.md)** (`/agent:system-design-reviewer`): Reviews architectural decisions and system design

### Configuration

- **[ClaudeSettingsUpdate](./ClaudeSettingsUpdate/ClaudeSettingsUpdate.md)** (`/agent:claude-settings-update`): Updates Claude settings configuration files

### Coordination

- **[TeamCoach](./TeamCoach/TeamCoach.md)** (`/agent:team-coach`): Intelligent multi-agent coordination and optimization
- **[TeamCoachAgent](./TeamCoachAgent/TeamCoachAgent.md)** (`/agent:teamcoach-agent`): Alternative TeamCoach implementation

### Development

- **[CodeReviewResponse](./CodeReviewResponse/CodeReviewResponse.md)** (`/agent:code-review-response`): Processes code review feedback and implements changes
- **[CodeReviewer](./CodeReviewer/CodeReviewer.md)** (`/agent:code-reviewer`): Conducts thorough code reviews on pull requests
- **[PrBacklogManager](./PrBacklogManager/PrBacklogManager.md)** (`/agent:pr-backlog-manager`): Manages the backlog of PRs ensuring review readiness
- **[PromptWriter](./PromptWriter/PromptWriter.md)** (`/agent:prompt-writer`): Creates high-quality structured prompt files

### Documentation

- **[ReadmeAgent](./ReadmeAgent/ReadmeAgent.md)** (`/agent:readme-agent`): Manages and maintains README.md files

### Infrastructure

- **[AgentUpdater](./AgentUpdater/AgentUpdater.md)** (`/agent:agent-updater`): Automatically checks for and manages updates for Claude Code agents
- **[Gadugi](./Gadugi/Gadugi.md)** (`/agent:gadugi`): Main Gadugi agent for system management
- **[MemoryManager](./MemoryManager/MemoryManager.md)** (`/agent:memory-manager`): Manages Memory.md and GitHub Issues synchronization
- **[WorktreeManager](./WorktreeManager/WorktreeManager.md)** (`/agent:worktree-manager`): Manages git worktree lifecycle for parallel execution

### Management

- **[ProgramManager](./ProgramManager/ProgramManager.md)** (`/agent:program-manager`): Manages program-level coordination and planning

### Orchestration

- **[ExecutionMonitor](./ExecutionMonitor/ExecutionMonitor.md)** (`/agent:execution-monitor`): Monitors parallel Claude Code CLI executions
- **[OrchestratorAgent](./OrchestratorAgent/OrchestratorAgent.md)** (`/agent:orchestrator-agent`): Coordinates parallel execution of multiple WorkflowManagers
- **[TaskAnalyzer](./TaskAnalyzer/TaskAnalyzer.md)** (`/agent:task-analyzer`): Enhanced task analyzer with intelligent decomposition
- **[WorkflowManager](./WorkflowManager/WorkflowManager.md)** (`/agent:workflow-manager`): Code-driven workflow orchestration with deterministic execution

### Planning

- **[TaskBoundsEval](./TaskBoundsEval/TaskBoundsEval.md)** (`/agent:task-bounds-eval`): Evaluates whether tasks are well understood and bounded
- **[TaskDecomposer](./TaskDecomposer/TaskDecomposer.md)** (`/agent:task-decomposer`): Breaks complex tasks into manageable subtasks

### Research

- **[TaskResearchAgent](./TaskResearchAgent/TaskResearchAgent.md)** (`/agent:task-research-agent`): Researches solutions for unknown or novel tasks

### Security

- **[XpiaDefenseAgent](./XpiaDefenseAgent/XpiaDefenseAgent.md)** (`/agent:xpia-defense-agent`): Implements cross-prompt injection attack defense

### Testing

- **[TestSolver](./TestSolver/TestSolver.md)** (`/agent:test-solver`): Analyzes and resolves failing tests
- **[TestWriter](./TestWriter/TestWriter.md)** (`/agent:test-writer`): Authors new tests for code coverage and TDD

## Agent Hierarchy

```
OrchestratorAgent (Top-level Coordinator)
├── WorkflowManager (Individual Workflow Orchestration)
│   ├── TaskAnalyzer (Task Analysis)
│   ├── TaskDecomposer (Task Breakdown)
│   ├── WorktreeManager (Environment Setup)
│   ├── TestWriter (Test Creation)
│   ├── TestSolver (Test Fixing)
│   ├── CodeReviewer (Phase 9 Review)
│   └── CodeReviewResponse (Review Response)
├── ExecutionMonitor (Parallel Execution Monitoring)
├── TaskBoundsEval (Task Evaluation)
└── TaskResearchAgent (Research & Investigation)

Support Agents:
├── MemoryManager (Memory & GitHub Sync)
├── AgentUpdater (Agent Updates)
├── ClaudeSettingsUpdate (Settings Management)
├── PromptWriter (Prompt Creation)
├── ReadmeAgent (Documentation)
├── SystemDesignReviewer (Architecture Review)
├── PrBacklogManager (PR Management)
├── TeamCoach (Team Coordination)
└── Gadugi (System Management)
```

## Usage Patterns

### For Multiple Tasks
```
/agent:orchestrator-agent

Execute the following tasks:
1. Task one description
2. Task two description
```

### For Single Workflow
```
/agent:workflow-manager

Task: Complete workflow for [specific task]
```

### For Specific Operations
```
/agent:[specific-agent]

[Agent-specific instructions]
```

## Agent Communication

Agents communicate through:
1. **File System**: Shared state files and worktrees
2. **Git Operations**: Branches, commits, and PRs
3. **Task Delegation**: Parent agents invoking child agents
4. **State Management**: JSON state files for persistence
5. **GitHub Integration**: Issues, PRs, and API operations

## Best Practices

1. **Use the Right Agent**: Select the most specific agent for your task
2. **Provide Clear Context**: Give agents complete information
3. **Follow Hierarchy**: Use orchestrator for multiple tasks, workflow-manager for single workflows
4. **Monitor Progress**: Use execution-monitor for parallel operations
5. **Maintain State**: Let agents manage their own state files

## Extension Points

New agents can be added by:
1. Creating agent specification in `/prompts/Gadugi-v0.3/agents/[AgentName]/`
2. Following the Claude Code sub-agent format
3. Implementing required tools and interfaces
4. Adding to appropriate category in this document
5. Testing with realistic scenarios

## Related Documentation

- [Guidelines](../Guidelines.md) - Development philosophy and practices
- [Claude Code Sub-Agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) - Agent specification format
- [CLAUDE.md](../../../CLAUDE.md) - System instructions and workflow requirements
