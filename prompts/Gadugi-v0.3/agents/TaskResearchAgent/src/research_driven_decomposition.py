def research_driven_decomposition(research_results):
    """Use research findings to inform task decomposition"""

    if research_results.feasibility == "TECHNICALLY_FEASIBLE":
        if research_results.complexity == "HIGH":
            # Decompose into research + implementation phases
            return [
                create_research_task(research_results),
                create_prototype_task(research_results),
                create_implementation_task(research_results),
                create_validation_task(research_results)
            ]
        else:
            # Direct implementation with research insights
            return [
                create_implementation_task_with_research(research_results)
            ]
    else:
        # Research alternative approaches
        return [
            create_alternative_research_task(research_results),
            create_fallback_implementation_task(research_results)
        ]
