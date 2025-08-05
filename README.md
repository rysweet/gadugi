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

### Prerequisites

Gadugi uses [UV (Ultraviolet)](https://github.com/astral-sh/uv) for fast Python dependency management. Install UV first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

### Environment Setup

1. **Clone and set up the repository**:
   ```bash
   git clone https://github.com/rysweet/gadugi.git
   cd gadugi

   # Install dependencies (creates .venv automatically)
   uv sync --extra dev

   # Verify installation
   uv run python -c "import gadugi; print(f'Gadugi {gadugi.get_version()} ready!')"
   ```

2. **Run tests to verify setup**:
   ```bash
   uv run pytest tests/ -v
   ```

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
- `/agent:readme-agent` - For README management and maintenance

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
- **readme-agent** - Manages and maintains README.md files on behalf of the Product Manager

### Infrastructure
- **agent-manager** - Manages external agent repositories with version control

## Development Setup

### Working with UV

Gadugi uses UV for fast, reliable Python dependency management:

```bash
# Install dependencies
uv sync --extra dev              # Development dependencies
uv sync                          # Production only

# Run commands
uv run pytest tests/             # Run tests
uv run ruff format .             # Format code
uv run ruff check .              # Lint code

# Manage dependencies
uv add requests                  # Add dependency
uv add --group dev mypy          # Add dev dependency
uv remove package                # Remove dependency
```

### Performance Benefits

UV provides significant performance improvements over pip:
- **10-100x faster** package installation
- **Automatic virtual environment** management
- **Reproducible builds** with `uv.lock`
- **Better dependency resolution**

### Development Workflow

1. **Setup**: `uv sync --extra dev`
2. **Test**: `uv run pytest tests/`
3. **Format**: `uv run ruff format .`
4. **Lint**: `uv run ruff check .`
5. **Add deps**: `uv add package`

See [docs/uv-migration-guide.md](docs/uv-migration-guide.md) for detailed instructions.

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
