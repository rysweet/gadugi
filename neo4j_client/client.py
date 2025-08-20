#!/usr/bin/env python3
"""
Neo4j client for Gadugi with environment-based configuration.
"""

import os
import sys
from typing import Dict, List, Optional

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable, AuthError


class Neo4jClient:
    """Manages Neo4j database connection with environment-based configuration."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j client with environment variables or provided values.

        Args:
            uri: Neo4j connection URI (defaults to env var NEO4J_URI or bolt://localhost:7688)
            user: Neo4j username (defaults to env var NEO4J_USER or 'neo4j')
            password: Neo4j password (defaults to env var NEO4J_PASSWORD, required in production)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7688")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")

        # Password handling - required in production, optional in development
        self.password = password or os.getenv("NEO4J_PASSWORD")
        if not self.password:
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError(
                    "NEO4J_PASSWORD environment variable is required in production"
                )
            else:
                # Development fallback - should be removed in production deployments
                print(
                    "WARNING: Using default password for development. Set NEO4J_PASSWORD for production."
                )
                self.password = "development-only-password"  # pragma: allowlist secret

        self.driver = None

    def connect(self) -> bool:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=basic_auth(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            print(f"Connected to Neo4j at {self.uri}")
            return True
        except ServiceUnavailable:
            print(f"Neo4j is not available at {self.uri}")
            print("Please ensure Neo4j is running: docker-compose up -d neo4j")
            return False
        except AuthError:
            print(f"Authentication failed for user {self.user}")
            print("Check your NEO4J_PASSWORD environment variable")
            return False
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def execute_query(
        self, query: str, parameters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters dictionary

        Returns:
            List of result dictionaries
        """
        if not self.driver:
            raise RuntimeError("Not connected to database")

        results = []
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            for record in result:
                results.append(dict(record))

        return results

    def test_connection(self) -> bool:
        """Test database connection and basic functionality."""
        try:
            result = self.execute_query("RETURN 1 AS test")
            return len(result) == 1 and result[0]["test"] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    @classmethod
    def from_environment(cls) -> "Neo4jClient":
        """Create a Neo4j client using only environment variables."""
        return cls()


def main():
    """Example usage of Neo4j client."""
    # Create client from environment variables
    client = Neo4jClient.from_environment()

    if not client.connect():
        print("Failed to connect to Neo4j")
        return 1

    # Test connection
    if client.test_connection():
        print("Neo4j connection test successful!")
    else:
        print("Neo4j connection test failed!")
        return 1

    # Close connection
    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
