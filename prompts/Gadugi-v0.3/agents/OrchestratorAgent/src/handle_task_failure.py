# Comprehensive error context tracking
def handle_task_failure(task_id, error):
    error_context = ErrorContext(
        error=error,
        task_id=task_id,
        phase="parallel_execution",
        system_state=get_system_state(),
        recovery_suggestions=generate_recovery_plan(error)
    )

    # Isolate failure with shared error handling
    error_handler.handle_error(error_context)

    # Clean up with state preservation
    cleanup_failed_task(task_id, preserve_state=True)

    # Continue with remaining tasks
    continue_with_healthy_tasks()
