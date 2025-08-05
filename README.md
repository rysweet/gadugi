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
│   ├── agents/                     # All agents stored here
│   │   ├── workflow-manager.md         # Main workflow orchestrator
│   │   ├── orchestrator-agent.md       # Parallel execution coordinator
│   │   ├── code-reviewer.md            # Code review automation
│   │   ├── code-review-response.md     # Review feedback processing
│   │   ├── prompt-writer.md            # Structured prompt creation
│   │   ├── agent-manager.md            # Agent repository management
│   │   ├── task-analyzer.md            # Task dependency analysis
│   │   ├── task-bounds-eval.md         # Task complexity evaluation
│   │   ├── task-decomposer.md          # Task breakdown specialist
│   │   ├── task-research-agent.md      # Research and planning
│   │   ├── worktree-manager.md         # Git worktree lifecycle
│   │   ├── execution-monitor.md        # Parallel execution tracking
│   │   ├── team-coach.md               # Team coordination & optimization
│   │   ├── teamcoach-agent.md          # Alternative team coaching
│   │   ├── pr-backlog-manager.md       # PR readiness management
│   │   ├── program-manager.md          # Project health & strategy
│   │   ├── memory-manager.md           # Memory.md synchronization
│   │   ├── test-solver.md              # Test failure diagnosis
│   │   ├── test-writer.md              # Test suite creation
│   │   ├── xpia-defense-agent.md       # Security protection
│   │   └── workflow-manager-phase9-enforcement.md  # Review enforcement
│   ├── shared/                     # Shared utilities and modules
│   ├── docs/                       # Additional documentation
│   └── templates/                  # Workflow templates
├── .github/
│   ├── Memory.md                   # AI assistant persistent memory
│   └── workflows/                  # GitHub Actions workflows
├── prompts/                        # Prompt templates
├── manifest.yaml                   # Agent registry and versions
├── CLAUDE.md                       # Project-specific AI instructions
├── claude-generic-instructions.md  # Generic Claude Code best practices
├── LICENSE                         # MIT License
└── README.md                       # This file
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

#### Primary Orchestrators
- `/agent:orchestrator-agent` - For coordinating multiple parallel workflows
- `/agent:workflow-manager` - For complete development workflows (issue → code → PR)

#### Specialized Agents
- `/agent:code-reviewer` - For comprehensive code reviews
- `/agent:prompt-writer` - For creating structured prompts
- `/agent:memory-manager` - For maintaining Memory.md and GitHub sync
- `/agent:program-manager` - For project health and issue lifecycle management
- `/agent:team-coach` - For team coordination and performance optimization

#### Development Tools
- `/agent:test-solver` - For diagnosing and fixing failing tests
- `/agent:test-writer` - For creating comprehensive test suites
- `/agent:pr-backlog-manager` - For managing PR readiness and backlogs

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
- **workflow-manager** - Orchestrates complete development workflows from issue creation to PR review
- **orchestrator-agent** - Coordinates parallel execution of multiple WorkflowManagers
- **task-analyzer** - Analyzes prompt files to identify dependencies and parallelization opportunities
- **worktree-manager** - Manages git worktree lifecycle for isolated parallel execution
- **execution-monitor** - Monitors parallel Claude Code CLI executions and tracks progress

### Task Analysis & Decomposition
- **task-bounds-eval** - Evaluates task complexity and scope boundaries
- **task-decomposer** - Breaks down complex tasks into manageable subtasks
- **task-research-agent** - Conducts research for task planning and implementation

### Code Quality & Review
- **code-reviewer** - Performs comprehensive code reviews on pull requests
- **code-review-response** - Processes code review feedback and implements changes
- **test-solver** - Diagnoses and fixes failing tests
- **test-writer** - Creates comprehensive test suites

### Team Coordination & Optimization
- **team-coach** - Provides intelligent multi-agent team coordination with performance analytics
- **teamcoach-agent** - Alternative implementation of team coaching functionality
- **pr-backlog-manager** - Manages PR backlogs by ensuring readiness for review and merge

### Project Management
- **program-manager** - Manages project health, issue lifecycle, and strategic direction
- **memory-manager** - Maintains and synchronizes Memory.md with GitHub Issues

### Productivity & Content Creation
- **prompt-writer** - Creates high-quality structured prompts for development workflows

### Security & Infrastructure
- **agent-manager** - Manages external agent repositories with version control
- **xpia-defense-agent** - Protects against Cross-Prompt Injection Attacks

### Specialized Enforcement
- **workflow-manager-phase9-enforcement** - Ensures Phase 9 code review enforcement in workflows

## Agent Hierarchy and Coordination

### Primary Orchestrators
- **orchestrator-agent** → Coordinates multiple **workflow-manager** instances for parallel execution
- **workflow-manager** → Main workflow orchestrator that invokes specialized agents as needed

### Agent Dependencies
- **orchestrator-agent** uses:
  - **task-analyzer** - To analyze dependencies and plan parallel execution
  - **worktree-manager** - To create isolated development environments
  - **execution-monitor** - To track progress of parallel executions
- **workflow-manager** integrates with:
  - **code-reviewer** - For automated code review (Phase 9)
  - **memory-manager** - For state persistence and GitHub sync
  - **pr-backlog-manager** - For PR lifecycle management
- **team-coach** provides optimization for:
  - **orchestrator-agent** - Performance analytics and team coordination
  - **workflow-manager** - Intelligent task assignment and coaching

### Usage Patterns
- **For multiple related tasks**: Use **orchestrator-agent** to coordinate parallel **workflow-manager** instances
- **For single complex workflows**: Use **workflow-manager** directly
- **For specialized tasks**: Invoke specific agents (code-reviewer, test-solver, etc.) directly
- **For project management**: Use **program-manager** for issue lifecycle and strategic direction

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
