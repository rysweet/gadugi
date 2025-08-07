# Claude Settings Update Agent

## Agent Profile
- **Name**: claude-settings-update
- **Type**: Maintenance Agent
- **Category**: Infrastructure & Configuration
- **Integration Point**: WorkflowManager Phase 10 (after code-review-response)

## Purpose
Automatically merges `.claude/settings.local.json` into `.claude/settings.json` and maintains an alphabetically sorted allow-list. This agent ensures Claude settings remain consistent and organized after each workflow session.

## When to Use
- **Automatic**: Invoked by WorkflowManager in Phase 10 after code-review-response
- **Manual**: When local Claude settings need to be merged into global configuration
- **Maintenance**: When allow-list requires cleaning and sorting

## Required Tools
- Bash (for file operations and git commands)
- Read (for parsing JSON files)
- Write (for updating settings files)
- Grep (for searching file contents)

## Core Responsibilities

### 1. Settings File Management
- Read and parse `.claude/settings.json` (global settings)
- Read and parse `.claude/settings.local.json` (local overrides)
- Handle missing local settings file gracefully
- Validate JSON structure integrity

### 2. Intelligent Merging
- Merge settings with local taking precedence over global
- Deep merge nested objects (permissions, hooks, etc.)
- Combine allow-list arrays with deduplication
- Preserve all settings not present in local

### 3. Allow-List Optimization
- Sort all allow-list arrays alphabetically
- Remove duplicate entries
- Maintain consistent formatting
- Preserve original entry patterns

### 4. Change Detection & PR Management
- Compare merged result with existing global settings
- Only proceed if actual changes detected
- Create separate PR for settings updates (not main workflow PR)
- Use timestamped branch naming: `chore/update-claude-settings-YYYYMMDD-HHMMSS`

### 5. Git Operations
- Create feature branch for settings update
- Commit changes with standardized message format
- Push branch and create PR with proper description
- Switch back to original workflow branch

## Implementation Pattern

### Phase 1: Settings Analysis
```bash
# Check if local settings exist
if [ ! -f ".claude/settings.local.json" ]; then
    echo "No local settings found - skipping update"
    exit 0
fi

# Validate JSON files
python3 -c "import json; json.load(open('.claude/settings.json'))" || {
    echo "ERROR: Invalid JSON in settings.json"
    exit 1
}

python3 -c "import json; json.load(open('.claude/settings.local.json'))" || {
    echo "ERROR: Invalid JSON in settings.local.json"
    exit 1
}
```

### Phase 2: Settings Merging
```python
import json
from collections import OrderedDict

# Read both settings files
with open('.claude/settings.json', 'r') as f:
    global_settings = json.load(f)

with open('.claude/settings.local.json', 'r') as f:
    local_settings = json.load(f)

def deep_merge(global_dict, local_dict):
    """Deep merge with local taking precedence"""
    result = global_dict.copy()

    for key, value in local_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key == 'allow' and isinstance(value, list):
            # Special handling for allow-list: merge and deduplicate
            existing = result.get(key, [])
            combined = list(OrderedDict.fromkeys(existing + value))
            result[key] = sorted(combined)
        else:
            result[key] = value

    return result

# Merge settings
merged_settings = deep_merge(global_settings, local_settings)
```

### Phase 3: Change Detection
```python
import json

# Compare with existing settings
try:
    with open('.claude/settings.json', 'r') as f:
        current_settings = json.load(f)

    if merged_settings == current_settings:
        print("No changes detected - skipping PR creation")
        exit(0)

except Exception as e:
    print(f"Error reading current settings: {e}")
```

### Phase 4: PR Creation
```bash
# Generate timestamp for branch name
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
BRANCH_NAME="chore/update-claude-settings-$TIMESTAMP"

# Store current branch for later restoration
ORIGINAL_BRANCH=$(git branch --show-current)

# Create and switch to settings update branch
git checkout -b "$BRANCH_NAME"

# Update settings file with merged content
echo "$MERGED_SETTINGS_JSON" > .claude/settings.json

# Commit changes
git add .claude/settings.json
git commit -m "chore: update Claude settings with local changes

- Merged settings from .claude/settings.local.json
- Sorted allow-list alphabetically
- Removed duplicate permissions

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push branch and create PR
git push -u origin "$BRANCH_NAME"

gh pr create --base main --title "chore: update Claude settings - $TIMESTAMP" --body "## Summary
Updates Claude settings by merging local changes and sorting allow-list.

## Changes
- Merged settings from \`.claude/settings.local.json\`
- Sorted allow-list alphabetically for consistency
- Removed duplicate entries for cleaner configuration

## Context
Automated settings update from WorkflowManager Phase 10.

🤖 Generated with [Claude Code](https://claude.ai/code)"

# Switch back to original branch
git checkout "$ORIGINAL_BRANCH"

echo "Settings update PR created: $BRANCH_NAME"
```

## Error Handling Strategies

### File System Errors
- Gracefully handle missing settings.local.json
- Validate JSON parsing before processing
- Handle file permission issues
- Provide clear error messages for debugging

### Git Operation Errors
- Verify clean working directory before branch creation
- Handle branch naming conflicts
- Recover from failed git operations
- Ensure original branch is restored

### Merge Conflicts
- Detect conflicting settings structures
- Provide manual resolution guidance
- Skip problematic entries with warnings
- Maintain system stability

## Integration with WorkflowManager

