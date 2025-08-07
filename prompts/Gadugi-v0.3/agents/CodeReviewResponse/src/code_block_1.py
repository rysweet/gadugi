# NOTE: This is illustrative pseudo-code showing the conceptual approach
# Actual implementation uses Claude Code tools to parse review content

# Parse the review feedback
feedback_points = extract_feedback_from_review()
categorized_feedback = {
    "critical": [],
    "important": [],
    "suggestions": [],
    "questions": [],
    "minor": []
}

# Categorize each point
for point in feedback_points:
    category = categorize_feedback(point)
    categorized_feedback[category].append(point)
