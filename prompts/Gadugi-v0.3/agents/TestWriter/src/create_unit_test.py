def create_unit_test(function_name, function_signature):
    """Create focused unit test for individual function."""
    return f'''
def test_{function_name}_happy_path(sample_input_fixture):
    """Test {function_name} with valid inputs."""
    # Arrange
    expected_result = calculate_expected_result(sample_input_fixture)

    # Act
    actual_result = {function_name}(sample_input_fixture)

    # Assert
    assert actual_result == expected_result
    assert validate_result_properties(actual_result)

def test_{function_name}_error_conditions(invalid_input_fixture):
    """Test {function_name} error handling."""
    with pytest.raises(ExpectedExceptionType) as exc_info:
        {function_name}(invalid_input_fixture)

    assert "expected error message" in str(exc_info.value)

def test_{function_name}_edge_cases(edge_case_fixtures):
    """Test {function_name} with edge case inputs."""
    for edge_case in edge_case_fixtures:
        result = {function_name}(edge_case.input)
        assert edge_case.validate_result(result)
'''
