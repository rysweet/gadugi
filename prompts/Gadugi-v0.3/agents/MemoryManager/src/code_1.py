# Pruning rules example
PRUNING_RULES = {
    "completed_tasks": {
        "age_threshold": "7 days",
        "keep_high_priority": True,
        "keep_recent_count": 10
    },
    "reflections": {
        "age_threshold": "30 days",
        "consolidate_similar": True
    },
    "context_items": {
        "relevance_scoring": True,
        "keep_referenced": True
    }
}
