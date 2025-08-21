#!/usr/bin/env python3
"""Tests for Neo4j Graph Database Service."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Add services directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "neo4j-graph"))

from neo4j_graph_service import (
    GraphDatabaseService,
    GraphNode,
    GraphRelationship,
    GraphStats,
    NodeType,
    QueryResult,
    QueryType,
    RecommendationRequest,
    RelationType,
    create_concept_node,
    create_document_node,
    create_task_node,
)


class TestNeo4jGraphService(unittest.IsolatedAsyncioTestCase):
    """Test cases for Neo4j Graph Database Service."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.service = GraphDatabaseService(
            uri="bolt://localhost:7687",
            username="test",
            password="test",
            database="test_gadugi",
        )

        # Sample test data
        self.test_agent_node = GraphNode(
            id="agent-test-001",
            type=NodeType.AGENT,
            properties={
                "name": "TestAgent",
                "status": "active",
                "capabilities": ["analysis", "generation"],
            },
        )

        self.test_task_node = GraphNode(
            id="task-test-001",
            type=NodeType.TASK,
            properties={
                "name": "Test Task",
                "priority": "high",
                "status": "pending",
                "description": "A test task for validation",
            },
        )

        self.test_relationship = GraphRelationship(
            id="rel-test-001",
            type=RelationType.ASSIGNED_TO,
            source_id="task-test-001",
            target_id="agent-test-001",
            properties={"assigned_at": datetime.now().isoformat(), "priority": "high"},
        )

    async def asyncTearDown(self) -> None:
        """Clean up test fixtures."""
        if hasattr(self.service, "driver") and self.service.driver:
            await self.service.disconnect()

    def test_service_initialization(self) -> None:
        """Test service initializes properly."""
        assert self.service is not None
        assert self.service.logger is not None
        assert self.service.uri == "bolt://localhost:7687"
        assert self.service.username == "test"
        assert self.service.database == "test_gadugi"
        assert not self.service.connected
        assert self.service.query_count == 0

    def test_node_type_enum(self) -> None:
        """Test NodeType enum functionality."""
        assert NodeType.AGENT.value == "agent"
        assert NodeType.WORKFLOW.value == "workflow"
        assert NodeType.TASK.value == "task"
        assert NodeType.MEMORY.value == "memory"
        assert NodeType.CONCEPT.value == "concept"
        assert NodeType.DOCUMENT.value == "document"

    def test_relationship_type_enum(self) -> None:
        """Test RelationType enum functionality."""
        assert RelationType.CREATED.value == "CREATED"
        assert RelationType.DEPENDS_ON.value == "DEPENDS_ON"
        assert RelationType.ASSIGNED_TO.value == "ASSIGNED_TO"
        assert RelationType.REFERENCES.value == "REFERENCES"
        assert RelationType.CONTAINS.value == "CONTAINS"

    def test_query_type_enum(self) -> None:
        """Test QueryType enum functionality."""
        assert QueryType.CREATE.value == "create"
        assert QueryType.READ.value == "read"
        assert QueryType.UPDATE.value == "update"
        assert QueryType.DELETE.value == "delete"
        assert QueryType.MATCH.value == "match"

    def test_graph_node_dataclass(self) -> None:
        """Test GraphNode dataclass functionality."""
        node = GraphNode(
            id="test-node",
            type=NodeType.CONCEPT,
            properties={"name": "Test Concept", "category": "testing"},
        )

        assert node.id == "test-node"
        assert node.type == NodeType.CONCEPT
        assert node.properties["name"] == "Test Concept"
        assert node.labels == ["concept"]  # Default from type
        assert node.created_at is not None
        assert node.updated_at is not None

    def test_graph_relationship_dataclass(self) -> None:
        """Test GraphRelationship dataclass functionality."""
        relationship = GraphRelationship(
            id="test-rel",
            type=RelationType.DEPENDS_ON,
            source_id="node1",
            target_id="node2",
            properties={"strength": "strong"},
        )

        assert relationship.id == "test-rel"
        assert relationship.type == RelationType.DEPENDS_ON
        assert relationship.source_id == "node1"
        assert relationship.target_id == "node2"
        assert relationship.strength == 1.0  # Default
        assert relationship.created_at is not None

    def test_query_result_dataclass(self) -> None:
        """Test QueryResult dataclass functionality."""
        result = QueryResult(
            success=True,
            operation="create_node",
            nodes=[{"id": "test", "name": "Test"}],
            relationships=[],
            paths=[],
            aggregations={},
            metadata={"count": 1},
            execution_time=0.5,
        )

        assert result.success
        assert result.operation == "create_node"
        assert len(result.nodes) == 1
        assert result.execution_time == 0.5
        assert len(result.warnings) == 0  # Default empty list
        assert len(result.errors) == 0  # Default empty list

    def test_graph_stats_dataclass(self) -> None:
        """Test GraphStats dataclass functionality."""
        stats = GraphStats(
            total_nodes=100,
            total_relationships=200,
            nodes_by_type={"agent": 10, "task": 90},
            relationships_by_type={"ASSIGNED_TO": 50, "DEPENDS_ON": 150},
        )

        assert stats.total_nodes == 100
        assert stats.total_relationships == 200
        assert "agent" in stats.nodes_by_type
        assert "ASSIGNED_TO" in stats.relationships_by_type
        assert stats.last_updated is not None

    def test_recommendation_request_dataclass(self) -> None:
        """Test RecommendationRequest dataclass functionality."""
        request = RecommendationRequest(
            source_node_id="node-123",
            recommendation_type="similar_nodes",
            max_results=5,
            filters={"type": "concept"},
            weights={"similarity": 0.8},
        )

        assert request.source_node_id == "node-123"
        assert request.recommendation_type == "similar_nodes"
        assert request.max_results == 5
        assert "type" in request.filters
        assert "similarity" in request.weights
        assert len(request.exclude_ids) == 0  # Default empty list

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_connect_success(self, mock_graph_db) -> None:
        """Test successful database connection."""
        # Mock driver and session
        mock_driver = Mock()
        mock_session = Mock()
        Mock()
        Mock()
        Mock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = 1  # Test query result
        mock_session.execute_write.return_value = None  # Schema creation

        result = await self.service.connect()

        assert result
        assert self.service.connected
        mock_graph_db.driver.assert_called_once()

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_connect_failure(self, mock_graph_db) -> None:
        """Test database connection failure."""
        mock_graph_db.driver.side_effect = Exception("Connection failed")

        result = await self.service.connect()

        assert not result
        assert not self.service.connected

    async def test_disconnect(self) -> None:
        """Test database disconnection."""
        # Mock driver
        mock_driver = Mock()
        self.service.driver = mock_driver
        self.service.connected = True

        await self.service.disconnect()

        mock_driver.close.assert_called_once()
        assert not self.service.connected

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_create_node_success(self, mock_graph_db) -> None:
        """Test successful node creation."""
        # Mock the Neo4j components
        mock_driver = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_record = Mock()

        # Setup return values
        mock_record.__getitem__ = Mock(return_value={"id": "test-node", "name": "Test"})
        mock_result.single.return_value = mock_record

        # Configure mocks
        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_write.return_value = mock_record

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.create_node(self.test_agent_node)

        assert result.success
        assert result.operation == "create_node"
        assert len(result.nodes) == 1
        assert "node_id" in result.metadata

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_create_node_failure(self, mock_graph_db) -> None:
        """Test node creation failure."""
        mock_driver = Mock()
        mock_session = Mock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_write.side_effect = Exception("Creation failed")

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.create_node(self.test_agent_node)

        assert not result.success
        assert len(result.errors) == 1
        assert "Creation failed" in result.errors[0]

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_get_node_success(self, mock_graph_db) -> None:
        """Test successful node retrieval."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_record = Mock()

        # Mock node data
        node_data = {"id": "test-node", "name": "Test Node", "type": "agent"}
        mock_record.__getitem__ = Mock(return_value=node_data)

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = mock_record

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.get_node("test-node")

        assert result.success
        assert result.operation == "get_node"
        assert len(result.nodes) == 1
        assert result.metadata["node_id"] == "test-node"

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_get_node_not_found(self, mock_graph_db) -> None:
        """Test node retrieval when node not found."""
        mock_driver = Mock()
        mock_session = Mock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = None  # Node not found

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.get_node("nonexistent-node")

        assert not result.success
        assert len(result.warnings) == 1
        assert "not found" in result.warnings[0]

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_update_node_success(self, mock_graph_db) -> None:
        """Test successful node update."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_record = Mock()

        updated_data = {
            "id": "test-node",
            "name": "Updated Test Node",
            "status": "modified",
        }
        mock_record.__getitem__ = Mock(return_value=updated_data)

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_write.return_value = mock_record

        self.service.driver = mock_driver
        self.service.connected = True

        update_properties = {"name": "Updated Test Node", "status": "modified"}
        result = await self.service.update_node("test-node", update_properties)

        assert result.success
        assert result.operation == "update_node"
        assert "updated_properties" in result.metadata
        assert len(result.metadata["updated_properties"]) == 2

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_delete_node_success(self, mock_graph_db) -> None:
        """Test successful node deletion."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_deleted = 1
        mock_counters.relationships_deleted = 2
        mock_summary.counters.return_value = mock_counters

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_write.return_value = mock_summary

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.delete_node("test-node")

        assert result.success
        assert result.operation == "delete_node"
        assert result.metadata["nodes_deleted"] == 1
        assert result.metadata["relationships_deleted"] == 2

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_create_relationship_success(self, mock_graph_db) -> None:
        """Test successful relationship creation."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_record = Mock()

        # Mock relationship and node data
        rel_data = {"id": "test-rel", "type": "ASSIGNED_TO"}
        source_data = {"id": "task-001", "name": "Test Task"}
        target_data = {"id": "agent-001", "name": "Test Agent"}

        mock_record.__getitem__ = Mock(
            side_effect=lambda key: {"r": rel_data, "a": source_data, "b": target_data}[key],
        )

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_write.return_value = mock_record

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.create_relationship(self.test_relationship)

        assert result.success
        assert result.operation == "create_relationship"
        assert len(result.relationships) == 1
        assert len(result.nodes) == 2
        assert "relationship_id" in result.metadata

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_find_nodes_success(self, mock_graph_db) -> None:
        """Test successful node finding."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock found nodes
        found_nodes = [
            {"n": {"id": "agent-001", "name": "Agent 1", "type": "agent"}},
            {"n": {"id": "agent-002", "name": "Agent 2", "type": "agent"}},
        ]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = found_nodes

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.find_nodes(
            node_type=NodeType.AGENT,
            properties={"status": "active"},
            limit=10,
        )

        assert result.success
        assert result.operation == "find_nodes"
        assert len(result.nodes) == 2
        assert result.metadata["result_count"] == 2
        assert result.metadata["limit"] == 10

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_find_relationships_success(self, mock_graph_db) -> None:
        """Test successful relationship finding."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock found relationships
        found_rels = [
            {
                "r": {"id": "rel-001", "type": "ASSIGNED_TO"},
                "a": {"id": "task-001", "name": "Task 1"},
                "b": {"id": "agent-001", "name": "Agent 1"},
            },
        ]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = found_rels

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.find_relationships(
            source_id="task-001",
            relationship_type=RelationType.ASSIGNED_TO,
        )

        assert result.success
        assert result.operation == "find_relationships"
        assert len(result.relationships) == 1
        assert len(result.nodes) == 2  # Source and target nodes
        assert result.metadata["result_count"] == 1

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_find_paths_success(self, mock_graph_db) -> None:
        """Test successful path finding."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock path with nodes and relationships
        mock_path = Mock()
        mock_path.nodes = [
            Mock(__iter__=lambda: iter([("id", "node1"), ("name", "Node 1")])),
            Mock(__iter__=lambda: iter([("id", "node2"), ("name", "Node 2")])),
        ]
        mock_path.relationships = [
            Mock(__iter__=lambda: iter([("id", "rel1"), ("type", "CONNECTS")])),
        ]

        found_paths = [{"path": mock_path}]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = found_paths

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.find_paths("node1", "node2", max_depth=3)

        assert result.success
        assert result.operation == "find_paths"
        assert len(result.paths) == 1
        assert result.metadata["paths_found"] == 1

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_get_node_neighbors_success(self, mock_graph_db) -> None:
        """Test successful neighbor node retrieval."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock neighbor data
        neighbors = [
            {
                "neighbor": {"id": "neighbor-001", "name": "Neighbor 1"},
                "r": {"id": "rel-001", "type": "CONNECTS"},
            },
        ]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = neighbors

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.get_node_neighbors(
            "central-node",
            relationship_types=[RelationType.CONNECTS],
            direction="outgoing",
        )

        assert result.success
        assert result.operation == "get_neighbors"
        assert len(result.nodes) == 1
        assert result.metadata["neighbor_count"] == 1

    def test_build_similar_nodes_query(self) -> None:
        """Test similar nodes query building."""
        request = RecommendationRequest(
            source_node_id="test-node",
            recommendation_type="similar_nodes",
            max_results=5,
        )

        query = self.service._build_similar_nodes_query(request)

        assert "MATCH (source {id: $source_id})" in query
        assert "commonConnections" in query
        assert "LIMIT 5" in query

    def test_build_related_content_query(self) -> None:
        """Test related content query building."""
        request = RecommendationRequest(
            source_node_id="test-node",
            recommendation_type="related_content",
            max_results=10,
        )

        query = self.service._build_related_content_query(request)

        assert "RELATED_TO|:REFERENCES|:SIMILAR_TO" in query
        assert "LIMIT 10" in query

    def test_build_next_actions_query(self) -> None:
        """Test next actions query building."""
        request = RecommendationRequest(
            source_node_id="test-node",
            recommendation_type="next_actions",
            max_results=3,
        )

        query = self.service._build_next_actions_query(request)

        assert "DEPENDS_ON" in query
        assert "Next dependency" in query
        assert "LIMIT 3" in query

    def test_build_recommendation_params(self) -> None:
        """Test recommendation parameter building."""
        request = RecommendationRequest(
            source_node_id="test-node",
            recommendation_type="similar_nodes",
            max_results=5,
            exclude_ids=["exclude-1", "exclude-2"],
        )

        params = self.service._build_recommendation_params(request)

        assert params["source_id"] == "test-node"
        assert params["max_results"] == 5
        assert len(params["exclude_ids"]) == 2

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_get_graph_stats_success(self, mock_graph_db) -> None:
        """Test successful graph statistics retrieval."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock stats data
        def mock_run_side_effect(query):
            mock_result = Mock()
            if "COUNT(n)" in query:
                mock_result.single.return_value = {"count": 100}
            elif "COUNT(r)" in query:
                mock_result.single.return_value = {"count": 200}
            elif "labels(n)" in query:
                mock_result.__iter__ = lambda: iter(
                    [{"type": "agent", "count": 50}, {"type": "task", "count": 50}],
                )
            elif "type(r)" in query:
                mock_result.__iter__ = lambda: iter(
                    [
                        {"type": "ASSIGNED_TO", "count": 100},
                        {"type": "DEPENDS_ON", "count": 100},
                    ],
                )
            return mock_result

        mock_transaction = Mock()
        mock_transaction.run.side_effect = mock_run_side_effect

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = {
            "node_count": 100,
            "relationship_count": 200,
            "node_types": {"agent": 50, "task": 50},
            "relationship_types": {"ASSIGNED_TO": 100, "DEPENDS_ON": 100},
        }

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.get_graph_stats()

        assert result.success
        assert result.operation == "get_stats"
        assert "total_nodes" in result.aggregations
        assert result.aggregations["total_nodes"] == 100
        assert result.aggregations["total_relationships"] == 200

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_search_content_success(self, mock_graph_db) -> None:
        """Test successful content search."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock search results
        search_results = [
            {
                "node": {
                    "id": "doc-001",
                    "title": "Test Document",
                    "content": "test content",
                },
            },
        ]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = search_results

        self.service.driver = mock_driver
        self.service.connected = True

        result = await self.service.search_content(
            "test query",
            node_types=[NodeType.DOCUMENT, NodeType.CONCEPT],
        )

        assert result.success
        assert result.operation == "search_content"
        assert len(result.nodes) == 1
        assert result.metadata["search_query"] == "test query"
        assert result.metadata["result_count"] == 1

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_execute_cypher_success(self, mock_graph_db) -> None:
        """Test successful custom Cypher query execution."""
        mock_driver = Mock()
        mock_session = Mock()

        # Mock cypher results
        cypher_results = [{"node_name": "Test Node", "relationship_count": 5}]

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = cypher_results

        self.service.driver = mock_driver
        self.service.connected = True

        custom_query = "MATCH (n) RETURN n.name as node_name, COUNT(*) as relationship_count"
        result = await self.service.execute_cypher(custom_query, {"param1": "value1"})

        assert result.success
        assert result.operation == "execute_cypher"
        assert "raw_results" in result.aggregations
        assert result.metadata["query"] == custom_query
        assert result.metadata["result_count"] == 1

    def test_update_query_stats(self) -> None:
        """Test query statistics updating."""
        initial_count = self.service.query_count
        initial_time = self.service.total_query_time

        self.service._update_query_stats(1.5)

        assert self.service.query_count == initial_count + 1
        assert self.service.total_query_time == initial_time + 1.5

    def test_get_performance_stats(self) -> None:
        """Test performance statistics retrieval."""
        # Set some test values
        self.service.query_count = 10
        self.service.total_query_time = 25.0
        self.service.connected = True

        stats = self.service.get_performance_stats()

        assert stats["connected"]
        assert stats["total_queries"] == 10
        assert stats["total_query_time"] == 25.0
        assert stats["average_query_time"] == 2.5

    async def test_health_check_healthy(self) -> None:
        """Test health check when service is healthy."""
        # Mock successful cypher execution
        with patch.object(self.service, "execute_cypher") as mock_execute:
            mock_result = Mock()
            mock_result.success = True
            mock_execute.return_value = mock_result

            self.service.connected = True
            health = await self.service.health_check()

            assert health["status"] == "healthy"
            assert health["connected"]
            assert health["test_query"] == "passed"

    async def test_health_check_disconnected(self) -> None:
        """Test health check when service is disconnected."""
        self.service.connected = False
        health = await self.service.health_check()

        assert health["status"] == "disconnected"
        assert not health["connected"]

    async def test_health_check_unhealthy(self) -> None:
        """Test health check when service is unhealthy."""
        # Mock failed cypher execution
        with patch.object(self.service, "execute_cypher") as mock_execute:
            mock_result = Mock()
            mock_result.success = False
            mock_result.errors = ["Query failed"]
            mock_execute.return_value = mock_result

            self.service.connected = True
            health = await self.service.health_check()

            assert health["status"] == "unhealthy"
            assert health["test_query"] == "failed"
            assert "errors" in health

    async def test_create_agent_node_convenience(self) -> None:
        """Test convenience method for creating agent nodes."""
        with patch.object(self.service, "create_node") as mock_create:
            mock_result = Mock()
            mock_result.success = True
            mock_create.return_value = mock_result

            result = await self.service.create_agent_node(
                "agent-123",
                "Test Agent",
                {"skill": "analysis"},
            )

            assert result.success
            mock_create.assert_called_once()

            # Check the node that was created
            created_node = mock_create.call_args[0][0]
            assert created_node.id == "agent-123"
            assert created_node.type == NodeType.AGENT
            assert created_node.properties["name"] == "Test Agent"
            assert created_node.properties["skill"] == "analysis"

    async def test_create_workflow_node_convenience(self) -> None:
        """Test convenience method for creating workflow nodes."""
        with patch.object(self.service, "create_node") as mock_create:
            mock_result = Mock()
            mock_result.success = True
            mock_create.return_value = mock_result

            result = await self.service.create_workflow_node(
                "workflow-456",
                "Test Workflow",
                "running",
            )

            assert result.success
            mock_create.assert_called_once()

            # Check the node that was created
            created_node = mock_create.call_args[0][0]
            assert created_node.id == "workflow-456"
            assert created_node.type == NodeType.WORKFLOW
            assert created_node.properties["name"] == "Test Workflow"
            assert created_node.properties["status"] == "running"

    async def test_create_dependency_relationship_convenience(self) -> None:
        """Test convenience method for creating dependency relationships."""
        with patch.object(self.service, "create_relationship") as mock_create:
            mock_result = Mock()
            mock_result.success = True
            mock_create.return_value = mock_result

            result = await self.service.create_dependency_relationship(
                "task-1",
                "task-2",
                "blocks",
            )

            assert result.success
            mock_create.assert_called_once()

            # Check the relationship that was created
            created_rel = mock_create.call_args[0][0]
            assert created_rel.source_id == "task-1"
            assert created_rel.target_id == "task-2"
            assert created_rel.type == RelationType.DEPENDS_ON
            assert created_rel.properties["dependency_type"] == "blocks"

    def test_create_concept_node_utility(self) -> None:
        """Test utility function for creating concept nodes."""
        node = create_concept_node(
            "concept-123",
            "Machine Learning",
            "technology",
            "AI and ML concepts",
        )

        assert node.id == "concept-123"
        assert node.type == NodeType.CONCEPT
        assert node.properties["name"] == "Machine Learning"
        assert node.properties["category"] == "technology"
        assert node.properties["description"] == "AI and ML concepts"

    def test_create_document_node_utility(self) -> None:
        """Test utility function for creating document nodes."""
        content = "This is a test document with some content for testing purposes."
        node = create_document_node(
            "doc-456",
            "Test Document",
            "/docs/test.md",
            content,
        )

        assert node.id == "doc-456"
        assert node.type == NodeType.DOCUMENT
        assert node.properties["title"] == "Test Document"
        assert node.properties["path"] == "/docs/test.md"
        assert "word_count" in node.properties
        assert node.properties["word_count"] == len(content.split())

    def test_create_task_node_utility(self) -> None:
        """Test utility function for creating task nodes."""
        node = create_task_node(
            "task-789",
            "Implement Feature X",
            "high",
            "in_progress",
        )

        assert node.id == "task-789"
        assert node.type == NodeType.TASK
        assert node.properties["name"] == "Implement Feature X"
        assert node.properties["priority"] == "high"
        assert node.properties["status"] == "in_progress"

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.service.logger is not None
        assert self.service.logger.name == "neo4j_graph"

        import logging

        assert self.service.logger.level == logging.INFO

    def test_neo4j_availability_check(self) -> None:
        """Test Neo4j availability detection."""
        # The service should detect whether Neo4j driver is available
        assert isinstance(self.service.neo4j_available, bool)

    def test_mock_implementation_fallback(self) -> None:
        """Test that mock implementation works when Neo4j is not available."""
        # Test with mock driver when Neo4j is not available
        if not self.service.neo4j_available:
            # Mock driver should be created without errors
            from neo4j_graph_service import MockDriver

            mock_driver = MockDriver()
            mock_session = mock_driver.session()

            assert mock_driver is not None
            assert mock_session is not None

    @patch("neo4j_graph_service.GraphDatabase")
    async def test_schema_initialization(self, mock_graph_db) -> None:
        """Test database schema initialization."""
        mock_driver = Mock()
        mock_session = Mock()
        Mock()

        mock_graph_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        mock_session.execute_read.return_value = 1  # Test query result
        mock_session.execute_write.return_value = None  # Schema creation

        self.service.driver = mock_driver

        # This should not raise an exception
        await self.service._initialize_schema()

        # Verify schema queries were executed
        mock_session.execute_write.assert_called()

    def test_cache_functionality(self) -> None:
        """Test query cache functionality."""
        # Test cache initialization
        assert len(self.service.query_cache) == 0
        assert self.service.cache_max_size == 1000

        # The actual caching logic would be tested in integration tests
        # since it depends on the specific query implementation


if __name__ == "__main__":
    unittest.main()
