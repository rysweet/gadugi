#!/bin/bash
# Orchestrator Execution Script
# Executes three tasks in parallel using WorkflowManager delegation

echo "=================================================="
echo "🎯 ORCHESTRATOR: Starting Parallel Task Execution"
echo "=================================================="
echo ""
echo "Tasks to execute:"
echo "1. Fix All Pyright Errors"
echo "2. Complete Team Coach Implementation"
echo "3. Clean Up All Worktrees"
echo ""

# Function to execute a task via WorkflowManager
execute_task() {
    local task_id=$1
    local prompt_file=$2
    local worktree_path=$3
    local description=$4

    echo "🚀 Starting Task: $task_id"
    echo "   Prompt: $prompt_file"
    echo "   Worktree: $worktree_path"
    echo ""

    # Create WorkflowManager invocation prompt
    cat > /tmp/orchestrator_${task_id}.md <<EOF
# WorkflowManager Task Execution

## Task: $description

## Source Prompt
Execute the workflow for: prompts/$prompt_file

## Worktree Information
- Path: $worktree_path
- Task ID: $task_id

## Requirements
Execute the complete 11-phase workflow:
1. Phase 1: Initial Setup
2. Phase 2: Issue Creation
3. Phase 3: Branch Management
4. Phase 4: Research and Planning
5. Phase 5: Implementation
6. Phase 6: Testing (MUST pass all tests)
7. Phase 7: Documentation
8. Phase 8: Pull Request Creation
9. Phase 9: Code Review (invoke CodeReviewer)
10. Phase 10: Review Response
11. Phase 11: Settings Update

## Critical Requirements
- This is a UV project - use 'uv run' for ALL Python commands
- All tests MUST pass before PR creation
- Execute all work in the specified worktree

/agent:WorkflowManager

Execute complete workflow for task $task_id using prompt file $prompt_file in worktree $worktree_path
EOF

    # Execute via claude CLI
    cd "$worktree_path"
    claude -p /tmp/orchestrator_${task_id}.md > /tmp/${task_id}_output.log 2>&1 &

    echo "   PID: $!"
    echo ""
}

# Execute all three tasks in parallel
echo "📁 Phase 1: Worktrees already created and UV environments set up"
echo ""

echo "🚀 Phase 2: Launching parallel WorkflowManager executions..."
echo ""

# Task 1: Fix Pyright Errors
execute_task "fix-pyright-errors" \
    "fix-all-pyright-errors.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-fix-pyright-errors" \
    "Fix All Pyright Errors"

# Task 2: Complete Team Coach
execute_task "complete-TeamCoach" \
    "complete-TeamCoach-implementation.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-complete-TeamCoach" \
    "Complete Team Coach Implementation"

# Task 3: Cleanup Worktrees
execute_task "cleanup-worktrees" \
    "cleanup-all-worktrees.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-cleanup-worktrees" \
    "Clean Up All Worktrees"

echo "⏳ Phase 3: Monitoring parallel executions..."
echo "   Waiting for all tasks to complete..."
echo ""

# Wait for all background jobs to complete
wait

echo "✅ Phase 4: All tasks completed!"
echo ""

echo "📊 Results Summary:"
echo "==================="

# Check results
for task_id in "fix-pyright-errors" "complete-TeamCoach" "cleanup-worktrees"; do
    if [ -f "/tmp/${task_id}_output.log" ]; then
        echo ""
        echo "Task: $task_id"
        echo "------------------------"
        # Check for success indicators
        if grep -q "Pull request created" "/tmp/${task_id}_output.log" || \
           grep -q "PR created" "/tmp/${task_id}_output.log" || \
           grep -q "Successfully created" "/tmp/${task_id}_output.log"; then
            echo "✅ SUCCESS - PR created"
        else
            echo "❌ FAILED or INCOMPLETE"
        fi

        # Show key outputs
        grep -E "(Issue #|PR #|Pull request #|Phase.*completed)" "/tmp/${task_id}_output.log" | head -5
    fi
done

echo ""
echo "=================================================="
echo "🎉 ORCHESTRATOR: Parallel Execution Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review the PRs created for each task"
echo "2. Merge PRs after approval"
echo "3. Clean up worktrees with: git worktree prune"
echo ""
echo "Log files available at:"
echo "  - /tmp/fix-pyright-errors_output.log"
echo "  - /tmp/complete-TeamCoach_output.log"
echo "  - /tmp/cleanup-worktrees_output.log"
