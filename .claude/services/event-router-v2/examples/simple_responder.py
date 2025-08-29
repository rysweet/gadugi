#!/usr/bin/env python3
"""
Simple Event Responder Example - Shows how to respond to specific events.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.client.client import EventRouterClient
from src.core.models import EventPriority


async def demonstrate_event_responses():
    """Demonstrate responding to specific events."""

    print("=" * 60)
    print("Event Response Patterns Demo")
    print("=" * 60)

    # Connect to running Event Router
    client = EventRouterClient(url="ws://localhost:9090")
    if not await client.connect():
        print("Failed to connect. Make sure Event Router is running:")
        print("  uv run python manage_router.py start --daemon")
        return

    print("\n✅ Connected to Event Router")

    # Pattern 1: Respond to specific topic
    print("\n1. Setting up handler for 'user.login' events...")

    @client.on("user.login")
    async def handle_login(event):
        user_id = event.payload.get("user_id")
        print(f"   → User {user_id} logged in at {event.payload.get('timestamp')}")

        # Respond by publishing a welcome event
        await client.publish(
            topic="notification.send",
            payload={
                "user_id": user_id,
                "message": f"Welcome back, user {user_id}!",
                "type": "welcome"
            }
        )

    # Pattern 2: Respond to pattern with wildcards
    print("2. Setting up handler for all 'error.*' events...")

    @client.on("error.*")
    async def handle_errors(event):
        print(f"   → ERROR: {event.topic} - {event.payload.get('message')}")

        # Respond based on error type
        if "critical" in event.payload.get("severity", ""):
            await client.publish(
                topic="alert.page_oncall",
                payload={
                    "error_id": event.id,
                    "severity": "critical",
                    "source": event.source
                },
                priority=EventPriority.CRITICAL
            )

    # Pattern 3: Respond to high-priority events only
    print("3. Setting up handler for high-priority task events...")

    async def handle_urgent_tasks(event):
        if event.priority >= EventPriority.HIGH:
            print(f"   → URGENT: {event.topic} (priority: {event.priority.name})")

            # Respond by escalating
            await client.publish(
                topic="task.escalated",
                payload={
                    "original_event": event.id,
                    "reason": "high_priority",
                    "escalated_to": "senior_agent"
                }
            )

    await client.subscribe(
        topics=["task.*"],
        priorities=[EventPriority.HIGH, EventPriority.CRITICAL],
        callback=handle_urgent_tasks  # type: ignore[assignment]
    )

    # Pattern 4: Chain responses
    print("4. Setting up response chain...")

    @client.on("order.placed")
    async def handle_order(event):
        order_id = event.payload.get("order_id")
        print(f"   → Order {order_id} received")

        # Trigger multiple responses
        # 1. Validate inventory
        await client.publish(
            topic="inventory.check",
            payload={"order_id": order_id, "items": event.payload.get("items")}
        )

        # 2. Process payment
        await client.publish(
            topic="payment.process",
            payload={"order_id": order_id, "amount": event.payload.get("total")}
        )

        # 3. Send confirmation
        await client.publish(
            topic="email.send",
            payload={
                "order_id": order_id,
                "customer": event.payload.get("customer"),
                "template": "order_confirmation"
            }
        )

    @client.on("inventory.check")
    async def check_inventory(event):
        print(f"   → Checking inventory for order {event.payload.get('order_id')}")
        # Respond with result
        await client.publish(
            topic="inventory.result",
            payload={"order_id": event.payload.get("order_id"), "available": True}
        )

    @client.on("payment.process")
    async def process_payment(event):
        print(f"   → Processing payment for order {event.payload.get('order_id')}")
        # Respond with result
        await client.publish(
            topic="payment.result",
            payload={"order_id": event.payload.get("order_id"), "status": "success"}
        )

    # Now simulate some events to see the responses
    print("\n" + "=" * 60)
    print("Simulating Events and Observing Responses:")
    print("=" * 60)

    # Simulate user login
    print("\n→ Publishing user.login event...")
    await client.publish(
        topic="user.login",
        payload={"user_id": "user123", "timestamp": datetime.now().isoformat()}
    )
    await asyncio.sleep(0.5)

    # Simulate error
    print("\n→ Publishing error.database event...")
    await client.publish(
        topic="error.database",
        payload={"message": "Connection timeout", "severity": "critical"}
    )
    await asyncio.sleep(0.5)

    # Simulate high-priority task
    print("\n→ Publishing high-priority task.created event...")
    await client.publish(
        topic="task.created",
        payload={"task_id": "task456", "description": "Urgent fix needed"},
        priority=EventPriority.CRITICAL
    )
    await asyncio.sleep(0.5)

    # Simulate order (triggers chain)
    print("\n→ Publishing order.placed event (triggers chain)...")
    await client.publish(
        topic="order.placed",
        payload={
            "order_id": "ORD789",
            "customer": "john@example.com",
            "items": ["item1", "item2"],
            "total": 99.99
        }
    )
    await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("Summary of Response Patterns:")
    print("=" * 60)
    print("""
1. DIRECT RESPONSE: Handle specific topic and respond
   user.login → notification.send

2. PATTERN MATCHING: Use wildcards to handle multiple events
   error.* → alert.page_oncall (for critical)

3. PRIORITY FILTERING: Respond only to high-priority events
   task.* + HIGH priority → task.escalated

4. RESPONSE CHAINS: One event triggers multiple responses
   order.placed → inventory.check + payment.process + email.send

5. CONDITIONAL RESPONSES: Check payload and respond accordingly
   Based on severity, type, or other fields
    """)

    await client.disconnect()
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demonstrate_event_responses())
