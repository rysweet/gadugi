#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Service for Gadugi v0.3
A REAL, working FastAPI service that integrates with Neo4j for context storage
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field
import uvicorn


# Pydantic Models for MCP Protocol
class ContextCreateRequest(BaseModel):
    """Request model for storing context"""
    content: str = Field(..., description="The context content to store")
    source: str = Field(..., description="Source of the context (e.g., agent name)")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    tags: Optional[List[str]] = Field(default=[], description="Tags for categorization")


class ContextResponse(BaseModel):
    """Response model for context operations"""
    id: str = Field(..., description="Unique context ID")
    content: str = Field(..., description="The context content")
    source: str = Field(..., description="Source of the context")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    timestamp: str = Field(..., description="ISO format timestamp")
    relationships: List[Dict[str, str]] = Field(default=[], description="Related contexts")


class ContextSearchRequest(BaseModel):
    """Request model for searching contexts"""
    query: str = Field(..., description="Search query")
    source: Optional[str] = Field(None, description="Filter by source")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    neo4j_connected: bool = Field(..., description="Neo4j connection status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Service version")


class MetricsResponse(BaseModel):
    """Service metrics response"""
    total_contexts: int = Field(..., description="Total number of stored contexts")
    total_agents: int = Field(..., description="Total number of agents")
    total_relationships: int = Field(..., description="Total number of relationships")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


# Neo4j Database Manager
class Neo4jManager:
    """Manages Neo4j connections and operations"""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    async def connect(self):
        """Initialize async connection to Neo4j"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        # Test connection
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 as test")
            test = await result.single()
            if test["test"] != 1:  # type: ignore
                raise Exception("Neo4j connection test failed")

    async def close(self):
        """Close the driver connection"""
        if self.driver:
            await self.driver.close()

    async def store_context(self, context: ContextCreateRequest) -> str:
        """Store context in Neo4j"""
        context_id = f"ctx-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat()

        async with self.driver.session() as session:  # type: ignore
            result = await session.run("""
                CREATE (c:Context {
                    id: $id,
                    content: $content,
                    source: $source,
                    timestamp: $timestamp,
                    metadata: $metadata,
                    tags: $tags
                })
                RETURN c.id as id
            """, id=context_id, content=context.content, source=context.source,
                timestamp=timestamp, metadata=dict(context.metadata or {}),
                tags=context.tags or [])

            _record = await result.single()

            # Create relationship to source agent if exists
            await session.run("""
                MATCH (a:Agent {name: $source})
                MATCH (c:Context {id: $id})
                CREATE (a)-[:CREATED]->(c)
            """, source=context.source, id=context_id)

            return context_id

    async def retrieve_context(self, context_id: str) -> Optional[ContextResponse]:
        """Retrieve context by ID"""
        async with self.driver.session() as session:  # type: ignore
            result = await session.run("""
                MATCH (c:Context {id: $id})
                OPTIONAL MATCH (c)-[r]-(related)
                RETURN c, collect({type: type(r), node: related.id}) as relationships
            """, id=context_id)

            record = await result.single()
            if not record:
                return None

            context_node = record["c"]
            relationships = record["relationships"]

            return ContextResponse(
                id=context_node["id"],
                content=context_node["content"],
                source=context_node["source"],
                metadata=dict(context_node.get("metadata", {})),
                tags=list(context_node.get("tags", [])),
                timestamp=context_node["timestamp"],
                relationships=[r for r in relationships if r["node"]]
            )

    async def search_contexts(self, search_req: ContextSearchRequest) -> List[ContextResponse]:
        """Search contexts with filters"""
        # Build WHERE clause
        where_clauses = []
        params = {"limit": search_req.limit}

        if search_req.query:
            where_clauses.append("c.content CONTAINS $query")
            params["query"] = search_req.query

        if search_req.source:
            where_clauses.append("c.source = $source")
            params["source"] = search_req.source

        if search_req.tags:
            where_clauses.append("any(tag IN $tags WHERE tag IN c.tags)")
            params["tags"] = search_req.tags

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with self.driver.session() as session:  # type: ignore
            result = await session.run(f"""
                MATCH (c:Context)
                WHERE {where_clause}
                RETURN c
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, **params)

            contexts = []
            async for record in result:
                context_node = record["c"]
                contexts.append(ContextResponse(
                    id=context_node["id"],
                    content=context_node["content"],
                    source=context_node["source"],
                    metadata=dict(context_node.get("metadata", {})),
                    tags=list(context_node.get("tags", [])),
                    timestamp=context_node["timestamp"],
                    relationships=[]
                ))

            return contexts

    async def get_metrics(self) -> Dict[str, int]:
        """Get database metrics"""
        async with self.driver.session() as session:  # type: ignore
            # Count contexts
            contexts_result = await session.run("MATCH (c:Context) RETURN count(c) as count")
            contexts_count = (await contexts_result.single())["count"]  # type: ignore

            # Count agents
            agents_result = await session.run("MATCH (a:Agent) RETURN count(a) as count")
            agents_count = (await agents_result.single())["count"]  # type: ignore

            # Count relationships
            rels_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rels_count = (await rels_result.single())["count"]  # type: ignore

            return {
                "total_contexts": contexts_count,
                "total_agents": agents_count,
                "total_relationships": rels_count
            }


# Global database manager
db_manager: Optional[Neo4jManager] = None
start_time = datetime.utcnow()


# FastAPI Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global db_manager

    # Startup
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7689")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "gadugi-password")

    db_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
    await db_manager.connect()
    print(f"✅ Connected to Neo4j at {neo4j_uri}")

    yield

    # Shutdown
    if db_manager:
        await db_manager.close()
        print("✅ Disconnected from Neo4j")


# Create FastAPI app
app = FastAPI(
    title="Gadugi MCP Service",
    description="Model Context Protocol service for Gadugi v0.3",
    version="0.3.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints
@app.post("/context/store", response_model=ContextResponse, status_code=status.HTTP_201_CREATED)
async def store_context(request: ContextCreateRequest):
    """Store a new context in Neo4j"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        context_id = await db_manager.store_context(request)
        stored_context = await db_manager.retrieve_context(context_id)
        if not stored_context:
            raise HTTPException(status_code=500, detail="Failed to store context")
        return stored_context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/retrieve/{context_id}", response_model=ContextResponse)
async def retrieve_context(context_id: str):
    """Retrieve context by ID"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")

    context = await db_manager.retrieve_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context


@app.post("/context/search", response_model=List[ContextResponse])
async def search_contexts(request: ContextSearchRequest):
    """Search contexts with filters"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        contexts = await db_manager.search_contexts(request)
        return contexts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    neo4j_connected = False
    if db_manager and db_manager.driver:
        try:
            async with db_manager.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                test = await result.single()
                neo4j_connected = test["test"] == 1  # type: ignore
        except:
            neo4j_connected = False

    return HealthResponse(
        status="healthy" if neo4j_connected else "degraded",
        neo4j_connected=neo4j_connected,
        timestamp=datetime.utcnow().isoformat(),
        version="0.3.0"
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get service metrics"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        metrics = await db_manager.get_metrics()
        uptime = (datetime.utcnow() - start_time).total_seconds()

        return MetricsResponse(
            total_contexts=metrics["total_contexts"],
            total_agents=metrics["total_agents"],
            total_relationships=metrics["total_relationships"],
            uptime_seconds=uptime
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Gadugi MCP Service",
        "version": "0.3.0",
        "status": "running",
        "endpoints": [
            "/context/store",
            "/context/retrieve/{id}",
            "/context/search",
            "/health",
            "/metrics",
            "/docs"
        ]
    }


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "mcp_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
