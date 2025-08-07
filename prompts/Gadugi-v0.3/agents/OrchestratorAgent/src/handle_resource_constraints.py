# Resource-aware execution with circuit breakers
@error_handler.with_graceful_degradation(sequential_fallback)
def handle_resource_constraints():
    # Monitor system resources
    if performance_analyzer.detect_resource_exhaustion():
        # Automatically reduce parallelism
        reduce_concurrent_tasks()

    # Circuit breaker for disk space
    if disk_circuit_breaker.is_open():
        cleanup_temporary_files()

    # Memory pressure handling
    if memory_monitor.pressure_detected():
        switch_to_sequential_execution()
