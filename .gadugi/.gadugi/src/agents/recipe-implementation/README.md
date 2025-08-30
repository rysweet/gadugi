# Recipe Implementation Agent


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

An intelligent agent that automates the implementation of components from recipe specifications in the Gadugi v0.3 system.

## Overview

The Recipe Implementation Agent parses recipe files (requirements, design decisions, dependencies), evaluates existing code against these specifications, generates code to fill gaps, and validates the implementation for completeness and quality.

## Features

- **Recipe Parsing**: Extracts requirements, design decisions, interfaces, and dependencies from recipe files
- **Code Evaluation**: Analyzes existing code to identify gaps against recipe requirements
- **Code Generation**: Automatically generates Python code to implement missing functionality
- **Implementation Validation**: Validates generated code for syntax, structure, quality, and completeness
- **Test Generation**: Creates test files based on recipe requirements

## Components

### 1. RecipeParser (`recipe_parser.py`)
Parses recipe directories containing:
- `requirements.md` - Functional and non-functional requirements
- `design.md` - Architecture and design decisions
- `dependencies.json` - Component dependencies
- `interfaces.yaml` - Interface specifications
- `metadata.json` - Recipe metadata

### 2. CodeEvaluator (`code_evaluator.py`)
- Analyzes existing Python code structure
- Compares implementation against recipe requirements
- Identifies gaps with severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- Calculates coverage and compliance scores

### 3. CodeGenerator (`code_generator.py`)
- Generates Python implementations from recipe specifications
- Creates classes, functions, and interfaces
- Generates test files
- Fixes identified gaps in existing code

### 4. ImplementationValidator (`validator.py`)
- Validates syntax and structure
- Runs quality checks (docstrings, type hints, error handling)
- Executes tests
- Provides improvement suggestions

### 5. RecipeImplementationAgent (`agent.py`)
Main orchestrator that coordinates all components.

## Usage

### Basic Implementation

```python
from recipe_implementation import RecipeImplementationAgent

# Create agent
agent = RecipeImplementationAgent(verbose=True)

# Implement from recipe
result = agent.implement_from_recipe(
    recipe_path=Path(".claude/recipes/event-system"),
    code_path=Path("existing_code/"),  # Optional: existing code to evaluate
    output_path=Path("generated/"),     # Where to save generated code
    auto_fix=True,                      # Automatically fix gaps
    validate=True                       # Validate generated code
)

# Check results
print(f"Success: {result['summary']['success']}")
print(f"Files generated: {result['generation']['files_generated']}")
print(f"Test pass rate: {result['validation']['test_pass_rate']:.1%}")
```

### Step-by-Step Usage

```python
# 1. Parse recipe
recipe = agent.parse_recipe(Path(".claude/recipes/memory-system"))

# 2. Evaluate existing code
evaluation = agent.evaluate_code(
    code_path=Path("src/memory/"),
    recipe=recipe
)

# 3. Generate implementation
generated_code = agent.generate_code(
    recipe=recipe,
    evaluation=evaluation,
    output_path=Path("generated/")
)

# 4. Validate implementation
validation = agent.validate_code(
    code=generated_code,
    recipe=recipe
)

# 5. Create tests
test_code = agent.create_tests(recipe)
```

## Recipe Format

### Requirements File (`requirements.md`)

```markdown
## Functional Requirements

### Event Publishing
- Agents must be able to publish events with defined schemas
- Events must include metadata (timestamp, source, priority)
- Support for synchronous and asynchronous publishing

## Non-Functional Requirements

### Performance
- Handle 10,000+ events per second
- Sub-millisecond routing latency

## Quality Requirements

### Testing
- Unit tests with 90%+ coverage
- Integration tests for event flow
```

### Dependencies File (`dependencies.json`)

```json
{
  "libraries": {
    "asyncio": {
      "version": "3.9+",
      "required": true
    },
    "fastapi": {
      "version": "0.100+",
      "required": false,
      "alternatives": ["flask", "aiohttp"]
    }
  },
  "services": {
    "neo4j": {
      "version": "5.0+",
      "required": true
    }
  }
}
```

### Interfaces File (`interfaces.yaml`)

```yaml
interfaces:
  - name: EventRouter
    type: class
    description: Main event routing service
    parameters:
      - name: __init__
        type: method
      - name: publish_event
        type: method
      - name: subscribe
        type: method

  - name: process_event
    type: function
    description: Process incoming event
    parameters:
      - name: event
        type: Event
    returns:
      type: bool
```

## Output

The agent generates:

1. **Implementation Files**: Python modules implementing recipe requirements
2. **Test Files**: Unit tests for the implementation
3. **Validation Report**: Detailed analysis of implementation quality
4. **Gap Fixes**: Code to address identified gaps

## Quality Checks

The agent performs:
- Syntax validation
- Structure verification
- Docstring presence
- Type hint coverage
- Error handling verification
- Code formatting (ruff)
- Type checking (pyright)
- Test execution (pytest)

## Integration with Gadugi v0.3

The Recipe Implementation Agent integrates with:
- **Event System**: Implements event-driven components
- **MCP Service**: Generates memory management code
- **Neo4j Integration**: Creates database interaction layers
- **Testing Framework**: Generates pytest-compatible tests

## Requirements

- Python 3.9+
- Optional: ruff (for linting)
- Optional: pyright (for type checking)
- Optional: pytest (for test execution)

## Future Enhancements

- Support for multiple programming languages
- Machine learning-based code generation
- Automatic dependency resolution
- Integration with CI/CD pipelines
- Real-time collaboration features
