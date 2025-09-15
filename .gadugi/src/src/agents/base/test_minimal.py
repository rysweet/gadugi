#!/usr/bin/env python3
"""
Minimal test for whiteboard components
"""

import asyncio
from whiteboard_collaboration import SharedWhiteboard, WhiteboardType


async def test_minimal():
    """Minimal test."""
    print("Creating whiteboard...")

    wb = SharedWhiteboard(
        whiteboard_id="test_001",
        whiteboard_type=WhiteboardType.TASK_COORDINATION,
        owner_agent="test_agent",
    )

    print("✅ Whiteboard created")

    try:
        # Test write operation
        success = await wb.write("test_agent", "test.key", {"value": "test_value"})
        print(f"✅ Write operation: {success}")

        # Test read operation
        value = await wb.read("test_agent", "test.key")
        print(f"✅ Read value: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("✅ Minimal test completed!")


if __name__ == "__main__":
    asyncio.run(test_minimal())
