# Fix Incomplete Implementation for {recipe_name}

## CRITICAL: REPLACE ALL STUBS WITH REAL IMPLEMENTATIONS

The code contains stubs/placeholders that MUST be replaced with COMPLETE implementations.

## Stub/TODO Issues Found
{stub_errors}

## YOUR MANDATORY TASK
1. Read ALL existing files in {output_path}
2. Find EVERY stub, TODO, and placeholder implementation
3. Replace them with COMPLETE, WORKING implementations
4. Every function must have MINIMUM 3-5 lines of real logic
5. Use any tools necessary to fix the issues and test your fixes

## HOW TO FIX EACH TYPE OF STUB

### For "pass" statements:
```python
# ❌ CURRENT (FORBIDDEN):
def process_data(self, data):
    pass

# ✅ REPLACE WITH:
def process_data(self, data):
    if not data:
        raise ValueError("Data cannot be empty")
    
    processed = []
    for item in data:
        validated = self._validate_item(item)
        transformed = self._transform_item(validated)
        processed.append(transformed)
    
    logger.info(f"Processed {len(processed)} items")
    return ProcessedResult(items=processed, count=len(processed))
```

### For placeholder returns:
```python
# ❌ CURRENT (FORBIDDEN):
def calculate_metrics(self, values):
    return {}

# ✅ REPLACE WITH:
def calculate_metrics(self, values):
    if not values:
        return {
            'count': 0,
            'sum': 0.0,
            'average': 0.0,
            'min': None,
            'max': None
        }
    
    numeric_values = [float(v) for v in values if v is not None]
    return {
        'count': len(numeric_values),
        'sum': sum(numeric_values),
        'average': sum(numeric_values) / len(numeric_values) if numeric_values else 0.0,
        'min': min(numeric_values) if numeric_values else None,
        'max': max(numeric_values) if numeric_values else None
    }}
```

### For TODO comments:
```python
# ❌ CURRENT (FORBIDDEN):
def validate_input(self, input):
    # TODO: implement validation
    return True

# ✅ REPLACE WITH:
def validate_input(self, input):
    if input is None:
        raise ValueError("Input cannot be None")
    
    if not isinstance(input, dict):
        raise TypeError(f"Expected dict, got {type(input).__name__}")
    
    required_fields = ['id', 'name', 'type']
    missing = [f for f in required_fields if f not in input]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    if not input.get('id'):
        raise ValueError("ID cannot be empty")
    
    logger.debug(f"Validated input with ID: {input['id']}")
    return True
```

## Requirements to Implement
{requirements}

## Design Specification
{design}

## TOOL USAGE GUIDELINES

**⚠️ Your working directory is {output_path}/ ⚠️**

- **Edit tool**: Fix existing files in `{output_path}/src/*.py` and `{output_path}/tests/*.py`
- **Write tool**: Create any NEW files needed in `{output_path}/`
- **Read/Grep tools**: Research patterns and validate fixes as needed
- **Bash tool**: Run tests and validate your fixes
- **DO NOT modify** `src/recipe_executor/` - that's the reference implementation

## MANDATORY FIXES
For EVERY function in EVERY file:
1. **Remove ALL `pass` statements** - Replace with real logic
2. **Remove ALL TODO comments** - Implement the functionality NOW
3. **Fix ALL placeholder returns** - Return meaningful computed values
4. **Add input validation** - Check for None, empty, invalid types
5. **Add error handling** - Raise meaningful exceptions
6. **Add logging** - Log important operations
7. **Ensure 3-5+ lines of logic** - No trivial implementations

## Files Location - CRITICAL PATH INSTRUCTIONS
Target directory: {output_path}/

**⚠️ CRITICAL: You MUST use EXACT paths as shown below - no shortcuts! ⚠️**

IMPORTANT - You MUST create/fix files using these EXACT paths:
- Main source files: {output_path}/src/*.py  
- Test files: {output_path}/tests/*.py
- CLI entry: {output_path}/cli.py
- Configuration: {output_path}/pyproject.toml

**MANDATORY FILE CREATION INSTRUCTIONS:**

1. **For NEW files** - Use Write tool with EXACT paths like:
   ```
   Write tool with file_path: {output_path}/src/__init__.py
   Write tool with file_path: {output_path}/src/recipe_executor.py
   Write tool with file_path: {output_path}/src/recipe_model.py
   Write tool with file_path: {output_path}/tests/test_recipe_executor.py
   Write tool with file_path: {output_path}/cli.py
   Write tool with file_path: {output_path}/pyproject.toml
   ```

2. **DO NOT CREATE FILES IN:**
   - ❌ `src/recipe_executor/` (wrong - this is the existing source)
   - ❌ `./` (wrong - this is root directory)
   - ❌ Any path without `{output_path}` prefix

3. **ALWAYS INCLUDE THE FULL PATH:**
   - ✅ CORRECT: `{output_path}/src/ast_stub_detector.py`
   - ❌ WRONG: `ast_stub_detector.py`
   - ❌ WRONG: `src/ast_stub_detector.py`

THIS IS MANDATORY - The build will FAIL if ANY stubs remain or if no files are created!