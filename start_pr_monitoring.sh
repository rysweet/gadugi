#!/bin/bash
# PR Monitoring Dashboard for v0.3 Retargeted PRs

cd /Users/ryan/src/gadugi2/gadugi

echo "============================================"
echo "PR MONITORING DASHBOARD - v0.3 REGENERATION"
echo "============================================"
echo ""
echo "Monitoring 14 retargeted PRs..."
echo ""

# Function to check PR status
check_pr_status() {
    local pr=$1
    gh pr view $pr --json number,title,baseRefName,mergeable,state --jq '"\(.number): \(.title) [\(.baseRefName)] Mergeable: \(.mergeable) State: \(.state)"'
}

# Continuous monitoring loop
while true; do
    clear
    echo "============================================"
    echo "PR STATUS DASHBOARD - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""
    
    echo "INFRASTRUCTURE PRs:"
    echo "-------------------"
    check_pr_status 287
    check_pr_status 280
    check_pr_status 278
    echo ""
    
    echo "PYRIGHT ERROR FIX PRs:"
    echo "----------------------"
    check_pr_status 279
    check_pr_status 270
    check_pr_status 286
    check_pr_status 293
    echo ""
    
    echo "FEATURE PRs:"
    echo "------------"
    check_pr_status 282
    check_pr_status 281
    check_pr_status 247
    echo ""
    
    echo "WORKFLOW PRs:"
    echo "-------------"
    check_pr_status 295
    check_pr_status 294
    check_pr_status 269
    check_pr_status 268
    echo ""
    
    echo "Press Ctrl+C to exit"
    echo "Refreshing in 30 seconds..."
    sleep 30
done