# Testing & Quality Assurance Instructions

## When to Load This File
Load when you need to:
- Run tests or fix test failures
- Fix type errors (pyright, mypy)
- Implement quality gates
- Set up pre-commit hooks

## Mandatory Testing Commands

### UV Python Projects (Has `uv.lock`)
```bash
# Detection
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    # Setup environment (REQUIRED in worktrees)
    uv sync --all-extras

    # Run tests (MUST pass to continue)
    uv run pytest tests/ -v
    uv run pytest tests/ --cov=. --cov-report=html

    # Linting & Formatting (MANDATORY)
    uv run ruff check .
    uv run ruff format .

    # Type checking
    uv run pyright
    uv run mypy . --ignore-missing-imports

    # Pre-commit (MANDATORY before PR)
    uv run pre-commit install
    uv run pre-commit run --all-files
fi
```

### Standard Python Projects
```bash
if [[ ! -f "uv.lock" ]]; then
    # Activate venv if available
    source venv/bin/activate 2>/dev/null || true

    # Same commands without 'uv run' prefix
    pytest tests/ -v
    ruff check .
    ruff format .
    pre-commit run --all-files
fi
```

## Phase 6: Testing Implementation

```bash
execute_phase_6_testing() {
    local worktree_path="$1"
    cd "$worktree_path"

    # 1. Detect project type
    if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
        TEST_CMD="uv run pytest"
        LINT_CMD="uv run ruff"
    else
        TEST_CMD="pytest"
        LINT_CMD="ruff"
    fi

    # 2. Run tests (BLOCKING)
    $TEST_CMD tests/ -v --tb=short || {
        echo "❌ TESTS FAILED - Cannot continue"
        return 1
    }

    # 3. Code quality (BLOCKING)
    $LINT_CMD check . || {
        echo "❌ LINTING FAILED - Cannot continue"
        return 1
    }

    # 4. Pre-commit hooks (BLOCKING)
    pre-commit run --all-files || {
        echo "❌ PRE-COMMIT FAILED - Cannot continue"
        return 1
    }

    echo "✅ ALL QUALITY GATES PASSED"
}
```

## Type Error Fixing Patterns

### Parallel Type Fixing Strategy
```python
# Identify high-error directories
uv run pyright 2>&1 | grep -E "^  /" | \
    sed 's/:.*//g' | xargs -n1 dirname | \
    sort | uniq -c | sort -nr | head -10

# Launch parallel fixes for each directory
Task 1: Fix .claude/agents (200 errors)
Task 2: Fix tests/shared (150 errors)
Task 3: Fix .claude/shared (100 errors)
```

### Common Type Error Fixes
1. **Missing imports**: Add `from typing import Optional, Dict, List`
2. **Optional handling**: Check `if value is not None:` before access
3. **Dataclass fields**: Use `field(default_factory=list)` for mutable defaults
4. **Method signatures**: Match parameter types with base class
5. **Import fallbacks**: Try/except with stub implementations

## Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest  # or pytest for non-UV
        language: system
        pass_filenames: false
        stages: [pre-push]
```

## Quality Gate Enforcement

### WorkflowManager Requirements
- MUST execute `phase_6_testing()` before Phase 7
- MUST validate Phase 6 completion before PR
- CANNOT proceed if any gate fails
- MUST save results for validation

### OrchestratorAgent Requirements
- MUST verify `phase_6_testing.json` exists
- MUST check `quality_gates_passed` is true
- CANNOT merge PRs that failed testing

## Error Recovery

When tests fail:
1. Log detailed error information
2. Save workflow state for resumption
3. Provide clear fix guidance
4. NEVER bypass requirements
5. Wait for manual fixes before continuing
