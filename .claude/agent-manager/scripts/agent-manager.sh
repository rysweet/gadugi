#!/bin/bash
# agent-manager.sh - Main script for Claude Code Agent Updater

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_MANAGER_ROOT="$(dirname "$SCRIPT_DIR")"

# Source required scripts
source "$SCRIPT_DIR/setup-hooks.sh"
source "$SCRIPT_DIR/check-updates.sh"

# Main function to handle commands
main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        setup-hooks)
            setup_startup_hooks "$@"
            ;;
        check-updates)
            check_for_updates "$@"
            ;;
        help|--help|-h)
            echo "Agent Updater - Automatically check and manage agent updates"
            echo ""
            echo "Usage: agent-manager.sh <command> [options]"
            echo ""
            echo "Commands:"
            echo "  setup-hooks    Configure startup hooks in settings.json"
            echo "  check-updates  Check for available agent updates"
            echo "  help           Show this help message"
            echo ""
            echo "Options for check-updates:"
            echo "  --force, -f    Force check even if recently checked"
            ;;
        *)
            echo "Unknown command: $command"
            echo "Run 'agent-manager.sh help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
