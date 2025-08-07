def generate_conflict_resolution_prompt(pr_number, conflict_assessment):
    return f"""
# Merge Conflict Resolution for PR #{pr_number}

## Objective
Resolve merge conflicts in PR #{pr_number} and ensure clean merge capability.

## Conflict Details
- Affected files: {', '.join(conflict_assessment.affected_files)}
- Complexity: {conflict_assessment.resolution_complexity}
- Base branch: main

## Resolution Steps
1. Checkout PR branch locally
2. Rebase against latest main
3. Resolve conflicts using automated strategies where possible
4. Run test suite to validate resolution
5. Push resolved changes to PR branch

## Success Criteria
- No merge conflicts remain
- All tests pass
- Code review approval maintained
- Clean git history preserved
"""
