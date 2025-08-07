def assess_well_bounded(task):
    indicators = [
        task.has_specific_acceptance_criteria(),
        task.has_clear_input_output_spec(),
        task.dependencies_are_known(),
        task.has_similar_examples(),
        task.technology_stack_is_familiar(),
        task.estimated_effort_is_confident(),
        task.success_metrics_are_defined()
    ]
    return sum(indicators) >= 5  # Threshold for well-bounded
