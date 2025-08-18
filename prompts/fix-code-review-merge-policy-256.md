# Fix Code-Review-Response Agent PR Merge Policy Violation (Issue #256)

## Context
The code-review-response agent is violating the PR merge policy by automatically merging PRs without explicit user approval. This is a critical governance violation that removes user control over the main branch.

## Requirements

### Primary Task
Update the `.claude/agents/code-review-response.md` agent to enforce the PR merge approval policy.

### Specific Changes Required

1. **Modify the merge behavior** in the code-review-response agent:
   - Remove any automatic merge logic
   - Add explicit prompting for user approval before merge
   - Must ask: "Would you like me to merge this PR?" and wait for response
   - Only proceed with merge after receiving explicit approval (e.g., "yes", "merge it", "please merge")

2. **Add clear documentation** in the agent file:
   - Document the PR merge approval policy prominently
   - Include examples of correct vs incorrect patterns
   - Add warning comments near any merge-related code

3. **Ensure compliance** with project standards:
   - Follow the existing agent file format and structure
   - Maintain compatibility with the workflow-manager integration
   - Preserve all other agent functionality

## Validation Criteria

- [ ] Agent file updated with merge approval logic
- [ ] Clear user prompting before any merge action
- [ ] Documentation added explaining the policy
- [ ] Examples provided of correct behavior
- [ ] No automatic merging without user consent

## Testing Requirements

- Manually test the agent with a sample PR review scenario
- Verify it prompts for approval before attempting merge
- Confirm it waits for and correctly interprets user response
- Test both approval and rejection scenarios

## References

- Issue #256: Code-review-response agent violating PR merge policy
- CLAUDE.md: PR Merge Approval Policy section
- Memory.md: Team Coach insights about governance violations
