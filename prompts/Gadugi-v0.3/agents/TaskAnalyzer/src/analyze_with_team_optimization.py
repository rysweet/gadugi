# Task analysis with team optimization
def analyze_with_team_optimization(tasks, team_capabilities):
    """Integrate with TeamCoach for optimal task assignment"""

    # Perform enhanced task analysis
    analysis_results = self.analyze_tasks_enhanced(tasks)

    # Get team capability assessment from TeamCoach
    team_assessment = teamcoach_agent.assess_team_capabilities(team_capabilities)

    # Optimize task assignments
    optimized_assignments = teamcoach_agent.optimize_task_assignments(
        tasks=analysis_results,
        team_capabilities=team_assessment,
        parallelization_constraints=self.get_parallelization_constraints()
    )

    # Update analysis with assignment optimizations
    for task in analysis_results:
        task.recommended_assignee = optimized_assignments.get_assignee(task.id)
        task.skill_match_score = optimized_assignments.get_match_score(task.id)
        task.team_coordination_overhead = optimized_assignments.get_coordination_overhead(task.id)

    return analysis_results
