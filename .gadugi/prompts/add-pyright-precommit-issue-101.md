# Add Pyright Type Checking to Pre-commit Hooks

## Title and Overview

**Pyright Integration for Pre-commit Type Safety**

This prompt implements comprehensive pyright type checking integration into the project's pre-commit hooks, addressing GitHub Issue #101. The implementation will fix existing Docker import warnings and establish continuous type safety validation.

**Context**: Most type errors have been fixed across the codebase through PRs #143, #156, and others. Now we need to integrate pyright into pre-commit hooks to maintain type safety going forward.

## Problem Statement

The project currently lacks automated type checking in pre-commit hooks, which can lead to:
1. Type errors being introduced and merged into main
2. Inconsistent type safety across the codebase
3. Docker import warnings in container_runtime modules
4. Manual type checking burden on developers

**Current Issues**:
- container_runtime/container_manager.py:5:8 - Import "docker" could not be resolved from source
- container_runtime/image_manager.py:8:8 - Import "docker" could not be resolved from source
- No pyright configuration file exists
- Pre-commit hooks don't include type checking

## Feature Requirements

### Functional Requirements
- Fix Docker import warnings in a portable way
- Configure pyright for the entire project
- Integrate pyright into pre-commit hooks
- Ensure all Python files pass type checking
- Maintain compatibility across different development environments

### Technical Requirements
- Investigate and implement portable solution for Docker imports (TYPE_CHECKING guards preferred)
- Create pyrightconfig.json with appropriate settings
- Update .pre-commit-config.yaml to include pyright
- Test in environments with and without Docker installed
- Ensure CI/CD compatibility

## Technical Analysis

### Docker Import Fix Options
1. **TYPE_CHECKING Guard** (Preferred):
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import docker
    from docker.models.containers import Container
else:
    try:
        import docker
        from docker.models.containers import Container
    except ImportError:
        docker = None
        Container = None
```

2. **Optional Dependency Approach**:
- Add docker as optional dev dependency in pyproject.toml
- Use try/except for runtime imports

### Pyright Configuration
Create pyrightconfig.json:
```json
{
  "include": [
    "**/*.py"
  ],
  "exclude": [
    "**/node_modules",
    "**/__pycache__",
    ".venv",
    "venv",
    ".git",
    ".worktrees"
  ],
  "typeCheckingMode": "standard",
  "pythonVersion": "3.11",
  "pythonPlatform": "All",
  "reportMissingImports": "warning",
  "reportMissingTypeStubs": "none",
  "reportUnusedImport": true,
  "reportUnusedVariable": true,
  "useLibraryCodeForTypes": true
}
```

### Pre-commit Hook Configuration
Update .pre-commit-config.yaml:
```yaml
  - repo: https://github.com/microsoft/pyright
    rev: v1.1.403
    hooks:
      - id: pyright
        name: pyright type checker
        entry: pyright
        language: node
        types: [python]
        additional_dependencies: ['pyright@1.1.403']
        pass_filenames: false
```

## Implementation Plan

### Phase 1: Fix Docker Import Warnings
- Analyze current Docker usage in container_runtime
- Implement TYPE_CHECKING guards for optional imports
- Update container_manager.py and image_manager.py
- Test imports work with and without Docker

### Phase 2: Configure Pyright
- Create pyrightconfig.json with project settings
- Set appropriate type checking mode (standard)
- Configure include/exclude paths
- Set Python version and platform settings

### Phase 3: Pre-commit Integration
- Update .pre-commit-config.yaml
- Add pyright hook with proper configuration
- Test pre-commit runs successfully
- Ensure it catches type errors

### Phase 4: Fix Remaining Type Issues
- Run pyright across entire codebase
- Fix any newly discovered type errors
- Ensure all files pass type checking
- Document any necessary type ignores

## Testing Requirements

### Import Testing
- Verify Docker imports work with Docker installed
- Verify graceful handling without Docker
- Test TYPE_CHECKING guards work correctly
- Ensure no runtime import errors

### Pyright Testing
- Run pyright on all Python files
- Verify configuration is applied correctly
- Test that errors are caught appropriately
- Ensure warnings are at acceptable levels

### Pre-commit Testing
- Run pre-commit on all files
- Test that pyright hook executes
- Verify it fails on type errors
- Test it passes on clean code

### Environment Testing
- Test in fresh virtual environment
- Test with UV package manager
- Test in CI/CD environment
- Test on different operating systems

## Success Criteria

### Core Requirements
- All Docker import warnings resolved
- Pyright successfully integrated into pre-commit
- All Python files pass type checking
- Pre-commit hooks run efficiently

### Quality Metrics
- Zero type errors in codebase
- Import warnings reduced to zero
- Pre-commit runs in < 30 seconds
- Works in all development environments

## Implementation Steps

1. Create feature branch for Issue #101
2. Implement TYPE_CHECKING guards in container_runtime modules
3. Create pyrightconfig.json with project settings
4. Update .pre-commit-config.yaml with pyright hook
5. Run pyright and fix any discovered issues
6. Test in multiple environments
7. Update documentation with type checking guidelines
8. Create PR with comprehensive testing results

---

*Note: This implementation addresses GitHub Issue #101 and ensures long-term type safety through automated pre-commit validation.*
