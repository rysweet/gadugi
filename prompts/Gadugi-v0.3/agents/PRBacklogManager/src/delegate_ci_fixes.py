   def delegate_ci_fixes(pr_number, ci_assessment):
       for failing_check in ci_assessment.failing_checks:
           if failing_check.retriable:
               # Retry transient failures automatically
               github_ops.retry_status_check(pr_number, failing_check.name)
           else:
               # Delegate fix to WorkflowMaster
               fix_prompt = generate_ci_fix_prompt(pr_number, failing_check)
               invoke_workflow_master(fix_prompt)
   