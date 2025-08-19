# Implement Neo4j Service - Core Persistence Layer

## Objective
Implement the missing Neo4j service for Gadugi v0.3's persistence layer.

## Requirements
1. **Docker Container Setup**
   - Neo4j container running on port 7475
   - Authentication: neo4j/gadugi-password
   - Persistent volume for data

2. **Service Implementation**
   - Location: `.claude/services/neo4j/`
   - Python client with connection pooling
   - Schema initialization script
   - CRUD operations for entities

3. **Core Functionality**
   - Recipe storage and retrieval
   - Agent state persistence
   - Task tracking
   - Event logging

## Implementation Files
```
.claude/services/neo4j/
├── __init__.py
├── client.py          # Neo4j client with connection pooling
├── models.py          # Data models
├── schema.py          # Schema initialization
├── docker-compose.yml # Container definition
└── tests/
    └── test_neo4j.py  # Integration tests
```

## Docker Setup
```yaml
# docker-compose.yml
services:
  gadugi-neo4j:
    image: neo4j:latest
    container_name: gadugi-neo4j
    ports:
      - "7475:7474"  # HTTP
      - "7688:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/gadugi-password
    volumes:
      - ./data:/data
```

## Testing
```bash
# Start Neo4j
docker-compose up -d

# Test connection
uv run python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7688', auth=('neo4j', 'gadugi-password')); driver.verify_connectivity()"

# Run tests
uv run pytest .claude/services/neo4j/tests/ -v
```

## Success Criteria
- Container starts and accepts connections
- Schema initialized properly
- All CRUD operations work
- Tests pass
- Zero pyright errors

This is a UV project - use `uv run` for all Python commands.

Create PR when complete.
