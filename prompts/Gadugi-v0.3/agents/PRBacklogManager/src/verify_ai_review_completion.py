def verify_ai_review_completion(pr_number):
    """Check if AI code review (Phase 9) has been completed"""
    pr_comments = github_ops.get_pr_comments(pr_number)
    ai_review_comments = [c for c in pr_comments if 'code-reviewer' in c.author]

    if not ai_review_comments:
        # AI review not yet performed
        return False

    latest_ai_review = max(ai_review_comments, key=lambda c: c.created_at)
    return check_review_completeness(latest_ai_review)
