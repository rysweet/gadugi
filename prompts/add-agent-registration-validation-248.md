# Add Agent Registration Validation to CI/CD (Issue #248)

## Context
Agent registration failures are not being caught early enough in the development process. Missing or malformed YAML frontmatter in agent files prevents proper registration, but this is only discovered at runtime. We need proactive validation in CI/CD.

## Requirements

### Primary Task
Create a comprehensive agent registration validation system that runs in CI/CD and pre-commit hooks.

### Specific Implementation Required

1. **Create validation script** `.github/scripts/validate-agent-registration.py`:
   - Parse all agent files in `.claude/agents/` and `.github/agents/`
   - Validate YAML frontmatter structure
   - Check for required fields (name, description, version, tools)
   - Verify YAML syntax is valid
   - Ensure agent names match filenames
   - Return non-zero exit code on any validation failure

2. **Validation checks to implement**:
   ```python
   # Required frontmatter structure
   ---
   name: agent-name
   description: Agent description
   version: 1.0.0
   tools:
     - ToolName
   ---
   ```
   - Frontmatter must exist (between --- markers)
   - 'name' field is required and non-empty
   - 'description' field is required and non-empty
   - 'version' field is required and valid semver
   - 'tools' field is required (can be empty list)
   - YAML must be valid (parseable)
   - Agent name should match filename (without .md)

3. **Add to GitHub Actions** workflow:
   - Create or update `.github/workflows/validate-agents.yml`
   - Run on all PRs and pushes to main
   - Run the validation script
   - Fail the workflow if validation fails
   - Provide clear error messages about what failed

4. **Add to pre-commit hooks**:
   - Update `.pre-commit-config.yaml`
   - Add local hook that runs the validation script
   - Ensure it runs before commits that modify agent files

5. **Error reporting**:
   - Clear, actionable error messages
   - Show file path and line number of issues
   - Suggest fixes for common problems
   - Support verbose mode for debugging

## Script Structure

```python
#!/usr/bin/env python3
"""Validate agent registration files for proper YAML frontmatter."""

import sys
import yaml
from pathlib import Path
import re

def validate_agent_file(filepath):
    """Validate a single agent file."""
    # Implementation here
    pass

def main():
    """Main validation entry point."""
    # Find all agent files
    # Validate each one
    # Report results
    # Exit with appropriate code
    pass

if __name__ == "__main__":
    sys.exit(main())
```

## Validation Criteria

- [ ] Validation script created and executable
- [ ] All current agent files pass validation
- [ ] GitHub Actions workflow created/updated
- [ ] Pre-commit hook configured
- [ ] Clear error messages for failures
- [ ] Documentation added for using the validator

## Testing Requirements

- Test with valid agent files (should pass)
- Test with missing frontmatter (should fail)
- Test with invalid YAML (should fail)
- Test with missing required fields (should fail)
- Test with mismatched names (should warn or fail)
- Verify GitHub Actions integration works
- Verify pre-commit hook blocks bad commits

## References

- Issue #248: Implement agent registration validator
- Memory.md: Team Coach insights about registration failures
- Existing agent file format in `.claude/agents/`
