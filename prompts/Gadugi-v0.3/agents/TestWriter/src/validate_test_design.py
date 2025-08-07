   def validate_test_design(test_plan):
       """Validate test design against shared instructions."""
       # Check for idempotency considerations
       idempotency_check = check_idempotency_design(test_plan)

       # Check for parallel safety
       parallel_safety = check_parallel_safety_design(test_plan)

       # Check for resource management
       resource_management = check_resource_management_design(test_plan)

       return {
           'idempotent': idempotency_check,
           'parallel_safe': parallel_safety,
           'resource_managed': resource_management
       }
   