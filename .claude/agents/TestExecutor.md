# Test Executor Agent


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

## Purpose
Single-responsibility executor for running tests and quality checks. This agent performs direct test execution without delegating to other agents.

## CRITICAL: No Delegation
This agent MUST NOT call or delegate to other agents. All operations must be direct tool usage only.

## Available Tools
- Bash (for running test commands)
- Read (for reading test results)
- Grep (for searching test output)

## Functions

### detect_uv_project()
Detects if the current directory is a UV project.

**Returns:**
- `dict`: Detection result with keys:
  - `is_uv_project`: Boolean indicating UV project
  - `has_pyproject`: Whether pyproject.toml exists
  - `has_uv_lock`: Whether uv.lock exists
  - `command_prefix`: Command prefix to use ("uv run" or "")

**Implementation:**
```bash
# Check for UV project markers
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo '{
        "is_uv_project": true,
        "has_pyproject": true,
        "has_uv_lock": true,
        "command_prefix": "uv run"
    }'
else
    echo '{
        "is_uv_project": false,
        "has_pyproject": '$(test -f "pyproject.toml" && echo true || echo false)',
        "has_uv_lock": '$(test -f "uv.lock" && echo true || echo false)',
        "command_prefix": ""
    }'
fi
```

**Usage Example:**
```python
project_info = detect_uv_project()
if project_info['is_uv_project']:
    print("UV project detected - will use 'uv run' prefix")
    cmd_prefix = project_info['command_prefix']
else:
    print("Standard Python project")
    cmd_prefix = ""
```

### run_pytest(test_path="tests/", verbose=True, coverage=False)
Runs pytest tests with UV detection.

**Parameters:**
- `test_path` (str): Path to test directory or file
- `verbose` (bool): Enable verbose output
- `coverage` (bool): Generate coverage report

**Returns:**
- `dict`: Test results with keys:
  - `exit_code`: Process exit code (0 = success)
  - `passed`: Number of passed tests
  - `failed`: Number of failed tests
  - `skipped`: Number of skipped tests
  - `coverage_percent`: Coverage percentage if requested

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
    # Ensure UV environment is set up
    uv sync --all-extras
else
    CMD_PREFIX=""
fi

# Build pytest command
PYTEST_CMD="${CMD_PREFIX} pytest ${test_path}"

if [[ $verbose == true ]]; then
    PYTEST_CMD="${PYTEST_CMD} -v"
fi

if [[ $coverage == true ]]; then
    PYTEST_CMD="${PYTEST_CMD} --cov=. --cov-report=term --cov-report=html"
fi

# Run tests and capture output
output=$(${PYTEST_CMD} 2>&1)
exit_code=$?

