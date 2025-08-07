def generate_workflow_prompt(task):
    """Generate WorkflowManager prompt with UV context"""

    uv_context = ""
    if hasattr(task, 'is_uv_project') and task.is_uv_project:
        uv_context = """

        **UV PROJECT DETECTED**: This is a UV Python project.

        CRITICAL REQUIREMENTS:
        - UV environment is already set up
        - Use 'uv run' prefix for ALL Python commands
        - Examples: 'uv run pytest tests/', 'uv run python script.py'
        - NEVER run Python commands directly (will fail)
        """

    return f"""
    Execute workflow for task: {task.name}
    Worktree: {task.worktree_path}
    {uv_context}

    [Rest of prompt content...]
    """
