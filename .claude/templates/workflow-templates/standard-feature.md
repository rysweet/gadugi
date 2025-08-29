# Standard Feature Workflow Template

This template demonstrates the standard workflow execution pattern for WorkflowManager.

## Phase 1: Issue Creation

```bash
gh issue create --title "feat: [feature description]" --body "$(cat <<'EOF'
## Overview
[Feature overview]

## Requirements
[Technical and functional requirements]

## Implementation Plan
[Step-by-step plan]

## Success Criteria
[Measurable outcomes]
EOF
)"
```

## Phase 2: Branch Creation

```bash
# Assuming issue #N was created
git checkout -b feature/[feature-name]-N
```

## Phase 3: Research and Planning

1. Analyze affected modules:
   ```bash
   grep -r "relevant_term" --include="*.py" .
   ls -la relevant/directory/
   ```

2. Read key files:
   ```
   Read relevant/module.py
   ```

3. Update Memory.md with findings

## Phase 4: Implementation

Break into focused commits:
1. First component
2. Second component
3. Integration
4. Edge cases

## Phase 5: Testing

```python
# Create comprehensive test file
# tests/test_feature.py
import unittest
from unittest.mock import Mock, patch

class TestFeature(unittest.TestCase):
    def setUp(self):
        # Test setup
        pass

    def test_happy_path(self):
        # Normal operation
        pass

    def test_edge_cases(self):
        # Boundary conditions
        pass

    def test_error_handling(self):
        # Error scenarios
        pass
```

## Phase 6: Documentation

- Update README.md if needed
- Add docstrings to all functions
- Update API documentation
- Add inline comments for complex logic

## Phase 7: Pull Request

```bash
gh pr create --base main --title "feat: [feature description]" --body "$(cat <<'EOF'
## Summary
[What this PR does]

## Changes
- [Change 1]
- [Change 2]

## Testing
- [Test coverage added]
- [Manual testing performed]

## Related Issues
Fixes #N

*Note: This PR was created by an AI agent on behalf of the repository owner.*

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"
```

## Phase 8: Review

```
/agent:CodeReviewer
```

Then address any feedback and ensure CI passes.
