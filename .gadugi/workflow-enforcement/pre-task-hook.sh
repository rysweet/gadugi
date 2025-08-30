#!/bin/bash
# Pre-Task Execution Hook
# Validates workflow compliance before task execution

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW_CHECKER="$SCRIPT_DIR/workflow-checker.py"
HOOK_LOG="$SCRIPT_DIR/hook_execution.log"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$HOOK_LOG"
}

# Function to display colored output
print_colored() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

# Function to check if orchestrator is running
is_orchestrator_context() {
    # Check environment variables that indicate orchestrator execution
    if [[ -n "${GADUGI_ORCHESTRATOR_ACTIVE:-}" ]] || [[ -n "${ORCHESTRATOR_TASK_ID:-}" ]]; then
        return 0
    fi

    # Check for orchestrator process
    if pgrep -f "orchestrator.*main.py" > /dev/null; then
        return 0
    fi

    # Check for workflow manager indicators
    if [[ -n "${WORKFLOW_PHASE:-}" ]] || [[ -n "${GADUGI_WORKFLOW_ID:-}" ]]; then
        return 0
    fi

    return 1
}

# Function to detect potential file modifications
detect_file_modifications() {
    local task_description="$1"
    local files=()

    # Extract potential file patterns from task description
    # This is a heuristic approach - may not catch all cases
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            files+=("$line")
        fi
    done < <(echo "$task_description" | grep -oE '\S+\.(py|js|ts|json|yaml|yml|md|txt|sh|bash|go|java|cpp|c|h)' || true)

    printf '%s\n' "${files[@]}"
}

# Function to show workflow reminder
show_workflow_reminder() {
    print_colored "$BLUE" "🚨 WORKFLOW REMINDER"
    print_colored "$YELLOW" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_colored "$YELLOW" "⚠️  Code changes must use the orchestrator workflow!"
    print_colored "$YELLOW" "📋 All modifications go through 11 validation phases"
    print_colored "$YELLOW" "🔒 This ensures quality, testing, and proper git management"
    print_colored "$YELLOW" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
}

# Function to show correct usage
show_correct_usage() {
    local task_description="$1"

    print_colored "$GREEN" "✅ CORRECT APPROACH:"
    echo "   Use orchestrator for this task:"
    echo
    print_colored "$BLUE" "   cd $REPO_ROOT"
    print_colored "$BLUE" "   python .claude/orchestrator/main.py \\"
    print_colored "$BLUE" "     --task \"$task_description\" \\"
    print_colored "$BLUE" "     --auto-approve"
    echo
    print_colored "$GREEN" "📚 For more info: cat .claude/workflow-enforcement/workflow-reminder.md"
    echo
}

# Function to handle workflow violation
handle_violation() {
    local task_description="$1"
    local files="$2"
    local severity="${3:-medium}"

    show_workflow_reminder

    print_colored "$RED" "❌ WORKFLOW VIOLATION DETECTED"
    print_colored "$RED" "Task: $task_description"

    if [[ -n "$files" ]]; then
        print_colored "$RED" "Files to modify: $files"
    fi

    echo
    show_correct_usage "$task_description"

    # Log the violation
    log_message "VIOLATION" "Task: $task_description | Files: $files | Severity: $severity"

    # Ask user for confirmation
    print_colored "$YELLOW" "Do you want to:"
    print_colored "$YELLOW" "  [o] Use orchestrator (recommended)"
    print_colored "$YELLOW" "  [c] Continue anyway (will be logged)"
    print_colored "$YELLOW" "  [a] Abort task"
    echo
    read -p "Choose [o/c/a]: " -n 1 -r choice
    echo

    case "$choice" in
        [Oo]*)
            print_colored "$GREEN" "✅ Excellent choice! Please use the orchestrator command above."
            exit 1
            ;;
        [Cc]*)
            print_colored "$YELLOW" "⚠️  Continuing with direct execution (logged as violation)"
            log_message "OVERRIDE" "User chose to continue | Task: $task_description"
            return 0
            ;;
        [Aa]*)
            print_colored "$BLUE" "🔄 Task aborted by user"
            exit 1
            ;;
        *)
            print_colored "$RED" "Invalid choice. Aborting for safety."
            exit 1
            ;;
    esac
}

# Main execution
main() {
    local task_description="${1:-}"
    local execution_method="${2:-direct}"

    # Initialize log if it doesn't exist
    if [[ ! -f "$HOOK_LOG" ]]; then
        touch "$HOOK_LOG"
        log_message "INIT" "Hook log initialized"
    fi

    log_message "INFO" "Pre-task hook executed | Task: $task_description | Method: $execution_method"

    # If no task description provided, show general reminder
    if [[ -z "$task_description" ]]; then
        show_workflow_reminder
        print_colored "$BLUE" "💡 Remember to use orchestrator for code changes!"
        exit 0
    fi

    # Check if we're already in orchestrator context
    if is_orchestrator_context; then
        log_message "INFO" "Orchestrator context detected - allowing execution"
        print_colored "$GREEN" "✅ Orchestrator context detected - workflow compliant"
        exit 0
    fi

    # Detect potential file modifications
    local files
    files=$(detect_file_modifications "$task_description")

    # Use workflow checker if available
    if [[ -f "$WORKFLOW_CHECKER" ]]; then
        local files_array=()
        if [[ -n "$files" ]]; then
            mapfile -t files_array <<< "$files"
        fi

        # Run workflow validation
        if python3 "$WORKFLOW_CHECKER" \
            --task "$task_description" \
            --files "${files_array[@]}" \
            --method "$execution_method" 2>/dev/null; then

            print_colored "$GREEN" "✅ Workflow compliance validated"
            log_message "COMPLIANT" "Task: $task_description | Method: $execution_method"
            exit 0
        else
            # Workflow checker detected violation
            handle_violation "$task_description" "$files" "high"
            exit $?
        fi
    else
        # Fallback heuristic validation if workflow checker not available
        log_message "WARNING" "Workflow checker not found - using heuristic validation"

        # Simple heuristic: if files detected and not using orchestrator, it's likely a violation
        if [[ -n "$files" ]] && [[ "$execution_method" != "orchestrator" ]]; then
            handle_violation "$task_description" "$files" "medium"
            exit $?
        fi
    fi

    # If we reach here, execution is likely OK
    print_colored "$GREEN" "✅ Pre-task validation passed"
    log_message "INFO" "Pre-task validation passed for: $task_description"
    exit 0
}

# Help function
show_help() {
    echo "Pre-Task Workflow Enforcement Hook"
    echo
    echo "Usage: $0 [TASK_DESCRIPTION] [EXECUTION_METHOD]"
    echo
    echo "Arguments:"
    echo "  TASK_DESCRIPTION    Description of the task to be executed"
    echo "  EXECUTION_METHOD    'orchestrator', 'direct', or 'unknown' (default: direct)"
    echo
    echo "Examples:"
    echo "  $0 'Fix bug in auth module' orchestrator"
    echo "  $0 'Read configuration files' direct"
    echo "  $0  # Show general workflow reminder"
    echo
    echo "Environment Variables:"
    echo "  GADUGI_ORCHESTRATOR_ACTIVE    Set when orchestrator is running"
    echo "  ORCHESTRATOR_TASK_ID          Current orchestrator task ID"
    echo "  WORKFLOW_PHASE                Current workflow phase"
    echo "  GADUGI_WORKFLOW_ID            Current workflow execution ID"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
