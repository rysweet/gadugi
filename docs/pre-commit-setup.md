# Pre-commit Setup and Usage Guide

This guide covers the setup and usage of pre-commit hooks in the Gadugi project.

## Quick Setup

### For UV Projects (Recommended)

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks on all files (verify setup)
uv run pre-commit run --all-files
```

### For Standard Python Projects

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (verify setup)
pre-commit run --all-files
```

## What Pre-commit Hooks Do

Our pre-commit configuration automatically runs these checks:

### Code Quality
- **ruff**: Python linting with auto-fixes
- **ruff-format**: Code formatting
- **debug-statements**: Removes debug print statements

### File Quality
- **trailing-whitespace**: Removes trailing spaces
- **end-of-file-fixer**: Ensures files end with newline
- **check-yaml**: Validates YAML syntax
- **check-merge-conflict**: Detects merge conflict markers

### Security
- **detect-secrets**: Finds potential secrets in code

### Testing (on push)
- **pytest**: Runs test suite before pushing

## Usage

### Automatic Usage

Once installed, hooks run automatically:

```bash
git commit -m "Your commit message"
# Hooks run automatically before commit
```

### Manual Usage

Run hooks manually anytime:

```bash
# Run all hooks on changed files
uv run pre-commit run  # UV projects
pre-commit run         # Standard projects

# Run all hooks on all files
uv run pre-commit run --all-files  # UV projects
pre-commit run --all-files         # Standard projects

# Run specific hook
uv run pre-commit run ruff          # UV projects
pre-commit run ruff                 # Standard projects
```

## Troubleshooting

### Installation Issues

**Hook installation failed:**
```bash
# Reinstall hooks
uv run pre-commit uninstall
uv run pre-commit install
```

**Pre-commit command not found:**
```bash
# For UV projects - pre-commit should be in pyproject.toml
uv sync --all-extras

# For standard projects - install pre-commit
pip install pre-commit
```

### Hook Execution Issues

**Hooks failing on commit:**
```bash
# See detailed output
uv run pre-commit run --all-files --verbose

# Skip hooks temporarily (not recommended)
git commit -m "message" --no-verify
```

**Specific hook failing:**
```bash
# Run individual hook to see details
uv run pre-commit run ruff --verbose
uv run pre-commit run trailing-whitespace --verbose
```

### Configuration Updates

**Update hook versions:**
```bash
# Update to latest versions
uv run pre-commit autoupdate

# Commit the updated .pre-commit-config.yaml
git add .pre-commit-config.yaml
git commit -m "Update pre-commit hook versions"
```

## Configuration Reference

Our `.pre-commit-config.yaml` configuration:

```yaml
repos:
  # Python code quality
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [ --fix ]  # Auto-fix issues where possible
      - id: ruff-format

  # General file quality
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements
      - id: mixed-line-ending
        args: ['--fix=lf']

  # Security scanning
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: .*\.lock$|package-lock\.json$

  # Testing (runs on push, not commit)
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest  # Use 'pytest' for non-UV projects
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-push]

# Global settings
default_language_version:
  python: python3.13

default_stages: [pre-commit, pre-push]

# Files to exclude from all hooks
exclude: |
  (?x)^(
    .*\.skip$|
    \.venv/.*|
    venv/.*|
    \.git/.*|
    \.pytest_cache/.*|
    __pycache__/.*|
    \.worktrees/.*
  )
```

## Best Practices

### For Developers

1. **Install hooks immediately** after cloning repository
2. **Run manually** before important commits
3. **Don't skip hooks** unless absolutely necessary
4. **Fix issues** rather than bypassing checks
5. **Update regularly** to get latest improvements

### For Teams

1. **Standardize on UV** for consistent tooling
2. **Document exceptions** when hooks must be skipped
3. **Review hook failures** in code reviews
4. **Update configurations** as project needs evolve
5. **Monitor hook performance** to prevent slow commits

## Integration with Workflows

Pre-commit hooks integrate with our development workflow:

- **Phase 6 Testing**: Agents verify all hooks pass
- **PR Creation**: Hooks must pass before PR creation
- **Code Review**: Hook failures prevent PR approval
- **CI/CD**: Hooks run again in continuous integration

This ensures consistent code quality across all development activities.