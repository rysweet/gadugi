#!/bin/bash
# Dynamic monitoring script for Recipe Executor - finds and monitors active process

echo "=== Recipe Executor Live Monitor ==="
echo "Started at: $(date)"
echo "===================================="

# Find the Claude subprocess for Recipe Executor
find_claude_process() {
    # Look for claude process that's a child of recipe_executor
    ps aux | grep "[c]laude.*recipe" | head -1 | awk '{print $2}'
}

# Find latest log file
find_latest_log() {
    ls -t .recipe_build/logs/recipe_executor*.log 2>/dev/null | head -1
}

# Find output directory
find_output_dir() {
    # Check for most recent self_host directory
    ls -td .recipe_build/self_host_v* 2>/dev/null | head -1
}

CLAUDE_PID=$(find_claude_process)
LOG_FILE=$(find_latest_log)
OUTPUT_DIR=$(find_output_dir)

if [ -z "$CLAUDE_PID" ]; then
    echo "No active Claude process found for Recipe Executor"
    exit 1
fi

if [ -z "$LOG_FILE" ]; then
    echo "No Recipe Executor log file found"
    exit 1
fi

echo "Monitoring:"
echo "  Claude PID: $CLAUDE_PID"
echo "  Log file: $LOG_FILE"
echo "  Output dir: $OUTPUT_DIR"
echo ""

# Function to check process
check_process() {
    if ps -p $CLAUDE_PID > /dev/null 2>&1; then
        echo "✓ Claude process (PID $CLAUDE_PID) is running"
        return 0
    else
        echo "✗ Claude process has ended"
        return 1
    fi
}

# Function to count generated files
count_files() {
    if [ -n "$OUTPUT_DIR" ]; then
        local py_count=$(find "$OUTPUT_DIR" -type f -name "*.py" 2>/dev/null | wc -l)
        local total_count=$(find "$OUTPUT_DIR" -type f 2>/dev/null | wc -l)
        echo "Generated files: $total_count total, $py_count Python files"
        # Also check for files in wrong location
        if [ -d "src/.recipe_build" ]; then
            local alt_count=$(find src/.recipe_build -type f -name "*.py" 2>/dev/null | wc -l)
            if [ $alt_count -gt 0 ]; then
                echo "  ⚠️  Files in alternate location: $alt_count Python files in src/.recipe_build"
            fi
        fi
    fi
}

# Function to show recent activity
show_activity() {
    echo "--- Recent activity ---"
    tail -3 "$LOG_FILE" | grep -E "INFO:|ERROR:" | sed 's/.*INFO: /  /' | sed 's/.*ERROR: /  ❌ /'
}

# Main monitoring loop
while check_process; do
    echo ""
    echo "[$(date +%H:%M:%S)]"
    count_files
    show_activity
    echo "---"
    sleep 30
done

echo ""
echo "=== Execution Complete ==="

# Final statistics
if [ -n "$OUTPUT_DIR" ]; then
    echo "Final file count in $OUTPUT_DIR:"
    find "$OUTPUT_DIR" -type f -name "*.py" 2>/dev/null | wc -l
    echo "Python files generated"
fi

# Check for files in wrong location
if [ -d "src/.recipe_build" ]; then
    ALT_COUNT=$(find src/.recipe_build -type f -name "*.py" 2>/dev/null | wc -l)
    if [ $ALT_COUNT -gt 0 ]; then
        echo ""
        echo "⚠️  WARNING: $ALT_COUNT Python files found in src/.recipe_build (wrong location)"
    fi
fi

# Show any errors from the log
echo ""
echo "=== Checking for errors ==="
grep -i error "$LOG_FILE" | tail -5 || echo "No errors found"

# Show final result
echo ""
echo "=== Final Status ==="
tail -10 "$LOG_FILE" | grep -E "Success:|Failed:|FAILED|complete"