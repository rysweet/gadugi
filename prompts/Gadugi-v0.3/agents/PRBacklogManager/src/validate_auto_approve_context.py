# Auto-approve safety checks
def validate_auto_approve_context():
    """Validate that auto-approve is safe in current context"""
    if not os.getenv('GITHUB_ACTIONS'):
        raise SecurityError("Auto-approve only allowed in GitHub Actions")

    if not os.getenv('CLAUDE_AUTO_APPROVE'):
        raise SecurityError("Auto-approve not explicitly enabled")

    # Additional safety checks
    if os.getenv('GITHUB_EVENT_NAME') not in ['pull_request', 'schedule', 'workflow_dispatch']:
        raise SecurityError("Auto-approve not allowed for this event type")

# Restricted operations in auto-approve mode
RESTRICTED_OPERATIONS = [
    'force_push',
    'delete_branch',
    'close_issue',
    'merge_pr'
]

def check_operation_safety(operation):
    """Ensure operation is safe for auto-approve"""
    if operation in RESTRICTED_OPERATIONS:
        raise SecurityError(f"Operation {operation} not allowed in auto-approve mode")
