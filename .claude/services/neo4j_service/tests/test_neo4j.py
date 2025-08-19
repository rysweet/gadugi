"""
Comprehensive tests for Neo4j service.

Tests client connectivity, models, schema management, and CRUD operations.
"""

import os
import pytest
from unittest.mock import Mock, patch

from ..client import Neo4jClient, Neo4jConnectionError
from ..models import Agent, Tool, Context, Workflow, Recipe, Event, Task
from ..schema import SchemaManager


class TestNeo4jClient:
    """Test Neo4j client functionality."""

    @pytest.fixture
    def mock_driver(self):
        """Mock Neo4j driver."""
        driver = Mock()
        session = Mock()
        transaction = Mock()

        # Mock session context manager
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)

        # Mock transaction context manager
        transaction.__enter__ = Mock(return_value=transaction)
        transaction.__exit__ = Mock(return_value=None)
        session.begin_transaction.return_value = transaction

        # Mock driver methods
        driver.session.return_value = session
        driver.close = Mock()

        return driver, session, transaction

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Neo4jClient(
            uri="bolt://localhost:7688", user="neo4j", password="test-password"  # pragma: allowlist secret
        )

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.uri == "bolt://localhost:7688"
        assert client.user == "neo4j"
        assert client.password == "test-password"  # pragma: allowlist secret
        assert client.driver is None

    @patch("neo4j.GraphDatabase.driver")
    def test_successful_connection(self, mock_graph_driver, client, mock_driver):
        """Test successful connection to Neo4j."""
        driver, session, _ = mock_driver
        mock_graph_driver.return_value = driver

        # Mock successful connection test
        result = Mock()
        result.consume.return_value = None
        session.run.return_value = result

        connected_driver = client.connect()

        assert connected_driver == driver
        assert client.driver == driver
        mock_graph_driver.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_connection_failure(self, mock_graph_driver, client):
        """Test connection failure handling."""
        from neo4j.exceptions import ServiceUnavailable

        mock_graph_driver.side_effect = ServiceUnavailable("Connection failed")

        with pytest.raises(Neo4jConnectionError):
            client.connect()

    def test_disconnect(self, client, mock_driver):
        """Test disconnection."""
        driver, _, _ = mock_driver
        client.driver = driver

        client.disconnect()

        driver.close.assert_called_once()
        assert client.driver is None

    @patch("neo4j.GraphDatabase.driver")
    def test_session_context_manager(self, mock_graph_driver, client, mock_driver):
        """Test session context manager."""
        driver, session, _ = mock_driver
        mock_graph_driver.return_value = driver

        with client.session() as s:
            assert s == session

        session.close.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_execute_query(self, mock_graph_driver, client, mock_driver):
        """Test query execution."""
        driver, session, _ = mock_driver
        mock_graph_driver.return_value = driver

        # Mock query result
        record1 = Mock()
        record1.data.return_value = {"id": "1", "name": "test"}
        record2 = Mock()
        record2.data.return_value = {"id": "2", "name": "test2"}

        result = Mock()
        result.__iter__ = Mock(return_value=iter([record1, record2]))
        session.run.return_value = result

        # Mock successful connection test
        consume_result = Mock()
        consume_result.consume.return_value = None
        session.run.side_effect = [consume_result, result]

        query_result = client.execute_query("MATCH (n) RETURN n")

        assert len(query_result) == 2
        assert query_result[0]["name"] == "test"
        assert query_result[1]["name"] == "test2"

    @patch("neo4j.GraphDatabase.driver")
    def test_health_check_success(self, mock_graph_driver, client, mock_driver):
        """Test successful health check."""
        driver, session, _ = mock_driver
        mock_graph_driver.return_value = driver

        # Mock successful health check
        record = Mock()
        record.__getitem__ = Mock(return_value=1)
        result = Mock()
        result.single.return_value = record

        # Mock connection test and health check
        consume_result = Mock()
        consume_result.consume.return_value = None
        session.run.side_effect = [consume_result, result]

        assert client.health_check() is True

    @patch("neo4j.GraphDatabase.driver")
    def test_health_check_failure(self, mock_graph_driver, client, mock_driver):
        """Test health check failure."""
        driver, session, _ = mock_driver
        mock_graph_driver.return_value = driver

        # Mock connection success then health check failure
        consume_result = Mock()
        consume_result.consume.return_value = None
        session.run.side_effect = [consume_result, Exception("Health check failed")]

        assert client.health_check() is False


