class TaskDecompositionCoordinator:
    """Orchestrates the enhanced Task Decomposition Analyzer system"""

    def __init__(self):
        self.task_bounds_eval = TaskBoundsEvalAgent()
        self.task_decomposer = TaskDecomposerAgent()
        self.task_research_agent = TaskResearchAgent()
        self.pattern_classifier = TaskPatternClassifier()

    def analyze_with_decomposition(self, prompt_files):
        """Complete task analysis with decomposition integration"""

        enhanced_results = []

        for prompt_file in prompt_files:
            # Step 1: Initial task analysis
            base_analysis = self.analyze_base_task(prompt_file)

            # Step 2: Task bounds evaluation
            bounds_result = self.task_bounds_eval.evaluate(base_analysis)

            # Step 3: Conditional decomposition
            if bounds_result.requires_decomposition:
                decomposition_result = self.task_decomposer.decompose(
                    base_analysis, bounds_result
                )
                base_analysis.subtasks = decomposition_result.subtasks
                base_analysis.decomposition_benefit = decomposition_result.speedup_factor

            # Step 4: Conditional research
            if bounds_result.requires_research:
                research_result = self.task_research_agent.research(
                    base_analysis, bounds_result.research_areas
                )
                base_analysis.research_findings = research_result

                # Re-evaluate after research
                bounds_result = self.task_bounds_eval.evaluate(base_analysis)

            # Step 5: Pattern-based optimization
            pattern_optimizations = self.pattern_classifier.optimize_for_patterns(
                base_analysis
            )
            base_analysis.apply_optimizations(pattern_optimizations)

            enhanced_results.append(base_analysis)

        # Step 6: Cross-task optimization
        cross_task_optimizations = self.optimize_cross_task_parallelization(
            enhanced_results
        )

        return self.generate_enhanced_execution_plan(
            enhanced_results, cross_task_optimizations
        )
