# Enforce Code Quality Compliance: Achieve Zero Pyright Errors

## Title and Overview
**Zero Pyright Errors Compliance Initiative**

Achieve complete elimination of the current 1343 pyright errors to establish mandatory compliance for future development. This initiative will implement zero-tolerance type checking and establish automated enforcement mechanisms.

## Problem Statement

The codebase currently has **1343 pyright errors** that prevent establishing mandatory type checking compliance. These errors span:
- Import resolution issues (reportMissingImports)
- Unused import/variable violations (reportUnusedImport/reportUnusedVariable)
- Type annotation issues (reportOptionalMemberAccess, reportAttributeAccessIssue)
- Missing type stubs and attribute access problems

**Critical Requirements**:
- Use UV environment for ALL Python commands (`uv run pyright`, `uv run ruff`, etc.)
- Achieve ZERO pyright errors across entire codebase
- Establish automated enforcement in pre-commit hooks
- Create comprehensive type checking compliance system

## Technical Analysis

### Error Categories (from pyright stats)
1. **Import Resolution (268 warnings)**: Missing module imports that need proper handling
2. **Unused Imports (300+ errors)**: Dead imports requiring cleanup
3. **Type Access Issues (400+ errors)**: Optional member access and attribute issues
4. **Variable Usage (200+ errors)**: Unused variables and parameters
5. **Type Annotation Issues (175+ errors)**: Missing or incorrect type hints

### UV Environment Requirements
All type checking MUST use UV virtual environment:
```bash
# Setup UV environment
uv sync --all-extras

# Run type checking
uv run pyright --stats
uv run pyright . --createstub missing_module

# Code quality checks
uv run ruff check .
uv run ruff format .
```

## Implementation Plan

### Phase 1: Critical Error Triage (Priority: HIGH)
- Identify breaking errors that prevent basic functionality
- Fix import resolution issues for core modules
- Address type access errors in critical paths
- Use UV environment for all operations: `uv run pyright`

### Phase 2: Systematic Error Resolution
- **Unused Imports/Variables**: Use `uv run ruff --fix` for automated cleanup
- **Type Annotations**: Add proper type hints where missing
- **Optional Access**: Add proper null checks and type guards
- **Attribute Issues**: Fix or suppress legitimate attribute access problems

### Phase 3: Import and Module Issues
- Resolve missing import warnings using TYPE_CHECKING guards
- Create or install missing type stubs
- Fix module resolution issues in .claude/ directories
- Handle conditional imports properly

### Phase 4: Automated Compliance Enforcement
- Update pyrightconfig.json with strict settings
- Add pyright to pre-commit hooks with UV integration
- Establish CI/CD pipeline validation
- Create automatic error prevention system

### Phase 5: Zero Tolerance Implementation
- Set pyright error count to ZERO as mandatory gate
- Configure pre-commit to fail on ANY type errors
- Update development workflow to require type checking
- Document compliance requirements for all developers

## Pyright Configuration

Create/update pyrightconfig.json for strict compliance:
```json
{
  "include": ["**/*.py"],
  "exclude": [
    "**/node_modules",
    "**/__pycache__",
    ".venv",
    ".worktrees"
  ],
  "typeCheckingMode": "strict",
  "pythonVersion": "3.11",
  "pythonPlatform": "All",
  "reportMissingImports": "error",
  "reportMissingTypeStubs": "warning",
  "reportUnusedImport": "error",
  "reportUnusedVariable": "error",
  "reportOptionalMemberAccess": "error",
  "reportAttributeAccessIssue": "error",
  "strictListInference": true,
  "strictDictionaryInference": true,
  "strictSetInference": true
}
```

## Pre-commit Integration with UV

Update .pre-commit-config.yaml:
```yaml
- repo: local
  hooks:
    - id: pyright-uv
      name: PyRight Type Checking (UV)
      entry: uv run pyright
      language: system
      types: [python]
      pass_filenames: false
      stages: [pre-commit]

    - id: ruff-check-uv
      name: Ruff Linting (UV)
      entry: uv run ruff check
      language: system
      types: [python]
      args: ["--fix"]

    - id: ruff-format-uv
      name: Ruff Formatting (UV)
      entry: uv run ruff format
      language: system
      types: [python]
```

## Error Resolution Strategy

### High Impact Fixes (Automated)
```bash
# Remove unused imports
uv run ruff --select F401 --fix .

# Fix formatting issues
uv run ruff format .

# Remove unused variables where safe
uv run ruff --select F841 --fix .
```

### Type Safety Fixes (Manual Review Required)
```python
# Optional member access fixes
def safe_access(obj: Optional[MyType]) -> str:
    if obj is not None:
        return obj.attribute
    return "default"

# Proper type guard usage
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import optional_module
```

### Import Resolution Fixes
```python
# Conditional imports for optional dependencies
try:
    import docker
    HAS_DOCKER = True
except ImportError:
    docker = None
    HAS_DOCKER = False
```

## Success Criteria

### Mandatory Requirements
- **ZERO pyright errors** across entire codebase
- **ZERO tolerance** for type checking failures in CI/CD
- **UV integration** working for all type checking commands
- **Pre-commit hooks** preventing type errors from being committed

### Quality Metrics
- Pyright error count: **0** (current: 1343)
- Warning count: **< 50** (current: 268)
- Pre-commit check time: **< 60 seconds**
- Type checking coverage: **100%** of Python files

## Testing Requirements

### Environment Testing
- Verify UV environment setup works correctly
- Test pyright runs without errors: `uv run pyright --stats`
- Validate pre-commit hooks function properly
- Ensure CI/CD pipeline integration

### Regression Testing
- Run full test suite after each major fix batch
- Verify no functionality broken by type fixes
- Test import resolution in all environments
- Validate type hints don't break runtime behavior

### Compliance Testing
- Test pre-commit prevents type errors from committing
- Verify CI/CD fails on type checking violations
- Validate developer workflow includes type checking
- Test automated error detection and reporting

## Implementation Steps

1. **Setup UV Environment**: `uv sync --all-extras`
2. **Baseline Assessment**: `uv run pyright --stats > baseline.txt`
3. **Automated Cleanup**: `uv run ruff --fix .`
4. **Systematic Error Resolution**: Fix errors by category priority
5. **Pre-commit Integration**: Update hooks with UV commands
6. **CI/CD Pipeline Updates**: Add type checking gates
7. **Documentation**: Update development guidelines
8. **Validation**: Achieve zero error milestone

## Risk Mitigation

### Backup Strategy
- Create feature branch for all type checking work
- Regular commits after each fix batch
- Maintain rollback capability for breaking changes

### Incremental Approach
- Fix errors in batches of 50-100 to maintain stability
- Test after each batch to catch regressions early
- Use automated tools where possible to minimize human error

### Compatibility Preservation
- Ensure type fixes don't break runtime behavior
- Validate imports still work across all environments
- Test optional dependencies maintain graceful degradation

---

*This prompt implements comprehensive type checking compliance to achieve zero pyright errors and establish mandatory quality gates for future development.*
