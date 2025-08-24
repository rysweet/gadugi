# Recipe Executor

A self-hosting build system that transforms recipe specifications into fully functional software components using AI-powered code generation.

## Features

- **Self-Hosting**: Can regenerate itself from its own recipe specification
- **TDD Approach**: Generates tests first, then implementation
- **Parallel Execution**: Builds independent recipes concurrently
- **Incremental Builds**: Smart caching and dependency tracking
- **Quality Gates**: Automatic validation with pyright, ruff, and pytest
- **Recipe Validation**: WHAT/HOW separation enforcement
- **Complexity Analysis**: Automatic decomposition of complex recipes

## Installation

```bash
# Install with UV (recommended)
uv sync --all-extras

# Or with pip
pip install -e .
```

## Usage

### Build a Recipe

```bash
# Build a single recipe
recipe-executor build path/to/recipe

# Build with parallel execution
recipe-executor build path/to/recipe --parallel

# Force rebuild
recipe-executor build path/to/recipe --force

# Dry run
recipe-executor build path/to/recipe --dry-run
```

### Validate a Recipe

```bash
# Check recipe structure and WHAT/HOW separation
recipe-executor validate path/to/recipe
```

### Analyze Complexity

```bash
# Check if recipe needs decomposition
recipe-executor complexity path/to/recipe
```

### Self-Hosting Test

```bash
# Test that Recipe Executor can regenerate itself
recipe-executor selftest
```

## Recipe Structure

Each recipe requires three files:

### requirements.md
Defines WHAT the system must do (functional requirements):
```markdown
# Component Requirements

## Purpose
Brief description of the component's purpose.

## Functional Requirements
- MUST validate input files
- SHOULD support caching
- COULD provide timing information

## Success Criteria
- All tests pass
- Quality gates pass
```

### design.md
Defines HOW the system will work (implementation approach):
```markdown
# Component Design

## Architecture
High-level architecture description.

## Components
- **Parser**: Parses input files
- **Validator**: Validates structure
- **Generator**: Generates output

## Language
Python
```

### components.json
Metadata and dependencies:
```json
{
  "name": "my-component",
  "version": "1.0.0",
  "type": "LIBRARY",
  "dependencies": ["other-recipe"],
  "description": "Component description",
  "metadata": {}
}
```

## Architecture

The Recipe Executor follows a multi-stage pipeline:

1. **Recipe Validation**: Check structure and WHAT/HOW separation
2. **Complexity Analysis**: Evaluate if decomposition needed
3. **Dependency Resolution**: Build dependency graph
4. **Parallel Execution**: Execute independent recipes concurrently
5. **TDD Generation**: Generate tests first, then implementation
6. **Quality Gates**: Run pyright, ruff, pytest
7. **State Management**: Cache results for incremental builds

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run pyright
```

## Self-Hosting Capability

Recipe Executor demonstrates true self-hosting by being able to regenerate itself from its own recipe specification:

```bash
# Regenerate Recipe Executor from its own recipe
recipe-executor build recipes/recipe-executor

# Verify the regenerated version works
cd .recipe_build/recipe-executor
python cli.py selftest
```

## License

MIT