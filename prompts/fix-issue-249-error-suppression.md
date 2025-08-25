# Fix Issue #249: Remove Error Suppression from Critical Code Paths

## Issue Summary
Error suppression (2>/dev/null, stderr=subprocess.DEVNULL) is hiding critical failures in agent invocations and test validations, making debugging difficult and masking real problems.

## Requirements

### 1. Identify Error Suppression Patterns
Search for and analyze all instances of:
- `2>/dev/null` in shell commands
- `stderr=subprocess.DEVNULL` in Python subprocess calls
- `stderr=DEVNULL` variations
- Any other error suppression patterns

### 2. Remove Suppression from Critical Paths
Remove error suppression from:
- Agent invocation code (workflow manager, orchestrator)
- Test validation scripts
- CI/CD pipeline scripts
- Agent registration and execution code
- Any subprocess calls that invoke Claude or agents

### 3. Keep Suppression Only Where Justified
Retain error suppression only for:
- Truly optional operations (e.g., cleanup that might fail harmlessly)
- Commands where stderr contains expected noise (with comment explaining why)
- Each retained suppression MUST have a comment justifying its use

### 4. Implementation Strategy
- Start with most critical files: orchestrator, workflow-manager, test scripts
- Replace suppression with proper error handling and logging
- Ensure errors are logged but execution continues where appropriate
- Add try/catch blocks with meaningful error messages

## Files to Search and Fix
Priority files to check:
- `/workspaces/gadugi/src/orchestrator/*.py`
- `/workspaces/gadugi/.claude/scripts/*.sh`
- `/workspaces/gadugi/.github/scripts/*.py`
- `/workspaces/gadugi/tests/test_*.py`
- Any workflow or agent execution scripts

## Success Criteria
- No error suppression in critical agent invocation paths
- All retained suppressions have clear justification comments
- Errors are properly logged rather than hidden
- Test failures become visible immediately
- Debugging is easier with full error output

## Testing Requirements
- Verify agent invocations show errors when they fail
- Confirm test scripts report actual failures
- Check that CI/CD pipeline shows all error messages
- Ensure logging captures previously suppressed errors
