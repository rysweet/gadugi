#!/bin/bash
#
# Test script for Orphaned PR Recovery functionality
#
# This script tests the orphaned_pr_recovery.sh utility to ensure it correctly
# identifies and fixes PRs missing mandatory code reviews.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RECOVERY_SCRIPT="$PROJECT_ROOT/.claude/utils/orphaned_pr_recovery.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Cross-platform date helper function
get_date_minutes_ago() {
    local minutes_ago="$1"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use date -v
        date -v-"${minutes_ago}M" -Iseconds
    else
        # Linux/GNU date - use date -d
        date -d "${minutes_ago} minutes ago" -Iseconds
    fi
}

# Test helper functions
run_test() {
    local test_name="$1"
    local test_function="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Running test: $test_name"

    if $test_function; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "$test_name"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "$test_name"
        return 1
    fi
}

# Mock GitHub CLI for testing
setup_gh_mock() {
    local mock_response="$1"
    local mock_script="/tmp/gh_mock_$$.sh"

    cat > "$mock_script" << EOF
#!/bin/bash
# Mock GitHub CLI for testing

case "\$1 \$2 \$3" in
    "pr list --state")
        echo '$mock_response'
        ;;
    "pr view * --json")
        if [[ "\$2" == "123" ]]; then
            echo '{"reviews": []}'
        elif [[ "\$2" == "124" ]]; then
            echo '{"reviews": [{"author": {"login": "CodeReviewer"}}]}'
        else
            echo '{"reviews": []}'
        fi
        ;;
    "pr comment * --body")
        echo "Comment posted to PR \$2"
        ;;
    *)
        echo "Mock gh: unknown command: \$*" >&2
        exit 1
        ;;
esac
EOF

    chmod +x "$mock_script"
    export PATH="/tmp:$PATH"
    ln -fs "$mock_script" "/tmp/gh"
}

cleanup_gh_mock() {
    rm -f "/tmp/gh_mock_$$".sh
    rm -f "/tmp/gh"
}

# Test cases
test_script_exists() {
    [ -f "$RECOVERY_SCRIPT" ] && [ -x "$RECOVERY_SCRIPT" ]
}

test_help_option() {
    "$RECOVERY_SCRIPT" --help &>/dev/null
}

test_dry_run_option() {
    # Create mock data for orphaned PRs
    local mock_prs='[
        {
            "number": 123,
            "title": "Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Run in dry-run mode
    local output
    output=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 2>&1)

    cleanup_gh_mock

    # Verify dry-run output
    echo "$output" | grep -q "DRY RUN" && echo "$output" | grep -q "Would invoke"
}

test_orphaned_pr_detection() {
    # Create mock data with one orphaned PR and one recent PR
    local mock_prs='[
        {
            "number": 123,
            "title": "Old Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        },
        {
            "number": 124,
            "title": "Recent Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 2)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Run detection
    local output
    output=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 2>&1)

    cleanup_gh_mock

    # Should detect PR 123 (old) but not PR 124 (recent)
    echo "$output" | grep -q "PR #123" && ! echo "$output" | grep -q "PR #124"
}

test_workflow_pr_identification() {
    # Create mock data with workflow and non-workflow PRs
    local mock_prs='[
        {
            "number": 125,
            "title": "Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        },
        {
            "number": 126,
            "title": "Manual Bug Fix",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Run detection
    local output
    output=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 2>&1)

    cleanup_gh_mock

    # Should identify PR 125 as workflow PR, skip PR 126
    echo "$output" | grep -q "PR #125" && echo "$output" | grep -q "workflow-managed"
}

test_max_age_parameter() {
    # Create mock data with PR that's 3 minutes old
    local mock_prs='[
        {
            "number": 127,
            "title": "Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 3)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Test with max-age=2 (should detect)
    local output1
    output1=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=2 2>&1)

    # Test with max-age=5 (should not detect)
    local output2
    output2=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 2>&1)

    cleanup_gh_mock

    # PR should be detected with max-age=2 but not max-age=5
    echo "$output1" | grep -q "PR #127" && ! echo "$output2" | grep -q "PR #127"
}

test_error_handling() {
    # Test with invalid GitHub CLI (simulate gh not available)
    export PATH="/nonexistent:$PATH"

    local output
    if output=$("$RECOVERY_SCRIPT" --dry-run 2>&1); then
        return 1  # Should fail when gh is not available
    else
        echo "$output" | grep -q "gh.*not installed"
    fi
}

test_logging_functionality() {
    # Create mock data
    local mock_prs='[
        {
            "number": 128,
            "title": "Feature Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Run script and check log file
    "$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 &>/dev/null

    cleanup_gh_mock

    # Verify log file was created and contains expected entries
    local log_file="/tmp/orphaned_pr_recovery.log"
    [ -f "$log_file" ] && grep -q "Starting orphaned PR detection" "$log_file"
}

test_state_file_integration() {
    # Test integration with WorkflowManager state files
    local temp_state_dir="/tmp/test_workflow_states"
    local test_task_id="test-task-123"
    local state_file="$temp_state_dir/$test_task_id/state.md"

    mkdir -p "$(dirname "$state_file")"

    # Create a state file indicating PR created but no Phase 9
    cat > "$state_file" << EOF
# WorkflowManager State
Task ID: $test_task_id

## Phase Completion Status
- [x] Phase 8: Pull Request
- [ ] Phase 9: Review

## Active Workflow
- **PR Number**: #129
EOF

    # Create mock for this specific PR
    local mock_prs='[
        {
            "number": 129,
            "title": "State File Test Implementation",
            "author": {"login": "test-user"},
            "createdAt": "'$(get_date_minutes_ago 10)'",
            "reviews": []
        }
    ]'

    setup_gh_mock "$mock_prs"

    # Run recovery
    local output
    output=$("$RECOVERY_SCRIPT" --dry-run --max-age-minutes=5 2>&1)

    cleanup_gh_mock
    rm -rf "$temp_state_dir"

    # Should detect the PR from state file context
    echo "$output" | grep -q "PR #129"
}

# Main test execution
main() {
    log_info "Starting Orphaned PR Recovery Tests"
    log_info "Recovery script: $RECOVERY_SCRIPT"

    # Verify prerequisites
    if ! command -v jq &>/dev/null; then
        log_error "jq is required for tests but not installed"
        exit 1
    fi

    # Run all tests
    run_test "Script exists and is executable" test_script_exists
    run_test "Help option works" test_help_option
    run_test "Dry run option works" test_dry_run_option
    run_test "Orphaned PR detection logic" test_orphaned_pr_detection
    run_test "Workflow PR identification" test_workflow_pr_identification
    run_test "Max age parameter handling" test_max_age_parameter
    run_test "Error handling for missing dependencies" test_error_handling
    run_test "Logging functionality" test_logging_functionality
    run_test "State file integration" test_state_file_integration

    # Test summary
    log_info ""
    log_info "Test Summary:"
    log_info "  Tests run: $TESTS_RUN"
    log_success "  Passed: $TESTS_PASSED"

    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "  Failed: $TESTS_FAILED"
        exit 1
    else
        log_success "All tests passed!"
        exit 0
    fi
}

# Cleanup on exit
trap cleanup_gh_mock EXIT

# Run main function
main "$@"
