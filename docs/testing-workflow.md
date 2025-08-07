# Testing Workflow Documentation

This document provides comprehensive guidance on the mandatory testing workflow that all agents and developers must follow in the Gadugi project.

## Overview

The Gadugi project enforces mandatory testing at Phase 6 of every workflow. This ensures code quality, prevents regressions, and maintains reliability standards across all development activities.

### Key Principles

1. **No PR without passing tests** - All tests must pass before PR creation
2. **Quality gates cannot be bypassed** - Agents must stop workflow if tests fail
3. **Comprehensive validation** - Tests, linting, formatting, and pre-commit hooks all required
4. **UV project support** - Full support for UV Python projects with proper command usage
5. **State tracking** - Test results are recorded for orchestrator validation

## Workflow Phases Integration

### Phase 6: Mandatory Testing

Every agent executing workflows must implement Phase 6 with these steps:

1. **Environment Setup**
   - Detect UV vs standard Python projects
   - Setup appropriate virtual environment
   - Install dependencies as needed

2. **Test Execution**
   - Run full test suite with pytest
   - Ensure all tests pass (no failures, no errors)
   - Handle test coverage if configured

3. **Code Quality Validation**
   - Run ruff linting checks
   - Verify code formatting with ruff format
   - Apply auto-fixes where possible

4. **Pre-commit Hook Validation**
   - Install pre-commit hooks if not present
   - Run all configured pre-commit hooks
   - Ensure all hooks pass

5. **Result Recording**
   - Create `.task/phase_6_testing.json` with test results
   - Record exit codes for all quality checks
   - Mark phase as completed only if all checks pass

### Phase 8: Pre-PR Validation

Before creating any PR, agents must:

1. Verify Phase 6 completion by checking `.task/phase_6_testing.json`
2. Confirm all quality gates passed
3. Only proceed if test validation is successful

## Command Reference

### UV Projects (Recommended)

UV projects are detected by the presence of both `pyproject.toml` and `uv.lock` files.

```bash
# Environment setup
uv sync --all-extras

# Run tests
uv run pytest tests/ -v
uv run pytest tests/ --cov=. --cov-report=html  # With coverage

# Code quality
uv run ruff check .          # Linting
uv run ruff format .         # Formatting

# Type checking (optional)
uv run mypy . --ignore-missing-imports

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files
```

### Standard Python Projects (Legacy)

For projects without UV support:

```bash
# Environment setup (if needed)
source venv/bin/activate  # If virtual environment exists

# Run tests
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html

# Code quality
ruff check .
ruff format .

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Agent Implementation Requirements

### WorkflowManager Agent

The WorkflowManager MUST:

- Implement `execute_phase_6_testing()` function
- Call testing function before Phase 7 (Documentation)
- Stop workflow if any quality gate fails
- Record test results in proper JSON format
- Validate Phase 6 completion before PR creation

### OrchestratorAgent

The OrchestratorAgent MUST:

- Validate `.task/phase_6_testing.json` exists for all completed tasks
- Check `test_results.quality_gates_passed` is true
- Not proceed with PR merging for tasks that failed testing
- Report test validation failures clearly
- Maintain test validation statistics

## Test Result Format

Test results are recorded in `.task/phase_6_testing.json`:

```json
{
    "phase_6_testing": {
        "completed": true,
        "status": "success",
        "timestamp": "2025-08-07T01:00:00Z",
        "test_results": {
            "pytest_exit_code": 0,
            "precommit_exit_code": 0,
            "lint_exit_code": 0,
            "format_exit_code": 0,
            "skipped_tests": 0,
            "quality_gates_passed": true,
            "coverage_percentage": 85  // Optional
        }
    }
}
```

### Status Values

- `"success"` - All tests passed, all quality gates passed
- `"failed"` - One or more quality gates failed
- `"error"` - Testing could not be completed due to environment issues

## Error Handling

### Test Failures

When tests fail, agents should:

1. **Log detailed error information**
   ```bash
   echo "❌ TESTS FAILED - Workflow cannot continue"
   echo "Fix all test failures before proceeding to Phase 7"
   ```

2. **Save workflow state** to allow resumption
3. **Return non-zero exit code** to stop workflow
4. **Never bypass** testing requirements

### Linting Failures

When linting fails, agents should:

1. **Attempt auto-fix** where possible (ruff --fix)
2. **Report remaining issues** that require manual intervention
3. **Stop workflow** until issues are resolved

### Pre-commit Hook Failures

When pre-commit hooks fail, agents should:

1. **Report specific hook failures**
2. **Provide guidance** on how to fix issues
3. **Stop workflow** until all hooks pass

## Pre-commit Configuration

The `.pre-commit-config.yaml` must include essential quality checks:

```yaml
repos:
  # Code formatting and linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [ --fix ]
      - id: ruff-format

  # Basic file quality checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: debug-statements

  # Security checks
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets

  # Test execution on push
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest  # or pytest for non-UV projects
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-push]
```

## Troubleshooting

### Common Issues

**UV environment not found:**
```bash
uv sync --all-extras
```

**Pre-commit hooks not installed:**
```bash
uv run pre-commit install  # For UV projects
pre-commit install         # For standard projects
```

**Tests failing due to missing dependencies:**
```bash
# Check pyproject.toml for test dependencies
uv sync --all-extras  # Ensures test dependencies are installed
```

**Permission issues with git hooks:**
```bash
chmod +x .git/hooks/pre-commit
```

### Debug Commands

```bash
# Check UV environment
uv run python -c "import sys; print(sys.executable)"

# Verify pytest can run
uv run pytest --collect-only

# Test specific file
uv run pytest tests/specific_test.py -v

# Check pre-commit configuration
uv run pre-commit run --all-files --verbose
```

## Best Practices

### For Developers

1. **Run tests locally** before committing
2. **Use pre-commit hooks** to catch issues early
3. **Write meaningful test descriptions**
4. **Mock external dependencies** appropriately
5. **Maintain test isolation**

### For Agents

1. **Fail fast** on test failures
2. **Provide clear error messages**
3. **Save state for recovery**
4. **Validate environment before testing**
5. **Record comprehensive test results**

### For Project Maintenance

1. **Keep test dependencies up to date**
2. **Review test coverage regularly**
3. **Update pre-commit hook versions**
4. **Monitor test execution times**
5. **Add new quality checks as needed**

## Integration with CI/CD

The testing workflow integrates with continuous integration:

- **Pre-commit hooks** run on every commit
- **Full test suite** runs on every push
- **Quality gates** prevent merge of failing code
- **Coverage reports** track test quality over time

## Metrics and Monitoring

The workflow tracks:

- Test execution times
- Pass/fail rates
- Code coverage percentages
- Quality gate success rates
- Agent compliance with testing requirements

These metrics help maintain and improve code quality standards across the project.