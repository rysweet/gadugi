   def evaluate_review_status(pr_number):
       reviews = github_ops.get_pr_reviews(pr_number)
       human_reviews = [r for r in reviews if not r.is_bot]

       return ReviewAssessment(
           has_approved_review=any(r.state == 'APPROVED' for r in human_reviews),
           pending_requests=github_ops.get_pending_review_requests(pr_number),
           ai_review_complete=check_ai_review_completion(pr_number)
       )
   