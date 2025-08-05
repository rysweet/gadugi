#!/bin/bash
"""
Orchestrator Agent Entry Point Script

This script serves as the entry point for Claude agent invocations of the format:
/agent:orchestrator-agent

It bridges the gap between Claude's agent invocation system and the Python
orchestrator implementation, enabling actual parallel execution.

Usage:
  ./run_orchestrator.sh                    # Interactive mode
  ./run_orchestrator.sh --stdin            # Agent invocation mode (reads from stdin)
  ./run_orchestrator.sh file1.md file2.md  # Direct file specification
"""

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Change to project root directory
cd "$PROJECT_ROOT" || {
    echo "Error: Could not change to project root directory: $PROJECT_ROOT"
    exit 1
}

# Verify we're in the correct directory
if [[ ! -f "pyproject.toml" ]] && [[ ! -f "package.json" ]]; then
    echo "Warning: Not in expected project root (no pyproject.toml or package.json found)"
    echo "Current directory: $(pwd)"
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found in PATH"
    exit 1
fi

# Check if required Python packages are available
python3 -c "import psutil" 2>/dev/null || {
    echo "Error: psutil package is required. Install with: pip install psutil"
    exit 1
}

# Set Python path to include orchestrator components
export PYTHONPATH="${PROJECT_ROOT}/.claude/orchestrator:${PROJECT_ROOT}/.claude/shared:${PYTHONPATH}"

# Log orchestrator invocation
echo "🚀 Orchestrator Agent Starting..."
echo "   Project Root: $PROJECT_ROOT"
echo "   Script Dir: $SCRIPT_DIR"
echo "   Args: $*"
echo "   Working Dir: $(pwd)"
echo ""

# Execute the orchestrator CLI with all arguments
exec python3 "${SCRIPT_DIR}/orchestrator_cli.py" "$@"
