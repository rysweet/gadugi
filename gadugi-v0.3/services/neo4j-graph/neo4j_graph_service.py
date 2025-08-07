#!/usr/bin/env python3
"""
Neo4j Graph Database Service for Gadugi v0.3

Provides shared memory persistence and graph-based relationships for multi-agent systems.
Handles knowledge graphs, agent interactions, workflow dependencies, and complex data relationships.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

try:
    from neo4j import GraphDatabase, Transaction, ManagedTransaction
    from neo4j.exceptions import ServiceUnavailable, TransientError

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

    # Mock classes for development without Neo4j driver
    class GraphDatabase:
        @staticmethod
        def driver(*args, **kwargs):
            return MockDriver()

    class MockDriver:
        def close(self):
            pass

        def session(self):
            return MockSession()

    class MockSession:
        def close(self):
            pass

        def run(self, *args, **kwargs):
            return MockResult()

        def execute_read(self, func):
            return func(MockTransaction())

        def execute_write(self, func):
            return func(MockTransaction())

    class MockTransaction:
        def run(self, *args, **kwargs):
            return MockResult()

    class MockResult:
        def single(self):
            return MockRecord()

        def data(self):
            return []

        def consume(self):
            return MockSummary()

    class MockRecord:
        def __getitem__(self, key):
            return None

        def get(self, key, default=None):
            return default

    class MockSummary:
        def counters(self):
            return MockCounters()

    class MockCounters:
        nodes_created = 0
        relationships_created = 0


class NodeType(Enum):
    """Node type enumeration for the knowledge graph."""

    AGENT = "agent"
    WORKFLOW = "workflow"
    TASK = "task"
    MEMORY = "memory"
    CONCEPT = "concept"
    DOCUMENT = "document"
    CODE = "code"
    TEST = "test"
    ISSUE = "issue"
    PR = "pull_request"
    USER = "user"
    PROJECT = "project"
    DEPENDENCY = "dependency"
    EVENT = "event"
    METRIC = "metric"


class RelationType(Enum):
    """Relationship type enumeration for the knowledge graph."""

    CREATED = "CREATED"
    MODIFIED = "MODIFIED"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    TESTS = "TESTS"
    REFERENCES = "REFERENCES"
    CONTAINS = "CONTAINS"
    PART_OF = "PART_OF"
    RELATED_TO = "RELATED_TO"
    FOLLOWS = "FOLLOWS"
    PRECEDES = "PRECEDES"
    ASSIGNED_TO = "ASSIGNED_TO"
    TRIGGERED_BY = "TRIGGERED_BY"
    PRODUCES = "PRODUCES"
    CONSUMES = "CONSUMES"
    SIMILAR_TO = "SIMILAR_TO"


class QueryType(Enum):
    """Query type enumeration for different operation types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MATCH = "match"
    AGGREGATE = "aggregate"
    PATH = "path"
    RECOMMENDATION = "recommendation"


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""

    id: str
    type: NodeType
    properties: Dict[str, Any]
    labels: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = [self.type.value]
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph."""

    id: str
    type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any]
    created_at: datetime = None
    strength: float = 1.0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class QueryResult:
    """Result of a graph query operation."""

    success: bool
    operation: str
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    paths: List[List[Dict[str, Any]]]
    aggregations: Dict[str, Any]
    metadata: Dict[str, Any]
    execution_time: float
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


@dataclass
class GraphStats:
    """Graph database statistics."""

    total_nodes: int = 0
    total_relationships: int = 0
    nodes_by_type: Dict[str, int] = None
    relationships_by_type: Dict[str, int] = None
    database_size: int = 0
    last_updated: datetime = None

    def __post_init__(self):
        if self.nodes_by_type is None:
            self.nodes_by_type = {}
        if self.relationships_by_type is None:
            self.relationships_by_type = {}
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class RecommendationRequest:
    """Request for graph-based recommendations."""

    source_node_id: str
    recommendation_type: str
    max_results: int = 10
    filters: Dict[str, Any] = None
    weights: Dict[str, float] = None
    exclude_ids: List[str] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.weights is None:
            self.weights = {}
        if self.exclude_ids is None:
            self.exclude_ids = []


class GraphDatabaseService:
    """Neo4j graph database service for Gadugi platform."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "gadugi",
        max_pool_size: int = 50,
        connection_timeout: float = 30.0,
        max_transaction_retry_time: float = 30.0,
    ):
        """Initialize the graph database service."""
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.max_pool_size = max_pool_size
        self.connection_timeout = connection_timeout
        self.max_transaction_retry_time = max_transaction_retry_time

        self.logger = self._setup_logging()

        # Connection state
        self.driver = None
        self.connected = False

        # Performance tracking
        self.query_count = 0
        self.total_query_time = 0.0
        self.last_health_check = None

        # Query cache for frequently used queries
        self.query_cache = {}
        self.cache_max_size = 1000

        # Neo4j availability check
        self.neo4j_available = NEO4J_AVAILABLE
        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j driver not available, using mock implementation")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the graph database service."""
        logger = logging.getLogger("neo4j_graph")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def connect(self) -> bool:
        """Connect to Neo4j database."""
        try:
            self.logger.info(f"Connecting to Neo4j at {self.uri}")

            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_pool_size=self.max_pool_size,
                connection_timeout=self.connection_timeout,
                max_transaction_retry_time=self.max_transaction_retry_time,
            )

            # Test connection
            await self._test_connection()

            # Initialize schema
            await self._initialize_schema()

            self.connected = True
            self.logger.info("Successfully connected to Neo4j database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Neo4j database."""
        if self.driver:
            self.driver.close()
            self.connected = False
            self.logger.info("Disconnected from Neo4j database")

    async def _test_connection(self):
        """Test the database connection."""

        def test_query(tx):
            result = tx.run("RETURN 1 as test")
            return result.single()["test"]

        with self.driver.session(database=self.database) as session:
            result = session.execute_read(test_query)
            if result != 1:
                raise Exception("Connection test failed")

    async def _initialize_schema(self):
        """Initialize database schema with constraints and indexes."""
        schema_queries = [
            # Node uniqueness constraints
            "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            # Performance indexes
            "CREATE INDEX agent_name_idx IF NOT EXISTS FOR (a:Agent) ON (a.name)",
            "CREATE INDEX workflow_status_idx IF NOT EXISTS FOR (w:Workflow) ON (w.status)",
            "CREATE INDEX task_priority_idx IF NOT EXISTS FOR (t:Task) ON (t.priority)",
            "CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX concept_category_idx IF NOT EXISTS FOR (c:Concept) ON (c.category)",
            "CREATE INDEX document_path_idx IF NOT EXISTS FOR (d:Document) ON (d.path)",
            # Temporal indexes
            "CREATE INDEX node_created_idx IF NOT EXISTS FOR (n) ON (n.created_at)",
            "CREATE INDEX node_updated_idx IF NOT EXISTS FOR (n) ON (n.updated_at)",
            # Full-text search indexes
            "CREATE FULLTEXT INDEX concept_content_idx IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.description, c.content]",
            "CREATE FULLTEXT INDEX document_content_idx IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content, d.summary]",
        ]

        def create_schema(tx):
            for query in schema_queries:
                try:
                    tx.run(query)
                except Exception as e:
                    # Constraints may already exist, which is fine
                    if "already exists" not in str(e).lower():
                        raise e

        try:
            with self.driver.session(database=self.database) as session:
                session.execute_write(create_schema)
            self.logger.info("Schema initialized successfully")
        except Exception as e:
            self.logger.error(f"Schema initialization failed: {e}")
            raise e

    # Node Operations

    async def create_node(self, node: GraphNode) -> QueryResult:
        """Create a new node in the graph."""
        start_time = time.time()

        def create_node_tx(tx):
            # Build labels string
            labels = ":".join(node.labels)

            # Prepare properties
            props = dict(node.properties)
            props.update(
                {
                    "id": node.id,
                    "created_at": node.created_at.isoformat(),
                    "updated_at": node.updated_at.isoformat(),
                }
            )

            query = f"""
            CREATE (n:{labels})
            SET n = $props
            RETURN n
            """

            result = tx.run(query, props=props)
            return result.single()

        try:
            with self.driver.session(database=self.database) as session:
                record = session.execute_write(create_node_tx)

                node_data = dict(record["n"])
                execution_time = time.time() - start_time

                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="create_node",
                    nodes=[node_data],
                    relationships=[],
                    paths=[],
                    aggregations={},
                    metadata={"node_id": node.id, "labels": node.labels},
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to create node {node.id}: {e}")

            return QueryResult(
                success=False,
                operation="create_node",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def get_node(self, node_id: str) -> QueryResult:
        """Retrieve a node by ID."""
        start_time = time.time()

        def get_node_tx(tx):
            query = """
            MATCH (n {id: $node_id})
            RETURN n
            """
            result = tx.run(query, node_id=node_id)
            return result.single()

        try:
            with self.driver.session(database=self.database) as session:
                record = session.execute_read(get_node_tx)

                if record:
                    node_data = dict(record["n"])
                    execution_time = time.time() - start_time

                    self._update_query_stats(execution_time)

                    return QueryResult(
                        success=True,
                        operation="get_node",
                        nodes=[node_data],
                        relationships=[],
                        paths=[],
                        aggregations={},
                        metadata={"node_id": node_id},
                        execution_time=execution_time,
                    )
                else:
                    execution_time = time.time() - start_time
                    return QueryResult(
                        success=False,
                        operation="get_node",
                        nodes=[],
                        relationships=[],
                        paths=[],
                        aggregations={},
                        metadata={},
                        execution_time=execution_time,
                        warnings=[f"Node {node_id} not found"],
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to get node {node_id}: {e}")

            return QueryResult(
                success=False,
                operation="get_node",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def update_node(
        self, node_id: str, properties: Dict[str, Any]
    ) -> QueryResult:
        """Update node properties."""
        start_time = time.time()

        def update_node_tx(tx):
            # Add updated timestamp
            props = dict(properties)
            props["updated_at"] = datetime.now().isoformat()

            query = """
            MATCH (n {id: $node_id})
            SET n += $props
            RETURN n
            """
            result = tx.run(query, node_id=node_id, props=props)
            return result.single()

        try:
            with self.driver.session(database=self.database) as session:
                record = session.execute_write(update_node_tx)

                if record:
                    node_data = dict(record["n"])
                    execution_time = time.time() - start_time

                    self._update_query_stats(execution_time)

                    return QueryResult(
                        success=True,
                        operation="update_node",
                        nodes=[node_data],
                        relationships=[],
                        paths=[],
                        aggregations={},
                        metadata={
                            "node_id": node_id,
                            "updated_properties": list(properties.keys()),
                        },
                        execution_time=execution_time,
                    )
                else:
                    execution_time = time.time() - start_time
                    return QueryResult(
                        success=False,
                        operation="update_node",
                        nodes=[],
                        relationships=[],
                        paths=[],
                        aggregations={},
                        metadata={},
                        execution_time=execution_time,
                        warnings=[f"Node {node_id} not found"],
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to update node {node_id}: {e}")

            return QueryResult(
                success=False,
                operation="update_node",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def delete_node(self, node_id: str) -> QueryResult:
        """Delete a node and all its relationships."""
        start_time = time.time()

        def delete_node_tx(tx):
            query = """
            MATCH (n {id: $node_id})
            DETACH DELETE n
            """
            result = tx.run(query, node_id=node_id)
            return result.consume()

        try:
            with self.driver.session(database=self.database) as session:
                summary = session.execute_write(delete_node_tx)

                nodes_deleted = summary.counters().nodes_deleted
                relationships_deleted = summary.counters().relationships_deleted

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="delete_node",
                    nodes=[],
                    relationships=[],
                    paths=[],
                    aggregations={},
                    metadata={
                        "node_id": node_id,
                        "nodes_deleted": nodes_deleted,
                        "relationships_deleted": relationships_deleted,
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to delete node {node_id}: {e}")

            return QueryResult(
                success=False,
                operation="delete_node",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Relationship Operations

    async def create_relationship(self, relationship: GraphRelationship) -> QueryResult:
        """Create a relationship between two nodes."""
        start_time = time.time()

        def create_relationship_tx(tx):
            # Prepare properties
            props = dict(relationship.properties)
            props.update(
                {
                    "id": relationship.id,
                    "created_at": relationship.created_at.isoformat(),
                    "strength": relationship.strength,
                }
            )

            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{relationship.type.value}]->(b)
            SET r = $props
            RETURN r, a, b
            """

            result = tx.run(
                query,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                props=props,
            )
            return result.single()

        try:
            with self.driver.session(database=self.database) as session:
                record = session.execute_write(create_relationship_tx)

                if record:
                    rel_data = dict(record["r"])
                    source_data = dict(record["a"])
                    target_data = dict(record["b"])

                    execution_time = time.time() - start_time
                    self._update_query_stats(execution_time)

                    return QueryResult(
                        success=True,
                        operation="create_relationship",
                        nodes=[source_data, target_data],
                        relationships=[rel_data],
                        paths=[],
                        aggregations={},
                        metadata={
                            "relationship_id": relationship.id,
                            "type": relationship.type.value,
                            "source_id": relationship.source_id,
                            "target_id": relationship.target_id,
                        },
                        execution_time=execution_time,
                    )
                else:
                    execution_time = time.time() - start_time
                    return QueryResult(
                        success=False,
                        operation="create_relationship",
                        nodes=[],
                        relationships=[],
                        paths=[],
                        aggregations={},
                        metadata={},
                        execution_time=execution_time,
                        warnings=["One or both nodes not found"],
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to create relationship {relationship.id}: {e}")

            return QueryResult(
                success=False,
                operation="create_relationship",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Query Operations

    async def find_nodes(
        self,
        node_type: Optional[NodeType] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> QueryResult:
        """Find nodes matching criteria."""
        start_time = time.time()

        def find_nodes_tx(tx):
            # Build query
            where_clauses = []
            params = {}

            if node_type:
                where_clauses.append(f"n:{node_type.value}")

            if properties:
                for key, value in properties.items():
                    param_name = f"prop_{key}"
                    where_clauses.append(f"n.{key} = ${param_name}")
                    params[param_name] = value

            where_clause = " AND ".join(where_clauses) if where_clauses else ""
            match_clause = f"MATCH (n{':' + where_clause if where_clause else ''})"

            if not where_clause and properties:
                # If we have properties but no type, add WHERE clause
                prop_conditions = [
                    f"n.{key} = ${param_name}"
                    for key, param_name in zip(
                        properties.keys(), [f"prop_{k}" for k in properties.keys()]
                    )
                ]
                where_clause = "WHERE " + " AND ".join(prop_conditions)
                match_clause = "MATCH (n)"

            query = f"""
            {match_clause}
            {where_clause}
            RETURN n
            LIMIT {limit}
            """

            result = tx.run(query, **params)
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(find_nodes_tx)

                nodes = [dict(record["n"]) for record in records]
                execution_time = time.time() - start_time

                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="find_nodes",
                    nodes=nodes,
                    relationships=[],
                    paths=[],
                    aggregations={},
                    metadata={
                        "node_type": node_type.value if node_type else None,
                        "filter_properties": list(properties.keys())
                        if properties
                        else [],
                        "result_count": len(nodes),
                        "limit": limit,
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to find nodes: {e}")

            return QueryResult(
                success=False,
                operation="find_nodes",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def find_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[RelationType] = None,
        limit: int = 100,
    ) -> QueryResult:
        """Find relationships matching criteria."""
        start_time = time.time()

        def find_relationships_tx(tx):
            # Build query components
            match_parts = []
            where_clauses = []
            params = {}

            if source_id and target_id:
                match_parts.append("(a {id: $source_id})")
                match_parts.append("(b {id: $target_id})")
                params["source_id"] = source_id
                params["target_id"] = target_id
            elif source_id:
                match_parts.append("(a {id: $source_id})")
                match_parts.append("(b)")
                params["source_id"] = source_id
            elif target_id:
                match_parts.append("(a)")
                match_parts.append("(b {id: $target_id})")
                params["target_id"] = target_id
            else:
                match_parts.append("(a)")
                match_parts.append("(b)")

            # Build relationship pattern
            if relationship_type:
                rel_pattern = f"[r:{relationship_type.value}]"
            else:
                rel_pattern = "[r]"

            query = f"""
            MATCH {match_parts[0]}-{rel_pattern}->{match_parts[1]}
            RETURN r, a, b
            LIMIT {limit}
            """

            result = tx.run(query, **params)
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(find_relationships_tx)

                relationships = []
                nodes = []
                node_ids = set()

                for record in records:
                    relationships.append(dict(record["r"]))

                    # Add unique nodes
                    source_node = dict(record["a"])
                    target_node = dict(record["b"])

                    if source_node["id"] not in node_ids:
                        nodes.append(source_node)
                        node_ids.add(source_node["id"])

                    if target_node["id"] not in node_ids:
                        nodes.append(target_node)
                        node_ids.add(target_node["id"])

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="find_relationships",
                    nodes=nodes,
                    relationships=relationships,
                    paths=[],
                    aggregations={},
                    metadata={
                        "source_id": source_id,
                        "target_id": target_id,
                        "relationship_type": relationship_type.value
                        if relationship_type
                        else None,
                        "result_count": len(relationships),
                        "limit": limit,
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to find relationships: {e}")

            return QueryResult(
                success=False,
                operation="find_relationships",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        relationship_types: Optional[List[RelationType]] = None,
    ) -> QueryResult:
        """Find paths between two nodes."""
        start_time = time.time()

        def find_paths_tx(tx):
            # Build relationship filter
            if relationship_types:
                rel_types = "|".join([rt.value for rt in relationship_types])
                rel_filter = f":{rel_types}"
            else:
                rel_filter = ""

            query = f"""
            MATCH path = (start {{id: $source_id}})-[{rel_filter}*1..{max_depth}]->(end {{id: $target_id}})
            RETURN path
            LIMIT 20
            """

            result = tx.run(query, source_id=source_id, target_id=target_id)
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(find_paths_tx)

                paths = []
                all_nodes = []
                all_relationships = []
                node_ids = set()

                for record in records:
                    path = record["path"]
                    path_nodes = []
                    path_relationships = []

                    # Extract nodes and relationships from path
                    nodes = path.nodes
                    relationships = path.relationships

                    for node in nodes:
                        node_data = dict(node)
                        path_nodes.append(node_data)

                        if node_data["id"] not in node_ids:
                            all_nodes.append(node_data)
                            node_ids.add(node_data["id"])

                    for rel in relationships:
                        rel_data = dict(rel)
                        path_relationships.append(rel_data)
                        all_relationships.append(rel_data)

                    paths.append(
                        {
                            "nodes": path_nodes,
                            "relationships": path_relationships,
                            "length": len(relationships),
                        }
                    )

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="find_paths",
                    nodes=all_nodes,
                    relationships=all_relationships,
                    paths=paths,
                    aggregations={},
                    metadata={
                        "source_id": source_id,
                        "target_id": target_id,
                        "max_depth": max_depth,
                        "paths_found": len(paths),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to find paths: {e}")

            return QueryResult(
                success=False,
                operation="find_paths",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Advanced Query Operations

    async def get_node_neighbors(
        self,
        node_id: str,
        relationship_types: Optional[List[RelationType]] = None,
        direction: str = "both",
        depth: int = 1,
    ) -> QueryResult:
        """Get neighboring nodes with specified criteria."""
        start_time = time.time()

        def get_neighbors_tx(tx):
            # Build relationship filter
            if relationship_types:
                rel_types = "|".join([rt.value for rt in relationship_types])
                rel_filter = f":{rel_types}"
            else:
                rel_filter = ""

            # Build direction pattern
            if direction == "incoming":
                pattern = f"(neighbor)-[r{rel_filter}*1..{depth}]->(center)"
            elif direction == "outgoing":
                pattern = f"(center)-[r{rel_filter}*1..{depth}]->(neighbor)"
            else:  # both
                pattern = f"(center)-[r{rel_filter}*1..{depth}]-(neighbor)"

            query = f"""
            MATCH {pattern}
            WHERE center.id = $node_id AND neighbor.id <> $node_id
            RETURN DISTINCT neighbor, r
            """

            result = tx.run(query, node_id=node_id)
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(get_neighbors_tx)

                nodes = []
                relationships = []
                node_ids = set()

                for record in records:
                    neighbor = dict(record["neighbor"])
                    if neighbor["id"] not in node_ids:
                        nodes.append(neighbor)
                        node_ids.add(neighbor["id"])

                    # Handle relationship data (could be a path)
                    rel_data = record["r"]
                    if isinstance(rel_data, list):
                        relationships.extend([dict(r) for r in rel_data])
                    else:
                        relationships.append(dict(rel_data))

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="get_neighbors",
                    nodes=nodes,
                    relationships=relationships,
                    paths=[],
                    aggregations={},
                    metadata={
                        "node_id": node_id,
                        "direction": direction,
                        "depth": depth,
                        "neighbor_count": len(nodes),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to get neighbors for {node_id}: {e}")

            return QueryResult(
                success=False,
                operation="get_neighbors",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    async def get_recommendations(self, request: RecommendationRequest) -> QueryResult:
        """Get recommendations based on graph analysis."""
        start_time = time.time()

        def get_recommendations_tx(tx):
            # Build base query based on recommendation type
            if request.recommendation_type == "similar_nodes":
                query = self._build_similar_nodes_query(request)
            elif request.recommendation_type == "related_content":
                query = self._build_related_content_query(request)
            elif request.recommendation_type == "next_actions":
                query = self._build_next_actions_query(request)
            else:
                query = self._build_generic_recommendation_query(request)

            result = tx.run(query, **self._build_recommendation_params(request))
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(get_recommendations_tx)

                recommendations = []
                for record in records:
                    recommendations.append(
                        {
                            "node": dict(record["recommended"]),
                            "score": record.get("score", 1.0),
                            "reason": record.get(
                                "reason", "Graph-based recommendation"
                            ),
                        }
                    )

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="get_recommendations",
                    nodes=[rec["node"] for rec in recommendations],
                    relationships=[],
                    paths=[],
                    aggregations={"recommendations": recommendations},
                    metadata={
                        "source_node_id": request.source_node_id,
                        "recommendation_type": request.recommendation_type,
                        "recommendation_count": len(recommendations),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to get recommendations: {e}")

            return QueryResult(
                success=False,
                operation="get_recommendations",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    def _build_similar_nodes_query(self, request: RecommendationRequest) -> str:
        """Build query for finding similar nodes."""
        return f"""
        MATCH (source {{id: $source_id}})
        MATCH (source)-[r1]-(intermediate)-[r2]-(recommended)
        WHERE recommended.id <> $source_id 
        AND NOT recommended.id IN $exclude_ids
        WITH recommended, COUNT(DISTINCT intermediate) as commonConnections
        RETURN recommended, commonConnections as score, 'Common connections' as reason
        ORDER BY score DESC
        LIMIT {request.max_results}
        """

    def _build_related_content_query(self, request: RecommendationRequest) -> str:
        """Build query for finding related content."""
        return f"""
        MATCH (source {{id: $source_id}})
        MATCH (source)-[:RELATED_TO|:REFERENCES|:SIMILAR_TO*1..2]-(recommended)
        WHERE recommended.id <> $source_id 
        AND NOT recommended.id IN $exclude_ids
        WITH recommended, COUNT(*) as connectionCount
        RETURN recommended, connectionCount as score, 'Related content' as reason
        ORDER BY score DESC
        LIMIT {request.max_results}
        """

    def _build_next_actions_query(self, request: RecommendationRequest) -> str:
        """Build query for suggesting next actions."""
        return f"""
        MATCH (source {{id: $source_id}})
        MATCH (source)-[:DEPENDS_ON]->(recommended)
        WHERE NOT recommended.id IN $exclude_ids
        RETURN recommended, 1.0 as score, 'Next dependency' as reason
        LIMIT {request.max_results}
        """

    def _build_generic_recommendation_query(
        self, request: RecommendationRequest
    ) -> str:
        """Build generic recommendation query."""
        return f"""
        MATCH (source {{id: $source_id}})
        MATCH (source)-[*1..3]-(recommended)
        WHERE recommended.id <> $source_id 
        AND NOT recommended.id IN $exclude_ids
        WITH recommended, COUNT(*) as pathCount
        RETURN recommended, pathCount as score, 'Graph proximity' as reason
        ORDER BY score DESC
        LIMIT {request.max_results}
        """

    def _build_recommendation_params(
        self, request: RecommendationRequest
    ) -> Dict[str, Any]:
        """Build parameters for recommendation queries."""
        return {
            "source_id": request.source_node_id,
            "exclude_ids": request.exclude_ids,
            "max_results": request.max_results,
        }

    # Analytics and Statistics

    async def get_graph_stats(self) -> QueryResult:
        """Get comprehensive graph statistics."""
        start_time = time.time()

        def get_stats_tx(tx):
            queries = {
                "node_count": "MATCH (n) RETURN COUNT(n) as count",
                "relationship_count": "MATCH ()-[r]->() RETURN COUNT(r) as count",
                "node_types": "MATCH (n) RETURN labels(n)[0] as type, COUNT(n) as count",
                "relationship_types": "MATCH ()-[r]->() RETURN type(r) as type, COUNT(r) as count",
            }

            results = {}
            for key, query in queries.items():
                result = tx.run(query)
                if key in ["node_types", "relationship_types"]:
                    results[key] = {
                        record["type"]: record["count"] for record in result
                    }
                else:
                    results[key] = result.single()["count"]

            return results

        try:
            with self.driver.session(database=self.database) as session:
                stats_data = session.execute_read(get_stats_tx)

                stats = GraphStats(
                    total_nodes=stats_data["node_count"],
                    total_relationships=stats_data["relationship_count"],
                    nodes_by_type=stats_data["node_types"],
                    relationships_by_type=stats_data["relationship_types"],
                    last_updated=datetime.now(),
                )

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="get_stats",
                    nodes=[],
                    relationships=[],
                    paths=[],
                    aggregations=asdict(stats),
                    metadata={"stats_type": "comprehensive"},
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to get graph stats: {e}")

            return QueryResult(
                success=False,
                operation="get_stats",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Full-text Search

    async def search_content(
        self, query: str, node_types: Optional[List[NodeType]] = None
    ) -> QueryResult:
        """Perform full-text search across node content."""
        start_time = time.time()

        def search_tx(tx):
            if node_types:
                # Search specific node types
                type_queries = []
                for node_type in node_types:
                    if node_type in [NodeType.CONCEPT, NodeType.DOCUMENT]:
                        index_name = f"{node_type.value}_content_idx"
                        type_queries.append(
                            f"CALL db.index.fulltext.queryNodes('{index_name}', $query)"
                        )

                if type_queries:
                    full_query = (
                        " UNION ".join(type_queries)
                        + " YIELD node RETURN DISTINCT node LIMIT 50"
                    )
                else:
                    # Fallback to property search
                    full_query = """
                    MATCH (n)
                    WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $query)
                    RETURN n as node
                    LIMIT 50
                    """
            else:
                # Search all content indexes
                full_query = """
                CALL db.index.fulltext.queryNodes('concept_content_idx', $query)
                YIELD node
                RETURN node
                UNION
                CALL db.index.fulltext.queryNodes('document_content_idx', $query)
                YIELD node
                RETURN node
                LIMIT 50
                """

            try:
                result = tx.run(full_query, query=query)
                return result.data()
            except Exception:
                # Fallback to simple property search
                fallback_query = """
                MATCH (n)
                WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $query)
                RETURN n as node
                LIMIT 50
                """
                result = tx.run(fallback_query, query=query)
                return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(search_tx)

                nodes = [dict(record["node"]) for record in records]
                execution_time = time.time() - start_time

                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="search_content",
                    nodes=nodes,
                    relationships=[],
                    paths=[],
                    aggregations={},
                    metadata={
                        "search_query": query,
                        "node_types": [nt.value for nt in node_types]
                        if node_types
                        else None,
                        "result_count": len(nodes),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to search content: {e}")

            return QueryResult(
                success=False,
                operation="search_content",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Custom Cypher Queries

    async def execute_cypher(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> QueryResult:
        """Execute custom Cypher query."""
        if parameters is None:
            parameters = {}

        start_time = time.time()

        def execute_cypher_tx(tx):
            result = tx.run(query, **parameters)
            return result.data()

        try:
            with self.driver.session(database=self.database) as session:
                records = session.execute_read(execute_cypher_tx)

                # Extract nodes, relationships, and other data
                nodes = []
                relationships = []
                other_data = []

                for record in records:
                    for key, value in record.items():
                        if hasattr(value, "labels") and hasattr(value, "items"):  # Node
                            nodes.append(dict(value))
                        elif hasattr(value, "type") and hasattr(
                            value, "start_node"
                        ):  # Relationship
                            relationships.append(dict(value))
                        else:
                            other_data.append({key: value})

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time)

                return QueryResult(
                    success=True,
                    operation="execute_cypher",
                    nodes=nodes,
                    relationships=relationships,
                    paths=[],
                    aggregations={"raw_results": records, "other_data": other_data},
                    metadata={
                        "query": query,
                        "parameters": list(parameters.keys()),
                        "result_count": len(records),
                    },
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to execute cypher query: {e}")

            return QueryResult(
                success=False,
                operation="execute_cypher",
                nodes=[],
                relationships=[],
                paths=[],
                aggregations={},
                metadata={"query": query},
                execution_time=execution_time,
                errors=[str(e)],
            )

    # Utility Methods

    def _update_query_stats(self, execution_time: float):
        """Update query performance statistics."""
        self.query_count += 1
        self.total_query_time += execution_time

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_query_time = (
            self.total_query_time / self.query_count if self.query_count > 0 else 0
        )

        return {
            "connected": self.connected,
            "neo4j_available": self.neo4j_available,
            "total_queries": self.query_count,
            "total_query_time": self.total_query_time,
            "average_query_time": avg_query_time,
            "last_health_check": self.last_health_check.isoformat()
            if self.last_health_check
            else None,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the graph database."""
        health_info = {
            "status": "unknown",
            "connected": self.connected,
            "neo4j_available": self.neo4j_available,
            "database": self.database,
            "uri": self.uri,
            "performance": self.get_performance_stats(),
        }

        if not self.connected:
            health_info["status"] = "disconnected"
            return health_info

        try:
            # Test basic connectivity
            result = await self.execute_cypher("RETURN 1 as test")
            if result.success:
                health_info["status"] = "healthy"
                health_info["test_query"] = "passed"
            else:
                health_info["status"] = "unhealthy"
                health_info["test_query"] = "failed"
                health_info["errors"] = result.errors

            self.last_health_check = datetime.now()

        except Exception as e:
            health_info["status"] = "error"
            health_info["error"] = str(e)

        return health_info

    # High-level convenience methods

    async def create_agent_node(
        self, agent_id: str, name: str, properties: Dict[str, Any] = None
    ) -> QueryResult:
        """Convenience method to create an agent node."""
        if properties is None:
            properties = {}

        properties.update({"name": name, "type": "agent", "status": "active"})

        node = GraphNode(id=agent_id, type=NodeType.AGENT, properties=properties)

        return await self.create_node(node)

    async def create_workflow_node(
        self, workflow_id: str, name: str, status: str = "created"
    ) -> QueryResult:
        """Convenience method to create a workflow node."""
        properties = {"name": name, "status": status, "type": "workflow"}

        node = GraphNode(id=workflow_id, type=NodeType.WORKFLOW, properties=properties)

        return await self.create_node(node)

    async def create_dependency_relationship(
        self, source_id: str, target_id: str, dependency_type: str = "requires"
    ) -> QueryResult:
        """Convenience method to create a dependency relationship."""
        relationship = GraphRelationship(
            id=str(uuid.uuid4()),
            type=RelationType.DEPENDS_ON,
            source_id=source_id,
            target_id=target_id,
            properties={"dependency_type": dependency_type},
        )

        return await self.create_relationship(relationship)


# Utility functions for creating common graph elements


def create_concept_node(
    concept_id: str, name: str, category: str, description: str = None
) -> GraphNode:
    """Create a concept node."""
    properties = {"name": name, "category": category, "type": "concept"}

    if description:
        properties["description"] = description

    return GraphNode(id=concept_id, type=NodeType.CONCEPT, properties=properties)


def create_document_node(
    doc_id: str, title: str, path: str, content: str = None
) -> GraphNode:
    """Create a document node."""
    properties = {"title": title, "path": path, "type": "document"}

    if content:
        properties["content"] = content[:1000]  # Truncate for performance
        properties["word_count"] = len(content.split())

    return GraphNode(id=doc_id, type=NodeType.DOCUMENT, properties=properties)


def create_task_node(
    task_id: str, name: str, priority: str = "normal", status: str = "pending"
) -> GraphNode:
    """Create a task node."""
    properties = {"name": name, "priority": priority, "status": status, "type": "task"}

    return GraphNode(id=task_id, type=NodeType.TASK, properties=properties)


async def main():
    """Main function for testing the Neo4j graph service."""
    service = GraphDatabaseService()

    try:
        # Connect to database
        connected = await service.connect()
        if not connected:
            print("Failed to connect to Neo4j database")
            return

        print("Connected to Neo4j database")

        # Create some test nodes
        agent_node = GraphNode(
            id="agent-001",
            type=NodeType.AGENT,
            properties={"name": "TestAgent", "status": "active"},
        )

        task_node = GraphNode(
            id="task-001",
            type=NodeType.TASK,
            properties={"name": "Test Task", "priority": "high"},
        )

        # Create nodes
        agent_result = await service.create_node(agent_node)
        task_result = await service.create_node(task_node)

        print(f"Created agent: {agent_result.success}")
        print(f"Created task: {task_result.success}")

        # Create relationship
        relationship = GraphRelationship(
            id="rel-001",
            type=RelationType.ASSIGNED_TO,
            source_id="task-001",
            target_id="agent-001",
            properties={"assigned_at": datetime.now().isoformat()},
        )

        rel_result = await service.create_relationship(relationship)
        print(f"Created relationship: {rel_result.success}")

        # Query the graph
        stats_result = await service.get_graph_stats()
        if stats_result.success:
            print(f"Graph stats: {stats_result.aggregations}")

        # Health check
        health = await service.health_check()
        print(f"Health status: {health['status']}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
