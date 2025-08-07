   def enhance_test_with_shared_instructions(test_code):
       """Apply shared instruction framework to test code."""

       # Ensure idempotency
       idempotent_code = SharedTestInstructions.ensure_test_idempotency(test_code)

       # Ensure resource cleanup
       cleanup_code = SharedTestInstructions.ensure_resource_cleanup(idempotent_code)

       # Validate structure
       is_valid, issues = SharedTestInstructions.validate_test_structure(cleanup_code)
       if not is_valid:
           cleanup_code = fix_structure_issues(cleanup_code, issues)

       # Validate dependency management
       deps_valid, dep_issues = SharedTestInstructions.validate_dependency_management(cleanup_code)
       if not deps_valid:
           cleanup_code = fix_dependency_issues(cleanup_code, dep_issues)

       # Validate parallel safety
       parallel_safe, parallel_issues = SharedTestInstructions.validate_parallel_safety(cleanup_code)
       if not parallel_safe:
           cleanup_code = fix_parallel_safety_issues(cleanup_code, parallel_issues)

       return cleanup_code
   