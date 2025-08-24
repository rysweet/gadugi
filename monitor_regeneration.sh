#!/bin/bash

# Monitor Recipe Executor regeneration progress
# Shows real-time logs and progress indicators

set -e

echo "=================================================="
echo "Recipe Executor Regeneration Monitor"
echo "=================================================="
echo ""

# Find the latest log file
LOG_DIR=".recipe_build/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Log directory not found: $LOG_DIR"
    echo "Run regeneration first: ./run_regeneration.sh"
    exit 1
fi

LATEST_LOG=$(ls -t "$LOG_DIR"/recipe_executor_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log files found"
    echo "Run regeneration first: ./run_regeneration.sh"
    exit 1
fi

echo "📋 Monitoring log: $LATEST_LOG"
echo ""
echo "Key indicators to watch:"
echo "  🔍 'Validating implementation' - Stub detection in progress"
echo "  🤖 'Generating code with Claude' - AI generation active"
echo "  ✅ 'Implementation validated' - Component passed validation"
echo "  ⚠️  'WARNING' - Potential issues detected"
echo "  ❌ 'ERROR' - Failures that need attention"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "--------------------------------------------------"
echo ""

# Function to show progress summary
show_summary() {
    echo ""
    echo "--------------------------------------------------"
    echo "Summary of current run:"
    echo ""
    
    # Count key events
    validations=$(grep -c "Validating implementation" "$LATEST_LOG" 2>/dev/null || echo 0)
    generations=$(grep -c "Generating code with Claude" "$LATEST_LOG" 2>/dev/null || echo 0)
    validated=$(grep -c "Implementation validated" "$LATEST_LOG" 2>/dev/null || echo 0)
    warnings=$(grep -c "WARNING" "$LATEST_LOG" 2>/dev/null || echo 0)
    errors=$(grep -c "ERROR" "$LATEST_LOG" 2>/dev/null || echo 0)
    
    echo "  Validations started: $validations"
    echo "  Code generations: $generations"
    echo "  Validated components: $validated"
    echo "  Warnings: $warnings"
    echo "  Errors: $errors"
    
    # Check for stub detection
    if grep -q "STUB DETECTED" "$LATEST_LOG" 2>/dev/null; then
        stub_count=$(grep -c "STUB DETECTED" "$LATEST_LOG")
        echo ""
        echo "  ⚠️  Stubs detected: $stub_count"
        echo "     (Intelligent detection should remediate these)"
    fi
    
    # Check for completion
    if grep -q "Build complete" "$LATEST_LOG" 2>/dev/null; then
        echo ""
        echo "  🎉 Build completed!"
    fi
    
    echo "--------------------------------------------------"
}

# Trap Ctrl+C to show summary before exit
trap show_summary EXIT

# Follow the log with highlighted output
tail -f "$LATEST_LOG" | while read line; do
    # Color code the output
    if echo "$line" | grep -q "ERROR"; then
        echo -e "\033[31m$line\033[0m"  # Red for errors
    elif echo "$line" | grep -q "WARNING"; then
        echo -e "\033[33m$line\033[0m"  # Yellow for warnings
    elif echo "$line" | grep -q "Implementation validated"; then
        echo -e "\033[32m$line\033[0m"  # Green for success
    elif echo "$line" | grep -q "Generating code with Claude"; then
        echo -e "\033[36m$line\033[0m"  # Cyan for AI generation
    elif echo "$line" | grep -q "STUB DETECTED"; then
        echo -e "\033[35m$line\033[0m"  # Magenta for stub detection
    else
        echo "$line"
    fi
done