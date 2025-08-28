"""
Comprehensive Memory Management System for Gadugi v0.3
Implements all required memory types per specification:
- Individual agent short and long term memory
- Project shared memory
- Task shared memory (whiteboard)
- Procedural memory
- Knowledge graph memory for each agent
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError


class MemoryType(Enum):
    """Extended memory types for comprehensive memory system."""
    
    # Individual Agent Memory
    SHORT_TERM = "short_term"          # Temporary, task-specific memories
    LONG_TERM = "long_term"            # Persistent agent memories
    EPISODIC = "episodic"              # Specific events and interactions
    SEMANTIC = "semantic"              # Facts and general knowledge
    PROCEDURAL = "procedural"          # How-to knowledge and skills
    WORKING = "working"                # Current task context
    
    # Shared Memory Spaces
    PROJECT_SHARED = "project_shared"  # Project-wide shared knowledge
    TASK_WHITEBOARD = "task_whiteboard"  # Task-specific shared workspace
    TEAM_KNOWLEDGE = "team_knowledge"  # Team-level shared knowledge
    
    # Knowledge Graph
    KNOWLEDGE_NODE = "knowledge_node"  # Node in agent's knowledge graph
    KNOWLEDGE_EDGE = "knowledge_edge"  # Relationship in knowledge graph


class MemoryScope(Enum):
    """Scope/visibility of memories."""
    
    PRIVATE = "private"        # Only accessible to owning agent
    TASK = "task"             # Shared within task context
    TEAM = "team"             # Shared within team
    PROJECT = "project"       # Shared across project
    GLOBAL = "global"         # Globally accessible


class MemoryPersistence(Enum):
    """Persistence levels for memories."""
    
    VOLATILE = "volatile"      # Lost on restart (short-term)
    SESSION = "session"        # Persists for session
    PERSISTENT = "persistent"  # Long-term storage
    ARCHIVED = "archived"      # Historical archive


@dataclass
class Memory:
    """Enhanced memory structure with all required fields."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.SEMANTIC
    scope: MemoryScope = MemoryScope.PRIVATE
    persistence: MemoryPersistence = MemoryPersistence.SESSION
    
    # Ownership and context
    agent_id: str = ""
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    team_id: Optional[str] = None
    
    # Content
    content: str = ""
    structured_data: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5
    confidence_score: float = 1.0
    decay_rate: float = 0.1  # For short-term memory decay
    
    # Access tracking
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Relationships
    parent_id: Optional[str] = None
    associations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    
    # Version control
    version: int = 1
    is_active: bool = True


@dataclass
class KnowledgeNode:
    """Node in an agent's knowledge graph."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    concept: str = ""
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Graph relationships
    related_concepts: List[str] = field(default_factory=list)
    parent_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)
    
    # Source tracking
    source_memories: List[str] = field(default_factory=list)
    source_tasks: List[str] = field(default_factory=list)


@dataclass
class Whiteboard:
    """Task-specific shared workspace for collaboration."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    created_by: str = ""  # Agent ID
    
    # Content sections
    notes: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    code_snippets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    participants: List[str] = field(default_factory=list)  # Agent IDs
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Version control
    version: int = 1
    history: List[Dict[str, Any]] = field(default_factory=list)


