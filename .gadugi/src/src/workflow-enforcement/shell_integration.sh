#!/bin/bash
# Workflow Enforcement Shell Integration
# Source this file in your shell profile for enhanced workflow support

# Function to validate workflow before common operations
gadugi_validate() {
    local task_desc="${1:-}"
    local files="${@:2}"

    if [[ -n "$task_desc" ]]; then
        python "/Users/ryan/src/gadugi5/gadugi/.gadugi/.gadugi/src/workflow-enforcement/validate-workflow.py" \
            --task "$task_desc" \
            --files $files
    else
        echo "🚨 Gadugi Workflow Enforcement Active"
        echo "💡 Use: gadugi_validate 'task description' [files...]"
    fi
}

# Enhanced git commands with workflow validation
git_with_validation() {
    local git_command="$1"
    shift

    case "$git_command" in
        "commit"|"add"|"rm"|"mv")
            if [[ -z "${GADUGI_ORCHESTRATOR_ACTIVE}" && -z "${GADUGI_EMERGENCY_OVERRIDE}" ]]; then
                echo "⚠️  Git operation detected without orchestrator context"
                echo "   Consider using: python .gadugi/.gadugi/src/orchestrator/main.py"
                read -p "Continue anyway? [y/N]: " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    return 1
                fi
            fi
            ;;
    esac

    command git "$git_command" "$@"
}

# Aliases for common operations
alias gvalidate='gadugi_validate'
alias gwf='gadugi_validate'
alias orchestrator='cd "/Users/ryan/src/gadugi5/gadugi" && python .gadugi/.gadugi/src/orchestrator/main.py'

# Environment variables
export GADUGI_WORKFLOW_ENFORCEMENT_ACTIVE=1
export GADUGI_ENFORCEMENT_DIR="/Users/ryan/src/gadugi5/gadugi/.claude/workflow-enforcement"

echo "✅ Gadugi Workflow Enforcement loaded"
echo "💡 Available commands:"
echo "   gvalidate 'task' [files...]  - Validate workflow compliance"
echo "   orchestrator                 - Launch orchestrator"
