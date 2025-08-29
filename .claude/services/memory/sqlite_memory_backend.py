#!/usr/bin/env python3
"""
SQLite-based memory backend for Gadugi v0.3.
This is a lightweight alternative to Neo4j for testing without Docker.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiosqlite


class SQLiteMemoryBackend:
    """SQLite-based memory storage for testing without Neo4j."""

    def __init__(self, db_path: str = ".claude/data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create memories table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    importance_score REAL DEFAULT 0.5,
                    task_id TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create knowledge nodes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    description TEXT,
                    confidence REAL DEFAULT 0.5,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create knowledge edges table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES knowledge_nodes(id),
                    FOREIGN KEY (target_id) REFERENCES knowledge_nodes(id)
                )
            """)

            # Create whiteboards table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS whiteboards (
                    id TEXT PRIMARY KEY,
                    task_id TEXT UNIQUE NOT NULL,
                    agent_id TEXT NOT NULL,
                    content TEXT DEFAULT '{}',
                    decisions TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create procedures table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    procedure_name TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    context TEXT,
                    success_rate REAL DEFAULT 0.0,
                    execution_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indices
            await db.execute("CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_memories_task ON memories(task_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_agent ON knowledge_nodes(agent_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_whiteboard_task ON whiteboards(task_id)")

            await db.commit()

    async def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str,
        task_id: Optional[str] = None,
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory."""
        memory_id = str(uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO memories (id, agent_id, content, memory_type, timestamp,
                                     importance_score, task_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                agent_id,
                content,
                memory_type,
                datetime.utcnow().isoformat(),
                importance_score,
                task_id,
                json.dumps(metadata) if metadata else None
            ))
            await db.commit()

        return memory_id

    async def get_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve memories."""
        query = "SELECT * FROM memories WHERE agent_id = ?"
        params = [agent_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def create_whiteboard(self, task_id: str, agent_id: str) -> str:
        """Create a whiteboard for a task."""
        whiteboard_id = str(uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO whiteboards (id, task_id, agent_id)
                VALUES (?, ?, ?)
            """, (whiteboard_id, task_id, agent_id))
            await db.commit()

        return whiteboard_id

    async def update_whiteboard(
        self,
        task_id: str,
        content: Optional[Dict[str, Any]] = None,
        decision: Optional[str] = None
    ) -> bool:
        """Update whiteboard content."""
        async with aiosqlite.connect(self.db_path) as db:
            if content:
                await db.execute("""
                    UPDATE whiteboards
                    SET content = ?, updated_at = ?
                    WHERE task_id = ?
                """, (json.dumps(content), datetime.utcnow().isoformat(), task_id))

            if decision:
                # Get current decisions
                async with db.execute(
                    "SELECT decisions FROM whiteboards WHERE task_id = ?", (task_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        decisions = json.loads(row[0])
                        decisions.append({
                            "decision": decision,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        await db.execute("""
                            UPDATE whiteboards
                            SET decisions = ?, updated_at = ?
                            WHERE task_id = ?
                        """, (json.dumps(decisions), datetime.utcnow().isoformat(), task_id))

            await db.commit()

        return True

    async def get_whiteboard(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get whiteboard content."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM whiteboards WHERE task_id = ?", (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    result = dict(row)
                    result['content'] = json.loads(result['content'])
                    result['decisions'] = json.loads(result['decisions'])
                    return result
        return None

    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: Optional[str] = None,
        confidence: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a knowledge node."""
        node_id = str(uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO knowledge_nodes (id, agent_id, concept, description, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                node_id,
                agent_id,
                concept,
                description,
                confidence,
                json.dumps(metadata) if metadata else None
            ))
            await db.commit()

        return node_id

    async def add_knowledge_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        weight: float = 1.0
    ) -> str:
        """Add a knowledge edge."""
        edge_id = str(uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO knowledge_edges (id, source_id, target_id, relationship, weight)
                VALUES (?, ?, ?, ?, ?)
            """, (edge_id, source_id, target_id, relationship, weight))
            await db.commit()

        return edge_id

    async def get_knowledge_graph(self, agent_id: str) -> Dict[str, Any]:
        """Get knowledge graph for an agent."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get nodes
            async with db.execute(
                "SELECT * FROM knowledge_nodes WHERE agent_id = ?", (agent_id,)
            ) as cursor:
                nodes = [dict(row) for row in await cursor.fetchall()]

            # Get edges for these nodes
            node_ids = [n['id'] for n in nodes]
            if node_ids:
                placeholders = ','.join('?' * len(node_ids))
                async with db.execute(
                    f"SELECT * FROM knowledge_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    node_ids + node_ids
                ) as cursor:
                    edges = [dict(row) for row in await cursor.fetchall()]
            else:
                edges = []

        return {
            "agent_id": agent_id,
            "nodes": nodes,
            "edges": edges
        }

    async def store_procedure(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None
    ) -> str:
        """Store a procedure."""
        procedure_id = str(uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO procedures (id, agent_id, procedure_name, steps, context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                procedure_id,
                agent_id,
                procedure_name,
                json.dumps(steps),
                context
            ))
            await db.commit()

        return procedure_id

    async def get_procedures(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get procedures for an agent."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM procedures WHERE agent_id = ? ORDER BY success_rate DESC",
                (agent_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                procedures = []
                for row in rows:
                    proc = dict(row)
                    proc['steps'] = json.loads(proc['steps'])
                    procedures.append(proc)
                return procedures

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Count memories by type
            async with db.execute("""
                SELECT memory_type, COUNT(*) as count
                FROM memories
                GROUP BY memory_type
            """) as cursor:
                memory_counts = dict(await cursor.fetchall())

            # Total counts
            for table in ['memories', 'knowledge_nodes', 'knowledge_edges', 'whiteboards', 'procedures']:
                async with db.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                    count = await cursor.fetchone()
                    stats[f'total_{table}'] = count[0]

            stats['memory_types'] = memory_counts

            return stats


async def test_sqlite_backend():
    """Test the SQLite memory backend."""
    print("Testing SQLite Memory Backend...")

    # Initialize backend
    backend = SQLiteMemoryBackend()
    await backend.initialize()
    print("✅ Database initialized")

    # Test storing memories
    agent_id = "test_agent_001"
    task_id = "task_001"

    # Store different memory types
    mem1 = await backend.store_memory(
        agent_id, "Starting test task", "short_term", task_id, 0.8
    )
    print(f"✅ Stored short-term memory: {mem1}")

    mem2 = await backend.store_memory(
        agent_id, "Learned SQLite is working", "long_term", importance_score=0.9
    )
    print(f"✅ Stored long-term memory: {mem2}")

    # Create whiteboard
    wb_id = await backend.create_whiteboard(task_id, agent_id)
    print(f"✅ Created whiteboard: {wb_id}")

    # Update whiteboard
    await backend.update_whiteboard(
        task_id,
        content={"notes": "Testing memory system", "status": "in_progress"},
        decision="Use SQLite for local testing"
    )
    print("✅ Updated whiteboard")

    # Add knowledge
    node1 = await backend.add_knowledge_node(
        agent_id, "SQLite", "Lightweight database for testing", confidence=0.95
    )
    node2 = await backend.add_knowledge_node(
        agent_id, "Memory System", "Stores agent memories", confidence=0.9
    )
    edge = await backend.add_knowledge_edge(
        node1, node2, "used_by", weight=0.8
    )
    print(f"✅ Added knowledge nodes and edge")

    # Store procedure
    proc_id = await backend.store_procedure(
        agent_id,
        "test_memory_system",
        ["Initialize backend", "Store memories", "Create whiteboard", "Add knowledge"],
        context="Testing Gadugi v0.3"
    )
    print(f"✅ Stored procedure: {proc_id}")

    # Retrieve data
    memories = await backend.get_memories(agent_id)
    print(f"✅ Retrieved {len(memories)} memories")

    whiteboard = await backend.get_whiteboard(task_id)
    print(f"✅ Retrieved whiteboard: {whiteboard['content']}")

    graph = await backend.get_knowledge_graph(agent_id)
    print(f"✅ Retrieved knowledge graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    procedures = await backend.get_procedures(agent_id)
    print(f"✅ Retrieved {len(procedures)} procedures")

    # Get stats
    stats = await backend.get_stats()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_sqlite_backend())
