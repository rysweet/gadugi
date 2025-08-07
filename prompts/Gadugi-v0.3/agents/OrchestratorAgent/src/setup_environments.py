def setup_environments(task_data):
    # Create orchestration state checkpoint
    orchestration_state = WorkflowState(
        task_id=f"orchestration-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        phase=WorkflowPhase.ENVIRONMENT_SETUP,
        tasks=task_data.tasks
    )

    # Save state with backup
    state_manager.save_state(orchestration_state)
    backup_manager = StateBackupRestore(state_manager)
    backup_manager.create_backup(orchestration_state.task_id)

    # CRITICAL: Setup worktrees for ALL tasks - this is MANDATORY
    # The orchestrator MUST ALWAYS use worktree-manager for isolation
    for task in task_data.tasks:
        try:
            # ALWAYS invoke worktree manager - no exceptions
            worktree_result = invoke_worktree_manager(task)

            # UV Project Detection and Setup
            worktree_path = worktree_result.path
            if is_uv_project(worktree_path):
                log_info(f"UV project detected in {worktree_path} - setting up UV environment")
                if not setup_uv_environment_for_task(task, worktree_path):
                    raise Exception(f"Failed to set up UV environment for task {task.id}")
                task.is_uv_project = True
            else:
                task.is_uv_project = False

            task_tracker.update_task_status(task.id, "worktree_ready")
        except Exception as e:
            error_handler.handle_error(ErrorContext(
                error=e,
                task_id=task.id,
                phase="environment_setup",
                recovery_action="retry_worktree_creation"
            ))
