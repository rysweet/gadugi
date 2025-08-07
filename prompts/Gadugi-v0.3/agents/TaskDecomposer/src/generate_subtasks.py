def generate_subtasks(task, strategy):
    """Generate subtasks using selected strategy"""

    subtasks = apply_decomposition_strategy(task, strategy)

    # Refine subtasks to meet quality criteria
    refined_subtasks = []
    for subtask in subtasks:
        if subtask.complexity_score() > MAX_SUBTASK_COMPLEXITY:
            # Recursively decompose complex subtasks
            nested_subtasks = generate_subtasks(subtask, strategy)
            refined_subtasks.extend(nested_subtasks)
        else:
            refined_subtasks.append(subtask)

    return refined_subtasks