# Parse results
passed=$(echo "$output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
failed=$(echo "$output" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
skipped=$(echo "$output" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo 0)

if [[ $coverage == true ]]; then
    coverage_percent=$(echo "$output" | grep -oE 'TOTAL.*[0-9]+%' | grep -oE '[0-9]+%' || echo "0%")
fi

echo "{
    \"exit_code\": ${exit_code},
    \"passed\": ${passed},
    \"failed\": ${failed},
    \"skipped\": ${skipped},
    \"coverage_percent\": \"${coverage_percent}\"
}"
```

**Usage Example:**
```python
# Run tests with coverage
results = run_pytest("tests/", verbose=True, coverage=True)

if results['exit_code'] == 0:
    print(f"✅ All tests passed! {results['passed']} passed, {results['skipped']} skipped")
    print(f"Coverage: {results['coverage_percent']}")
else:
    print(f"❌ {results['failed']} tests failed")
```

### run_ruff_check(path=".", fix=False)
Runs ruff linting with UV detection.

**Parameters:**
- `path` (str): Path to check
- `fix` (bool): Auto-fix issues if True

**Returns:**
- `dict`: Linting results with keys:
  - `exit_code`: Process exit code
  - `issues_found`: Number of issues found
  - `issues_fixed`: Number of issues fixed (if fix=True)

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
else
    CMD_PREFIX=""
fi

# Build command
RUFF_CMD="${CMD_PREFIX} ruff check ${path}"

if [[ $fix == true ]]; then
    RUFF_CMD="${RUFF_CMD} --fix"
fi

# Run ruff
output=$(${RUFF_CMD} 2>&1)
exit_code=$?

# Parse results
issues_found=$(echo "$output" | grep -oE 'Found [0-9]+ error' | grep -oE '[0-9]+' || echo 0)

if [[ $fix == true ]]; then
    issues_fixed=$(echo "$output" | grep -oE 'Fixed [0-9]+ error' | grep -oE '[0-9]+' || echo 0)
else
    issues_fixed=0
fi

echo "{
    \"exit_code\": ${exit_code},
    \"issues_found\": ${issues_found},
    \"issues_fixed\": ${issues_fixed}
}"
```

**Usage Example:**
```python
# Check and auto-fix linting issues
results = run_ruff_check(".", fix=True)

if results['issues_fixed'] > 0:
    print(f"🔧 Fixed {results['issues_fixed']} linting issues")
if results['exit_code'] == 0:
    print("✅ No linting issues remaining")
```

### run_ruff_format(path=".", check=False)
Runs ruff formatting with UV detection.

**Parameters:**
- `path` (str): Path to format
- `check` (bool): Check only, don't modify files

**Returns:**
- `dict`: Format results with keys:
  - `exit_code`: Process exit code
  - `files_changed`: Number of files that need/were formatted

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
else
    CMD_PREFIX=""
fi

# Build command
RUFF_FMT_CMD="${CMD_PREFIX} ruff format ${path}"

if [[ $check == true ]]; then
    RUFF_FMT_CMD="${RUFF_FMT_CMD} --check"
fi

# Run formatter
output=$(${RUFF_FMT_CMD} 2>&1)
exit_code=$?

# Parse results
if [[ $check == true ]]; then
    files_changed=$(echo "$output" | grep -oE '[0-9]+ file.*would be' | grep -oE '[0-9]+' || echo 0)
else
    files_changed=$(echo "$output" | grep -oE '[0-9]+ file.*reformatted' | grep -oE '[0-9]+' || echo 0)
fi

echo "{
    \"exit_code\": ${exit_code},
    \"files_changed\": ${files_changed}
}"
```

**Usage Example:**
```python
# Check formatting without changing files
results = run_ruff_format(".", check=True)

if results['files_changed'] > 0:
    print(f"⚠️  {results['files_changed']} files need formatting")
    # Now actually format them
    run_ruff_format(".")
    print("✅ Files formatted")
```

### run_pyright(path=".")
Runs pyright type checking with UV detection.

**Parameters:**
- `path` (str): Path to type check

**Returns:**
- `dict`: Type check results with keys:
  - `exit_code`: Process exit code
  - `errors`: Number of type errors
  - `warnings`: Number of warnings
  - `information`: Number of information messages

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
else
    CMD_PREFIX=""
fi

# Run pyright
output=$(${CMD_PREFIX} pyright ${path} 2>&1)
exit_code=$?

# Parse results
errors=$(echo "$output" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' || echo 0)
warnings=$(echo "$output" | grep -oE '[0-9]+ warning' | grep -oE '[0-9]+' || echo 0)
information=$(echo "$output" | grep -oE '[0-9]+ information' | grep -oE '[0-9]+' || echo 0)

echo "{
    \"exit_code\": ${exit_code},
    \"errors\": ${errors},
    \"warnings\": ${warnings},
    \"information\": ${information}
}"
```

**Usage Example:**
```python
# Run type checking
results = run_pyright(".")

if results['errors'] == 0:
    print("✅ No type errors found")
    if results['warnings'] > 0:
        print(f"⚠️  {results['warnings']} warnings to review")
else:
    print(f"❌ {results['errors']} type errors must be fixed")
```

### run_precommit(all_files=True)
Runs pre-commit hooks with UV detection.

**Parameters:**
- `all_files` (bool): Check all files vs only staged

**Returns:**
- `dict`: Pre-commit results with keys:
  - `exit_code`: Process exit code
  - `hooks_passed`: Number of hooks that passed
  - `hooks_failed`: Number of hooks that failed

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
    # Install pre-commit hooks if needed
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        ${CMD_PREFIX} pre-commit install
    fi
else
    CMD_PREFIX=""
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        pre-commit install
    fi
fi

# Build command
PRECOMMIT_CMD="${CMD_PREFIX} pre-commit run"

if [[ $all_files == true ]]; then
    PRECOMMIT_CMD="${PRECOMMIT_CMD} --all-files"
fi

