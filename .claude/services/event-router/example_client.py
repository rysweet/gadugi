#!/usr/bin/env python3
"""Example client for Event Router - demonstrates publishing and subscribing."""

import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)

async def publisher_client():
    """Example publisher that sends events."""
    uri = "ws://localhost:9090"
    
    print("Publisher: Connecting to Event Router...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Publisher: Connected!")
            
            # Publish different types of events
            events = [
                {
                    "type": "publish_event",
                    "event": {
                        "type": "agent_started",
                        "priority": "normal",
                        "source": "orchestrator",
                        "target": "monitor",
                        "payload": {
                            "agent_id": "agent-001",
                            "agent_type": "code_reviewer",
                            "task": "Review PR #123"
                        },
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "version": "1.0"
                        }
                    }
                },
                {
                    "type": "publish_event",
                    "event": {
                        "type": "task_created",
                        "priority": "high",
                        "source": "task_manager",
                        "target": "worker_pool",
                        "payload": {
                            "task_id": "task-456",
                            "description": "Process urgent data batch",
                            "priority": "high"
                        },
                        "metadata": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                },
                {
                    "type": "publish_event",
                    "event": {
                        "type": "system_alert",
                        "priority": "critical",
                        "source": "monitoring",
                        "target": "admin",
                        "payload": {
                            "alert_type": "performance",
                            "message": "High memory usage detected",
                            "severity": "warning"
                        },
                        "metadata": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                }
            ]
            
            for event in events:
                print(f"\nPublisher: Sending {event['event']['type']}...")
                await websocket.send(json.dumps(event))
                
                # Wait for acknowledgment
                response = await websocket.recv()
                resp_data = json.loads(response)
                print(f"Publisher: Received ack: {resp_data}")
                
                # Small delay between events
                await asyncio.sleep(1)
            
            print("\nPublisher: All events sent!")
            
    except Exception as e:
        print(f"Publisher Error: {e}")

async def subscriber_client():
    """Example subscriber that receives events."""
    uri = "ws://localhost:9090"
    
    print("Subscriber: Connecting to Event Router...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Subscriber: Connected!")
            
            # Subscribe to specific events
            subscription = {
                "type": "subscribe",
                "subscription": {
                    "type": "filtered",
                    "filter": {
                        "event_types": ["agent_started", "task_created", "system_alert"],
                        "priorities": ["high", "critical", "normal"]
                    }
                }
            }
            
            print("Subscriber: Setting up subscription...")
            await websocket.send(json.dumps(subscription))
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            resp_data = json.loads(response)
            print(f"Subscriber: Subscription confirmed: {resp_data}")
            
            # Listen for events
            print("\nSubscriber: Listening for events...")
            print("-" * 40)
            
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    event_data = json.loads(message)
                    
                    if event_data.get("type") == "event_delivery":
                        event = event_data.get("event", {})
                        print(f"\n📨 Received Event:")
                        print(f"   Type: {event.get('type')}")
                        print(f"   Priority: {event.get('priority')}")
                        print(f"   Source: {event.get('source')}")
                        print(f"   Payload: {json.dumps(event.get('payload', {}), indent=6)}")
                    else:
                        print(f"Subscriber: Received: {event_data}")
                        
            except asyncio.TimeoutError:
                print("\nSubscriber: No more events (timeout). Closing connection.")
                
    except Exception as e:
        print(f"Subscriber Error: {e}")

async def interactive_client():
    """Interactive client for testing."""
    uri = "ws://localhost:9090"
    
    print("Interactive Client")
    print("=" * 50)
    print("Commands:")
    print("  ping - Send ping message")
    print("  pub <type> <msg> - Publish event")
    print("  sub - Subscribe to all events")
    print("  quit - Exit")
    print("=" * 50)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to Event Router!")
            
            # Start listener task
            async def listen():
                try:
                    while True:
                        message = await websocket.recv()
                        print(f"\n📥 Received: {json.loads(message)}")
                        print("> ", end="", flush=True)
                except:
                    pass
            
            listener = asyncio.create_task(listen())
            
            while True:
                command = input("> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "ping":
                    await websocket.send(json.dumps({"type": "ping"}))
                elif command == "sub":
                    sub_msg = {
                        "type": "subscribe",
                        "subscription": {
                            "type": "all"
                        }
                    }
                    await websocket.send(json.dumps(sub_msg))
                elif command.startswith("pub "):
                    parts = command.split(" ", 2)
                    if len(parts) >= 3:
                        event_msg = {
                            "type": "publish_event",
                            "event": {
                                "type": parts[1],
                                "priority": "normal",
                                "source": "interactive",
                                "payload": {"message": parts[2]}
                            }
                        }
                        await websocket.send(json.dumps(event_msg))
                    else:
                        print("Usage: pub <type> <message>")
                else:
                    print("Unknown command. Try: ping, pub, sub, quit")
            
            listener.cancel()
            
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Run example clients."""
    print("Event Router Client Examples")
    print("=" * 60)
    print("1. Run publisher and subscriber")
    print("2. Run interactive client")
    print("3. Run publisher only")
    print("4. Run subscriber only")
    print("=" * 60)
    
    choice = input("Select option (1-4): ").strip()
    
    if choice == "1":
        # Run both publisher and subscriber
        await asyncio.gather(
            subscriber_client(),
            asyncio.create_task(asyncio.sleep(1)).then(publisher_client())
        )
    elif choice == "2":
        await interactive_client()
    elif choice == "3":
        await publisher_client()
    elif choice == "4":
        await subscriber_client()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        # First, let's create a helper coroutine for delayed execution
        async def run_with_delay():
            # Start subscriber
            subscriber_task = asyncio.create_task(subscriber_client())
            
            # Wait a bit then start publisher
            await asyncio.sleep(2)
            await publisher_client()
            
            # Give subscriber time to receive messages
            await asyncio.sleep(3)
            
            # Cancel subscriber
            subscriber_task.cancel()
            try:
                await subscriber_task
            except asyncio.CancelledError:
                pass
        
        # Check command line args
        if len(sys.argv) > 1:
            if sys.argv[1] == "pub":
                asyncio.run(publisher_client())
            elif sys.argv[1] == "sub":
                asyncio.run(subscriber_client())
            elif sys.argv[1] == "both":
                asyncio.run(run_with_delay())
            elif sys.argv[1] == "interactive":
                asyncio.run(interactive_client())
            else:
                print("Usage: python example_client.py [pub|sub|both|interactive]")
        else:
            asyncio.run(main())
            
    except KeyboardInterrupt:
        print("\nClient terminated.")