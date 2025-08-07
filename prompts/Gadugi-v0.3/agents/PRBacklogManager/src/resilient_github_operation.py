@github_circuit_breaker
def resilient_github_operation(operation_func, *args, **kwargs):
    """Execute GitHub operation with circuit breaker protection"""
    try:
        return operation_func(*args, **kwargs)
    except RateLimitError:
        # Wait for rate limit reset
        sleep_time = calculate_rate_limit_wait()
        time.sleep(sleep_time)
        return operation_func(*args, **kwargs)
    except TemporaryAPIError as e:
        # Retry with exponential backoff
        return retry_manager.execute_with_backoff(operation_func, *args, **kwargs)
