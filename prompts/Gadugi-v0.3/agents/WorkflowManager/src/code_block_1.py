# Initialize shared managers for workflow execution
github_ops = GitHubOperations()
state_manager = WorkflowStateManager()
error_handler = ErrorHandler(retry_manager=RetryManager())
task_tracker = TaskTracker(todowrite_manager=TodoWriteManager())
phase_tracker = WorkflowPhaseTracker()
productivity_analyzer = ProductivityAnalyzer()

# Configure circuit breakers for workflow resilience
github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
implementation_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=600)
