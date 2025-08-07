# Enhanced task analysis with container execution
@container_runtime.with_security_policy("task_analysis")
def analyze_task_in_container(task):
    """Secure task analysis in containerized environment"""

    with container_runtime.create_analysis_container() as container:
        # Secure file analysis
        analysis_result = container.execute_analysis(task.prompt_file)

        # Pattern recognition in isolated environment
        pattern_result = container.execute_pattern_analysis(task.description)

        # Dependency analysis with network isolation
        dependency_result = container.execute_dependency_analysis(
            task.target_files,
            network_access=False
        )

        return combine_analysis_results([
            analysis_result, pattern_result, dependency_result
        ])
