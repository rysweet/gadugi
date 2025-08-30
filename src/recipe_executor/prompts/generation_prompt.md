# Generate COMPLETE Implementation for {recipe_name}

## CRITICAL: NO STUBS - COMPLETE IMPLEMENTATION REQUIRED

**YOU MUST GENERATE COMPLETE, WORKING CODE - NO STUBS, NO PLACEHOLDERS**

### FORBIDDEN (Will cause immediate failure):
- Functions with just `pass`
- Functions that return `None`, `{}`, `[]` as placeholders
- TODO comments
- NotImplementedError
- Functions that just return their input unchanged
- Any function with less than 3-5 lines of real logic

### REQUIRED (Every function must have):
- Real data transformation or processing logic
- Input validation and error checking
- Proper error handling with meaningful messages
- Actual business logic implementation
- Logging of important operations

## Context
You are implementing a PRODUCTION-READY component based on the following recipe.

CRITICAL: You MUST use your Write tool to create actual files with COMPLETE implementations.

## Requirements

{requirements}

## Design Specification

{design}

### Components to Implement

{components}

### Implementation Notes

{implementation_notes}

## Target Language

Language: {language}

## Implementation Examples

### Example: Validation Function
```{language}
# ✅ CORRECT - Real implementation:
def validate_config(self, config: dict) -> ValidationResult:
    errors = []
    warnings = []
    
    # Check required fields
    required = ['name', 'version', 'components']
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: {{field}}")
    
    # Validate version format
    if 'version' in config:
        if not re.match(r'^\d+\.\d+\.\d+$', config['version']):
            errors.append(f"Invalid version format: {{config['version']}}")
    
    # Validate components
    if 'components' in config:
        if not isinstance(config['components'], list):
            errors.append("Components must be a list")
        elif len(config['components']) == 0:
            warnings.append("No components defined")
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

### Example: Processing Function
```{language}
# ✅ CORRECT - Real implementation:
def process_recipe(self, recipe_data: dict) -> ProcessedRecipe:
    # Parse and validate input
    if not recipe_data:
        raise ValueError("Recipe data cannot be empty")
    
    # Extract and transform fields
    name = recipe_data.get('name', '').strip()
    if not name:
        raise ValueError("Recipe name is required")
    
    # Process components
    components = []
    for comp_data in recipe_data.get('components', []):
        component = self._parse_component(comp_data)
        component = self._validate_component(component)
        component = self._enhance_component(component)
        components.append(component)
    
    # Build result with computed fields
    return ProcessedRecipe(
        name=name,
        components=components,
        component_count=len(components),
        processed_at=datetime.now(),
        checksum=self._calculate_checksum(recipe_data)
    )
```

## Code Quality Standards

- MUST have COMPLETE implementations - no stubs
- MUST follow {language} best practices and idioms
- MUST include proper type safety where applicable
- MUST be properly formatted according to {language} standards
- MUST include documentation for all public APIs
- MUST handle errors appropriately using {language} conventions
- MUST be production-ready, not prototype quality
- MUST use standard {language} project structure
- MUST use appropriate testing framework for {language}

## Import Convention Requirements

**CRITICAL FOR PYTHON PACKAGES**:
- MUST use relative imports within the same package (e.g., `from . import module`, `from .module import Class`)
- NEVER use absolute imports with the package name for internal imports
- For cross-package imports, use absolute imports
- Example for a package named `recipe_executor`:
  ```python
  # CORRECT - relative imports within package:
  from . import parser
  from .parser import RecipeParser
  from ..utils import helper  # parent package
  
  # WRONG - absolute imports within same package:
  from recipe_executor import parser  # DON'T DO THIS
  from recipe_executor.parser import RecipeParser  # DON'T DO THIS
  ```
- This ensures the package works correctly when installed or run as a module

## Output Structure

Generate files as specified in the design section.
Every file must contain COMPLETE, WORKING implementations.

## Dependencies

This recipe depends on: {dependencies}

## Success Criteria

{success_criteria}

## FINAL REMINDER

- **NO STUBS** - Every function must have real implementation
- **NO PLACEHOLDERS** - Complete working code only
- **NO TODO COMMENTS** - Finish everything now
- **MINIMUM 3-5 LINES OF LOGIC** per function
- If you cannot implement something fully, report the issue instead of creating a stub