# Enhanced task initialization with shared modules
def initialize_workflow_task(task_id=None, prompt_file=None):
    # Generate unique task ID with enhanced tracking
    if not task_id:
        task_id = f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"

    # Initialize productivity tracking
    productivity_analyzer.start_workflow_tracking(task_id, prompt_file)

    # Check for existing state with enhanced state management
    existing_state = state_manager.load_state(task_id)
    if existing_state:
        print(f"Found interrupted workflow for task {task_id}")

        # Validate state consistency
        if state_manager.validate_state_consistency(existing_state):
            # Offer resumption options with recovery context
            recovery_options = generate_recovery_options(existing_state)
            offer_resumption_choice(recovery_options)
        else:
            print("State inconsistency detected, initiating recovery...")
            recovery_manager.initiate_state_recovery(task_id)

    # Check for any orphaned workflows with advanced detection
    orphaned_workflows = state_manager.detect_orphaned_workflows()
    if orphaned_workflows:
        print("Found interrupted workflows:")
        for workflow in orphaned_workflows:
            print(f"- {workflow.task_id}: {workflow.description} (Phase: {workflow.current_phase})")

    # Initialize comprehensive workflow state
    workflow_state = WorkflowState(
        task_id=task_id,
        prompt_file=prompt_file,
        phase=WorkflowPhase.INITIALIZATION,
        started_at=datetime.now(),
        state_directory=f".github/workflow-states/{task_id}"
    )

    # Create initial checkpoint with backup
    checkpoint_manager = CheckpointManager(state_manager)
    checkpoint_manager.create_checkpoint(workflow_state)

    # Initialize backup system
    backup_restore = StateBackupRestore(state_manager)
    backup_restore.create_backup(task_id)

    return workflow_state
