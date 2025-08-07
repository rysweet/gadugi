# Enhanced task evaluation with shared modules integration
@error_handler.with_circuit_breaker(analysis_circuit_breaker)
def analyze_task(prompt_file):
    # Initialize task analysis tracking
    task_tracker.start_task_analysis(prompt_file)

    # Step 1: Parse prompt file content
    task_metadata = extract_enhanced_metadata(prompt_file)

    # Step 2: Evaluate task bounds and complexity
    bounds_eval_result = invoke_task_bounds_eval(task_metadata)

    # Step 3: Determine if decomposition is needed
    if bounds_eval_result.requires_decomposition:
        decomposition_result = invoke_task_decomposer(task_metadata)
        task_metadata.subtasks = decomposition_result.subtasks

    # Step 4: Check if research is required
    if bounds_eval_result.requires_research:
        research_result = invoke_task_research_agent(task_metadata)
        task_metadata.research_findings = research_result

    return enhanced_task_analysis(task_metadata)