# Run pre-commit
output=$(${PRECOMMIT_CMD} 2>&1)
exit_code=$?

# Parse results
hooks_passed=$(echo "$output" | grep -c "Passed" || echo 0)
hooks_failed=$(echo "$output" | grep -c "Failed" || echo 0)

echo "{
    \"exit_code\": ${exit_code},
    \"hooks_passed\": ${hooks_passed},
    \"hooks_failed\": ${hooks_failed}
}"
```

**Usage Example:**
```python
# Run all pre-commit hooks
results = run_precommit(all_files=True)

if results['exit_code'] == 0:
    print(f"✅ All {results['hooks_passed']} hooks passed")
else:
    print(f"❌ {results['hooks_failed']} hooks failed")
```

### run_full_test_suite()
Runs the complete test suite with all quality checks in proper order.

**Returns:**
- `dict`: Full suite results with keys:
  - `all_passed`: Boolean indicating if all checks passed
  - `pytest_passed`: Test suite status
  - `ruff_passed`: Linting status
  - `format_passed`: Formatting status
  - `pyright_passed`: Type checking status
  - `precommit_passed`: Pre-commit hooks status

**Implementation:**
```bash
# This function runs all checks in the proper order
# Order: format -> lint -> type check -> tests -> pre-commit

echo "Starting full test suite..."
all_passed=true

# Step 1: Format code
echo "Step 1/5: Formatting code..."
format_result=$(run_ruff_format ".")
format_exit=$(echo $format_result | jq -r '.exit_code')
if [[ $format_exit -ne 0 ]]; then
    echo "❌ Formatting failed"
    all_passed=false
    format_passed=false
else
    echo "✅ Formatting passed"
    format_passed=true
fi

# Step 2: Lint code
echo "Step 2/5: Linting code..."
ruff_result=$(run_ruff_check ".")
ruff_exit=$(echo $ruff_result | jq -r '.exit_code')
if [[ $ruff_exit -ne 0 ]]; then
    echo "❌ Linting failed"
    all_passed=false
    ruff_passed=false
else
    echo "✅ Linting passed"
    ruff_passed=true
fi

# Step 3: Type checking
echo "Step 3/5: Type checking..."
pyright_result=$(run_pyright ".")
pyright_errors=$(echo $pyright_result | jq -r '.errors')
if [[ $pyright_errors -gt 0 ]]; then
    echo "❌ Type checking failed with $pyright_errors errors"
    all_passed=false
    pyright_passed=false
else
    echo "✅ Type checking passed"
    pyright_passed=true
fi

# Step 4: Run tests
echo "Step 4/5: Running tests..."
pytest_result=$(run_pytest "tests/" true true)
pytest_exit=$(echo $pytest_result | jq -r '.exit_code')
if [[ $pytest_exit -ne 0 ]]; then
    echo "❌ Tests failed"
    all_passed=false
    pytest_passed=false
else
    echo "✅ Tests passed"
    pytest_passed=true
fi

# Step 5: Pre-commit hooks
echo "Step 5/5: Running pre-commit hooks..."
precommit_result=$(run_precommit true)
precommit_exit=$(echo $precommit_result | jq -r '.exit_code')
if [[ $precommit_exit -ne 0 ]]; then
    echo "❌ Pre-commit hooks failed"
    all_passed=false
    precommit_passed=false
else
    echo "✅ Pre-commit hooks passed"
    precommit_passed=true
fi

# Return results
echo "{
    \"all_passed\": ${all_passed},
    \"pytest_passed\": ${pytest_passed},
    \"ruff_passed\": ${ruff_passed},
    \"format_passed\": ${format_passed},
    \"pyright_passed\": ${pyright_passed},
    \"precommit_passed\": ${precommit_passed}
}"
```

**Usage Example:**
```python
# Run complete test suite
results = run_full_test_suite()

if results['all_passed']:
    print("🎉 All quality checks passed! Ready for PR.")
else:
    print("❌ Some checks failed:")
    if not results['format_passed']:
        print("  - Formatting issues")
    if not results['ruff_passed']:
        print("  - Linting issues")
    if not results['pyright_passed']:
        print("  - Type checking issues")
    if not results['pytest_passed']:
        print("  - Test failures")
    if not results['precommit_passed']:
        print("  - Pre-commit hook failures")
