# CRITICAL: ABSOLUTELY NO STUBS - ZERO TOLERANCE POLICY

## ⛔ THIS IS A HARD REQUIREMENT - FAILURE MEANS REJECTION ⛔

### THE GOLDEN RULE
**EVERY FUNCTION MUST HAVE A COMPLETE, WORKING IMPLEMENTATION**

### FORBIDDEN PATTERNS - AUTOMATIC FAILURE

These patterns will cause IMMEDIATE REJECTION:

```python
# ❌ FORBIDDEN - NEVER DO THIS
def some_method(self):
    pass  # ABSOLUTELY FORBIDDEN!

def another_method(self):
    raise NotImplementedError  # ABSOLUTELY FORBIDDEN!

def third_method(self):
    ...  # ABSOLUTELY FORBIDDEN!

def fourth_method(self):
    # TODO: implement this  # ABSOLUTELY FORBIDDEN!
    return

def fifth_method(self):
    return None  # FORBIDDEN if that's the only line!
```

### REQUIRED PATTERNS - WHAT YOU MUST DO

```python
# ✅ REQUIRED - ALWAYS DO THIS
def some_method(self):
    """Complete implementation."""
    logger.debug("Processing started")
    
    # Actual logic here
    result = []
    for item in self.data:
        processed = self._process_item(item)
        result.append(processed)
    
    logger.info(f"Processed {len(result)} items")
    return result

def another_method(self):
    """Another complete implementation."""
    if not self.initialized:
        self._initialize()
    
    # Real processing
    output = self.transform(self.input_data)
    self.validate(output)
    
    return output
```

## IMPLEMENTATION REQUIREMENTS FOR COMMON METHODS

### For `__init__` methods:
```python
# ✅ CORRECT
def __init__(self):
    """Initialize with actual setup."""
    self.data = []
    self.cache = {}
    self.logger = logging.getLogger(__name__)
    self.initialized = False
    self._setup_internals()
```

### For validation methods:
```python
# ✅ CORRECT
def validate(self, data):
    """Actually validate the data."""
    errors = []
    
    if not data:
        errors.append("Data cannot be empty")
    
    if not isinstance(data, dict):
        errors.append(f"Expected dict, got {type(data)}")
    
    required_fields = ['name', 'type', 'value']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        raise ValidationError(f"Validation failed: {errors}")
    
    return True
```

### For processing methods:
```python
# ✅ CORRECT
def process(self, input_data):
    """Process with real logic."""
    # Pre-processing
    cleaned = self._clean_data(input_data)
    normalized = self._normalize(cleaned)
    
    # Main processing
    results = []
    for item in normalized:
        transformed = self._transform_item(item)
        validated = self._validate_item(transformed)
        results.append(validated)
    
    # Post-processing
    output = self._format_output(results)
    self._save_to_cache(output)
    
    return output
```

## ZERO EXTERNAL DEPENDENCIES RULE

### FORBIDDEN IMPORTS
```python
# ❌ NEVER import these
import networkx  # FORBIDDEN
import numpy  # FORBIDDEN
import pandas  # FORBIDDEN
import requests  # FORBIDDEN
from sklearn import *  # FORBIDDEN
```

### ALLOWED IMPORTS (Standard Library ONLY)
```python
# ✅ ONLY these are allowed
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
from datetime import datetime
import subprocess
import re
import hashlib
```

## IMPORT STRUCTURE RULES

### For internal imports - ALWAYS USE RELATIVE
```python
# ✅ CORRECT
from .recipe_model import Recipe
from .validator import Validator
from .orchestrator import Orchestrator

# ❌ WRONG
from recipe_executor.recipe_model import Recipe  # NO!
from src.recipe_executor.validator import Validator  # NO!
```

## VALIDATION CHECKLIST

Before generating ANY code, verify:

- [ ] ZERO `pass` statements (except abstract base classes)
- [ ] ZERO `raise NotImplementedError` (except abstract methods)
- [ ] ZERO `TODO`, `FIXME`, `XXX` comments
- [ ] ZERO external package imports
- [ ] ALL imports are relative for internal modules
- [ ] EVERY function has actual implementation logic
- [ ] EVERY method does something meaningful
- [ ] NO placeholder returns
- [ ] NO empty function bodies

## CONSEQUENCES OF VIOLATIONS

1. **Any `pass` statement** = IMMEDIATE FAILURE
2. **Any `NotImplementedError`** = IMMEDIATE FAILURE  
3. **Any TODO comment** = IMMEDIATE FAILURE
4. **Any external import** = IMMEDIATE FAILURE
5. **Any absolute internal import** = IMMEDIATE FAILURE

## THE CONTRACT

By generating code for Recipe Executor, you agree to:
1. Provide COMPLETE implementations for EVERY function
2. Use ONLY Python standard library
3. Use ONLY relative imports for internal modules
4. Include REAL logic in every method
5. NEVER leave placeholders or stubs

**REMEMBER: Recipe Executor MUST be able to regenerate itself. Stubs break self-hosting!**