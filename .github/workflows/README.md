# GitHub Actions AI Code Review

This directory contains a simple GitHub Actions workflow that automatically invokes the `code-reviewer` agent for pull request reviews.

## Workflow: AI Code Review

**File:** `ai-code-review.yml`

### When it runs:
- When a pull request is opened (and not a draft)
- When a pull request is marked as ready for review

### What it does:
1. Checks out the repository code with full git history
2. Uses the Anthropic Claude Code Base Action to invoke the code-reviewer agent
3. Provides the prompt: "Use the code-reviewer subagent to check changes in this PR"
4. Uses the repository's `.claude/settings.json` configuration
5. Extracts the review and posts it as a comment on the PR

### Requirements:
- `ANTHROPIC_API_KEY` secret must be configured in the repository
- `.claude/settings.json` file must exist in the repository
- The repository must have a `code-reviewer` agent defined in `.claude/agents/`

### Configuration:
The workflow uses the repository's Claude configuration located in the `.claude/` directory, ensuring it follows the project's specific agent setup and permissions defined in `.claude/settings.json`.
