# CRITICAL CODE GENERATION GUIDELINES

## ABSOLUTE REQUIREMENTS - VIOLATION MEANS BUILD FAILURE

### NO STUBS OR PLACEHOLDERS - ZERO TOLERANCE

**THE FOLLOWING WILL CAUSE IMMEDIATE BUILD FAILURE:**

1. **Functions with just `pass`** - FORBIDDEN
2. **Functions that return `None`, `{}`, `[]`, or dummy values** - FORBIDDEN
3. **TODO comments** - FORBIDDEN
4. **NotImplementedError** - FORBIDDEN
5. **Functions that just return their input unchanged** - FORBIDDEN
6. **Placeholder text like "Add implementation here"** - FORBIDDEN
7. **Empty exception classes with just `pass`** - FORBIDDEN
8. **Functions with less than 3-5 lines of real logic** - FORBIDDEN

### COMPLETE IMPLEMENTATION FIRST TIME

**YOU MUST GENERATE COMPLETE, WORKING CODE ON THE FIRST ATTEMPT**

- No iterative development - get it right the first time
- No "we'll implement this later" - implement it NOW
- No "basic implementation" - full implementation ONLY
- Every function must DO REAL WORK
- Every component must be FULLY FUNCTIONAL
- Every requirement must be SATISFIED

### Zero BS Principle (from .claude/Guidelines.md)

**NO BULLSHIT. NO CLAIMS WITHOUT EVIDENCE. NO FAKE COMPLETIONS.**

- If you can't implement it fully, STOP and report the issue
- Don't pretend something works when it doesn't
- Don't create shells that need filling in later
- Create PRODUCTION-QUALITY code that runs immediately

### What "Real Implementation" Means

Every function must:
1. **Transform data** - Take input and produce meaningful output
2. **Validate inputs** - Check for errors and edge cases
3. **Handle errors** - Proper exception handling with context
4. **Perform its stated purpose** - Actually do what the name suggests
5. **Have substance** - Minimum 3-5 lines of actual logic

### Examples of FAILURES vs SUCCESS

**❌ FAILURE - Will be rejected:**
```python
def process_data(data):
    pass  # TODO: implement

def validate_input(input):
    return True  # Placeholder

def transform_records(records):
    return records  # Just returns input

def calculate_metrics(data):
    return {}  # Returns dummy value
```

**✅ SUCCESS - Acceptable implementations:**
```python
def process_data(data):
    if not data:
        raise ValueError("Data cannot be empty")
    
    processed = []
    for item in data:
        validated = self._validate_item(item)
        transformed = self._apply_transformations(validated)
        processed.append(transformed)
    
    return ProcessedData(
        items=processed,
        count=len(processed),
        timestamp=datetime.now()
    )

def validate_input(input):
    if not isinstance(input, dict):
        raise TypeError(f"Expected dict, got {type(input).__name__}")
    
    required_fields = ['id', 'name', 'value']
    missing = [f for f in required_fields if f not in input]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    if not input['id'] or not isinstance(input['id'], str):
        raise ValueError("ID must be a non-empty string")
    
    return True

def transform_records(records):
    if not records:
        return []
    
    transformed = []
    for record in records:
        transformed.append({
            'id': record.get('id', '').upper(),
            'name': record.get('name', '').strip().title(),
            'value': float(record.get('value', 0)),
            'processed_at': datetime.now().isoformat(),
            'checksum': hashlib.md5(str(record).encode()).hexdigest()
        })
    
    return transformed

def calculate_metrics(data):
    if not data:
        return {
            'count': 0,
            'sum': 0,
            'average': 0,
            'min': None,
            'max': None,
            'std_dev': 0
        }
    
    values = [float(d.get('value', 0)) for d in data]
    return {
        'count': len(values),
        'sum': sum(values),
        'average': sum(values) / len(values) if values else 0,
        'min': min(values) if values else None,
        'max': max(values) if values else None,
        'std_dev': self._calculate_std_dev(values)
    }
```

### Quality Requirements

Every generated file must:
1. **Pass pyright with ZERO errors**
2. **Pass ruff format and ruff check**
3. **Have comprehensive tests that pass**
4. **Include proper type hints**
5. **Include error handling**
6. **Include logging where appropriate**
7. **Be production-ready**

### If You Can't Implement Fully

If you cannot create a complete implementation:
1. **STOP immediately**
2. **Report what's blocking you**
3. **Don't create partial implementations**
4. **Don't create stubs to "fill in later"**

Better to fail fast than create incomplete code that will fail review.

## Remember: COMPLETE IMPLEMENTATION FIRST TIME OR DON'T GENERATE AT ALL