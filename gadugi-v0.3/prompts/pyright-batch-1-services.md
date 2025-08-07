# Pyright Type Safety Fix - Batch 1: High-Error Services

## Target Files
Fix pyright errors in these service files with highest error counts:

### 1. services/neo4j-graph/neo4j_graph_service.py (44 errors)
Common issues:
- Missing type annotations on async functions
- Untyped dictionary returns
- Optional attribute access without None checks

Fixes needed:
```python
# Add type imports
from typing import Dict, List, Optional, Any, AsyncGenerator

# Fix async function signatures
async def method_name(self, param: str) -> Dict[str, Any]:
    
# Handle Optional attributes
if self.connection is not None:
    # safe to use self.connection
    
# Fix dictionary annotations
result: Dict[str, Any] = {}
```

### 2. services/cli/gadugi_cli_service.py (33 errors)
Common issues:
- Mock class methods missing implementations
- Dataclass field initialization
- Missing return type annotations

Fixes needed:
```python
# Fix mock classes
class MockClass:
    def __init__(self) -> None:
        pass
    
    def required_method(self) -> str:
        return "mock"

# Fix dataclass fields
from dataclasses import dataclass, field

@dataclass
class Config:
    items: List[str] = field(default_factory=list)
```

### 3. services/mcp/mcp_service.py (17 errors)
Common issues:
- Async generator type annotations
- Redis client type hints
- JSON serialization types

Fixes needed:
```python
# Fix async generators
async def stream_data(self) -> AsyncGenerator[Dict[str, Any], None]:
    yield {"data": "value"}
    
# Handle Redis optional
redis_client: Optional[Redis] = None
```

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-batch-1-services
- Fix actual type issues, don't just add ignores
- Test that functionality still works after fixes
- Commit each file separately with clear messages