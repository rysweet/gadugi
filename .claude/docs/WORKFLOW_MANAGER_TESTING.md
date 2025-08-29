# WorkflowManager Integration Testing Guide

## Overview

This guide provides instructions for creating integration tests for the WorkflowManager sub-agent to ensure reliable workflow execution.

## Test Structure

### 1. Test Prompt Creation

Create a minimal test prompt file for validation:

```markdown
# Test Feature Implementation Prompt

## Overview
Test feature for WorkflowManager integration testing.

## Problem Statement
We need to verify WorkflowManager can execute all workflow phases correctly.

## Requirements
- Create a simple test file
- Add basic functionality
- Include documentation

## Technical Analysis
This is a minimal implementation for testing purposes.

## Implementation Plan
1. Create test file
2. Add test function
3. Write unit test
4. Update documentation

## Testing Requirements
- Unit test for the test function
- Verify function works correctly

## Success Criteria
- All workflow phases complete successfully
- Test file is created and functional
- Documentation is updated

## Implementation Steps
1. Create issue for test feature
2. Create feature branch
3. Implement test file
4. Write tests
5. Create PR
6. Complete review
```

### 2. Integration Test Script

```python
# test_workflow_master_integration.py
import subprocess
import time
import os

class TestWorkflowManagerIntegration:
    """Integration tests for WorkflowManager sub-agent."""

    def setup_method(self):
        """Set up test environment."""
        self.test_prompt = "test_feature.md"
        self.test_branch = None
        self.test_issue = None

    def teardown_method(self):
        """Clean up test artifacts."""
        # Clean up test branch if created
        if self.test_branch:
            subprocess.run(["git", "checkout", "main"])
            subprocess.run(["git", "branch", "-D", self.test_branch])

    def test_workflow_execution(self):
        """Test complete workflow execution."""
        # 1. Create test prompt
        self._create_test_prompt()

        # 2. Invoke WorkflowManager
        # Note: This would be done through Claude Code
        # For testing, we verify each phase manually

        # 3. Verify issue creation
        assert self._verify_issue_created()

        # 4. Verify branch creation
        assert self._verify_branch_created()

        # 5. Verify implementation
        assert self._verify_files_created()

        # 6. Verify tests
        assert self._verify_tests_created()

        # 7. Verify PR creation
        assert self._verify_pr_created()

    def test_prompt_validation(self):
        """Test prompt validation mechanism."""
        # Create invalid prompt (missing sections)
        invalid_prompt = """
        # Invalid Prompt
        This prompt is missing required sections.
        """

        # Verify WorkflowManager detects invalid prompt
        # and invokes PromptWriter

    def test_task_structure_validation(self):
        """Test TodoWrite task structure validation."""
        # Test with invalid task structure
        invalid_tasks = [
            {"content": "Missing required fields"},
            {"id": "1", "status": "pending"},  # Missing content and priority
        ]

        # Verify validation catches these issues
```

### 3. Workflow Phase Validation

Each workflow phase should be tested:

```python
def _verify_issue_created(self):
    """Verify GitHub issue was created correctly."""
    # Check for issue with expected title
    result = subprocess.run(
        ["gh", "issue", "list", "--search", "Test Feature"],
        capture_output=True,
        text=True
    )
    return "Test Feature" in result.stdout

def _verify_branch_created(self):
    """Verify feature branch was created."""
    result = subprocess.run(
        ["git", "branch", "--list"],
        capture_output=True,
        text=True
    )
    branches = result.stdout
    # Look for feature/test-feature-N branch
    return any("feature/test-feature" in line for line in branches.split("\n"))

def _verify_files_created(self):
    """Verify implementation files were created."""
    # Check for expected files
    expected_files = [
        "test_feature.py",
        "tests/test_test_feature.py",
        "docs/test_feature.md"
    ]
    return all(os.path.exists(f) for f in expected_files)
```

## Running Integration Tests

### Manual Testing

1. Create test prompt file
2. Invoke WorkflowManager:
   ```
   /agent:WorkflowManager
   Execute workflow from: /prompts/test_feature.md
   ```
3. Monitor execution and verify each phase
4. Check final deliverables

### Automated Testing

Run the integration test suite:
```bash
pytest test_workflow_master_integration.py -v
```

## Test Scenarios

### 1. Happy Path
- Valid prompt file
- All phases execute successfully
- PR created and reviewed

### 2. Invalid Prompt
- Missing required sections
- WorkflowManager invokes PromptWriter
- New prompt created and workflow continues

### 3. Task Validation
- Invalid task structure
- Validation catches error
- Proper error message provided

### 4. Error Recovery
- Git conflict during branch creation
- Test failure during execution
- CI/CD pipeline failure

## Success Metrics

Integration tests should verify:
- ✅ All workflow phases execute in order
- ✅ Proper error handling for common failures
- ✅ Task structure validation works correctly
- ✅ Prompt validation triggers PromptWriter when needed
- ✅ State management allows resumption after interruption
- ✅ Final deliverables meet quality standards

## Continuous Improvement

After each test run:
1. Document any issues found
2. Update WorkflowManager to handle edge cases
3. Add new test scenarios as discovered
4. Improve error messages and recovery mechanisms