class MemoryManager:
    """Comprehensive memory management system for Gadugi."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "gadugi123!",
        database: str = "neo4j"
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[AsyncDriver] = None
        
    async def connect(self) -> None:
        """Connect to Neo4j database."""
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            await self._initialize_schema()
    
    async def disconnect(self) -> None:
        """Disconnect from Neo4j database."""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    async def _initialize_schema(self) -> None:
        """Initialize or update the database schema."""
        if not self._driver:
            return
            
        async with self._driver.session(database=self.database) as session:
            # Create constraints and indexes
            queries = [
                # Memory constraints
                "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE INDEX memory_agent IF NOT EXISTS FOR (m:Memory) ON (m.agent_id)",
                "CREATE INDEX memory_type IF NOT EXISTS FOR (m:Memory) ON (m.type)",
                "CREATE INDEX memory_scope IF NOT EXISTS FOR (m:Memory) ON (m.scope)",
                "CREATE INDEX memory_task IF NOT EXISTS FOR (m:Memory) ON (m.task_id)",
                
                # Knowledge graph constraints
                "CREATE CONSTRAINT knowledge_id IF NOT EXISTS FOR (k:KnowledgeNode) REQUIRE k.id IS UNIQUE",
                "CREATE INDEX knowledge_agent IF NOT EXISTS FOR (k:KnowledgeNode) ON (k.agent_id)",
                "CREATE INDEX knowledge_concept IF NOT EXISTS FOR (k:KnowledgeNode) ON (k.concept)",
                
                # Whiteboard constraints
                "CREATE CONSTRAINT whiteboard_id IF NOT EXISTS FOR (w:Whiteboard) REQUIRE w.id IS UNIQUE",
                "CREATE INDEX whiteboard_task IF NOT EXISTS FOR (w:Whiteboard) ON (w.task_id)",
            ]
            
            for query in queries:
                try:
                    await session.run(query)
                except Neo4jError as e:
                    # Ignore if already exists
                    if "already exists" not in str(e).lower():
                        raise
    
    # ========== Individual Agent Memory Management ==========
    
    async def store_agent_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: MemoryType,
        is_short_term: bool = False,
        **kwargs
    ) -> Memory:
        """Store a memory for an individual agent.
        
        Args:
            agent_id: ID of the agent
            content: Memory content
            memory_type: Type of memory
            is_short_term: Whether this is short-term (volatile) or long-term memory
            **kwargs: Additional memory attributes
        """
        memory = Memory(
            agent_id=agent_id,
            content=content,
            type=memory_type,
            persistence=MemoryPersistence.VOLATILE if is_short_term else MemoryPersistence.PERSISTENT,
            scope=MemoryScope.PRIVATE,
            **kwargs
        )
        
        if is_short_term:
            # Set expiration for short-term memories
            memory.expires_at = datetime.now() + timedelta(hours=24)
            memory.decay_rate = 0.2
        
        await self._store_memory(memory)
        return memory
    
    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 100
    ) -> List[Memory]:
        """Retrieve memories for an agent.
        
        Args:
            agent_id: ID of the agent
            memory_type: Optional filter by memory type
            short_term_only: Only retrieve short-term memories
            long_term_only: Only retrieve long-term memories
            limit: Maximum number of memories to retrieve
        """
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (m:Memory {agent_id: $agent_id})
        WHERE m.is_active = true
        """
        
        params = {"agent_id": agent_id}
        
        if memory_type:
            query += " AND m.type = $memory_type"
            params["memory_type"] = memory_type.value
        
        if short_term_only:
            query += " AND m.persistence = 'volatile'"
        elif long_term_only:
            query += " AND m.persistence = 'persistent'"
        
        query += """
        RETURN m
        ORDER BY m.updated_at DESC
        LIMIT $limit
        """
        params["limit"] = limit
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
            
        return [self._record_to_memory(r["m"]) for r in records]
    
    async def consolidate_short_term_memories(
        self,
        agent_id: str,
        threshold_hours: int = 24
    ) -> List[Memory]:
        """Consolidate short-term memories into long-term memories.
        
        This simulates memory consolidation where important short-term
        memories are converted to long-term storage.
        """
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        cutoff = datetime.now() - timedelta(hours=threshold_hours)
        
        query = """
        MATCH (m:Memory {agent_id: $agent_id, persistence: 'volatile'})
        WHERE m.created_at < $cutoff
        AND m.importance_score >= 0.7
        AND m.access_count >= 2
        SET m.persistence = 'persistent',
            m.type = 'long_term',
            m.updated_at = $now
        RETURN m
        """
        
        params = {
            "agent_id": agent_id,
            "cutoff": cutoff.isoformat(),
            "now": datetime.now().isoformat()
        }
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
        
        return [self._record_to_memory(r["m"]) for r in records]
    
    # ========== Project Shared Memory ==========
    
    async def store_project_memory(
        self,
        project_id: str,
        content: str,
        created_by: str,
        **kwargs
    ) -> Memory:
        """Store a project-wide shared memory."""
        memory = Memory(
            project_id=project_id,
            agent_id=created_by,
            content=content,
            type=MemoryType.PROJECT_SHARED,
            scope=MemoryScope.PROJECT,
            persistence=MemoryPersistence.PERSISTENT,
            **kwargs
        )
        
        await self._store_memory(memory)
        return memory
    
    async def get_project_memories(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[Memory]:
        """Retrieve project-wide shared memories."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (m:Memory {project_id: $project_id, type: 'project_shared'})
        WHERE m.is_active = true
        RETURN m
        ORDER BY m.importance_score DESC, m.updated_at DESC
        LIMIT $limit
        """
        
        params = {"project_id": project_id, "limit": limit}
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
        
        return [self._record_to_memory(r["m"]) for r in records]
    
    # ========== Task Whiteboard (Shared Workspace) ==========
    
    async def create_whiteboard(
        self,
        task_id: str,
        agent_id: str
    ) -> Whiteboard:
        """Create a new task whiteboard."""
        whiteboard = Whiteboard(
            task_id=task_id,
            created_by=agent_id,
            participants=[agent_id]
        )
        
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        CREATE (w:Whiteboard {
            id: $id,
            task_id: $task_id,
            created_by: $created_by,
            participants: $participants,
            notes: $notes,
            decisions: $decisions,
            action_items: $action_items,
            created_at: $created_at,
            updated_at: $updated_at,
            version: $version
        })
        RETURN w
        """
        
        params = {
            "id": whiteboard.id,
            "task_id": whiteboard.task_id,
            "created_by": whiteboard.created_by,
            "participants": whiteboard.participants,
            "notes": json.dumps(whiteboard.notes),
            "decisions": json.dumps(whiteboard.decisions),
            "action_items": json.dumps(whiteboard.action_items),
            "created_at": whiteboard.created_at.isoformat(),
            "updated_at": whiteboard.updated_at.isoformat(),
            "version": whiteboard.version
        }
        
        async with self._driver.session(database=self.database) as session:
            await session.run(query, params)
        
        return whiteboard
    
    async def update_whiteboard(
        self,
        task_id: str,
        agent_id: str,
        section: str,
        content: Dict[str, Any]
    ) -> None:
        """Update a section of the task whiteboard."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        valid_sections = ["notes", "decisions", "action_items", "diagrams", "code_snippets"]
        if section not in valid_sections:
            raise ValueError(f"Invalid section: {section}")
        
        query = f"""
        MATCH (w:Whiteboard {{task_id: $task_id}})
        SET w.{section} = w.{section} + [$content],
            w.updated_at = $updated_at,
            w.version = w.version + 1
        WHERE NOT $agent_id IN w.participants
        SET w.participants = w.participants + [$agent_id]
        RETURN w
        """
        
        params = {
            "task_id": task_id,
            "agent_id": agent_id,
            "content": json.dumps({
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "content": content
            }),
            "updated_at": datetime.now().isoformat()
        }
        
        async with self._driver.session(database=self.database) as session:
            await session.run(query, params)
    
    async def get_whiteboard(self, task_id: str) -> Optional[Whiteboard]:
        """Retrieve a task whiteboard."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (w:Whiteboard {task_id: $task_id})
        RETURN w
        """
        
        params = {"task_id": task_id}
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
        
        if not records:
            return None
        
        record = records[0]["w"]
        return Whiteboard(
            id=record["id"],
            task_id=record["task_id"],
            created_by=record["created_by"],
            participants=record["participants"],
            notes=json.loads(record.get("notes", "[]")),
            decisions=json.loads(record.get("decisions", "[]")),
            action_items=json.loads(record.get("action_items", "[]")),
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
            version=record["version"]
        )
    
    # ========== Procedural Memory ==========
    
    async def store_procedural_memory(
        self,
        agent_id: str,
        procedure_name: str,
        steps: List[str],
        context: Optional[str] = None,
        **kwargs
    ) -> Memory:
        """Store procedural knowledge (how-to information)."""
        structured_data = {
            "procedure_name": procedure_name,
            "steps": steps,
            "context": context
        }
        
        memory = Memory(
            agent_id=agent_id,
            content=f"Procedure: {procedure_name}",
            structured_data=structured_data,
            type=MemoryType.PROCEDURAL,
            persistence=MemoryPersistence.PERSISTENT,
            scope=MemoryScope.PRIVATE,
            **kwargs
        )
        
        await self._store_memory(memory)
        return memory
    
    async def get_procedural_memories(
        self,
        agent_id: str,
        procedure_name: Optional[str] = None
    ) -> List[Memory]:
        """Retrieve procedural memories for an agent."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (m:Memory {agent_id: $agent_id, type: 'procedural'})
        WHERE m.is_active = true
        """
        
        params = {"agent_id": agent_id}
        
        if procedure_name:
            query += " AND m.content CONTAINS $procedure_name"
            params["procedure_name"] = procedure_name
        
        query += """
        RETURN m
        ORDER BY m.access_count DESC, m.updated_at DESC
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
        
        return [self._record_to_memory(r["m"]) for r in records]
    
    # ========== Knowledge Graph Management ==========
    
    async def add_knowledge_node(
        self,
        agent_id: str,
        concept: str,
        description: str,
        **kwargs
    ) -> KnowledgeNode:
        """Add a node to an agent's knowledge graph."""
        node = KnowledgeNode(
            agent_id=agent_id,
            concept=concept,
            description=description,
            **kwargs
        )
        
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        CREATE (k:KnowledgeNode {
            id: $id,
            agent_id: $agent_id,
            concept: $concept,
            description: $description,
            attributes: $attributes,
            confidence: $confidence,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN k
        """
        
        params = {
            "id": node.id,
            "agent_id": node.agent_id,
            "concept": node.concept,
            "description": node.description,
            "attributes": json.dumps(node.attributes),
            "confidence": node.confidence,
            "created_at": node.created_at.isoformat(),
            "updated_at": node.updated_at.isoformat()
        }
        
        async with self._driver.session(database=self.database) as session:
            await session.run(query, params)
        
        return node
    
    async def link_knowledge_nodes(
        self,
        node1_id: str,
        node2_id: str,
        relationship: str,
        strength: float = 1.0
    ) -> None:
        """Create a relationship between knowledge nodes."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (k1:KnowledgeNode {id: $node1_id})
        MATCH (k2:KnowledgeNode {id: $node2_id})
        CREATE (k1)-[r:RELATES_TO {
            type: $relationship,
            strength: $strength,
            created_at: $created_at
        }]->(k2)
        """
        
        params = {
            "node1_id": node1_id,
            "node2_id": node2_id,
            "relationship": relationship,
            "strength": strength,
            "created_at": datetime.now().isoformat()
        }
        
        async with self._driver.session(database=self.database) as session:
            await session.run(query, params)
    
    async def get_knowledge_graph(
        self,
        agent_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Retrieve an agent's knowledge graph."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (k:KnowledgeNode {agent_id: $agent_id})
        OPTIONAL MATCH path = (k)-[r:RELATES_TO*1..""" + str(max_depth) + """]->(related)
        RETURN k, relationships(path) as rels, nodes(path) as nodes
        """
        
        params = {"agent_id": agent_id}
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, params)
            records = await result.data()
        
        # Build graph structure
        nodes = {}
        edges = []
        
        for record in records:
            # Add main node
            k = record["k"]
            if k["id"] not in nodes:
                nodes[k["id"]] = {
                    "id": k["id"],
                    "concept": k["concept"],
                    "description": k["description"],
                    "confidence": k["confidence"]
                }
            
            # Add related nodes and edges
            if record["nodes"]:
                for node in record["nodes"]:
                    if node["id"] not in nodes:
                        nodes[node["id"]] = {
                            "id": node["id"],
                            "concept": node["concept"],
                            "description": node["description"],
                            "confidence": node["confidence"]
                        }
            
            if record["rels"]:
                for rel in record["rels"]:
                    edges.append({
                        "from": rel.start_node["id"],
                        "to": rel.end_node["id"],
                        "type": rel["type"],
                        "strength": rel["strength"]
                    })
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    # ========== Helper Methods ==========
    
    async def _store_memory(self, memory: Memory) -> None:
        """Store a memory in Neo4j."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        CREATE (m:Memory {
            id: $id,
            type: $type,
            scope: $scope,
            persistence: $persistence,
            agent_id: $agent_id,
            task_id: $task_id,
            project_id: $project_id,
            team_id: $team_id,
            content: $content,
            structured_data: $structured_data,
            tags: $tags,
            metadata: $metadata,
            importance_score: $importance_score,
            confidence_score: $confidence_score,
            decay_rate: $decay_rate,
            access_count: $access_count,
            created_at: $created_at,
            updated_at: $updated_at,
            expires_at: $expires_at,
            version: $version,
            is_active: $is_active
        })
        RETURN m
        """
        
        params = {
            "id": memory.id,
            "type": memory.type.value,
            "scope": memory.scope.value,
            "persistence": memory.persistence.value,
            "agent_id": memory.agent_id,
            "task_id": memory.task_id,
            "project_id": memory.project_id,
            "team_id": memory.team_id,
            "content": memory.content,
            "structured_data": json.dumps(memory.structured_data) if memory.structured_data else None,
            "tags": memory.tags,
            "metadata": json.dumps(memory.metadata),
            "importance_score": memory.importance_score,
            "confidence_score": memory.confidence_score,
            "decay_rate": memory.decay_rate,
            "access_count": memory.access_count,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
            "version": memory.version,
            "is_active": memory.is_active
        }
        
        async with self._driver.session(database=self.database) as session:
            await session.run(query, params)
    
    def _record_to_memory(self, record: Dict[str, Any]) -> Memory:
        """Convert a Neo4j record to a Memory object."""
        return Memory(
            id=record["id"],
            type=MemoryType(record["type"]),
            scope=MemoryScope(record["scope"]),
            persistence=MemoryPersistence(record["persistence"]),
            agent_id=record["agent_id"],
            task_id=record.get("task_id"),
            project_id=record.get("project_id"),
            team_id=record.get("team_id"),
            content=record["content"],
            structured_data=json.loads(record["structured_data"]) if record.get("structured_data") else None,
            tags=record.get("tags", []),
            metadata=json.loads(record.get("metadata", "{}")),
            importance_score=record["importance_score"],
            confidence_score=record["confidence_score"],
            decay_rate=record["decay_rate"],
            access_count=record["access_count"],
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
            expires_at=datetime.fromisoformat(record["expires_at"]) if record.get("expires_at") else None,
            version=record["version"],
            is_active=record["is_active"]
        )
    
    async def cleanup_expired_memories(self) -> int:
        """Remove expired short-term memories."""
        if not self._driver:
            raise RuntimeError("Not connected to database")
        
        query = """
        MATCH (m:Memory)
        WHERE m.expires_at IS NOT NULL
        AND datetime(m.expires_at) < datetime()
        DELETE m
        RETURN count(m) as deleted_count
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query)
            record = await result.single()
        
        return record["deleted_count"] if record else 0