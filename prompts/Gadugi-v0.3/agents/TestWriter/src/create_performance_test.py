def create_performance_test(operation_name, performance_requirements):
    """Create performance validation test."""
    return f'''
def test_{operation_name}_performance(performance_fixtures):
    """Test {operation_name} meets performance requirements."""
    import time

    # Arrange
    start_time = time.time()

    # Act
    result = perform_{operation_name}(performance_fixtures.large_dataset)

    # Assert
    execution_time = time.time() - start_time
    assert execution_time < {performance_requirements.max_time_seconds}
    assert result.meets_quality_criteria()
'''
