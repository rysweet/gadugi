# Team Coach Label Implementation

## Issue #250: Team Coach should create and use dedicated label for issues

### Requirements
1. Team Coach should create a 'CreatedByTeamCoach' label if it doesn't exist
2. All issues created by Team Coach should use this label
3. The label should have purple color (7057ff)
4. Update the team-coach.md agent file with these changes

### Implementation Details

The Team Coach agent needs to be updated to:
1. Create the 'CreatedByTeamCoach' label with purple color (7057ff) if it doesn't already exist
2. Use this label on all issues it creates
3. Include proper error handling for label creation (silent failure if label exists)

### Changes Needed

In `/Users/ryan/src/gadugi6/gadugi/.claude/agents/team-coach.md`:

1. Add label creation command before creating issues (around line 45-49)
2. Update the issue creation command to include the 'CreatedByTeamCoach' label (around line 69)
3. Add documentation about the label requirement

### Testing
- Verify the label gets created with correct color
- Verify all Team Coach issues get the label
- Verify silent failure if label already exists
