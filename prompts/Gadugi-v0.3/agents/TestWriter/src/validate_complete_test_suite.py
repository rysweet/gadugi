   def validate_complete_test_suite(test_suite_code):
       """Perform final validation of complete test suite."""

       validation_results = {
           'structure_valid': True,
           'idempotent': True,
           'parallel_safe': True,
           'well_documented': True,
           'fixtures_appropriate': True,
           'coverage_complete': True
       }

       # Run all shared instruction validations
       for test_method in extract_test_methods(test_suite_code):
           # Validate each test individually
           method_validation = validate_individual_test(test_method)

           # Aggregate results
           for key in validation_results:
               validation_results[key] &= method_validation.get(key, True)

       return validation_results
   