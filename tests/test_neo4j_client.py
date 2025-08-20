"""Tests for Neo4j client with environment variables."""

import os
import pytest
from unittest.mock import patch, MagicMock

from neo4j_client import Neo4jClient


class TestNeo4jClient:
    """Test Neo4j client environment variable handling."""

    def test_client_uses_environment_variables(self):
        """Test that client reads from environment variables."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_URI": "bolt://test:7687",
                "NEO4J_USER": "testuser",
                "NEO4J_PASSWORD": "testpass",  # pragma: allowlist secret
            },
        ):
            client = Neo4jClient()
            assert client.uri == "bolt://test:7687"
            assert client.user == "testuser"
            assert client.password == "testpass"  # pragma: allowlist secret

    def test_client_uses_defaults_when_no_env(self):
        """Test that client uses sensible defaults in development."""
        with patch.dict(os.environ, {}, clear=True):
            client = Neo4jClient()
            assert client.uri == "bolt://localhost:7688"
            assert client.user == "neo4j"
            # In development mode, should use fallback password
            assert (
                client.password
                == "development-only-password"  # pragma: allowlist secret
            )

    def test_client_requires_password_in_production(self):
        """Test that password is required in production environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            with pytest.raises(
                ValueError, match="NEO4J_PASSWORD.*required.*production"
            ):
                Neo4jClient()

    def test_client_from_environment(self):
        """Test creating client from environment variables."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_URI": "bolt://envtest:7687",
                "NEO4J_USER": "envuser",
                "NEO4J_PASSWORD": "envpass",  # pragma: allowlist secret
            },
        ):
            client = Neo4jClient.from_environment()
            assert client.uri == "bolt://envtest:7687"
            assert client.user == "envuser"
            assert client.password == "envpass"  # pragma: allowlist secret

    def test_client_override_env_with_params(self):
        """Test that constructor parameters override environment variables."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_URI": "bolt://env:7687",
                "NEO4J_USER": "envuser",
                "NEO4J_PASSWORD": "envpass",  # pragma: allowlist secret
            },
        ):
            client = Neo4jClient(
                uri="bolt://param:7687",
                user="paramuser",
                password="parampass",  # pragma: allowlist secret
            )
            assert client.uri == "bolt://param:7687"
            assert client.user == "paramuser"
            assert client.password == "parampass"  # pragma: allowlist secret

    @patch("neo4j_client.client.GraphDatabase")
    def test_connect_with_env_credentials(self, mock_graph_db):
        """Test that connection uses environment credentials."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        with patch.dict(
            os.environ,
            {
                "NEO4J_URI": "bolt://test:7687",
                "NEO4J_USER": "testuser",
                "NEO4J_PASSWORD": "testpass",  # pragma: allowlist secret
            },
        ):
            client = Neo4jClient()
            result = client.connect()

            # Verify GraphDatabase.driver was called with env values
            mock_graph_db.driver.assert_called_once()
            call_args = mock_graph_db.driver.call_args
            assert call_args[0][0] == "bolt://test:7687"

            assert result is True
