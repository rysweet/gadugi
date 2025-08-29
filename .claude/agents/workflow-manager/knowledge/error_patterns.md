# Common Workflow Error Patterns and Solutions


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Git-Related Errors

### Merge Conflicts
**Pattern**: `merge conflict|CONFLICT|both modified`
**Common Causes**:
- Multiple developers editing same lines
- Outdated branch not synced with main
- Auto-generated files in version control

**Solutions**:
```bash
# Prevention
git pull origin main  # Before starting work
git rebase main       # Keep branch current

# Resolution
git status            # See conflicted files
# Edit files to resolve conflicts
git add .             # Stage resolved files
git commit            # Complete merge/rebase
```

**Recovery Strategies**:
- Abort merge: `git merge --abort`
- Abort rebase: `git rebase --abort`
- Use merge tool: `git mergetool`

### Branch Not Found
**Pattern**: `branch.*not found|does not exist|no such ref`
**Common Causes**:
- Typo in branch name
- Branch deleted by other developer
- Working in wrong repository

**Solutions**:
```bash
# List all branches
git branch -a

# Fetch latest from remote
git fetch origin

# Create branch if it should exist
git checkout -b missing-branch-name
```

### Detached HEAD State
**Pattern**: `detached HEAD|HEAD detached`
**Common Causes**:
- Checking out specific commit
- Switching to tag instead of branch
- Result of certain rebase operations

**Solutions**:
```bash
# Create branch from current state
git checkout -b new-branch-name

# Or return to a branch
git checkout main
```

### Authentication Failures
**Pattern**: `authentication failed|permission denied|403|401`
**Common Causes**:
- Expired tokens
- Wrong credentials
- Repository access revoked
- SSH key issues

**Solutions**:
```bash
# Check SSH connection
ssh -T git@github.com

# Update remote URL to HTTPS
git remote set-url origin https://github.com/user/repo.git

# Re-authenticate with Git credential helper
git config --global credential.helper store
```

## Build and Environment Errors

### Dependency Issues
**Pattern**: `module.*not found|import.*error|no module named|dependency.*missing`
**Common Causes**:
- Missing package installation
- Wrong Python environment
- Outdated requirements
- Package version conflicts

**Solutions**:
```bash
# For UV projects
uv sync
uv add package-name

# For pip projects
pip install -r requirements.txt
pip install package-name

# Check environment
which python
python --version
pip list
```

### Virtual Environment Problems
**Pattern**: `command not found|not in PATH|wrong python version`
**Common Causes**:
- Virtual environment not activated
- Wrong environment selected
- Environment corruption

**Solutions**:
```bash
# UV environment
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or use UV run directly
uv run python script.py
uv run pytest
```

### Build Tool Errors
**Pattern**: `build failed|compilation error|make.*error`
**Common Causes**:
- Missing build dependencies
- Incompatible tool versions
- Corrupted build cache

**Solutions**:
```bash
# Clean and rebuild
make clean && make
npm run clean && npm run build

# Clear caches
rm -rf node_modules && npm install
pip cache purge
```

## Testing Errors

### Test Discovery Issues
**Pattern**: `no tests found|test discovery failed|collection failed`
**Common Causes**:
- Wrong test naming convention
- Missing `__init__.py` files
- Incorrect test directory structure
- Configuration file issues

**Solutions**:
```bash
# Check test structure
find . -name "*test*.py"

# Run with verbose discovery
pytest -v --collect-only

# Fix naming (tests must start with 'test_' or end with '_test.py')
mv testfile.py test_file.py
```

### Import Errors in Tests
**Pattern**: `import.*error.*test|module.*not found.*test`
**Common Causes**:
- Wrong PYTHONPATH
- Missing test dependencies
- Circular imports

**Solutions**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install test dependencies
uv add --dev pytest pytest-cov

# Use relative imports in tests
from ..module import function
```

### Test Data Issues
**Pattern**: `fixture.*not found|test data.*missing|database.*error`
**Common Causes**:
- Missing test fixtures
- Database not initialized
- Test data cleanup issues

**Solutions**:
```bash
# Create test fixtures
@pytest.fixture
def sample_data():
    return {"key": "value"}

# Database setup for tests
pytest --setup-only
```

## Type Checking Errors

### MyPy/Pyright Errors
**Pattern**: `type.*error|incompatible types|cannot assign`
**Common Causes**:
- Missing type annotations
- Incorrect type hints
- Version mismatches

**Solutions**:
```python
# Add proper type hints
def function(param: str) -> int:
    return len(param)

# Use Optional for nullable values
from typing import Optional
def maybe_none() -> Optional[str]:
    return None

# Type ignore for complex cases
result = complex_function()  # type: ignore
```

### Missing Type Stubs
**Pattern**: `missing library stubs|no library stub file`
**Common Causes**:
- Third-party library without type hints
- Missing types-* packages

**Solutions**:
```bash
# Install type stubs
uv add --dev types-requests
uv add --dev types-PyYAML

