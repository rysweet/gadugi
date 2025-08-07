# Leverage shared modules
error_handler = ErrorHandler()
github_ops = GitHubOperations()
state_manager = WorkflowStateManager()

# Circuit breaker for complex test generation
@CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
def generate_test_suite(code_analysis):
    """Generate comprehensive test suite with error protection."""
    try:
        return create_comprehensive_tests(code_analysis)
    except Exception as e:
        return provide_manual_test_guidance(code_analysis, e)
