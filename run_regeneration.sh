#!/bin/bash

# Recipe Executor Self-Regeneration Script
# Purpose: Run Recipe Executor to regenerate itself and verify success

set -e  # Exit on error

echo "=================================================="
echo "Recipe Executor Self-Regeneration Test"
echo "=================================================="
echo ""

# 1. Check current state
echo "📋 Current State Check:"
echo "----------------------"
if [ -d "src/recipe_executor" ]; then
    echo "✅ Recipe Executor source exists"
    file_count=$(find src/recipe_executor -name "*.py" | wc -l)
    echo "   Found $file_count Python files"
else
    echo "❌ Recipe Executor source missing!"
    exit 1
fi

# 2. Create output directory for regeneration
OUTPUT_DIR=".recipe_build/regenerated"
echo ""
echo "📁 Creating output directory: $OUTPUT_DIR"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 3. Run Recipe Executor to regenerate itself
echo ""
echo "🚀 Starting Self-Regeneration:"
echo "------------------------------"
echo "Command: python -m src.recipe_executor recipes/recipe-executor/requirements.md --output-dir=$OUTPUT_DIR --verbose"
echo ""

# Run with proper error handling
if python -m src.recipe_executor recipes/recipe-executor/requirements.md \
    --output-dir="$OUTPUT_DIR" \
    --verbose \
    --force-rebuild; then
    
    echo ""
    echo "✅ Regeneration command completed successfully"
else
    echo ""
    echo "❌ Regeneration failed with exit code: $?"
    echo "Check logs in .recipe_build/logs/"
    exit 1
fi

# 4. Verify generated files
echo ""
echo "📊 Verification:"
echo "---------------"

# Check if files were generated
if [ -d "$OUTPUT_DIR/src/recipe_executor" ]; then
    generated_count=$(find "$OUTPUT_DIR/src/recipe_executor" -name "*.py" | wc -l)
    echo "✅ Generated $generated_count Python files"
    
    # List key files
    echo ""
    echo "Key files generated:"
    for file in orchestrator.py claude_code_generator.py validator.py state_manager.py; do
        if [ -f "$OUTPUT_DIR/src/recipe_executor/$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (missing)"
        fi
    done
else
    echo "❌ No Recipe Executor files generated!"
    exit 1
fi

# 5. Run quality checks on generated code
echo ""
echo "🔍 Quality Checks:"
echo "-----------------"

# Check for stubs
echo -n "Checking for stub implementations... "
stub_count=$(grep -r "raise NotImplementedError\|pass  # TODO\|# STUB" "$OUTPUT_DIR" 2>/dev/null | wc -l || echo 0)
if [ "$stub_count" -eq 0 ]; then
    echo "✅ No stubs detected"
else
    echo "⚠️  Found $stub_count potential stubs"
    echo "   Running intelligent stub detection..."
fi

# Check for syntax errors
echo -n "Checking Python syntax... "
if python -m py_compile "$OUTPUT_DIR/src/recipe_executor/orchestrator.py" 2>/dev/null; then
    echo "✅ Valid Python syntax"
else
    echo "❌ Syntax errors detected"
fi

# 6. Compare with original (optional)
echo ""
echo "📈 Comparison with Original:"
echo "---------------------------"
original_lines=$(wc -l < src/recipe_executor/orchestrator.py)
if [ -f "$OUTPUT_DIR/src/recipe_executor/orchestrator.py" ]; then
    generated_lines=$(wc -l < "$OUTPUT_DIR/src/recipe_executor/orchestrator.py")
    echo "Original orchestrator.py: $original_lines lines"
    echo "Generated orchestrator.py: $generated_lines lines"
    
    if [ "$generated_lines" -gt 100 ]; then
        echo "✅ Substantial implementation generated"
    else
        echo "⚠️  Generated file seems small"
    fi
fi

# 7. Summary
echo ""
echo "=================================================="
echo "Summary:"
echo "=================================================="

if [ "$stub_count" -eq 0 ] && [ "$generated_count" -gt 10 ]; then
    echo "🎉 SUCCESS: Recipe Executor successfully regenerated itself!"
    echo "Generated code is in: $OUTPUT_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Review generated code in $OUTPUT_DIR"
    echo "2. Run tests: cd $OUTPUT_DIR && python -m pytest tests/"
    echo "3. Compare with original: diff -u src/ $OUTPUT_DIR/src/"
else
    echo "⚠️  PARTIAL SUCCESS: Regeneration completed but needs review"
    echo "- Check for stubs or incomplete implementations"
    echo "- Review logs in .recipe_build/logs/"
fi

echo ""
echo "Log file: .recipe_build/logs/recipe_executor_*.log"
echo "=================================================="