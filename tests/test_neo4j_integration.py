"""
Neo4j Integration Test Suite for Gadugi v0.3

Tests Neo4j connectivity, schema initialization, and basic operations.
"""

import os
import pytest
from typing import Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError


class Neo4jConnection:
    """Neo4j connection manager for testing."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7475",
        user: str = "neo4j",
        password: Optional[str] = None,
    ):
        """Initialize Neo4j connection."""
        self.uri = uri
        self.user = user
        # Use environment variable or default password
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver: Optional[Driver] = None  # type: ignore[assignment]

    def connect(self) -> Driver:  # type: ignore[assignment]
        """Establish connection to Neo4j."""
        if not self.driver:
            self.driver = GraphDatabase.driver(  # type: ignore[assignment]
                self.uri, auth=(self.user, self.password)
            )
        return self.driver

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None

    def test_connection(self) -> bool:
        """Test if Neo4j is accessible."""
        try:
            driver = self.connect()
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                single_result = result.single()
                return single_result is not None and single_result["test"] == 1
        except (ServiceUnavailable, AuthError) as e:
            print(f"Connection failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False


class TestNeo4jIntegration:
    """Test suite for Neo4j integration."""

    @pytest.fixture
    def neo4j_conn(self):
        """Provide Neo4j connection for tests."""
        conn = Neo4jConnection()
        yield conn
        conn.close()

    def test_neo4j_connection(self, neo4j_conn):
        """Test basic Neo4j connectivity on port 7475."""
        assert neo4j_conn.test_connection(), "Failed to connect to Neo4j on port 7475"

    def test_schema_initialization(self, neo4j_conn):
        """Test that schema can be initialized."""
        driver = neo4j_conn.connect()

        # Read schema file
        schema_path = "neo4j/init/init_schema.cypher"
        assert os.path.exists(schema_path), f"Schema file not found: {schema_path}"

        with open(schema_path, "r") as f:
            schema_content = f.read()

        # Execute schema commands
        with driver.session() as session:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_content.split(";") if s.strip()]

            for statement in statements:
                if statement and not statement.startswith("//"):
                    try:
                        session.run(statement)
                    except Exception as e:
                        pytest.fail(f"Failed to execute schema statement: {e}")

    def test_agent_nodes_created(self, neo4j_conn):
        """Test that agent nodes are created properly."""
        driver = neo4j_conn.connect()

        with driver.session() as session:
            # Check for system agents
            result = session.run("""
                MATCH (a:Agent)
                WHERE a.id IN ['system', 'orchestrator', 'workflow_manager']
                RETURN a.id as id, a.name as name, a.type as type
                ORDER BY a.id
            """)

            agents = list(result)
            assert len(agents) >= 3, "Expected at least 3 system agents"

            # Verify each agent
            agent_ids = [a["id"] for a in agents]
            assert "system" in agent_ids, "System agent not found"
            assert "orchestrator" in agent_ids, "Orchestrator agent not found"
            assert "workflow_manager" in agent_ids, "Workflow manager not found"

    def test_tool_nodes_created(self, neo4j_conn):
        """Test that tool nodes are created properly."""
        driver = neo4j_conn.connect()

        with driver.session() as session:
            # Check for tools
            result = session.run("""
                MATCH (t:Tool)
                WHERE t.id IN ['read', 'write', 'bash', 'grep']
                RETURN t.id as id, t.name as name, t.category as category
                ORDER BY t.id
            """)

            tools = list(result)
            assert len(tools) >= 4, "Expected at least 4 basic tools"

            # Verify tool categories
            tool_categories = {t["id"]: t["category"] for t in tools}
            assert tool_categories.get("read") == "file_ops", "Read tool has wrong category"
            assert tool_categories.get("bash") == "execution", "Bash tool has wrong category"

    def test_relationships_created(self, neo4j_conn):
        """Test that relationships between nodes are created."""
        driver = neo4j_conn.connect()

        with driver.session() as session:
            # Check system relationships
            result = session.run("""
                MATCH (system:Agent {id: 'system'})-[r:MANAGES]->(orchestrator:Agent {id: 'orchestrator'})
                RETURN count(r) as count
            """)

            count = result.single()["count"]
            assert count >= 1, "System->Orchestrator relationship not found"

            # Check tool usage relationships
            result = session.run("""
                MATCH (orchestrator:Agent {id: 'orchestrator'})-[r:USES]->(t:Tool)
                RETURN count(r) as count
            """)

            count = result.single()["count"]
            assert count >= 3, "Orchestrator should use at least 3 tools"

    def test_crud_operations(self, neo4j_conn):
        """Test basic CRUD operations."""
        driver = neo4j_conn.connect()

        with driver.session() as session:
            # Create a test node
            session.run("""
                CREATE (test:TestNode {
                    id: 'test_123',
                    name: 'Test Node',
                    created: datetime()
                })
            """)

            # Read the node
            result = session.run("""
                MATCH (test:TestNode {id: 'test_123'})
                RETURN test.name as name
            """)

            name = result.single()["name"]
            assert name == "Test Node", "Failed to read created node"

            # Update the node
            session.run("""
                MATCH (test:TestNode {id: 'test_123'})
                SET test.updated = datetime(), test.status = 'active'
            """)

            # Verify update
            result = session.run("""
                MATCH (test:TestNode {id: 'test_123'})
                RETURN test.status as status
            """)

            status = result.single()["status"]
            assert status == "active", "Failed to update node"

            # Delete the node
            session.run("""
                MATCH (test:TestNode {id: 'test_123'})
                DELETE test
            """)

            # Verify deletion
            result = session.run("""
                MATCH (test:TestNode {id: 'test_123'})
                RETURN count(test) as count
            """)

            count = result.single()["count"]
            assert count == 0, "Failed to delete node"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
