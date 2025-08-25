# Remove Error Suppression from Critical Code Paths (Issue #249)

## Context
Error suppression (using `2>/dev/null` and `stderr=subprocess.DEVNULL`) in critical code paths is masking real failures and preventing proper debugging. This was discovered when Team Coach agent registration failures were hidden by error suppression in tests.

## Requirements

### Primary Task
Audit and remove error suppression from all critical code paths, especially in agent invocations and tests.

### Specific Changes Required

1. **Search and identify** all instances of error suppression:
   - Find all occurrences of `2>/dev/null` in shell commands
   - Find all occurrences of `stderr=subprocess.DEVNULL` in Python code
   - Find all occurrences of `stderr=DEVNULL` (imported variant)
   - Focus on test files and agent-related code

2. **Remove suppression from critical paths**:
   - Agent invocation code (workflow-manager, orchestrator, etc.)
   - Test files that validate agent functionality
   - Core system operations (git commands, file operations)
   - CI/CD scripts and validation code

3. **Keep suppression only where justified**:
   - Truly optional operations (e.g., cleanup that may fail)
   - Each kept suppression must have a comment explaining why
   - Comment format: `# Error suppression justified: [specific reason]`

4. **Replace with proper error handling**:
   - Log errors instead of suppressing them
   - Use try-except blocks with appropriate error messages
   - Return error states that can be checked by callers

## Files to Check (Priority Order)

1. Test files:
   - `tests/test_team_coach.py`
   - `tests/test_workflow_manager.py`
   - `tests/test_orchestrator.py`
   - Any other test files with agent invocations

2. Agent implementation files:
   - `src/orchestrator/*.py`
   - `src/workflow_manager/*.py`
   - Any subprocess or shell command execution code

3. Scripts and utilities:
   - `.github/scripts/*.py`
   - `.claude/scripts/*.sh`
   - Build and CI/CD scripts

## Validation Criteria

- [ ] All error suppression instances identified
- [ ] Critical path suppressions removed
- [ ] Proper error handling added where needed
- [ ] Justification comments added for kept suppressions
- [ ] Tests still pass after changes
- [ ] Errors now properly visible in logs

## Testing Requirements

- Run full test suite to ensure nothing breaks
- Manually trigger error conditions to verify they're visible
- Check that CI/CD logs show errors when they occur
- Verify agent registration failures are now caught

## References

- Issue #249: Audit and remove error suppression from critical paths
- Memory.md: Team Coach session insights about hidden failures
- Previous incident where Team Coach registration failed silently
