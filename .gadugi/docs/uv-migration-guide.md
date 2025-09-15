# UV Migration Guide for Gadugi Team

This guide helps team members transition from pip-based workflows to UV (Ultraviolet) for Python dependency management in the Gadugi project.

## Quick Migration Checklist

- [ ] Install UV on your system
- [ ] Pull the latest changes with UV configuration
- [ ] Run `uv sync --extra dev` to set up the environment
- [ ] Update your development workflow to use `uv run` commands
- [ ] Test that all your existing workflows work with UV

## Before Migration

### What You Had Before
```bash
# Old workflow
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r .github/MemoryManager/requirements.txt
pip install pytest pytest-cov black isort flake8
python -m pytest tests/
```

### What You Get After
```bash
# New workflow
uv sync --extra dev
uv run pytest tests/
```

That's it! UV handles virtual environment creation, dependency installation, and environment activation automatically.

## Step-by-Step Migration

### Step 1: Install UV

Follow the [UV Installation Guide](uv-installation-guide.md) for your platform.

**Quick install (macOS/Linux):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Update Your Local Repository

```bash
git fetch origin
git checkout main
git pull origin main

# If you were working on a feature branch, rebase it
git checkout your-feature-branch
git rebase main
```

### Step 3: Set Up UV Environment

```bash
# Install all dependencies (core + development)
uv sync --extra dev

# Or install only core dependencies
uv sync
```

This command:
- Creates a virtual environment in `.venv/`
- Installs all dependencies from `pyproject.toml`
- Uses the `uv.lock` file for exact versions

### Step 4: Update Your Development Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `source venv/bin/activate` | Not needed | UV manages activation automatically |
| `pip install package` | `uv add package` | Automatically updates pyproject.toml |
| `pip install -r requirements.txt` | `uv sync` | Uses pyproject.toml instead |
| `python script.py` | `uv run python script.py` | Runs in UV environment |
| `pytest tests/` | `uv run pytest tests/` | Runs tests in UV environment |
| `black .` | `uv run black .` | Runs formatter in UV environment |
| `pip freeze > requirements.txt` | `uv lock` | Updates uv.lock automatically |

### Step 5: IDE Configuration

#### VS Code
1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Run "Python: Select Interpreter"
3. Choose the interpreter in `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

#### PyCharm
1. Go to Settings/Preferences → Project → Python Interpreter
2. Click the gear icon → Add
3. Select "Existing environment"
4. Point to `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

#### Other IDEs
Most IDEs will automatically detect the `.venv` directory. If not, manually point to `.venv/bin/python`.

## Common Workflows

### Daily Development

```bash
# Start working
cd gadugi
uv sync --extra dev  # Only needed if dependencies changed

# Run tests
uv run pytest tests/

# Format code
uv run ruff format .

# Run linting
uv run ruff check .

# Add a new dependency
uv add requests

# Add a development dependency
uv add --group dev mypy

# Run a script
uv run python my_script.py
```

### Working with Dependencies

```bash
# Add a new production dependency
uv add pydantic

# Add a development dependency
uv add --group dev pytest-xdist

# Remove a dependency
uv remove requests

# Update all dependencies
uv lock --upgrade

# Sync dependencies after pulling changes
uv sync
```

### Testing Workflows

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_specific.py

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html

# Run integration tests only
uv run pytest tests/integration/

# Run tests in parallel
uv add --group dev pytest-xdist
uv run pytest tests/ -n auto
```

## Performance Improvements You'll See

### Installation Speed
- **Before**: 30-60 seconds for full environment setup
- **After**: 5-15 seconds for full environment setup
- **Improvement**: 50-80% faster

### CI/CD Performance
- **Before**: 2-4 minutes for dependency installation
- **After**: 30-90 seconds for dependency installation
- **Improvement**: 60-75% faster

### Developer Experience
- **No virtual environment activation** - UV handles it automatically
- **Automatic dependency updates** - pyproject.toml and uv.lock stay in sync
- **Faster environment switching** - UV reuses environments efficiently
- **Better error messages** - UV provides clearer dependency resolution errors

## Troubleshooting Migration Issues

### "uv: command not found"
```bash
# Add UV to your PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or install UV again
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Module not found" errors
```bash
# Make sure you're using uv run
uv run python script.py  # NOT: python script.py

# Or sync dependencies
uv sync --extra dev
```

### Tests failing after migration
```bash
# Make sure you have dev dependencies
uv sync --extra dev

# Run tests with UV
uv run pytest tests/

# Check if pytest markers are configured
uv run pytest --markers
```

### Lock file conflicts during git merge
```bash
# Delete lock file and regenerate
rm uv.lock
uv lock

# Or use UV's resolution
uv lock --upgrade
```

### IDE not recognizing packages
1. Make sure your IDE is pointing to `.venv/bin/python`
2. Restart your IDE after changing interpreter
3. Clear IDE caches if available

## Advanced Usage

### Multiple Python Versions
```bash
# Install specific Python version
uv python install 3.11

# Create environment with specific Python
uv venv --python 3.11

# List available Python versions
uv python list
```

### Custom Scripts
Add scripts to `pyproject.toml`:
```toml
[project.scripts]
gadugi-test = "pytest"
gadugi-format = "black ."
```

Then run:
```bash
uv run gadugi-test
uv run gadugi-format
```

### Environment Variables
```bash
# Set environment variables
UV_EXTRA_INDEX_URL=https://test.pypi.org/simple uv sync

# Or use .env files (supported automatically)
echo "PYTHONPATH=." > .env
uv run python script.py
```

## Team Coordination

### For Team Leads
1. **Communicate the change** - Share this guide with the team
2. **Set a migration deadline** - Give team 1-2 weeks to migrate
3. **Update CI/CD first** - Ensure automated systems work
4. **Provide support** - Help team members with migration issues

### For Team Members
1. **Install UV immediately** - Don't wait until you need it
2. **Test your workflows** - Try your common development tasks
3. **Ask questions early** - Don't struggle silently
4. **Share feedback** - Report any issues or improvements

### For Code Reviews
- **uv.lock changes are normal** - Don't worry about large lock file diffs
- **Check pyproject.toml changes** - These are the important dependency changes
- **Test locally with UV** - Make sure changes work with UV environment

## Getting Help

If you encounter issues during migration:

1. **Check this guide** - Many common issues are covered here
2. **Try the [UV Cheat Sheet](uv-cheat-sheet.md)** - Quick command reference
3. **Ask the team** - Someone else may have solved the same issue
4. **Create an issue** - Document problems for the team
5. **Check UV docs** - https://github.com/astral-sh/uv

## Success Indicators

You've successfully migrated when:
- [ ] You can run `uv --version` successfully
- [ ] `uv sync --extra dev` completes without errors
- [ ] `uv run pytest tests/` passes existing tests
- [ ] Your IDE recognizes packages in the UV environment
- [ ] You're using `uv run` for all Python commands
- [ ] You can add dependencies with `uv add package`

Welcome to faster Python development with UV! 🚀
