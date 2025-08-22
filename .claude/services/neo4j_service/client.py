"""
Neo4j Client with Connection Pooling

Provides a robust client for Neo4j operations with connection pooling,
error handling, and retry logic.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Generator
from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, TransientError

from .models import Neo4jEntityBase


logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails."""


class Neo4jClient:
    """Neo4j client with connection pooling and error handling."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        max_connection_lifetime: int = 1000,
        max_connection_pool_size: int = 100,
        connection_acquisition_timeout: int = 60,
        max_retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (defaults to NEO4J_URI env var or bolt://localhost:7688)
            user: Username for authentication (defaults to NEO4J_USER env var or neo4j)
            password: Password for authentication (defaults to NEO4J_PASSWORD env var)
            max_connection_lifetime: Max lifetime for connections in seconds
            max_connection_pool_size: Max number of connections in pool
            connection_acquisition_timeout: Timeout for acquiring connection
            max_retry_attempts: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        # Use environment variables with fallbacks for development
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7688")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")

        if not self.password:
            raise ValueError(
                "Neo4j password not provided. Set NEO4J_PASSWORD environment variable "
                "or pass password parameter."
            )
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay

        # Initialize driver with connection pooling
        self.driver: Optional[Driver] = None
        self._driver_config = {
            "max_connection_lifetime": max_connection_lifetime,
            "max_connection_pool_size": max_connection_pool_size,
            "connection_acquisition_timeout": connection_acquisition_timeout,
        }

        logger.info(f"Initialized Neo4j client for {uri}")

    def connect(self) -> Driver:
        """
        Establish connection to Neo4j with retry logic.

        Returns:
            Neo4j driver instance

        Raises:
            Neo4jConnectionError: If connection fails after all retries
        """
        if self.driver is not None:
            return self.driver

        last_error = None
        for attempt in range(self.max_retry_attempts):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri, auth=(self.user, self.password), **self._driver_config
                )

                # Test the connection
                with self.driver.session() as session:
                    session.run("RETURN 1").consume()

                logger.info(f"Successfully connected to Neo4j at {self.uri}")
                return self.driver

            except (ServiceUnavailable, AuthError, TransientError) as e:
                last_error = e
                if attempt < self.max_retry_attempts - 1:
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All connection attempts failed: {e}")

        raise Neo4jConnectionError(
            f"Failed to connect to Neo4j after {self.max_retry_attempts} attempts: {last_error}"
        )

    def disconnect(self) -> None:
        """Close the Neo4j driver connection."""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            logger.info("Disconnected from Neo4j")

    @contextmanager
    def session(self, **kwargs) -> Generator[Session, None, None]:
        """
        Context manager for Neo4j sessions.

        Args:
            **kwargs: Additional session parameters

        Yields:
            Neo4j session instance
        """
        driver = self.connect()
        session = driver.session(**kwargs)
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def transaction(self, **kwargs) -> Generator[Transaction, None, None]:
        """
        Context manager for Neo4j transactions.

        Args:
            **kwargs: Additional session parameters

        Yields:
            Neo4j transaction instance
        """
        with self.session(**kwargs) as session:
            tx = session.begin_transaction()
            try:
                yield tx
                tx.commit()
            except Exception:
                tx.rollback()
                raise

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        retries: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query with retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters
            retries: Number of retries (defaults to client's max_retry_attempts)

        Returns:
            List of result records as dictionaries

        Raises:
            Neo4jConnectionError: If query execution fails
        """
        if parameters is None:
            parameters = {}

        if retries is None:
            retries = self.max_retry_attempts

        last_error = None
        for attempt in range(retries):
            try:
                with self.session() as session:
                    result = session.run(query, parameters)
                    return [record.data() for record in result]

            except TransientError as e:
                last_error = e
                if attempt < retries - 1:
                    logger.warning(
                        f"Query attempt {attempt + 1} failed: {e}. Retrying..."
                    )
                    time.sleep(0.5 * (2**attempt))  # Exponential backoff
                else:
                    logger.error(f"Query failed after {retries} attempts: {e}")

            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise Neo4jConnectionError(f"Query execution failed: {e}")

        raise Neo4jConnectionError(
            f"Query failed after {retries} attempts: {last_error}"
        )

    def execute_write_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query in a write transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        if parameters is None:
            parameters = {}

        with self.session() as session:
            with session.begin_transaction() as tx:
                result = tx.run(query, parameters)
                return [record.data() for record in result]

    def health_check(self) -> bool:
        """
        Check if Neo4j is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            with self.session() as session:
                result = session.run("RETURN 1 as health_check")
                record = result.single()
                return record["health_check"] == 1 if record else False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.session() as session:
                # Get node counts by label
                node_counts = {}
                labels_result = session.run("CALL db.labels()")
                for record in labels_result:
                    label = record["label"]
                    count_result = session.run(
                        f"MATCH (n:{label}) RETURN count(n) as count"
                    )
                    count_record = count_result.single()
                    node_counts[label] = count_record["count"] if count_record else 0

                # Get relationship counts
                rel_counts = {}
                rel_types_result = session.run("CALL db.relationshipTypes()")
                for record in rel_types_result:
                    rel_type = record["relationshipType"]
                    count_result = session.run(
                        f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                    )
                    count_record = count_result.single()
                    rel_counts[rel_type] = count_record["count"] if count_record else 0

                # Get constraints and indexes
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = [record.data() for record in constraints_result]

                indexes_result = session.run("SHOW INDEXES")
                indexes = [record.data() for record in indexes_result]

                return {
                    "node_counts": node_counts,
                    "relationship_counts": rel_counts,
                    "constraints": len(constraints),
                    "indexes": len(indexes),
                    "constraint_details": constraints,
                    "index_details": indexes,
                }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    # CRUD Operations for entities
    def create_entity(self, entity: Neo4jEntityBase) -> Dict[str, Any]:
        """
        Create an entity in Neo4j.

        Args:
            entity: Entity to create

        Returns:
            Created entity data
        """
        return entity.create(self)

    def read_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Read an entity from Neo4j.

        Args:
            entity_type: Type of entity (label)
            entity_id: Entity ID

        Returns:
            Entity data or None if not found
        """
        query = f"MATCH (n:{entity_type} {{id: $id}}) RETURN n"
        results = self.execute_query(query, {"id": entity_id})
        return results[0]["n"] if results else None

    def update_entity(
        self, entity_type: str, entity_id: str, updates: Dict[str, Any]
    ) -> bool:
        """
        Update an entity in Neo4j.

        Args:
            entity_type: Type of entity (label)
            entity_id: Entity ID
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise
        """
        # Build SET clause dynamically
        set_clauses = [f"n.{key} = ${key}" for key in updates.keys()]
        set_clause = ", ".join(set_clauses)

        query = f"""
        MATCH (n:{entity_type} {{id: $id}})
        SET {set_clause}, n.updated = datetime()
        RETURN count(n) as updated_count
        """

        parameters = {"id": entity_id, **updates}
        results = self.execute_write_query(query, parameters)
        return results[0]["updated_count"] > 0 if results else False

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Delete an entity from Neo4j.

        Args:
            entity_type: Type of entity (label)
            entity_id: Entity ID

        Returns:
            True if deletion succeeded, False otherwise
        """
        query = f"""
        MATCH (n:{entity_type} {{id: $id}})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """

        results = self.execute_write_query(query, {"id": entity_id})
        return results[0]["deleted_count"] > 0 if results else False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
