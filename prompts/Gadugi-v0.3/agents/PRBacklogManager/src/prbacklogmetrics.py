class PRBacklogMetrics:
    def __init__(self):
        self.processing_times = []
        self.resolution_rates = {}
        self.error_frequencies = {}

    def calculate_efficiency_score(self):
        """Calculate overall efficiency of PR backlog management"""
        avg_processing_time = statistics.mean(self.processing_times)
        automation_rate = self.calculate_automation_rate()
        accuracy_rate = self.calculate_accuracy_rate()

        return EfficiencyScore(
            processing_speed=min(100, 300 / avg_processing_time),  # 5 min target
            automation_effectiveness=automation_rate * 100,
            accuracy_rating=accuracy_rate * 100,
            overall_score=(processing_speed + automation_effectiveness + accuracy_rating) / 3
        )
