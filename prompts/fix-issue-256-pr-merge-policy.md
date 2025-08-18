# Fix Issue #256: Code-review-response Agent Violating PR Merge Policy

## Issue Summary
The code-review-response agent is automatically merging PRs without waiting for explicit user approval, violating the project's PR merge policy.

## Requirements

### 1. Update Agent Instructions
- Modify `.claude/agents/code-review-response.md` to enforce user approval requirement
- Add explicit prompts asking for user permission before merging
- Ensure agent NEVER auto-merges even after successful review

### 2. Implementation Details
- Add a clear section in the agent instructions about PR merge policy
- Include example dialogues showing correct vs incorrect behavior
- Add validation step that checks for explicit user approval words like "merge it", "please merge", "go ahead and merge"

### 3. Key Changes Needed
- Update the "Phase 10: Review Response" section to include approval workflow
- Add "CRITICAL: PR Merge Approval Required" section with clear examples
- Modify any merge command templates to include approval check

### 4. Testing Requirements
- Verify agent instructions contain the new merge policy
- Ensure examples demonstrate waiting for approval
- Check that merge commands are conditional on user approval

## Success Criteria
- Agent instructions explicitly state PR merge requires user approval
- Clear examples show agent asking "Would you like me to merge this PR?"
- Documentation includes both correct and incorrect patterns
- No automatic merging occurs without explicit user consent

## Files to Modify
- `.claude/agents/code-review-response.md` - Primary agent instructions

## Related Context
- This is part of fixing governance violations discovered in Team Coach session
- PR #253 was auto-merged without permission, demonstrating the issue
- Must align with project-wide PR merge policy in CLAUDE.md
