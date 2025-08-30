#!/usr/bin/env python3
"""
Test script for V03Agent event publishing capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import v03_agent
sys.path.insert(0, str(Path(__file__).parent))

from v03_agent import V03Agent, AgentCapabilities, EventConfiguration, TaskOutcome


class TestAgent(V03Agent):
    """Test agent implementation."""

    def __init__(self):
        capabilities = AgentCapabilities(
            can_write_code=True,
            can_test=True,
            expertise_areas=["testing", "event_publishing"],
        )

        # Configure events with graceful degradation
        event_config = EventConfiguration(
            enabled=True,
            event_router_url="http://localhost:8000",
            timeout_seconds=2,
            graceful_degradation=True,
            emit_heartbeat=False,  # Disable for testing
        )

        super().__init__(
            agent_id="test-agent-001",
            agent_type="test-agent",
            capabilities=capabilities,
            event_config=event_config,
        )

    async def execute_task(self, task):
        """Simple test task implementation."""
        print(f"  🔧 Executing test task: {task.get('description', 'Unknown task')}")
        await asyncio.sleep(0.1)  # Simulate work

        return TaskOutcome(
            success=True,
            task_id=self.current_task_id or "test-task",
            task_type="test",
            steps_taken=["Step 1: Analyze", "Step 2: Execute", "Step 3: Verify"],
            duration_seconds=0.1,
            lessons_learned="Test completed successfully",
        )


async def test_event_publishing():
    """Test the event publishing functionality."""
    print("\n" + "=" * 60)
    print("Testing V03Agent Event Publishing")
    print("=" * 60)

    agent = TestAgent()

    try:
        print("\n1. Initializing agent...")
        await agent.initialize(mcp_url="http://localhost:8000")

        print("\n2. Testing task lifecycle events...")
        task_id = await agent.start_task("Test event publishing functionality")

        # Execute a test task
        outcome = await agent.execute_task(
            {
                "description": "Test event publishing functionality",
                "type": "integration_test",
            }
        )

        # Learn from the outcome
        await agent.learn_from_outcome(outcome)

        print("\n3. Testing knowledge learning event...")
        await agent.emit_knowledge_learned(
            knowledge_type="pattern",
            content="Event publishing works correctly with graceful degradation",
            confidence=0.9,
            source="integration_test",
        )

        print("\n4. Testing collaboration event...")
        await agent.emit_collaboration(
            message="Event publishing test completed successfully",
            message_type="status_update",
            decision="Proceed with deployment",
        )

        print("\n5. Testing error event...")
        await agent.emit_error(
            error_type="test_error",
            error_message="This is a test error for validation",
            context={"test_case": "error_emission", "expected": True},
        )

        print("\n6. Testing batch flush...")
        flushed_count = await agent.flush_event_batch()
        print(f"  📤 Flushed {flushed_count} batched events")

        print("\n✅ All event publishing tests completed!")

        # Print event publishing status
        if agent._event_publishing_enabled:
            print("  🟢 Event publishing: ENABLED")
            print(f"  📡 Event router: {agent.event_config.event_router_url}")
            print(f"  📦 Batched events: {len(agent._event_batch)}")
        else:
            print("  🟡 Event publishing: DISABLED (graceful degradation)")
            print(f"  📦 Batched events: {len(agent._event_batch)}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n7. Shutting down agent...")
        await agent.shutdown()


async def test_without_event_router():
    """Test graceful degradation when event router is unavailable."""
    print("\n" + "=" * 60)
    print("Testing Graceful Degradation (No Event Router)")
    print("=" * 60)

    # Configure with a non-existent event router
    event_config = EventConfiguration(
        enabled=True,
        event_router_url="http://localhost:9999",  # Non-existent port
        timeout_seconds=1,
        graceful_degradation=True,
    )

    capabilities = AgentCapabilities(expertise_areas=["resilience_testing"])

    agent = V03Agent(
        agent_id="resilience-test-agent",
        agent_type="resilience-test",
        capabilities=capabilities,
        event_config=event_config,
    )

    try:
        print("\n1. Initializing agent with unavailable event router...")
        await agent.initialize()

        print("\n2. Testing operations with degraded event system...")
        task_id = await agent.start_task("Test resilience without event router")

        # These should all work despite event router being unavailable
        await agent.emit_knowledge_learned(
            "resilience", "System continues to work", 0.8
        )
        await agent.emit_collaboration("Still collaborating despite events being down")

        print(f"\n  📦 Batched events (should have some): {len(agent._event_batch)}")
        print(f"  🟡 Event publishing enabled: {agent._event_publishing_enabled}")

        print("\n✅ Graceful degradation test completed!")

    except Exception as e:
        print(f"\n❌ Graceful degradation test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await agent.shutdown()


async def main():
    """Run all tests."""
    try:
        await test_event_publishing()
        await test_without_event_router()

        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
