#!/bin/bash
# UV Virtual Environment Setup Script for Gadugi Agents
# Provides reusable functions for agents to properly handle UV virtual environments in worktrees

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if current directory is a UV project
is_uv_project() {
    if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if UV is installed and available
check_uv_available() {
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed or not in PATH"
        log_info "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi

    log_info "UV version: $(uv --version)"
    return 0
}

# Set up UV virtual environment in current directory
setup_uv_environment() {
    local working_dir="${1:-$(pwd)}"
    local sync_args="${2:---all-extras}"

    log_info "Setting up UV environment in: $working_dir"

    # Change to the working directory
    cd "$working_dir"

    # Verify this is a UV project
    if ! is_uv_project; then
        log_error "Not a UV project (missing pyproject.toml or uv.lock)"
        return 1
    fi

    # Check UV availability
    if ! check_uv_available; then
        return 1
    fi

    # Run UV sync with specified arguments
    log_info "Running: uv sync $sync_args"
    if uv sync $sync_args; then
        log_success "UV environment setup completed"

        # Verify virtual environment was created
        if [[ -d ".venv" ]]; then
            log_success "Virtual environment created at .venv/"

            # Show Python interpreter path
            local python_path
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                python_path=".venv/Scripts/python.exe"
            else
                python_path=".venv/bin/python"
            fi

            if [[ -f "$python_path" ]]; then
                log_info "Python interpreter: $python_path"
                log_info "Python version: $($python_path --version 2>&1)"
            fi
        else
            log_warning "Virtual environment directory not found"
        fi

        return 0
    else
        log_error "UV sync failed"
        return 1
    fi
}

# Activate UV virtual environment (source this function)
activate_uv_environment() {
    local working_dir="${1:-$(pwd)}"

    cd "$working_dir"

    if ! is_uv_project; then
        log_error "Not a UV project"
        return 1
    fi

    # Determine activation script path based on OS
    local activate_script
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        activate_script=".venv/Scripts/activate"
    else
        activate_script=".venv/bin/activate"
    fi

    if [[ -f "$activate_script" ]]; then
        log_info "Activating UV virtual environment"
        source "$activate_script"
        log_success "Virtual environment activated"
        log_info "Python: $(which python)"
        return 0
    else
        log_error "Virtual environment not found at $activate_script"
        log_info "Run setup_uv_environment first"
        return 1
    fi
}

# Run a command with UV (preferred method)
uv_run() {
    local working_dir="$1"
    shift # Remove working_dir from arguments
    local command="$@"

    cd "$working_dir"

    if ! is_uv_project; then
        log_error "Not a UV project"
        return 1
    fi

    log_info "Running in UV environment: $command"
    uv run $command
}

# Run Python commands with UV
uv_run_python() {
    local working_dir="$1"
    shift
    local python_args="$@"

    uv_run "$working_dir" python $python_args
}

# Run pytest with UV
uv_run_pytest() {
    local working_dir="$1"
    shift
    local pytest_args="${@:-tests/}"

    uv_run "$working_dir" pytest $pytest_args
}

# Install additional packages with UV
uv_add_package() {
    local working_dir="$1"
    local package="$2"
    local dev_flag="${3:-}"

    cd "$working_dir"

    if ! is_uv_project; then
        log_error "Not a UV project"
        return 1
    fi

    local cmd="uv add"
    if [[ "$dev_flag" == "--dev" || "$dev_flag" == "--group=dev" ]]; then
        cmd="$cmd --group dev"
    fi
    cmd="$cmd $package"

    log_info "Installing package: $cmd"
    $cmd
}

# Check UV environment health
check_uv_environment() {
    local working_dir="${1:-$(pwd)}"

    cd "$working_dir"

    log_info "Checking UV environment health in: $working_dir"

    # Check if UV project
    if ! is_uv_project; then
        log_error "Not a UV project (missing pyproject.toml or uv.lock)"
        return 1
    fi

    # Check UV availability
    if ! check_uv_available; then
        return 1
    fi

    # Check virtual environment
    if [[ ! -d ".venv" ]]; then
        log_warning "Virtual environment not found - run setup_uv_environment"
        return 1
    fi

    # Check if environment is in sync
    log_info "Checking if environment is in sync..."
    if uv sync --check; then
        log_success "Environment is in sync"
    else
        log_warning "Environment is not in sync - consider running 'uv sync'"
    fi

    # Test basic Python functionality
    if uv run python -c "import sys; print(f'Python {sys.version} ready')"; then
        log_success "UV environment is healthy"
        return 0
    else
        log_error "UV environment has issues"
        return 1
    fi
}

# Clean up UV environment
cleanup_uv_environment() {
    local working_dir="${1:-$(pwd)}"

    cd "$working_dir"

    log_info "Cleaning up UV environment in: $working_dir"

    if [[ -d ".venv" ]]; then
        log_info "Removing virtual environment"
        rm -rf ".venv"
        log_success "Virtual environment removed"
    fi

    # Optionally clean UV cache (commented out by default)
    # log_info "Cleaning UV cache"
    # uv cache clean
}

# Show UV environment information
show_uv_info() {
    local working_dir="${1:-$(pwd)}"

    cd "$working_dir"

    log_info "UV Environment Information for: $working_dir"
    echo "=================================="

    if is_uv_project; then
        echo "✅ UV Project: Yes"

        if [[ -f "pyproject.toml" ]]; then
            echo "📄 pyproject.toml: Found"
            # Show project name if available
            if command -v python &> /dev/null; then
                local project_name
                project_name=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb')).get('project', {}).get('name', 'Unknown'))" 2>/dev/null || echo "Unknown")
                echo "📦 Project Name: $project_name"
            fi
        fi

        if [[ -f "uv.lock" ]]; then
            echo "🔒 uv.lock: Found"
            echo "📊 Lock file size: $(du -h uv.lock | cut -f1)"
        fi

        if [[ -d ".venv" ]]; then
            echo "🐍 Virtual Environment: Found (.venv/)"
            local python_path
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                python_path=".venv/Scripts/python.exe"
            else
                python_path=".venv/bin/python"
            fi

            if [[ -f "$python_path" ]]; then
                echo "🎯 Python: $($python_path --version 2>&1)"
                echo "📍 Python Path: $python_path"
            fi
        else
            echo "❌ Virtual Environment: Not found"
        fi

        if command -v uv &> /dev/null; then
            echo "⚡ UV Version: $(uv --version)"
        else
            echo "❌ UV: Not installed"
        fi

    else
        echo "❌ UV Project: No (missing pyproject.toml or uv.lock)"
    fi

    echo "=================================="
}

# Main function for interactive usage
main() {
    local command="${1:-help}"
    local working_dir="${2:-$(pwd)}"

    case "$command" in
        "setup")
            setup_uv_environment "$working_dir" "${3:---all-extras}"
            ;;
        "check")
            check_uv_environment "$working_dir"
            ;;
        "info")
            show_uv_info "$working_dir"
            ;;
        "cleanup")
            cleanup_uv_environment "$working_dir"
            ;;
        "activate")
            activate_uv_environment "$working_dir"
            ;;
        "run")
            shift 2  # Remove command and working_dir
            uv_run "$working_dir" "$@"
            ;;
        "python")
            shift 2  # Remove command and working_dir
            uv_run_python "$working_dir" "$@"
            ;;
        "pytest")
            shift 2  # Remove command and working_dir
            uv_run_pytest "$working_dir" "$@"
            ;;
        "help"|*)
            echo "UV Environment Setup Script for Gadugi Agents"
            echo ""
            echo "Usage: $0 <command> [working_dir] [args...]"
            echo ""
            echo "Commands:"
            echo "  setup [dir] [sync_args]  - Set up UV environment (default: --all-extras)"
            echo "  check [dir]              - Check UV environment health"
            echo "  info [dir]               - Show UV environment information"
            echo "  cleanup [dir]            - Clean up UV environment"
            echo "  activate [dir]           - Activate UV environment (source this script)"
            echo "  run [dir] <command>      - Run command with UV"
            echo "  python [dir] <args>      - Run Python with UV"
            echo "  pytest [dir] [args]      - Run pytest with UV"
            echo "  help                     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 setup /path/to/worktree"
            echo "  $0 check ."
            echo "  $0 run . pytest tests/"
            echo "  $0 python . -c 'import sys; print(sys.version)'"
            echo ""
            echo "For agents to source functions:"
            echo "  source $0"
            ;;
    esac
}

# If script is executed (not sourced), run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
