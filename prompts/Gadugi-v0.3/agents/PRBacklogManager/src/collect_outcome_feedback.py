def collect_outcome_feedback(pr_number, final_outcome):
    """Collect feedback on PR processing outcomes"""
    if final_outcome == 'merged_successfully':
        # Positive feedback - strategies worked
        record_successful_strategy(pr_number)
    elif final_outcome == 'merge_failed':
        # Negative feedback - analyze what went wrong
        analyze_failure_causes(pr_number)
        update_resolution_strategies()
