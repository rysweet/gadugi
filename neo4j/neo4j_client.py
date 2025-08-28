#!/usr/bin/env python3
"""Neo4j client for Gadugi v0.3."""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from neo4j import GraphDatabase
import json


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str = field(default_factory=lambda: f"bolt://{os.getenv('NEO4J_HOST', 'localhost')}:{os.getenv('NEO4J_BOLT_PORT', '7687')}")
    username: str = field(default_factory=lambda: os.getenv('NEO4J_USERNAME', 'neo4j'))
    password: str = field(default_factory=lambda: os.getenv('NEO4J_PASSWORD', 'changeme'))
    database: str = field(default_factory=lambda: os.getenv('NEO4J_DATABASE', 'gadugi'))
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    encrypted: bool = False


class Neo4jClient:
    """Client for interacting with Neo4j database."""

    def __init__(self, config: Optional[Neo4jConfig] = None):
        """Initialize Neo4j client.
        
        Args:
            config: Neo4j configuration. Uses defaults if not provided.
        """
        self.config = config or Neo4jConfig()
        self.driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
            max_connection_lifetime=self.config.max_connection_lifetime,
            max_connection_pool_size=self.config.max_connection_pool_size,
            connection_timeout=self.config.connection_timeout,
            encrypted=self.config.encrypted
        )
        self.logger = logging.getLogger(__name__)

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def verify_connectivity(self) -> bool:
        """Verify database connectivity.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            self.logger.error(f"Connection verification failed: {e}")
            return False

    # ============================================
    # AGENT OPERATIONS
    # ============================================

    def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create an agent node.
        
        Args:
            agent_data: Agent properties including id, name, type, etc.
            
        Returns:
            Agent ID of created agent.
        """
        query = """
        CREATE (a:Agent {
            id: $id,
            name: $name,
            type: $type,
            version: $version,
            status: $status,
            created_at: datetime(),
            updated_at: datetime(),
            capabilities: $capabilities,
            metadata: $metadata
        })
        RETURN a.id as agent_id
        """

        # Ensure required fields
        agent_data.setdefault('status', 'initializing')
        agent_data.setdefault('capabilities', [])
        agent_data.setdefault('metadata', json.dumps({}))

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **agent_data)
            return result.single()["agent_id"]

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID.
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            Agent properties or None if not found.
        """
        query = """
        MATCH (a:Agent {id: $agent_id})
        RETURN a
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, agent_id=agent_id)
            record = result.single()
            return dict(record["a"]) if record else None

    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent status.
        
        Args:
            agent_id: Agent identifier.
            status: New status.
            
        Returns:
            True if updated, False otherwise.
        """
        query = """
        MATCH (a:Agent {id: $agent_id})
        SET a.status = $status, a.updated_at = datetime()
        RETURN a.id as agent_id
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, agent_id=agent_id, status=status)
            return result.single() is not None

    # ============================================
    # MEMORY OPERATIONS
    # ============================================

    def create_memory(self, memory_data: Dict[str, Any]) -> str:
        """Create a memory node and link to agent.
        
        Args:
            memory_data: Memory properties including agent_id.
            
        Returns:
            Memory ID of created memory.
        """
        query = """
        MATCH (a:Agent {id: $agent_id})
        CREATE (m:Memory {
            id: $id,
            content: $content,
            type: $type,
            timestamp: datetime(),
            priority: $priority,
            importance: $importance,
            tags: $tags,
            access_count: 0,
            decay_rate: $decay_rate
        })
        CREATE (a)-[:CREATES]->(m)
        RETURN m.id as memory_id
        """

        # Set defaults
        memory_data.setdefault('priority', 'normal')
        memory_data.setdefault('importance', 0.5)
        memory_data.setdefault('tags', [])
        memory_data.setdefault('decay_rate', 0.1)

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **memory_data)
            record = result.single()
            if not record:
                raise ValueError(f"Agent {memory_data.get('agent_id')} not found")
            return record["memory_id"]

    def get_agent_memories(
        self,
        agent_id: str,
        limit: int = 100,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get memories created by an agent.
        
        Args:
            agent_id: Agent identifier.
            limit: Maximum number of memories to return.
            memory_type: Optional filter by memory type.
            
        Returns:
            List of memory nodes.
        """
        if memory_type:
            query = """
            MATCH (a:Agent {id: $agent_id})-[:CREATES]->(m:Memory {type: $memory_type})
            RETURN m
            ORDER BY m.timestamp DESC
            LIMIT $limit
            """
            params = {"agent_id": agent_id, "memory_type": memory_type, "limit": limit}
        else:
            query = """
            MATCH (a:Agent {id: $agent_id})-[:CREATES]->(m:Memory)
            RETURN m
            ORDER BY m.timestamp DESC
            LIMIT $limit
            """
            params = {"agent_id": agent_id, "limit": limit}

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **params)
            return [dict(record["m"]) for record in result]

    def find_similar_memories(
        self,
        memory_id: str,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Find memories similar to a given memory.
        
        Args:
            memory_id: Reference memory ID.
            threshold: Minimum similarity threshold.
            limit: Maximum number of results.
            
        Returns:
            List of (memory, similarity_score) tuples.
        """
        query = """
        MATCH (m1:Memory {id: $memory_id})
        MATCH (m1)-[r:ASSOCIATES_WITH]-(m2:Memory)
        WHERE r.strength >= $threshold
        RETURN m2, r.strength as similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                query,
                memory_id=memory_id,
                threshold=threshold,
                limit=limit
            )
            return [(dict(record["m2"]), record["similarity"]) for record in result]

    # ============================================
    # TASK OPERATIONS
    # ============================================

    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a task node.
        
        Args:
            task_data: Task properties.
            
        Returns:
            Task ID of created task.
        """
        query = """
        CREATE (t:Task {
            id: $id,
            name: $name,
            description: $description,
            type: $type,
            status: $status,
            priority: $priority,
            created_at: datetime(),
            timeout_seconds: $timeout_seconds
        })
        RETURN t.id as task_id
        """

        # Set defaults
        task_data.setdefault('status', 'pending')
        task_data.setdefault('priority', 'normal')
        task_data.setdefault('type', 'general')
        task_data.setdefault('timeout_seconds', 300)

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **task_data)
            return result.single()["task_id"]

    def assign_task_to_agent(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent.
        
        Args:
            task_id: Task identifier.
            agent_id: Agent identifier.
            
        Returns:
            True if assignment successful, False otherwise.
        """
        query = """
        MATCH (t:Task {id: $task_id})
        MATCH (a:Agent {id: $agent_id})
        CREATE (t)-[:ASSIGNED_TO]->(a)
        SET t.assigned_to = $agent_id, t.status = 'scheduled'
        RETURN t.id as task_id
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, task_id=task_id, agent_id=agent_id)
            return result.single() is not None

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None
    ) -> bool:
        """Update task status.
        
        Args:
            task_id: Task identifier.
            status: New status.
            result: Optional task result (JSON string).
            
        Returns:
            True if updated, False otherwise.
        """
        if status == 'completed' and result:
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.status = $status, 
                t.completed_at = datetime(),
                t.result = $result
            RETURN t.id as task_id
            """
            params = {"task_id": task_id, "status": status, "result": result}
        elif status == 'running':
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.status = $status, t.started_at = datetime()
            RETURN t.id as task_id
            """
            params = {"task_id": task_id, "status": status}
        else:
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.status = $status
            RETURN t.id as task_id
            """
            params = {"task_id": task_id, "status": status}

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **params)
            return result.single() is not None

    def get_task_dependencies(self, task_id: str) -> Dict[str, List[str]]:
        """Get task dependencies.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            Dictionary with 'depends_on' and 'blocks' lists.
        """
        query = """
        MATCH (t:Task {id: $task_id})
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
        OPTIONAL MATCH (blocked:Task)-[:DEPENDS_ON]->(t)
        RETURN 
            collect(DISTINCT dep.id) as depends_on,
            collect(DISTINCT blocked.id) as blocks
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, task_id=task_id)
            record = result.single()
            return {
                "depends_on": record["depends_on"] if record else [],
                "blocks": record["blocks"] if record else []
            }

    # ============================================
    # KNOWLEDGE OPERATIONS
    # ============================================

    def create_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """Create a knowledge node.
        
        Args:
            knowledge_data: Knowledge properties.
            
        Returns:
            Knowledge ID of created node.
        """
        query = """
        CREATE (k:Knowledge {
            id: $id,
            title: $title,
            content: $content,
            domain: $domain,
            confidence: $confidence,
            source: $source,
            created_at: datetime(),
            verified: $verified,
            version: 1
        })
        RETURN k.id as knowledge_id
        """

        # Set defaults
        knowledge_data.setdefault('confidence', 0.5)
        knowledge_data.setdefault('verified', False)
        knowledge_data.setdefault('domain', 'general')

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **knowledge_data)
            return result.single()["knowledge_id"]

    def find_related_knowledge(
        self,
        topic: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find knowledge nodes related to a topic.
        
        Args:
            topic: Topic to search for.
            limit: Maximum number of results.
            
        Returns:
            List of knowledge nodes with their related nodes.
        """
        query = """
        MATCH (k:Knowledge)
        WHERE k.title CONTAINS $topic OR k.content CONTAINS $topic
        OPTIONAL MATCH (k)-[:RELATED_TO]-(related:Knowledge)
        RETURN k, collect(related) as related
        LIMIT $limit
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, topic=topic, limit=limit)
            return [
                {
                    "knowledge": dict(record["k"]),
                    "related": [dict(r) for r in record["related"] if r]
                }
                for record in result
            ]

    # ============================================
    # TEAM OPERATIONS
    # ============================================

    def create_team(self, team_data: Dict[str, Any]) -> str:
        """Create a team node.
        
        Args:
            team_data: Team properties.
            
        Returns:
            Team ID of created team.
        """
        query = """
        CREATE (tm:Team {
            id: $id,
            name: $name,
            created_at: datetime(),
            objectives: $objectives,
            performance_score: $performance_score
        })
        RETURN tm.id as team_id
        """

        # Set defaults
        team_data.setdefault('objectives', json.dumps([]))
        team_data.setdefault('performance_score', 0.0)

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, **team_data)
            return result.single()["team_id"]

    def add_agent_to_team(self, agent_id: str, team_id: str) -> bool:
        """Add an agent to a team.
        
        Args:
            agent_id: Agent identifier.
            team_id: Team identifier.
            
        Returns:
            True if successful, False otherwise.
        """
        query = """
        MATCH (a:Agent {id: $agent_id})
        MATCH (tm:Team {id: $team_id})
        CREATE (a)-[:MEMBER_OF]->(tm)
        RETURN a.id as agent_id
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, agent_id=agent_id, team_id=team_id)
            return result.single() is not None

    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all members of a team.
        
        Args:
            team_id: Team identifier.
            
        Returns:
            List of agent nodes.
        """
        query = """
        MATCH (a:Agent)-[:MEMBER_OF]->(tm:Team {id: $team_id})
        RETURN a
        ORDER BY a.name
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, team_id=team_id)
            return [dict(record["a"]) for record in result]

    # ============================================
    # UTILITY OPERATIONS
    # ============================================

    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a custom Cypher query.
        
        Args:
            query: Cypher query string.
            parameters: Query parameters.
            
        Returns:
            List of result records as dictionaries.
        """
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def clear_database(self) -> bool:
        """Clear all nodes and relationships (USE WITH CAUTION).
        
        Returns:
            True if successful, False otherwise.
        """
        query = "MATCH (n) DETACH DELETE n"

        try:
            with self.driver.session(database=self.config.database) as session:
                session.run(query)
                return True
        except Exception as e:
            self.logger.error(f"Failed to clear database: {e}")
            return False
