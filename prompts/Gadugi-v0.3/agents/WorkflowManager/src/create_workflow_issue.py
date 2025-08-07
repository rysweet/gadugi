# Issue creation with shared modules and error handling
@error_handler.with_circuit_breaker(github_circuit_breaker)
def create_workflow_issue(workflow_state, prompt_data):
    # Track phase start
    phase_tracker.start_phase(WorkflowPhase.ISSUE_CREATION)
    productivity_analyzer.record_phase_start("issue_creation")

    # Prepare comprehensive issue data
    issue_data = IssueData(
        title=f"{prompt_data.feature_name} - {workflow_state.task_id}",
        body=format_issue_body(prompt_data),
        labels=["enhancement", "ai-generated"],
        assignees=[]
    )

    # Create issue with retry logic
    issue_result = retry_manager.execute_with_retry(
        lambda: github_manager.create_issue(issue_data),
        max_attempts=3,
        backoff_strategy="exponential"
    )

    if issue_result.success:
        # Update workflow state
        workflow_state.issue_number = issue_result.issue_number
        workflow_state.issue_url = issue_result.issue_url

        # Create checkpoint after successful issue creation
        checkpoint_manager.create_checkpoint(workflow_state)

        # Track phase completion
        phase_tracker.complete_phase(WorkflowPhase.ISSUE_CREATION)
        productivity_analyzer.record_phase_completion("issue_creation")

        print(f"✅ Created issue #{issue_result.issue_number}: {issue_result.issue_url}")
        return issue_result
    else:
        # Handle failure with error context
        error_context = ErrorContext(
            error=issue_result.error,
            task_id=workflow_state.task_id,
            phase="issue_creation",
            recovery_action="retry_issue_creation"
        )
        error_handler.handle_error(error_context)
        raise WorkflowError(f"Failed to create issue: {issue_result.error}")
