class TaskComplexityPredictor:
    """ML-based task complexity prediction"""

    def __init__(self):
        self.model = None  # Load pre-trained model
        self.feature_extractor = TaskFeatureExtractor()

    def predict_complexity(self, task_description):
        features = self.feature_extractor.extract(task_description)
        return self.model.predict(features)

    def predict_decomposition_benefit(self, task_description):
        features = self.feature_extractor.extract(task_description)
        return self.model.predict_decomposition_score(features)
