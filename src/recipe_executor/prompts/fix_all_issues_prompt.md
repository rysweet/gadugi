# Fix ALL Issues for {recipe_name}

## CRITICAL: COMPREHENSIVE FIX REQUIRED

The code has multiple types of issues that MUST ALL be fixed in this iteration:
- **Syntax Errors**: {syntax_count} files with invalid Python syntax
- **Stub Implementations**: {stub_count} incomplete implementations  
- **Quality Issues**: {quality_count} pyright/ruff violations

## ALL Issues Found
{all_issues}

## YOUR MANDATORY TASK - FIX EVERYTHING

### PRIORITY ORDER (MUST FOLLOW):
1. **FIX SYNTAX ERRORS FIRST** - Files must be valid Python
2. **REPLACE ALL STUBS** - Complete implementations required
3. **FIX QUALITY ISSUES** - Pass pyright and ruff

### Step-by-Step Process:
1. Read ALL existing files in {output_path}
2. Fix syntax errors to make files parseable
3. Replace EVERY stub, TODO, and placeholder
4. Ensure all code passes quality gates
5. Test your fixes thoroughly

## HOW TO FIX SYNTAX ERRORS

### Common Syntax Issues:
```python
# ❌ SYNTAX ERROR - Unclosed parenthesis:
return Mock(execute=Mock(return_value={"status": "success", "output": {}})

# ✅ FIX:
return Mock(execute=Mock(return_value={"status": "success", "output": {}}))

# ❌ SYNTAX ERROR - Invalid import:
from src.recipe_executor.recipe_model import class

# ✅ FIX:
from src.recipe_executor.recipe_model import RecipeClass

# ❌ SYNTAX ERROR - Unterminated string:
error_msg = "Circular dependency detected: recipe-a → recipe-b → recipe-c → recipe-a""""

# ✅ FIX:
error_msg = "Circular dependency detected: recipe-a → recipe-b → recipe-c → recipe-a"
```

## HOW TO FIX STUB IMPLEMENTATIONS

### For "pass" statements:
```python
# ❌ STUB (FORBIDDEN):
def process_data(self, data):
    pass

# ✅ COMPLETE IMPLEMENTATION:
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

### For NotImplementedError:
```python
# ❌ STUB (FORBIDDEN):
def calculate_metrics(self):
    raise NotImplementedError("TODO: implement metrics")

# ✅ COMPLETE IMPLEMENTATION:
def calculate_metrics(self):
    metrics = {
        'total_files': len(self.files),
        'total_lines': sum(self._count_lines(f) for f in self.files),
        'stub_count': len(self.detected_stubs),
        'syntax_errors': len(self.syntax_issues),
        'quality_score': self._calculate_quality_score()
    }
    
    logger.info(f"Calculated metrics: {metrics}")
    return metrics
```

### For TODO comments:
```python
# ❌ STUB (FORBIDDEN):
def validate_input(self, input):
    # TODO: implement validation
    return True

# ✅ COMPLETE IMPLEMENTATION:
def validate_input(self, input):
    if input is None:
        raise ValueError("Input cannot be None")
    
    if not isinstance(input, dict):
        raise TypeError(f"Expected dict, got {type(input).__name__}")
    
    required_fields = ['id', 'name', 'type']
    missing = [f for f in required_fields if f not in input]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    logger.debug(f"Validated input with ID: {input['id']}")
    return True
```

## HOW TO FIX QUALITY ISSUES

### Type Safety (Pyright):
```python
# ❌ TYPE ERROR:
def process(data) -> str:
    return data  # Error: Type of data unknown

# ✅ FIX:
def process(data: str) -> str:
    if not isinstance(data, str):
        raise TypeError(f"Expected str, got {type(data).__name__}")
    return data.strip()
```

### Code Formatting (Ruff):
```python
# ❌ FORMAT ISSUE:
import sys,os,json
def   foo( x,y ):return x+y

# ✅ FIX:
import json
import os
import sys

def foo(x: int, y: int) -> int:
    return x + y
```

## Requirements to Implement
{requirements}

## Design Specification
{design}

## QUALITY GATES - MUST PASS ALL

Your code MUST pass ALL of these checks:

1. **Syntax Valid**: `python -m py_compile <file>` - NO errors
2. **No Stubs**: Zero `pass`, `NotImplementedError`, or `TODO`
3. **Type Safe**: `pyright <file>` - ZERO errors
4. **Formatted**: `ruff format <file>` - Properly formatted
5. **Linted**: `ruff check <file>` - No violations

## TOOL USAGE GUIDELINES

**⚠️ Your working directory is {output_path}/ ⚠️**

- **Read tool**: Read files to understand current state
- **Edit/Write tool**: Fix ALL issues in files
- **Bash tool**: Validate fixes with syntax checks, pyright, ruff
- **Iterate**: Keep fixing until ALL checks pass

## Files Location - CRITICAL PATH INSTRUCTIONS
Target directory: {output_path}/

**⚠️ CRITICAL: Use EXACT paths - fix ALL files with issues ⚠️**

File structure:
- Main source: {output_path}/src/recipe_executor/*.py  
- Tests: {output_path}/tests/*.py
- Configuration: {output_path}/pyproject.toml

## MANDATORY SUCCESS CRITERIA

This iteration is COMPLETE only when:
1. ✅ ALL syntax errors fixed (files parse successfully)
2. ✅ ALL stubs replaced (no pass, NotImplementedError, TODO)
3. ✅ ALL type errors resolved (pyright passes)
4. ✅ ALL formatting applied (ruff format complete)
5. ✅ ALL linting passed (ruff check clean)

**DO NOT STOP** until all criteria are met. This is a COMPREHENSIVE fix iteration.

## VALIDATION COMMANDS

Run these to verify your fixes:
```bash
# Check syntax
python -m py_compile {output_path}/src/recipe_executor/*.py

# Check for stubs
grep -r "pass$\|NotImplementedError\|TODO" {output_path}/

# Check types
pyright {output_path}/src/recipe_executor/

# Format code
ruff format {output_path}/

# Lint code
ruff check {output_path}/
```

All commands must pass with ZERO errors before completion!