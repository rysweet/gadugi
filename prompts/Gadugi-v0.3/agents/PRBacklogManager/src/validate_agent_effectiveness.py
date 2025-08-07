def validate_agent_effectiveness():
    """Comprehensive validation of agent performance"""
    recent_prs = github_ops.get_recent_processed_prs(days=30)

    metrics = {
        'accuracy': calculate_labeling_accuracy(recent_prs),
        'speed': calculate_average_processing_time(recent_prs),
        'automation_rate': calculate_automation_success_rate(recent_prs),
        'merge_success': calculate_merge_success_rate(recent_prs)
    }

    return ValidationResult(
        meets_sla=all(metric >= threshold for metric, threshold in SLA_THRESHOLDS.items()),
        improvement_areas=identify_improvement_opportunities(metrics),
        recommendations=generate_optimization_recommendations(metrics)
    )
