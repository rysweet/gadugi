# Python Quality Standards Design

## Architecture
Layered quality enforcement through automated tooling at multiple stages of development.

## Components

### Pre-commit Configuration
- **Purpose**: Enforce quality gates before code is committed
- **Tools**: pre-commit framework with ruff and pyright hooks
- **Implementation**: `.pre-commit-config.yaml` in project root

### Pyright Configuration
- **Purpose**: Strict type checking for Python code
- **Configuration**: `pyrightconfig.json` with strict mode enabled
- **Checks**: All type errors must be resolved

### Ruff Configuration
- **Purpose**: Fast Python linting and formatting
- **Configuration**: `pyproject.toml` with ruff settings
- **Rules**: PEP 8 compliance with 100 char line length

### Testing Setup
- **Framework**: pytest with coverage reporting
- **Structure**: tests/ directory mirroring src/ structure
- **Coverage**: Minimum 80% with HTML reports

## Implementation Notes

All Python projects using this pattern will have:
1. Automatic code formatting on save (via editor integration)
2. Pre-commit hooks that prevent committing bad code
3. CI/CD checks that validate all quality gates
4. Clear error messages when quality standards are not met

## Code Examples

### Pre-commit hook configuration:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### Pyright configuration:
```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.11",
  "reportMissingTypeStubs": false
}
```