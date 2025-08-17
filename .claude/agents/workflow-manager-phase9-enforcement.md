---
name: workflow-manager-phase9-enforcement
model: inherit
description: Enforcement mechanism for mandatory Phase 9 code review in WorkflowManager
version: 1.0.0
tools: []
---

# WorkflowManager Phase 9 Enforcement Implementation

## CRITICAL: How to Actually Enforce Phase 9

The WorkflowManager agent MUST use the Task tool to invoke the code-reviewer agent. Here's the exact implementation:

### After PR Creation (Phase 8 Complete)

```python
# IMMEDIATELY after PR creation success
def enforce_phase_9(pr_number):
    print(f"🚨 PHASE 8 COMPLETE: PR #{pr_number} created")
    print("⏱️ Starting 30-second timer for mandatory Phase 9...")

    # Wait 30 seconds for PR to propagate
    time.sleep(30)

    print(f"🚨 ENFORCING PHASE 9: Invoking code-reviewer for PR #{pr_number}")

    # Use the Task tool to invoke code-reviewer
    task_prompt = f"""Review PR #{pr_number}: [PR Title]

This is the MANDATORY Phase 9 code review required by WorkflowManager.

Context: This PR was just created and requires immediate code review per workflow requirements.

Please conduct a thorough review of all changes."""

    # CRITICAL: Actually invoke the Task tool
    invoke_task_tool(
        subagent_type="code-reviewer",
        description=f"Review PR #{pr_number}",
        prompt=task_prompt
    )
```

### In WorkflowManager Execution

When executing Phase 8 (PR Creation), the agent MUST:

1. Create the PR using gh CLI
2. Verify PR was created successfully
3. **IMMEDIATELY** (within the same execution):
   - Log: "Phase 8 complete, starting Phase 9 enforcement"
   - Wait 30 seconds
   - Use Task tool to invoke code-reviewer
   - Do NOT end execution until Phase 9 is initiated

### Example Task Tool Invocation

The WorkflowManager should invoke the Task tool like this:

```
Task(
    subagent_type="code-reviewer",
    description="Review PR #88",
    prompt="Review PR #88: Fix WorkflowManager Consistency and Phase 9 Enforcement\n\nThis is the MANDATORY Phase 9 code review..."
)
```

### Recovery Action for PR #88

Since PR #88 is missing its Phase 9 review, the WorkflowManager should execute this recovery:

1. Detect that PR #88 has no reviews
2. Log: "CRITICAL: PR #88 missing mandatory Phase 9 review"
3. Invoke Task tool with code-reviewer subagent
4. Verify review was posted
5. Continue to Phase 10 (code-review-response)

## Implementation in workflow-manager.md

The workflow-manager.md agent prompt needs to be updated to:

1. **Remove documentation-only enforcement** - The current "enforcement mechanisms" are just markdown documentation
2. **Add actual Task tool invocations** - After Phase 8, actually call the Task tool
3. **Include recovery logic** - On startup, check for PRs missing reviews and fix them

## Key Insight

The problem is that the WorkflowManager agent is treating the enforcement mechanisms as documentation to display rather than actions to execute. The agent needs explicit instructions to:

- Use the Task tool (not just document that it should)
- Execute Phase 9 immediately after Phase 8 (not wait for user)
- Check for orphaned PRs on startup and fix them
