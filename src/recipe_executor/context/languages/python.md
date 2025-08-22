# Python-Specific Guidelines

## Language Standards

### Code Quality Requirements
- **Type Hints**: MUST use type hints for all function signatures
- **Docstrings**: MUST include comprehensive docstrings for all public functions
- **Format**: MUST be formatted with `ruff format` (or `black`)
- **Lint**: MUST pass `ruff check` (or `flake8`)
- **Type Check**: MUST pass `pyright` or `mypy` with zero errors

### Project Structure
```
project/
├── src/
│   └── module_name/
│       ├── __init__.py
│       ├── core.py
│       └── models.py
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_models.py
├── pyproject.toml
├── README.md
└── .gitignore
```

### Testing Framework
- Use `pytest` for testing
- Include fixtures in `conftest.py`
- Use parameterized tests where appropriate
- Aim for 80%+ code coverage

### Package Management
- Prefer `uv` for virtual environment management
- Use `pyproject.toml` for project configuration
- Pin dependencies with exact versions

### Python-Specific Patterns

#### Error Handling
```python
class CustomError(Exception):
    """Custom exception with context."""
    def __init__(self, message: str, context: dict):
        super().__init__(message)
        self.context = context
```

#### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def resource_manager():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)
```

#### Dataclasses for Models
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Model:
    id: str
    name: str
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
```

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local application imports

Each group separated by a blank line, sorted alphabetically.

### Async/Await Support
When implementing async functionality:
- Use `asyncio` for concurrency
- Prefer `async with` for async context managers
- Use `asyncio.gather()` for parallel execution
- Include proper error handling with `try/except`

### Logging Best Practices
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic info")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical failures")
```