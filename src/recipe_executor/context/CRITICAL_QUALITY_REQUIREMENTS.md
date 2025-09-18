# CRITICAL QUALITY REQUIREMENTS FOR CODE GENERATION

## 🚨 MANDATORY PYTHON VERSION AND SYNTAX REQUIREMENTS

### Python Version Target: 3.9+
**ALL GENERATED CODE MUST BE COMPATIBLE WITH PYTHON 3.9**

❌ **NEVER USE Python 3.10+ syntax:**
```python
# ❌ FORBIDDEN - Python 3.10+ union syntax
def method(self, value: str | None) -> list[str] | None:
    pass

# ❌ FORBIDDEN - Python 3.10+ match/case
match value:
    case "a":
        return 1
```

✅ **ALWAYS USE Python 3.9 compatible syntax:**
```python
# ✅ CORRECT - Python 3.9 compatible
from typing import Optional, List, Union

def method(self, value: Optional[str]) -> Optional[List[str]]:
    # Proper implementation here
    if value is None:
        return None
    return [value]

# ✅ CORRECT - Use if/elif instead of match
if value == "a":
    return 1
elif value == "b":
    return 2
```

## 📝 TYPE ANNOTATION REQUIREMENTS

### ALWAYS Import from typing module for Python 3.9:
```python
# ✅ REQUIRED imports at top of EVERY file
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
```

### Dataclass Field Defaults:
```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MyClass:
    # ❌ FORBIDDEN - Never use None as default for collections
    items: List[str] = None  # WRONG!
    
    # ✅ CORRECT - Use field(default_factory)
    items: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # ✅ CORRECT - Optional fields
    name: Optional[str] = None
    count: Optional[int] = None
```

## 🔧 RUFF COMPLIANCE REQUIREMENTS

### Code Style Rules:
1. **No nested if statements** - Combine with `and`
   ```python
   # ❌ FORBIDDEN
   if condition1:
       if condition2:
           do_something()
   
   # ✅ CORRECT
   if condition1 and condition2:
       do_something()
   ```

2. **Use enumerate() for index tracking**
   ```python
   # ❌ FORBIDDEN
   i = 0
   for item in items:
       process(i, item)
       i += 1
   
   # ✅ CORRECT
   for i, item in enumerate(items):
       process(i, item)
   ```

3. **Import organization**
   ```python
   # ✅ CORRECT order
   # 1. Standard library
   import os
   import sys
   from pathlib import Path
   
   # 2. Third party
   import pytest
   
   # 3. Local imports
   from .recipe_model import Recipe
   ```

## 🎯 PYRIGHT STRICT MODE REQUIREMENTS

### Every function MUST have complete type hints:
```python
# ❌ FORBIDDEN - Missing type hints
def process(data):
    return data.upper()

# ✅ CORRECT - Full type hints
def process(data: str) -> str:
    """Process the input data.
    
    Args:
        data: Input string to process
        
    Returns:
        Processed uppercase string
    """
    return data.upper()
```

### Handle Optional types properly:
```python
def process(value: Optional[str]) -> str:
    # ✅ CORRECT - Check for None first
    if value is None:
        return ""
    return value.upper()
```

## 🧪 PYTEST REQUIREMENTS

### Every module MUST have testable functions:
```python
# ✅ Every class needs at least:
class MyClass:
    def __init__(self):
        self.data = []
    
    def validate(self) -> bool:
        """Validation method that can be tested."""
        return len(self.data) > 0
    
    def process(self, input_data: str) -> str:
        """Processing method with clear inputs/outputs."""
        if not input_data:
            raise ValueError("Input cannot be empty")
        return input_data.strip().lower()
```

## 🚫 FORBIDDEN PATTERNS - AUTOMATIC FAILURE

These patterns will cause IMMEDIATE quality gate failure:

1. **Empty implementations**
   ```python
   def method(self):
       pass  # ❌ INSTANT FAILURE
       
   def method(self):
       ...  # ❌ INSTANT FAILURE
       
   def method(self):
       raise NotImplementedError  # ❌ INSTANT FAILURE
   ```

2. **Missing error handling**
   ```python
   # ❌ FORBIDDEN
   def read_file(path: str):
       return open(path).read()
   
   # ✅ CORRECT
   def read_file(path: str) -> str:
       try:
           with open(path, 'r') as f:
               return f.read()
       except FileNotFoundError:
           logger.error(f"File not found: {path}")
           raise
       except Exception as e:
           logger.error(f"Error reading file {path}: {e}")
           raise
   ```

## ✅ QUALITY CHECKLIST FOR EVERY FILE

Before considering ANY file complete, verify:

- [ ] Uses Python 3.9 compatible syntax (no `|` unions, no match/case)
- [ ] Imports from `typing` module for all type hints
- [ ] All functions have complete type annotations
- [ ] All functions have docstrings
- [ ] No nested if statements (use `and` instead)
- [ ] Uses enumerate() for index iteration
- [ ] Dataclass fields use field(default_factory) for collections
- [ ] Optional fields properly typed as Optional[T]
- [ ] Proper error handling with try/except
- [ ] Logging statements for debugging
- [ ] No stub implementations (pass, ..., NotImplementedError)
- [ ] At least one testable method per class

## 🎯 TARGET METRICS

Generated code MUST achieve:
- **0 pyright errors** when run with Python 3.9 target
- **0 ruff format issues**
- **0 ruff lint errors**
- **100% valid Python syntax**
- **0 stub implementations**