# Workflow for Issue #249: Remove Error Suppression from Critical Paths

## Task
Audit and remove error suppression (2>/dev/null and stderr=subprocess.DEVNULL) from critical code paths, especially in agent invocations and tests.

## Implementation Steps
1. Search for all error suppression patterns
2. Remove suppression from critical paths
3. Add proper error handling
4. Add justification comments for kept suppressions
5. Test all changes

## Files to Check
- Test files in tests/
- Agent implementation files in src/
- Scripts in .github/scripts/ and .claude/scripts/

Execute complete workflow with all 13 phases.
