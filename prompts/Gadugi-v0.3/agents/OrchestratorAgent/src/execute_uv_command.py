def execute_uv_command(worktree_path, command_args):
    """Execute command in UV environment"""
    uv_cmd = ["uv", "run"] + command_args

    result = subprocess.run(
        uv_cmd,
        cwd=worktree_path,
        capture_output=True,
        text=True
    )

    return result.returncode == 0, result.stdout, result.stderr
