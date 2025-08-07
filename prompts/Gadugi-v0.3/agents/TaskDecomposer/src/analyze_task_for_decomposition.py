def analyze_task_for_decomposition(task):
    analysis = {
        "complexity_drivers": identify_complexity_sources(task),
        "natural_boundaries": find_component_boundaries(task),
        "dependency_points": identify_dependency_points(task),
        "parallelization_opportunities": find_parallel_opportunities(task),
        "integration_challenges": assess_integration_complexity(task),
        "risk_factors": identify_risk_factors(task)
    }
    return analysis
