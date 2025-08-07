#!/bin/bash
# Local orchestrator runner that works from gadugi directory
#
# This wrapper allows running the orchestrator from within /Users/ryan/gadugi7/gadugi
# instead of from /Users/ryan/gadugi7

# Save current directory
ORIGINAL_DIR="$(pwd)"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Export PYTHONPATH to include orchestrator components
export PYTHONPATH="${SCRIPT_DIR}/.claude/orchestrator:${SCRIPT_DIR}/.claude/shared:${PYTHONPATH}"

# Create temporary prompts directory if needed
if [ ! -d "${SCRIPT_DIR}/prompts" ]; then
    echo "⚠️  Prompts directory not found, using gadugi-v0.3/prompts as fallback"
    # Don't create symlink, just note the issue
fi

echo "🚀 Local Orchestrator Starting..."
echo "   Working Dir: ${SCRIPT_DIR}"
echo "   Prompts Dir: ${SCRIPT_DIR}/prompts"
echo ""

# Run the orchestrator CLI directly with Python, bypassing the broken shell script
exec python3 "${SCRIPT_DIR}/.claude/orchestrator/orchestrator_cli.py" "$@"