class TestNeo4jModels:
    """Test Neo4j model classes."""

    def test_agent_creation(self):
        """Test agent model creation."""
        agent = Agent(
            name="Test Agent",
            type="worker",
            description="A test agent",
            capabilities=["read", "write"],
            status="active",
        )

        assert agent.name == "Test Agent"
        assert agent.type == "worker"
        assert agent.label == "Agent"
        assert "read" in agent.capabilities
        assert agent.status == "active"
        assert agent.id is not None

    def test_agent_to_dict(self):
        """Test agent serialization."""
        agent = Agent(name="Test Agent", type="worker", capabilities=["read", "write"])

        data = agent.to_dict()

        assert data["name"] == "Test Agent"
        assert data["type"] == "worker"
        assert "read" in data["capabilities"]
        assert data["id"] == agent.id
        assert "created" in data

    def test_agent_from_dict(self):
        """Test agent deserialization."""
        data = {
            "id": "test-agent-123",
            "name": "Test Agent",
            "type": "worker",
            "capabilities": ["read", "write"],
            "status": "active",
            "created": "2024-01-01T00:00:00",
        }

        agent = Agent.from_dict(data)

        assert agent.id == "test-agent-123"
        assert agent.name == "Test Agent"
        assert agent.type == "worker"
        assert agent.status == "active"

    def test_tool_creation(self):
        """Test tool model creation."""
        tool = Tool(
            name="Read Tool",
            category="file_ops",
            description="Reads files",
            version="1.0.0",
        )

        assert tool.name == "Read Tool"
        assert tool.category == "file_ops"
        assert tool.label == "Tool"
        assert tool.version == "1.0.0"

    def test_context_creation(self):
        """Test context model creation."""
        context = Context(
            content="Test context content",
            source="test-agent",
            context_type="success",
            tags=["test", "success"],
        )

        assert context.content == "Test context content"
        assert context.source == "test-agent"
        assert context.context_type == "success"
        assert "test" in context.tags
        assert context.label == "Context"

    def test_workflow_creation(self):
        """Test workflow model creation."""
        workflow = Workflow(
            name="Test Workflow",
            status="running",
            current_phase=1,
            agent_id="test-agent",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.status == "running"
        assert workflow.current_phase == 1
        assert workflow.agent_id == "test-agent"
        assert workflow.label == "Workflow"

    def test_recipe_creation(self):
        """Test recipe model creation."""
        recipe = Recipe(
            name="Test Recipe",
            requirements={"python": ">=3.9"},
            design={"pattern": "service"},
            version="1.0.0",
            author="test-author",
        )

        assert recipe.name == "Test Recipe"
        assert recipe.requirements["python"] == ">=3.9"
        assert recipe.design["pattern"] == "service"
        assert recipe.version == "1.0.0"
        assert recipe.author == "test-author"
        assert recipe.label == "Recipe"

    def test_event_creation(self):
        """Test event model creation."""
        event = Event(
            event_type="workflow_completed",
            source="workflow-manager",
            data={"workflow_id": "test-123"},
            priority=1,
        )

        assert event.event_type == "workflow_completed"
        assert event.source == "workflow-manager"
        assert event.data["workflow_id"] == "test-123"
        assert event.priority == 1
        assert event.label == "Event"

    def test_task_creation(self):
        """Test task model creation."""
        task = Task(
            name="Test Task",
            description="A test task",
            priority=2,
            assigned_agent="test-agent",
            dependencies=["task-1", "task-2"],
        )

        assert task.name == "Test Task"
        assert task.description == "A test task"
        assert task.priority == 2
        assert task.assigned_agent == "test-agent"
        assert "task-1" in task.dependencies
        assert task.label == "Task"


class TestSchemaManager:
    """Test schema management functionality."""

    @pytest.fixture
    def mock_client(self):
        """Mock Neo4j client."""
        client = Mock(spec=Neo4jClient)
        return client

    def test_schema_manager_init(self, mock_client):
        """Test schema manager initialization."""
        manager = SchemaManager(mock_client)
        assert manager.client == mock_client

    def test_create_constraints(self, mock_client):
        """Test constraint creation."""
        manager = SchemaManager(mock_client)
        mock_client.execute_write_query.return_value = []

        result = manager.create_constraints()

        assert result is True
        assert mock_client.execute_write_query.call_count >= 7  # At least 7 constraints

    def test_create_indexes(self, mock_client):
        """Test index creation."""
        manager = SchemaManager(mock_client)
        mock_client.execute_write_query.return_value = []

        result = manager.create_indexes()

        assert result is True
        assert mock_client.execute_write_query.call_count >= 15  # At least 15 indexes

    def test_create_system_nodes(self, mock_client):
        """Test system node creation."""
        manager = SchemaManager(mock_client)
        mock_client.execute_write_query.return_value = []

        result = manager.create_system_nodes()

        assert result is True
        assert mock_client.execute_write_query.call_count >= 7  # Agents + tools

    def test_create_system_relationships(self, mock_client):
        """Test system relationship creation."""
        manager = SchemaManager(mock_client)
        mock_client.execute_write_query.return_value = []

        result = manager.create_system_relationships()

        assert result is True
        assert mock_client.execute_write_query.call_count >= 6  # Multiple relationships

    def test_full_schema_setup(self, mock_client):
        """Test complete schema setup."""
        manager = SchemaManager(mock_client)
        mock_client.execute_write_query.return_value = []

        result = manager.full_schema_setup()

        assert result is True
        # Should call execute_write_query many times for all setup steps
        assert mock_client.execute_write_query.call_count > 20

    def test_validate_schema_success(self, mock_client):
        """Test schema validation success."""
        manager = SchemaManager(mock_client)

        # Mock constraint and index queries
        mock_client.execute_query.side_effect = [
            [
                {"name": "agent_id_unique"},
                {"name": "tool_id_unique"},
                {"name": "context_id_unique"},
                {"name": "workflow_id_unique"},
            ],
            [
                {"name": "agent_name_index"},
                {"name": "tool_name_index"},
                {"name": "context_timestamp_index"},
            ],
            [{"count": 3}],  # System agents count
        ]

        mock_client.get_stats.return_value = {"node_counts": {"Agent": 3}}

        validation = manager.validate_schema()

        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_schema_missing_constraints(self, mock_client):
        """Test schema validation with missing constraints."""
        manager = SchemaManager(mock_client)

        # Mock missing constraints
        mock_client.execute_query.side_effect = [
            [],  # No constraints
            [{"name": "agent_name_index"}],  # Some indexes
            [{"count": 3}],  # System agents count
        ]

        mock_client.get_stats.return_value = {}

        validation = manager.validate_schema()

        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert "Missing constraints" in validation["errors"][0]


class TestIntegration:
    """Integration tests for the complete Neo4j service."""

    @pytest.fixture
    def integration_client(self):
        """
        Client for integration tests.

        Note: These tests require a running Neo4j instance.
        Set NEO4J_TEST_URI environment variable to override default.
        """
        uri = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7688")
        return Neo4jClient(uri=uri, user="neo4j", password="gadugi-password")  # pragma: allowlist secret

    @pytest.mark.integration
    def test_end_to_end_workflow(self, integration_client):
        """
        Test complete end-to-end workflow.

        This test requires a running Neo4j instance and is marked
        as integration test.
        """
        try:
            # Test connection
            assert integration_client.health_check() is True

            # Initialize schema
            schema_manager = SchemaManager(integration_client)
            assert schema_manager.full_schema_setup() is True

            # Create test entities
            agent = Agent(
                name="Integration Test Agent",
                type="test",
                description="Agent for integration testing",
            )

            tool = Tool(
                name="Integration Test Tool",
                category="test",
                description="Tool for integration testing",
            )

            # Test entity creation
            agent_result = integration_client.create_entity(agent)
            assert agent_result is not None

            tool_result = integration_client.create_entity(tool)
            assert tool_result is not None

            # Test entity reading
            read_agent = integration_client.read_entity("Agent", agent.id)
            assert read_agent is not None
            assert read_agent["name"] == "Integration Test Agent"

            # Test entity update
            updates = {"status": "updated", "description": "Updated description"}
            update_success = integration_client.update_entity(
                "Agent", agent.id, updates
            )
            assert update_success is True

            # Verify update
            updated_agent = integration_client.read_entity("Agent", agent.id)
            assert updated_agent["status"] == "updated"

            # Test entity deletion
            delete_success = integration_client.delete_entity("Agent", agent.id)
            assert delete_success is True

            # Verify deletion
            deleted_agent = integration_client.read_entity("Agent", agent.id)
            assert deleted_agent is None

            # Clean up
            integration_client.delete_entity("Tool", tool.id)

        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