```

### check_test_coverage(threshold=80)
Checks test coverage against threshold.

**Parameters:**
- `threshold` (int): Minimum coverage percentage required

**Returns:**
- `dict`: Coverage results with keys:
  - `current_coverage`: Current coverage percentage
  - `meets_threshold`: Boolean indicating if threshold is met
  - `missing_lines`: Number of uncovered lines

**Implementation:**
```bash
# Detect UV project
project_info=$(detect_uv_project)
if [[ $(echo $project_info | jq -r '.is_uv_project') == "true" ]]; then
    CMD_PREFIX="uv run"
else
    CMD_PREFIX=""
fi

# Run coverage
output=$(${CMD_PREFIX} pytest tests/ --cov=. --cov-report=term 2>&1)

# Parse coverage percentage
coverage=$(echo "$output" | grep -oE 'TOTAL.*[0-9]+%' | grep -oE '[0-9]+' || echo 0)
missing=$(echo "$output" | grep -oE 'TOTAL.*[0-9]+ ' | awk '{print $3}' || echo 0)

if [[ $coverage -ge $threshold ]]; then
    meets_threshold=true
else
    meets_threshold=false
fi

echo "{
    \"current_coverage\": ${coverage},
    \"meets_threshold\": ${meets_threshold},
    \"missing_lines\": ${missing}
}"
```

**Usage Example:**
```python
# Check if we meet 80% coverage threshold
results = check_test_coverage(threshold=80)

if results['meets_threshold']:
    print(f"✅ Coverage {results['current_coverage']}% meets threshold")
else:
    print(f"❌ Coverage {results['current_coverage']}% below 80% threshold")
    print(f"   Need to cover {results['missing_lines']} more lines")
```

## Complete Usage Examples

### Example 1: UV Project Detection and Setup
```python
# First detect project type
project = detect_uv_project()

if project['is_uv_project']:
    print("UV project detected")
    # Ensure environment is set up
    os.system("uv sync --all-extras")
    cmd_prefix = "uv run"
else:
    print("Standard Python project")
    cmd_prefix = ""

# Now run tests with appropriate prefix
test_results = run_pytest("tests/", verbose=True, coverage=True)
print(f"Tests: {test_results['passed']} passed, {test_results['failed']} failed")
```

### Example 2: Pre-PR Quality Check
```python
# Run full suite before creating PR
print("Running pre-PR quality checks...")

results = run_full_test_suite()

if results['all_passed']:
    print("🎉 All checks passed! Ready to create PR.")
    
    # Check coverage too
    coverage = check_test_coverage(threshold=80)
    if coverage['meets_threshold']:
        print(f"✅ Coverage: {coverage['current_coverage']}%")
    else:
        print(f"⚠️  Coverage: {coverage['current_coverage']}% (below 80% threshold)")
else:
    print("❌ Cannot create PR - fix issues first")
    exit(1)
```

### Example 3: Continuous Integration Check
```python
# CI/CD pipeline check
def ci_check():
    """Run all checks required for CI."""
    
    # Detect project type first
    project = detect_uv_project()
    print(f"Project type: {'UV' if project['is_uv_project'] else 'Standard Python'}")
    
    # Format check (don't modify)
    format_check = run_ruff_format(".", check=True)
    if format_check['files_changed'] > 0:
        print(f"❌ {format_check['files_changed']} files need formatting")
        return False
    
    # Linting
    lint_check = run_ruff_check(".")
    if lint_check['issues_found'] > 0:
        print(f"❌ {lint_check['issues_found']} linting issues")
        return False
    
    # Type checking
    type_check = run_pyright(".")
    if type_check['errors'] > 0:
        print(f"❌ {type_check['errors']} type errors")
        return False
    
    # Tests with coverage
    test_check = run_pytest("tests/", coverage=True)
    if test_check['exit_code'] != 0:
        print(f"❌ {test_check['failed']} tests failed")
        return False
    
    # Coverage threshold
    coverage_check = check_test_coverage(threshold=80)
    if not coverage_check['meets_threshold']:
        print(f"❌ Coverage {coverage_check['current_coverage']}% below threshold")
        return False
    
    print("✅ All CI checks passed!")
    return True

# Run CI checks
if ci_check():
    exit(0)
else:
    exit(1)
```

## Error Handling
- Check for test framework availability
- Handle missing dependencies
- Provide clear failure messages
- Return non-zero exit codes on failure
