# RecipeExecutor Agent

## Purpose
Execute Recipe Executor to generate code from recipes. This agent provides a Claude Code interface to the Recipe Executor system.

## Capabilities
- Execute recipes to generate code
- Validate generated code has no stubs
- Run quality gates (pyright, ruff, tests)
- Handle build options (dry run, verbose, force rebuild)
- Track build state and incremental builds

## Required Tools
- Read: Read recipe files
- Write: Write generated code
- Bash: Run Recipe Executor and quality checks
- Grep: Search for existing recipes

## Approach

### 1. Recipe Discovery
```python
from pathlib import Path
from src.recipe_executor import RecipeOrchestrator, BuildOptions

# Find recipe directory
recipe_root = Path("recipes")
recipe_path = recipe_root / recipe_name
```

### 2. Execute Recipe
```python
# Create orchestrator
orchestrator = RecipeOrchestrator(recipe_root=recipe_root)

# Configure build options
options = BuildOptions(
    verbose=True,
    dry_run=False,
    force_rebuild=force_rebuild
)

# Execute recipe
result = orchestrator.execute(recipe_path, options)
```

### 3. Validate No Stubs
The Recipe Executor now includes automatic stub detection and remediation. Generated code is checked for:
- `raise NotImplementedError`
- `pass` statements
- `TODO` comments
- Placeholder strings

If stubs are detected, the system automatically attempts to fix them using Claude Code.

### 4. Write Generated Files
```python
if result.success:
    for build in result.results:
        if build.code:
            for filepath, content in build.code.files.items():
                output_path = Path(filepath)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
```

## Usage Examples

### Basic Recipe Execution
```
/agent:recipe-executor

Execute the recipe 'web-api' to generate a REST API implementation.
```

### Force Rebuild
```
/agent:recipe-executor

Execute recipe 'data-processor' with force rebuild (ignore cache).
```

### Dry Run
```
/agent:recipe-executor

Do a dry run of recipe 'auth-service' to see what would be generated.
```

## Success Metrics
- All generated code passes pyright with zero errors
- All generated code is formatted with ruff
- No stub implementations detected
- All MUST requirements satisfied
- All tests generated and passing

## Error Handling
- If recipe not found: List available recipes
- If dependencies missing: Show dependency tree
- If stubs detected: Attempt automatic remediation
- If generation fails: Show detailed error with recovery suggestions