#!/usr/bin/env python3
"""Test Neo4j connection and basic operations."""

import sys
import uuid
import json
import logging
from neo4j_client import Neo4jClient, Neo4jConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connectivity(client: Neo4jClient) -> bool:
    """Test basic connectivity.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if test passes, False otherwise.
    """
    logger.info("Testing connectivity...")
    
    if client.verify_connectivity():
        logger.info("✓ Connection successful")
        return True
    else:
        logger.error("✗ Connection failed")
        return False


def test_agent_operations(client: Neo4jClient) -> bool:
    """Test agent CRUD operations.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("\nTesting agent operations...")
    
    try:
        # Create agent
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        created_id = client.create_agent({
            "id": agent_id,
            "name": "Test Agent",
            "type": "worker",
            "version": "0.3.0",
            "capabilities": ["testing", "validation"]
        })
        assert created_id == agent_id
        logger.info(f"✓ Created agent: {agent_id}")
        
        # Get agent
        agent = client.get_agent(agent_id)
        assert agent is not None
        assert agent["name"] == "Test Agent"
        logger.info(f"✓ Retrieved agent: {agent['name']}")
        
        # Update agent status
        success = client.update_agent_status(agent_id, "running")
        assert success
        logger.info("✓ Updated agent status")
        
        # Verify update
        agent = client.get_agent(agent_id)
        assert agent["status"] == "running"
        logger.info("✓ Status update verified")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Agent test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in agent test: {e}")
        return False


def test_memory_operations(client: Neo4jClient) -> bool:
    """Test memory CRUD operations.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("\nTesting memory operations...")
    
    try:
        # First create an agent for the memory
        agent_id = f"test-agent-mem-{uuid.uuid4().hex[:8]}"
        client.create_agent({
            "id": agent_id,
            "name": "Memory Test Agent",
            "type": "worker",
            "version": "0.3.0"
        })
        
        # Create memory
        memory_id = f"test-memory-{uuid.uuid4().hex[:8]}"
        created_id = client.create_memory({
            "id": memory_id,
            "agent_id": agent_id,
            "content": "Test memory content",
            "type": "episodic",
            "priority": "high",
            "importance": 0.8,
            "tags": ["test", "validation"]
        })
        assert created_id == memory_id
        logger.info(f"✓ Created memory: {memory_id}")
        
        # Get agent memories
        memories = client.get_agent_memories(agent_id)
        assert len(memories) == 1
        assert memories[0]["content"] == "Test memory content"
        logger.info(f"✓ Retrieved {len(memories)} memories")
        
        # Test filtered retrieval
        memories = client.get_agent_memories(agent_id, memory_type="episodic")
        assert len(memories) == 1
        logger.info("✓ Filtered memory retrieval works")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Memory test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in memory test: {e}")
        return False


