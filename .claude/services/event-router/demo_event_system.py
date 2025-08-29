#!/usr/bin/env python3
"""
Demonstration script for the enhanced Event Router with memory integration.
Shows agent lifecycle event tracking, persistence, filtering, and replay capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List

from models import (
    AgentEvent, EventType, EventPriority,
    AgentInitializedEvent, TaskStartedEvent, TaskCompletedEvent,
    KnowledgeLearnedEvent, CollaborationMessageEvent,
    EventFilter, EventReplayRequest
)
from handlers import (
    MemoryEventStorage, EventHandler, EventFilterEngine,
    EventReplayEngine
)
from config import get_settings


async def demonstrate_event_system():
    """Demonstrate the complete event system functionality."""

    print("🚀 Event Router Memory Integration Demo")
    print("=" * 50)

    # Initialize settings and components
    settings = get_settings()
    print(f"📋 Configuration:")
    print(f"  - Memory Backend: {settings.memory_backend_url}")
    print(f"  - SQLite Path: {settings.sqlite_db_path}")
    print(f"  - Memory Integration: {settings.enable_memory_integration}")
    print()

    try:
        # Initialize the event system
        print("⚙️ Initializing Event System...")

        memory_storage = MemoryEventStorage(
            memory_backend_url=settings.memory_backend_url,
            sqlite_db_path=settings.sqlite_db_path
        )
        await memory_storage.initialize()
        print("✅ Memory storage initialized")

        filter_engine = EventFilterEngine()
        print("✅ Filter engine initialized")

        replay_engine = EventReplayEngine(memory_storage)
        print("✅ Replay engine initialized")

        event_handler = EventHandler(memory_storage, filter_engine)
        await event_handler.initialize()
        print("✅ Event handler initialized")

        print()

        # Demonstrate agent lifecycle events
        await demonstrate_agent_lifecycle(event_handler)

        # Demonstrate event filtering
        await demonstrate_event_filtering(filter_engine, memory_storage)

        # Demonstrate event replay
        await demonstrate_event_replay(replay_engine, memory_storage)

        # Show storage statistics
        await show_storage_statistics(memory_storage)

        print("\n🎉 Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        raise


async def demonstrate_agent_lifecycle(event_handler: EventHandler):
    """Demonstrate agent lifecycle event tracking."""
    print("🤖 Agent Lifecycle Event Demonstration")
    print("-" * 40)

    session_id = f"demo_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # 1. Agent Initialization
    print("1️⃣ Agent Initialization...")
    init_event = AgentInitializedEvent(
        agent_id="TaskDecomposer_001",
        agent_type="TaskDecomposer",
        version="1.0.0",
        session_id=session_id,
        capabilities=["task_breakdown", "dependency_analysis", "estimation"],
        priority=EventPriority.HIGH
    )

    result = await event_handler.handle_event(init_event)
    print(f"   ✅ Agent initialized - Event ID: {result['event_id']}")
    print(f"   📝 Stored in memory: {result['stored_in_memory']}")

    # 2. Task Started
    print("\n2️⃣ Task Started...")
    task_event = TaskStartedEvent(
        agent_id="TaskDecomposer_001",
        task_id="task_feature_x_001",
        task_description="Implement user authentication system",
        estimated_duration=120,
        dependencies=["task_database_setup"],
        session_id=session_id,
        project_id="gadugi_v03",
        tags=["authentication", "security", "backend"]
    )

    result = await event_handler.handle_event(task_event)
    print(f"   ✅ Task started - Event ID: {result['event_id']}")

    # 3. Knowledge Learned
    print("\n3️⃣ Knowledge Learned...")
    knowledge_event = KnowledgeLearnedEvent(
        agent_id="TaskDecomposer_001",
        knowledge_type="pattern",
        content="JWT tokens should always be validated server-side to prevent security vulnerabilities",
        confidence=0.95,
        source="security_analysis",
        session_id=session_id,
        task_id="task_feature_x_001",
        tags=["security", "jwt", "validation"],
        priority=EventPriority.HIGH
    )

    result = await event_handler.handle_event(knowledge_event)
    print(f"   ✅ Knowledge learned - Event ID: {result['event_id']}")
    print(f"   🧠 Confidence: {knowledge_event.confidence}")

    # 4. Collaboration Message
    print("\n4️⃣ Inter-Agent Collaboration...")
    collab_event = CollaborationMessageEvent(
        agent_id="TaskDecomposer_001",
        recipient_id="CodeWriter_001",
        message_type="request",
        content="Please implement JWT validation middleware based on learned security pattern",
        requires_response=True,
        session_id=session_id,
        task_id="task_feature_x_001",
        tags=["collaboration", "security", "implementation"]
    )

    result = await event_handler.handle_event(collab_event)
    print(f"   ✅ Collaboration message sent - Event ID: {result['event_id']}")

    # 5. Task Completed
    print("\n5️⃣ Task Completed...")
    completion_event = TaskCompletedEvent(
        agent_id="TaskDecomposer_001",
        task_id="task_feature_x_001",
        result="Successfully decomposed authentication system into 5 subtasks with security patterns identified",
        duration=95,  # minutes
        artifacts=["task_breakdown.json", "security_requirements.md", "implementation_plan.md"],
        session_id=session_id,
        success_metrics={
            "subtasks_created": 5,
            "dependencies_mapped": 3,
            "security_patterns_identified": 2,
            "estimated_vs_actual_duration": 0.79  # 95/120
        },
        tags=["completion", "authentication", "decomposition"],
        priority=EventPriority.NORMAL
    )

    result = await event_handler.handle_event(completion_event)
    print(f"   ✅ Task completed - Event ID: {result['event_id']}")
    print(f"   ⏱️  Duration: {completion_event.duration} minutes")
    print(f"   📊 Success metrics: {len(completion_event.success_metrics)} recorded")

    print(f"\n📋 Session ID for replay: {session_id}")
    return session_id


async def demonstrate_event_filtering(filter_engine: EventFilterEngine, storage: MemoryEventStorage):
    """Demonstrate advanced event filtering capabilities."""
    print("\n🔍 Event Filtering Demonstration")
    print("-" * 40)

    # 1. Filter by event type
    print("1️⃣ Filter by Event Type (Task Events)...")
    task_filter = EventFilter(
        event_types=[EventType.TASK_STARTED, EventType.TASK_COMPLETED],
        limit=10
    )

    task_events = await filter_engine.filter_events(storage, task_filter)
    print(f"   📊 Found {len(task_events)} task-related events")

    # 2. Filter by priority
    print("\n2️⃣ Filter by Priority (High Priority Events)...")
    priority_filter = EventFilter(
        priority=EventPriority.HIGH,
        limit=10
    )

    high_priority_events = await filter_engine.filter_events(storage, priority_filter)
    print(f"   🚨 Found {len(high_priority_events)} high priority events")

    # 3. Filter by tags
    print("\n3️⃣ Filter by Tags (Security-related)...")
    tag_filter = EventFilter(
        tags=["security"],
        limit=20
    )

    security_events = await filter_engine.filter_events(storage, tag_filter)
    print(f"   🔐 Found {len(security_events)} security-related events")

    # 4. Time-based filter
    print("\n4️⃣ Filter by Time (Last Hour)...")
    time_filter = EventFilter(
        start_time=datetime.utcnow() - timedelta(hours=1),
        limit=50
    )

    recent_events = await filter_engine.filter_events(storage, time_filter)
    print(f"   ⏰ Found {len(recent_events)} events from the last hour")

    # Show sample event details
    if recent_events:
        sample_event = recent_events[0]
        print(f"\n📝 Sample Event Details:")
        print(f"   🆔 ID: {sample_event.id}")
        print(f"   📋 Type: {sample_event.event_type}")
        print(f"   👤 Agent: {sample_event.agent_id}")
        print(f"   ⚡ Priority: {sample_event.priority}")
        print(f"   🏷️  Tags: {', '.join(sample_event.tags)}")


async def demonstrate_event_replay(replay_engine: EventReplayEngine, storage: MemoryEventStorage):
    """Demonstrate event replay for crash recovery."""
    print("\n🔄 Event Replay Demonstration")
    print("-" * 40)

    # Get recent session events for replay
    recent_filter = EventFilter(
        start_time=datetime.utcnow() - timedelta(hours=1),
        limit=100
    )

    recent_events = await storage.get_events(recent_filter)

    if not recent_events:
        print("   ℹ️  No recent events available for replay demonstration")
        return

    # Find a session ID to replay
    session_ids = set()
    for event in recent_events:
        if event.session_id:
            session_ids.add(event.session_id)

    if not session_ids:
        print("   ℹ️  No session events available for replay")
        return

    demo_session_id = list(session_ids)[0]
    print(f"1️⃣ Replaying Session: {demo_session_id}")

    # Create replay request
    replay_request = EventReplayRequest(
        session_id=demo_session_id,
        from_timestamp=datetime.utcnow() - timedelta(hours=2)
    )

    # Execute replay
    replay_result = await replay_engine.replay_events(replay_request)

    print(f"   📊 Replay Results:")
    print(f"   🔢 Events replayed: {replay_result['event_count']}")
    print(f"   🎯 Event types: {list(replay_result['summary']['event_types'].keys())}")
    print(f"   👥 Agents involved: {len(replay_result['summary']['agents'])}")
    print(f"   📋 Tasks involved: {len(replay_result['summary']['tasks'])}")

    if replay_result['summary']['time_range']:
        time_range = replay_result['summary']['time_range']
        print(f"   ⏰ Time range: {time_range['start']} to {time_range['end']}")

    print(f"\n   💡 Use Case: This replay data can be used to:")
    print(f"      • Restore agent state after crashes")
    print(f"      • Audit agent decision-making processes")
    print(f"      • Debug collaborative workflows")
    print(f"      • Generate performance analytics")


async def show_storage_statistics(storage: MemoryEventStorage):
    """Display storage system statistics."""
    print("\n📊 Storage System Statistics")
    print("-" * 40)

    try:
        # Get storage info
        storage_info = await storage.get_storage_info()
        print(f"📈 Total Events: {storage_info.total_events}")

        if storage_info.events_by_type:
            print(f"🏷️  Events by Type:")
            for event_type, count in storage_info.events_by_type.items():
                print(f"   • {event_type}: {count}")

        # Get integration status
        integration_status = await storage.get_integration_status()
        print(f"\n🔗 Integration Status:")
        print(f"   • Connected: {integration_status.connected}")
        print(f"   • Backend Type: {integration_status.backend_type}")
        print(f"   • Pending Events: {integration_status.pending_events}")
        print(f"   • Failed Events: {integration_status.failed_events}")

        if integration_status.last_sync:
            print(f"   • Last Sync: {integration_status.last_sync}")

        # Get health status
        health_status = await storage.get_health_status()
        print(f"\n💚 Health Status:")
        print(f"   • Overall: {health_status['status']}")
        print(f"   • SQLite Backend: {'✅' if health_status['sqlite_backend'] else '❌'}")
        print(f"   • Memory Interface: {'✅' if health_status['memory_interface'] else '❌'}")
        print(f"   • Cache Size: {health_status['cache_size']} events")

        if 'sqlite_events' in health_status:
            print(f"   • SQLite Events: {health_status['sqlite_events']}")

    except Exception as e:
        print(f"❌ Error retrieving storage statistics: {e}")


if __name__ == "__main__":
    """Run the demonstration."""
    print("🎬 Starting Event Router Memory Integration Demo...")
    print("This demonstrates the production-ready event system with:")
    print("• Agent lifecycle event tracking")
    print("• Memory system integration")
    print("• Event filtering and querying")
    print("• Crash recovery via event replay")
    print("• Production-grade persistence")
    print()

    asyncio.run(demonstrate_event_system())
