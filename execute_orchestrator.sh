#!/bin/bash
# Execute the orchestrator with three parallel tasks

echo "============================================"
echo "ORCHESTRATOR PARALLEL EXECUTION"
echo "============================================"
echo "Tasks to execute:"
echo "  1. Fix all pyright errors"
echo "  2. Complete team coach implementation"
echo "  3. Clean up all worktrees"
echo "============================================"

# Change to main repository directory
cd /Users/ryan/src/gadugi2/gadugi

# Execute the orchestrator directly with the three prompt files
python3 .claude/orchestrator/orchestrator_main.py \
    prompts/fix-all-pyright-errors.md \
    prompts/complete-team-coach-implementation.md \
    prompts/cleanup-all-worktrees.md \
    --parallel \
    --max-workers 3 \
    --verbose

echo "============================================"
echo "Orchestrator execution completed"
echo "============================================"