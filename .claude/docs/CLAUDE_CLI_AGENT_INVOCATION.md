# Claude CLI Agent Invocation Guide

## Overview

This guide documents how to invoke Claude Code agents from scripts and automation tools using the Claude CLI.

## CLI Reference

Based on https://docs.anthropic.com/en/docs/claude-code/cli-reference:

- **Interactive mode**: `claude` or `claude "initial prompt"`
- **Non-interactive mode**: `claude -p "prompt"` (executes and exits)
- **Continue conversation**: `claude -c` or `claude -c -p "prompt"`
- **Resume specific session**: `claude -r "<session-id>" "prompt"`

## Agent Invocation Patterns

### From Bash Scripts

```bash
# Non-interactive agent invocation
claude -p "/agent:CodeReviewer

Review PR #123 for implementation quality and completeness."

# With environment context
export PR_NUMBER=123
claude -p "/agent:CodeReviewer

Review PR $PR_NUMBER which was automatically created by WorkflowManager."
```

### From Automated Workflows

```bash
# In WorkflowManager Phase 9
invoke_code_reviewer() {
    local pr_number="$1"

    echo "Invoking CodeReviewer agent for PR #$pr_number"

    # Build the prompt
    local prompt="/agent:CodeReviewer

Review PR #$pr_number as part of mandatory Phase 9 workflow execution.

Context: WorkflowManager automatic code review invocation.

Focus on:
1. Implementation quality
2. Test coverage
3. Documentation
4. Security considerations"

    # Execute non-interactively
    if claude -p "$prompt"; then
        echo "Code review completed successfully"
        return 0
    else
        echo "Code review invocation failed"
        return 1
    fi
}
```

### From Recovery Scripts

```bash
# Orphaned PR recovery
recover_orphaned_pr() {
    local pr_number="$1"

    claude -p "/agent:CodeReviewer

Review PR #$pr_number which appears to be missing mandatory code review.

Context: Orphaned PR recovery - automatic Phase 9 enforcement.

This PR was created over 5 minutes ago without receiving the mandatory
Phase 9 code review. Please conduct a thorough review."
}
```

## Important Considerations

1. **Non-interactive Mode**: Always use `-p` flag for automation to prevent hanging
2. **Error Handling**: Check return codes and handle failures gracefully
3. **Timeouts**: Consider implementing timeouts for long-running operations
4. **Context Passing**: Use clear context in prompts since agents can't access shell variables
5. **Session Management**: For multi-step workflows, consider using `-c` to continue conversations

## Example Integration

### WorkflowManager Enhanced Phase 9

```bash
# Phase 9: Mandatory Code Review
execute_phase_9() {
    local pr_number="$1"

    # Check if review already exists
    if gh pr view "$pr_number" --json reviews | jq -e '.reviews | length > 0' >/dev/null; then
        echo "Review already exists for PR #$pr_number"
        return 0
    fi

    # Invoke CodeReviewer agent
    echo "🚨 ENFORCING Phase 9: Invoking CodeReviewer for PR #$pr_number"

    local prompt="/agent:CodeReviewer

MANDATORY Phase 9 Review for PR #$pr_number

This is an automated invocation by WorkflowManager to ensure 100% Phase 9 compliance.
The PR must receive a comprehensive code review before the workflow can proceed.

Please review all changes and provide feedback."

    # Execute with timeout
    timeout 300 claude -p "$prompt"
    local exit_code=$?

    if [ $exit_code -eq 124 ]; then
        echo "ERROR: Code review timed out after 5 minutes"
        return 1
    elif [ $exit_code -ne 0 ]; then
        echo "ERROR: Code review invocation failed with exit code $exit_code"
        return 1
    fi

    # Verify review was posted
    sleep 10
    if gh pr view "$pr_number" --json reviews | jq -e '.reviews | length > 0' >/dev/null; then
        echo "✅ Code review posted successfully"
        return 0
    else
        echo "⚠️ Review may not have been posted, retrying..."
        return 1
    fi
}
```

## Testing Agent Invocation

To test if Claude CLI is properly configured:

```bash
# Simple test
claude -p "Hello, can you confirm you received this message?"

# Agent test
claude -p "/agent:CodeReviewer

This is a test invocation. Please confirm you can receive agent commands."
```

## Troubleshooting

1. **Command not found**: Ensure `claude` is in your PATH
2. **Timeouts**: Use `timeout` command to prevent hanging
3. **No output**: Check if using `-p` flag for non-interactive mode
4. **Authentication**: Ensure Claude CLI is properly authenticated

## Future Enhancements

1. **Structured Output**: Parse agent responses for automated workflows
2. **Batch Operations**: Process multiple PRs in sequence
3. **Webhook Integration**: Trigger from GitHub webhooks
4. **Status Reporting**: Integration with CI/CD pipelines
