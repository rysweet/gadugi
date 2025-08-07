# Enhanced task analysis with Task Decomposition Analyzer integration
@error_handler.with_circuit_breaker(github_circuit_breaker)
def analyze_tasks_enhanced(prompt_files):
    # Initialize enhanced analysis tracking
    performance_analyzer.record_phase_start("enhanced_task_analysis")
    task_tracker.update_phase(WorkflowPhase.ANALYSIS, "in_progress")

    # Step 1: Initial task analysis with enhanced capabilities
    analysis_result = retry_manager.execute_with_retry(
        lambda: invoke_enhanced_task_analyzer(prompt_files, {
            'enable_decomposition': True,
            'ml_classification': True,
            'pattern_recognition': True,
            'historical_analysis': True
        }),
        max_attempts=3,
        backoff_strategy="exponential"
    )

    # Step 2: Process decomposition results
    enhanced_tasks = []
    for task in analysis_result.tasks:
        if task.requires_decomposition:
            # Task was automatically decomposed by TaskDecomposer
            enhanced_tasks.extend(task.subtasks)
            performance_analyzer.record_decomposition_benefit(
                task.id, task.decomposition_benefit
            )
        else:
            enhanced_tasks.append(task)

    # Step 3: Apply ML-based optimizations
    ml_optimizations = apply_ml_optimizations(enhanced_tasks)
    for task in enhanced_tasks:
        task.apply_optimizations(ml_optimizations.get(task.id, []))

    # Step 4: Pre-validate all tasks for governance compliance
    for task in enhanced_tasks:
        try:
            validate_workflow_compliance(task)
            task.governance_validated = True
        except WorkflowComplianceError as e:
            error_handler.log_error(f"Task {task.id} failed governance validation: {e}")
            task.governance_validated = False
            task.compliance_errors = str(e)

    # Step 5: Update execution plan with enhanced insights and validated tasks
    enhanced_execution_plan = generate_enhanced_execution_plan(
        enhanced_tasks,
        analysis_result.dependency_graph,
        analysis_result.performance_predictions
    )

    # Track enhanced analysis completion
    performance_analyzer.record_phase_completion("enhanced_task_analysis", {
        'original_task_count': len(prompt_files),
        'enhanced_task_count': len(enhanced_tasks),
        'decomposition_applied': sum(1 for t in analysis_result.tasks if t.requires_decomposition),
        'research_required': sum(1 for t in analysis_result.tasks if t.requires_research),
        'ml_classifications': len([t for t in enhanced_tasks if hasattr(t, 'ml_classification')])
    })

    return enhanced_execution_plan

def invoke_enhanced_task_analyzer(prompt_files, config):
    """Invoke task analyzer with enhanced decomposition capabilities"""
    # The enhanced task-analyzer now automatically coordinates with:
    # - TaskBoundsEval for complexity assessment
    # - TaskDecomposer for intelligent decomposition
    # - TaskResearchAgent for research requirements
    # - ML classification for pattern recognition

    analyzer_prompt = f"""
    /agent:task-analyzer

    Perform enhanced analysis with Task Decomposition Analyzer integration:
    Prompt files: {', '.join(prompt_files)}

    Enhanced Configuration:
    - Task Decomposition Analyzer integration: {config['enable_decomposition']}
    - Machine learning classification: {config['ml_classification']}
    - Pattern recognition system: {config['pattern_recognition']}
    - Historical analysis: {config['historical_analysis']}

    Required Analysis:
    1. Evaluate task bounds and complexity for each prompt
    2. Apply intelligent decomposition where beneficial
    3. Identify research requirements and suggest approaches
    4. Perform ML-based classification and pattern recognition
    5. Generate optimized parallel execution plan
    6. Provide comprehensive risk assessment

    Return enhanced analysis with all coordination results included.
    """

    return execute_claude_agent_invocation(analyzer_prompt)
