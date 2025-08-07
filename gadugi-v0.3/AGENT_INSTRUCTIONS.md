# Agent Code Generation Instructions for Gadugi v0.3

## CRITICAL: Type Safety Requirements

**ALL agents generating Python code for Gadugi v0.3 MUST follow strict type safety rules.**

### 1. Mandatory Type Annotations

Every function MUST have complete type annotations:

```python
# ❌ WRONG - No type annotations
def process_task(task, config):
    return {"status": "complete"}

# ✅ CORRECT - Full type annotations
from typing import Dict, Any, Optional

def process_task(task: str, config: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return {"status": "complete"}
```

### 2. Optional Type Handling

Always use explicit `is not None` checks:

```python
# ❌ WRONG - Implicit truthiness check
if self.connection:
    self.connection.close()

# ✅ CORRECT - Explicit None check
if self.connection is not None:
    self.connection.close()
```

### 3. Async Function Types

All async functions need return type annotations:

```python
# ❌ WRONG - Missing async types
async def fetch_data():
    return await api_call()

# ✅ CORRECT - Proper async types
from typing import Optional, Dict, Any, AsyncGenerator

async def fetch_data() -> Optional[Dict[str, Any]]:
    return await api_call()

async def stream_data() -> AsyncGenerator[str, None]:
    for item in items:
        yield item
```

### 4. Dataclass Field Initialization

Use field factories for mutable defaults:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

# ❌ WRONG - Mutable default
@dataclass
class Config:
    items: List[str] = []
    settings: Dict[str, Any] = {}

# ✅ CORRECT - Field factories
@dataclass
class Config:
    items: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
```

### 5. Test File Import Setup

All test files MUST set up import paths correctly:

```python
# Add to the TOP of every test file
import sys
from pathlib import Path

# Add src directories to path
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
orchestrator_dir = src_dir / "orchestrator"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(orchestrator_dir) not in sys.path:
    sys.path.insert(0, str(orchestrator_dir))

# Now imports will work
from workflow_manager_engine import WorkflowManager
```

### 6. Common Type Patterns

#### Dictionary Types
```python
from typing import Dict, Any, List

# Specific types when possible
user_data: Dict[str, str] = {"name": "John", "email": "john@example.com"}

# Use Any for truly dynamic data
response: Dict[str, Any] = {"status": 200, "data": [...]}

# Nested structures
results: List[Dict[str, Any]] = []
```

#### Union Types
```python
from typing import Union

# For multiple possible types
def process(data: Union[str, int, float]) -> str:
    return str(data)
```

#### TypedDict for Structured Data
```python
from typing import TypedDict

class UserData(TypedDict):
    name: str
    age: int
    email: str
    active: bool

def get_user() -> UserData:
    return {"name": "John", "age": 30, "email": "john@example.com", "active": True}
```

### 7. Validation Before Commit

**MANDATORY**: Before committing any Python code:

1. **Run pyright check**:
   ```bash
   cd gadugi-v0.3
   npx pyright
   ```
   
2. **Fix ALL errors** (not just warnings)

3. **Verify specific file**:
   ```bash
   npx pyright path/to/your/file.py
   ```

### 8. Type Checking in IDEs

Configure your IDE for type checking:
- **VS Code**: Install Pylance extension
- **PyCharm**: Enable type checking in settings
- **Command line**: Use `pyright` or `mypy`

### 9. Import Organization

Keep imports organized and typed:

```python
# Standard library imports
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TypedDict

# Third-party imports
import pytest
from dataclasses import dataclass, field

# Local imports (after path setup in tests)
from workflow_manager_engine import WorkflowManager
```

### 10. Error Messages

When pyright reports errors, fix them properly:

- **reportMissingImports**: Add sys.path setup or install package
- **reportOptionalMemberAccess**: Add `is not None` check
- **reportGeneralTypeIssues**: Add proper type annotations
- **reportUnknownMemberType**: Specify concrete types instead of Any

## Enforcement

These rules are enforced by:
1. **Pre-commit hooks** - Runs pyright before allowing commits
2. **CI/CD pipeline** - Fails builds with type errors
3. **Code review** - Type safety is a merge requirement

## Questions?

If unsure about type annotations:
1. Check existing code in the same module
2. Use `reveal_type()` to see what pyright infers
3. Start with `Any` and refine to specific types
4. Ask for review if complex types are needed

Remember: **Type safety prevents bugs and improves code quality!**