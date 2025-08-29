#!/usr/bin/env python3
"""
Integration test for V03Agent event emission through Event Router.
Tests that events are properly emitted, routed, and persisted.
"""

import asyncio
import sys
import os
from datetime import datetime
import aiohttp

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # Add gadugi root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from claude.agents.base.v03_agent import V03Agent
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


async def test_event_emission():
    """Test emitting events through V03Agent to Event Router."""

    print("\n" + "="*60)
    print("🧪 V03AGENT EVENT EMISSION TEST")
    print("="*60 + "\n")

    # Create a test agent instance
    print("📦 Creating test agent instance...")

    # Override event router URL to use port 8001
    @dataclass
    class TestEventConfig:
        enabled: bool = True
        event_router_url: str = "http://localhost:8001"
        timeout_seconds: int = 10
        retry_attempts: int = 3
        batch_size: int = 10
        emit_heartbeat: bool = False
        heartbeat_interval: int = 30
        store_in_memory: bool = False
        graceful_degradation: bool = True

    @dataclass
    class TestCapabilities:
        can_parallelize: bool = True
        can_create_prs: bool = False
        can_write_code: bool = True
        can_review_code: bool = False
        can_test: bool = True
        can_document: bool = True
        expertise_areas: List[str] = None
        max_parallel_tasks: int = 3

        def __post_init__(self):
            if self.expertise_areas is None:
                self.expertise_areas = ["testing", "event-emission"]

    # Create a minimal test agent
    class TestAgent(V03Agent):
        def __init__(self):
            super().__init__(
                agent_id="test-agent-001",
                agent_type="testrunner",
                capabilities=TestCapabilities(),
                event_config=TestEventConfig()
            )

    agent = TestAgent()
    await agent.initialize()

    print(f"✅ Agent initialized: {agent.agent_id}")

    # Test 1: Emit initialization event
    print("\n📋 TEST 1: Agent Initialization Event")
    print("-" * 40)
    success = await agent.emit_initialized(version="v0.3-test")
    print(f"  {'✅' if success else '❌'} emit_initialized: {success}")

    # Test 2: Emit started event (core system event)
    print("\n📋 TEST 2: Agent Started Event")
    print("-" * 40)
    task_id = "test-task-001"
    success = await agent.emit_started(
        input_data={"test": "Run integration tests"},
        task_id=task_id
    )
    print(f"  {'✅' if success else '❌'} emit_started: {success}")

    # Test 3: Emit task started event
    print("\n📋 TEST 3: Task Started Event")
    print("-" * 40)
    success = await agent.emit_task_started(
        task_description="Testing event emission",
        estimated_duration=60,
        dependencies=["event-router", "v03-agent"]
    )
    print(f"  {'✅' if success else '❌'} emit_task_started: {success}")

    # Test 4: Emit hasQuestion event (high priority)
    print("\n📋 TEST 4: Has Question Event (High Priority)")
    print("-" * 40)
    success = await agent.emit_has_question(
        question="Should we proceed with the deployment?",
        context={"environment": "production", "risk": "medium"},
        options=["Yes", "No", "Review changes first"]
    )
    print(f"  {'✅' if success else '❌'} emit_has_question: {success}")

    # Test 5: Emit needsApproval event (high priority)
    print("\n📋 TEST 5: Needs Approval Event (High Priority)")
    print("-" * 40)
    success = await agent.emit_needs_approval(
        command="rm -rf /tmp/test_data",
        description="Clean up test data directory",
        risk_level="low"
    )
    print(f"  {'✅' if success else '❌'} emit_needs_approval: {success}")

    # Test 6: Emit knowledge learned event
    print("\n📋 TEST 6: Knowledge Learned Event")
    print("-" * 40)
    success = await agent.emit_knowledge_learned(
        knowledge_type="event-pattern",
        content="High priority events are routed through orchestration",
        confidence=0.95,
        source="integration-test"
    )
    print(f"  {'✅' if success else '❌'} emit_knowledge_learned: {success}")

    # Test 7: Emit collaboration event
    print("\n📋 TEST 7: Collaboration Event")
    print("-" * 40)
    success = await agent.emit_collaboration(
        message="Test results ready for review",
        message_type="notification",
        recipient_id="orchestration-001",
        requires_response=False
    )
    print(f"  {'✅' if success else '❌'} emit_collaboration: {success}")

    # Test 8: Emit error event (critical priority)
    print("\n📋 TEST 8: Error Event (Critical Priority)")
    print("-" * 40)
    success = await agent.emit_error(
        error_type="TestFailure",
        error_message="Integration test failed: Event routing not working",
        context={"test_id": "test-001", "severity": "high"}
    )
    print(f"  {'✅' if success else '❌'} emit_error: {success}")

    # Test 9: Emit task completed event
    print("\n📋 TEST 9: Task Completed Event")
    print("-" * 40)
    success = await agent.emit_task_completed(
        task_id=task_id,
        task_type="integration-test",
        success=True,
        duration_seconds=2.5,
        artifacts=["test_results.json", "event_log.txt"],
        result="All events successfully emitted"
    )
    print(f"  {'✅' if success else '❌'} emit_task_completed: {success}")

    # Test 10: Emit stopped event (core system event)
    print("\n📋 TEST 10: Agent Stopped Event")
    print("-" * 40)
    success = await agent.emit_stopped(
        output_data={"tests_passed": 10, "tests_failed": 0},
        task_id=task_id,
        success=True,
        duration_seconds=3.0
    )
    print(f"  {'✅' if success else '❌'} emit_stopped: {success}")

    # Clean up
    await agent.cleanup()

    print("\n" + "="*60)
    print("✅ EVENT EMISSION TESTS COMPLETE")
    print("="*60 + "\n")


async def check_event_persistence():
    """Check if events were persisted to storage."""

    print("\n" + "="*60)
    print("🔍 CHECKING EVENT PERSISTENCE")
    print("="*60 + "\n")

    async with aiohttp.ClientSession() as session:
        # Query recent events
        try:
            async with session.get("http://localhost:8001/events/recent?limit=10") as response:
                if response.status == 200:
                    events = await response.json()
                    print(f"📊 Found {len(events)} recent events:")
                    for event in events:
                        print(f"  - {event.get('event_type', 'unknown')}: "
                              f"{event.get('agent_id', 'unknown')} "
                              f"[{event.get('priority', 'normal')}]")
                else:
                    print(f"❌ Failed to query events: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Error querying events: {e}")

        # Check subscription routing
        print("\n🔍 Checking subscription routing...")
        try:
            # Query for a specific event type to see who subscribes
            test_events = [
                "testrunner.hasQuestion",
                "testrunner.needsApproval",
                "testrunner.stopped"
            ]

            for event_type in test_events:
                async with session.post(
                    "http://localhost:8001/events/query",
                    json={"event_type": event_type}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        count = result.get("count", 0)
                        print(f"  {event_type}: {count} events found")
                    else:
                        print(f"  {event_type}: Query failed")
        except Exception as e:
            print(f"❌ Error checking routing: {e}")


async def main():
    """Run all integration tests."""

    # Run event emission tests
    await test_event_emission()

    # Wait a moment for events to be processed
    await asyncio.sleep(1)

    # Check persistence
    await check_event_persistence()

    print("\n🎉 Integration testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
