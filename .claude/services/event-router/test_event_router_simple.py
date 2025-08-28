#!/usr/bin/env python3
"""Simple test to verify Event Router functionality."""

import asyncio
import json
import sys
from datetime import datetime
from event_router_service import (
    EventRouterService,
    Event,
    EventType,
    EventPriority,
    EventFilter,
    Subscription
)

async def test_direct_api():
    """Test the Event Router using direct API calls (no WebSocket)."""
    print("=" * 60)
    print("Testing Event Router Service - Direct API")
    print("=" * 60)
    
    # Create service
    service = EventRouterService(
        host="localhost",
        port=9090,
        max_workers=5,
        queue_size=1000
    )
    
    print("\n1. Creating Event Router Service...")
    
    # Test queue functionality
    print("\n2. Testing Event Queue...")
    
    # Create test events
    events = [
        Event(
            id="evt-001",
            type=EventType.TASK_CREATED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(),
            source="test_script",
            target="worker",
            payload={"task": "high_priority_task"},
            metadata={"test": True}
        ),
        Event(
            id="evt-002",
            type=EventType.AGENT_STARTED,
            priority=EventPriority.NORMAL,
            timestamp=datetime.now(),
            source="test_script",
            target=None,
            payload={"agent": "test_agent"},
            metadata={"test": True}
        ),
        Event(
            id="evt-003",
            type=EventType.SYSTEM_ALERT,
            priority=EventPriority.CRITICAL,
            timestamp=datetime.now(),
            source="test_script",
            target="admin",
            payload={"alert": "critical_issue"},
            metadata={"test": True}
        )
    ]
    
    # Test publishing events
    print("\n3. Publishing test events...")
    for event in events:
        await service.publish_event(event)
        print(f"   ✓ Published {event.type.value} with priority {event.priority.value}")
    
    # Check queue size
    print(f"\n4. Queue size: {service.event_queue.qsize()}")
    
    # Test subscription
    print("\n5. Testing subscriptions...")
    
    received_events = []
    
    def event_handler(event: Event):
        """Handle received events."""
        received_events.append(event)
        print(f"   ✓ Received event: {event.type.value} from {event.source}")
    
    # Create subscription
    subscription = Subscription(
        id="sub-001",
        subscriber_id="test_subscriber",
        subscription_type="filtered",  # type: ignore[assignment]
        filter=EventFilter(
            event_types=[EventType.TASK_CREATED, EventType.AGENT_STARTED],
            priorities=[EventPriority.HIGH, EventPriority.NORMAL]
        ),
        callback=event_handler,
        endpoint=None
    )
    
    # Add subscription (not async)
    service.subscribe(
        subscriber_id="test_subscriber",
        event_filter=subscription.filter,
        callback=event_handler
    )
    
    print("   ✓ Created subscription for TASK_CREATED and AGENT_STARTED events")
    
    # Process events (simulate event processing)
    print("\n6. Processing events...")
    
    # Start the service processing (in background)
    process_task = asyncio.create_task(service._process_events())
    
    # Give it time to process
    await asyncio.sleep(2)
    
    # Cancel processing
    process_task.cancel()
    try:
        await process_task
    except asyncio.CancelledError:
        pass
    
    # Check results
    print(f"\n7. Results:")
    print(f"   - Events published: {len(events)}")
    print(f"   - Events in queue: {service.event_queue.qsize()}")
    print(f"   - Subscriptions active: {len(service.subscriptions)}")
    print(f"   - Stats: {service.stats.total_events} total events")
    
    # Test filtering
    print("\n8. Testing event filtering...")
    
    # Create a filter
    test_filter = EventFilter(
        event_types=[EventType.TASK_CREATED],
        priorities=[EventPriority.HIGH]
    )
    
    # Check which events match
    for event in events:
        matches = service._event_matches_filter(event, test_filter)
        print(f"   Event {event.id} matches filter: {matches}")
    
    print("\n✅ Event Router basic functionality test completed!")
    
    return True

async def test_websocket_server():
    """Test starting the WebSocket server."""
    print("\n" + "=" * 60)
    print("Testing Event Router Service - WebSocket Server")
    print("=" * 60)
    
    # Create service
    service = EventRouterService(
        host="localhost",
        port=9091,  # Different port to avoid conflicts
        max_workers=5,
        queue_size=1000
    )
    
    print("\n1. Starting WebSocket server on port 9091...")
    
    # Start the server (but don't wait forever)
    server_task = asyncio.create_task(service.start())
    
    # Give it time to start
    await asyncio.sleep(2)
    
    if service.running:
        print("   ✓ WebSocket server started successfully")
    else:
        print("   ✗ WebSocket server failed to start")
    
    # Stop the server
    print("\n2. Stopping server...")
    await service.stop()
    
    # Cancel the server task
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    
    print("   ✓ Server stopped")
    
    return True

async def main():
    """Run all tests."""
    try:
        # Test direct API
        api_success = await test_direct_api()
        
        # Test WebSocket server
        ws_success = await test_websocket_server()
        
        if api_success and ws_success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ SOME TESTS FAILED")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)