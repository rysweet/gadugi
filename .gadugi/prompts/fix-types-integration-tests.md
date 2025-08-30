# Fix Type Errors in Integration Tests

## Objective
Fix type errors in integration test files that test the enhanced separation architecture.

## Target Files
- tests/integration/test_enhanced_separation_basic.py (12 errors)
- tests/integration/test_enhanced_separation_basic_broken.py (12 errors)
- tests/integration/test_workflow_manager_enhanced_separation.py (6 errors)
- tests/integration/test_orchestrator_agent_enhanced_separation.py
- tests/test_workflow_manager_consistency.py (10 errors)
- tests/test_program_manager.py (10 errors)

## Focus Areas
1. **Mock object typing**: Ensure all mocks have proper type annotations
2. **Fixture typing**: Add type hints to pytest fixtures
3. **Import organization**: Fix missing imports and circular dependencies
4. **Assertion typing**: Ensure assertion comparisons have compatible types

## Strategy
1. Add comprehensive type stubs for all mock objects
2. Use pytest type hints for fixtures
3. Fix import issues with TYPE_CHECKING pattern
4. Ensure all test data has proper type annotations
5. Add Protocol definitions for complex mock interfaces

## Requirements
- All integration tests must continue to pass
- Test coverage must be maintained
- No changes to test logic, only type annotations
- Preserve all existing test functionality
