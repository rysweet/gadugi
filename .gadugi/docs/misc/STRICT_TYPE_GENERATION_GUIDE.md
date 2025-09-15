# Guide for Generating Strict Type-Compliant Code

## The Problem
We keep generating code that fails strict type checking, then have to fix thousands of errors later. This is backwards - we should generate correct code from the start.

## Why Strict Type Checking is Hard

1. **Implicit Any Types**: Python allows untyped code, but strict mode forbids it
2. **Optional Handling**: Strict mode requires explicit None checks
3. **Complete Annotations**: Every function parameter and return must be typed
4. **No Type Inference Gaps**: Can't rely on type inference for complex cases

## How to Generate Strict Type-Compliant Code

### 1. ALWAYS Use Full Type Annotations

❌ **Bad** (generates type errors):
```python
def process_data(data):
    return data.get('value')

class Manager:
    def __init__(self):
        self.items = []
```

✅ **Good** (strict compliant):
```python
from typing import Any, Dict, List, Optional

def process_data(data: Dict[str, Any]) -> Optional[Any]:
    return data.get('value')

class Manager:
    def __init__(self) -> None:
        self.items: List[str] = []
```

### 2. Handle None/Optional Properly

❌ **Bad**:
```python
def get_user(user_id: int) -> User | None:
    user = fetch_user(user_id)
    return user.name  # Error: user might be None
```

✅ **Good**:
```python
def get_user(user_id: int) -> Optional[str]:
    user = fetch_user(user_id)
    if user is not None:
        return user.name
    return None
```

### 3. Use Dataclasses with Proper Field Definitions

❌ **Bad**:
```python
@dataclass
class Config:
    items = []  # Mutable default!
    value = None  # Type unknown!
```

✅ **Good**:
```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Config:
    items: List[str] = field(default_factory=list)
    value: Optional[int] = None
```

### 4. Import Type Checking Blocks

For circular imports or optional dependencies:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User  # Only imported for type checking
```

### 5. Protocol and ABC Usage

```python
from typing import Protocol

class Processor(Protocol):
    def process(self, data: str) -> int: ...

def use_processor(proc: Processor) -> None:
    result = proc.process("test")
```

### 6. Generic Types

```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)
```

## Template for New Python Files

```python
#!/usr/bin/env python3
"""Module description."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

# Type variables
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExampleClass:
    """Example with proper typing."""

    required_field: str
    optional_field: Optional[int] = None
    list_field: List[str] = field(default_factory=list)
    dict_field: Dict[str, Any] = field(default_factory=dict)

    def method(self, param: str) -> Optional[str]:
        """Method with full type annotations."""
        if not param:
            return None
        return param.upper()


def example_function(
    required: str,
    optional: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Function with complete type annotations."""
    result: Dict[str, Any] = {"required": required}

    if optional is not None:
        result["optional"] = optional

    result.update(kwargs)
    return result


class ExampleProtocol(Protocol):
    """Protocol for type checking."""

    def required_method(self, value: str) -> int:
        """Required method signature."""
        ...


def main() -> None:
    """Entry point with type annotation."""
    instance = ExampleClass(required_field="test")
    result = instance.method("hello")

    if result is not None:
        print(f"Result: {result}")


if __name__ == "__main__":
    main()
```

## Pyright Configuration for Strict Mode

```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.9",
  "reportMissingTypeStubs": false,  // Third-party libs may not have stubs
  "reportUnknownMemberType": false,  // Too strict for practical use
  "reportUnknownArgumentType": false,  // Too strict for practical use
  "reportUnknownVariableType": false,  // Too strict for practical use
  "reportUnknownLambdaType": false,  // Lambdas often have inference
  "reportUnknownParameterType": true,  // Important: all params typed
  "reportMissingParameterType": true,  // Important: no missing types
  "reportMissingTypeArgument": true,  // Generics must be complete
  "reportInvalidTypeVarUse": true,  // TypeVars must be used correctly
  "reportUnnecessaryTypeIgnoreComment": true,  // Clean up type: ignore
}
```

## Code Generation Rules

When generating new code, ALWAYS:

1. **Start with imports**: typing module, TYPE_CHECKING
2. **Add return type to __init__**: `-> None`
3. **Type all parameters**: No bare parameters
4. **Type all returns**: Even if None
5. **Type all class attributes**: In __init__ or class body
6. **Use Optional[]**: Not `| None` for Python < 3.10 compat
7. **Guard None access**: Check before accessing optional attributes
8. **Use field()**: For dataclass mutable defaults
9. **Cast when needed**: `cast(Type, value)` for type narrowing
10. **Add type: ignore sparingly**: Only for known issues with comment

## Testing Generated Code

Before committing any generated code:

```bash
# Save to file
echo "$generated_code" > temp_module.py

# Check with strict mode
echo '{"typeCheckingMode": "strict", "include": ["temp_module.py"]}' > temp_pyright.json
pyright --project temp_pyright.json temp_module.py

# Only commit if zero errors
```

## Common Patterns That ALWAYS Need Types

1. **Empty collections**:
   ```python
   items: List[str] = []
   data: Dict[str, Any] = {}
   ```

2. **Class attributes**:
   ```python
   self.name: str = "default"
   self.count: int = 0
   ```

3. **Function defaults**:
   ```python
   def func(items: Optional[List[str]] = None) -> None:
       if items is None:
           items = []
   ```

4. **Exception handling**:
   ```python
   try:
       value: int = int(input_str)
   except ValueError as e:
       value = 0
   ```

## Conclusion

By following these patterns from the start, we can generate code that passes strict type checking immediately, avoiding the need for massive cleanup campaigns later. The key is to be explicit about types from the moment we write the first line of code.