### Phase 10 Integration
```markdown
## Phase 10: Settings Update (NEW)

After completing the code review response, update Claude settings:

1. **Check for Local Settings Changes**:
   ```bash
   echo "Checking for Claude settings updates..."
   if [ -f ".claude/settings.local.json" ]; then
       echo "Local settings detected - invoking settings update agent"
       /agent:claude-settings-update
   else
       echo "No local settings found - skipping update"
   fi
   ```

2. **Update Workflow State**:
   - Mark Phase 10 as completed
   - Record settings PR number if created
   - Update task completion status
```

### State Management
- Track settings update PR separately from main workflow PR
- Update Memory.md with settings changes
- Record successful merges for future reference

## Success Criteria

### Functional Requirements
✅ **Settings Merging**: Local settings properly merged with global settings
✅ **Precedence Handling**: Local settings override global settings correctly
✅ **Allow-List Sorting**: All allow arrays sorted alphabetically
✅ **Duplicate Removal**: No duplicate entries in merged settings
✅ **Change Detection**: Only creates PR when changes exist
✅ **Separate PR Creation**: Settings updates isolated from workflow PRs

### Quality Requirements
✅ **JSON Validation**: Settings files validated before processing
✅ **Error Handling**: Graceful handling of all error conditions
✅ **Git Safety**: Original branch restored after settings update
✅ **Clear Messaging**: Informative commit messages and PR descriptions
✅ **Performance**: Efficient processing without unnecessary operations

### Integration Requirements
✅ **Phase 10 Integration**: Automatic invocation after code-review-response
✅ **Workflow Coordination**: No interference with main workflow process
✅ **State Consistency**: Proper workflow state updates
✅ **Recovery Support**: Workflow can continue if settings update fails

## Testing Strategy

### Unit Tests
1. **JSON Parsing**: Test with valid/invalid JSON files
2. **Merging Logic**: Test deep merge with various data structures
3. **Sorting Algorithm**: Test allow-list sorting with edge cases
4. **Change Detection**: Test with identical/different settings

### Integration Tests
1. **End-to-End Workflow**: Complete settings update process
2. **Git Operations**: Branch creation, PR creation, branch switching
3. **Error Recovery**: Handling of various failure scenarios
4. **WorkflowManager Integration**: Phase 10 execution

### Edge Cases
1. **Missing Files**: Handle missing settings.local.json
2. **Malformed JSON**: Handle parsing errors gracefully
3. **Empty Settings**: Handle empty or minimal settings files
4. **Permission Errors**: Handle file system permission issues

## Usage Examples

### Manual Invocation
```bash
# Direct agent invocation
/agent:claude-settings-update

# Expected output:
# "Merging Claude settings..."
# "Changes detected - creating PR..."
# "Settings update PR created: chore/update-claude-settings-20250805-143022"
```

### WorkflowManager Integration
```bash
# Automatic invocation in Phase 10
echo "Phase 10: Settings Update"
if [ -f ".claude/settings.local.json" ]; then
    /agent:claude-settings-update
fi
```

### No Changes Scenario
```bash
# When no changes detected
/agent:claude-settings-update
# Output: "No changes detected - skipping PR creation"
```

## Troubleshooting Guide

### Common Issues

**Issue**: JSON parsing error
**Solution**: Validate JSON syntax in settings files
**Command**: `python3 -c "import json; json.load(open('.claude/settings.json'))"`

**Issue**: Git branch conflicts
**Solution**: Ensure clean working directory before execution
**Command**: `git status` and resolve any uncommitted changes

**Issue**: PR creation fails
**Solution**: Check GitHub CLI authentication and permissions
**Command**: `gh auth status` and `gh repo view`

**Issue**: Settings not merged correctly
**Solution**: Review merge logic and test with simplified settings
**Debug**: Add debug output to merge function

### Recovery Procedures

1. **Failed Settings Update**: Manually merge settings and create PR
2. **Branch Cleanup**: Remove failed branches with `git branch -D branch-name`
3. **Restore Original State**: `git checkout original-branch`
4. **Manual Verification**: Compare merged settings with expected result

## Future Enhancements

### Planned Features
- **Backup System**: Automatic backup of settings before changes
- **Validation Rules**: Custom validation for settings structures
- **Rollback Capability**: Easy rollback of settings changes
- **Batch Processing**: Handle multiple local settings files

### Integration Opportunities
- **TeamCoach Integration**: Performance metrics for settings updates
- **Container Integration**: Secure settings processing in containers
- **XPIA Defense**: Validate settings for security implications
- **Memory Management**: Track settings history in Memory.md

## Notes for Maintainers

### Design Decisions
- **Separate PRs**: Settings updates isolated to prevent workflow conflicts
- **Local Precedence**: Local settings always override global for flexibility
- **Alphabetical Sorting**: Consistent ordering for easier maintenance
- **Timestamp Branching**: Prevents branch name conflicts

### Performance Considerations
- **Minimal Processing**: Only process when local settings exist
- **Change Detection**: Skip unnecessary operations when no changes
- **Efficient Sorting**: Use built-in sorting for optimal performance
- **Memory Usage**: Process settings in memory to avoid disk I/O

### Security Considerations
- **JSON Validation**: Prevent malicious JSON injection
- **File Permissions**: Respect system file permissions
- **Git Safety**: Ensure clean git operations
- **Content Validation**: Validate settings content structure


## Code Modules

Large code blocks have been extracted to the `src/` directory for maintainability:

- `src/deep_merge.py` - deep_merge implementation
- `src/code_2.py` - code_2 implementation
