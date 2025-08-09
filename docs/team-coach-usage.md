# Team Coach Agent Usage Guide

## Overview

The Team Coach agent is automatically invoked at the end of every workflow session (Phase 13) to analyze performance and identify improvement opportunities.

## Automatic Invocation

Team Coach runs automatically during Phase 13 of the workflow to:
1. Analyze the completed session
2. Identify improvement opportunities
3. Create GitHub issues for actionable improvements
4. Update Memory.md with insights

## GitHub Issue Creation

### Label Management

Team Coach automatically manages its own label:
- **Label Name**: `CreatedByTeamCoach`
- **Color**: Purple (#7057ff)
- **Description**: "Issues created by Team Coach agent"

The agent will:
1. Create the label if it doesn't exist
2. Apply it to all issues it creates
3. Handle existing labels gracefully

### Issue Format

All Team Coach issues follow this format:
- **Title**: `[Team Coach] <specific improvement>`
- **Labels**: `enhancement, CreatedByTeamCoach`
- **Body**: Structured with Opportunity, Evidence, Solution, and Impact sections

## Finding Team Coach Issues

To find all issues created by Team Coach:

```bash
# List all Team Coach created issues
gh issue list --label "CreatedByTeamCoach"

# Search for Team Coach issues
gh issue list --search "[Team Coach]"
```

## Manual Invocation

While Team Coach normally runs automatically, you can invoke it manually:

```
/agent:team-coach

Analyze the current session and provide improvement recommendations.
```

## Configuration

The Team Coach agent is configured in `.claude/agents/team-coach.md` with:
- Proper YAML frontmatter for agent registration
- Tools: Read, Write, Edit, Bash, Grep, LS, TodoWrite, WebSearch
- Model: inherit (uses the same model as the main Claude session)

## Best Practices

1. **Review Team Coach Issues Regularly**: Check the CreatedByTeamCoach label weekly
2. **Prioritize High-Impact Improvements**: Focus on issues that affect multiple workflows
3. **Close Completed Improvements**: Mark issues as closed when implemented
4. **Provide Feedback**: Add comments to Team Coach issues to guide future analysis

## Troubleshooting

### Team Coach Doesn't Run
- Check that Phase 13 is enabled in workflow-manager.md
- Verify team-coach.md has proper YAML frontmatter
- Ensure no error suppression (`2>/dev/null`) in Phase 13 execution

### Issues Not Created
- Verify GitHub CLI is authenticated: `gh auth status`
- Check that the repository allows issue creation
- Ensure the CreatedByTeamCoach label isn't restricted

### Label Not Applied
- Team Coach will create the label automatically
- If creation fails, it will still create the issue with 'enhancement' label
- Check repository permissions for label creation

## Recent Improvements

- Added proper YAML frontmatter for agent registration
- Implemented automatic label creation
- Removed error suppression for better debugging
- Standardized agent naming to `/agent:team-coach`