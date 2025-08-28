"""
Tests for event-router service.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Any, Dict

# Import based on available framework
try:
    from fastapi.testclient import TestClient  # type: ignore[import-untyped]
    use_fastapi = True
except ImportError:
    use_fastapi = False
    TestClient = None  # type: ignore[misc]

if not use_fastapi:
    # Flask imports
    try:
        from flask.testing import FlaskClient  # type: ignore[import-untyped]
        from ..main import app as flask_app
    except ImportError:
        # If Flask is not available, we'll handle this in fixtures
        FlaskClient = None  # type: ignore[misc]
        flask_app = None  # type: ignore[misc]

from ..models import RequestModel


@pytest.fixture
def client() -> Any:
    """Create test client."""
    if use_fastapi and TestClient is not None:
        try:
            from ..main import app
            if app is not None:
                return TestClient(app)
            else:
                pytest.skip("FastAPI app not available")
        except ImportError:
            pytest.skip("FastAPI not available")
    else:
        if flask_app is not None:
            flask_app.testing = True
            return flask_app.test_client()
        else:
            pytest.skip("Flask not available")


@pytest.fixture
def sample_request() -> RequestModel:
    """Create sample request."""
    return RequestModel(
        id="test-123",
        data={"test": "data"},
        metadata={"source": "test"}
    )


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self, client: Any) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore
        
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client: Any) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore
        
        assert data["service"] == "event-router"
        assert data["status"] == "running"


class TestProcessEndpoint:
    """Test process endpoint."""

    def test_process_valid_request(self, client: Any, sample_request: RequestModel) -> None:
        """Test processing valid request."""
        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 200
        
        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore
        
        assert data["success"] is True
        assert "data" in data

    def test_process_invalid_request(self, client: Any) -> None:
        """Test processing invalid request."""
        response = client.post(
            "/process",
            json={}
        )
        # FastAPI returns 422 for validation errors, Flask returns 400
        assert response.status_code in [400, 422]

    def test_process_empty_data(self, client: Any) -> None:
        """Test processing with empty data."""
        response = client.post(
            "/process",
            json={"data": {}}
        )
        # Should still work with empty data dict
        assert response.status_code == 200


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status(self, client: Any) -> None:
        """Test status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200
        
        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore
        
        assert data["service"] == "event-router"
        assert data["status"] == "operational"


class TestErrorHandling:
    """Test error handling."""

    @patch(".claude.services.event-router.main.process_request")
    def test_process_error_handling(
        self, 
        mock_process: MagicMock, 
        client: Any, 
        sample_request: RequestModel
    ) -> None:
        """Test error handling in process endpoint."""
        mock_process.side_effect = Exception("Test error")

        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 500
        
        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore
        
        assert "error" in data