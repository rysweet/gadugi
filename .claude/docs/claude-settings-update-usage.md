# Claude Settings Update Agent - Usage Guide

## Overview

The `ClaudeSettingsUpdate` agent automatically manages Claude settings by merging local changes into global configuration and maintaining consistent formatting. This agent is designed to run automatically as part of the WorkflowManager process, but can also be invoked manually when needed.

## Table of Contents

1. [Automatic Usage (Recommended)](#automatic-usage-recommended)
2. [Manual Usage](#manual-usage)
3. [Settings File Structure](#settings-file-structure)
4. [Merge Behavior](#merge-behavior)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Automatic Usage (Recommended)

### WorkflowManager Integration

The agent runs automatically in **Phase 11** of the WorkflowManager process:

```bash
# Automatic execution flow:
# Phase 8: PR Creation
# Phase 9: Code Review
# Phase 10: Review Response
# Phase 11: Settings Update (AUTOMATIC) ← ClaudeSettingsUpdate runs here
```

When you complete a workflow using WorkflowManager, the settings update happens automatically:

```bash
# Example WorkflowManager execution
/agent:WorkflowManager "Execute workflow for /prompts/my-feature.md"

# Output will include:
# ... other phases ...
# ✅ Phase 10: Review Response completed
# 📋 Phase 11: Claude Settings Update
# ✅ Local settings detected - invoking settings update agent
# 🚀 AUTOMATIC: Invoking ClaudeSettingsUpdate agent
# Settings update PR created: chore/update-claude-settings-20250805-143022
# ✅ Settings update completed successfully
```

### What Happens Automatically

1. **Detection**: Checks if `.claude/settings.local.json` exists
2. **Merging**: Merges local settings into global settings with proper precedence
3. **Sorting**: Alphabetically sorts all allow-list arrays
4. **Change Detection**: Only creates PR if actual changes detected
5. **Branch Creation**: Creates timestamped branch (`chore/update-claude-settings-YYYYMMDD-HHMMSS`)
6. **PR Creation**: Creates separate PR for settings updates
7. **Branch Restoration**: Returns to original workflow branch

## Manual Usage

### Direct Invocation

You can invoke the agent manually when needed:

```bash
# Manual invocation
/agent:ClaudeSettingsUpdate

# Expected output when changes detected:
# Merging Claude settings...
# Changes detected - creating PR...
# Settings update PR created: chore/update-claude-settings-20250805-143022

# Expected output when no changes:
# No changes detected - skipping PR creation
```

### When to Use Manual Invocation

- **Ad-hoc Settings Updates**: When you've made local changes outside of a workflow
- **Maintenance**: Periodic cleanup of settings files
- **Testing**: Validating settings merge behavior
- **Recovery**: After failed automatic execution

## Settings File Structure

### Global Settings (`.claude/settings.json`)

The main Claude configuration file:

```json
{
  "permissions": {
    "additionalDirectories": ["/tmp"],
    "allow": [
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(echo:*)",
      "Bash(python:*)"
    ],
    "deny": []
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $CLAUDE_PROJECT_DIR/.claude/hooks/cleanup.py",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

### Local Settings (`.claude/settings.local.json`)

Local overrides and additions:

```json
{
  "permissions": {
    "allow": [
      "Bash(git push:*)",
      "Bash(gh pr create:*)",
      "Bash(claude:*)",
      "Bash(docker:*)"
    ]
  }
}
```

### Merged Result

After agent processing:

```json
{
  "permissions": {
    "additionalDirectories": ["/tmp"],
    "allow": [
      "Bash(claude:*)",
      "Bash(docker:*)",
      "Bash(echo:*)",
      "Bash(gh pr create:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(python:*)"
    ],
    "deny": []
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $CLAUDE_PROJECT_DIR/.claude/hooks/cleanup.py",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

## Merge Behavior

### Deep Merging Rules

1. **Local Precedence**: Local settings always override global settings
2. **Deep Merge**: Nested objects are merged recursively
3. **Array Handling**: Special logic for `allow` arrays (merge + deduplicate + sort)
4. **Preservation**: Global settings not in local are preserved

### Allow-List Processing

```json
// Before merge:
"global_allow": ["Bash(git add:*)", "Bash(echo:*)", "Bash(python:*)"]
"local_allow": ["Bash(git push:*)", "Bash(echo:*)", "Bash(docker:*)"]

// After merge (combined, deduplicated, sorted):
"merged_allow": [
  "Bash(docker:*)",
  "Bash(echo:*)",      // ← deduplicated
  "Bash(git add:*)",
  "Bash(git push:*)",
  "Bash(python:*)"
]
```

### Nested Object Merging

```json
// Global settings
"hooks": {
  "Stop": [{"command": "stop1"}],
  "Start": [{"command": "start1"}]
}

// Local settings
"hooks": {
  "Stop": [{"command": "stop2"}]  // ← will override
}

// Merged result
"hooks": {
  "Stop": [{"command": "stop2"}],  // ← local took precedence
  "Start": [{"command": "start1"}] // ← global preserved
}
```

## Common Scenarios

### Scenario 1: New Permissions

You need to add new bash commands for a project:

```bash
# 1. Add to .claude/settings.local.json
echo '{
  "permissions": {
    "allow": [
      "Bash(npm install:*)",
      "Bash(npm run:*)",
      "Bash(yarn:*)"
    ]
  }
}' > .claude/settings.local.json

# 2. Run workflow or manual update
/agent:ClaudeSettingsUpdate

# 3. Review and merge the settings PR
gh pr view $(gh pr list --author "@me" --json number --jq '.[0].number')
```

### Scenario 2: Project-Specific Settings

Different projects need different permissions:

```json
// For Python projects
{
  "permissions": {
    "allow": [
      "Bash(pip install:*)",
      "Bash(python -m pytest:*)",
      "Bash(poetry:*)"
    ]
  }
}

// For Node.js projects
{
  "permissions": {
    "allow": [
      "Bash(npm install:*)",
      "Bash(npm run:*)",
      "Bash(yarn install:*)"
    ]
  }
}
```

### Scenario 3: Cleanup and Organization

Existing settings are messy and need cleanup:

```bash
# 1. Current settings.json has duplicates and poor ordering
# 2. Create empty local settings to trigger cleanup
echo '{"permissions": {"allow": []}}' > .claude/settings.local.json

# 3. Run agent to clean up
/agent:ClaudeSettingsUpdate

# 4. Remove local settings after cleanup
rm .claude/settings.local.json
```

### Scenario 4: No Changes Needed

Agent detects no changes and skips PR creation:

```bash
/agent:ClaudeSettingsUpdate

# Output:
# Checking for Claude settings changes...
# ✅ Local settings detected - parsing files
# 🔍 Comparing merged settings with current settings
# ℹ️  No changes detected - skipping PR creation
# ✅ Settings already up to date
```

## Troubleshooting

### Common Issues

#### Issue: JSON Parsing Error

```bash
# Error message:
# ERROR: Invalid JSON in settings.local.json

# Solution: Validate JSON syntax
python3 -c "import json; json.load(open('.claude/settings.local.json'))"

# Fix JSON syntax errors and retry
```

#### Issue: Git Branch Conflicts

```bash
# Error message:
# fatal: A branch named 'chore/update-claude-settings-...' already exists

# Solution: Clean up existing branches
git branch -D chore/update-claude-settings-20250805-143022

# Or wait for timestamp to change and retry
```

#### Issue: PR Creation Fails

```bash
# Error message:
# gh: HTTP 401: Unauthorized

# Solution: Check GitHub CLI authentication
gh auth status
gh auth login  # if needed
```

#### Issue: Settings Not Merged Correctly

```bash
# Debug: Check merge logic
python3 -c "
import json
from collections import OrderedDict

with open('.claude/settings.json') as f:
    global_settings = json.load(f)

with open('.claude/settings.local.json') as f:
    local_settings = json.load(f)

print('Global:', json.dumps(global_settings, indent=2))
print('Local:', json.dumps(local_settings, indent=2))
"
```

### Recovery Procedures

#### Failed Settings Update

1. **Check git status**: `git status`
2. **Review branch state**: `git branch -a`
3. **Manual merge**: Edit `.claude/settings.json` manually
4. **Create PR manually**: Use `gh pr create`
5. **Clean up**: Remove temporary branches

#### Corrupt Settings Files

1. **Backup current files**: `cp .claude/settings.json .claude/settings.json.backup`
2. **Validate JSON**: Use online JSON validator
3. **Restore from git**: `git checkout HEAD -- .claude/settings.json`
4. **Reapply changes**: Manually merge needed changes

## Best Practices

### Development Workflow

1. **Use Local Settings**: Always make changes in `.claude/settings.local.json`
2. **Test First**: Validate JSON before running agent
3. **Review PRs**: Always review settings PRs before merging
4. **Keep Clean**: Remove local settings after merging if no longer needed

### Settings Organization

```json
{
  "permissions": {
    "allow": [
      // Group related commands together with comments

      // Git operations
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",

      // GitHub CLI
      "Bash(gh pr create:*)",
      "Bash(gh issue create:*)",

      // Development tools
      "Bash(python:*)",
      "Bash(npm:*)",
      "Bash(docker:*)"
    ]
  }
}
```

### Security Considerations

1. **Validate Permissions**: Review all new permissions for security implications
2. **Principle of Least Privilege**: Only add permissions actually needed
3. **Regular Audits**: Periodically review and clean up unused permissions
4. **Dangerous Commands**: Be extra careful with commands like `rm`, `sudo`, `curl`

### Performance Tips

1. **Minimal Local Settings**: Keep local settings as small as possible
2. **Batch Changes**: Make multiple changes at once rather than frequent small updates
3. **Clean Branches**: Delete old settings update branches regularly
4. **Monitor PR Count**: Don't accumulate too many open settings PRs

## Integration Examples

### With CI/CD Pipelines

```yaml
# .github/workflows/settings-validation.yml
name: Validate Claude Settings
on:
  pull_request:
    paths:
      - '.claude/settings.json'
      - '.claude/settings.local.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate JSON
        run: |
          python3 -c "import json; json.load(open('.claude/settings.json'))"
          if [ -f ".claude/settings.local.json" ]; then
            python3 -c "import json; json.load(open('.claude/settings.local.json'))"
          fi
```

### With Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: claude-settings-validation
        name: Validate Claude Settings
        entry: python3 -c "import json, sys; json.load(open(sys.argv[1]))"
        language: system
        files: '^\.claude/settings.*\.json$'
```

### With Development Scripts

```bash
#!/bin/bash
# scripts/update-claude-settings.sh

set -e

echo "🔧 Updating Claude settings..."

# Validate local settings if they exist
if [ -f ".claude/settings.local.json" ]; then
    echo "📋 Validating local settings..."
    python3 -c "import json; json.load(open('.claude/settings.local.json'))"
    echo "✅ Local settings are valid JSON"
fi

# Run settings update agent
echo "🚀 Running ClaudeSettingsUpdate agent..."
/agent:ClaudeSettingsUpdate

echo "✅ Settings update completed!"
```

## Advanced Usage

### Custom Merge Logic

For advanced users who need custom merge behavior, you can create a wrapper script:

```python
#!/usr/bin/env python3
"""Custom settings merge with additional validation."""

import json
import os
from collections import OrderedDict

def custom_merge(global_settings, local_settings):
    """Custom merge with additional validation rules."""

    # Basic deep merge
    result = deep_merge(global_settings, local_settings)

    # Custom validation rules
    dangerous_commands = ['rm -rf', 'sudo', 'dd if=']
    allow_list = result.get('permissions', {}).get('allow', [])

    for cmd in allow_list:
        for dangerous in dangerous_commands:
            if dangerous in cmd:
                print(f"⚠️  WARNING: Potentially dangerous command detected: {cmd}")

    return result

def deep_merge(global_dict, local_dict):
    """Standard deep merge logic."""
    # ... implementation ...
    pass

if __name__ == '__main__':
    # Use custom merge logic before calling agent
    with open('.claude/settings.json') as f:
        global_settings = json.load(f)

    with open('.claude/settings.local.json') as f:
        local_settings = json.load(f)

    merged = custom_merge(global_settings, local_settings)

    # Proceed with agent invocation
    os.system('/agent:ClaudeSettingsUpdate')
```

### Batch Processing Multiple Projects

```bash
#!/bin/bash
# Process settings for multiple projects

PROJECTS=(
    "/path/to/project1"
    "/path/to/project2"
    "/path/to/project3"
)

for project in "${PROJECTS[@]}"; do
    echo "Processing $project..."
    cd "$project"

    if [ -f ".claude/settings.local.json" ]; then
        /agent:ClaudeSettingsUpdate
    else
        echo "No local settings found in $project"
    fi
done
```

This comprehensive usage guide covers all aspects of using the ClaudeSettingsUpdate agent effectively in various scenarios and environments.
