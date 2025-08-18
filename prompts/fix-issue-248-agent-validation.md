# Fix Issue #248: Add Agent Registration Validation to CI/CD

## Issue Summary
Tests are not validating agent registration before mocking, allowing broken agents to pass tests. Need automated validation of agent YAML frontmatter in CI/CD pipeline.

## Requirements

### 1. Create Validation Script
Create `.github/scripts/validate-agent-registration.py` that:
- Scans all files in `.claude/agents/` directory
- Validates YAML frontmatter structure
- Checks for required fields: name, type, tools
- Reports detailed errors for invalid agents
- Returns non-zero exit code on validation failure

### 2. Script Implementation Details
The validation script should:
- Parse YAML frontmatter between `---` markers
- Validate required fields are present and non-empty
- Check that 'tools' is a list if present
- Provide clear error messages showing which agent failed and why
- Support both individual file validation and directory scanning

### 3. GitHub Actions Integration
Add validation to CI/CD pipeline:
- Create or update `.github/workflows/validate-agents.yml`
- Run validation on every PR that touches agent files
- Run as part of main CI workflow
- Fail the build if any agent is invalid

### 4. Pre-commit Hook
Create local validation:
- Add pre-commit hook configuration for agent validation
- Update `.pre-commit-config.yaml` to include agent validator
- Provide instructions for developers to install pre-commit

## Implementation Details

### Validation Script Structure
```python
#!/usr/bin/env python3
# Should handle:
# - YAML parsing with proper error handling
# - Clear reporting of which agents fail
# - Exit codes: 0 for success, 1 for validation failure
# - Optional verbose mode for debugging
```

### Required YAML Structure
```yaml
---
name: agent-name
type: sub-agent  # or other valid types
tools:
  - Read
  - Write
  - Edit
---
```

## Files to Create/Modify
- Create: `.github/scripts/validate-agent-registration.py`
- Create/Update: `.github/workflows/validate-agents.yml`
- Update: `.pre-commit-config.yaml` (if exists) or create with validation hook

## Success Criteria
- Script successfully validates all existing valid agents
- Script catches agents missing required fields
- CI/CD fails when invalid agents are submitted
- Pre-commit hook prevents committing invalid agents locally
- Clear error messages help developers fix issues quickly

## Testing Requirements
- Test script with valid agent files (should pass)
- Test with agent missing 'name' field (should fail)
- Test with agent missing 'type' field (should fail)
- Test with agent missing frontmatter entirely (should fail)
- Verify GitHub Actions workflow triggers on agent file changes
- Confirm pre-commit hook works locally
