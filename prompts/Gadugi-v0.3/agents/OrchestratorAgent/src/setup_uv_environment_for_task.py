def setup_uv_environment_for_task(task, worktree_path):
    """Set up UV environment for a specific task worktree"""
    try:
        # Use shared UV setup script
        setup_script = Path(".claude/scripts/setup-uv-env.sh")
        if not setup_script.exists():
            log_error("UV setup script not found")
            return False

        # Run UV setup
        result = subprocess.run([
            "bash", str(setup_script), "setup", worktree_path, "--all-extras"
        ], capture_output=True, text=True, check=True)

        log_info(f"UV environment setup completed for task {task.id}")
        return True

    except subprocess.CalledProcessError as e:
        log_error(f"UV setup failed for task {task.id}: {e.stderr}")
        return False
