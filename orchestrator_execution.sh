#!/bin/bash
# Orchestrator Execution Script
# Executes three critical v0.3 tasks in parallel using WorkflowManager delegation

echo "=================================================="
echo "🎯 ORCHESTRATOR: Starting Parallel Task Execution"
echo "=================================================="
echo ""
echo "Tasks to execute:"
echo "1. Fix Final Pyright Errors (achieve ZERO errors)"
echo "2. Complete Testing Suite (full coverage)"
echo "3. Final Integration Check (system validation)"
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
9. Phase 9: Code Review (invoke code-reviewer)
10. Phase 10: Review Response
11. Phase 11: Settings Update

## Critical Requirements
- This is a UV project - use 'uv run' for ALL Python commands
- All tests MUST pass before PR creation
- Execute all work in the specified worktree

/agent:workflow-manager

Execute complete workflow for task $task_id using prompt file $prompt_file in worktree $worktree_path
EOF

    # Execute via claude CLI with --dangerously-skip-permissions flag
    cd "$worktree_path"
    claude --dangerously-skip-permissions -p /tmp/orchestrator_${task_id}.md > /tmp/${task_id}_output.log 2>&1 &

    echo "   PID: $!"
    echo ""
}

# Execute all three tasks in parallel
echo "📁 Phase 1: Creating worktrees and setting up UV environments..."
echo ""

# Create worktrees for each task
create_worktree() {
    local task_id=$1
    local worktree_path=$2

    if [ -d "$worktree_path" ]; then
        echo "   Worktree already exists: $worktree_path"
    else
        echo "   Creating worktree: $worktree_path"
        git worktree add "$worktree_path" -b "feature/$task_id" || {
            # If branch exists, use it
            git worktree add "$worktree_path" "feature/$task_id"
        }

        # Set up UV environment
        echo "   Setting up UV environment..."
        cd "$worktree_path"
        uv sync --all-extras
        cd - > /dev/null
    fi
}

# Create worktrees
create_worktree "fix-final-pyright-errors" "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-fix-final-pyright-errors"
create_worktree "complete-testing-suite" "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-complete-testing-suite"
create_worktree "final-integration-check" "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-final-integration-check"

echo ""

echo "🚀 Phase 2: Launching parallel WorkflowManager executions..."
echo ""

# Task 1: Fix Final Pyright Errors
execute_task "fix-final-pyright-errors" \
    "fix-final-pyright-errors.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-fix-final-pyright-errors" \
    "Fix Final Pyright Errors - Achieve ZERO errors"

# Task 2: Complete Testing Suite
execute_task "complete-testing-suite" \
    "complete-testing-suite.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-complete-testing-suite" \
    "Complete Testing Suite - Full Coverage"

# Task 3: Final Integration Check
execute_task "final-integration-check" \
    "final-integration-check.md" \
    "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-final-integration-check" \
    "Final Integration Check - System Validation"

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
for task_id in "fix-final-pyright-errors" "complete-testing-suite" "final-integration-check"; do
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
echo "  - /tmp/fix-final-pyright-errors_output.log"
echo "  - /tmp/complete-testing-suite_output.log"
echo "  - /tmp/final-integration-check_output.log"
