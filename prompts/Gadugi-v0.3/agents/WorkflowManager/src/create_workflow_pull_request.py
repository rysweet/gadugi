# PR creation with shared modules and comprehensive error handling
@error_handler.with_circuit_breaker(github_circuit_breaker)
def create_workflow_pull_request(workflow_state, implementation_summary):
    # Track phase start
    phase_tracker.start_phase(WorkflowPhase.PULL_REQUEST_CREATION)
    productivity_analyzer.record_phase_start("pr_creation")

    # Prepare comprehensive PR data
    pr_data = PullRequestData(
        title=f"{implementation_summary.feature_name} - Implementation",
        body=format_pr_body(workflow_state, implementation_summary),
        head=workflow_state.branch_name,
        base="main",
        draft=False,
        labels=["enhancement", "ai-generated"]
    )

    # Create PR with retry logic and atomic state updates
    try:
        pr_result = retry_manager.execute_with_retry(
            lambda: github_manager.create_pull_request(pr_data),
            max_attempts=3,
            backoff_strategy="exponential"
        )

        if pr_result.success:
            # Atomic state update - both must succeed
            workflow_state.pr_number = pr_result.pr_number
            workflow_state.pr_url = pr_result.pr_url
            workflow_state.phase = WorkflowPhase.PULL_REQUEST_CREATED

            # Verify PR actually exists before marking complete
            verification_result = github_manager.verify_pull_request_exists(pr_result.pr_number)
            if not verification_result.exists:
                raise WorkflowError(f"PR {pr_result.pr_number} was created but cannot be verified")

            # Create critical checkpoint after PR creation
            checkpoint_manager.create_checkpoint(workflow_state)

            # Track successful completion
            phase_tracker.complete_phase(WorkflowPhase.PULL_REQUEST_CREATION)
            productivity_analyzer.record_phase_completion("pr_creation")

            print(f"✅ Created PR #{pr_result.pr_number}: {pr_result.pr_url}")
            return pr_result

        else:
            raise WorkflowError(f"Failed to create PR: {pr_result.error}")

    except Exception as e:
        # Comprehensive error handling with recovery context
        error_context = ErrorContext(
            error=e,
            task_id=workflow_state.task_id,
            phase="pull_request_creation",
            system_state={
                "branch": workflow_state.branch_name,
                "issue": workflow_state.issue_number,
                "commits": get_commit_count(workflow_state.branch_name)
            },
            recovery_action="retry_pr_creation_with_verification"
        )

        error_handler.handle_error(error_context)

        # Mark phase as failed but preserve state for recovery
        phase_tracker.mark_phase_failed(WorkflowPhase.PULL_REQUEST_CREATION, str(e))
        raise WorkflowError(f"CRITICAL: Failed to create PR for task {workflow_state.task_id}: {e}")
