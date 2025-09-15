# Fix UV Migration Test Failures

## Objective
Comprehensively analyze and fix all 39 failing tests to achieve 100% test pass rate for UV migration PR #36.

## Background
- Current test status: 522/561 passing (93.0% pass rate)
- 39 tests are failing, these failures existed before UV migration
- Need to systematically fix or properly skip tests to complete migration

## Failing Tests Analysis

### 1. GitHub Actions Integration (1 test)
- `test_from_environment_schedule` - PR number assertion failure

### 2. Enhanced Separation Basic Tests (6 tests total)
- TodoWrite integration failures
- StateManager API compatibility issues
- Code duplication calculation errors

### 3. Orchestrator Agent Tests (7 tests)
- CircuitBreaker parameter issues
- Missing API methods (batch_merge_pull_requests, etc.)
- WorkflowPhase enum issues

### 4. WorkflowManager Tests (10 tests)
- GitHubOperations config issues
- Missing verify_pull_request_exists method
- TaskData initialization problems
- ErrorContext parameter issues

### 5. Program Manager Tests (2 tests)
- Triage and priority update failures

### 6. TeamCoach Hook Tests (13 tests)
- Missing 'claude' command in CI
- JSON parsing errors in settings
- Hook execution failures

## Fix Strategy

### Phase 1: Quick Wins
1. Fix JSON syntax errors in settings files
2. Add conditional skips for tests requiring 'claude' CLI
3. Fix simple API parameter mismatches

### Phase 2: API Compatibility
1. Update test expectations to match actual API
2. Fix missing method mocks
3. Resolve enum and constant issues

### Phase 3: Integration Tests
1. Fix TodoWrite integration expectations
2. Resolve StateManager compatibility
3. Update orchestration test scenarios

### Phase 4: CI-Specific Issues
1. Skip tests requiring unavailable commands
2. Add environment detection for CI
3. Mock external dependencies properly

## Implementation Steps

1. **Create Issue**: "Fix 39 failing tests blocking UV migration merge"
2. **Create Branch**: `fix/uv-migration-test-failures`
3. **Group Fixes**: Address similar failures together
4. **Test Locally**: Ensure fixes work in dev environment
5. **Test in CI**: Verify all tests pass in GitHub Actions
6. **Document**: Explain each fix or skip decision
7. **Create PR**: With comprehensive description of changes

## Success Criteria
- All tests either pass or skip with clear reason
- No reduction in actual test coverage
- CI runs green on all platforms
- Clear documentation of changes

## Notes
- Use TestSolver agent for complex failures
- Some tests may be obsolete and can be removed
- Prioritize fixing over skipping when possible
- Ensure backwards compatibility maintained
