# Pyright Type Safety Fix - Final Batch 1: Service Files

## Target: Fix 107 Errors in Service Files

### Priority Files (107 errors total)

#### 1. neo4j_graph_service.py (44 errors)
Common issues:
- Neo4j import resolution 
- Optional type handling
- Dataclass field initialization

Fixes needed:
```python
# Fix import issues
try:
    from neo4j import GraphDatabase  # type: ignore[import]
except ImportError:
    GraphDatabase = None

# Fix dataclass fields
from dataclasses import dataclass, field
@dataclass
class NodeData:
    labels: List[str] = field(default_factory=list)  # NOT: = None
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None  # Use Optional for datetime

# Fix Optional checks
if self.driver is not None:  # NOT: if self.driver:
    self.driver.close()
```

#### 2. gadugi_cli_service.py (33 errors)
Issues:
- Rich library import resolution
- Mock class missing methods
- Dataclass field initialization

Fixes:
```python
# Fix Rich imports
try:
    from rich.console import Console  # type: ignore[import]
    from rich.table import Table  # type: ignore[import]
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Enhanced mock classes
    class Table:
        def __init__(self, title: str = ""):
            self.title = title
        def add_column(self, name: str, **kwargs: Any) -> None:
            pass
        def add_row(self, *args: Any, **kwargs: Any) -> None:
            pass

# Fix return type
def get_name(self) -> str:
    return self.name or "default"  # NOT: return self.name (which could be None)
```

#### 3. mcp_service.py (17 errors)
Issues:
- Redis import handling
- Dataclass field initialization
- Optional datetime fields

Fixes:
```python
# Fix Redis import
try:
    import redis  # type: ignore[import]
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Fix dataclass fields
@dataclass
class MemoryEntry:
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None
```

#### 4. llm_proxy_service.py (13 errors)
Issues:
- OpenAI/Anthropic import handling
- AsyncGenerator types
- Optional field handling

Fixes:
```python
# Fix provider imports
try:
    import openai  # type: ignore[import]
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Fix async generator types
from typing import AsyncGenerator
async def stream_response(self) -> AsyncGenerator[str, None]:
    for chunk in chunks:
        yield chunk
```

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-final-batch-1-services
- Fix all 107 errors in service files
- Maintain functionality while adding type safety
- Test that services still work after fixes