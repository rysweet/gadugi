# Shared module integration (when available)
from shared.error_handling import CircuitBreaker, RetryManager
from shared.task_tracking import TaskMetrics, TaskTracker
from shared.state_management import StateManager

class TaskBoundsEvaluator:
    def __init__(self):
        self.retry_manager = RetryManager()
        self.task_tracker = TaskTracker()
        self.state_manager = StateManager()
        self.circuit_breaker = CircuitBreaker()

    @circuit_breaker.protect
    def evaluate_task_bounds(self, task_data):
        return self.retry_manager.execute_with_retry(
            lambda: self._perform_evaluation(task_data),
            max_attempts=3
        )
