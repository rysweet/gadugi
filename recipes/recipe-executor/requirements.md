# Recipe Executor Requirements

## Core Purpose
The Recipe Executor is a self-hosting build system that transforms recipe specifications into fully functional software components. It serves as the foundation of the Gadugi system by reading structured recipe files, resolving dependencies between components, and generating production-quality code that adheres to strict quality standards. The system must be capable of regenerating itself from its own recipe specification, demonstrating true self-hosting capability.

## Functional Requirements

### 1. Recipe Structure Management

#### 1.1 Recipe File Parsing
- MUST read and parse three mandatory recipe files from each recipe directory:
  - `requirements.md`: Contains functional and non-functional requirements written in structured markdown format
  - `design.md`: Specifies the technical design, architecture, and implementation approach
  - `components.json`: Defines metadata, versioning, and dependencies on other recipes
- MUST validate that all three files exist and contain valid content before proceeding with recipe execution
- MUST parse markdown files to extract structured data such as requirement priorities (MUST, SHOULD, COULD), validation criteria, and success metrics
- MUST parse JSON files with proper error handling, providing clear messages about malformed JSON or missing required fields

#### 1.2 Recipe Validation
- MUST validate that each recipe contains all required sections and follows the expected structure
- MUST ensure that requirement identifiers are unique within a recipe and follow a consistent naming pattern (e.g., "req_1", "req_2")
- MUST verify that all referenced components in the design exist and are properly defined
- MUST check that success criteria are measurable and linked to specific requirements
- MUST validate that component types (service, agent, library, tool) are recognized and supported

#### 1.3 Requirements vs Design Separation Validation
- MUST validate that requirements.md contains only WHAT needs to be done, not HOW
- MUST detect design details (implementation specifics, technology choices, algorithms) in requirements
- MUST validate that design.md contains only HOW to implement, not WHAT to implement
- MUST detect requirements (functional needs, business rules) incorrectly placed in design
- MUST propose corrections when requirements and design are mixed
- MUST use AI to generate improved versions that properly separate concerns
- MUST check for common violations:
  - Implementation details in requirements (e.g., "MUST use PostgreSQL" vs "MUST persist data")
  - Functional requirements in design (e.g., "The system validates user input" vs "Uses Zod schema validation")
  - Technology choices in requirements (e.g., "MUST use React" vs "MUST provide web interface")

#### 1.4 Dependency Management
- MUST support hierarchical recipe dependencies where recipes can depend on other recipes (not Python packages)
  - Example: A "web-server" recipe might depend on "http-handler", "request-router", and "response-formatter" recipes
- MUST clearly distinguish between recipe dependencies (in components.json) and Python package dependencies (in pyproject.toml)
  - Recipe dependencies: `{"dependencies": ["base-recipe", "utility-recipe"]}`
  - Python dependencies: Managed through UV in generated pyproject.toml files
- MUST detect circular dependencies and fail immediately with a clear error message showing the cycle
  - Example error: "Circular dependency detected: recipe-a → recipe-b → recipe-c → recipe-a"
- MUST validate that all declared recipe dependencies actually exist in the recipe repository

### 2. Dependency Resolution

#### 2.1 Dependency Graph Construction
- MUST build a directed acyclic graph (DAG) representing all recipe dependencies
- MUST use topological sorting to determine the correct build order, ensuring dependencies are built before dependents
- MUST handle complex dependency trees with multiple levels and shared dependencies
  - Example: If both recipe-a and recipe-b depend on recipe-c, recipe-c must be built first and shared
- MUST optimize the dependency graph to identify opportunities for parallel execution

#### 2.2 Build Order Determination
- MUST execute recipes in strict topological order to ensure all dependencies are available when needed
- MUST group independent recipes that can be built in parallel at each level of the dependency graph
- MUST provide a visual or textual representation of the planned execution order for verification
- MUST support partial builds by analyzing which recipes are affected by changes

#### 2.3 Incremental Builds
- MUST detect when a recipe or its dependencies have changed by comparing checksums
- MUST trigger rebuilds only for changed recipes and their dependents, not the entire graph
- MUST provide options to force rebuild even when cache indicates no changes
- MUST track build state to know which recipes need rebuilding

### 3. Design Patterns Support

