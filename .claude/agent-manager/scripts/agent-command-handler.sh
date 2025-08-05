#!/bin/bash
# agent-command-handler.sh - Handle agent-manager commands from Claude Code

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_MANAGER_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to parse and execute agent-manager commands
handle_agent_command() {
    local full_command="$*"
    
    # Extract the command from various formats
    # Format 1: /agent:agent-manager check-updates
    # Format 2: check-updates
    # Format 3: "check for updates"
    
    local command=""
    local args=""
    
    # Check if it's a direct command
    if [[ "$full_command" =~ ^(check-updates|setup-hooks|status|help)(\s+.*)?$ ]]; then
        command="${BASH_REMATCH[1]}"
        args="${BASH_REMATCH[2]:-}"
    # Check for natural language patterns
    elif [[ "$full_command" =~ check.*update ]]; then
        command="check-updates"
    elif [[ "$full_command" =~ setup.*hook ]]; then
        command="setup-hooks"
    elif [[ "$full_command" =~ (status|info) ]]; then
        command="status"
    elif [[ "$full_command" =~ help ]]; then
        command="help"
    fi
    
    # If no command matched, try to be helpful
    if [ -z "$command" ]; then
        echo "🤔 I couldn't understand the command: '$full_command'"
        echo ""
        echo "Available commands:"
        echo "  • check-updates - Check for available agent updates"
        echo "  • setup-hooks   - Configure startup hooks"
        echo "  • status        - Show agent status"
        echo "  • help          - Show help message"
        echo ""
        echo "Example usage:"
        echo "  /agent:agent-manager check-updates"
        return 1
    fi
    
    # Execute the command
    "$SCRIPT_DIR/agent-manager.sh" "$command" $args
}

# Main entry point
if [ $# -eq 0 ]; then
    # No arguments, show help
    "$SCRIPT_DIR/agent-manager.sh" help
else
    handle_agent_command "$@"
fi