#!/usr/bin/env python3
"""Run the Event Router server."""

import asyncio
import logging
from event_router_service import EventRouterService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Start the Event Router server."""
    print("=" * 60)
    print("Starting Event Router Server")
    print("=" * 60)
    print()
    print("Server Configuration:")
    print("  Host: localhost")
    print("  Port: 9090")
    print("  WebSocket URL: ws://localhost:9090")
    print()
    print("Endpoints:")
    print("  - WebSocket: ws://localhost:9090")
    print("  - Send messages in JSON format")
    print()
    print("Message Types:")
    print("  - publish_event: Publish an event")
    print("  - subscribe: Subscribe to events")
    print("  - unsubscribe: Unsubscribe from events")
    print("  - ping: Health check")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Create and start service
    service = EventRouterService(
        host="localhost", port=9090, max_workers=10, queue_size=10000
    )

    try:
        await service.start()
        # Keep running until interrupted
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await service.stop()
        print("Server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer terminated.")
