#!/bin/bash

# setup-uv-env.sh
# Shared UV virtual environment setup script for Gadugi agents
# 
# This script provides reusable functions for setting up UV virtual environments
# in worktrees, ensuring consistent dependency management across all agents.
#
# Usage:
#   source .claude/scripts/setup-uv-env.sh
#   setup_uv_environment_if_needed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages with colors
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to detect if current directory is a UV project
is_uv_project() {
    if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
        return 0  # true - is UV project
    else
        return 1  # false - not UV project
    fi
}

# Function to check if UV is installed
check_uv_installation() {
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed or not in PATH"
        log_info "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    log_info "UV version: $(uv --version)"
    return 0
}

# Function to verify virtual environment is active
verify_venv_active() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_warning "Virtual environment not detected"
        return 1
    fi
    
    log_success "Virtual environment active: $VIRTUAL_ENV"
    return 0
}

# Function to setup UV virtual environment
setup_uv_environment() {
    local current_dir
    current_dir=$(pwd)
    
    log_info "Setting up UV virtual environment in: $current_dir"
    
    # Check UV installation
    if ! check_uv_installation; then
        return 1
    fi
    
    # Verify we're in a UV project
    if ! is_uv_project; then
        log_error "Not a UV project (missing pyproject.toml or uv.lock)"
        return 1
    fi
    
    log_info "UV project detected, syncing dependencies..."
    
    # Sync dependencies with all extras
    if uv sync --all-extras; then
        log_success "Dependencies synced successfully"
    else
        log_error "Failed to sync dependencies"
        return 1
    fi
    
    # Check if .venv directory exists
    if [[ ! -d ".venv" ]]; then
        log_error "Virtual environment directory .venv not found after sync"
        return 1
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    if source .venv/bin/activate; then
        log_success "Virtual environment activated"
    else
        log_error "Failed to activate virtual environment"
        return 1
    fi
    
    # Verify activation
    if verify_venv_active; then
        log_success "UV virtual environment setup complete"
        
        # Show Python and key package versions for verification
        log_info "Python version: $(uv run python --version)"
        
        # Check if pytest is available (common dependency)
        if uv run python -c "import pytest; print(f'pytest version: {pytest.__version__}')" 2>/dev/null; then
            log_info "pytest available: $(uv run python -c 'import pytest; print(pytest.__version__)')"
        fi
        
        return 0
    else
        log_error "Virtual environment activation verification failed"
        return 1
    fi
}

# Function to run UV command with error handling
run_uv_command() {
    local cmd="$1"
    shift
    local args=("$@")
    
    if ! is_uv_project; then
        log_warning "Not a UV project, running command directly: $cmd ${args[*]}"
        "$cmd" "${args[@]}"
        return $?
    fi
    
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        log_warning "Virtual environment not active, attempting to activate..."
        if ! source .venv/bin/activate; then
            log_error "Failed to activate virtual environment for command: $cmd ${args[*]}"
            return 1
        fi
    fi
    
    log_info "Running UV command: uv run $cmd ${args[*]}"
    uv run "$cmd" "${args[@]}"
}

# Function to run Python with UV
run_python() {
    run_uv_command python "$@"
}

# Function to run pytest with UV
run_pytest() {
    run_uv_command pytest "$@"
}

# Function to run ruff format with UV
run_ruff_format() {
    run_uv_command ruff format "$@"
}

# Function to run ruff check with UV
run_ruff_check() {
    run_uv_command ruff check "$@"
}

# Main function to setup UV environment if needed
setup_uv_environment_if_needed() {
    local force_setup="${1:-false}"
    
    log_info "Checking if UV environment setup is needed..."
    
    # If not a UV project, skip setup
    if ! is_uv_project; then
        log_info "Not a UV project (missing pyproject.toml or uv.lock), skipping UV setup"
        return 0
    fi
    
    # If virtual environment is already active and force is not requested, skip
    if [[ "$force_setup" != "true" ]] && verify_venv_active &>/dev/null; then
        log_success "UV virtual environment already active, skipping setup"
        return 0
    fi
    
    # Setup UV environment
    if setup_uv_environment; then
        log_success "UV environment setup completed successfully"
        return 0
    else
        log_error "UV environment setup failed"
        return 1
    fi
}

# Function to cleanup UV environment (for testing/debugging)
cleanup_uv_environment() {
    log_info "Cleaning up UV environment..."
    
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log_info "Deactivating virtual environment"
        deactivate 2>/dev/null || true
    fi
    
    if [[ -d ".venv" ]]; then
        log_warning "Removing .venv directory"
        rm -rf .venv
    fi
    
    log_success "UV environment cleanup complete"
}

# Function to show UV environment status
show_uv_status() {
    log_info "UV Environment Status:"
    echo "---"
    
    if is_uv_project; then
        log_success "UV project detected (pyproject.toml and uv.lock found)"
    else
        log_warning "Not a UV project"
        return 1
    fi
    
    if command -v uv &> /dev/null; then
        log_success "UV installed: $(uv --version)"
    else
        log_error "UV not installed"
    fi
    
    if [[ -d ".venv" ]]; then
        log_success "Virtual environment directory exists"
    else
        log_warning "Virtual environment directory missing"
    fi
    
    if verify_venv_active &>/dev/null; then
        log_success "Virtual environment is active"
        log_info "Python executable: $(which python)"
        log_info "Python version: $(python --version)"
    else
        log_warning "Virtual environment not active"
    fi
    
    echo "---"
}

# Export functions for use by agents
export -f is_uv_project
export -f check_uv_installation
export -f verify_venv_active
export -f setup_uv_environment
export -f setup_uv_environment_if_needed
export -f run_uv_command
export -f run_python
export -f run_pytest
export -f run_ruff_format
export -f run_ruff_check
export -f cleanup_uv_environment
export -f show_uv_status
export -f log_info
export -f log_success
export -f log_warning
export -f log_error

# If script is run directly (not sourced), show status
if [[ "${BASH_SOURCE[0]:-}" == "${0:-}" ]]; then
    show_uv_status
fi