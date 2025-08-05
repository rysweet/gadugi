# Fix Test Type Errors (Priority P2)

## Context
Fix type errors in test files after core modules have been properly typed. Test files often have different typing requirements and patterns that need specialized handling.

## Requirements

### 1. Test-Specific Type Fixes
Address unique test typing challenges:
- Mock object typing and test fixtures
- Pytest fixture type annotations
- Test parameter typing for parametrized tests
- Assert statement type compatibility

### 2. Test Framework Integration
Properly type test framework components:
- Pytest fixtures and conftest.py
- Test class inheritance and methods
- Mock objects and patches
- Async test typing

### 3. Test Data Typing
Type test data and utilities:
- Test factories and builders
- Sample data structures
- Test configuration objects
- Validation helpers

## Implementation Strategy

### Phase 1: Test Infrastructure Typing
1. **conftest.py files**
   - Type pytest fixtures properly
   - Add return type annotations for fixture functions
   - Type shared test utilities

2. **Test base classes**
   - Type test class inheritance
   - Add proper setUp/tearDown typing
   - Type shared test methods

### Phase 2: Integration Test Typing
Focus on integration tests as they interact with core modules:

1. **Orchestrator integration tests**
   - Type multi-agent coordination tests
   - Fix parallel execution test typing
   - Type result aggregation testing

2. **WorkflowMaster integration tests**
   - Type workflow orchestration tests
   - Fix state management test typing
   - Type phase transition testing

3. **Shared module integration tests**
   - Type GitHub operation tests
   - Fix error handling test typing
   - Type state persistence testing

### Phase 3: Unit Test Typing
Fix unit tests for individual components:

1. **Mock object typing**
   - Properly type Mock and MagicMock objects
   - Add type annotations for patched methods
   - Type mock return values and side effects

2. **Test parameter typing**
   - Type parametrized test parameters
   - Add proper test data typing
   - Type test factories and builders

3. **Assertion typing**
   - Fix type compatibility in assertions
   - Type custom assertion helpers
   - Handle optional and nullable types in tests

## Test-Specific Type Patterns

### Pytest Fixture Typing
```python
from typing import Generator, Any
import pytest

@pytest.fixture
def sample_task() -> Task:
    return Task(id="test-task", status="pending")

@pytest.fixture
def mock_github_ops() -> Generator[Mock, None, None]:
    with patch('shared.github_operations.GitHubOperations') as mock:
        yield mock
```

### Mock Object Typing
```python
from unittest.mock import Mock, MagicMock
from typing import cast

def test_workflow_execution():
    mock_executor = cast(Mock, MagicMock(spec=WorkflowExecutor))
    mock_executor.execute.return_value = OperationResult(success=True, data=None)
```

### Parametrized Test Typing
```python
@pytest.mark.parametrize(
    "input_data,expected_result",
    [
        (TaskData(id="1", status="pending"), True),
        (TaskData(id="2", status="completed"), False),
    ]
)
def test_task_processing(input_data: TaskData, expected_result: bool):
    assert process_task(input_data) == expected_result
```

### Async Test Typing
```python
import pytest
from typing import AsyncGenerator

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    client = AsyncClient()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_async_operation(async_client: AsyncClient) -> None:
    result = await async_client.perform_operation()
    assert result.success
```

## Automated Tools

### test_type_fixer.py
```python
# Automated test type fixing
def fix_fixture_typing(file_path: str) -> None:
    """Add type annotations to pytest fixtures"""

def fix_mock_typing(file_path: str) -> None:
    """Add proper typing for mock objects"""

def fix_parametrize_typing(file_path: str) -> None:
    """Add type annotations for parametrized tests"""
```

### test_type_validator.py
```python
# Test type validation
def validate_fixture_types(file_path: str) -> List[str]:
    """Validate pytest fixture type annotations"""

def check_mock_compatibility(file_path: str) -> List[str]:
    """Check mock object type compatibility"""

def verify_test_data_types(file_path: str) -> List[str]:
    """Verify test data type consistency"""
```

## Test File Categories

### High Priority Test Files
1. **Integration tests** - Test core system interactions
2. **Shared module tests** - Test foundational components
3. **Agent coordination tests** - Test multi-agent workflows

### Medium Priority Test Files
1. **Unit tests** - Test individual components
2. **Utility tests** - Test helper functions
3. **Configuration tests** - Test setup and configuration

### Low Priority Test Files
1. **Example tests** - Demonstration code tests
2. **Legacy tests** - Older test patterns
3. **Experimental tests** - Prototype testing code

## Validation Process

### Test-Specific Validation
1. **Type checking**: Ensure pyright passes on test files
2. **Test execution**: All tests continue to pass
3. **Mock validation**: Mock objects properly typed and functional
4. **Fixture validation**: Pytest fixtures work correctly with typing

### Comprehensive Testing
1. Run full test suite after type fixes
2. Verify no test regressions introduced
3. Check test coverage maintained
4. Validate test performance not degraded

## Success Criteria
- Reduce test file type errors by 80%+
- All integration tests properly typed
- Mock objects and fixtures correctly typed
- 100% test pass rate maintained
- Test execution time not significantly increased

## Deliverables
1. **Type-Fixed Test Files**
   - All integration tests with proper type annotations
   - Unit tests with appropriate typing
   - Test utilities and fixtures typed correctly

2. **Test Typing Guidelines**
   - Best practices for typing test code
   - Patterns for common test scenarios
   - Mock object typing standards

3. **Test Type Tools**
   - Automated test type fixing scripts
   - Test type validation utilities
   - Type coverage tools for tests

4. **Test Type Documentation**
   - Guide for typing test code
   - Common patterns and solutions
   - Troubleshooting for test type issues
