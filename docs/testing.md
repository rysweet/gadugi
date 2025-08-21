# Test Infrastructure Documentation

## Overview

This document describes the test infrastructure setup, dependencies, and best practices for the Gadugi project.

## Test Dependencies

### Required Packages
- `pytest`: Core testing framework
- `pytest-xdist`: Parallel test execution
- `pytest-cov`: Coverage reporting
- `pytest-timeout`: Test timeout management
- `pytest-asyncio`: Async test support

### Installation
```bash
# Using UV (recommended)
uv sync --all-extras

# Install test dependencies
uv add --group dev pytest pytest-xdist pytest-cov pytest-timeout pytest-asyncio
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_specific.py

# Run tests matching pattern
uv run pytest -k "test_pattern"
```

### Parallel Test Execution
```bash
# Run tests in parallel (auto-detect CPU cores)
uv run pytest -n auto

# Run with specific number of workers
uv run pytest -n 4

# Run with load balancing
uv run pytest -n auto --dist loadscope
```

### Test Coverage
```bash
# Run with coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term

# Generate coverage badge
uv run pytest --cov=. --cov-report=term --cov-report=html --cov-report=json
```

### Test Markers
```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Combine markers
uv run pytest -m "unit and not slow"
```

## Test Organization

### Directory Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Shared test fixtures
├── conftest.py     # Pytest configuration and fixtures
└── data/          # Test data files
```

### Test Naming Conventions
- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Mock external dependencies

### 2. Test Documentation
```python
def test_complex_scenario():
    """
    Test that complex workflow handles edge cases.
    
    Given: Initial state with specific conditions
    When: Action is performed
    Then: Expected outcome occurs
    """
    # Test implementation
```

### 3. Fixture Usage
```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### 4. Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiplication(input, expected):
    assert input * 2 == expected
```

### 5. Async Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == expected_value
```

## Performance Optimization

### Test Result Caching
pytest automatically caches test results between runs:

```bash
# Clear cache
uv run pytest --cache-clear

# Show cache info
uv run pytest --cache-show

# Rerun only failed tests
uv run pytest --lf  # last failed
uv run pytest --ff  # failed first
```

### Parallel Execution Strategies
- `--dist load`: Distribute tests as they complete (default)
- `--dist loadscope`: Group by module for better fixture reuse
- `--dist loadfile`: Group by file
- `--dist loadgroup`: Group by xdist_group mark

### CI/CD Optimization
```yaml
# Example GitHub Actions configuration
- name: Run Tests
  run: |
    uv run pytest \
      -n auto \
      --dist loadscope \
      --cov=. \
      --cov-report=xml \
      --cov-report=term \
      --junit-xml=test-results.xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes source directory
2. **Fixture Not Found**: Check fixture scope and conftest.py location
3. **Parallel Test Failures**: Some tests may need serialization
4. **Coverage Gaps**: Ensure all source files are included in coverage

### Debug Options
```bash
# Show fixture usage
uv run pytest --fixtures

# Show test collection without running
uv run pytest --collect-only

# Verbose failure output
uv run pytest -vv --tb=long

# Drop into debugger on failure
uv run pytest --pdb
```

## Prerequisites

### System Requirements
- Python 3.11 or higher
- UV package manager (recommended)
- Git for version control

### Environment Setup
1. Clone repository
2. Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Set up environment: `uv sync --all-extras`
4. Run tests: `uv run pytest`

## Continuous Integration

Tests are automatically run on:
- Every push to main branch
- Every pull request
- Scheduled nightly builds

See `.github/workflows/` for CI configuration details.