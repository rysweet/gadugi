#!/usr/bin/env python3
"""
Simple MCP service using SQLite backend for testing without Docker/Neo4j.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sqlite_memory_backend import SQLiteMemoryBackend


# Pydantic models
class MemoryStoreRequest(BaseModel):
    agent_id: str
    content: str
    memory_type: str = "semantic"
    task_id: Optional[str] = None
    importance_score: float = 0.5
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(BaseModel):
    id: str
    agent_id: str
    content: str
    memory_type: str
    timestamp: str
    importance_score: float
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WhiteboardCreateRequest(BaseModel):
    task_id: str
    agent_id: str


class WhiteboardUpdateRequest(BaseModel):
    content: Optional[Dict[str, Any]] = None
    decision: Optional[str] = None


class KnowledgeNodeRequest(BaseModel):
    agent_id: str
    concept: str
    description: Optional[str] = None
    confidence: float = 0.5
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    relationship: str
    weight: float = 1.0


class ProcedureStoreRequest(BaseModel):
    agent_id: str
    procedure_name: str
    steps: List[str]
    context: Optional[str] = None


# Global backend instance
backend = SQLiteMemoryBackend()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize backend on startup."""
    await backend.initialize()
    print("✅ SQLite memory backend initialized")
    yield
    print("Shutting down memory service")


# Create FastAPI app
app = FastAPI(
    title="Gadugi Memory Service (SQLite)",
    description="Lightweight memory service for testing Gadugi v0.3 without Docker",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = await backend.get_stats()
        return {
            "status": "healthy",
            "backend": "sqlite",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/memory/agent/store", response_model=Dict[str, str])
async def store_agent_memory(request: MemoryStoreRequest):
    """Store agent memory."""
    try:
        memory_id = await backend.store_memory(
            agent_id=request.agent_id,
            content=request.content,
            memory_type=request.memory_type,
            task_id=request.task_id,
            importance_score=request.importance_score,
            metadata=request.metadata,
        )
        return {"id": memory_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/agent/{agent_id}")
async def get_agent_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 100,
):
    """Get agent memories."""
    try:
        memories = await backend.get_memories(
            agent_id=agent_id, memory_type=memory_type, task_id=task_id, limit=limit
        )
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/whiteboard/create")
async def create_whiteboard(request: WhiteboardCreateRequest):
    """Create a whiteboard."""
    try:
        whiteboard_id = await backend.create_whiteboard(
            task_id=request.task_id, agent_id=request.agent_id
        )
        return {"id": whiteboard_id, "task_id": request.task_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/whiteboard/update/{task_id}")
async def update_whiteboard(task_id: str, request: WhiteboardUpdateRequest):
    """Update whiteboard."""
    try:
        success = await backend.update_whiteboard(
            task_id=task_id, content=request.content, decision=request.decision
        )
        return {"task_id": task_id, "status": "updated" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whiteboard/{task_id}")
async def get_whiteboard(task_id: str):
    """Get whiteboard content."""
    try:
        whiteboard = await backend.get_whiteboard(task_id)
        if not whiteboard:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        return whiteboard
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge/node/create")
async def create_knowledge_node(request: KnowledgeNodeRequest):
    """Create knowledge node."""
    try:
        node_id = await backend.add_knowledge_node(
            agent_id=request.agent_id,
            concept=request.concept,
            description=request.description,
            confidence=request.confidence,
            metadata=request.metadata,
        )
        return {"id": node_id, "concept": request.concept, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge/edge/create")
async def create_knowledge_edge(request: KnowledgeEdgeRequest):
    """Create knowledge edge."""
    try:
        edge_id = await backend.add_knowledge_edge(
            source_id=request.source_id,
            target_id=request.target_id,
            relationship=request.relationship,
            weight=request.weight,
        )
        return {
            "id": edge_id,
            "relationship": request.relationship,
            "status": "created",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/graph/{agent_id}")
async def get_knowledge_graph(agent_id: str):
    """Get knowledge graph."""
    try:
        graph = await backend.get_knowledge_graph(agent_id)
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/procedural/store")
async def store_procedure(request: ProcedureStoreRequest):
    """Store procedure."""
    try:
        procedure_id = await backend.store_procedure(
            agent_id=request.agent_id,
            procedure_name=request.procedure_name,
            steps=request.steps,
            context=request.context,
        )
        return {
            "id": procedure_id,
            "procedure_name": request.procedure_name,
            "status": "stored",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/procedural/{agent_id}")
async def get_procedures(agent_id: str):
    """Get procedures."""
    try:
        procedures = await backend.get_procedures(agent_id)
        return procedures
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    try:
        stats = await backend.get_stats()
        return {"timestamp": datetime.utcnow().isoformat(), "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Alias endpoints for compatibility
@app.post("/memory/project/store")
async def store_project_memory(request: MemoryStoreRequest):
    """Store project-level memory (alias)."""
    request.memory_type = "project_shared"
    return await store_agent_memory(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
