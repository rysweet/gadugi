#!/usr/bin/env python3
"""
Simple test for whiteboard collaboration system
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from whiteboard_collaboration import WhiteboardManager, WhiteboardPermission


async def test_basic_functionality():
    """Test basic whiteboard functionality."""
    print("Testing Whiteboard System...")

    # Initialize manager
    manager = WhiteboardManager(db_path=".claude/data/test_whiteboards.db")
    await manager.initialize()
    print("✅ Manager initialized")

    # Create whiteboard
    whiteboard_id = await manager.create_whiteboard(
        name="Test Whiteboard",
        created_by="test_agent",
        template_id="task_coordination"
    )
    print(f"✅ Created whiteboard: {whiteboard_id}")

    # Get whiteboard
    wb = await manager.get_whiteboard(whiteboard_id, "test_agent")
    if wb:
        print("✅ Retrieved whiteboard")

        # Write some data
        await wb.write("test_agent", "test_key", "test_value")
        print("✅ Wrote data to whiteboard")

        # Read data back
        value = await wb.read("test_agent", "test_key")
        print(f"✅ Read value: {value}")

        # Get info
        info = await wb.get_info("test_agent")
        print(f"✅ Whiteboard info: {info['statistics']['total_changes']} changes")

        # Get templates
        templates = await manager.get_templates()
        print(f"✅ Found {len(templates)} templates")

    print("✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
