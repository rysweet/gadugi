   @pr_analysis_circuit_breaker
   def evaluate_ci_status(pr_number):
       checks = github_ops.get_status_checks(pr_number)
       failing_checks = [check for check in checks if check.status != 'success']

       return CIAssessment(
           all_passing=len(failing_checks) == 0,
           failing_checks=failing_checks,
           can_auto_retry=[check for check in failing_checks if check.retriable]
       )
   