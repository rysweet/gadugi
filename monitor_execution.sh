#!/bin/bash
# Monitor Recipe Executor execution

echo "Starting Recipe Executor at $(date)"
echo "============================================"

# Start the Recipe Executor in background
uv run python -m src.recipe_executor execute recipes/recipe-executor \
    --output-dir .recipe_build/self_host_test \
    --verbose 2>&1 | tee .recipe_build/execution_$(date +%s).log &

PID=$!
echo "Recipe Executor PID: $PID"

# Monitor progress
while kill -0 $PID 2>/dev/null; do
    echo -n "."
    sleep 10
done

echo ""
echo "Recipe Executor completed at $(date)"
echo "============================================"

# Check results
if [ -d ".recipe_build/self_host_test/src" ]; then
    echo "Files generated successfully!"
    echo "Counting generated files..."
    find .recipe_build/self_host_test -type f -name "*.py" | wc -l
else
    echo "No files generated - checking logs..."
    tail -20 .recipe_build/execution_*.log
fi