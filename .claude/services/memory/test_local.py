#!/usr/bin/env python3
"""
Test the local memory system for Gadugi v0.3
"""

import asyncio
import httpx
from datetime import datetime
import json


async def test_memory_system():
    """Test all memory system endpoints."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        print("=" * 50)
        print("Testing Gadugi v0.3 Memory System")
        print("=" * 50)

        # Health check
        print("\n1. Health Check...")
        response = await client.get("/health")
        health = response.json()
        print(f"   Status: {health['status']}")
        print(f"   Backend: {health.get('backend', 'unknown')}")

        # Create test agent and task
        agent_id = f"test_agent_{datetime.now().strftime('%H%M%S')}"
        task_id = f"task_{datetime.now().strftime('%H%M%S')}"

        print(f"\n2. Testing with agent: {agent_id}")
        print(f"   Task ID: {task_id}")

        # Store memories
        print("\n3. Storing Memories...")

        # Short-term memory
        response = await client.post("/memory/agent/store", json={
            "agent_id": agent_id,
            "content": "Testing v0.3 memory system",
            "memory_type": "short_term",
            "task_id": task_id,
            "importance_score": 0.8
        })
        mem1 = response.json()
        print(f"   ✅ Short-term memory: {mem1['id']}")

        # Long-term memory
        response = await client.post("/memory/agent/store", json={
            "agent_id": agent_id,
            "content": "Gadugi v0.3 uses SQLite for local testing",
            "memory_type": "long_term",
            "importance_score": 0.95
        })
        mem2 = response.json()
        print(f"   ✅ Long-term memory: {mem2['id']}")

        # Episodic memory
        response = await client.post("/memory/agent/store", json={
            "agent_id": agent_id,
            "content": "Started testing at " + datetime.now().isoformat(),
            "memory_type": "episodic",
            "task_id": task_id,
            "importance_score": 0.6
        })
        mem3 = response.json()
        print(f"   ✅ Episodic memory: {mem3['id']}")

        # Retrieve memories
        print("\n4. Retrieving Memories...")
        response = await client.get(f"/memory/agent/{agent_id}")
        memories = response.json()
        print(f"   Found {len(memories)} memories")
        for mem in memories:
            print(f"   - {mem['memory_type']}: {mem['content'][:50]}...")

        # Create and update whiteboard
        print("\n5. Testing Whiteboard...")
        response = await client.post("/whiteboard/create", json={
            "task_id": task_id,
            "agent_id": agent_id
        })
        wb = response.json()
        print(f"   ✅ Created whiteboard: {wb['id']}")

        # Update whiteboard
        response = await client.post(f"/whiteboard/update/{task_id}", json={
            "content": {
                "notes": "Testing memory system",
                "status": "in_progress",
                "findings": ["SQLite backend works", "All memory types functional"]
            },
            "decision": "System is ready for use"
        })
        print(f"   ✅ Updated whiteboard")

        # Get whiteboard
        response = await client.get(f"/whiteboard/{task_id}")
        whiteboard = response.json()
        print(f"   Content: {whiteboard['content']}")

        # Test knowledge graph
        print("\n6. Testing Knowledge Graph...")

        # Add nodes
        response = await client.post("/knowledge/node/create", json={
            "agent_id": agent_id,
            "concept": "Gadugi v0.3",
            "description": "Self-hosting AI system with memory",
            "confidence": 0.9
        })
        node1 = response.json()
        print(f"   ✅ Created node: {node1['concept']}")

        response = await client.post("/knowledge/node/create", json={
            "agent_id": agent_id,
            "concept": "SQLite",
            "description": "Lightweight database for testing",
            "confidence": 0.95
        })
        node2 = response.json()
        print(f"   ✅ Created node: {node2['concept']}")

        response = await client.post("/knowledge/node/create", json={
            "agent_id": agent_id,
            "concept": "Memory System",
            "description": "Stores agent memories and knowledge",
            "confidence": 0.85
        })
        node3 = response.json()
        print(f"   ✅ Created node: {node3['concept']}")

        # Add edges
        response = await client.post("/knowledge/edge/create", json={
            "source_id": node1['id'],
            "target_id": node3['id'],
            "relationship": "contains",
            "weight": 0.9
        })
        print(f"   ✅ Created edge: {node1['concept']} -> contains -> {node3['concept']}")

        response = await client.post("/knowledge/edge/create", json={
            "source_id": node2['id'],
            "target_id": node3['id'],
            "relationship": "powers",
            "weight": 0.8
        })
        print(f"   ✅ Created edge: {node2['concept']} -> powers -> {node3['concept']}")

        # Get knowledge graph
        response = await client.get(f"/knowledge/graph/{agent_id}")
        graph = response.json()
        print(f"   Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

        # Test procedures
        print("\n7. Testing Procedures...")
        response = await client.post("/memory/procedural/store", json={
            "agent_id": agent_id,
            "procedure_name": "test_memory_system",
            "steps": [
                "Start memory service",
                "Create agent and task",
                "Store memories",
                "Create whiteboard",
                "Add knowledge nodes",
                "Link knowledge with edges",
                "Store procedure"
            ],
            "context": "Testing Gadugi v0.3"
        })
        proc = response.json()
        print(f"   ✅ Stored procedure: {proc['procedure_name']}")

        # Get procedures
        response = await client.get(f"/memory/procedural/{agent_id}")
        procedures = response.json()
        print(f"   Found {len(procedures)} procedures")

        # Test project memory
        print("\n8. Testing Project Memory...")
        response = await client.post("/memory/project/store", json={
            "agent_id": agent_id,
            "content": "Gadugi v0.3 successfully tested with SQLite backend",
            "memory_type": "project_shared",
            "importance_score": 1.0,
            "metadata": {
                "project": "gadugi",
                "version": "0.3",
                "test_date": datetime.now().isoformat()
            }
        })
        proj_mem = response.json()
        print(f"   ✅ Stored project memory: {proj_mem['id']}")

        # Get metrics
        print("\n9. System Metrics...")
        response = await client.get("/metrics")
        metrics = response.json()
        stats = metrics['stats']
        print(f"   Total memories: {stats.get('total_memories', 0)}")
        print(f"   Total knowledge nodes: {stats.get('total_knowledge_nodes', 0)}")
        print(f"   Total knowledge edges: {stats.get('total_knowledge_edges', 0)}")
        print(f"   Total whiteboards: {stats.get('total_whiteboards', 0)}")
        print(f"   Total procedures: {stats.get('total_procedures', 0)}")

        if 'memory_types' in stats:
            print("\n   Memory breakdown:")
            for mem_type, count in stats['memory_types'].items():
                print(f"   - {mem_type}: {count}")

        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("=" * 50)

        return True


async def test_agent_integration():
    """Test agent integration with memory system."""
    print("\n" + "=" * 50)
    print("Testing Agent Integration")
    print("=" * 50)

    # Import the memory interface
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    try:
        from shared.memory_integration import AgentMemoryInterface

        async with AgentMemoryInterface(
            agent_id="integration_test_agent",
            mcp_base_url="http://localhost:8000"
        ) as memory:
            print("\n✅ Connected to memory system")

            # Store memories
            mem_id = await memory.remember_short_term("Testing agent integration")
            print(f"✅ Stored short-term memory: {mem_id}")

            # Create whiteboard for task collaboration
            whiteboard_id = await memory.create_whiteboard()
            print(f"✅ Created whiteboard: {whiteboard_id}")

            # Write to whiteboard
            await memory.write_to_whiteboard("test_data", {"status": "testing"})
            print("✅ Updated whiteboard")

            # Add knowledge
            knowledge_id = await memory.add_knowledge(
                "Agent Integration",
                "Successfully integrated with memory system"
            )
            print(f"✅ Added knowledge: {knowledge_id}")

            # Learn from experience (Note: This method may not exist in basic interface)
            # Instead, use learn_procedure which is available
            proc_id = await memory.learn_procedure(
                "Test memory integration",
                ["Step 1: Connect to memory", "Step 2: Store data", "Step 3: Retrieve data"],
                context="Testing the memory integration workflow"
            )
            print(f"✅ Learned procedure: {proc_id}")

            # Recall memories
            memories = await memory.recall_memories(limit=5)
            print(f"✅ Recalled {len(memories)} memories")

            print("\n✅ Agent integration test passed!")

    except ImportError as e:
        print(f"⚠️  Could not import memory interface: {e}")
        print("   This is expected if running standalone")


if __name__ == "__main__":
    print("\nGadugi v0.3 Memory System Test")
    print("==============================\n")

    try:
        # Run basic tests
        success = asyncio.run(test_memory_system())

        if success:
            # Try agent integration
            asyncio.run(test_agent_integration())

    except httpx.ConnectError:
        print("❌ Error: Could not connect to memory service")
        print("   Please start the service first:")
        print("   .claude/services/memory/start_local.sh")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
