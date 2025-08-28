#!/bin/bash

# Single monitoring script for Recipe Executor self-hosting

echo "=========================================="
echo "Recipe Executor Self-Hosting Monitor"
echo "NO TIMEOUT - Patient Mode"
echo "=========================================="
echo ""

# Function to count files
count_files() {
    local dir="$1"
    local pattern="$2"
    find "$dir" -type f -name "$pattern" 2>/dev/null | wc -l
}

# The self-host output directory
BUILD_DIR=".recipe_build/self_host"

# Monitor loop
while true; do
    clear
    echo "=========================================="
    echo "Recipe Executor Self-Hosting Monitor"
    echo "NO TIMEOUT - Patient Mode"
    echo "=========================================="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Check if Recipe Executor process is running
    if pgrep -f "recipe_executor.*self-host" > /dev/null; then
        echo "✅ Recipe Executor Self-Host: RUNNING"
    else
        echo "⚠️  Recipe Executor Self-Host: NOT RUNNING"
    fi
    
    # Check if Claude process is running
    if pgrep -f "claude" > /dev/null; then
        echo "✅ Claude Code Generator: RUNNING (NO TIMEOUT)"
    else
        echo "⚠️  Claude Code Generator: NOT RUNNING"
    fi
    echo ""
    
    # Show latest log activity
    LOG_FILE=$(ls -t .recipe_build/logs/recipe_executor_*.log 2>/dev/null | head -1)
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Latest Activity from $(basename $LOG_FILE):"
        tail -5 "$LOG_FILE" | while read line; do
            if echo "$line" | grep -q "creating file:"; then
                filename=$(echo "$line" | sed 's/.*creating file: //')
                echo "  ✨ Creating: $filename"
            elif echo "$line" | grep -q "using tool:"; then
                tool=$(echo "$line" | sed 's/.*using tool: //')
                echo "  🔧 Tool: $tool"
            elif echo "$line" | grep -q "PASSED"; then
                echo "  ✅ Stage PASSED"
            elif echo "$line" | grep -q "FAILED"; then
                echo "  ❌ Stage FAILED"
            elif echo "$line" | grep -q "iteration"; then
                echo "  🔄 $line"
            else
                msg=$(echo "$line" | sed 's/.*INFO - //' | head -c 60)
                [ -n "$msg" ] && echo "  📝 $msg..."
            fi
        done
    fi
    echo ""
    
    # Check build directory
    if [ -d "$BUILD_DIR" ]; then
        echo "📂 Build Directory: $BUILD_DIR"
        
        # Count files
        py_files=$(count_files "$BUILD_DIR" "*.py")
        test_files=$(count_files "$BUILD_DIR/tests" "test_*.py")
        total_files=$(find "$BUILD_DIR" -type f ! -path "*/.*" 2>/dev/null | wc -l)
        
        echo "  📊 Statistics:"
        echo "    • Total files: $total_files"
        echo "    • Python modules: $py_files"
        echo "    • Test files: $test_files"
        echo ""
        
        # Show structure
        echo "  📁 Structure:"
        if [ -d "$BUILD_DIR/src/recipe_executor" ]; then
            src_count=$(ls -1 "$BUILD_DIR/src/recipe_executor/"*.py 2>/dev/null | wc -l)
            echo "    • src/recipe_executor/: $src_count files"
            ls -1 "$BUILD_DIR/src/recipe_executor/"*.py 2>/dev/null | head -5 | while read f; do
                size=$(du -h "$f" | cut -f1)
                echo "      - $(basename $f) ($size)"
            done
        fi
        
        if [ -d "$BUILD_DIR/tests" ]; then
            test_count=$(ls -1 "$BUILD_DIR/tests/"*.py 2>/dev/null | wc -l)
            echo "    • tests/: $test_count files"
        fi
        
        # Check for key files
        echo ""
        echo "  🔍 Key Files:"
        [ -f "$BUILD_DIR/pyproject.toml" ] && echo "    ✓ pyproject.toml"
        [ -f "$BUILD_DIR/pyrightconfig.json" ] && echo "    ✓ pyrightconfig.json"
        [ -f "$BUILD_DIR/src/recipe_executor/__init__.py" ] && echo "    ✓ __init__.py"
        [ -f "$BUILD_DIR/src/recipe_executor/orchestrator.py" ] && echo "    ✓ orchestrator.py"
        [ -f "$BUILD_DIR/src/recipe_executor/recipe_model.py" ] && echo "    ✓ recipe_model.py"
        [ -f "$BUILD_DIR/src/recipe_executor/recipe_parser.py" ] && echo "    ✓ recipe_parser.py"
    else
        echo "📂 Build directory not yet created"
    fi
    echo ""
    
    # Show Claude log size if exists
    CLAUDE_LOG=$(ls -t .recipe_build/prompts/claude_*.log 2>/dev/null | head -1)
    if [ -f "$CLAUDE_LOG" ]; then
        log_lines=$(wc -l < "$CLAUDE_LOG")
        log_size=$(du -h "$CLAUDE_LOG" | cut -f1)
        echo "📊 Claude Output:"
        echo "  Log: $(basename $CLAUDE_LOG)"
        echo "  Lines: $log_lines"
        echo "  Size: $log_size"
        
        # Show if Claude is actually writing files
        if grep -q "Write tool" "$CLAUDE_LOG" 2>/dev/null; then
            echo "  🔧 Claude is using Write tool"
        fi
    fi
    
    echo ""
    echo "=========================================="
    echo "NO TIMEOUT - Being patient with Claude..."
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing every 5 seconds..."
    
    sleep 5
done