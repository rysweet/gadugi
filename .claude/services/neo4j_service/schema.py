"""
Neo4j Schema Manager for Gadugi v0.3

Manages database schema initialization, constraints, and indexes.
"""

import logging
import os
from typing import Dict, Optional, Any

from .client import Neo4jClient


logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages Neo4j schema operations."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize schema manager.

        Args:
            client: Neo4j client instance
        """
        self.client = client

    def initialize_schema(self, schema_file: Optional[str] = None) -> bool:
        """
        Initialize the database schema.

        Args:
            schema_file: Path to schema file (defaults to neo4j/init/init_schema.cypher)

        Returns:
            True if initialization succeeded, False otherwise
        """
        if schema_file is None:
            # Look for schema file in standard locations
            schema_paths = [
                "neo4j-setup/init/init_schema.cypher",
                "../../../neo4j-setup/init/init_schema.cypher",
                "init_schema.cypher",
            ]

            schema_file = None
            for path in schema_paths:
                if os.path.exists(path):
                    schema_file = path
                    break

            if schema_file is None:
                logger.error("Schema file not found in standard locations")
                return False

        try:
            logger.info(f"Initializing schema from {schema_file}")

            # Read schema file
            with open(schema_file, "r") as f:
                schema_content = f.read()

            # Execute schema commands
            return self._execute_schema_commands(schema_content)

        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_file}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False

    def _execute_schema_commands(self, schema_content: str) -> bool:
        """
        Execute schema commands from content.

        Args:
            schema_content: Schema file content

        Returns:
            True if execution succeeded, False otherwise
        """
        try:
            # Split by semicolon and execute each statement
            statements = []
            current_statement = ""

            for line in schema_content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("//"):
                    continue

                current_statement += line + " "

                # If line ends with semicolon, it's a complete statement
                if line.endswith(";"):
                    statements.append(current_statement.rstrip("; "))
                    current_statement = ""

            # Add final statement if it doesn't end with semicolon
            if current_statement.strip():
                statements.append(current_statement.strip())

            # Execute each statement
            for statement in statements:
                if statement:
                    logger.debug(f"Executing: {statement[:100]}...")
                    self.client.execute_write_query(statement)

            logger.info(f"Successfully executed {len(statements)} schema statements")
            return True

        except Exception as e:
            logger.error(f"Failed to execute schema commands: {e}")
            return False

    def create_constraints(self) -> bool:
        """
        Create essential constraints for the schema.

        Returns:
            True if constraints created successfully
        """
        constraints = [
            # Unique constraints for IDs
            "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT context_id_unique IF NOT EXISTS FOR (c:Context) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT recipe_id_unique IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
        ]

        try:
            for constraint in constraints:
                self.client.execute_write_query(constraint)

            logger.info(f"Created {len(constraints)} constraints")
            return True

        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")
            return False

    def create_indexes(self) -> bool:
        """
        Create performance indexes for the schema.

        Returns:
            True if indexes created successfully
        """
        indexes = [
            # Name indexes for search
            "CREATE INDEX agent_name_index IF NOT EXISTS FOR (a:Agent) ON (a.name)",
            "CREATE INDEX tool_name_index IF NOT EXISTS FOR (t:Tool) ON (t.name)",
            "CREATE INDEX recipe_name_index IF NOT EXISTS FOR (r:Recipe) ON (r.name)",
            "CREATE INDEX workflow_name_index IF NOT EXISTS FOR (w:Workflow) ON (w.name)",
            "CREATE INDEX task_name_index IF NOT EXISTS FOR (t:Task) ON (t.name)",
            # Status indexes for filtering
            "CREATE INDEX agent_status_index IF NOT EXISTS FOR (a:Agent) ON (a.status)",
            "CREATE INDEX workflow_status_index IF NOT EXISTS FOR (w:Workflow) ON (w.status)",
            "CREATE INDEX event_status_index IF NOT EXISTS FOR (e:Event) ON (e.status)",
            "CREATE INDEX task_status_index IF NOT EXISTS FOR (t:Task) ON (t.status)",
            "CREATE INDEX recipe_status_index IF NOT EXISTS FOR (r:Recipe) ON (r.status)",
            # Timestamp indexes for time-based queries
            "CREATE INDEX context_timestamp_index IF NOT EXISTS FOR (c:Context) ON (c.created)",
            "CREATE INDEX event_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.created)",
            "CREATE INDEX workflow_timestamp_index IF NOT EXISTS FOR (w:Workflow) ON (w.created)",
            # Type indexes for categorization
            "CREATE INDEX agent_type_index IF NOT EXISTS FOR (a:Agent) ON (a.type)",
            "CREATE INDEX tool_category_index IF NOT EXISTS FOR (t:Tool) ON (t.category)",
            "CREATE INDEX context_type_index IF NOT EXISTS FOR (c:Context) ON (c.context_type)",
            "CREATE INDEX event_type_index IF NOT EXISTS FOR (e:Event) ON (e.event_type)",
            # Priority indexes for task management
            "CREATE INDEX event_priority_index IF NOT EXISTS FOR (e:Event) ON (e.priority)",
            "CREATE INDEX task_priority_index IF NOT EXISTS FOR (t:Task) ON (t.priority)",
        ]

        try:
            for index in indexes:
                self.client.execute_write_query(index)

            logger.info(f"Created {len(indexes)} indexes")
            return True

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False

    def create_system_nodes(self) -> bool:
        """
        Create essential system nodes.

        Returns:
            True if system nodes created successfully
        """
        system_nodes = [
            # System agents
            """
            MERGE (system:Agent {id: 'system'})
            ON CREATE SET
                system.name = 'Gadugi System',
                system.type = 'system',
                system.created = datetime(),
                system.status = 'active',
                system.description = 'Core system agent'
            """,
            """
            MERGE (orchestrator:Agent {id: 'orchestrator'})
            ON CREATE SET
                orchestrator.name = 'Orchestrator Agent',
                orchestrator.type = 'orchestrator',
                orchestrator.created = datetime(),
                orchestrator.status = 'active',
                orchestrator.description = 'Coordinates parallel task execution'
            """,
            """
            MERGE (workflow_manager:Agent {id: 'workflow_manager'})
            ON CREATE SET
                workflow_manager.name = 'Workflow Manager',
                workflow_manager.type = 'manager',
                workflow_manager.created = datetime(),
                workflow_manager.status = 'active',
                workflow_manager.description = 'Manages individual workflow execution'
            """,
            # Essential tools
            """
            MERGE (read_tool:Tool {id: 'read'})
            ON CREATE SET
                read_tool.name = 'Read',
                read_tool.category = 'file_ops',
                read_tool.created = datetime(),
                read_tool.description = 'Read files from filesystem'
            """,
            """
            MERGE (write_tool:Tool {id: 'write'})
            ON CREATE SET
                write_tool.name = 'Write',
                write_tool.category = 'file_ops',
                write_tool.created = datetime(),
                write_tool.description = 'Write files to filesystem'
            """,
            """
            MERGE (bash_tool:Tool {id: 'bash'})
            ON CREATE SET
                bash_tool.name = 'Bash',
                bash_tool.category = 'execution',
                bash_tool.created = datetime(),
                bash_tool.description = 'Execute bash commands'
            """,
            """
            MERGE (grep_tool:Tool {id: 'grep'})
            ON CREATE SET
                grep_tool.name = 'Grep',
                grep_tool.category = 'search',
                grep_tool.created = datetime(),
                grep_tool.description = 'Search files with patterns'
            """,
        ]

        try:
            for statement in system_nodes:
                self.client.execute_write_query(statement)

            logger.info("Created system nodes")
            return True

        except Exception as e:
            logger.error(f"Failed to create system nodes: {e}")
            return False

    def create_system_relationships(self) -> bool:
        """
        Create relationships between system entities.

        Returns:
            True if relationships created successfully
        """
        relationships = [
            # Agent management relationships
            """
            MATCH (system:Agent {id: 'system'})
            MATCH (orchestrator:Agent {id: 'orchestrator'})
            MERGE (system)-[:MANAGES]->(orchestrator)
            """,
            """
            MATCH (orchestrator:Agent {id: 'orchestrator'})
            MATCH (workflow_manager:Agent {id: 'workflow_manager'})
            MERGE (orchestrator)-[:COORDINATES]->(workflow_manager)
            """,
            # Tool usage relationships
            """
            MATCH (orchestrator:Agent {id: 'orchestrator'})
            MATCH (read_tool:Tool {id: 'read'})
            MERGE (orchestrator)-[:USES]->(read_tool)
            """,
            """
            MATCH (orchestrator:Agent {id: 'orchestrator'})
            MATCH (write_tool:Tool {id: 'write'})
            MERGE (orchestrator)-[:USES]->(write_tool)
            """,
            """
            MATCH (orchestrator:Agent {id: 'orchestrator'})
            MATCH (bash_tool:Tool {id: 'bash'})
            MERGE (orchestrator)-[:USES]->(bash_tool)
            """,
            """
            MATCH (workflow_manager:Agent {id: 'workflow_manager'})
            MATCH (bash_tool:Tool {id: 'bash'})
            MERGE (workflow_manager)-[:USES]->(bash_tool)
            """,
        ]

        try:
            for statement in relationships:
                self.client.execute_write_query(statement)

            logger.info("Created system relationships")
            return True

        except Exception as e:
            logger.error(f"Failed to create system relationships: {e}")
            return False

    def full_schema_setup(self) -> bool:
        """
        Perform complete schema setup.

        Returns:
            True if all setup completed successfully
        """
        logger.info("Starting full schema setup")

        steps = [
            ("constraints", self.create_constraints),
            ("indexes", self.create_indexes),
            ("system nodes", self.create_system_nodes),
            ("system relationships", self.create_system_relationships),
        ]

        for step_name, step_func in steps:
            logger.info(f"Setting up {step_name}...")
            if not step_func():
                logger.error(f"Failed to set up {step_name}")
                return False

        logger.info("Full schema setup completed successfully")
        return True

    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the current schema state.

        Returns:
            Dictionary with validation results
        """
        validation = {"valid": True, "errors": [], "warnings": [], "stats": {}}

        try:
            # Check for required constraints
            constraints_result = self.client.execute_query("SHOW CONSTRAINTS")
            constraint_names = [c.get("name", "") for c in constraints_result]

            required_constraints = [
                "agent_id_unique",
                "tool_id_unique",
                "context_id_unique",
                "workflow_id_unique",
            ]

            missing_constraints = []
            for constraint in required_constraints:
                if not any(constraint in name for name in constraint_names):
                    missing_constraints.append(constraint)

            if missing_constraints:
                validation["errors"].append(
                    f"Missing constraints: {missing_constraints}"
                )
                validation["valid"] = False

            # Check for required indexes
            indexes_result = self.client.execute_query("SHOW INDEXES")
            index_names = [i.get("name", "") for i in indexes_result]

            required_indexes = [
                "agent_name_index",
                "tool_name_index",
                "context_timestamp_index",
            ]

            missing_indexes = []
            for index in required_indexes:
                if not any(index in name for name in index_names):
                    missing_indexes.append(index)

            if missing_indexes:
                validation["warnings"].append(f"Missing indexes: {missing_indexes}")

            # Check for system nodes
            system_agents = self.client.execute_query("""
                MATCH (a:Agent)
                WHERE a.id IN ['system', 'orchestrator', 'workflow_manager']
                RETURN count(a) as count
            """)

            if system_agents[0]["count"] < 3:
                validation["errors"].append("Missing system agents")
                validation["valid"] = False

            # Get statistics
            validation["stats"] = self.client.get_stats()

        except Exception as e:
            validation["errors"].append(f"Validation failed: {e}")
            validation["valid"] = False

        return validation
