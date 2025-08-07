class TaskPatternClassifier:
    """ML-based task pattern recognition and optimization"""

    def __init__(self):
        self.pattern_model = self.load_pattern_classification_model()
        self.complexity_predictor = self.load_complexity_prediction_model()
        self.optimization_engine = self.load_optimization_model()

    def classify_tasks(self, tasks):
        """Classify tasks using ML patterns"""
        classifications = []

        for task in tasks:
            # Extract features for ML classification
            features = self.extract_task_features(task)

            # Predict task patterns
            pattern_prediction = self.pattern_model.predict(features)

            # Predict complexity
            complexity_prediction = self.complexity_predictor.predict(features)

            # Generate optimization suggestions
            optimizations = self.optimization_engine.suggest_optimizations(
                features, pattern_prediction, complexity_prediction
            )

            classification = TaskClassification(
                primary_type=pattern_prediction.primary_type,
                subtypes=pattern_prediction.subtypes,
                patterns=pattern_prediction.patterns,
                confidence=pattern_prediction.confidence,
                complexity_scores=complexity_prediction,
                optimizations=optimizations
            )

            classifications.append(classification)

        return classifications

    def extract_task_features(self, task):
        """Extract ML features from task description"""
        return TaskFeatures(
            # Text-based features
            description_length=len(task.description),
            keyword_counts=self.count_technical_keywords(task.description),
            complexity_indicators=self.extract_complexity_indicators(task.description),

            # File-based features
            file_count=len(task.target_files),
            file_types=self.analyze_file_types(task.target_files),

            # Dependency features
            dependency_count=len(task.dependencies),
            external_dependency_count=len(task.external_dependencies),

            # Historical features
            similar_task_outcomes=self.get_similar_task_history(task)
        )
