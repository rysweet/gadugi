"""
Tests for event-router service.
"""

import pytest
<<<<<<< HEAD
from unittest.mock import patch

from ..main import app
from ..models import RequestModel
=======
from fastapi.testclient import TestClient
from unittest.mock import patch

from ..main import app
>>>>>>> feature/gadugi-v0.3-regeneration


@pytest.fixture
def client():
    """Create test client."""
<<<<<<< HEAD
    return app.test_client()
=======
    return TestClient(app)
>>>>>>> feature/gadugi-v0.3-regeneration


@pytest.fixture
def sample_request():
    """Create sample request."""
    return RequestModel(
        id="test-123",
        data={"test": "data"},
        metadata={"source": "test"}
    )


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
<<<<<<< HEAD
        assert response.get_json()["status"] == "healthy"
=======
        assert response.json()["status"] == "healthy"
>>>>>>> feature/gadugi-v0.3-regeneration


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
<<<<<<< HEAD
        data = response.get_json()
=======
        data = response.json()
>>>>>>> feature/gadugi-v0.3-regeneration
        assert data["service"] == "event-router"
        assert data["status"] == "running"


class TestProcessEndpoint:
    """Test process endpoint."""

    def test_process_valid_request(self, client, sample_request):
        """Test processing valid request."""
        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 200
<<<<<<< HEAD
        data = response.get_json()
=======
        data = response.json()
>>>>>>> feature/gadugi-v0.3-regeneration
        assert data["success"] is True
        assert "data" in data

    def test_process_invalid_request(self, client):
        """Test processing invalid request."""
        response = client.post(
            "/process",
            json={}
        )
<<<<<<< HEAD
        assert response.status_code == 400  # Validation error
=======
        assert response.status_code == 422  # Validation error
>>>>>>> feature/gadugi-v0.3-regeneration

    def test_process_empty_data(self, client):
        """Test processing with empty data."""
        response = client.post(
            "/process",
            json={"data": {}}
        )
        # Should still work with empty data dict
        assert response.status_code == 200


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status(self, client):
        """Test status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200
<<<<<<< HEAD
        data = response.get_json()
=======
        data = response.json()
>>>>>>> feature/gadugi-v0.3-regeneration
        assert data["service"] == "event-router"
        assert data["status"] == "operational"


class TestErrorHandling:
    """Test error handling."""

    @patch("main.process_request")
    def test_process_error_handling(self, mock_process, client, sample_request):
        """Test error handling in process endpoint."""
        mock_process.side_effect = Exception("Test error")

        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 500
<<<<<<< HEAD
        assert "error" in response.get_json()
=======
        assert "error" in response.json()
>>>>>>> feature/gadugi-v0.3-regeneration
