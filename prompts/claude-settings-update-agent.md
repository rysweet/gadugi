# Claude Settings Update Agent Implementation

## Overview
Create a new specialized agent called `ClaudeSettingsUpdate` that merges `.claude/settings.local.json` into `.claude/settings.json` and maintains an alphabetically sorted allow-list. This agent will be integrated into the WorkflowManager's Phase 10 (after CodeReviewResponse) to ensure Claude settings are consistently updated after each workflow session.

## Problem Statement
Currently, there's no automated way to merge local Claude settings changes into the main settings file. This leads to:
- Manual maintenance of `.claude/settings.json`
- Inconsistent allow-list ordering
- Potential conflicts between local and global settings
- Missing integration with the workflow system

The new agent should handle this maintenance automatically as part of the standard workflow process.

## Technical Analysis

### Key Requirements
1. **Settings Merging**: Read both `.claude/settings.local.json` and `.claude/settings.json`, merge with local taking precedence
2. **Allow-list Sorting**: Ensure the allow-list array is sorted alphabetically for consistency
3. **Change Detection**: Only create PRs when actual changes are detected
4. **Separate PR Creation**: Settings updates should be in a separate PR from the main workflow
5. **Branch Management**: Switch back to main workflow branch after settings PR creation
6. **Graceful Handling**: Handle cases where settings.local.json doesn't exist
7. **WorkflowManager Integration**: Be invoked automatically in Phase 10 after CodeReviewResponse

### Integration Points
- **WorkflowManager Phase 10**: Add invocation after CodeReviewResponse agent
- **Branch Naming**: Use pattern `chore/update-claude-settings-TIMESTAMP`
- **PR Creation**: Use GitHub CLI for automated PR creation
- **State Management**: Update workflow state to track settings update PR

### Technical Approach
1. **Settings Parsing**: Use JSON parsing to read and merge configuration files
2. **Deep Merge Strategy**: Local settings override global settings with recursive merging
3. **Array Sorting**: Sort allow-list arrays alphabetically for consistent ordering
4. **Diff Detection**: Compare merged result with existing settings to detect changes
5. **Git Operations**: Create branch, commit changes, push, and create PR
6. **Error Handling**: Graceful failure handling with appropriate error messages

### File Structure
The agent will be created at:
- `.claude/agents/ClaudeSettingsUpdate.md`

And will modify:
- `.claude/agents/WorkflowManager.md` (add Phase 10 integration)

## Testing Requirements

### Unit Test Scenarios
1. **Merge Operations**:
   - Merge when both files exist with different settings
   - Handle missing settings.local.json gracefully
   - Handle missing settings.json gracefully
   - Verify local settings take precedence

2. **Sorting Functionality**:
   - Sort allow-list arrays alphabetically
   - Handle empty allow-lists
   - Handle malformed allow-lists

3. **Change Detection**:
   - Detect when changes are needed
   - Skip processing when no changes detected
   - Handle identical files correctly

4. **Git Operations**:
   - Branch creation with timestamp naming
   - Commit creation with proper messages
   - PR creation with appropriate title/body
   - Error handling for git failures

### Integration Test Scenarios
1. **WorkflowManager Integration**:
   - Verify invocation in Phase 10
   - Confirm branch switching behavior
   - Validate state management updates

2. **End-to-End Testing**:
   - Complete workflow with settings update
   - Multiple workflow sessions with accumulating changes
   - Error recovery scenarios

## Success Criteria

### Functional Requirements
✅ **Settings Merging**: Successfully merge settings.local.json into settings.json with local precedence
✅ **Allow-list Sorting**: Maintain alphabetically sorted allow-list arrays
✅ **Change Detection**: Only create PRs when actual changes exist
✅ **Separate PR Creation**: Settings updates in separate PR from main workflow
✅ **Branch Management**: Proper branch creation and switching
✅ **WorkflowManager Integration**: Automatic invocation in Phase 10
✅ **Error Handling**: Graceful handling of all error conditions

### Quality Requirements
✅ **Test Coverage**: Comprehensive unit and integration tests
✅ **Documentation**: Clear agent documentation with usage examples
✅ **Error Messages**: Helpful error messages for troubleshooting
✅ **Git Integration**: Proper git operations with meaningful commit messages
✅ **Performance**: Efficient processing without unnecessary operations

### Integration Requirements
✅ **Phase 10 Integration**: WorkflowManager automatically invokes after CodeReviewResponse
✅ **State Consistency**: Workflow state properly updated with settings PR information
✅ **Branch Isolation**: Settings changes don't interfere with main workflow PR
✅ **Recovery Support**: Workflow can resume if settings update fails

## Implementation Steps

### Phase 1: Agent Creation
1. Create GitHub issue for tracking
2. Create feature branch for implementation
3. Implement ClaudeSettingsUpdate.md agent
4. Create comprehensive test suite

### Phase 2: WorkflowManager Integration
1. Update WorkflowManager.md to include Phase 10 settings update
2. Add proper error handling and state management
3. Test integration thoroughly

### Phase 3: Documentation and Testing
1. Create usage documentation
2. Add troubleshooting guide
3. Validate all success criteria
4. Create pull request for review

### Phase 4: Validation
1. Test complete workflow end-to-end
2. Verify PR creation works correctly
3. Confirm branch management is proper
4. Validate error handling scenarios

## Implementation Notes

### JSON Merging Strategy
```json
{
  "localSettings": {
    "allow-list": ["new-file.ts", "existing-file.js"],
    "custom-option": "local-value"
  },
  "globalSettings": {
    "allow-list": ["existing-file.js", "old-file.py"],
    "custom-option": "global-value",
    "other-option": "preserved-value"
  },
  "mergedResult": {
    "allow-list": ["existing-file.js", "new-file.ts", "old-file.py"],
    "custom-option": "local-value",
    "other-option": "preserved-value"
  }
}
```

### Branch Naming Convention
- Pattern: `chore/update-claude-settings-YYYYMMDD-HHMMSS`
- Example: `chore/update-claude-settings-20250805-143022`

### Commit Message Format
```
chore: update Claude settings with local changes

- Merged settings from .claude/settings.local.json
- Sorted allow-list alphabetically
- [Additional changes if any]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### PR Title and Description Format
```
Title: chore: update Claude settings - [timestamp]

Body:
## Summary
Updates Claude settings by merging local changes and sorting allow-list.

## Changes
- Merged settings from `.claude/settings.local.json`
- Sorted allow-list alphabetically for consistency
- [List specific changes detected]

## Context
Automated settings update from WorkflowManager Phase 10.

🤖 Generated with [Claude Code](https://claude.ai/code)
```