def test_task_operations(client: Neo4jClient) -> bool:
    """Test task CRUD operations.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("\nTesting task operations...")
    
    try:
        # Create task
        task_id = f"test-task-{uuid.uuid4().hex[:8]}"
        created_id = client.create_task({
            "id": task_id,
            "name": "Test Task",
            "description": "A test task for validation",
            "type": "validation",
            "priority": "high"
        })
        assert created_id == task_id
        logger.info(f"✓ Created task: {task_id}")
        
        # Create agent for assignment
        agent_id = f"test-agent-task-{uuid.uuid4().hex[:8]}"
        client.create_agent({
            "id": agent_id,
            "name": "Task Test Agent",
            "type": "worker",
            "version": "0.3.0"
        })
        
        # Assign task to agent
        success = client.assign_task_to_agent(task_id, agent_id)
        assert success
        logger.info(f"✓ Assigned task to agent")
        
        # Update task status
        success = client.update_task_status(task_id, "running")
        assert success
        logger.info("✓ Updated task status to running")
        
        # Complete task with result
        result = json.dumps({"status": "success", "score": 100})
        success = client.update_task_status(task_id, "completed", result)
        assert success
        logger.info("✓ Completed task with result")
        
        # Create dependency test
        task2_id = f"test-task-dep-{uuid.uuid4().hex[:8]}"
        client.create_task({
            "id": task2_id,
            "name": "Dependent Task",
            "description": "Task that depends on another"
        })
        
        # Create dependency
        client.execute_query(
            "MATCH (t1:Task {id: $t1}), (t2:Task {id: $t2}) "
            "CREATE (t2)-[:DEPENDS_ON]->(t1)",
            {"t1": task_id, "t2": task2_id}
        )
        
        # Check dependencies
        deps = client.get_task_dependencies(task2_id)
        assert task_id in deps["depends_on"]
        logger.info("✓ Task dependencies work correctly")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Task test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in task test: {e}")
        return False


def test_team_operations(client: Neo4jClient) -> bool:
    """Test team operations.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("\nTesting team operations...")
    
    try:
        # Create team
        team_id = f"test-team-{uuid.uuid4().hex[:8]}"
        created_id = client.create_team({
            "id": team_id,
            "name": "Test Team",
            "objectives": json.dumps(["Test objective 1", "Test objective 2"]),
            "performance_score": 0.95
        })
        assert created_id == team_id
        logger.info(f"✓ Created team: {team_id}")
        
        # Create agents for team
        agent_ids = []
        for i in range(3):
            agent_id = f"test-team-agent-{i}-{uuid.uuid4().hex[:8]}"
            agent_ids.append(agent_id)
            client.create_agent({
                "id": agent_id,
                "name": f"Team Member {i+1}",
                "type": "worker",
                "version": "0.3.0"
            })
        
        # Add agents to team
        for agent_id in agent_ids:
            success = client.add_agent_to_team(agent_id, team_id)
            assert success
        logger.info(f"✓ Added {len(agent_ids)} agents to team")
        
        # Get team members
        members = client.get_team_members(team_id)
        assert len(members) == 3
        logger.info(f"✓ Retrieved {len(members)} team members")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Team test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in team test: {e}")
        return False


def test_knowledge_operations(client: Neo4jClient) -> bool:
    """Test knowledge operations.
    
    Args:
        client: Neo4j client instance.
        
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("\nTesting knowledge operations...")
    
    try:
        # Create knowledge items
        knowledge_ids = []
        topics = ["Python", "Neo4j", "Testing"]
        
        for i, topic in enumerate(topics):
            knowledge_id = f"test-knowledge-{i}-{uuid.uuid4().hex[:8]}"
            knowledge_ids.append(knowledge_id)
            created_id = client.create_knowledge({
                "id": knowledge_id,
                "title": f"Knowledge about {topic}",
                "content": f"This is detailed information about {topic}",
                "domain": topic.lower(),
                "confidence": 0.8 + (i * 0.05),
                "source": "test_suite",
                "verified": True
            })
            assert created_id == knowledge_id
        logger.info(f"✓ Created {len(knowledge_ids)} knowledge items")
        
        # Search for knowledge
        results = client.find_related_knowledge("Python")
        assert len(results) > 0
        assert "Python" in results[0]["knowledge"]["title"]
        logger.info(f"✓ Found {len(results)} related knowledge items")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Knowledge test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in knowledge test: {e}")
        return False


def run_all_tests():
    """Run all Neo4j tests."""
    logger.info("=" * 60)
    logger.info("Gadugi v0.3 Neo4j Connection Tests")
    logger.info("=" * 60)
    
    # Create client
    config = Neo4jConfig()
    
    try:
        with Neo4jClient(config) as client:
            # Run tests
            tests = [
                ("Connectivity", test_connectivity),
                ("Agent Operations", test_agent_operations),
                ("Memory Operations", test_memory_operations),
                ("Task Operations", test_task_operations),
                ("Team Operations", test_team_operations),
                ("Knowledge Operations", test_knowledge_operations)
            ]
            
            results = []
            for test_name, test_func in tests:
                try:
                    passed = test_func(client)
                    results.append((test_name, passed))
                except Exception as e:
                    logger.error(f"Test {test_name} crashed: {e}")
                    results.append((test_name, False))
            
            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("Test Summary:")
            logger.info("=" * 60)
            
            passed_count = 0
            for test_name, passed in results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                logger.info(f"{test_name:.<30} {status}")
                if passed:
                    passed_count += 1
            
            logger.info("=" * 60)
            logger.info(f"Overall: {passed_count}/{len(tests)} tests passed")
            
            if passed_count == len(tests):
                logger.info("\n✅ All tests passed! Neo4j is working correctly.")
                return 0
            else:
                logger.error(f"\n❌ {len(tests) - passed_count} tests failed.")
                return 1
                
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.error("Make sure Neo4j is running: docker-compose up -d neo4j")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())