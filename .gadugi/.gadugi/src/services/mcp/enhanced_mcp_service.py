"""
Enhanced MCP Service with Complete Memory System Integration
Implements the MCP protocol for memory operations as specified in Gadugi v0.3
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our comprehensive memory manager
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "neo4j-memory"))
from memory_manager import (  # type: ignore[import]
    MemoryManager,
    MemoryType,
)


# ========== Pydantic Models for API ==========


class MemoryCreateRequest(BaseModel):
    """Request model for creating a memory."""

    agent_id: str
    content: str
    memory_type: str = "semantic"
    is_short_term: bool = False
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    importance_score: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryResponse(BaseModel):
    """Response model for memory operations."""

    id: str
    agent_id: str
    content: str
    type: str
    scope: str
    persistence: str
    created_at: str
    importance_score: float
    access_count: int


class WhiteboardCreateRequest(BaseModel):
    """Request model for creating a whiteboard."""

    task_id: str
    agent_id: str


class WhiteboardUpdateRequest(BaseModel):
    """Request model for updating a whiteboard."""

    task_id: str
    agent_id: str
    section: str
    content: Dict[str, Any]


class KnowledgeNodeCreateRequest(BaseModel):
    """Request model for creating a knowledge node."""

    agent_id: str
    concept: str
    description: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class KnowledgeLinkRequest(BaseModel):
    """Request model for linking knowledge nodes."""

    node1_id: str
    node2_id: str
    relationship: str
    strength: float = 1.0


class ProceduralMemoryRequest(BaseModel):
    """Request model for storing procedural memory."""

    agent_id: str
    procedure_name: str
    steps: List[str]
    context: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ProjectMemoryRequest(BaseModel):
    """Request model for project shared memory."""

    project_id: str
    content: str
    created_by: str
    tags: List[str] = Field(default_factory=list)
    importance_score: float = 0.5


class MemorySearchRequest(BaseModel):
    """Request model for searching memories."""

    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    limit: int = 100


# ========== FastAPI Application ==========

app = FastAPI(
    title="Gadugi MCP Service",
    description="Memory and Context Protocol Service for Gadugi v0.3",
    version="0.3.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory manager instance
memory_manager: Optional[MemoryManager] = None


async def get_memory_manager() -> MemoryManager:
    """Dependency to get the memory manager instance."""
    global memory_manager
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    return memory_manager


@app.on_event("startup")
async def startup_event():
    """Initialize the memory manager on startup."""
    global memory_manager
    memory_manager = MemoryManager()
    if memory_manager:
        await memory_manager.connect()

    # Start background task for memory cleanup
    asyncio.create_task(periodic_memory_cleanup())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global memory_manager
    if memory_manager:
        await memory_manager.disconnect()


async def periodic_memory_cleanup():
    """Background task to clean up expired memories."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        if memory_manager:
            try:
                deleted = await memory_manager.cleanup_expired_memories()
                print(f"Cleaned up {deleted} expired memories")
            except Exception as e:
                print(f"Error during memory cleanup: {e}")


# ========== Health and Status Endpoints ==========


