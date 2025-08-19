# Fix Test Infrastructure - Critical

## Objective
Fix all 22 test collection errors to enable the test suite to run properly.

## Current Issues
1. **Missing imports in test_stubs.py**: `Callable` not imported
2. **Test collection failures**: 22 tests cannot be collected
3. **Import errors**: Various test files have broken imports

## Requirements
1. Fix ALL test collection errors
2. Ensure `uv run pytest` can collect all tests
3. Verify tests actually run (not just collect)
4. No test suppression - fix actual issues

## Test Command
```bash
# This is a UV project - use uv run
uv sync --all-extras
uv run pytest tests/ -v --tb=short
```

## Success Criteria
- ZERO test collection errors
- All tests can be executed (passing or failing is ok)
- Clean pytest output with no import warnings

## Files to Check
- tests/test_stubs.py (primary issue)
- tests/agents/*/test_*.py (various import issues)
- tests/test_*.py (root level tests)

Create PR when complete.
