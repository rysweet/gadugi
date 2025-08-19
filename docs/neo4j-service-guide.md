# Neo4j Service Guide

## Overview

The Neo4j Service provides graph database functionality for the Gadugi system, offering persistent storage for recipes, agent states, workflows, and their relationships. This service is built with robust connection management, comprehensive data models, and extensive testing.

## Features

### 🔧 Core Functionality
- **Connection Management**: Connection pooling with automatic retry and failover
- **Schema Management**: Automated schema initialization with constraints and indexes
- **Data Models**: Rich entity models for Agents, Tools, Workflows, Recipes, Events, and Tasks
- **CRUD Operations**: Full create, read, update, delete operations for all entities
- **Health Monitoring**: Database health checks and performance statistics

### 🏗️ Architecture
- **Client Layer**: `Neo4jClient` with connection pooling and retry logic
- **Model Layer**: Abstract base classes with type-safe serialization
- **Schema Layer**: `SchemaManager` for database structure management
- **Container Layer**: Docker Compose setup for easy deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ with UV package manager
- Neo4j 5.19+ compatible environment

### 1. Start Neo4j Container

```bash
# Start Neo4j service
docker-compose -f .claude/services/neo4j_service/docker-compose.yml up -d

# Or use the main project compose file
docker-compose -f docker-compose.gadugi.yml up -d neo4j
```

### 2. Initialize Schema

```python
from claude.services.neo4j_service import Neo4jClient, SchemaManager

# Create client
client = Neo4jClient(
    uri="bolt://localhost:7688",
    user="neo4j",
    password="gadugi-password"  # pragma: allowlist secret
)

# Initialize schema
schema_manager = SchemaManager(client)
schema_manager.full_schema_setup()
```

### 3. Basic Usage

```python
from claude.services.neo4j_service import Agent, Tool, Context

# Create entities
agent = Agent(
    name="My Agent",
    type="worker",
    capabilities=["read", "write"],
    status="active"
)

tool = Tool(
    name="My Tool",
    category="file_ops",
    description="Does file operations"
)

# Save to Neo4j
with client:
    agent_result = client.create_entity(agent)
    tool_result = client.create_entity(tool)

    # Read entities
    saved_agent = client.read_entity("Agent", agent.id)

    # Update entities
    client.update_entity("Agent", agent.id, {"status": "updated"})

    # Delete entities
    client.delete_entity("Tool", tool.id)
```

## Configuration

### Connection Parameters
- **URI**: `bolt://localhost:7688` (default)
- **Authentication**: `neo4j/gadugi-password`
- **Connection Pool**: 100 max connections
- **Retry Logic**: 3 attempts with exponential backoff

### Docker Configuration
```yaml
services:
  neo4j:
    image: neo4j:5.19
    ports:
      - "7475:7474"  # HTTP
      - "7688:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/gadugi-password
    volumes:
      - neo4j_data:/data
```

## Data Models

### Base Entity
All entities inherit from `Neo4jEntityBase`:
```python
class Neo4jEntityBase(ABC):
    def __init__(self, id=None, created=None, updated=None, **kwargs):
        self.id = id or str(uuid.uuid4())
        self.created = created or datetime.now(timezone.utc)
        self.updated = updated
```

### Available Entities

#### Agent
Represents system agents and their capabilities.
```python
agent = Agent(
    name="Agent Name",
    type="worker|orchestrator|manager",
    description="Agent description",
    capabilities=["tool1", "tool2"],
    config={"setting": "value"},
    status="active|inactive|error"
)
```

#### Tool
Represents tools available to agents.
```python
tool = Tool(
    name="Tool Name",
    category="file_ops|execution|search",
    description="Tool description",
    parameters={"param": "schema"},
    version="1.0.0"
)
```

#### Workflow
Represents workflow executions.
```python
workflow = Workflow(
    name="Workflow Name",
    status="pending|running|completed|failed",
    phases=[{"phase": 1, "status": "completed"}],
    current_phase=2,
    agent_id="agent-123"
)
```

#### Recipe
Represents development recipes.
```python
recipe = Recipe(
    name="Recipe Name",
    requirements={"python": ">=3.9"},
    design={"pattern": "service"},
    dependencies=["recipe-1", "recipe-2"],
    status="draft|active|deprecated",
    version="1.0.0",
    author="author-name"
)
```

