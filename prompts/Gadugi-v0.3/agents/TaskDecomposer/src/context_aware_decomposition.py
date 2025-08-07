def context_aware_decomposition(task, context):
    """Adjust decomposition based on project context"""

    if context.team_size == "SMALL":
        # Fewer, larger subtasks for small teams
        return coarse_grained_decomposition(task)
    elif context.team_size == "LARGE":
        # More, smaller subtasks for large teams
        return fine_grained_decomposition(task)

    if context.timeline == "URGENT":
        # Focus on parallel execution
        return parallel_optimized_decomposition(task)
    elif context.timeline == "FLEXIBLE":
        # Focus on quality and maintainability
        return quality_optimized_decomposition(task)
