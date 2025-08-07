   def apply_readiness_labels(pr_number, readiness_result):
       current_labels = github_ops.get_pr_labels(pr_number)

       if readiness_result.is_ready:
           # Add ready-seeking-human label
           if 'ready-seeking-human' not in current_labels:
               github_ops.add_labels(pr_number, ['ready-seeking-human'])
               github_ops.add_comment(pr_number,
                   "✅ PR is ready for human review and merge! All automated checks passed.")
       else:
           # Remove ready-seeking-human label if present
           if 'ready-seeking-human' in current_labels:
               github_ops.remove_labels(pr_number, ['ready-seeking-human'])

           # Add specific blocking labels
           blocking_issues = identify_blocking_issues(readiness_result.assessment)
           github_ops.add_labels(pr_number, blocking_issues)
   