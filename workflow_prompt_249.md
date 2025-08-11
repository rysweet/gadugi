# WorkflowManager Prompt for Issue #249

## Task Details
- **Issue**: #249 - Remove error suppression from critical paths
- **Worktree**: /workspaces/gadugi/.worktrees/issue-249-error-suppression
- **Branch**: fix/issue-249-error-suppression
- **Priority**: HIGH

## Implementation Requirements

### Remove Error Suppression from Critical Paths

Error suppression (2>/dev/null and stderr=subprocess.DEVNULL) is hiding real problems in tests and agent invocations. This needs to be audited and fixed.

### Required Changes

1. **Search for all error suppression patterns**:
   - Find all instances of `2>/dev/null` in shell commands
   - Find all instances of `stderr=subprocess.DEVNULL` in Python code
   - Find all instances of `stderr=DEVNULL` in Python code
   - Check test files in `tests/` directory
   - Check agent implementation files in `src/`
   - Check scripts in `.github/scripts/` and `.claude/scripts/`

2. **Remove suppression from critical paths**:
   - Agent invocations should never suppress errors
   - Test assertions should never suppress errors
   - Critical subprocess calls should log errors
   - Keep suppression only where justified with comments

3. **Add proper error handling**:
   - Replace suppression with proper try/except blocks
   - Log errors appropriately
   - Let tests fail visibly when there are real problems
   - Add error context to exceptions

4. **Add justification comments**:
   - For any kept suppressions, add clear comments explaining why
   - Document what errors are expected and safe to ignore
   - Ensure future developers understand the reasoning

## Workflow Phases to Execute

Execute all 13 phases:
1. Initial Setup
2. Issue Creation (Issue #249 already exists)
3. Branch Management (branch already created)
4. Research and Planning
5. Implementation
6. Testing
7. Documentation
8. Pull Request
9. Review (invoke code-reviewer)
10. Review Response
11. Settings Update
12. Deployment Readiness
13. Team Coach Reflection

## Success Criteria

- All error suppression removed from critical paths
- Proper error handling added where needed
- Justification comments for any kept suppressions
- Tests properly fail when there are real problems
- Agent invocations show errors when they occur
- All tests pass after changes