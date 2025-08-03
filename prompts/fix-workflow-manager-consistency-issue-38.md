# Fix WorkflowManager Consistency and Phase 9 Enforcement - Issue #38

## Overview

The WorkflowManager agent is experiencing consistency issues where it doesn't reliably invoke the code reviewer and code review response agents after creating PRs (Phase 9), and sometimes stops after planning without executing implementation. This prompt addresses these critical workflow execution gaps.

## Problem Statement

### Current Issues:
1. **Phase 9 Skipping**: Despite being marked as "MANDATORY - NEVER SKIP", the code review phase is often not executed
2. **Incomplete Execution**: WorkflowManager sometimes creates a plan but stops before implementation
3. **Missing Code Review Response**: Even when reviews happen, the code-review-response agent is not consistently invoked
4. **State Management Gaps**: Phase transitions aren't properly tracked, leading to orphaned PRs

### Evidence:
- PR #36 was created but no code review was invoked
- Multiple PRs exist without automated code reviews
- WorkflowManager documentation clearly states Phase 9 is mandatory
- State files show Phase 8 complete but Phase 9 never starts

## Technical Analysis

### Root Causes:
1. **Weak Phase Enforcement**: No programmatic enforcement of mandatory phases
2. **Missing Phase Transition Logic**: No automatic progression from Phase 8 to Phase 9
3. **Insufficient Task List Generation**: TodoWrite lists don't always include review tasks
4. **Early Termination**: Agent completes planning but doesn't transition to execution

### Required Fixes:
1. **Strengthen Phase 9 Enforcement**: Add multiple checkpoints and automatic invocation
2. **Improve Task List Generation**: Always include review tasks in TodoWrite
3. **Add Phase Transition Hooks**: Automatic progression between phases
4. **Prevent Early Termination**: Ensure full workflow execution

## Implementation Plan

### Phase 1: Strengthen WorkflowManager Prompt

1. **Add Explicit Phase 9 Enforcement**:
   ```markdown
   ### CRITICAL: Phase 9 Enforcement
   
   **PHASE 9 IS ABSOLUTELY MANDATORY - ENFORCEMENT MECHANISMS:**
   
   1. **Automatic Invocation After PR Creation**:
      - IMMEDIATELY after PR creation success, add code review task
      - Set a 30-second timer to invoke code-reviewer
      - Log CRITICAL error if review not invoked
   
   2. **Task List Requirements**:
      - ALWAYS include "Invoke code-reviewer agent" as task #8
      - ALWAYS include "Process review with code-review-response" as task #9
      - Mark both as HIGH priority
   
   3. **State Validation**:
      - Before marking workflow complete, VERIFY review exists
      - If no review found, FORCE code-reviewer invocation
      - Update state only after review confirmation
   ```

2. **Improve Task Generation**:
   ```python
   # Enhanced task list generation
   def generate_workflow_tasks(prompt_data):
       tasks = [
           # ... phases 1-7 ...
           TaskData(
               id="8",
               content="Create pull request",
               status="pending",
               priority="high",
               phase=WorkflowPhase.PULL_REQUEST_CREATION
           ),
           TaskData(
               id="9",
               content="MANDATORY: Invoke code-reviewer agent",
               status="pending",
               priority="critical",  # New priority level
               phase=WorkflowPhase.REVIEW,
               auto_invoke=True  # Flag for automatic execution
           ),
           TaskData(
               id="10", 
               content="MANDATORY: Process review with code-review-response agent",
               status="pending",
               priority="critical",
               phase=WorkflowPhase.REVIEW_RESPONSE,
               auto_invoke=True
           )
       ]
   ```

3. **Add Phase Transition Hooks**:
   ```markdown
   ### Automatic Phase Transitions
   
   **CRITICAL: These transitions MUST happen automatically:**
   
   1. **Phase 8 → Phase 9**:
      - After PR creation confirmation
      - Maximum 30-second delay
      - No user intervention required
   
   2. **Phase 9 → Phase 10**:
      - After review posted confirmation
      - Immediate invocation of code-review-response
      - Even for approvals (acknowledge and confirm)
   ```

### Phase 2: Add Execution Guarantees

1. **Prevent Early Termination**:
   ```markdown
   ### Execution Completion Requirements
   
   **NEVER terminate WorkflowManager until:**
   1. All 10 phases are complete OR
   2. An unrecoverable error occurs OR
   3. User explicitly cancels
   
   **After creating task list:**
   - IMMEDIATELY start Phase 1 execution
   - Do NOT wait for user confirmation
   - Do NOT stop after planning
   ```

