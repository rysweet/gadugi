# Bug Fix Workflow Template

This template demonstrates the workflow for bug fixes.

## Phase 1: Issue Creation

```bash
gh issue create --title "fix: [bug description]" --body "$(cat <<'EOF'
## Bug Description
[What is broken]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Expected vs Actual]

## Root Cause
[Analysis of why it's happening]

## Fix Approach
[How to fix it]

## Testing Plan
[How to verify the fix]
EOF
)"
```

## Phase 2: Branch Creation

```bash
# Assuming issue #N was created
git checkout -b fix/[bug-description]-N
```

## Phase 3: Research and Diagnosis

1. Reproduce the bug:
   ```bash
   python reproduce_bug.py
   pytest tests/test_affected_module.py::test_specific -v
   ```

2. Analyze root cause:
   ```bash
   grep -n "error_message" --include="*.py" .
   git log -p affected/file.py
   ```

3. Document findings in Memory.md

## Phase 4: Implementation

Focused fix with minimal changes:
1. Fix the root cause
2. Handle edge cases
3. Prevent regression

## Phase 5: Testing

```python
# Add regression test
def test_bug_regression(self):
    """Test that [bug description] is fixed."""
    # Setup conditions that caused bug
    # Verify it now works correctly
    # Test edge cases
```

## Phase 6: Documentation

- Add comment explaining the fix
- Update any affected documentation
- Document any behavior changes

## Phase 7: Pull Request

```bash
gh pr create --base main --title "fix: [bug description]" --body "$(cat <<'EOF'
## Summary
This PR fixes [bug description] by [fix approach].

## Root Cause
[Explanation of what was wrong]

## Solution
[Explanation of the fix]

## Testing
- Added regression test
- Verified original issue is resolved
- Tested edge cases

## Related Issues
Fixes #N

*Note: This PR was created by an AI agent on behalf of the repository owner.*

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"
```

## Phase 8: Review

Invoke code reviewer and ensure:
- Fix is minimal and focused
- No unintended side effects
- Regression test is comprehensive