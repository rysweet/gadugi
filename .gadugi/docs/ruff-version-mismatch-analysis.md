# Ruff Version Mismatch Analysis

## Problem
Pre-commit hooks and CI are formatting code differently, causing conflicts where:
- Local pre-commit changes formatting one way
- CI expects different formatting
- This creates a loop where commits fail CI even after local formatting

## Root Cause
**Version mismatch between pre-commit and project dependencies:**

### Pre-commit Configuration (.pre-commit-config.yaml)
- Uses: `https://github.com/astral-sh/ruff-pre-commit`
- Version: `v0.8.4`
- This installs: **ruff==0.8.4**

### Project Dependencies (pyproject.toml)
- Specifies: **ruff==0.12.7**

### CI Environment (.github/workflows/test-uv.yml)
- Runs: `uv run ruff format --check .`
- Uses: **ruff==0.12.7** (from pyproject.toml via uv)

## Why This Causes Issues
Different versions of ruff have different formatting rules. Between v0.8.4 and v0.12.7, there were changes in how multi-line assertions are formatted:

### Ruff 0.8.4 formats as:
```python
assert (
    duplication_reduction_percentage > 70.0
), f"Expected >70% duplication reduction, got {duplication_reduction_percentage:.1f}%"
```

### Ruff 0.12.7 formats as:
```python
assert duplication_reduction_percentage > 70.0, (
    f"Expected >70% duplication reduction, got {duplication_reduction_percentage:.1f}%"
)
```

## Solution
Update `.pre-commit-config.yaml` to use a version of ruff-pre-commit that includes ruff 0.12.7:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.7  # Update from v0.8.4 to match pyproject.toml
    hooks:
      - id: ruff
        args: [ --fix ]
      - id: ruff-format
```

## Alternative Solutions

### Option 1: Pin to Specific Version (Recommended)
Keep pre-commit and pyproject.toml versions in sync by updating both when upgrading ruff.

### Option 2: Use Local Hook
Replace the pre-commit ruff hooks with local hooks that use the project's installed version:
```yaml
- repo: local
  hooks:
    - id: ruff
      name: ruff
      entry: uv run ruff check --fix
      language: system
      types: [python]
    - id: ruff-format
      name: ruff-format
      entry: uv run ruff format
      language: system
      types: [python]
```

### Option 3: Use System Hook
Let pre-commit use the system-installed ruff:
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.12.7
  hooks:
    - id: ruff
      args: [ --fix ]
      language: system  # Use system ruff instead of isolated one
```

## Verification Steps
After applying the fix:
1. Run `pre-commit clean` to clear cached environments
2. Run `pre-commit install --install-hooks` to reinstall hooks
3. Test formatting on the problematic file
4. Verify CI passes with the same formatting

## Prevention
1. Add a CI check that validates pre-commit config versions match project dependencies
2. Document the requirement to update both locations when upgrading ruff
3. Consider using a single source of truth for tool versions (e.g., only use uv/pyproject.toml)
