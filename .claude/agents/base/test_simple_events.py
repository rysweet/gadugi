#!/usr/bin/env python3
"""
Simple test for V03Agent event publishing without external dependencies.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the memory integration to avoid dependency issues
sys.modules['shared.memory_integration'] = MagicMock()


class MockMemoryInterface:
    """Mock memory interface for testing."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def remember_short_term(self, content, tags=None):
        print(f"    Memory: {content} (tags: {tags})")

    async def remember_long_term(self, content, tags=None, importance=0.5):
        print(f"    Long-term memory: {content} (importance: {importance})")

    async def start_task(self, description):
        print(f"    Task started in memory: {description}")

    async def recall_memories(self, limit=10, memory_types=None):
        return []

    async def write_to_whiteboard(self, key, value):
        print(f"    Whiteboard: {key} = {value}")

    async def store_procedure(self, procedure_name, steps, context):
        print(f"    Procedure stored: {procedure_name}")
        return f"proc_{hash(procedure_name) % 1000:03d}"


# Patch the memory integration
from v03_agent import V03Agent, AgentCapabilities, EventConfiguration, TaskOutcome

# Override the memory interface creation
original_init = V03Agent.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)

def patched_initialize(self, mcp_url=None):
    """Initialize without external dependencies."""
    print(f"🚀 Initializing {self.agent_type} agent: {self.agent_id}")

    # Use mock memory interface
    self.memory = MockMemoryInterface()

    # Initialize event system (this is what we want to test)
    return self._initialize_event_system_and_setup()

async def _initialize_event_system_and_setup(self):
    """Setup without memory system dependencies."""
    await self.memory.__aenter__()

    # Initialize event publishing
    await self._initialize_event_system()

    self.knowledge_loaded = True

    # Store initialization
    await self.memory.remember_short_term(
        f"Agent {self.agent_id} initialized",
        tags=["initialization", self.agent_type]
    )

    # Emit initialization event
    await self.emit_initialized()

    print(f"✅ {self.agent_type} agent ready with event publishing")

# Patch methods
V03Agent.initialize = patched_initialize
V03Agent._initialize_event_system_and_setup = _initialize_event_system_and_setup  # type: ignore[attr-defined]


class TestAgent(V03Agent):
    """Test agent implementation."""

    def __init__(self):
        capabilities = AgentCapabilities(
            can_write_code=True,
            can_test=True,
            expertise_areas=["testing", "event_publishing"]
        )

        # Configure events for testing
        event_config = EventConfiguration(
            enabled=True,
            event_router_url="http://localhost:8000",
            timeout_seconds=2,
            graceful_degradation=True,
            emit_heartbeat=False  # Disable for testing
        )

        super().__init__(
            agent_id="test-agent-001",
            agent_type="test-agent",
            capabilities=capabilities,
            event_config=event_config
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
            lessons_learned="Test completed successfully"
        )


async def test_event_system():
    """Test the core event system functionality."""
    print("\n" + "="*60)
    print("Testing V03Agent Event System (Simplified)")
    print("="*60)

    agent = TestAgent()

    try:
        print("\n1. Initializing agent...")
        await agent.initialize()

        print(f"\n   Event system status:")
        print(f"   - Enabled: {agent.event_config.enabled}")
        print(f"   - Publishing: {agent._event_publishing_enabled}")
        print(f"   - Router URL: {agent.event_config.event_router_url}")
        print(f"   - Graceful degradation: {agent.event_config.graceful_degradation}")

        print("\n2. Testing event emission methods...")

        # Test task events
        task_id = await agent.start_task("Test event publishing functionality")
        print(f"   - Task started: {task_id}")

        # Test knowledge learning
        result = await agent.emit_knowledge_learned(
            knowledge_type="pattern",
            content="Event system works with graceful degradation",
            confidence=0.9
        )
        print(f"   - Knowledge event emitted: {result}")

        # Test collaboration
        result = await agent.emit_collaboration(
            message="Testing collaboration events",
            message_type="status_update"
        )
        print(f"   - Collaboration event emitted: {result}")

        # Test error event
        result = await agent.emit_error(
            error_type="test_error",
            error_message="This is a test error"
        )
        print(f"   - Error event emitted: {result}")

        print("\n3. Testing batch operations...")
        batch_count = len(agent._event_batch)
        print(f"   - Batched events: {batch_count}")

        if batch_count > 0:
            flushed = await agent.flush_event_batch()
            print(f"   - Flushed events: {flushed}")

        print("\n4. Testing task completion...")
        outcome = await agent.execute_task({
            "description": "Test task with events",
            "type": "integration_test"
        })

        await agent.learn_from_outcome(outcome)

        print("\n✅ Event system test completed successfully!")

        # Show final statistics
        print(f"\n   Final statistics:")
        print(f"   - Event publishing enabled: {agent._event_publishing_enabled}")
        print(f"   - HTTP session active: {agent._event_session is not None}")
        print(f"   - Remaining batched events: {len(agent._event_batch)}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n5. Shutting down agent...")
        await agent.shutdown()
        print("   Agent shutdown complete!")


async def main():
    """Run the simplified test."""
    try:
        await test_event_system()
        print("\n" + "="*60)
        print("🎉 Event system test completed!")
        print("="*60)

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