# Or ignore missing stubs
# mypy: ignore-missing-imports
```

## CI/CD Pipeline Errors

### GitHub Actions Failures
**Pattern**: `action.*failed|workflow.*failed|step.*failed`
**Common Causes**:
- Wrong YAML syntax
- Missing secrets/environment variables
- Dependency version conflicts
- Timeout issues

**Solutions**:
```yaml
# Add timeout and error handling
- name: Run tests
  run: pytest
  timeout-minutes: 10
  continue-on-error: false

# Debug with tmate
- name: Debug with tmate
  uses: mxschmitt/action-tmate@v3
  if: failure()
```

### Docker Build Issues
**Pattern**: `docker.*build.*failed|dockerfile.*error`
**Common Causes**:
- Invalid Dockerfile syntax
- Missing base image
- Permission issues
- Build context too large

**Solutions**:
```dockerfile
# Use .dockerignore
node_modules
.git
*.log

# Multi-stage builds for smaller images
FROM python:3.11-slim as builder
# build steps
FROM python:3.11-slim as runtime
COPY --from=builder /app /app
```

### Deployment Errors
**Pattern**: `deployment.*failed|service.*unavailable|connection.*refused`
**Common Causes**:
- Configuration mismatches
- Missing environment variables
- Network issues
- Resource constraints

**Solutions**:
- Check environment-specific configs
- Validate all required environment variables
- Monitor resource usage (CPU, memory)
- Test network connectivity

## Code Quality Issues

### Linting Errors
**Pattern**: `lint.*error|style.*violation|format.*error`
**Common Causes**:
- Inconsistent code style
- Long lines
- Unused imports
- Missing docstrings

**Solutions**:
```bash
# Auto-fix with formatters
black .
isort .
autoflake --remove-all-unused-imports --in-place **/*.py

# Configure pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Security Scan Failures
**Pattern**: `security.*vulnerability|cve|known.*vulnerability`
**Common Causes**:
- Outdated dependencies
- Hardcoded secrets
- Insecure configurations

**Solutions**:
```bash
# Update dependencies
uv update
pip-audit

# Remove secrets from code
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch secrets.txt'

# Use environment variables
import os
API_KEY = os.getenv('API_KEY')
```

## Recovery Patterns

### Checkpoint and Recovery
**Implementation**:
```python
import json
from pathlib import Path

def save_checkpoint(workflow_id: str, state: dict):
    checkpoint_dir = Path(".github/workflow-states")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    with open(checkpoint_dir / f"{workflow_id}.json", 'w') as f:
        json.dump(state, f)

def load_checkpoint(workflow_id: str) -> dict:
    checkpoint_file = Path(f".github/workflow-states/{workflow_id}.json")
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {}
```

### Rollback Strategies
```bash
# Git rollback
git reset --hard HEAD~1  # Dangerous: loses changes
git revert HEAD          # Safe: creates new commit

# Database rollback (if applicable)
# Implement transaction-based changes
BEGIN;
-- changes here
ROLLBACK;  -- if error
COMMIT;    -- if success
```

### Automated Error Detection
```python
import re
from typing import Dict, List

ERROR_PATTERNS = {
    'git_error': [
        r'merge conflict',
        r'branch.*not found',
        r'authentication failed'
    ],
    'build_error': [
        r'build.*failed',
        r'compilation error',
        r'missing dependency'
    ],
    'test_error': [
        r'test.*failed',
        r'assertion error',
        r'no tests found'
    ]
}

def detect_error_pattern(error_message: str) -> List[str]:
    """Detect error patterns in message."""
    detected = []
    error_lower = error_message.lower()

    for pattern_type, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, error_lower):
                detected.append(pattern_type)
                break

    return detected
```

## Prevention Strategies

### Pre-flight Checks
```python
async def pre_workflow_validation(context):
    """Run validation before starting workflow."""
    checks = []

    # Check git status
    result = subprocess.run(['git', 'status', '--porcelain'],
                          capture_output=True, text=True)
    if result.stdout.strip():
        checks.append("WARNING: Uncommitted changes detected")

    # Check branch
    result = subprocess.run(['git', 'branch', '--show-current'],
                          capture_output=True, text=True)
    if 'main' in result.stdout or 'master' in result.stdout:
        checks.append("ERROR: Working on main branch")

    # Check environment
    if Path("uv.lock").exists():
        result = subprocess.run(['uv', 'run', 'python', '--version'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            checks.append("ERROR: UV environment not working")

    return checks
```

### Monitoring and Alerts
- Set up error tracking (Sentry, Rollbar)
- Monitor CI/CD pipeline health
- Alert on repeated failures
- Track error trends and patterns

### Documentation and Training
- Maintain runbooks for common errors
- Document recovery procedures
- Regular team training on error handling
- Post-mortem analysis for major failures

This comprehensive error pattern guide helps identify, resolve, and prevent common workflow issues.