#### 3.1 Design Pattern Definition
- MUST support Design Patterns as reusable, composable recipe fragments
- MUST allow recipes to inherit from one or more Design Patterns
- MUST resolve and apply Design Patterns before recipe execution
- Design Patterns define:
  - Common project structure (scaffolding)
  - Quality standards (linting, formatting, testing)
  - Development practices (pre-commit hooks, CI/CD)
  - Architectural patterns (error handling, logging, monitoring)

#### 3.2 Design Pattern Structure
- MUST support Design Patterns stored in `patterns/` directory
- Each pattern MUST have:
  - `pattern.json`: Metadata and configuration
  - `requirements.md`: Requirements the pattern satisfies
  - `design.md`: Design decisions and implementation approach
  - `templates/`: Optional template files to include
- MUST support pattern composition (patterns using other patterns)

#### 3.3 Pattern Application
- MUST merge pattern requirements with recipe requirements
- MUST apply pattern design decisions to recipe implementation
- MUST include pattern templates in generated output
- MUST handle conflicts between patterns gracefully
- Example patterns:
  - `python-quality`: Ruff, pyright, pre-commit setup
  - `tdd-testing`: Test-first development setup
  - `cli-interface`: Click-based CLI scaffolding
  - `api-service`: REST API boilerplate

### 4. Recipe Complexity Evaluation

#### 4.1 Recipe Decomposition Analysis
- MUST evaluate each recipe for complexity before execution
- MUST determine if a recipe should be decomposed into smaller component recipes
- MUST check for indicators of excessive complexity:
  - More than 10 distinct components in design
  - More than 20 MUST requirements
  - Multiple unrelated functional areas
  - Mixing infrastructure, business logic, and UI concerns
- MUST recommend decomposition strategy when complexity threshold exceeded
- MUST support automatic recipe splitting into logical sub-recipes
- MUST validate that Recipe Executor's own recipe has been properly decomposed

### 5. Execution Engine

#### 5.1 Test-Driven Development (TDD) Red-Green-Refactor Cycle
- MUST follow strict TDD methodology with complete red-green-refactor cycles
- MUST create test files that cover all MUST requirements with specific test cases
  - Example: For a requirement "MUST parse JSON files", generate tests for valid JSON, invalid JSON, empty files, and missing files
- MUST ensure tests initially fail (red phase) before generating implementation
- MUST run generated tests to verify they fail appropriately
- MUST generate implementation code targeting test passage (green phase)
- MUST iteratively fix failing tests using dedicated test-solver agent
- MUST continue AI generation iterations until ALL tests pass
- MUST support refactoring phase while maintaining passing tests

#### 5.2 AI-Powered Code Generation
- MUST use AI-powered code generation, not template-based generation
- MUST create detailed generation prompts that include:
  - Complete requirements with validation criteria
  - Design specifications with architectural decisions
  - Existing test files that need to pass
  - Quality standards and coding conventions
- MUST parse generated output to extract files and their content
- MUST validate that generated code satisfies requirements before proceeding

#### 5.3 Code Quality Enforcement
- MUST ensure all generated Python code includes comprehensive type hints for every function, method, and variable
- MUST generate code that passes strict pyright type checking with absolutely zero errors
- MUST format all generated code with ruff for consistent style
- MUST include descriptive docstrings for all classes, methods, and functions
- MUST generate code that handles errors appropriately with try-except blocks and logging
- MUST support parallel execution where dependencies allow, utilizing available CPU cores efficiently

### 6. Code Review and Iteration

#### 6.1 Automated Code Review
- MUST perform automated code review on all generated code using dedicated code-reviewer agent
- MUST review for:
  - Adherence to Zero BS principle (no stubs, no placeholders)
  - Simplicity and avoiding over-engineering
  - Security vulnerabilities and unsafe patterns
  - Code quality and maintainability
  - Test coverage and quality
- MUST generate detailed review feedback with specific line-by-line comments
- MUST categorize issues as critical (must fix) or suggestions (nice to have)

#### 6.2 Review Response and Iteration
- MUST process code review feedback using code-review-response agent
- MUST fix all critical issues identified in review
- MUST iterate between implementation and review until all critical issues resolved
- MUST document review decisions and rationale for any suggestions not implemented
- MUST maintain review history for learning and pattern recognition

### 7. Post-Generation Validation

