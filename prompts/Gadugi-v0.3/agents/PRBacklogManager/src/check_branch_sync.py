   def check_branch_sync(pr_number):
       pr_details = github_ops.get_pr_details(pr_number)
       behind_count = github_ops.get_commits_behind_main(pr_details.head_sha)

       return SyncAssessment(
           is_up_to_date=behind_count == 0,
           commits_behind=behind_count,
           requires_update=behind_count > 0
       )
   