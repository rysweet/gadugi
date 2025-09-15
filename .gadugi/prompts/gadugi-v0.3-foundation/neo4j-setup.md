# Neo4j Database Setup Task

## Objective
Set up Neo4j graph database for Gadugi v0.3 to store agents, memories, and knowledge nodes with proper relationships.

## Requirements

### 1. Docker Compose Configuration
Create `docker-compose.yml` in project root:
```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    container_name: gadugi-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/gadugi123
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_pagecache_size=512M
      - NEO4J_dbms_memory_heap_initial__size=512M
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - ./data/neo4j/data:/data
      - ./data/neo4j/logs:/logs
      - ./data/neo4j/import:/var/lib/neo4j/import
      - ./data/neo4j/plugins:/plugins
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:7474 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### 2. Graph Schema Definition
Create `neo4j/schema.cypher`:

#### Node Types
```cypher
// Agent Node
CREATE CONSTRAINT agent_id IF NOT EXISTS
FOR (a:Agent) REQUIRE a.id IS UNIQUE;

// Properties: id, name, type, version, status, created_at, updated_at, capabilities[]

// Memory Node
CREATE CONSTRAINT memory_id IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE;

// Properties: id, content, type, timestamp, agent_id, priority, tags[]

// Knowledge Node
CREATE CONSTRAINT knowledge_id IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.id IS UNIQUE;

// Properties: id, title, content, domain, confidence, source, created_at, verified

// Task Node
CREATE CONSTRAINT task_id IF NOT EXISTS
FOR (t:Task) REQUIRE t.id IS UNIQUE;

// Properties: id, description, status, priority, created_at, completed_at, result

// User Node
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

// Properties: id, name, role, preferences
```

#### Relationship Types
```cypher
// Agent Relationships
(a1:Agent)-[:DELEGATES_TO]->(a2:Agent)
(a:Agent)-[:CREATES]->(m:Memory)
(a:Agent)-[:EXECUTES]->(t:Task)
(a:Agent)-[:KNOWS]->(k:Knowledge)

// Memory Relationships
(m1:Memory)-[:REFERENCES]->(m2:Memory)
(m:Memory)-[:ABOUT]->(k:Knowledge)
(m:Memory)-[:GENERATED_BY]->(t:Task)

// Task Relationships
(t1:Task)-[:DEPENDS_ON]->(t2:Task)
(t1:Task)-[:SUBTASK_OF]->(t2:Task)
(t:Task)-[:ASSIGNED_TO]->(a:Agent)
(t:Task)-[:REQUESTED_BY]->(u:User)