@app.get("/health")
async def health_check(mm: MemoryManager = Depends(get_memory_manager)):
    """Check service health and Neo4j connection."""
    try:
        # Test Neo4j connection
        if mm._driver:
            async with mm._driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.single()

        return {
            "status": "healthy",
            "service": "MCP Service",
            "neo4j": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/metrics")
async def get_metrics(mm: MemoryManager = Depends(get_memory_manager)):
    """Get service metrics."""
    try:
        async with mm._driver.session() as session:
            # Count memories by type
            result = await session.run("""
                MATCH (m:Memory)
                RETURN m.type as type, count(m) as count
            """)
            memory_counts = await result.data()

            # Count knowledge nodes
            result = await session.run("""
                MATCH (k:KnowledgeNode)
                RETURN count(k) as count
            """)
            knowledge_count = (await result.single())["count"]

            # Count whiteboards
            result = await session.run("""
                MATCH (w:Whiteboard)
                RETURN count(w) as count
            """)
            whiteboard_count = (await result.single())["count"]

        return {
            "memories_by_type": {item["type"]: item["count"] for item in memory_counts},
            "total_memories": sum(item["count"] for item in memory_counts),
            "knowledge_nodes": knowledge_count,
            "whiteboards": whiteboard_count,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# ========== Individual Agent Memory Endpoints ==========


@app.post("/memory/agent/store", response_model=MemoryResponse)
async def store_agent_memory(
    request: MemoryCreateRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Store a memory for an individual agent."""
    try:
        memory_type = MemoryType(request.memory_type)
        memory = await mm.store_agent_memory(
            agent_id=request.agent_id,
            content=request.content,
            memory_type=memory_type,
            is_short_term=request.is_short_term,
            task_id=request.task_id,
            project_id=request.project_id,
            tags=request.tags,
            importance_score=request.importance_score,
            metadata=request.metadata,
        )

        return MemoryResponse(
            id=memory.id,
            agent_id=memory.agent_id,
            content=memory.content,
            type=memory.type.value,
            scope=memory.scope.value,
            persistence=memory.persistence.value,
            created_at=memory.created_at.isoformat(),
            importance_score=memory.importance_score,
            access_count=memory.access_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@app.get("/memory/agent/{agent_id}", response_model=List[MemoryResponse])
async def get_agent_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    short_term_only: bool = False,
    long_term_only: bool = False,
    limit: int = 100,
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Retrieve memories for an agent."""
    try:
        mt = MemoryType(memory_type) if memory_type else None
        memories = await mm.get_agent_memories(
            agent_id=agent_id,
            memory_type=mt,
            short_term_only=short_term_only,
            long_term_only=long_term_only,
            limit=limit,
        )

        return [
            MemoryResponse(
                id=m.id,
                agent_id=m.agent_id,
                content=m.content,
                type=m.type.value,
                scope=m.scope.value,
                persistence=m.persistence.value,
                created_at=m.created_at.isoformat(),
                importance_score=m.importance_score,
                access_count=m.access_count,
            )
            for m in memories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve memories: {str(e)}"
        )


@app.post("/memory/agent/{agent_id}/consolidate")
async def consolidate_memories(
    agent_id: str,
    threshold_hours: int = 24,
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Consolidate short-term memories into long-term storage."""
    try:
        consolidated = await mm.consolidate_short_term_memories(
            agent_id=agent_id, threshold_hours=threshold_hours
        )

        return {
            "consolidated_count": len(consolidated),
            "memories": [m.id for m in consolidated],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to consolidate memories: {str(e)}"
        )


# ========== Project Shared Memory Endpoints ==========


@app.post("/memory/project/store", response_model=MemoryResponse)
async def store_project_memory(
    request: ProjectMemoryRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Store a project-wide shared memory."""
    try:
        memory = await mm.store_project_memory(
            project_id=request.project_id,
            content=request.content,
            created_by=request.created_by,
            tags=request.tags,
            importance_score=request.importance_score,
        )

        return MemoryResponse(
            id=memory.id,
            agent_id=memory.agent_id,
            content=memory.content,
            type=memory.type.value,
            scope=memory.scope.value,
            persistence=memory.persistence.value,
            created_at=memory.created_at.isoformat(),
            importance_score=memory.importance_score,
            access_count=memory.access_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store project memory: {str(e)}"
        )


@app.get("/memory/project/{project_id}", response_model=List[MemoryResponse])
async def get_project_memories(
    project_id: str, limit: int = 100, mm: MemoryManager = Depends(get_memory_manager)
):
    """Retrieve project-wide shared memories."""
    try:
        memories = await mm.get_project_memories(project_id=project_id, limit=limit)

        return [
            MemoryResponse(
                id=m.id,
                agent_id=m.agent_id,
                content=m.content,
                type=m.type.value,
                scope=m.scope.value,
                persistence=m.persistence.value,
                created_at=m.created_at.isoformat(),
                importance_score=m.importance_score,
                access_count=m.access_count,
            )
            for m in memories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve project memories: {str(e)}"
        )


# ========== Task Whiteboard Endpoints ==========


@app.post("/whiteboard/create")
async def create_whiteboard(
    request: WhiteboardCreateRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Create a new task whiteboard."""
    try:
        whiteboard = await mm.create_whiteboard(
            task_id=request.task_id, agent_id=request.agent_id
        )

        return {
            "id": whiteboard.id,
            "task_id": whiteboard.task_id,
            "created_by": whiteboard.created_by,
            "created_at": whiteboard.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create whiteboard: {str(e)}"
        )


@app.post("/whiteboard/update")
async def update_whiteboard(
    request: WhiteboardUpdateRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Update a task whiteboard."""
    try:
        await mm.update_whiteboard(
            task_id=request.task_id,
            agent_id=request.agent_id,
            section=request.section,
            content=request.content,
        )

        return {"status": "success", "task_id": request.task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update whiteboard: {str(e)}"
        )


@app.get("/whiteboard/{task_id}")
async def get_whiteboard(task_id: str, mm: MemoryManager = Depends(get_memory_manager)):
    """Retrieve a task whiteboard."""
    try:
        whiteboard = await mm.get_whiteboard(task_id)

        if not whiteboard:
            raise HTTPException(status_code=404, detail="Whiteboard not found")

        return {
            "id": whiteboard.id,
            "task_id": whiteboard.task_id,
            "created_by": whiteboard.created_by,
            "participants": whiteboard.participants,
            "notes": whiteboard.notes,
            "decisions": whiteboard.decisions,
            "action_items": whiteboard.action_items,
            "created_at": whiteboard.created_at.isoformat(),
            "updated_at": whiteboard.updated_at.isoformat(),
            "version": whiteboard.version,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve whiteboard: {str(e)}"
        )


# ========== Procedural Memory Endpoints ==========


@app.post("/memory/procedural/store", response_model=MemoryResponse)
async def store_procedural_memory(
    request: ProceduralMemoryRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Store procedural knowledge."""
    try:
        memory = await mm.store_procedural_memory(
            agent_id=request.agent_id,
            procedure_name=request.procedure_name,
            steps=request.steps,
            context=request.context,
            tags=request.tags,
        )

        return MemoryResponse(
            id=memory.id,
            agent_id=memory.agent_id,
            content=memory.content,
            type=memory.type.value,
            scope=memory.scope.value,
            persistence=memory.persistence.value,
            created_at=memory.created_at.isoformat(),
            importance_score=memory.importance_score,
            access_count=memory.access_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store procedural memory: {str(e)}"
        )


@app.get("/memory/procedural/{agent_id}")
async def get_procedural_memories(
    agent_id: str,
    procedure_name: Optional[str] = None,
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Retrieve procedural memories for an agent."""
    try:
        memories = await mm.get_procedural_memories(
            agent_id=agent_id, procedure_name=procedure_name
        )

        return [
            {
                "id": m.id,
                "procedure": m.structured_data.get("procedure_name")
                if m.structured_data
                else None,
                "steps": m.structured_data.get("steps") if m.structured_data else [],
                "context": m.structured_data.get("context")
                if m.structured_data
                else None,
                "access_count": m.access_count,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve procedural memories: {str(e)}"
        )


# ========== Knowledge Graph Endpoints ==========


@app.post("/knowledge/node/create")
async def create_knowledge_node(
    request: KnowledgeNodeCreateRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Add a node to an agent's knowledge graph."""
    try:
        node = await mm.add_knowledge_node(
            agent_id=request.agent_id,
            concept=request.concept,
            description=request.description,
            attributes=request.attributes,
            confidence=request.confidence,
        )

        return {
            "id": node.id,
            "agent_id": node.agent_id,
            "concept": node.concept,
            "description": node.description,
            "confidence": node.confidence,
            "created_at": node.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create knowledge node: {str(e)}"
        )


@app.post("/knowledge/link")
async def link_knowledge_nodes(
    request: KnowledgeLinkRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Create a relationship between knowledge nodes."""
    try:
        await mm.link_knowledge_nodes(
            node1_id=request.node1_id,
            node2_id=request.node2_id,
            relationship=request.relationship,
            strength=request.strength,
        )

        return {"status": "success", "linked": [request.node1_id, request.node2_id]}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to link knowledge nodes: {str(e)}"
        )


@app.get("/knowledge/graph/{agent_id}")
async def get_knowledge_graph(
    agent_id: str, max_depth: int = 2, mm: MemoryManager = Depends(get_memory_manager)
):
    """Retrieve an agent's knowledge graph."""
    try:
        graph = await mm.get_knowledge_graph(agent_id=agent_id, max_depth=max_depth)

        return graph
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve knowledge graph: {str(e)}"
        )


# ========== Memory Search Endpoints ==========


@app.post("/memory/search")
async def search_memories(
    request: MemorySearchRequest, mm: MemoryManager = Depends(get_memory_manager)
):
    """Search for memories across the system."""
    try:
        # Build search query based on parameters
        conditions = []
        params = {}

        if request.agent_id:
            conditions.append("m.agent_id = $agent_id")
            params["agent_id"] = request.agent_id

        if request.memory_type:
            conditions.append("m.type = $memory_type")
            params["memory_type"] = request.memory_type

        if request.task_id:
            conditions.append("m.task_id = $task_id")
            params["task_id"] = request.task_id

        if request.project_id:
            conditions.append("m.project_id = $project_id")
            params["project_id"] = request.project_id

        if request.tags:
            conditions.append("ANY(tag IN $tags WHERE tag IN m.tags)")
            params["tags"] = request.tags

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        MATCH (m:Memory)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.importance_score DESC, m.updated_at DESC
        LIMIT $limit
        """
        params["limit"] = request.limit

        async with mm._driver.session() as session:
            result = await session.run(query, params)
            records = await result.data()

        return [
            {
                "id": r["m"]["id"],
                "agent_id": r["m"]["agent_id"],
                "content": r["m"]["content"],
                "type": r["m"]["type"],
                "importance_score": r["m"]["importance_score"],
                "created_at": r["m"]["created_at"],
            }
            for r in records
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search memories: {str(e)}"
        )


# ========== Legacy MCP Context Endpoints (for compatibility) ==========


@app.post("/context/store")
async def store_context(
    data: Dict[str, Any], mm: MemoryManager = Depends(get_memory_manager)
):
    """Legacy endpoint for storing context (maps to memory storage)."""
    try:
        # Convert legacy context to memory
        memory = await mm.store_agent_memory(
            agent_id=data.get("agent_id", "unknown"),
            content=json.dumps(data.get("context", {})),
            memory_type=MemoryType.WORKING,
            is_short_term=True,
            metadata={"legacy_context": True},
        )

        return {"context_id": memory.id, "status": "stored"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store context: {str(e)}"
        )


@app.get("/context/retrieve/{context_id}")
async def retrieve_context(
    context_id: str, mm: MemoryManager = Depends(get_memory_manager)
):
    """Legacy endpoint for retrieving context."""
    try:
        # Retrieve as memory
        query = """
        MATCH (m:Memory {id: $context_id})
        RETURN m
        """

        async with mm._driver.session() as session:
            result = await session.run(query, {"context_id": context_id})
            record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Context not found")

        memory = record["m"]
        context = (
            json.loads(memory["content"])
            if memory["content"].startswith("{")
            else {"content": memory["content"]}
        )

        return {
            "context_id": memory["id"],
            "agent_id": memory["agent_id"],
            "context": context,
            "created_at": memory["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve context: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "enhanced_mcp_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
