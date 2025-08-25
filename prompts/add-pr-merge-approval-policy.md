# Add PR Merge Approval Policy to Instructions

## Objective
Update project instructions to ensure future Claude sessions never auto-merge PRs without explicit user approval.

## Problem
Claude has been auto-merging PRs after successful review without waiting for user approval. This removes user control over what enters the main branch.

## Requirements

### 1. Update CLAUDE.md
Add a new section "PR Merge Approval Policy" that includes:
- Clear statement: "NEVER merge PRs without explicit user approval"
- Required workflow steps (create, review, respond, STOP AND WAIT)
- Correct pattern example (wait for user approval)
- Incorrect pattern example (auto-merging)
- Why this policy exists

### 2. Update Memory.md
Add to Important Notes section:
- "PR Merge Policy: NEVER merge PRs without explicit user approval"
- Make this highly visible for future sessions

### 3. Documentation Standards
- Use clear, emphatic language (⚠️ CRITICAL)
- Provide concrete examples
- Explain the reasoning
- Make it impossible to miss

## Implementation Details

The sections should emphasize:
1. Create PR → Review → Respond → STOP
2. Report status and wait for explicit approval
3. Only merge when user says "merge it" or similar
4. User maintains control over main branch

## Success Criteria
- Future Claude sessions will see this policy immediately
- Clear examples prevent misunderstanding
- User control over merges is maintained
- Policy is documented in multiple places for redundancy