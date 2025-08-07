def requires_research(task):
    indicators = [
        task.involves_new_technology(),
        task.has_unclear_feasibility(),
        task.needs_architectural_decisions(),
        task.has_performance_unknowns(),
        task.involves_third_party_integration(),
        task.has_security_implications(),
        task.needs_competitive_analysis()
    ]
    return sum(indicators) >= 2  # Threshold for research needed
