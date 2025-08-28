#!/usr/bin/env python3
"""Initialize Neo4j database with schema and sample data."""

import sys
import logging
import uuid
import json
from pathlib import Path
from neo4j_client import Neo4jClient, Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def execute_schema_file(client: Neo4jClient, schema_file: Path) -> bool:
    """Execute schema commands from a Cypher file.
    
    Args:
        client: Neo4j client instance.
        schema_file: Path to schema.cypher file.
        
    Returns:
        True if successful, False otherwise.
    """
    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    # Read and parse schema file
    with open(schema_file, 'r') as f:
        content = f.read()

    # Split into individual commands (by semicolon and double newline)
    commands = []
    current_command = []

    for line in content.split('\n'):
        # Skip comments and empty lines
        if line.strip().startswith('//') or not line.strip():
            continue

        current_command.append(line)

        # Check if command is complete
        if line.strip().endswith(';'):
            command = ' '.join(current_command).strip()
            if command and not command.startswith('//'):
                # Remove trailing semicolon
                command = command.rstrip(';')
                commands.append(command)
            current_command = []

    # Add any remaining command
    if current_command:
        command = ' '.join(current_command).strip()
        if command and not command.startswith('//'):
            commands.append(command)

    # Execute each command
    success_count = 0
    failed_commands = []

    for i, command in enumerate(commands, 1):
        try:
            client.execute_query(command)
            logger.info(f"Executed command {i}/{len(commands)}: {command[:50]}...")
            success_count += 1
        except Exception as e:
            # Some constraints might already exist, which is fine
            if "already exists" in str(e).lower() or "equivalent constraint" in str(e).lower():
                logger.info(f"Constraint already exists: {command[:50]}...")
                success_count += 1
            else:
                logger.error(f"Failed to execute command {i}: {e}")
                logger.error(f"Command: {command}")
                failed_commands.append((command, str(e)))

    logger.info(f"Successfully executed {success_count}/{len(commands)} commands")

    if failed_commands:
        logger.error("Failed commands:")
        for cmd, error in failed_commands:
            logger.error(f"  - {cmd[:50]}...: {error}")
        return False

    return True


def create_sample_data(client: Neo4jClient) -> None:
    """Create sample data for testing.
    
    Args:
        client: Neo4j client instance.
    """
    logger.info("Creating sample data...")

    # Create Orchestrator Agent
    orchestrator_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
    orchestrator = client.create_agent({
        "id": orchestrator_id,
        "name": "Primary Orchestrator",
        "type": "coordinator",
        "version": "0.3.0",
        "status": "running",
        "capabilities": ["parallel_execution", "task_coordination", "resource_management"],
        "metadata": json.dumps({"max_parallel_tasks": 10, "region": "us-west-2"})
    })
    logger.info(f"Created orchestrator agent: {orchestrator}")

    # Create Worker Agents
    worker_ids = []
    for i in range(3):
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        worker_ids.append(worker_id)
        client.create_agent({
            "id": worker_id,
            "name": f"Worker Agent {i+1}",
            "type": "worker",
            "version": "0.3.0",
            "status": "running",
            "capabilities": ["task_execution", "state_management"],
            "metadata": json.dumps({"worker_index": i})
        })
        logger.info(f"Created worker agent: {worker_id}")

    # Create a Team
    team_id = f"team-{uuid.uuid4().hex[:8]}"
    client.create_team({
        "id": team_id,
        "name": "Development Team Alpha",
        "objectives": json.dumps([
            "Complete v0.3 implementation",
            "Improve system performance",
            "Enhance test coverage"
        ]),
        "performance_score": 0.85
    })
    logger.info(f"Created team: {team_id}")

    # Add agents to team
    client.add_agent_to_team(orchestrator_id, team_id)
    for worker_id in worker_ids:
        client.add_agent_to_team(worker_id, team_id)
    logger.info(f"Added {len(worker_ids) + 1} agents to team")

    # Create sample tasks
    task_ids = []
    task_types = ["code_review", "test_execution", "documentation", "deployment"]
    priorities = ["low", "normal", "high", "critical"]

    for i in range(5):
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task_ids.append(task_id)
        client.create_task({
            "id": task_id,
            "name": f"Sample Task {i+1}",
            "description": "This is a sample task for testing Neo4j integration",
            "type": task_types[i % len(task_types)],
            "priority": priorities[i % len(priorities)],
            "timeout_seconds": 300 + (i * 60)
        })
        logger.info(f"Created task: {task_id}")

    # Assign some tasks to workers
    for i, task_id in enumerate(task_ids[:3]):
        worker_id = worker_ids[i % len(worker_ids)]
        client.assign_task_to_agent(task_id, worker_id)
        logger.info(f"Assigned task {task_id} to {worker_id}")

    # Create sample memories
    for worker_id in worker_ids[:2]:
        for i in range(3):
            memory_id = f"memory-{uuid.uuid4().hex[:8]}"
            client.create_memory({
                "id": memory_id,
                "agent_id": worker_id,
                "content": f"Sample memory content {i+1} for worker {worker_id}",
                "type": ["episodic", "semantic", "procedural"][i % 3],
                "priority": "normal",
                "importance": 0.5 + (i * 0.1),
                "tags": ["sample", "test", f"memory_{i}"]
            })
            logger.info(f"Created memory {memory_id} for {worker_id}")

    # Create sample knowledge
    domains = ["python", "neo4j", "agents", "orchestration"]
    for i in range(4):
        knowledge_id = f"knowledge-{uuid.uuid4().hex[:8]}"
        client.create_knowledge({
            "id": knowledge_id,
            "title": f"Knowledge Item {i+1}",
            "content": f"This is sample knowledge about {domains[i]}",
            "domain": domains[i],
            "confidence": 0.7 + (i * 0.05),
            "source": "sample_data_generator",
            "verified": i % 2 == 0
        })
        logger.info(f"Created knowledge: {knowledge_id}")

    # Create task dependencies
    if len(task_ids) >= 2:
        # Make task 2 depend on task 1
        client.execute_query(
            """
            MATCH (t1:Task {id: $task1_id})
            MATCH (t2:Task {id: $task2_id})
            CREATE (t2)-[:DEPENDS_ON]->(t1)
            """,
            {"task1_id": task_ids[0], "task2_id": task_ids[1]}
        )
        logger.info(f"Created dependency: {task_ids[1]} depends on {task_ids[0]}")

    logger.info("Sample data creation complete!")


