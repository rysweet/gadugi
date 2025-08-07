   def coordinate_branch_update(pr_number, sync_assessment):
       if sync_assessment.commits_behind <= 10:
           # Simple update - delegate to WorkflowMaster
           update_prompt = generate_branch_update_prompt(pr_number)
           invoke_workflow_master(update_prompt)
       else:
           # Large update - recommend human review
           github_ops.add_comment(pr_number,
               f"⚠️ Branch is {sync_assessment.commits_behind} commits behind main. "
               "Consider manual rebase to preserve commit history.")
   