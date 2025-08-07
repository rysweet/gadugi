class PatternBasedDecomposer:
    """Use common software patterns for decomposition"""

    patterns = {
        "MVC": ["Model", "View", "Controller"],
        "ETL": ["Extract", "Transform", "Load"],
        "CRUD": ["Create", "Read", "Update", "Delete"],
        "AUTH": ["Authentication", "Authorization", "Session Management"],
        "API": ["Request Handling", "Business Logic", "Response Formatting"]
    }

    def decompose_by_pattern(self, task, pattern):
        if pattern in self.patterns:
            return [
                f"Implement {component} for {task.name}"
                for component in self.patterns[pattern]
            ]