#### 7.1 Requirements Compliance Validation
- MUST validate generated artifacts against original recipe requirements
- MUST use dedicated validation agent to verify:
  - All MUST requirements have corresponding implementation
  - All design components are properly implemented
  - All interfaces match specifications
  - All success criteria can be demonstrated
- MUST generate compliance matrix showing requirement-to-code mapping
- MUST fail the build if any MUST requirement is not satisfied

#### 7.2 Artifact Completeness Check
- MUST verify all expected artifacts are generated:
  - Source code in proper directory structure
  - Comprehensive test suites with > 80% coverage
  - Configuration files (pyproject.toml, pyrightconfig.json, etc.)
  - Documentation (README.md, API docs, etc.)
- MUST validate artifact quality and completeness
- MUST ensure no partial or incomplete files

### 8. Self-Hosting Capability

#### 8.1 Bootstrap Process
- MUST be able to regenerate itself from its own recipe located in `recipes/recipe-executor/`
- MUST start from a minimal Python implementation that can read and execute the recipe-executor recipe
- MUST produce a new version of itself that is functionally identical to the current implementation
- MUST support iterative self-improvement where each generation can build the next

#### 8.2 Self-Protection
- MUST detect when output would overwrite Recipe Executor's own source files
- MUST refuse to overwrite files in `src/recipe_executor/` when running
- MUST provide clear error message when self-overwrite is attempted
- MUST suggest using a different output directory or git worktree for self-regeneration
- SHOULD support a `--allow-self-overwrite` flag only with explicit confirmation

#### 8.3 Self-Validation
- MUST validate that regenerated code capability matches current implementation through comprehensive testing
- MUST compare generated code structure with current implementation to ensure completeness
- MUST run the full test suite on the regenerated version to ensure no regressions
- MUST maintain backward compatibility with existing recipe formats during regeneration

#### 8.4 Version Management
- MUST track version numbers and ensure compatibility during self-regeneration
- MUST support upgrading from older versions while maintaining data and state
- MUST provide rollback capability if regeneration produces an incompatible version
- MUST document any breaking changes between versions

### 9. Component Generation

#### 9.1 Multi-Language Support
- MUST generate Python code as the primary implementation language
- MUST support generation of configuration files (JSON, YAML, TOML) from specifications
- MUST generate comprehensive documentation in Markdown format
- MUST support generation of shell scripts for automation tasks
- SHOULD support other languages through extensible generation plugins

#### 9.2 Project Structure
- MUST generate complete Python project structure including:
  - `src/` directory with proper package organization
  - `tests/` directory with comprehensive test coverage
  - `pyproject.toml` with UV configuration and dependencies
  - `pyrightconfig.json` for strict type checking
  - `.gitignore` with appropriate Python patterns
  - `README.md` with usage documentation
- MUST create `__init__.py` files with proper exports for all packages
- MUST organize code into logical modules following clean architecture principles

#### 9.3 Test Generation
- MUST generate pytest-compatible test files for all components
- MUST create unit tests for individual functions and methods
- MUST generate integration tests for component interactions
- MUST include fixtures and parameterized tests where appropriate
- MUST achieve minimum 80% code coverage with generated tests

### 10. Validation and Testing

#### 10.1 Requirements Validation
- MUST validate that implementations match requirements from the recipe
- MUST check that public APIs match the design specification
- MUST verify that all success criteria defined in the recipe are met
- MUST generate a requirements traceability matrix showing which code satisfies each requirement
- MUST fail the build if any MUST requirement is not satisfied

#### 10.2 Dependency Validation
- MUST ensure all dependencies are satisfied before execution begins
- MUST verify that dependency versions are compatible with requirements
- MUST check that dependency interfaces match expected contracts
- MUST validate that transitive dependencies don't introduce conflicts
- MUST provide clear error messages when dependencies are missing or incompatible

#### 10.3 Quality Gates
- MUST run generated tests and report results with detailed failure information
- MUST enforce quality gates at each stage of the build process
- MUST ensure all generated Python code passes strict pyright type checking with zero errors
  - Example: "error: Argument of type 'str | None' cannot be assigned to parameter of type 'str'"
