#!/bin/bash

# Monitor Recipe Executor regeneration progress for 2nd generation

echo "🔄 Monitoring Recipe Executor Regeneration v2"
echo "================================================"
echo ""

LOG_FILE=".recipe_build/logs/recipe_executor_20250824_022136.log"
OUTPUT_DIR=".recipe_build/regenerated/generated_recipe-executor/src"

while true; do
    clear
    echo "🔄 Recipe Executor Regeneration v2 Monitor"
    echo "================================================"
    echo "Time: $(date '+%H:%M:%S')"
    echo ""
    
    # Check if process is still running
    if pgrep -f "claude.*recipe-executor" > /dev/null; then
        echo "✅ Generation process is running"
    else
        echo "⚠️  Generation process not found - may have completed or failed"
    fi
    
    echo ""
    
    # Count generated files
    if [ -d "$OUTPUT_DIR" ]; then
        file_count=$(find "$OUTPUT_DIR" -name "*.py" 2>/dev/null | wc -l)
        echo "📁 Files generated so far: $file_count"
        
        # List recent files
        echo ""
        echo "Recently generated files:"
        find "$OUTPUT_DIR" -name "*.py" -printf "%f\n" 2>/dev/null | tail -5
    else
        echo "⏳ Waiting for output directory to be created..."
    fi
    
    echo ""
    
    # Check latest log activity
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Latest log entries:"
        tail -5 "$LOG_FILE" | grep -E "INFO:|WARNING:|ERROR:" | sed 's/^.*INFO:/INFO:/' | sed 's/^.*WARNING:/⚠️ WARNING:/' | sed 's/^.*ERROR:/❌ ERROR:/'
        
        # Check for completion
        if grep -q "Build complete" "$LOG_FILE" 2>/dev/null; then
            echo ""
            echo "🎉 BUILD COMPLETE!"
            
            # Show summary
            echo ""
            echo "Summary:"
            grep -E "Success:|Failed:|Time:" "$LOG_FILE" | tail -10
            break
        fi
        
        # Check for errors
        if grep -q "ERROR:" "$LOG_FILE" 2>/dev/null; then
            echo ""
            echo "⚠️  Errors detected in log"
        fi
    fi
    
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    sleep 5
done