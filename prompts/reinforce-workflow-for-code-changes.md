# Reinforce Workflow for Code Changes

## Objective
Create and enforce a strict workflow mechanism that ensures all code changes go through the proper orchestrator and WorkflowManager agents with full 11-phase workflow.

## Priority
CRITICAL

## Context
Code changes MUST follow the proper workflow to maintain code quality, ensure proper testing, and preserve git history. This task will create enforcement mechanisms to prevent bypassing the orchestrator.

## Tasks

### 1. Create Workflow Enforcement Documentation
Create `.claude/workflow-enforcement.md` with:
- Clear explanation of mandatory workflow for code changes
- Decision tree for when to use orchestrator vs direct execution
- Examples of violations and correct approaches
- Consequences of bypassing workflow

### 2. Update CLAUDE.md with Strict Requirements
Enhance CLAUDE.md to include:
- **CRITICAL** section on workflow enforcement
- Clear distinction between code changes and informational queries
- Mandatory use of orchestrator for ANY file modifications
- Examples of what constitutes a "code change"

### 3. Create Pre-Execution Validation Script
Develop `.claude/scripts/validate-workflow.py`:
```python
def validate_execution_method(task_type, files_to_modify):
    """
    Validates that the correct execution method is being used.
    Returns: (is_valid, error_message, suggested_method)
    """
    if task_type == "code_change" and files_to_modify:
        if not using_orchestrator():
            return False, "Code changes must use orchestrator", "OrchestratorAgent"
    return True, None, None
```

### 4. Implement Workflow Hooks
Create hooks that intercept execution attempts:
- `.claude/hooks/pre-execution-hook.py`
- Detects when files will be modified
- Warns if orchestrator is not being used
- Optionally blocks direct execution

### 5. Create Workflow Validation Checklist
Develop `.claude/workflow-validation.md`:
- [ ] Is this a code change? → Use orchestrator
- [ ] Will files be modified? → Use orchestrator  
- [ ] Is this adding functionality? → Use orchestrator
- [ ] Is this fixing bugs? → Use orchestrator
- [ ] Is this only reading/analyzing? → Direct execution OK
- [ ] Is this only answering questions? → Direct execution OK

### 6. Add Enforcement to Agent Instructions
Update all agent markdown files to include:
```markdown
## CRITICAL: Workflow Enforcement
This agent MUST be invoked through the orchestrator for any code changes.
Direct invocation is ONLY permitted for read-only operations.
```

### 7. Create Workflow Compliance Report
Implement `.claude/scripts/workflow-compliance.py`:
- Tracks all executions and their methods
- Identifies potential workflow violations
- Generates compliance reports
- Suggests corrections for violations

### 8. Implement Graceful Enforcement
Rather than hard blocking, implement:
- Warning messages for first violation
- Escalating warnings for repeated violations
- Automatic redirection to orchestrator when appropriate
- Educational messages explaining why workflow matters

### 9. Create Emergency Override Mechanism
For rare cases where direct execution is justified:
- Require explicit override flag
- Log the override with justification
- Send notification about override usage
- Review overrides periodically

### 10. Add Workflow Status Indicators
Create visual/text indicators showing:
- Current execution method (orchestrator/direct)
- Workflow phase if using orchestrator
- Compliance status
- Warnings if in violation

## Implementation Requirements

### Files to Create
- `.claude/workflow-enforcement.md`
- `.claude/scripts/validate-workflow.py`
- `.claude/hooks/pre-execution-hook.py`
- `.claude/workflow-validation.md`
- `.claude/scripts/workflow-compliance.py`

### Files to Update
- `CLAUDE.md` - Add strict workflow requirements
- All agent files in `.claude/agents/` - Add enforcement notices
- `.claude/Guidelines.md` - Include workflow guidelines
- `.claude/instructions/orchestration.md` - Enhance with enforcement

## Success Criteria
- Workflow enforcement mechanism is active
- All code changes go through orchestrator
- Clear documentation exists for workflow requirements
- Validation scripts prevent accidental violations
- Compliance can be monitored and reported
- Emergency overrides are logged and justified

## Testing Plan
1. Attempt direct file modification → Should trigger warning
2. Use orchestrator for code change → Should proceed normally
3. Direct execution for analysis → Should be allowed
4. Test emergency override → Should work with logging
5. Run compliance report → Should show all executions

## Notes
- Balance enforcement with usability
- Focus on education over punishment
- Make the right path the easy path
- Provide clear guidance when violations detected