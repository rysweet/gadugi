# Gadugi - Multi-Agent System for AI-Assisted Coding

> **Gadugi** is a multi-agent system for AI-assisted coding. It takes its name from the Cherokee word (gah-DOO-gee) that means communal work - where community members come together to accomplish tasks that benefit everyone, sharing collective wisdom and mutual support.

## Overview

Gadugi provides a collection of reusable AI agents that work together (and in parallel) to enhance software development workflows. While currently implemented for Claude Code, the architecture is designed to be agent-host neutral and can be adapted to other AI coding assistants.

## Philosophy

The Cherokee concept of Gadugi represents:
- **ᎦᏚᎩ (Gadugi) - Communal Work**: Agents working together for mutual benefit
- **ᎠᏓᏅᏙ (Adanvdo) - Collective Wisdom**: Sharing patterns and knowledge  
- **ᎠᎵᏍᏕᎸᏗ (Alisgelvdi) - Mutual Support**: Agents helping each other
- **ᎤᏂᎦᏚ (Unigadv) - Shared Resources**: Pooling tools and capabilities

## Repository Structure

```
gadugi/
├── .claude/
│   ├── agents/                 # All agents stored here
│   │   ├── workflow-master.md      # Orchestrates development workflows
│   │   ├── orchestrator-agent.md   # Manages parallel execution
│   │   ├── code-reviewer.md        # Automated code review
│   │   ├── code-review-response.md # Processes review feedback
│   │   ├── prompt-writer.md        # Creates structured prompts
│   │   ├── agent-manager.md        # Manages agent synchronization
│   │   ├── task-analyzer.md        # Analyzes task dependencies
│   │   ├── worktree-manager.md     # Manages git worktrees
│   │   └── execution-monitor.md    # Monitors parallel execution
│   ├── agent-manager/          # Agent manager configuration
│   ├── orchestrator/           # Orchestrator components
│   ├── docs/                   # Additional documentation
│   └── templates/              # Workflow templates
├── prompts/                    # Prompt templates
├── manifest.yaml              # Agent registry and versions
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Quick Start

### Bootstrap Agent Manager

The agent-manager is required to sync agents from gadugi:

1. **Download agent-manager locally**:
   ```bash
   mkdir -p .claude/agents
   curl -o .claude/agents/agent-manager.md \
     https://raw.githubusercontent.com/rysweet/gadugi/main/.claude/agents/agent-manager.md
   ```

2. **Initialize and configure**:
   ```
   /agent:agent-manager init
   /agent:agent-manager register-repo https://github.com/rysweet/gadugi
   ```

3. **Install agents**:
   ```
   /agent:agent-manager install all
   ```

The agent-manager will handle all necessary configuration updates.

### Using Agents

Once installed, invoke agents as needed:
- `/agent:workflow-manager` - For complete development workflows
- `/agent:orchestrator-agent` - For parallel task execution
- `/agent:code-reviewer` - For code review tasks
- `/agent:prompt-writer` - For creating structured prompts

### Important: Hook Limitations

**Claude Code hooks cannot directly invoke agents using `/agent:agent-name` syntax.**

Hooks execute in shell environments where the `/agent:` syntax is not recognized, resulting in "No such file or directory" errors. Instead:

**❌ This fails in hooks:**
```json
{
  "command": "/agent:agent-manager check-and-update-agents"
}
```

**✅ Use hooks for notifications:**
```json
{
  "command": "echo 'Use \"/agent:agent-manager check-and-update-agents\" to check for updates'"
}
```

Then manually invoke agents in Claude Code sessions as needed.

## Available Agents

### Workflow Management
- **workflow-master** - Orchestrates complete development workflows from issue to PR
- **orchestrator-agent** - Enables parallel execution of multiple agents
- **task-analyzer** - Analyzes prompt files for dependencies and parallelization
- **worktree-manager** - Manages git worktree lifecycle for isolated execution
- **execution-monitor** - Monitors parallel executions and tracks progress

### Code Quality
- **code-reviewer** - Performs comprehensive code reviews on pull requests
- **code-review-response** - Processes and responds to code review feedback

### Productivity
- **prompt-writer** - Creates high-quality structured prompts for complex tasks

### Infrastructure
- **agent-manager** - Manages external agent repositories with version control

## Version Management

We use semantic versioning:
- **Major**: Breaking changes to agent interfaces
- **Minor**: New agents or features
- **Patch**: Bug fixes and improvements

See `manifest.yaml` for current agent versions.

## License

MIT License - See [LICENSE](LICENSE) for details

## Acknowledgments

- The Cherokee Nation for the inspiring concept of Gadugi
- Anthropic for enabling AI-powered development

---

*ᎤᎵᎮᎵᏍᏗ (Ulihelisdi) - "We are helping each other"*
