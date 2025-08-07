class ComparativeAnalysisMethod:
    """Compare multiple solutions or approaches"""

    def execute(self, alternatives):
        comparison_matrix = ComparisonMatrix()

        for alternative in alternatives:
            # Evaluate across multiple dimensions
            evaluation = evaluate_alternative(alternative, [
                "performance", "complexity", "maintainability",
                "cost", "risk", "scalability"
            ])
            comparison_matrix.add_evaluation(alternative, evaluation)

        return comparison_matrix.generate_recommendations()
