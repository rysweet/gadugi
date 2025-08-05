# Test Workflow Execution

This document demonstrates how WorkflowManager would execute a workflow.

## Example Prompt: Simple Feature Addition

Given a prompt file `/prompts/AddLoggingFeature.md`, WorkflowManager would:

### 1. Parse the Prompt
Extract:
- Feature: Add structured logging to Gadugi
- Requirements: Use Python logging module, JSON format
- Success criteria: All modules use consistent logging

### 2. Create Task List
```python
tasks = [
    {"id": "1", "content": "Create GitHub issue for logging feature", "status": "pending", "priority": "high"},
    {"id": "2", "content": "Create feature branch", "status": "pending", "priority": "high"},
    {"id": "3", "content": "Research current logging usage", "status": "pending", "priority": "high"},
    {"id": "4", "content": "Implement logging configuration", "status": "pending", "priority": "high"},
    {"id": "5", "content": "Add logging to core modules", "status": "pending", "priority": "high"},
    {"id": "6", "content": "Write tests for logging", "status": "pending", "priority": "high"},
    {"id": "7", "content": "Update documentation", "status": "pending", "priority": "medium"},
    {"id": "8", "content": "Create pull request", "status": "pending", "priority": "high"},
    {"id": "9", "content": "Complete code review", "status": "pending", "priority": "high"}
]
```

### 3. Execute Each Phase

#### Issue Creation
```bash
gh issue create --title "feat: add structured logging to Gadugi" \
  --body "Add JSON-formatted structured logging using Python logging module..."
# Returns: Issue #22 created
```

#### Branch Creation
```bash
git checkout -b feature/add-logging-22
```

#### Research Phase
- Use Grep to find existing logging
- Read relevant modules
- Update Memory.md with findings

#### Implementation
- Create logging configuration
- Add to each module systematically
- Make focused commits

#### Testing
- Write unit tests for logging
- Test JSON format output
- Verify all modules included

#### Documentation
- Update README with logging configuration
- Add docstrings
- Document log levels

#### Pull Request
```bash
gh pr create --title "feat: add structured logging" \
  --body "Implements structured JSON logging across all modules..."
```

#### Review
```
/agent:code-reviewer
```

### 4. Track Progress
Throughout execution, update task status:
- pending → in_progress → completed
- Handle any errors that arise
- Save state if interrupted

## Verification

WorkflowManager ensures:
- ✅ All phases completed
- ✅ Clean git history
- ✅ Comprehensive PR
- ✅ Tests passing
- ✅ Documentation updated
- ✅ Review completed
