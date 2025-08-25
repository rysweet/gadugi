#!/bin/bash

# Cleanup Worktrees Script
# Purpose: Safely remove all Git worktrees except the current one
# Usage: ./cleanup-worktrees.sh [--dry-run] [--force]
#
# Options:
#   --dry-run    Show what would be removed without actually removing
#   --force      Remove worktrees even if they have uncommitted changes
#   --help       Show this help message

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORKTREE_BASE_DIR=".worktrees"
DRY_RUN=false
FORCE_REMOVE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE_REMOVE=true
            shift
            ;;
        --help)
            head -n 11 "$0" | tail -n 9 | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to log messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get the current worktree path
get_current_worktree() {
    local current_dir="$(pwd)"

    # Check if we're in a worktree
    if git rev-parse --git-common-dir >/dev/null 2>&1; then
        local git_common_dir="$(git rev-parse --git-common-dir)"
        local git_dir="$(git rev-parse --git-dir)"

        if [ "$git_common_dir" != "$git_dir" ]; then
            # We're in a worktree
            echo "$current_dir"
            return 0
        fi
    fi

    # Not in a worktree or main repository
    echo ""
    return 1
}

# Function to check if a worktree has uncommitted changes
has_uncommitted_changes() {
    local worktree_path="$1"

    if [ -d "$worktree_path" ]; then
        (cd "$worktree_path" && git status --porcelain 2>/dev/null | grep -q .)
        return $?
    fi

    return 1
}

# Function to remove a single worktree
remove_worktree() {
    local worktree_path="$1"
    local worktree_name="$(basename "$worktree_path")"

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would remove worktree: $worktree_path"
        return 0
    fi

    # Check for uncommitted changes
    if has_uncommitted_changes "$worktree_path" && [ "$FORCE_REMOVE" = false ]; then
        log_warning "Worktree has uncommitted changes: $worktree_name (use --force to remove anyway)"
        return 1
    fi

    # Remove the worktree
    if git worktree remove "$worktree_path" ${FORCE_REMOVE:+--force} 2>/dev/null; then
        log_success "Removed worktree: $worktree_name"
        return 0
    else
        log_error "Failed to remove worktree: $worktree_name"
        return 1
    fi
}

# Main cleanup function
cleanup_worktrees() {
    log_info "Starting worktree cleanup process..."

    # Get current worktree (if any)
    local current_worktree="$(get_current_worktree || echo "")"
    if [ -n "$current_worktree" ]; then
        log_info "Current worktree: $current_worktree"
    else
        log_info "Not currently in a worktree"
    fi

    # Get list of all worktrees
    local worktrees_removed=0
    local worktrees_skipped=0
    local worktrees_failed=0

    log_info "Scanning for worktrees to clean up..."

    # Process each worktree (use git worktree list directly to avoid duplicates)
    while IFS= read -r line; do
        # Parse worktree list output (format: "path commit [branch]")
        local worktree_path="$(echo "$line" | awk '{print $1}')"
        local worktree_branch="$(echo "$line" | sed -n 's/.*\[\(.*\)\].*/\1/p')"

        # Skip if this is the main repository
        if [[ ! "$worktree_path" =~ /$WORKTREE_BASE_DIR/ ]]; then
            continue
        fi

        # Skip if this is the current worktree
        if [ "$worktree_path" = "$current_worktree" ]; then
            log_info "Skipping current worktree: $(basename "$worktree_path")"
            ((worktrees_skipped++))
            continue
        fi

        # Check if worktree is prunable (marked for removal by git)
        if echo "$line" | grep -q "prunable"; then
            log_warning "Worktree is prunable: $(basename "$worktree_path")"
        fi

        # Try to remove the worktree
        if remove_worktree "$worktree_path"; then
            ((worktrees_removed++))
        else
            ((worktrees_failed++))
        fi

    done < <(git worktree list)

    # Run git worktree prune to clean up any remaining references
    if [ "$DRY_RUN" = false ]; then
        log_info "Running git worktree prune..."
        git worktree prune
        log_success "Pruned stale worktree references"
    else
        log_info "[DRY RUN] Would run: git worktree prune"
    fi

    # Summary
    echo ""
    log_info "Cleanup Summary:"
    log_info "  Worktrees removed: $worktrees_removed"
    log_info "  Worktrees skipped: $worktrees_skipped"
    if [ $worktrees_failed -gt 0 ]; then
        log_warning "  Worktrees failed: $worktrees_failed"
    fi

    # Final verification
    echo ""
    log_info "Current worktree status:"
    git worktree list

    if [ $worktrees_failed -gt 0 ]; then
        return 1
    fi

    return 0
}

# Function to clean up branches associated with removed worktrees
cleanup_branches() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would clean up orphaned branches"
        return 0
    fi

    log_info "Cleaning up orphaned branches..."

    # Get list of branches that start with common worktree prefixes
    local branches_deleted=0

    for prefix in "feature/parallel-" "task/" "fix/"; do
        while IFS= read -r branch; do
            # Check if branch is merged
            if git branch --merged main | grep -q "^  $branch$"; then
                if git branch -d "$branch" 2>/dev/null; then
                    log_success "Deleted merged branch: $branch"
                    ((branches_deleted++))
                fi
            fi
        done < <(git branch | grep "^  $prefix" | sed 's/^  //')
    done

    if [ $branches_deleted -gt 0 ]; then
        log_success "Deleted $branches_deleted merged branches"
    else
        log_info "No orphaned branches to clean up"
    fi
}

# Main execution
main() {
    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a Git repository"
        exit 1
    fi

    # Navigate to repository root
    cd "$(git rev-parse --show-toplevel)"

    # Display mode
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY RUN mode - no changes will be made"
    fi

    if [ "$FORCE_REMOVE" = true ]; then
        log_warning "Force mode enabled - will remove worktrees with uncommitted changes"
    fi

    # Perform cleanup
    cleanup_worktrees
    local cleanup_status=$?

    # Optionally clean up branches
    cleanup_branches

    if [ $cleanup_status -eq 0 ]; then
        log_success "Worktree cleanup completed successfully!"
    else
        log_warning "Worktree cleanup completed with some failures"
        exit 1
    fi
}

# Run main function
main "$@"