2. **Add Progress Checkpoints**:
   ```markdown
   ### Progress Verification Checkpoints
   
   After each phase, verify:
   1. Expected artifacts exist (issue, branch, PR, review)
   2. State file is updated
   3. Next phase is queued for execution
   4. No manual intervention needed for next phase
   ```

### Phase 3: Implement Recovery Mechanisms

1. **Orphaned PR Detection**:
   ```bash
   # Add to WorkflowManager initialization
   detect_and_fix_orphaned_prs() {
       echo "Scanning for PRs missing reviews..."
       
       gh pr list --author "@me" --state open --json number,createdAt | \
       jq -r '.[] | select((now - (.createdAt | fromdateiso8601)) > 300) | .number' | \
       while read -r pr_num; do
           if ! gh pr view "$pr_num" --json reviews | jq -e '.reviews | length > 0' >/dev/null; then
               echo "CRITICAL: PR #$pr_num missing review! Invoking code-reviewer..."
               invoke_code_reviewer "$pr_num"
           fi
       done
   }
   ```

2. **State Repair Function**:
   ```python
   def repair_incomplete_workflows():
       """Fix workflows that stopped prematurely"""
       
       for state_file in glob(".github/workflow-states/*/state.md"):
           state = parse_state_file(state_file)
           
           # Check if implementation was planned but not executed
           if state.phase == "planning_complete" and not state.implementation_started:
               print(f"Found stalled workflow: {state.task_id}")
               print("Resuming from Phase 4: Implementation")
               resume_workflow(state.task_id, start_phase=4)
           
           # Check if PR created but review missing
           elif state.pr_number and not state.review_complete:
               print(f"Found PR #{state.pr_number} missing review")
               force_phase_9_execution(state.pr_number)
   ```

### Phase 4: Update Agent Instructions

1. **Add Execution Commitment**:
   ```markdown
   ## Execution Commitment
   
   When invoked with a prompt file, you MUST:
   1. Parse the prompt completely
   2. Generate full task list (including review tasks)
   3. BEGIN EXECUTION IMMEDIATELY
   4. Continue through ALL phases
   5. Only stop for unrecoverable errors
   
   NEVER:
   - Stop after planning
   - Wait for user confirmation between phases
   - Skip Phase 9 or 10
   - Mark workflow complete without review
   ```

2. **Add TodoWrite Enforcement**:
   ```markdown
   ## TodoWrite Requirements
   
   Your task list MUST ALWAYS include:
   - Task for each of the 10 workflow phases
   - "Invoke code-reviewer agent" as a CRITICAL priority task
   - "Process review with code-review-response" as a CRITICAL priority task
   - Clear dependencies between tasks
   - No gaps in task numbering
   ```

## Testing Requirements

1. **Phase 9 Enforcement Tests**:
   - Verify code-reviewer is invoked after every PR
   - Confirm review tasks are always in TodoWrite
   - Test automatic phase transition

2. **Execution Completion Tests**:
   - Verify workflow continues after planning
   - Test that all phases execute sequentially
   - Confirm no early termination

3. **Recovery Tests**:
   - Test orphaned PR detection and fixing
   - Verify state repair for incomplete workflows
   - Test resumption from various interruption points

## Success Criteria

1. **100% Phase 9 Execution**: Every PR gets a code review automatically
2. **0% Planning-Only Runs**: WorkflowManager always executes implementation
3. **100% Review Response**: Every review gets processed with code-review-response
4. **Automatic Recovery**: Orphaned PRs are detected and fixed within 5 minutes

## Migration Steps

1. Update WorkflowManager prompt with enhanced instructions
2. Add automatic phase transition logic
3. Implement orphaned PR detection
4. Add state repair functionality
5. Update task generation to include mandatory review tasks
6. Test with sample workflows
7. Deploy and monitor for consistency

## Rollback Plan

If issues arise:
1. Revert to previous WorkflowManager prompt
2. Manually invoke code-reviewer for any missed PRs
3. Document specific failure scenarios
4. Iterate on fixes based on failure analysis

## Long-term Improvements

1. **GitHub Actions Integration**: Webhook to ensure reviews happen
2. **Status Checks**: Require review before merge capability
3. **Metrics Dashboard**: Track phase completion rates
4. **Automated Alerts**: Notify when phases are skipped