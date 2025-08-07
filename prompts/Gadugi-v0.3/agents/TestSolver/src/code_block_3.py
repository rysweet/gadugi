   is_valid, issues = SharedTestInstructions.validate_test_structure(test_code)
   if not is_valid:
       print(f"Structure Issues: {issues}")
   