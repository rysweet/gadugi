def recover_from_partial_failure(pr_task_id):
    """Recover from partial processing failure"""
    saved_state = state_manager.load_state(pr_task_id)

    if saved_state.last_successful_phase >= 2:
        # Resume from issue resolution
        resume_from_phase_3(pr_task_id, saved_state)
    elif saved_state.last_successful_phase >= 1:
        # Resume from analysis
        resume_from_phase_2(pr_task_id, saved_state)
    else:
        # Restart from beginning
        restart_pr_evaluation(pr_task_id)
