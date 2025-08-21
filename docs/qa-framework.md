# Gadugi v0.3 QA Framework

## Overview

The Gadugi v0.3 QA Framework provides comprehensive quality assurance tools for Python development, including dependency management, code formatting, type checking, testing, and pre-commit hooks.

## Tools and Configuration

### 1. UV - Python Dependency Management

UV is configured as the primary package manager for Gadugi v0.3.

**Installation:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Usage:**
```bash
# Install all dependencies
uv sync

# Install with QA extras
uv sync --all-extras

# Run any Python command
uv run python script.py
uv run pytest tests/
```

**Important:** ALL Python commands must be prefixed with `uv run` to ensure proper environment isolation.

### 2. Ruff - Code Formatting and Linting

Ruff is configured for fast Python formatting and linting with a 100-character line length.

**Configuration:** See `pyproject.toml` `[tool.ruff]` section

**Usage:**
```bash
# Format code
uv run ruff format .

# Check linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### 3. Pyright - Static Type Checking

Pyright provides strict static type checking for Python code.

**Configuration:** See `pyrightconfig.json`

**Usage:**
```bash
# Check all types
uv run pyright

# Check specific file
uv run pyright path/to/file.py

# Generate type stubs
uv run pyright --createstub package_name
```

### 4. Pytest - Testing Framework

Pytest is configured for comprehensive testing with coverage reporting.

**Configuration:** See `pyproject.toml` `[tool.pytest.ini_options]` section

**Usage:**
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=gadugi --cov-report=html

# Run specific test file
uv run pytest tests/test_specific.py

# Run tests matching pattern
uv run pytest -k "test_pattern"

# Run with verbose output
uv run pytest -v

# Run and stop on first failure
uv run pytest -x
```

### 5. Pre-commit Hooks

Pre-commit hooks automatically run quality checks before commits.

**Setup:**
```bash
# Install pre-commit hooks
uv run pre-commit install

# Run on all files manually
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

**Configured Hooks:**
- **File Checks:** trailing whitespace, end-of-file fixer, YAML/JSON/TOML validation
- **Python Formatting:** Ruff formatter (runs first)
- **Python Linting:** Ruff linter with auto-fix
- **Type Checking:** Pyright for static type analysis
- **Security:** detect-secrets to prevent credential leaks
- **Testing:** Pytest runs on pre-push (not every commit)

## Development Workflow

### 1. Initial Setup

```bash
# Clone repository
git clone <repository>
cd gadugi

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up environment
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### 2. Before Starting Work

```bash
# Ensure environment is up to date
uv sync --frozen

# Run all quality checks
uv run pre-commit run --all-files
```

### 3. During Development

```bash
# Format code as you work
uv run ruff format path/to/file.py

# Check types incrementally
uv run pyright path/to/file.py

# Run related tests
uv run pytest tests/test_module.py
```

### 4. Before Committing

```bash
# Pre-commit hooks run automatically, but you can test manually
uv run pre-commit run --all-files

# Run full test suite
uv run pytest --cov=gadugi
```

### 5. Fixing Issues

```bash
# Auto-fix formatting
uv run ruff format .

# Auto-fix linting issues
uv run ruff check --fix .

# Review type errors
uv run pyright

# Fix failing tests
uv run pytest -x --tb=short
```

## CI/CD Integration

Add these steps to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.9'

- name: Install UV
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync --all-extras

- name: Run ruff
  run: uv run ruff check .

- name: Run pyright
  run: uv run pyright

- name: Run tests
  run: uv run pytest --cov=gadugi --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Quality Standards

### Code Quality Requirements

1. **All code must pass ruff formatting** (100-character line length)
2. **All code must pass ruff linting** (configured rules in pyproject.toml)
3. **All code must be pyright clean** (strict mode, no type errors)
4. **All tests must pass** (100% of existing tests)
5. **Pre-commit hooks must pass** (all configured hooks)

### Testing Requirements

1. **Unit Tests:** All functions and classes should have unit tests
2. **Integration Tests:** Key workflows should have integration tests
3. **Coverage Target:** Maintain or improve existing coverage
4. **Test Documentation:** Tests should be well-documented with docstrings

### Type Safety Requirements

1. **Type Hints:** All functions should have type hints
2. **Return Types:** All functions should specify return types
3. **Variable Annotations:** Use type annotations for clarity
4. **No `Any` Types:** Avoid using `Any` unless absolutely necessary

## Troubleshooting

### Common Issues and Solutions

#### UV Environment Issues
```bash
# Recreate environment
rm -rf .venv
uv sync --all-extras
```

#### Pyright Import Errors
```bash
# Ensure UV environment is active
uv run pyright

# Check pyrightconfig.json paths
cat pyrightconfig.json
```

#### Pre-commit Hook Failures
```bash
# Skip hooks temporarily (emergency only)
git commit --no-verify

# Fix and re-run
uv run pre-commit run --all-files
```

#### Test Discovery Issues
```bash
# Verify test structure
uv run pytest --collect-only

# Run with more verbose output
uv run pytest -vvv
```

## Best Practices

1. **Always use UV:** Prefix all Python commands with `uv run`
2. **Commit often:** Smaller commits are easier to review
3. **Write tests first:** TDD helps ensure code quality
4. **Type everything:** Comprehensive type hints catch bugs early
5. **Format consistently:** Let ruff handle formatting automatically
6. **Review pre-commit output:** Don't skip hook failures
7. **Keep dependencies updated:** Regular `uv sync` ensures consistency

## Additional Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pyright Documentation](https://github.com/microsoft/pyright)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)

## Support

For issues or questions about the QA framework:
1. Check this documentation
2. Review error messages carefully
3. Consult tool-specific documentation
4. Open an issue with detailed error information