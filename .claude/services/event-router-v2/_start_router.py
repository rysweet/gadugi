#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

sys.path.append('/home/rysweet/gadugi/.claude/services/event-router-v2/src')

from core.router import EventRouter  # type: ignore[import]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('event_router.log'),
        logging.StreamHandler()
    ]
)

async def main():
    router = EventRouter(
        host="localhost",
        port=9090,
        max_queue_size=10000,
        max_clients=1000,
        use_multi_queue=False
    )
    print(f"Event Router starting on ws://localhost:9090")
    await router.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEvent Router stopped")
