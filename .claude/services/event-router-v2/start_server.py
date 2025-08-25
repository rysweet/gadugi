#!/usr/bin/env python3
"""Standalone Event Router Server."""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.router import EventRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Start the Event Router server."""
    router = EventRouter(host="0.0.0.0", port=9090)
    print("Starting Event Router on ws://0.0.0.0:9090")
    print("Press Ctrl+C to stop")
    
    try:
        await router.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await router.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")