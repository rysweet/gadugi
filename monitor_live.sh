#!/bin/bash
# Live monitoring script for Recipe Executor

echo "=== Recipe Executor Live Monitor ==="
echo "Started at: $(date)"
echo "===================================="

# Function to check process
check_process() {
    if ps -p 1837630 > /dev/null 2>&1; then
        echo "✓ Claude process (PID 1837630) is running"
        return 0
    else
        echo "✗ Claude process has ended"
        return 1
    fi
}

# Function to count generated files
count_files() {
    local count=$(find .recipe_build/self_host_test/generated_recipe-executor -type f 2>/dev/null | wc -l)
    echo "Generated files: $count"
}

# Function to show last log entries
show_logs() {
    echo "--- Last 5 log entries ---"
    tail -5 .recipe_build/logs/recipe_executor_20250826_035910.log | cut -d'-' -f5-
}

# Main monitoring loop
while check_process; do
    echo ""
    echo "[$(date +%H:%M:%S)]"
    count_files
    show_logs
    echo "---"
    sleep 15
done

echo ""
echo "=== Execution Complete ==="
echo "Final file count:"
find .recipe_build/self_host_test/generated_recipe-executor -type f -name "*.py" 2>/dev/null | wc -l
echo "Python files generated"

# Show any errors from the log
echo ""
echo "=== Checking for errors ==="
grep -i error .recipe_build/logs/recipe_executor_20250826_035910.log | tail -5 || echo "No errors found"