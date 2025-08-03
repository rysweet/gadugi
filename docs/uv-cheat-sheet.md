# UV Cheat Sheet for Gadugi

Quick reference for common UV commands used in Gadugi development.

## Essential Commands

### Environment Management
```bash
# Set up project dependencies
uv sync                    # Install core dependencies
uv sync --extra dev        # Install with development dependencies
uv sync --all-extras       # Install all optional dependencies

# Create fresh virtual environment
uv venv                    # Create .venv in current directory
uv venv --force            # Recreate existing environment
uv venv --python 3.11      # Use specific Python version
```

### Dependency Management
```bash
# Add dependencies
uv add pydantic            # Add to core dependencies
uv add --group dev pytest  # Add to dev dependencies
uv add "requests>=2.28"    # Add with version constraint

# Remove dependencies
uv remove pydantic         # Remove from dependencies
uv remove --group dev mypy # Remove from dev dependencies

# Update dependencies
uv lock --upgrade          # Update all dependencies
uv sync --upgrade          # Update and sync dependencies
```

### Running Commands
```bash
# Run Python commands
uv run python script.py    # Run script in UV environment
uv run python -m module    # Run module in UV environment
uv run python -c "code"    # Run inline Python code

# Common development commands
uv run pytest tests/       # Run tests
uv run ruff format .       # Format code
uv run ruff check .        # Run linting
```

## Development Workflow

### Starting Development
```bash
cd gadugi
uv sync --extra dev        # Set up development environment
uv run pytest tests/      # Verify everything works
```

### Daily Development
```bash
# Run tests frequently
uv run pytest tests/integration/  # Run integration tests
uv run pytest tests/shared/       # Run shared module tests
uv run pytest -x                  # Stop on first failure
uv run pytest -v                  # Verbose output

# Code quality
uv run ruff format .              # Format code
uv run ruff check .               # Check style
```

### Adding New Features
```bash
# Add new dependencies as needed
uv add pydantic            # For data validation
uv add --group dev mypy    # For type checking

# Install and test
uv sync                    # Sync new dependencies
uv run pytest tests/      # Test with new dependencies
```

## Testing Commands

### Basic Testing
```bash
uv run pytest                     # Run all tests
uv run pytest tests/              # Run specific directory
uv run pytest tests/test_file.py  # Run specific file
uv run pytest -k "test_name"      # Run tests matching pattern
```

### Test Options
```bash
uv run pytest -v                  # Verbose output
uv run pytest -x                  # Stop on first failure
uv run pytest --tb=short          # Short traceback format
uv run pytest -s                  # Don't capture output
uv run pytest --lf                # Run last failed tests
```

### Coverage Testing
```bash
uv run pytest --cov=.             # Run with coverage
uv run pytest --cov-report=html   # Generate HTML report
uv run pytest --cov-report=term   # Terminal coverage report
```

## Cache and Performance

### Cache Management
```bash
uv cache clean                    # Clear all cached data
uv cache dir                      # Show cache directory
uv cache info                     # Show cache statistics
```

### Performance Commands
```bash
time uv sync                      # Measure sync time
uv lock --offline                 # Use only cached packages
UV_NO_CACHE=1 uv sync            # Disable cache for one command
```

## Python Version Management

### Python Installation
```bash
uv python list                    # List available Python versions
uv python install 3.11            # Install Python 3.11
uv python install 3.12            # Install Python 3.12
```

### Using Different Python Versions
```bash
uv venv --python 3.11             # Create venv with Python 3.11
uv run --python 3.11 pytest      # Run with specific Python version
```

## Lock File Management

### Lock File Operations
```bash
uv lock                           # Generate lock file
uv lock --upgrade                 # Upgrade all dependencies
uv lock --upgrade-package pkg     # Upgrade specific package
```

### Lock File Troubleshooting
```bash
rm uv.lock && uv lock             # Regenerate lock file
uv sync --frozen                  # Sync without updating lock
```

## Project Structure Commands

### Project Information
```bash
uv info                           # Show project information
uv tree                           # Show dependency tree
uv show package                   # Show package information
```

### Configuration
```bash
uv config list                    # Show current configuration
uv config set key value           # Set configuration value
```

## Common Patterns for Gadugi

### Memory Manager Development
```bash
# Work with memory manager
cd .github/memory-manager
uv run python memory_manager.py
uv run python -c "import yaml; print(yaml.__version__)"
```

### Orchestrator Development
```bash
# Test orchestrator components
uv run python .claude/orchestrator/tests/run_tests.py
uv run pytest .claude/orchestrator/tests/
```

### Integration Testing
```bash
# Run full integration test
uv run python test_orchestrator_fix_integration.py

# Run specific integration tests
uv run pytest tests/integration/ -v
```

## Troubleshooting

### Common Issues
```bash
# Command not found
which uv                          # Check if UV is installed
export PATH="$HOME/.local/bin:$PATH"  # Add to PATH

# Module not found
uv sync --extra dev               # Ensure dev dependencies installed
uv run python -c "import sys; print(sys.path)"  # Check Python path

# Tests failing
uv run pytest --tb=long          # Get detailed error information
uv run pytest tests/ -v          # Verbose test output
```

### Reset Environment
```bash
# Complete environment reset
rm -rf .venv uv.lock
uv venv
uv sync --extra dev
```

### Performance Issues
```bash
# Clear cache and retry
uv cache clean
uv sync --extra dev

# Check for dependency conflicts
uv lock --verbose
```

## Environment Variables

### Useful UV Environment Variables
```bash
export UV_CACHE_DIR=~/.cache/uv   # Custom cache directory
export UV_NO_CACHE=1              # Disable caching
export UV_VERBOSE=1               # Enable verbose output
export UV_INDEX_URL=custom-url    # Custom package index
```

### Development Environment Variables
```bash
export PYTHONPATH=.               # Add current directory to Python path
export PYTEST_MARKERS=unit        # Set default pytest markers
```

## CI/CD Integration

### GitHub Actions
```bash
# Install UV in CI
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use the action
- uses: astral-sh/setup-uv@v4
```

### Local CI Simulation
```bash
# Simulate CI environment
UV_NO_CACHE=1 uv sync --extra dev
uv run pytest tests/ --cov=. --cov-report=xml
```

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --extra dev` |
| Run tests | `uv run pytest tests/` |
| Add dependency | `uv add package` |
| Format code | `uv run ruff format .` |
| Sort imports | *(handled by ruff)* |
| Run linting | `uv run ruff check .` |
| Update dependencies | `uv lock --upgrade` |
| Clear cache | `uv cache clean` |
| Reset environment | `rm -rf .venv && uv sync --extra dev` |
| Show help | `uv --help` |

## Next Steps

- See [UV Installation Guide](uv-installation-guide.md) for setup
- Check [UV Migration Guide](uv-migration-guide.md) for team transition
- Read [UV Documentation](https://github.com/astral-sh/uv) for advanced features
