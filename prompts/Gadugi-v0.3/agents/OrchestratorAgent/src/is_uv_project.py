def is_uv_project(worktree_path):
    """Check if worktree contains a UV project"""
    return (Path(worktree_path) / "pyproject.toml").exists() and \
           (Path(worktree_path) / "uv.lock").exists()
