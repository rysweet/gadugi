# Getting Started with Gadugi

This guide will help you set up and start using Gadugi for AI-assisted development.

## Prerequisites

### 1. Install UV (Python Package Manager)

UV is required for Python dependency management:

```bash
# Install UV using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### 2. Install Claude Code

Install the Claude desktop application from [claude.ai](https://claude.ai):

1. Download Claude for your platform
2. Sign in with your Anthropic account
3. Enable developer features in settings

### 3. Install GitHub CLI

```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login
```

## Repository Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rysweet/gadugi.git
cd gadugi
```

### 2. Set Up Python Environment

```bash
# UV automatically creates and manages the virtual environment
uv sync --all-extras

# Verify setup
uv run python -c "import gadugi; print('Setup successful!')"
```

### 3. Install Pre-commit Hooks

```bash
uv run pre-commit install
```

### 4. Configure Claude Code

Create or update `.claude/settings.json`:

```json
{
  "tools": {
    "allowed": [
      "Read", "Write", "Edit", "Bash", "Grep", "LS",
      "TodoWrite", "WebSearch", "Task"
    ]
  }
}
```

## Your First Workflow

### Example: Fix a Bug

1. **Create an issue**:
```bash
gh issue create --title "Fix import error in module X" --body "Description of the bug"
```

2. **Invoke the workflow manager**:
```
/agent:workflow-manager

Fix the import error in module X as described in issue #[number].
This requires debugging the import statements and ensuring all dependencies are correct.
```

3. **The agent will**:
   - Create a feature branch
   - Set up an isolated worktree
   - Research the issue
   - Implement the fix
   - Run tests
   - Create a pull request
   - Invoke code review

### Example: Parallel Tasks

For multiple independent tasks, use the orchestrator:

```
/agent:orchestrator-agent

Execute these tasks in parallel:
- Fix import error in module X
- Add unit tests for module Y
- Update documentation for feature Z
```

## Verifying Your Setup

Run the setup verification script:

```bash
# Check all components
./scripts/verify-setup.sh

# Expected output:
# ✅ UV installed and configured
# ✅ Python environment active
# ✅ Git worktrees available
# ✅ GitHub CLI authenticated
# ✅ Claude agents accessible
```

## Next Steps

- Read [Architecture](architecture.md) to understand the system design
- Browse [Agent Catalog](agents/README.md) to see available agents
- Review [Common Workflows](workflows.md) for typical patterns
- Check [Troubleshooting](troubleshooting.md) if you encounter issues

## Quick Command Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --all-extras` |
| Run tests | `uv run pytest tests/` |
| Format code | `uv run ruff format .` |
| Check linting | `uv run ruff check .` |
| Create issue | `gh issue create` |
| List PRs | `gh pr list` |
| Invoke agent | `/agent:[agent-name]` |

## Getting Help

- **Documentation**: Browse the `/docs` directory
- **Issues**: Check [GitHub Issues](https://github.com/rysweet/gadugi/issues)
- **Agent Help**: Use `/agent:task-analyzer` for task guidance
- **Memory**: Check `.github/Memory.md` for context
