#!/bin/bash
# Start Orchestrator Dashboard for PR Maintenance

cd /Users/ryan/src/gadugi2/gadugi

echo "============================================"
echo "ORCHESTRATOR MONITORING DASHBOARD"
echo "============================================"
echo ""
echo "Starting dashboard for PR maintenance workflow..."
echo "This will monitor parallel PR updates and reviews"
echo ""

# Start the dashboard
python .claude/orchestrator/monitoring/dashboard.py

# Keep terminal open after completion
echo ""
echo "Dashboard terminated. Press any key to close..."
read -n 1
