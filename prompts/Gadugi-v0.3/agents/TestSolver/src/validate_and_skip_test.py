def validate_and_skip_test(test_code, reason, justification):
    """Validate skip justification before applying."""
    is_valid, message = SharedTestInstructions.validate_skip_justification(
        reason, justification
    )

    if not is_valid:
        raise ValueError(f"Invalid skip justification: {message}")

    # Apply skip with proper documentation
    skip_decorator = f"@pytest.mark.skipif(True, reason='{justification}')"
    return f"{skip_decorator}\n{test_code}"
