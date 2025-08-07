   def create_test_method(method_name, purpose, requirements):
       """Create individual test method with clear intent."""

       # Analyze purpose to guide test structure
       analysis = SharedTestInstructions.analyze_test_purpose("", purpose)

       test_method = f'''
   def test_{method_name}(self, shared_fixture_name):
       """
       Test {purpose}.

       Requirements:
       {format_requirements(requirements)}

       Expected Behavior:
       - {analysis.expected_outcome}

       Test Strategy:
       - Setup: {describe_setup()}
       - Action: {describe_action()}
       - Verification: {describe_verification()}
       """

       # Arrange
       {generate_setup_code()}

       # Act
       {generate_action_code()}

       # Assert
       {generate_assertion_code()}

       # Verify idempotency (run again to ensure same result)
       {generate_idempotency_check()}
   '''

       return test_method
   