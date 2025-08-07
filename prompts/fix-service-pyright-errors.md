# Fix Service File Pyright Errors (43 errors)

## Target Files
- gadugi-v0.3/services/neo4j-graph/neo4j_graph_service.py (34 errors)
- gadugi-v0.3/services/mcp/mcp_service.py (9 errors)

## Fix Patterns

### Neo4j Service
```python
try:
    from neo4j import GraphDatabase, AsyncGraphDatabase  # type: ignore[import]
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    AsyncGraphDatabase = None
```

### MCP Service
```python
try:
    import redis  # type: ignore[import]
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
```

### Dataclass Fields
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ServiceConfig:
    items: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
```

## Steps
1. Create branch: feature/pyright-service-fixes
2. Fix neo4j_graph_service.py imports and dataclass fields
3. Fix mcp_service.py imports and dataclass fields
4. Run `npx pyright gadugi-v0.3/services/` to verify 0 errors
5. Create PR to feature/gadugi-v0.3-regeneration

## Success Criteria
- Both service files have 0 pyright errors
- Optional imports handled correctly
- All dataclass fields properly initialized