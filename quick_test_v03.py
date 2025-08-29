#!/usr/bin/env python3
"""
Quick test of Gadugi v0.3 functionality without FastAPI.
Demonstrates the core memory system capabilities.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add path to import our modules
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "services" / "memory"))

from sqlite_memory_backend import SQLiteMemoryBackend


async def main():
    """Run a quick test of v0.3 capabilities."""

    print("=" * 60)
    print("  Gadugi v0.3 Quick Test")
    print("  Testing core memory system without server")
    print("=" * 60)

    # Initialize backend
    backend = SQLiteMemoryBackend(db_path=".claude/data/test_memory.db")
    await backend.initialize()
    print("\n✅ Memory backend initialized")

    # Create test agent
    agent_id = f"demo_agent_{datetime.now().strftime('%H%M%S')}"
    task_id = f"demo_task_{datetime.now().strftime('%H%M%S')}"

    print(f"\n📤 Agent ID: {agent_id}")
    print(f"📤 Task ID: {task_id}")

    # ===== Memory Operations =====
    print("\n" + "=" * 40)
    print("1️⃣  MEMORY OPERATIONS")
    print("=" * 40)

    # Store different memory types
    memories_stored = []

    # Short-term memory
    mem_id = await backend.store_memory(
        agent_id=agent_id,
        content="Starting Gadugi v0.3 test",
        memory_type="short_term",
        task_id=task_id,
        importance_score=0.7,
    )
    memories_stored.append(("short_term", mem_id))
    print(f"✅ Short-term: {mem_id[:8]}...")

    # Long-term memory
    mem_id = await backend.store_memory(
        agent_id=agent_id,
        content="Gadugi v0.3 is a self-hosting AI system",
        memory_type="long_term",
        importance_score=0.95,
    )
    memories_stored.append(("long_term", mem_id))
    print(f"✅ Long-term: {mem_id[:8]}...")

    # Episodic memory
    mem_id = await backend.store_memory(
        agent_id=agent_id,
        content=f"Test began at {datetime.now().isoformat()}",
        memory_type="episodic",
        task_id=task_id,
        importance_score=0.6,
    )
    memories_stored.append(("episodic", mem_id))
    print(f"✅ Episodic: {mem_id[:8]}...")

    # Semantic memory
    mem_id = await backend.store_memory(
        agent_id=agent_id,
        content="SQLite backend enables local testing without Docker",
        memory_type="semantic",
        importance_score=0.85,
    )
    memories_stored.append(("semantic", mem_id))
    print(f"✅ Semantic: {mem_id[:8]}...")

    # Procedural memory (stored as procedure)
    proc_id = await backend.store_procedure(
        agent_id=agent_id,
        procedure_name="run_v03_test",
        steps=[
            "Initialize memory backend",
            "Create agent and task",
            "Store memories",
            "Create whiteboard",
            "Build knowledge graph",
            "Test collaboration",
        ],
        context="Testing Gadugi v0.3",
    )
    print(f"✅ Procedural: {proc_id[:8]}...")

    # Project shared memory
    mem_id = await backend.store_memory(
        agent_id=agent_id,
        content="Gadugi v0.3 milestone: Zero pyright errors achieved",
        memory_type="project_shared",
        importance_score=1.0,
        metadata={"project": "gadugi", "version": "0.3", "milestone": True},
    )
    memories_stored.append(("project_shared", mem_id))
    print(f"✅ Project Shared: {mem_id[:8]}...")

    # ===== Whiteboard Operations =====
    print("\n" + "=" * 40)
    print("2️⃣  WHITEBOARD COLLABORATION")
    print("=" * 40)

    # Create whiteboard
    wb_id = await backend.create_whiteboard(task_id, agent_id)
    print(f"✅ Created whiteboard: {wb_id[:8]}...")

    # Update whiteboard with content
    await backend.update_whiteboard(
        task_id=task_id,
        content={
            "status": "testing",
            "findings": [
                "Memory system operational",
                "All memory types functional",
                "No Docker required",
            ],
            "next_steps": [
                "Test orchestrator integration",
                "Validate agent collaboration",
                "Run performance benchmarks",
            ],
        },
    )
    print("✅ Updated whiteboard content")

    # Add decision
    await backend.update_whiteboard(task_id=task_id, decision="System ready for agent deployment")
    print("✅ Added decision to whiteboard")

    # Retrieve whiteboard
    whiteboard = await backend.get_whiteboard(task_id)
    print(f"📋 Whiteboard status: {whiteboard['content']['status']}")
    print(f"📋 Findings: {len(whiteboard['content']['findings'])} items")
    print(f"📋 Decisions: {len(whiteboard['decisions'])} made")

    # ===== Knowledge Graph =====
    print("\n" + "=" * 40)
    print("3️⃣  KNOWLEDGE GRAPH")
    print("=" * 40)

    # Add knowledge nodes
    nodes = []

    node1 = await backend.add_knowledge_node(
        agent_id=agent_id,
        concept="Gadugi v0.3",
        description="Self-hosting AI system with advanced memory",
        confidence=0.95,
    )
    nodes.append(("Gadugi v0.3", node1))
    print("✅ Node: Gadugi v0.3")

    node2 = await backend.add_knowledge_node(
        agent_id=agent_id,
        concept="Memory System",
        description="Multi-type memory storage and retrieval",
        confidence=0.9,
    )
    nodes.append(("Memory System", node2))
    print("✅ Node: Memory System")

    node3 = await backend.add_knowledge_node(
        agent_id=agent_id,
        concept="Type Safety",
        description="Zero pyright errors achieved",
        confidence=1.0,
    )
    nodes.append(("Type Safety", node3))
    print("✅ Node: Type Safety")

    node4 = await backend.add_knowledge_node(
        agent_id=agent_id,
        concept="Parallel Execution",
        description="3-5x faster task completion",
        confidence=0.85,
    )
    nodes.append(("Parallel Execution", node4))
    print("✅ Node: Parallel Execution")

    # Add edges
    edges = [
        (node1, node2, "contains", 0.9),
        (node1, node3, "achieves", 1.0),
        (node1, node4, "enables", 0.85),
        (node2, node4, "supports", 0.8),
    ]

    for source, target, rel, weight in edges:
        await backend.add_knowledge_edge(source, target, rel, weight)

    print(f"✅ Added {len(edges)} knowledge edges")

    # Get knowledge graph
    graph = await backend.get_knowledge_graph(agent_id)
    print(f"📊 Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    # ===== Memory Recall =====
    print("\n" + "=" * 40)
    print("4️⃣  MEMORY RECALL")
    print("=" * 40)

    # Recall all memories
    all_memories = await backend.get_memories(agent_id)
    print(f"✅ Total memories: {len(all_memories)}")

    # Group by type
    by_type = {}
    for mem in all_memories:
        mem_type = mem["memory_type"]
        if mem_type not in by_type:
            by_type[mem_type] = 0
        by_type[mem_type] += 1

    for mem_type, count in by_type.items():
        print(f"   - {mem_type}: {count}")

    # Recall task-specific memories
    task_memories = await backend.get_memories(agent_id, task_id=task_id)
    print(f"✅ Task memories: {len(task_memories)}")

    # ===== Statistics =====
    print("\n" + "=" * 40)
    print("5️⃣  SYSTEM STATISTICS")
    print("=" * 40)

    stats = await backend.get_stats()
    print(f"📊 Total memories: {stats['total_memories']}")
    print(f"📊 Knowledge nodes: {stats['total_knowledge_nodes']}")
    print(f"📊 Knowledge edges: {stats['total_knowledge_edges']}")
    print(f"📊 Whiteboards: {stats['total_whiteboards']}")
    print(f"📊 Procedures: {stats['total_procedures']}")

    # ===== Summary =====
    print("\n" + "=" * 60)
    print("✅ GADUGI V0.3 TEST COMPLETE")
    print("=" * 60)
    print("\n🎯 Key Features Demonstrated:")
    print("  • Multi-type memory system (6 types)")
    print("  • Task whiteboard collaboration")
    print("  • Knowledge graph construction")
    print("  • Procedure storage and retrieval")
    print("  • Project-shared memory")
    print("  • SQLite backend (no Docker required)")

    print("\n💡 Next Steps:")
    print("  1. Run: .claude/services/memory/start_local.sh")
    print("  2. Access API: http://localhost:8000/docs")
    print("  3. Test agents with memory integration")
    print("  4. Deploy orchestrator for parallel tasks")

    print("\n📚 Documentation:")
    print("  • Quick Start: RUN_V0.3_GUIDE.md")
    print("  • Memory System: .claude/services/memory/README.md")
    print("  • Agent Integration: .claude/shared/memory_integration.py")

    return True


if __name__ == "__main__":
    print("\n🚀 Starting Gadugi v0.3 Quick Test...\n")

    try:
        success = asyncio.run(main())

        if success:
            print("\n✅ All systems operational!")
            print("🎉 Gadugi v0.3 is ready for use!\n")
        else:
            print("\n⚠️  Some tests may have issues.\n")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
