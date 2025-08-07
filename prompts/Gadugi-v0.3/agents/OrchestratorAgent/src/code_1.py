# Initialize shared managers at startup
github_ops = GitHubOperations()
state_manager = WorkflowStateManager()
error_handler = ErrorHandler(retry_manager=RetryManager())
task_tracker = TaskTracker(todowrite_manager=TodoWriteManager())
performance_analyzer = ProductivityAnalyzer()

# Configure circuit breakers for resilient operations
github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
execution_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=600)
