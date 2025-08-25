# Agent Registration Validation System

## Overview

This validation system ensures all agent files have proper YAML frontmatter to prevent runtime registration failures. It runs automatically in CI/CD and pre-commit hooks.

## Components

### 1. Validation Script
- **Location**: `.github/scripts/validate-agent-registration.py`
- **Purpose**: Validates YAML frontmatter in all agent files
- **Checks**:
  - Frontmatter exists (between `---` markers)
  - Required fields are present: `name`, `description`, `tools`
  - Optional `version` field follows semver format if present
  - Tools field can be a list or comma-separated string
  - Agent name matches filename (warning only)

### 2. GitHub Actions Workflow
- **Location**: `.github/workflows/validate-agents.yml`
- **Triggers**: PRs and pushes that modify agent files
- **Runs**: Python validation script with verbose output
- **Fails**: CI if any agent files are invalid

### 3. Pre-commit Hook
- **Configuration**: In `.pre-commit-config.yaml`
- **Runs**: Before commits that modify agent files
- **Prevents**: Committing invalid agent files

## Usage

### Manual Validation

Run the validation script manually:

```bash
# Basic validation
python .github/scripts/validate-agent-registration.py

# Verbose mode for debugging
python .github/scripts/validate-agent-registration.py --verbose
```

### Pre-commit Setup

Install pre-commit hooks:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install

# Run manually on all files
pre-commit run validate-agents --all-files
```

## Valid Agent File Format

All agent files must have YAML frontmatter at the beginning:

```markdown
---
name: agent-name
description: Clear description of what the agent does
tools: Read, Write, Edit, Bash  # or ["Read", "Write", "Edit", "Bash"]
model: inherit  # optional but recommended
version: 1.0.0  # optional, must be semver if present
---

# Agent Name

Agent documentation content...
```

### Required Fields

- **name**: The agent's identifier (should match filename)
- **description**: Clear, concise description of the agent's purpose
- **tools**: List of tools the agent uses (comma-separated string or YAML list)

### Optional Fields

- **version**: Semantic version (e.g., 1.0.0, 2.1.3-beta)
- **model**: Model to use (typically "inherit")
- **imports**: Python imports for the agent

## Common Issues and Fixes

### Missing Frontmatter
**Error**: "Missing YAML frontmatter (should be between --- markers)"
**Fix**: Add frontmatter block at the very beginning of the file

### Missing Required Fields
**Error**: "Missing required field: 'description'"
**Fix**: Add the missing field to the frontmatter

### Invalid YAML Syntax
**Error**: "Invalid YAML syntax: ..."
**Fix**: Check for proper YAML formatting (indentation, quotes, etc.)

### Invalid Version Format
**Error**: "Invalid version format: '1.0' (expected semver like 1.0.0)"
**Fix**: Use proper semantic versioning: MAJOR.MINOR.PATCH

## CI/CD Integration

The validation runs automatically:

1. **On Pull Requests**: Validates changed agent files
2. **On Push to Main**: Ensures main branch stays valid
3. **Pre-commit**: Catches issues before commit

Failed validation will:
- Block PR merges
- Fail CI builds
- Prevent local commits (with pre-commit hooks)

## Troubleshooting

### Validation Passes Locally but Fails in CI
- Ensure you're testing with the same Python version
- Check for uncommitted changes
- Verify file encoding is UTF-8

### Pre-commit Hook Not Running
- Run `pre-commit install` to set up hooks
- Check `.git/hooks/pre-commit` exists
- Ensure Python is available in PATH

### False Positives
- Agent name warnings are informational only
- Version field is optional
- Tools can be string or list format

## Implementation Notes

This validation system addresses Issue #248: Agent registration failures due to missing or malformed YAML frontmatter. It provides early detection of registration issues before runtime, improving development velocity and reducing debugging time.

The validator is intentionally flexible:
- Accepts both string and list formats for tools
- Makes version field optional for backward compatibility
- Provides clear, actionable error messages
- Includes verbose mode for debugging

## Future Enhancements

Potential improvements for consideration:
- Auto-fix capability for common issues
- Validation of tool names against known tools
- Schema validation for complex frontmatter
- Integration with agent registration system
