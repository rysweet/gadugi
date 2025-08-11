#!/usr/bin/env python3
"""
Test suite for MCP Service
"""

import asyncio
import httpx
import pytest
from  import


BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "neo4j_connected" in data
        assert "timestamp" in data
        assert "version" in data


@pytest.mark.asyncio
async def test_store_context():
    """Test storing a context"""
    async with httpx.AsyncClient() as client:
        context_data = {
            "content": "Test context for Gadugi MCP Service",
            "source": "test_suite",
            "metadata": {"test": True, "version": "0.3.0"},
            "tags": ["test", "mcp", "gadugi"]
        }

        response = await client.post(f"{BASE_URL}/context/store", json=context_data)
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["content"] == context_data["content"]
        assert data["source"] == context_data["source"]
        assert data["tags"] == context_data["tags"]

        return data["id"]  # Return for use in other tests


@pytest.mark.asyncio
async def test_retrieve_context():
    """Test retrieving a context by ID"""
    async with httpx.AsyncClient() as client:
        # First store a context
        context_data = {
            "content": "Context to retrieve",
            "source": "test_suite",
            "tags": ["retrieve", "test"]
        }

        store_response = await client.post(f"{BASE_URL}/context/store", json=context_data)
        context_id = store_response.json()["id"]

        # Now retrieve it
        response = await client.get(f"{BASE_URL}/context/retrieve/{context_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == context_id
        assert data["content"] == context_data["content"]
        assert data["source"] == context_data["source"]


@pytest.mark.asyncio
async def test_search_contexts():
    """Test searching contexts"""
    async with httpx.AsyncClient() as client:
        # Store some test contexts
        for i in range(3):
            await client.post(f"{BASE_URL}/context/store", json={
                "content": f"Searchable context {i}",
                "source": "search_test",
                "tags": ["search", f"item-{i}"]
            })

        # Search for them
        search_request = {
            "query": "Searchable",
            "source": "search_test",
            "limit": 10
        }

        response = await client.post(f"{BASE_URL}/context/search", json=search_request)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3
        assert all("Searchable" in ctx["content"] for ctx in data)


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test metrics endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        data = response.json()

        assert "total_contexts" in data
        assert "total_agents" in data
        assert "total_relationships" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "Gadugi MCP Service"
        assert data["status"] == "running"
        assert "endpoints" in data


@pytest.mark.asyncio
async def test_404_context():
    """Test retrieving non-existent context"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/context/retrieve/non-existent-id")
        assert response.status_code == 404


def test_mcp_service_integration():
    """Run all integration tests"""
    print("\n🧪 Running MCP Service Integration Tests\n")

    # Run async tests
    loop = asyncio.get_event_loop()

    tests = [
        ("Health Check", test_health_endpoint()),
        ("Store Context", test_store_context()),
        ("Retrieve Context", test_retrieve_context()),
        ("Search Contexts", test_search_contexts()),
        ("Metrics", test_metrics_endpoint()),
        ("Root Endpoint", test_root_endpoint()),
        ("404 Test", test_404_context()),
    ]

    for test_name, test_coro in tests:
        try:
            loop.run_until_complete(test_coro)
            print(f"✅ {test_name} passed")
        except AssertionError as e:
            print(f"❌ {test_name} failed: {e}")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")

    print("\n✅ MCP Service tests completed!\n")


if __name__ == "__main__":
    # For standalone testing
    test_mcp_service_integration()
