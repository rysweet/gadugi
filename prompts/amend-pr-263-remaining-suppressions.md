# Amend PR #263 to Remove Remaining Error Suppressions

**Task**: Add commits to existing PR #263 to remove ALL remaining error suppression instances

**Context**:
- PR #263 (fix/issue-249-remove-error-suppression) is still open
- It already addresses some error suppressions but missed 11+ instances
- Need to complete the job by fixing all remaining suppressions
- This is an AMENDMENT to the existing PR, not a new one

**Requirements**:

## Step 1: Continue on Existing Branch
- Work on branch: fix/issue-249-remove-error-suppression
- Add new commits to fix remaining issues

## Step 2: Fix Remaining Error Suppressions

### Files to Fix:
1. **container_runtime/image_manager.py** (4 instances)
   - Lines 279, 316, 317, 387: `|| true` after find commands
   - Replace with proper error handling or add justification comment

2. **.github/workflows/test-uv.yml** (1 instance)
   - Line 34: `sudo systemctl status docker || true`
   - This is diagnostic output - add comment explaining it's for debugging

3. **.claude/utils/orphaned_pr_recovery.sh** (1 instance)
   - Line 199: Complex jq query with `2>/dev/null || true`
   - Handle query errors properly

4. **.claude/scripts/enforce_phase_9.sh** (1 instance)
   - Line 192: `gh pr comment "$PR_NUMBER" --body "$success_comment" || true`
   - Check if comment posting succeeds

5. **.claude/agents/team-coach.md** (1 instance)
   - Line 48: `gh label create` with `2>/dev/null || true`
   - Check if label exists first before creating

6. **.claude/agents/workflow-manager.md** (2 instances)
   - Lines 682-683: Git operations with `|| true`
   - Handle git errors properly

7. **.claude/agent-manager/scripts/agent-manager.sh** (1 instance)
   - Line 17: `shift || true`
   - Handle argument shifting edge case

## Step 3: Add Error Handling Documentation

Create `docs/error-handling-guidelines.md` with comprehensive guidelines

## Step 4: Update PR Description

Add to PR #263 description:
- List of ALL error suppressions removed (original + these new ones)
- Link to new error handling guidelines document
- Explanation of why this is important

## Expected Outcome:
- PR #263 will have additional commits fixing all remaining suppressions
- Total of ~25+ error suppression instances fixed across the codebase
- Clear documentation preventing future occurrences
- All CI checks still passing