#### Event
Represents system events.
```python
event = Event(
    event_type="workflow_completed",
    source="agent-id",
    data={"key": "value"},
    status="pending|processed|failed",
    priority=1
)
```

#### Task
Represents individual tasks.
```python
task = Task(
    name="Task Name",
    description="Task description",
    status="pending|in_progress|completed|failed",
    priority=1,
    assigned_agent="agent-id",
    dependencies=["task-1", "task-2"]
)
```

## Schema Management

### Constraints
The service automatically creates unique constraints:
- `agent_id_unique`, `tool_id_unique`, `context_id_unique`
- `workflow_id_unique`, `recipe_id_unique`, `event_id_unique`, `task_id_unique`

### Indexes
Performance indexes are created for:
- **Names**: Fast lookups by entity names
- **Status**: Filtering by status fields
- **Timestamps**: Time-based queries
- **Types**: Categorization queries
- **Priorities**: Task/event ordering

### System Nodes
Initial system entities are created:
- System agents: `system`, `orchestrator`, `workflow_manager`
- Essential tools: `read`, `write`, `bash`, `grep`
- Relationships between system entities

## Error Handling

### Connection Failures
```python
from claude.services.neo4j_service import Neo4jConnectionError

try:
    client.connect()
except Neo4jConnectionError as e:
    print(f"Failed to connect: {e}")
```

### Retry Logic
- Automatic retry with exponential backoff
- Configurable max attempts and delay
- Circuit breaker patterns for stability

### Health Monitoring
```python
# Check database health
if client.health_check():
    print("Neo4j is healthy")

# Get detailed statistics
stats = client.get_stats()
print(f"Node counts: {stats['node_counts']}")
print(f"Relationship counts: {stats['relationship_counts']}")
```

## Testing

### Unit Tests
```bash
# Run all Neo4j service tests
uv run pytest .claude/services/neo4j_service/tests/ -v

# Run specific test categories
uv run pytest -k "TestNeo4jClient" -v
uv run pytest -k "TestNeo4jModels" -v
uv run pytest -k "TestSchemaManager" -v
```

### Integration Tests
```bash
# Start Neo4j first
docker-compose -f .claude/services/neo4j_service/docker-compose.yml up -d

# Run integration tests
uv run pytest -m integration -v
```

### Connection Testing
```bash
# Test basic connectivity
uv run python .claude/services/neo4j_service/connection_test.py
```

## Performance Considerations

### Connection Pooling
- Pool size: 100 connections (configurable)
- Connection lifetime: 1000 seconds
- Acquisition timeout: 60 seconds

### Query Optimization
- Use parameterized queries for safety
- Leverage indexes for filtering
- Batch operations when possible

### Monitoring
```python
# Get performance statistics
stats = client.get_stats()
print(f"Total nodes: {sum(stats['node_counts'].values())}")
print(f"Total relationships: {sum(stats['relationship_counts'].values())}")
```

## Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs gadugi-neo4j-service
```

#### Port Conflicts
The service uses non-standard ports to avoid conflicts:
- HTTP: 7475 (instead of 7474)
- Bolt: 7688 (instead of 7687)

#### Schema Issues
```python
# Validate schema state
schema_manager = SchemaManager(client)
validation = schema_manager.validate_schema()

if not validation["valid"]:
    print("Schema issues:", validation["errors"])
```

#### Test Failures
```bash
# Check if tests can connect
NEO4J_TEST_URI=bolt://localhost:7688 uv run pytest -v

# Reset test database
docker-compose down -v  # Removes volumes
docker-compose up -d
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Client will now log all operations
client = Neo4jClient(uri="bolt://localhost:7688")
```

## Security

### Authentication
- Default credentials: `neo4j/gadugi-password`
- Change credentials in production environments
- Use environment variables for sensitive data

### Network Security
- Bind to localhost only by default
- Use encrypted connections in production
- Configure firewall rules appropriately

### Data Protection
- Regular backups of Neo4j data volumes
- Encryption at rest (enterprise edition)
- Access control through Neo4j security features

## Development

### Adding New Entity Types
1. Create model class inheriting from `Neo4jEntityBase`
2. Define `label` property
3. Add to `__init__.py` exports
4. Create tests
5. Update schema if needed

### Contributing
- Follow existing code patterns
- Add comprehensive tests
- Update documentation
- Run quality checks: `uv run ruff check && uv run pyright && uv run pytest`

## References

- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Operations Manual](https://neo4j.com/docs/operations-manual/current/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
