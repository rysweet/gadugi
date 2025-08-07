def requires_decomposition(task):
    indicators = [
        task.estimated_duration() > timedelta(days=3),
        task.touches_multiple_systems(),
        task.has_multiple_stakeholders(),
        task.has_parallel_work_opportunities(),
        task.complexity_score() > HIGH_COMPLEXITY_THRESHOLD,
        task.has_research_components(),
        task.has_multiple_acceptance_criteria()
    ]
    return sum(indicators) >= 3  # Threshold for decomposition needed
