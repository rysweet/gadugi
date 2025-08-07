# Handle synchronization conflicts
conflict_resolution = {
    "task_modified_both_places": "prompt_user_choice",
    "task_completed_memory_open_github": "close_github_issue",
    "task_reopened_github_completed_memory": "reopen_memory_task",
    "content_diverged": "merge_with_manual_review"
}
