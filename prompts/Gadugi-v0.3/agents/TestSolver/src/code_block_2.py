   analysis = SharedTestInstructions.analyze_test_purpose(test_code, context)
   print(f"Test Purpose: {analysis.purpose}")
   print(f"Requirements: {analysis.requirements}")
   print(f"Expected Outcome: {analysis.expected_outcome}")
   