// Knowledge Relationships
(k1:Knowledge)-[:RELATED_TO]->(k2:Knowledge)
(k:Knowledge)-[:DERIVED_FROM]->(m:Memory)
(k:Knowledge)-[:VERIFIED_BY]->(a:Agent)
```

### 3. Python Connection Module
Create `neo4j_client.py`:
```python
"""Neo4j client for Gadugi v0.3."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from neo4j import GraphDatabase, Result
import logging

@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "gadugi123"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50

class Neo4jClient:
    """Client for interacting with Neo4j database."""

    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
            max_connection_lifetime=config.max_connection_lifetime,
            max_connection_pool_size=config.max_connection_pool_size
        )
        self.logger = logging.getLogger(__name__)

    def close(self):
        """Close the database connection."""
        self.driver.close()

    def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create an agent node."""
        query = """
        CREATE (a:Agent {
            id: $id,
            name: $name,
            type: $type,
            version: $version,
            status: $status,
            created_at: datetime(),
            capabilities: $capabilities
        })
        RETURN a.id as agent_id
        """
        with self.driver.session() as session:
            result = session.run(query, **agent_data)
            return result.single()["agent_id"]

    def create_memory(self, memory_data: Dict[str, Any]) -> str:
        """Create a memory node and link to agent."""
        query = """
        MATCH (a:Agent {id: $agent_id})
        CREATE (m:Memory {
            id: $id,
            content: $content,
            type: $type,
            timestamp: datetime(),
            priority: $priority,
            tags: $tags
        })
        CREATE (a)-[:CREATES]->(m)
        RETURN m.id as memory_id
        """
        with self.driver.session() as session:
            result = session.run(query, **memory_data)
            return result.single()["memory_id"]

    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a task node."""
        query = """
        CREATE (t:Task {
            id: $id,
            description: $description,
            status: $status,
            priority: $priority,
            created_at: datetime()
        })
        RETURN t.id as task_id
        """
        with self.driver.session() as session:
            result = session.run(query, **task_data)
            return result.single()["task_id"]

    def link_task_to_agent(self, task_id: str, agent_id: str):
        """Assign a task to an agent."""
        query = """
        MATCH (t:Task {id: $task_id})
        MATCH (a:Agent {id: $agent_id})
        CREATE (t)-[:ASSIGNED_TO]->(a)
        """
        with self.driver.session() as session:
            session.run(query, task_id=task_id, agent_id=agent_id)

    def get_agent_memories(self, agent_id: str) -> List[Dict]:
        """Get all memories created by an agent."""
        query = """
        MATCH (a:Agent {id: $agent_id})-[:CREATES]->(m:Memory)
        RETURN m
        ORDER BY m.timestamp DESC
        """
        with self.driver.session() as session:
            result = session.run(query, agent_id=agent_id)
            return [dict(record["m"]) for record in result]

    def find_related_knowledge(self, topic: str) -> List[Dict]:
        """Find knowledge nodes related to a topic."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.title CONTAINS $topic OR k.content CONTAINS $topic
        OPTIONAL MATCH (k)-[:RELATED_TO]-(related:Knowledge)
        RETURN k, collect(related) as related
        """
        with self.driver.session() as session:
            result = session.run(query, topic=topic)
            return [
                {
                    "knowledge": dict(record["k"]),
                    "related": [dict(r) for r in record["related"]]
                }
                for record in result
            ]
```

### 4. Database Initialization Script
Create `neo4j/init_db.py`:
```python
#!/usr/bin/env python3
"""Initialize Neo4j database with schema and sample data."""

from neo4j_client import Neo4jClient, Neo4jConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the Neo4j database."""
    client = Neo4jClient(Neo4jConfig())

    try:
        # Create constraints
        with open("neo4j/schema.cypher", "r") as f:
            schema_commands = f.read().split(";")

        with client.driver.session() as session:
            for command in schema_commands:
                if command.strip():
                    session.run(command)
                    logger.info(f"Executed: {command[:50]}...")

        # Create sample data
        orchestrator = client.create_agent({
            "id": "orchestrator-001",
            "name": "Orchestrator",
            "type": "coordinator",
            "version": "0.3.0",
            "status": "active",
            "capabilities": ["parallel_execution", "task_coordination"]
        })

        memory = client.create_memory({
            "id": "mem-001",
            "agent_id": orchestrator,
            "content": "System initialized successfully",
            "type": "system",
            "priority": "high",
            "tags": ["initialization", "system"]
        })

        logger.info("Database initialized successfully")

    finally:
        client.close()

if __name__ == "__main__":
    initialize_database()
```

### 5. Testing Script
Create `neo4j/test_connection.py`:
```python
#!/usr/bin/env python3
"""Test Neo4j connection and basic operations."""

from neo4j_client import Neo4jClient, Neo4jConfig
import uuid

def test_neo4j():
    """Test Neo4j connection and operations."""
    client = Neo4jClient(Neo4jConfig())

    try:
        # Test connection
        with client.driver.session() as session:
            result = session.run("RETURN 1 as test")
            assert result.single()["test"] == 1
            print("✓ Connection successful")

        # Test agent creation
        agent_id = client.create_agent({
            "id": f"test-agent-{uuid.uuid4()}",
            "name": "Test Agent",
            "type": "test",
            "version": "0.3.0",
            "status": "testing",
            "capabilities": ["testing"]
        })
        print(f"✓ Created agent: {agent_id}")

        # Test memory creation
        memory_id = client.create_memory({
            "id": f"test-memory-{uuid.uuid4()}",
            "agent_id": agent_id,
            "content": "Test memory content",
            "type": "test",
            "priority": "low",
            "tags": ["test"]
        })
        print(f"✓ Created memory: {memory_id}")

        # Test retrieval
        memories = client.get_agent_memories(agent_id)
        assert len(memories) == 1
        print(f"✓ Retrieved {len(memories)} memories")

        print("\n✅ All tests passed!")

    finally:
        client.close()

if __name__ == "__main__":
    test_neo4j()
```

## Success Criteria
- Docker Compose file works and starts Neo4j
- Neo4j accessible at http://localhost:7474
- Schema constraints created successfully
- Python client can connect and perform CRUD operations
- Test script passes all checks
- Sample data loaded correctly
- Documentation complete

## Implementation Notes
- Use Neo4j Community Edition for simplicity
- Include APOC plugin for advanced operations
- Ensure proper error handling in client
- Use connection pooling for performance
- Test with UV environment
- Consider adding graph visualization tools later