- MUST format all generated code with ruff, automatically fixing style issues
- MUST use UV for package management in all Python projects, ensuring consistent dependency resolution
- MUST execute all generated tests with pytest and fail if any test fails
- MUST check code coverage and warn if below 80% threshold

### 11. State Management

#### 11.1 Build State Tracking
- MUST track build state and progress throughout the entire execution lifecycle
- MUST record which recipes have been built, when, and with what result
- MUST track dependencies between builds to understand impact of changes
- MUST support resuming interrupted builds from the last successful state
- MUST provide detailed build logs for troubleshooting failures

#### 11.2 Incremental Build Support
- MUST support incremental builds that only rebuild changed components
- MUST detect changes through file checksums and timestamps
- MUST propagate rebuilds to dependent components when dependencies change
- MUST reuse unchanged artifacts when possible
- MUST provide options to force full rebuilds when needed

#### 11.3 Build History and Artifacts
- MUST maintain build history with timestamps and outcomes
- MUST store all generated artifacts in a structured directory layout
- MUST support rollback to previous builds by restoring earlier artifacts
- MUST clean up old artifacts based on configurable retention policies
- MUST track build success rates

### 12. Stub Detection and Prevention

#### 12.1 Zero Stub Enforcement
- MUST detect stub implementations in generated code including:
  - `raise NotImplementedError` statements
  - Empty `pass` statements as function bodies
  - TODO, FIXME, XXX, HACK comments
  - Placeholder strings like "not yet implemented"
- MUST automatically attempt to remediate detected stubs using Claude Code
- MUST fail the build if stubs cannot be remediated after 3 attempts
- MUST provide clear reports showing exact location of detected stubs

#### 12.2 Code Completeness Validation
- MUST verify that all generated functions have actual implementations
- MUST check that generated tests actually test functionality (not just pass)
- MUST ensure no placeholder or template code remains in output
- MUST validate that all methods have more than trivial implementations

### 13. Recipe Execution Agents

#### 13.1 Core Recipe Agents
- MUST provide dedicated agents for recipe execution stages:
  - **RecipeDecomposer Agent**: Evaluates and decomposes complex recipes
  - **TestGenerator Agent**: Generates comprehensive test suites following TDD
  - **TestSolver Agent**: Iteratively fixes failing tests until all pass
  - **CodeReviewer Agent**: Reviews generated code for quality and compliance
  - **CodeReviewResponse Agent**: Addresses review feedback and fixes issues
  - **RequirementsValidator Agent**: Validates artifacts against recipe requirements
- MUST ensure agents follow proper specification format with defined tools and capabilities

#### 13.2 Agent Capabilities
- **RecipeExecutor Agent** MUST:
  - Execute any recipe with proper options
  - Validate no stubs in output
  - Handle incremental builds
  - Report detailed errors
- **RecipeWriter Agent** MUST:
  - Convert natural language to structured requirements
  - Separate requirements from design properly
  - Follow Zero BS principle in recipe creation
  - Generate valid components.json
- **RecipeExtractor Agent** MUST:
  - Analyze existing code structure
  - Extract requirements from implementation
  - Generate complete recipe sets
  - Create composite recipes for systems

### 14. Error Handling

#### 14.1 Error Detection and Reporting
- MUST provide clear error messages for recipe issues that explain what went wrong and how to fix it
  - Example: "Error in recipe 'web-server': Missing required file 'design.md'. Please create this file with the component design specifications."
- MUST fail fast on critical errors to avoid cascading failures
- MUST distinguish between recoverable and non-recoverable errors
- MUST include context about where and why the error occurred

#### 14.2 Recovery Logic  
- MUST allow manual retry of failed operations after fixes have been applied
- MUST support skipping failed optional components to continue build process
- MUST provide rollback capability when builds fail partway through

#### 14.3 Logging and Debugging
- MUST log all operations for debugging with configurable verbosity levels
- MUST support structured logging with timestamps, severity levels, and categories
- MUST provide trace-level logging for detailed troubleshooting
- MUST sanitize sensitive information from logs
- MUST support log rotation and archival for long-running operations

## Non-Functional Requirements

### Reliability
- MUST be deterministic where the same recipe inputs always produce identical outputs regardless of when or where they are executed
- MUST handle system failures gracefully without corrupting state or losing progress
- MUST maintain data integrity during crashes through atomic operations and proper transaction handling
- MUST support running in containerized environments for isolation and reproducibility
- MUST handle file system issues such as insufficient permissions, disk space constraints, and locked files

