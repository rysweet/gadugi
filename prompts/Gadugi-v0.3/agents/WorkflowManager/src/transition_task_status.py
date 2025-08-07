# Enhanced status transitions with validation
def transition_task_status(task_id, new_status):
    # Validate transition is allowed
    current_task = task_tracker.get_task(task_id)
    if not task_tracker.is_valid_transition(current_task.status, new_status):
        raise TaskTransitionError(f"Invalid transition: {current_task.status} -> {new_status}")

    # Check dependencies for in_progress transitions
    if new_status == "in_progress":
        unmet_dependencies = task_tracker.check_dependencies(task_id)
        if unmet_dependencies:
            raise DependencyError(f"Unmet dependencies: {unmet_dependencies}")

    # Ensure only one task is in_progress
    if new_status == "in_progress":
        active_tasks = task_tracker.get_active_tasks()
        if active_tasks:
            raise ConcurrencyError(f"Task {active_tasks[0].id} is already in progress")

    # Update with enhanced tracking
    update_task_progress(task_id, new_status)
