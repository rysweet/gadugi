#!/bin/bash
#
# Phase 9 Enforcement Script for WorkflowManager
# 
# This script ensures that Phase 9 (code review) is ALWAYS executed after PR creation.
# It should be invoked by WorkflowManager immediately after creating a PR.
#
# Usage: ./enforce_phase_9.sh <PR_NUMBER>
#

set -euo pipefail

# Check if PR number is provided
if [ $# -eq 0 ]; then
    echo "ERROR: PR number required"
    echo "Usage: $0 <PR_NUMBER>"
    exit 1
fi

PR_NUMBER="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/phase_9_enforcement_${PR_NUMBER}.log"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log "INFO" "🚨 PHASE 9 ENFORCEMENT: Starting for PR #$PR_NUMBER"

# Function to wait for PR propagation with adaptive timing
wait_for_pr_propagation() {
    local pr_num="$1"
    local max_wait=60
    local waited=0
    local check_interval=5
    
    log "INFO" "Waiting for PR #$pr_num to fully propagate (max ${max_wait}s)..."
    
    while [ $waited -lt $max_wait ]; do
        # Check if PR is accessible and has all expected metadata
        if gh pr view "$pr_num" --json reviews,title,author >/dev/null 2>&1; then
            # Add minimum wait time to ensure GitHub API consistency
            local min_wait=10
            if [ $waited -lt $min_wait ]; then
                local remaining_wait=$((min_wait - waited))
                log "INFO" "PR accessible, waiting ${remaining_wait}s more for API consistency..."
                sleep $remaining_wait
            fi
            log "INFO" "✅ PR propagation complete (waited ${waited}s total)"
            return 0
        fi
        
        log "INFO" "PR not fully accessible yet, waiting ${check_interval}s more (${waited}s elapsed)..."
        sleep $check_interval
        waited=$((waited + check_interval))
    done
    
    log "WARN" "PR propagation timeout after ${max_wait}s, proceeding anyway"
    return 0
}

# Function to check if review exists
check_review_exists() {
    local pr_num="$1"
    local review_count
    
    review_count=$(gh pr view "$pr_num" --json reviews --jq '.reviews | length' 2>/dev/null || echo "0")
    
    if [ "$review_count" -gt 0 ]; then
        log "INFO" "✅ Review already exists for PR #$pr_num (count: $review_count)"
        return 0
    else
        log "WARN" "⚠️ No review found for PR #$pr_num"
        return 1
    fi
}

# Function to invoke code reviewer
invoke_code_reviewer() {
    local pr_num="$1"
    
    log "INFO" "🚨 ENFORCING MANDATORY Phase 9: Invoking code-reviewer for PR #$pr_num"
    
    # Post a comment to document the enforcement
    local comment="🚨 **Phase 9 Enforcement Triggered**

This PR has completed Phase 8 (PR creation) and is now automatically proceeding to Phase 9 (mandatory code review).

**Status**: Invoking code-reviewer agent...

*This is an automated WorkflowManager Phase 9 enforcement action.*"
    
    gh pr comment "$pr_num" --body "$comment" || log "WARN" "Failed to post enforcement comment"
    
    # Build the code review prompt as a single line with proper escaping
    local review_prompt="/agent:code-reviewer\\n\\nReview PR #$pr_num - MANDATORY Phase 9 Execution\\n\\nThis is an automated Phase 9 enforcement action triggered by WorkflowManager after PR creation.\\n\\nContext:\\n- PR was just created and requires mandatory code review\\n- This review is part of the automated workflow execution\\n- Phase 9 CANNOT be skipped per WorkflowManager requirements\\n\\nPlease conduct a comprehensive review of all changes in PR #$pr_num."
    
    log "INFO" "Executing: claude -p with single-line prompt for code review"
    
    # Execute the code review using Claude CLI with proper single-line format
    if echo -e "$review_prompt" | claude -p -; then
        log "INFO" "✅ Code reviewer invocation completed successfully"
        return 0
    else
        log "ERROR" "❌ Code reviewer invocation failed"
        return 1
    fi
}

# Function to verify review was posted
verify_review_posted() {
    local pr_num="$1"
    local max_attempts=10
    local attempt=1
    
    log "INFO" "Verifying review was posted for PR #$pr_num..."
    
    while [ $attempt -le $max_attempts ]; do
        log "INFO" "Verification attempt $attempt/$max_attempts"
        
        if check_review_exists "$pr_num"; then
            log "INFO" "✅ Review verification successful!"
            return 0
        fi
        
        log "INFO" "Waiting 10 seconds before retry..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log "ERROR" "❌ Review was not posted after $max_attempts attempts"
    return 1
}

# Main enforcement logic
main() {
    log "INFO" "=== PHASE 9 ENFORCEMENT START ==="
    
    # Step 1: Check if PR exists
    if ! gh pr view "$PR_NUMBER" >/dev/null 2>&1; then
        log "ERROR" "PR #$PR_NUMBER does not exist!"
        exit 1
    fi
    
    log "INFO" "✅ PR #$PR_NUMBER exists"
    
    # Step 2: Wait adaptively for PR to propagate
    log "INFO" "⏱️ Waiting for PR to propagate with adaptive timing..."
    wait_for_pr_propagation "$PR_NUMBER"
    
    # Step 3: Check if review already exists
    if check_review_exists "$PR_NUMBER"; then
        log "INFO" "✅ Review already exists - Phase 9 complete"
        exit 0
    fi
    
    # Step 4: Invoke code reviewer
    log "INFO" "🚨 No review found - ENFORCING Phase 9"
    if ! invoke_code_reviewer "$PR_NUMBER"; then
        log "ERROR" "❌ Failed to invoke code reviewer"
        
        # Retry once
        log "INFO" "🔄 Retrying code reviewer invocation..."
        if ! invoke_code_reviewer "$PR_NUMBER"; then
            log "ERROR" "❌ Second attempt failed - CRITICAL ERROR"
            exit 1
        fi
    fi
    
    # Step 5: Verify review was posted
    if verify_review_posted "$PR_NUMBER"; then
        log "INFO" "✅ PHASE 9 ENFORCEMENT COMPLETE - Review posted successfully"
        
        # Post success comment
        local success_comment="✅ **Phase 9 Complete**

The mandatory code review has been successfully posted for this PR.

**Next Step**: Phase 10 - Code Review Response will be invoked automatically.

*This is an automated WorkflowManager status update.*"
        
        gh pr comment "$PR_NUMBER" --body "$success_comment" || true
        
        exit 0
    else
        log "ERROR" "❌ PHASE 9 ENFORCEMENT FAILED - Review not posted"
        exit 1
    fi
}

# Execute main function
main