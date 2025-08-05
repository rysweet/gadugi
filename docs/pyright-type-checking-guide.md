# Pyright Type Checking Guide

## Overview

This document describes the pyright type checking configuration for the Gadugi project. Pyright is Microsoft's Python static type checker that helps identify type-related issues in the codebase.

## Configuration

### pyrightconfig.json

The project uses a `pyrightconfig.json` configuration file with the following key settings:

- **Type Checking Mode**: `standard` - balanced type checking level
- **Python Version**: `3.13` - matching project requirements
- **Included Paths**:
  - `.claude/shared` - Shared modules
  - `gadugi` - Main package
  - `container_runtime` - Container execution system
  - `tests` - Test suite
  - `.github/memory-manager` - Memory management utilities
  - `src/agents` - Agent implementations

- **Excluded Paths**:
  - Cache directories (`__pycache__`, `.pytest_cache`, etc.)
  - Build artifacts (`build`, `dist`, `*.egg-info`)
  - Version control (`.git`)
  - Virtual environments (`.venv`, `venv`)
  - Working trees (`.worktrees`)

### Pre-commit Integration

Pyright is integrated into the pre-commit hooks via:

```yaml
- repo: https://github.com/RobertCraigie/pyright-python
  rev: v1.1.350
  hooks:
    - id: pyright
      additional_dependencies: [PyYAML>=6.0]
```

## Current Type Checking Status

### Summary Statistics

- **Total Issues**: 6,752 (1,042 errors + 5,710 warnings)
- **Files Analyzed**: 62 checked out of 238 parsed
- **Analysis Time**: ~3.2 seconds

### Issue Breakdown by Category

#### Top Issues by Type (Rule)
1. **reportUnknownMemberType** (2,549 issues) - Unknown member types in objects
2. **reportUnknownVariableType** (1,037 issues) - Variables with unknown types
3. **reportUnknownParameterType** (490 issues) - Function parameters without types
4. **reportMissingParameterType** (450 issues) - Missing type annotations for parameters
5. **reportPossiblyUnboundVariable** (411 issues) - Variables that might not be initialized

#### Top Files by Issue Count
1. **test_delegation_coordinator.py** (541 issues)
2. **test_task_tracking.py** (537 issues)
3. **test_state_management.py** (458 issues)
4. **test_error_handling.py** (372 issues)
5. **test_readiness_assessor.py** (364 issues)

#### Issues by Module Category
- **Test Files**: 5,432 issues (80% of total)
- **Container Runtime**: 188 issues
- **Core Modules**: ~400 issues combined

## Priority Areas for Type Safety Improvement

### High Priority (Errors - 1,042 total)
These should be addressed first as they represent critical type safety issues:

1. **Missing Import Errors** (86 issues)
   - Fix import statements for missing modules
   - Add proper module paths to PYTHONPATH

2. **Attribute Access Issues** (14 issues)
   - Fix access to non-existent attributes
   - Add proper type guards

3. **General Type Issues** (4 issues)
   - Critical type mismatches that could cause runtime errors

### Medium Priority (High-Impact Warnings)
Focus on these warnings that significantly impact code maintainability:

1. **Missing Parameter Types** (450 issues)
   - Add type annotations to function parameters
   - Use proper generic types where applicable

2. **Unknown Parameter Types** (490 issues)
   - Import proper type definitions
   - Add type hints to function signatures

3. **Uninitialized Instance Variables** (74 issues)
   - Initialize instance variables in `__init__`
   - Add proper default values

### Low Priority (Code Quality Warnings)
Address these for improved code quality:

1. **Unused Imports** (83 issues)
   - Remove or use imported modules
   - Clean up import statements

2. **Unused Variables** (22 issues)
   - Remove unused variable assignments
   - Use underscore prefix for intentionally unused variables

## Implementation Strategy

### Phase 1: Foundation (High Priority)
1. **Fix Missing Imports** (86 issues)
   - Resolve import errors first to enable proper type checking
   - Update PYTHONPATH and module structure as needed

2. **Add Core Type Annotations**
   - Start with shared modules in `.claude/shared/`
   - Focus on public APIs and interfaces

### Phase 2: Core Modules (Medium Priority)
1. **Container Runtime** (188 issues)
   - Add type annotations to container management classes
   - Fix SecurityPolicy and ContainerManager types

2. **Shared Modules** (~400 issues)
   - Update base_classes.py with proper type hints
   - Fix error_handling.py type issues
   - Add types to task_tracking.py

### Phase 3: Test Infrastructure (Lower Priority)
1. **Test Files** (5,432 issues - 80% of total)
   - Most test issues are low-impact (mock objects, test data)
   - Focus on test utilities and fixtures first
   - Consider excluding some test files from strict type checking

### Phase 4: Optimization
1. **Performance Monitoring**
   - Monitor analysis time as types are added
   - Adjust configuration if needed

2. **CI/CD Integration**
   - Ensure pre-commit hooks work efficiently
   - Consider running subset of checks on commits vs. push

## Best Practices

### Type Annotation Guidelines
```python
# Good: Explicit type hints
def process_data(items: list[dict[str, Any]]) -> ProcessResult:
    return ProcessResult(processed_items=items)

# Good: Generic types
T = TypeVar('T')
def safe_get(data: dict[str, T], key: str, default: T) -> T:
    return data.get(key, default)

# Good: Protocol for duck typing
class Writable(Protocol):
    def write(self, data: str) -> None: ...
```

### Configuration Recommendations
- Keep `typeCheckingMode` at `standard` for balanced checking
- Use `reportUnknownVariableType: "warning"` during migration
- Consider `ignore` patterns for legacy code that's hard to type

## Troubleshooting

### Common Issues and Solutions

1. **"Import could not be resolved"**
   - Add module path to `extraPaths` in pyrightconfig.json
   - Check if module is properly installed in environment

2. **"Type is partially unknown"**
   - Add explicit type annotations
   - Import proper type definitions
   - Use `Any` type as temporary solution

3. **"Method does not call super().__init__()"**
   - Add `super().__init__()` call in child class constructors
   - Or explicitly disable the rule for specific classes

### Performance Optimization
- Exclude unnecessary files from analysis
- Use `ignore` patterns for files that don't need strict typing
- Consider splitting large analysis into smaller chunks

## Integration with Development Workflow

### Pre-commit Usage
```bash
# Run pyright check manually
uv run pyright

# Run with JSON output for automation
uv run pyright --outputjson

# Check specific files
uv run pyright path/to/file.py

# Get statistics
uv run pyright --stats
```

### IDE Integration
Most IDEs support pyright through the Python Language Server (Pylsp) or directly:
- VS Code: Python extension uses pyright by default
- PyCharm: Can be configured to use pyright
- Vim/Neovim: Through LSP plugins

## Next Steps

1. **Immediate Actions** (Week 1):
   - Fix the 86 missing import errors
   - Add type annotations to core shared modules

2. **Short Term** (Month 1):
   - Complete container runtime type annotations
   - Address uninitialized instance variables

3. **Long Term** (Month 2-3):
   - Systematic type annotation of remaining modules
   - Optimize configuration based on usage patterns
   - Consider stricter type checking modes

## Resources

- [Pyright Documentation](https://microsoft.github.io/pyright/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [mypy Type System Reference](https://mypy.readthedocs.io/en/stable/type_system_reference.html)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
