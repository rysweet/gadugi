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
    
    logger.info(f"Processed {{len(processed)}} items")
    return ProcessedResult(items=processed, count=len(processed))
```

### For placeholder returns:
```python
# ❌ CURRENT (FORBIDDEN):
def calculate_metrics(self, values):
    return {{}}

# ✅ REPLACE WITH:
def calculate_metrics(self, values):
    if not values:
        return {{
            'count': 0,
            'sum': 0.0,
            'average': 0.0,
            'min': None,
            'max': None
        }}
    
    numeric_values = [float(v) for v in values if v is not None]
    return {{
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
        raise TypeError(f"Expected dict, got {{type(input).__name__}}")
    
    required_fields = ['id', 'name', 'type']
    missing = [f for f in required_fields if f not in input]
    if missing:
        raise ValueError(f"Missing required fields: {{missing}}")
    
    if not input.get('id'):
        raise ValueError("ID cannot be empty")
    
    logger.debug(f"Validated input with ID: {{input['id']}}")
    return True
```

## Requirements to Implement
{requirements}

## Design Specification
{design}

## MANDATORY FIXES
For EVERY function in EVERY file:
1. **Remove ALL `pass` statements** - Replace with real logic
2. **Remove ALL TODO comments** - Implement the functionality NOW
3. **Fix ALL placeholder returns** - Return meaningful computed values
4. **Add input validation** - Check for None, empty, invalid types
5. **Add error handling** - Raise meaningful exceptions
6. **Add logging** - Log important operations
7. **Ensure 3-5+ lines of logic** - No trivial implementations

## Files Location
Target directory: {output_path}

IMPORTANT: 
- If no files exist yet, use Write tool to CREATE new files with complete implementations
- If files exist, use Edit tool to fix any stubs in the existing files
- Start immediately by either creating files or reading and fixing existing ones

THIS IS MANDATORY - The build will FAIL if ANY stubs remain or if no files are created!