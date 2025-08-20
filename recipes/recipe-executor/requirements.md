# Recipe Executor Requirements

## Core Purpose
The Recipe Executor is a self-hosting build system that executes recipes to generate code, documentation, and system components. It follows a deterministic, dependency-driven approach to building software.

## Functional Requirements

### 1. Recipe Structure Management
- MUST read and parse recipe files (requirements.md, design.md, components.json)
- MUST validate recipe structure and completeness
- MUST support hierarchical recipe dependencies
- MUST detect circular dependencies and fail fast

### 2. Dependency Resolution
- MUST build a directed acyclic graph (DAG) of dependencies
- MUST execute recipes in topological order
- MUST cache built components to avoid rebuilding
- MUST detect when dependencies have changed and trigger rebuilds

### 3. Execution Engine
- MUST generate code from design specifications
- MUST validate generated code against requirements
- MUST create tests for generated components
- MUST run quality gates (pyright, ruff, pytest)
- MUST support parallel execution where dependencies allow

### 4. Self-Hosting Capability
- MUST be able to regenerate itself from its own recipe
- MUST bootstrap from minimal Python implementation
- MUST validate that regenerated code matches current implementation
- MUST maintain version compatibility during self-regeneration

### 5. Component Generation
- MUST generate Python code from design specifications
- MUST generate appropriate tests for components
- MUST generate documentation from recipes
- MUST support multiple output formats (code, configs, docs)

### 6. Validation and Testing
- MUST validate that implementations match requirements
- MUST ensure all dependencies are satisfied before execution
- MUST run generated tests and report results
- MUST enforce quality gates at each stage
- MUST ensure all generated Python code passes strict pyright type checking with zero errors
- MUST format all generated code with ruff
- MUST use UV for package management in all Python projects

### 7. State Management
- MUST track build state and progress
- MUST support incremental builds
- MUST maintain build history and artifacts
- MUST support rollback to previous builds

### 8. Error Handling
- MUST provide clear error messages for recipe issues
- MUST fail fast on critical errors
- MUST support retry logic for transient failures
- MUST log all operations for debugging

## Non-Functional Requirements

### Performance
- MUST execute recipes in under 5 seconds for simple components
- MUST support parallel execution utilizing available CPU cores
- MUST cache aggressively to avoid redundant work

### Reliability
- MUST be deterministic - same inputs produce same outputs
- MUST handle system failures gracefully
- MUST maintain data integrity during crashes

### Usability
- MUST provide clear progress indicators
- MUST generate human-readable error messages
- MUST support dry-run mode for validation
- MUST provide detailed logs for troubleshooting

### Maintainability
- MUST follow clean architecture principles
- MUST have comprehensive test coverage (>90%)
- MUST be well-documented with examples
- MUST support plugin architecture for extensions

## Success Criteria
1. Can regenerate itself from its own recipe with byte-identical output
2. Can build all Gadugi components from their recipes
3. Passes all quality gates (pyright, ruff, pytest)
4. Executes complex dependency graphs correctly
5. Provides clear, actionable error messages
6. Supports incremental builds efficiently