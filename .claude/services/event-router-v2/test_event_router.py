#!/usr/bin/env python3
"""Test Event Router V2 - Simple end-to-end test."""

import asyncio
import sys
import logging
from datetime import datetime

# Setup path
sys.path.append('src')

from core.router import EventRouter  # type: ignore[import]
from core.models import Event, EventType, EventPriority  # type: ignore[import]
from client.client import EventRouterClient  # type: ignore[import]

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_event_router():
    """Test the event router with a simple producer-consumer pattern."""
    
    print("\n" + "=" * 60)
    print("Event Router V2 - End-to-End Test")
    print("=" * 60)
    
    # 1. Start the server
    print("\n1. Starting Event Router Server...")
    router = EventRouter(host="localhost", port=9091)
    server_task = asyncio.create_task(router.start())
    await asyncio.sleep(1)
    print("   ✅ Server started on ws://localhost:9091")
    
    # 2. Create producer client
    print("\n2. Creating Producer Client...")
    producer = EventRouterClient(url="ws://localhost:9091")
    connected = await producer.connect()
    if connected:
        print("   ✅ Producer connected")
    else:
        print("   ❌ Producer connection failed")
        return
    
    # 3. Create consumer client
    print("\n3. Creating Consumer Client...")
    consumer = EventRouterClient(url="ws://localhost:9091")
    connected = await consumer.connect()
    if connected:
        print("   ✅ Consumer connected")
    else:
        print("   ❌ Consumer connection failed")
        return
    
    # 4. Set up subscription
    print("\n4. Setting up Consumer Subscription...")
    received_events = []
    
    @consumer.on("test.*")
    async def handle_test_event(event):
        received_events.append(event)
        print(f"   📨 Consumer received: {event.topic} - {event.payload.get('message')}")
    
    sub_id = await consumer.subscribe(
        topics=["test.*"],
        callback=handle_test_event
    )
    print(f"   ✅ Subscription created: {sub_id}")
    
    # 5. Publish events
    print("\n5. Publishing Events...")
    events_to_send = [
        ("test.message", {"message": "Hello, Event Router!", "index": 1}, EventPriority.HIGH),
        ("test.data", {"message": "Data update", "value": 42}, EventPriority.NORMAL),
        ("test.alert", {"message": "Important alert!", "severity": "high"}, EventPriority.CRITICAL),
    ]
    
    for topic, payload, priority in events_to_send:
        event_id = await producer.publish(
            topic=topic,
            payload=payload,
            priority=priority
        )
        print(f"   📤 Published: {topic} (priority: {priority.name}) - Event ID: {event_id}")
        await asyncio.sleep(0.5)
    
    # 6. Wait for events to be processed
    print("\n6. Waiting for Event Processing...")
    await asyncio.sleep(2)
    
    # 7. Verify results
    print("\n7. Results:")
    print(f"   Events sent: {len(events_to_send)}")
    print(f"   Events received: {len(received_events)}")
    
    if len(received_events) == len(events_to_send):
        print("   ✅ All events successfully delivered!")
    else:
        print(f"   ⚠️  Only {len(received_events)} of {len(events_to_send)} events received")
    
    # 8. Check health
    print("\n8. Health Check:")
    health = await producer.get_health()
    if health:
        print(f"   Server Status: {health.get('status', 'unknown')}")
        print(f"   Events Processed: {health.get('events_processed', 0)}")
        print(f"   Active Subscriptions: {health.get('active_subscriptions', 0)}")
        print(f"   Connected Clients: {health.get('connected_clients', 0)}")
    
    # 9. Test reconnection
    print("\n9. Testing Auto-Reconnection...")
    print("   Simulating connection drop...")
    await producer.websocket.close()
    await asyncio.sleep(2)
    
    if producer.is_connected:
        print("   ✅ Client auto-reconnected!")
        
        # Send another event after reconnection
        event_id = await producer.publish(
            topic="test.reconnect",
            payload={"message": "Sent after reconnection!"}
        )
        print(f"   📤 Published after reconnect: {event_id}")
    else:
        print("   ⚠️  Client did not auto-reconnect")
    
    # 10. Cleanup
    print("\n10. Cleaning up...")
    await producer.disconnect()
    await consumer.disconnect()
    await router.stop()
    server_task.cancel()
    
    print("\n" + "=" * 60)
    print("✅ Event Router V2 Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_event_router())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")