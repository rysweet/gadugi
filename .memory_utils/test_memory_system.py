#!/usr/bin/env python3
"""
Basic tests for the hierarchical memory system
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from memory_manager import MemoryManager, MemoryLevel
from agent_interface import AgentMemoryInterface


def test_memory_manager():
    """Test basic memory manager functionality"""
    print("Testing Memory Manager...")

    # Use current directory for testing
    manager = MemoryManager()

    # Test 1: List memories
    print("\n1. Listing memories:")
    memories = manager.list_memories()
    for level, files in memories.items():
        print(f"  {level}: {files}")

    # Test 2: Read existing memory
    print("\n2. Reading project context:")
    context = manager.read_memory(MemoryLevel.PROJECT, "context")
    if context["exists"]:
        print(f"  Found: {context['metadata']}")
        print(f"  Sections: {list(context['sections'].keys())}")

    # Test 3: Add memory entry
    print("\n3. Adding test memory entry:")
    manager.add_memory_entry(
        MemoryLevel.PROJECT,
        "context",
        "Test Entries",
        "Test entry from memory system validation",
    )
    print("  Entry added successfully")

    # Test 4: Search memories
    print("\n4. Searching for 'Gadugi':")
    results = manager.search_memories("Gadugi")
    for level, filename, match in results[:3]:  # Show first 3 results
        print(f"  {level}/{filename}: {match[:80]}...")


def test_agent_interface():
    """Test agent memory interface"""
    print("\n\nTesting Agent Interface...")

    # Test 1: OrchestratorAgent permissions
    print("\n1. Testing OrchestratorAgent:")
    orchestrator = AgentMemoryInterface("test-orch", "orchestrator-agent")
    summary = orchestrator.get_memory_summary()
    print(f"  Can read: {list(summary['accessible_memories'].keys())}")
    print(
        f"  Can write: {[k for k, v in summary['accessible_memories'].items() if v['can_write']]}"
    )

    # Test 2: CodeReviewer permissions
    print("\n2. Testing CodeReviewer:")
    reviewer = AgentMemoryInterface("test-reviewer", "code-reviewer")
    summary = reviewer.get_memory_summary()
    print(f"  Can read: {list(summary['accessible_memories'].keys())}")
    print(
        f"  Can write: {[k for k, v in summary['accessible_memories'].items() if v['can_write']]}"
    )

    # Test 3: Record agent memory
    print("\n3. Recording agent memory:")
    success = orchestrator.record_agent_memory(
        "Test Results", "Memory system validation completed successfully"
    )
    print(f"  Recording: {'Success' if success else 'Failed'}")

    # Test 4: Permission denial
    print("\n4. Testing permission denial:")
    # CodeReviewer shouldn't write to project level
    denied = reviewer.add_memory_entry(
        MemoryLevel.PROJECT, "context", "Unauthorized", "This should be denied"
    )
    print(
        f"  Write to project level: {'Allowed (ERROR!)' if denied else 'Denied (correct)'}"
    )


if __name__ == "__main__":
    print("Hierarchical Memory System Test Suite")
    print("=" * 50)

    test_memory_manager()
    test_agent_interface()

    print("\n" + "=" * 50)
    print("All tests completed!")