### Usability
- MUST provide clear progress indicators showing current operation
- MUST generate human-readable error messages that non-experts can understand and act upon
- MUST support dry-run mode for validation that checks everything without making any changes
- MUST provide detailed logs for troubleshooting at multiple verbosity levels
- MUST include helpful examples and comprehensive documentation accessible through CLI help commands

### Maintainability
- MUST follow clean architecture principles with clear separation of concerns between parsing, generation, and validation
- MUST have comprehensive test coverage exceeding 90% for all core components
- MUST be well-documented with examples for all public APIs and common use cases
- MUST support plugin architecture for extensions without modifying core functionality
- MUST use consistent coding standards enforced through automated tooling


### Security
- MUST validate all input files to prevent injection attacks and malicious content
- MUST run generated code in sandboxed environments during testing phase
- MUST not expose sensitive information such as API keys or passwords in logs or error messages
- MUST validate Claude Code responses to ensure no malicious code injection
- SHOULD support signing of generated artifacts for integrity verification

## Success Criteria

1. **Self-Regeneration Test**: The Recipe Executor can successfully regenerate itself from its own recipe, and the regenerated version passes all tests and can itself regenerate the Recipe Executor, demonstrating complete self-hosting capability.

2. **Complex Dependency Test**: Successfully builds a complex recipe graph with 10+ recipes, multiple dependency levels, and shared dependencies, executing in the correct order with parallel optimization where possible.

3. **Quality Compliance**: All generated code achieves:
   - Zero pyright errors in strict mode
   - 100% ruff formatting compliance
   - Minimum 90% test coverage
   - All tests passing with detailed reports

4. **Error Handling Test**: Provides clear, actionable error messages for common failure scenarios including:
   - Missing recipe files with suggestions for creation
   - Circular dependencies with visualization of the cycle
   - Invalid recipe format with specific line numbers
   - Generation failures with recovery suggestions
   - Test failures with debugging information

5. **Incremental Build Test**: Correctly identifies changed recipes and rebuilds only affected components, skipping unchanged recipes to avoid unnecessary Claude API calls.

6. **Parallel Build Test**: When building multiple independent recipes, executes them in parallel rather than sequentially.

7. **Documentation Quality**: Every generated component includes:
   - Complete README with installation and usage examples
   - Inline code documentation with type hints
   - API documentation with parameter descriptions
   - Test documentation explaining coverage and purpose

## Example Scenarios

### Scenario 1: Building a Web API Recipe
Given a recipe for a REST API with requirements for CRUD operations, authentication, and rate limiting, the Recipe Executor should:
1. Parse the requirements to identify all endpoints and security requirements
2. Generate comprehensive tests for each endpoint including success cases, failure cases, and edge cases
3. Generate implementation code with proper error handling, input validation, and security measures
4. Create integration tests that verify the complete API flow including authentication and rate limiting
5. Produce documentation with OpenAPI specifications, usage examples, and deployment instructions

### Scenario 2: Circular Dependency Detection
When recipe-a depends on recipe-b, and recipe-b depends on recipe-a, the system should:
1. Detect the circular dependency during graph construction phase
2. Generate a clear error message: "Circular dependency detected: recipe-a → recipe-b → recipe-a"
3. Provide a visual representation of the dependency cycle
4. Suggest solutions such as extracting common functionality to a shared recipe
5. Fail fast without attempting to build either recipe to avoid infinite loops

### Scenario 3: Incremental Build After Change
When a developer modifies the requirements.md file for a utility recipe that three other recipes depend on:
1. Detect the change through checksum comparison during initialization
2. Mark the utility recipe and its three dependents for rebuild
3. Skip rebuilding the dozens of unaffected recipes in the repository
4. Execute the rebuild in parallel where dependencies allow
5. Skip unaffected recipes and only rebuild what changed

### Scenario 4: Failed Test Recovery
When generated tests fail during execution:
1. Capture detailed test failure information including assertions and stack traces
2. Generate a report showing which requirements are not being met
3. Provide suggestions for fixing the implementation based on test expectations
4. Support re-running only the failed tests after fixes are applied
5. Maintain the build state to allow resumption without starting over