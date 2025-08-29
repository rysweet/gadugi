# UV Environment Setup Instructions

## When to Load This File
Load when you need to:
- Set up Python virtual environments
- Manage UV projects
- Handle dependencies
- Troubleshoot Python environment issues

## UV Project Detection

### Identifying UV Projects
```bash
# UV project has BOTH files:
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo "UV project detected"
fi
```

## Required UV Setup

### In Worktrees
```bash
cd .worktrees/task-*/

# ALWAYS sync first
uv sync --all-extras

# Then use uv run prefix for ALL Python
uv run python script.py
uv run pytest tests/
uv run ruff check .
uv run pyright
```

### NEVER Run Directly
```bash
# These WILL FAIL in UV projects:
python script.py     # ❌ Wrong
pytest tests/        # ❌ Wrong
ruff check .        # ❌ Wrong

# Always use uv run prefix:
uv run python script.py  # ✅ Correct
uv run pytest tests/     # ✅ Correct
uv run ruff check .     # ✅ Correct
```

## UV Setup Script

### Using Shared Script
```bash
source .claude/scripts/setup-uv-env.sh

# Setup environment
setup_uv_environment "$(pwd)" "--all-extras"

# Check health
check_uv_environment "$(pwd)"

# Run commands
uv_run "$(pwd)" pytest tests/
uv_run_python "$(pwd)" script.py
```

### Agent Integration Pattern
```bash
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo "UV project - setting up"
    source .claude/scripts/setup-uv-env.sh

    if setup_uv_environment "$(pwd)" "--all-extras"; then
        echo "UV ready"
        uv_run_pytest "$(pwd)" tests/
    else
        echo "UV setup failed"
        exit 1
    fi
else
    echo "Standard Python project"
    # Normal Python setup
fi
```

## UV Commands Reference

| Task | Command | Notes |
|------|---------|-------|
| Setup | `uv sync --all-extras` | Once per worktree |
| Run script | `uv run python script.py` | Always use uv run |
| Run tests | `uv run pytest tests/` | Never direct pytest |
| Format | `uv run ruff format .` | UV manages versions |
| Lint | `uv run ruff check .` | Consistent tooling |
| Add dep | `uv add package` | Updates pyproject.toml |
| Add dev dep | `uv add --group dev package` | Development tools |

## Common UV Issues

### "Module not found"
```bash
# Check you're using uv run
uv run python script.py  # ✅
python script.py         # ❌

# Ensure synced
uv sync --all-extras
```

### "uv: command not found"
```bash
# Check installation
which uv
uv --version

# Install if missing
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Virtual env not found
```bash
# Re-sync
uv sync --all-extras

# Check health
source .claude/scripts/setup-uv-env.sh
check_uv_environment "$(pwd)"
```

## Environment Validation

```bash
validate_uv_environment() {
    local path="$1"
    cd "$path"

    # Check files
    if [[ ! -f "pyproject.toml" || ! -f "uv.lock" ]]; then
        echo "Not UV project"
        return 1
    fi

    # Check UV installed
    if ! command -v uv &> /dev/null; then
        echo "UV not installed"
        return 1
    fi

    # Check venv
    if [[ ! -d ".venv" ]]; then
        echo "Creating venv"
        uv sync --all-extras
    fi

    # Test Python
    if ! uv run python -c "print('OK')"; then
        echo "UV not working"
        return 1
    fi

    return 0
}
```

## Agent-Specific Requirements

### WorktreeManager
- MUST run `uv sync --all-extras` in setup
- Detect UV projects automatically
- Update environment documentation

### WorkflowManager
- Check for UV when starting workflow
- Use `uv run` for all Python commands
- Validate UV before tests

### OrchestratorAgent
- Coordinate UV setup across worktrees
- Pass UV status to sub-agents
- Ensure consistent setup

## Best Practices

1. **Always sync in new worktrees**
2. **Never mix UV and non-UV commands**
3. **Check project type before Python ops**
4. **Use shared setup scripts**
5. **Validate environment before execution**
