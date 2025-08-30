#!/usr/bin/env python3
"""Test the actual Flask-based Event Router implementation."""

import time
import requests
import json
from datetime import datetime

# Base URL for the event router
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "event-router"
    print("✅ Health check passed")

def test_root_endpoint():
    """Test the root endpoint."""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "event-router"
    assert "endpoints" in data
    print("✅ Root endpoint passed")

def test_create_event():
    """Test creating an event."""
    print("Testing event creation...")

    event_data = {
        "event_type": "task.started",
        "agent_id": "test-agent-1",
        "task_id": "task-123",
        "priority": "high",
        "payload": {
            "description": "Test task",
            "status": "pending"
        },
        "tags": ["test", "integration"]
    }

    response = requests.post(f"{BASE_URL}/events", json=event_data)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert "event_id" in data
    print(f"✅ Event created with ID: {data['event_id']}")
    return data["event_id"]

def test_list_events():
    """Test listing events."""
    print("Testing event listing...")

    response = requests.get(f"{BASE_URL}/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data
    print(f"✅ Listed {data['count']} events")

def test_filter_events():
    """Test filtering events."""
    print("Testing event filtering...")

    filter_data = {
        "event_types": ["task.started"],
        "priority": "high",
        "limit": 10
    }

    response = requests.post(f"{BASE_URL}/events/filter", json=filter_data)
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "count" in data
    print(f"✅ Filtered {data['count']} events")

def test_storage_info():
    """Test storage info endpoint."""
    print("Testing storage info...")

    response = requests.get(f"{BASE_URL}/events/storage")
    assert response.status_code == 200
    data = response.json()
    assert "total_events" in data
    print(f"✅ Storage info: {data['total_events']} total events")

def test_memory_status():
    """Test memory integration status."""
    print("Testing memory integration status...")

    response = requests.get(f"{BASE_URL}/memory/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
    assert "backend_type" in data
    print(f"✅ Memory status: {data['backend_type']} backend")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Actual Event Router Implementation")
    print("=" * 60)

    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Event Router is not running or not healthy")
            print("Start it with: cd .claude/services/event-router && python3 main.py")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to Event Router at http://localhost:8000")
        print("Start it with: cd .claude/services/event-router && python3 main.py")
        return 1

    # Run tests
    try:
        test_health_check()
        test_root_endpoint()
        event_id = test_create_event()
        test_list_events()
        test_filter_events()
        test_storage_info()
        test_memory_status()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