def verify_installation(client: Neo4jClient) -> bool:
    """Verify that the database is properly set up.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if verification successful, False otherwise.
    """
    logger.info("Verifying database installation...")

    try:
        # Check connectivity
        if not client.verify_connectivity():
            logger.error("Failed to connect to Neo4j database")
            return False
        logger.info("✓ Database connectivity verified")

        # Check node counts
        result = client.execute_query("""
            MATCH (a:Agent) WITH count(a) as agents
            MATCH (t:Task) WITH agents, count(t) as tasks
            MATCH (m:Memory) WITH agents, tasks, count(m) as memories
            MATCH (k:Knowledge) WITH agents, tasks, memories, count(k) as knowledge
            MATCH (tm:Team) WITH agents, tasks, memories, knowledge, count(tm) as teams
            RETURN agents, tasks, memories, knowledge, teams
        """)

        if result:
            counts = result[0]
            logger.info("✓ Database contains:")
            logger.info(f"  - Agents: {counts.get('agents', 0)}")
            logger.info(f"  - Tasks: {counts.get('tasks', 0)}")
            logger.info(f"  - Memories: {counts.get('memories', 0)}")
            logger.info(f"  - Knowledge: {counts.get('knowledge', 0)}")
            logger.info(f"  - Teams: {counts.get('teams', 0)}")

        # Check constraints
        result = client.execute_query("SHOW CONSTRAINTS")
        logger.info(f"✓ Constraints configured: {len(result)} constraints")

        # Check indexes
        result = client.execute_query("SHOW INDEXES")
        logger.info(f"✓ Indexes configured: {len(result)} indexes")

        return True

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def main():
    """Main initialization function."""
    logger.info("=" * 60)
    logger.info("Gadugi v0.3 Neo4j Database Initialization")
    logger.info("=" * 60)

    # Create client
    config = Neo4jConfig()
    logger.info(f"Connecting to Neo4j at {config.uri}")

    try:
        with Neo4jClient(config) as client:
            # Test connection
            if not client.verify_connectivity():
                logger.error("Cannot connect to Neo4j. Is it running?")
                logger.error("Start Neo4j with: docker-compose up -d neo4j")
                sys.exit(1)

            logger.info("✓ Connected to Neo4j successfully")

            # Execute schema
            schema_file = Path(__file__).parent / "schema.cypher"
            if execute_schema_file(client, schema_file):
                logger.info("✓ Schema created successfully")
            else:
                logger.warning("⚠ Some schema commands failed (may already exist)")

            # Create sample data
            create_sample_data(client)

            # Verify installation
            if verify_installation(client):
                logger.info("\n" + "=" * 60)
                logger.info("✅ Neo4j database initialized successfully!")
                logger.info("=" * 60)
                logger.info("\nYou can now:")
                logger.info("  - Access Neo4j Browser at http://localhost:7474")
                logger.info("  - Username: neo4j")
                logger.info("  - Password: (configured in .env file)")
                logger.info("  - Run test script: python neo4j/test_connection.py")
            else:
                logger.error("❌ Verification failed")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Make sure Neo4j is running: docker-compose up -d neo4j")
        sys.exit(1)


if __name__ == "__main__":
    main()
