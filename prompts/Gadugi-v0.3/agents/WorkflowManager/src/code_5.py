# MANDATORY tasks that MUST be in every workflow
TaskData(
    id="9",
    content="🚨 MANDATORY: Invoke code-reviewer agent (Phase 9 - CANNOT SKIP)",
    status="pending",
    priority="high",  # Maximum priority
    phase=WorkflowPhase.REVIEW,
    auto_invoke=True,  # Flag for automatic execution
    enforcement_level="CRITICAL"  # New enforcement level
),
TaskData(
    id="10",
    content="🚨 MANDATORY: Process review with code-review-response agent",
    status="pending",
    priority="high",  # Maximum priority
    phase=WorkflowPhase.REVIEW_RESPONSE,
    auto_invoke=True,  # Flag for automatic execution
    enforcement_level="CRITICAL"  # New enforcement level
)
