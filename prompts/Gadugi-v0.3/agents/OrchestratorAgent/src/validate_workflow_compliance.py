def validate_workflow_compliance(task):
    """Ensure task will be executed through proper WorkflowManager workflow"""

    # Check 1: Verify WorkflowManager will be used
    if not task.uses_workflow_manager:
        raise InvalidExecutionMethodError(task.id)

    # Check 2: Verify complete workflow phases will be followed
    required_phases = ['setup', 'issue_creation', 'branch_creation', 'implementation',
                      'testing', 'documentation', 'pr_creation', 'review']
    missing_phases = [phase for phase in required_phases if phase not in task.planned_phases]
    if missing_phases:
        raise IncompleteWorkflowError(task.id, missing_phases)

    # Check 3: Verify no direct execution bypass
    if task.execution_method in ['direct', 'claude_-p', 'shell_script']:
        raise DirectExecutionError(task.id, task.execution_method)

    return True
