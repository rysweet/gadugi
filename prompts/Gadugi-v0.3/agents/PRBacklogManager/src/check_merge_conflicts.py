   @github_circuit_breaker
   def check_merge_conflicts(pr_number):
       merge_status = github_ops.get_merge_status(pr_number)
       if merge_status.has_conflicts:
           return ConflictAssessment(
               has_conflicts=True,
               affected_files=merge_status.conflicted_files,
               resolution_complexity=assess_conflict_complexity(merge_status)
           )
       return ConflictAssessment(has_conflicts=False)
   