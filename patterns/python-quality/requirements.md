# Python Quality Standards Requirements

## Purpose
Ensure all Python code adheres to strict quality standards for maintainability, readability, and correctness.

## Functional Requirements

### Code Formatting
- MUST format all Python code with ruff
- MUST use consistent indentation (4 spaces)
- MUST follow PEP 8 style guidelines
- MUST have maximum line length of 100 characters

### Type Safety
- MUST include type hints for all function parameters and return values
- MUST pass pyright type checking with zero errors in strict mode
- MUST avoid using `Any` type except when absolutely necessary
- MUST use `Optional[]` for nullable types

### Testing
- MUST have minimum 80% test coverage
- MUST use pytest for all tests
- MUST include both unit and integration tests
- MUST have all tests passing before code is considered complete

## Non-Functional Requirements

### Development Workflow
- MUST use pre-commit hooks to enforce quality gates
- MUST run quality checks in CI/CD pipeline
- MUST fail builds if quality gates are not met

### Documentation
- MUST include docstrings for all public functions and classes
- MUST use Google-style docstrings
- MUST document all parameters and return types

## Success Criteria
- Zero pyright errors
- Zero ruff formatting issues
- All tests passing
- Pre-commit hooks configured and working