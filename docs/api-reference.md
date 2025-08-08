# API Reference

Complete reference for Gadugi CLI commands, agent interfaces, and configuration.

## Agent Invocation Syntax

### Basic Format
```
/agent:[agent-name]

[Task description and requirements]
```

### With Context
```
/agent:[agent-name]

Context: [Background information]
Task: [What needs to be done]
Requirements: [Specific requirements]
Success Criteria: [How to measure success]
```

## Core Agents API

### orchestrator-agent

**Purpose**: Coordinate parallel task execution

**Syntax**:
```
/agent:orchestrator-agent

Execute these specific prompts in parallel:
- prompt-1.md
- prompt-2.md
- prompt-3.md
```

**Parameters**:
- `prompts`: List of prompt files to execute
- `parallel`: Boolean (default: true)
- `priority`: Task priority ordering

### workflow-manager

**Purpose**: Execute 11-phase development workflow

**Syntax**:
```
/agent:workflow-manager

[Detailed task description]
```

**Parameters**:
- `task`: Task description
- `issue`: Issue number (optional)
- `branch`: Branch name (optional)
- `skip_phases`: Phases to skip (not recommended)

### code-reviewer

**Purpose**: Review pull requests

**Syntax**:
```
/agent:code-reviewer

Review PR #[number] - [title]
Focus on: [specific areas]
```

**Parameters**:
- `pr_number`: Pull request number
- `focus_areas`: Specific review focus
- `security_check`: Enable security review

## Tool Descriptions

### Read
Read files from the filesystem.

**Usage**: Read specific files or directories
**Parameters**:
- `file_path`: Path to file
- `limit`: Line limit (optional)
- `offset`: Starting line (optional)

### Write
Write new files to the filesystem.

**Usage**: Create new files
**Parameters**:
- `file_path`: Path to file
- `content`: File content

### Edit
Edit existing files.

**Usage**: Modify file contents
**Parameters**:
- `file_path`: Path to file
- `old_string`: Text to replace
- `new_string`: Replacement text
- `replace_all`: Replace all occurrences

### Bash
Execute shell commands.

**Usage**: Run system commands
**Parameters**:
- `command`: Command to execute
- `timeout`: Timeout in ms (default: 120000)
- `description`: Command description

### Grep
Search file contents.

**Usage**: Find patterns in files
**Parameters**:
- `pattern`: Search pattern (regex)
- `path`: Search path
- `glob`: File pattern
- `output_mode`: Output format

### TodoWrite
Manage task lists.

**Usage**: Track tasks and progress
**Parameters**:
- `todos`: Array of task objects
  - `id`: Task identifier
  - `content`: Task description
  - `status`: pending|in_progress|completed

### Task
Delegate to specialized agents.

**Usage**: Invoke sub-agents
**Parameters**:
- `subagent_type`: Agent to invoke
- `description`: Task description
- `prompt`: Detailed instructions

## Configuration Files

### .claude/settings.json

Main Claude configuration:

```json
{
  "tools": {
    "allowed": [
      "Read", "Write", "Edit", "Bash",
      "Grep", "LS", "TodoWrite", "Task"
    ],
    "timeout": 120000
  },
  "agents": {
    "path": ".claude/agents",
    "auto_invoke_review": true
  }
}
```

### pyproject.toml

Python project configuration:

```toml
[project]
name = "gadugi"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
    "pre-commit>=3.5.0"
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### .pre-commit-config.yaml

Pre-commit hooks configuration:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

## Environment Variables

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub authentication | None (uses gh auth) |
| `CLAUDE_API_KEY` | Claude API key | None (uses desktop) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GADUGI_WORKTREE_PATH` | Worktree directory | `.worktrees` |
| `GADUGI_PARALLEL_LIMIT` | Max parallel tasks | 5 |
| `GADUGI_TIMEOUT` | Agent timeout (ms) | 300000 |
| `GADUGI_DEBUG` | Debug mode | false |
| `UV_SYSTEM_PYTHON` | Use system Python | false |

## GitHub CLI Commands

### Issue Management

```bash
# Create issue
gh issue create --title "Title" --body "Body" --label "label"

# List issues
gh issue list [--state open|closed|all]

# View issue
gh issue view <number>

# Close issue
gh issue close <number>
```

### Pull Request Management

```bash
# Create PR
gh pr create --base main --head branch --title "Title"

# List PRs
gh pr list [--state open|closed|merged|all]

# View PR
gh pr view <number>

# Check PR status
gh pr checks <number>

# Merge PR
gh pr merge <number> [--squash|--merge|--rebase]
```

### Workflow Management

```bash
# List workflow runs
gh run list [--workflow name]

# View run details
gh run view <run-id>

# Watch run progress
gh run watch <run-id>

# Download artifacts
gh run download <run-id>
```

## Git Worktree Commands

### Basic Operations

```bash
# Add worktree
git worktree add <path> -b <branch>

# List worktrees
git worktree list

# Remove worktree
git worktree remove <path>

# Prune worktrees
git worktree prune
```

### Advanced Operations

```bash
# Lock worktree
git worktree lock <path>

# Unlock worktree
git worktree unlock <path>

# Move worktree
git worktree move <path> <new-path>

# Repair worktree
git worktree repair
```

## UV Commands

### Project Management

```bash
# Initialize project
uv init

# Sync dependencies
uv sync [--all-extras]

# Add dependency
uv add <package>

# Remove dependency
uv remove <package>

# Update dependencies
uv update
```

### Environment Management

```bash
# Create venv
uv venv

# Run command
uv run <command>

# Run Python
uv run python <script>

# Run tests
uv run pytest
```

## Testing Commands

### pytest

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_file.py::test_function

# With coverage
uv run pytest --cov=. --cov-report=html

# Verbose output
uv run pytest -v --tb=short
```

### Linting

```bash
# Check linting
uv run ruff check .

# Fix linting
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 1 | General error | Check error message |
| 2 | Missing dependency | Run `uv sync` |
| 3 | Git error | Check git status |
| 4 | Agent error | Check agent logs |
| 5 | Timeout | Increase timeout |
| 127 | Command not found | Install missing tool |

## API Limits

### GitHub API

- **Authenticated**: 5,000 requests/hour
- **Unauthenticated**: 60 requests/hour
- **Search**: 30 requests/minute

### Agent Execution

- **Parallel limit**: 5 tasks (configurable)
- **Timeout**: 5 minutes default (configurable)
- **Memory limit**: System dependent

## WebHooks and Events

### GitHub WebHook Events

Gadugi can respond to:
- `issues.opened`
- `pull_request.opened`
- `pull_request.review_requested`
- `workflow_run.completed`

### Agent Events

Internal events:
- `agent.started`
- `agent.completed`
- `agent.failed`
- `workflow.phase_changed`
- `worktree.created`
- `worktree.removed`
