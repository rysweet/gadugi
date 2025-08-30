# Fix Type Errors in PR Backlog Manager Tests

## Objective
Fix all pyright type errors in the PR Backlog Manager agent test files, which account for ~330 errors.

## Target Files
- tests/agents/pr_backlog_manager/test_delegation_coordinator.py (142 errors)
- tests/agents/pr_backlog_manager/test_core.py (57 errors)
- tests/agents/pr_backlog_manager/test_integration.py (48 errors)
- tests/agents/pr_backlog_manager/test_readiness_assessor.py (46 errors)
- tests/agents/pr_backlog_manager/test_github_actions_integration.py (39 errors)

## Focus Areas
1. **reportAttributeAccessIssue**: Fix mock object attribute access with proper type stubs
2. **reportOptionalSubscript**: Handle optional dictionary/list access properly
3. **reportOptionalMemberAccess**: Add None checks before accessing optional attributes

## Strategy
1. Create type stubs for mock objects used in tests
2. Add proper None checks for optional values
3. Use Union types where multiple types are possible
4. Ensure all GitHub API mock responses have correct types
5. Fix delegation status and state type issues

## Requirements
- Maintain test functionality and coverage
- Use typing.Protocol for mock object interfaces
- Add comprehensive type hints to test fixtures
- Ensure no runtime behavior changes
