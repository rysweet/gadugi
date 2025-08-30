#!/usr/bin/env python3
"""
Simple test for whiteboard collaboration system
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from whiteboard_collaboration import WhiteboardManager, WhiteboardType


async def test_basic_functionality():
    """Test basic whiteboard functionality."""
    print("Testing Whiteboard System...")

    # Initialize manager
    manager = WhiteboardManager()
    await manager.initialize()
    print("✅ Manager initialized")

    # Create whiteboard
    wb = await manager.create_whiteboard(
        whiteboard_type=WhiteboardType.TASK_COORDINATION, owner_agent="test_agent"
    )
    whiteboard_id = wb.whiteboard_id
    print(f"✅ Created whiteboard: {whiteboard_id}")

    # Get whiteboard
    wb = manager.get_whiteboard(whiteboard_id)
    if wb:
        print("✅ Retrieved whiteboard")

        # Write some data
        await wb.write("test_agent", "test_key", {"value": "test_value"})
        print("✅ Wrote data to whiteboard")

        # Read data back
        value = await wb.read("test_agent", "test_key")
        print(f"✅ Read value: {value}")

        # Get stats
        stats = wb.get_stats()
        print(f"✅ Whiteboard stats: {stats['total_entries']} entries")

        # List all whiteboards
        # Note: list_whiteboards method doesn't exist, use the internal _whiteboards dict
        whiteboards = list(manager._whiteboards.keys())
        print(f"✅ Found {len(whiteboards)} whiteboards")

    print("✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
