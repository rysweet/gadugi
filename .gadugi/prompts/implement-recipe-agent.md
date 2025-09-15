# Task: Build Recipe Implementation Agent (#235)

## Description
Build the agent that implements components from recipes by parsing recipe files, evaluating existing code, and generating/modifying code to match specifications.

## Requirements
1. **Location**: `.claude/agents/recipe-implementation/`
2. **Purpose**: Automate implementation of components from recipe specifications

## Core Functionality
1. **Recipe Parsing**:
   - Parse `requirements.md` for functional/non-functional requirements
   - Parse `design.md` for architecture decisions
   - Parse `dependencies.json` for component dependencies
   - Extract interfaces and API specifications

2. **Code Evaluation**:
   - Analyze existing code against requirements
   - Identify gaps and missing functionality
   - Check compliance with design patterns
   - Validate interface implementations

3. **Code Generation**:
   - Generate new code to match recipes
   - Modify existing code to meet requirements
   - Create test files based on requirements
   - Ensure quality standards (pyright, ruff)

4. **Validation**:
   - Verify implementation matches recipe
   - Run generated tests
   - Check code quality metrics
   - Generate implementation report

## Agent Structure
```python
class RecipeImplementationAgent:
    def parse_recipe(recipe_path: Path) -> RecipeSpec
    def evaluate_existing_code(code_path: Path, recipe: RecipeSpec) -> EvaluationReport
    def generate_implementation(recipe: RecipeSpec, evaluation: EvaluationReport) -> GeneratedCode
    def validate_implementation(code: GeneratedCode, recipe: RecipeSpec) -> ValidationReport
    def create_tests(recipe: RecipeSpec) -> TestSuite
```

## Quality Requirements
- All Python code must use `uv run` for commands
- Code must be pyright clean
- Code must be ruff formatted
- All tests must pass
- Agent must be fully autonomous

## Files to Create
1. `.claude/agents/recipe-implementation/agent.py` - Main agent implementation
2. `.claude/agents/recipe-implementation/recipe_parser.py` - Recipe file parser
3. `.claude/agents/recipe-implementation/code_evaluator.py` - Code evaluation logic
4. `.claude/agents/recipe-implementation/code_generator.py` - Code generation logic
5. `.claude/agents/recipe-implementation/validator.py` - Implementation validator
6. `.claude/agents/recipe-implementation/models.py` - Data models
7. `.claude/agents/recipe-implementation/tests/test_agent.py` - Unit tests
8. `.claude/agents/recipe-implementation/__init__.py` - Module exports
9. `.claude/agents/recipe-implementation/README.md` - Agent documentation
