# Eliminate All Remaining Error Suppression Instances

**Task**: Remove all instances of `|| true` and `2>/dev/null` error suppression and add documentation to prevent future occurrences

**Context**:
- PR #263 addressed error suppression but instances remain
- Found 11+ instances of `|| true` pattern
- Found 2+ instances of `2>/dev/null || true` pattern
- This violates our error handling principles

**Requirements**:

## Step 1: Fix All Error Suppression Instances

### Files to Fix:
1. **container_runtime/image_manager.py** (4 instances)
   - Lines 279, 316, 317, 387
   - Replace with proper error handling or justify if truly optional

2. **.github/workflows/test-uv.yml** (1 instance)
   - Line 34: `sudo systemctl status docker || true`
   - Replace with proper status check

3. **.claude/utils/orphaned_pr_recovery.sh** (1 instance)
   - Line 199: Complex query with suppression
   - Handle query errors properly

4. **.claude/scripts/enforce_phase_9.sh** (1 instance)
   - Line 192: `gh pr comment` with suppression
   - Handle comment posting errors

5. **.claude/agents/team-coach.md** (1 instance)
   - Line 48: Label creation with suppression
   - Check if label exists first

6. **.claude/agents/workflow-manager.md** (2 instances)
   - Lines 682-683: Git operations with suppression
   - Handle git errors properly

7. **.claude/agent-manager/scripts/agent-manager.sh** (1 instance)
   - Line 17: `shift || true`
   - Handle argument shifting properly

## Step 2: Add Error Handling Guidelines

Create a new document: `docs/error-handling-guidelines.md` with:

### Content for Guidelines:
```markdown
# Error Handling Guidelines

## NEVER Suppress Errors

### ❌ Bad Patterns to Avoid:
- `command || true` - Hides all failures
- `command 2>/dev/null` - Suppresses error messages
- `command 2>&1 >/dev/null` - Suppresses everything
- `try: ... except: pass` - Python equivalent of suppression

### ✅ Good Patterns to Use:

#### Pattern 1: Check Before Acting
\`\`\`bash
# Check if resource exists before creating
if ! gh label list | grep -q "MyLabel"; then
    gh label create "MyLabel" --color "7057ff"
fi
\`\`\`

#### Pattern 2: Handle Specific Errors
\`\`\`bash
# Capture and handle specific error
if ! result=$(command 2>&1); then
    echo "Command failed with: $result"
    # Take appropriate action
fi
\`\`\`

#### Pattern 3: Justified Suppression (RARE)
\`\`\`bash
# ONLY when failure is truly optional and documented
# Justification: Directory might not exist, but that's OK
rm -rf /tmp/cache/* 2>/dev/null || true  # Optional cleanup, OK if fails
\`\`\`

## When Suppression Might Be Acceptable

ONLY suppress errors when ALL conditions are met:
1. The operation is truly optional
2. Failure doesn't affect the program's correctness
3. A clear comment explains why suppression is justified
4. The suppression is logged for debugging

## Examples of Proper Error Handling

### Dockerfile Cleanup (Currently Problematic)
\`\`\`dockerfile
# Bad
RUN find /usr -name "__pycache__" -type d -exec rm -rf {} + || true

# Good
RUN find /usr -name "__pycache__" -type d -exec rm -rf {} + 2>&1 | grep -v "No such file" || echo "Cleanup completed"
\`\`\`

### GitHub CLI Operations
\`\`\`bash
# Bad
gh pr comment "$PR" --body "$msg" || true

# Good
if ! gh pr comment "$PR" --body "$msg" 2>&1; then
    echo "Warning: Could not post comment to PR $PR"
    # Continue but log the issue
fi
\`\`\`

### Git Operations
\`\`\`bash
# Bad
git push || true

# Good
if ! git push 2>&1; then
    echo "Push failed - checking for conflicts..."
    git pull --rebase
    git push
fi
\`\`\`

## Testing for Error Suppression

Add to CI/CD pipeline:
\`\`\`bash
# Check for error suppression patterns
if grep -r "|| true" --include="*.sh" --include="*.py" .; then
    echo "Error: Found error suppression with '|| true'"
    exit 1
fi
\`\`\`

## Remember

> "Every suppressed error is a future debugging nightmare."

Errors are valuable information. Handle them, log them, but never hide them.
```

## Step 3: Update Contributing Guidelines

Add section to CONTRIBUTING.md about error handling requirements

## Step 4: Add Pre-commit Hook

Create pre-commit hook to detect error suppression patterns

## Implementation Priority:
1. Fix all existing suppressions
2. Add documentation
3. Add automated checks
4. Update contributing guidelines
