# Data Models Recipe Design

## Architecture Overview
The Data Models package provides strongly-typed, validated data structures for the Recipe Executor system using Pydantic v2 for runtime validation and Python dataclasses for simple structures.

## Technology Choices
- **Pydantic v2**: Runtime validation, JSON serialization, type coercion
- **Python 3.11+**: Native type hints, dataclasses, enums
- **JSON Schema**: Model schema generation for documentation
- **UUID**: Unique identifiers for recipes and components

## Component Design

### Component: Core Recipe Model (`recipe_model.py`)
Main Recipe class with nested structures for metadata, requirements, design, and components.

**Classes to implement:**
- `RequirementPriority(str, Enum)`: MUST, SHOULD, COULD
- `ComponentType(str, Enum)`: SERVICE, LIBRARY, CLI, AGENT, MODULE
- `RecipeMetadata(BaseModel)`: name, version, description, author, timestamps, tags
- `Requirement(BaseModel)`: id, priority, description, category
- `Requirements(BaseModel)`: functional, non_functional lists with helper methods
- `ComponentDesign(BaseModel)`: name, type, path, interfaces, dependencies
- `Design(BaseModel)`: overview, technology_choices, components, patterns
- `Components(BaseModel)`: name, version, type, dependencies, metadata
- `Recipe(BaseModel)`: Complete recipe with all nested structures

**Key methods:**
- `Recipe.get_dependencies()`: Return list of recipe dependencies
- `Recipe.is_valid()`: Check if recipe is complete and valid
- `Recipe.to_summary()`: Generate human-readable summary
- `Requirements.get_by_priority()`: Filter requirements by priority
- `Requirements.count()`: Count requirements by category

### Component: Requirements Model (`requirements_model.py`)
Extended requirement tracking with status, validation rules, and coverage analysis.

**Classes to implement:**
- `RequirementStatus(str, Enum)`: PENDING, IN_PROGRESS, IMPLEMENTED, VERIFIED, DEFERRED
- `RequirementCategory(str, Enum)`: FUNCTIONAL, NON_FUNCTIONAL, PERFORMANCE, SECURITY, etc.
- `ValidationRule(BaseModel)`: name, check_type, target, expected_value
- `RequirementLink(BaseModel)`: source_id, target_id, link_type, description
- `ExtendedRequirement(BaseModel)`: Full requirement tracking with status and validation
- `RequirementsMatrix(BaseModel)`: Track requirements relationships and coverage

**Key methods:**
- `ExtendedRequirement.is_complete()`: Check if requirement is implemented and verified
- `ExtendedRequirement.add_implementation()`: Link component to requirement
- `RequirementsMatrix.get_uncovered_requirements()`: Find unimplemented requirements
- `RequirementsMatrix.get_coverage_stats()`: Calculate implementation/verification percentages

### Component: Design Model (`design_model.py`)
Component architecture specifications with interfaces and dependencies.

**Classes to implement:**
- `InterfaceType(str, Enum)`: REST_API, GRPC, CLI, PYTHON_API, FILE_BASED, EVENT_DRIVEN
- `MethodSignature(BaseModel)`: name, parameters, return_type, description
- `Interface(BaseModel)`: name, type, methods, properties, events
- `Dependency(BaseModel)`: name, version, type (internal/external), optional
- `DesignPattern(BaseModel)`: name, category, description, participants
- `ComponentArchitecture(BaseModel)`: Detailed component design with all relationships
- `SystemArchitecture(BaseModel)`: Overall system with components, layers, data flow

**Key methods:**
- `Interface.get_method()`: Find method by name
- `ComponentArchitecture.get_external_dependencies()`: Filter external dependencies
- `ComponentArchitecture.to_component_diagram()`: Generate PlantUML diagram
- `SystemArchitecture.validate_dependencies()`: Check all dependencies are satisfied

### Component: Execution Models (`execution_model.py`)
State tracking for recipe execution, generation results, and test outcomes.

**Classes to implement:**
- `ExecutionPhase(str, Enum)`: INITIALIZING, PARSING, VALIDATING, GENERATING, etc.
- `ErrorSeverity(str, Enum)`: INFO, WARNING, ERROR, CRITICAL
- `ExecutionError(BaseModel)`: phase, severity, message, details, timestamp
- `ComponentStatus(BaseModel)`: Track individual component build status
- `ExecutionState(BaseModel)`: Complete execution state with phases and errors
- `GenerationResult(BaseModel)`: Files generated, iterations, metrics
- `TestResult(BaseModel)`: Test execution results with pass/fail counts
- `ExecutionReport(BaseModel)`: Complete execution summary

**Key methods:**
- `ExecutionState.update_phase()`: Transition between execution phases
- `ExecutionState.get_progress()`: Calculate percentage complete
- `ComponentStatus.mark_completed()`: Update status with output files
- `GenerationResult.add_file()`: Track generated files
- `TestResult.success_rate()`: Calculate test pass percentage

### Component: Validation Models (`validation_model.py`)
Structured validation results with categorized issues and recommendations.

**Classes to implement:**
- `ValidationSeverity(str, Enum)`: INFO, WARNING, ERROR, CRITICAL
- `ValidationCategory(str, Enum)`: SYNTAX, SEMANTIC, STRUCTURE, CONSISTENCY, etc.
- `ValidationIssue(BaseModel)`: Base class with severity, category, message
- `ValidationError(ValidationIssue)`: Errors that must be fixed
- `ValidationWarning(ValidationIssue)`: Issues that should be reviewed
- `ValidationInfo(ValidationIssue)`: Informational messages
- `ValidationRule(BaseModel)`: Rule specification with parameters
- `ValidationResult(BaseModel)`: Complete validation with errors, warnings, info
- `ValidationContext(BaseModel)`: Context for validation operations
- `ValidationReport(BaseModel)`: Comprehensive report with recommendations

**Key methods:**
- `ValidationResult.get_errors_by_severity()`: Group issues by severity level
- `ValidationResult.get_errors_by_category()`: Group issues by category
- `ValidationResult.has_critical_errors()`: Check for blocking errors
- `ValidationReport.aggregate_results()`: Combine multiple validation results
- `ValidationReport.generate_summary()`: Create statistics summary

## Implementation Requirements

### All Models Must:
1. Use Pydantic BaseModel for validation
2. Include comprehensive type hints
3. Provide `Field(default_factory=list/dict)` for mutable defaults
4. Include docstrings for all classes and methods
5. Support JSON serialization/deserialization
6. Include appropriate `__str__` and `__repr__` methods
7. Handle optional fields with `Optional[Type]` or `Type | None`
8. Use enums for constrained string values
9. Include validation methods where appropriate
10. Follow Python naming conventions

### File Structure:
Each component should be a complete Python module with:
- Module-level docstring
- All necessary imports (pydantic, typing, datetime, enum, etc.)
- All classes defined in the component section
- Helper functions if needed
- No placeholder or stub implementations

### Quality Requirements:
- Zero pyright errors
- Pass ruff formatting and linting
- Include type hints for all parameters and returns
- Handle edge cases (empty lists, None values, etc.)
- Provide useful error messages in validators