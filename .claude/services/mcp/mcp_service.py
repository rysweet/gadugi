"""MCP Service - Memory Control Protocol REST API."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cache import LRUCache
from .models import (
    Context,
    ContextLoadResponse,
    ContextSaveRequest,
    Memory,
    MemoryPruneRequest,
    MemoryPruneResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryType,
)
from .neo4j_client import Neo4jMemoryClient


class MCPService:
    """Memory Control Protocol service implementation."""
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_username: str = "neo4j",
        neo4j_password: str = "password",
        cache_size: int = 1000,
        cache_memory_mb: int = 100,
    ):
        """Initialize MCP service.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_username: Neo4j username
            neo4j_password: Neo4j password
            cache_size: Maximum cache entries
            cache_memory_mb: Maximum cache memory in MB
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize Neo4j client
        self.neo4j_client = Neo4jMemoryClient(
            uri=neo4j_uri,
            username=neo4j_username,
            password=neo4j_password,
        )
        
        # Initialize LRU cache
        self.cache = LRUCache(
            max_size=cache_size,
            max_memory_mb=cache_memory_mb,
            default_ttl=300,  # 5 minutes
        )
        
        # Statistics
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
    
    async def startup(self) -> None:
        """Startup tasks."""
        await self.neo4j_client.connect()
        self.logger.info("MCP Service started")
    
    async def shutdown(self) -> None:
        """Shutdown tasks."""
        await self.neo4j_client.disconnect()
        self.cache.clear()
        self.logger.info("MCP Service stopped")
    
    # Memory Operations
    
    async def create_memory(self, memory: Memory) -> Memory:
        """Create a new memory.
        
        Args:
            memory: Memory to create
            
        Returns:
            Created memory with ID
        """
        try:
            # Store in Neo4j
            memory_id = await self.neo4j_client.store_memory(memory)
            memory.id = memory_id
            
            # Add to cache
            cache_key = f"memory:{memory_id}"
            self.cache.put(cache_key, memory)
            
            self.logger.info(f"Created memory {memory_id}")
            return memory
        
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error creating memory: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create memory: {str(e)}"
            )
    
    async def get_memory(self, memory_id: str) -> Memory:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory object
        """
        try:
            # Check cache first
            cache_key = f"memory:{memory_id}"
            cached_memory = self.cache.get(cache_key)
            if cached_memory:
                self.logger.debug(f"Cache hit for memory {memory_id}")
                cached_memory.update_access()
                return cached_memory
            
            # Fetch from Neo4j
            memory = await self.neo4j_client.retrieve_memory(memory_id)
            if not memory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Memory {memory_id} not found"
                )
            
            # Update cache
            self.cache.put(cache_key, memory)
            
            # Update access metadata
            memory.update_access()
            await self.neo4j_client.update_memory(memory)
            
            return memory
        
        except HTTPException:
            raise
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error retrieving memory {memory_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve memory: {str(e)}"
            )
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> Memory:
        """Update an existing memory.
        
        Args:
            memory_id: Memory ID
            updates: Fields to update
            
        Returns:
            Updated memory
        """
        try:
            # Get existing memory
            memory = await self.get_memory(memory_id)
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            memory.updated_at = datetime.now()
            
            # Update in Neo4j
            success = await self.neo4j_client.update_memory(memory)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update memory in database"
                )
            
            # Update cache
            cache_key = f"memory:{memory_id}"
            self.cache.put(cache_key, memory)
            
            self.logger.info(f"Updated memory {memory_id}")
            return memory
        
        except HTTPException:
            raise
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error updating memory {memory_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update memory: {str(e)}"
            )
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if deleted
        """
        try:
            # Delete from Neo4j
            success = await self.neo4j_client.delete_memory(memory_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Memory {memory_id} not found"
                )
            
            # Remove from cache
            cache_key = f"memory:{memory_id}"
            self.cache.remove(cache_key)
            
            self.logger.info(f"Deleted memory {memory_id}")
            return True
        
        except HTTPException:
            raise
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error deleting memory {memory_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete memory: {str(e)}"
            )
    
    async def search_memories(self, request: MemorySearchRequest) -> MemorySearchResponse:
        """Search memories semantically.
        
        Args:
            request: Search request
            
        Returns:
            Search response with matching memories
        """
        try:
            start_time = time.time()
            
            # Search in Neo4j
            memories = await self.neo4j_client.search_memories(
                query=request.query,
                agent_id=request.agent_id,
                memory_types=request.memory_types,
                tags=request.tags,
                limit=request.limit,
            )
            
            # Filter by relevance threshold
            if request.use_embeddings and request.threshold > 0:
                # Would calculate embeddings and filter here
                # For now, just use importance score as proxy
                memories = [
                    m for m in memories
                    if m.importance_score >= request.threshold
                ]
            
            # Update cache with search results
            for memory in memories[:10]:  # Cache top 10 results
                cache_key = f"memory:{memory.id}"
                self.cache.put(cache_key, memory, ttl=60)  # Short TTL for search results
            
            search_time_ms = (time.time() - start_time) * 1000
            
            return MemorySearchResponse(
                memories=memories,
                total_count=len(memories),
                search_time_ms=search_time_ms,
            )
        
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error searching memories: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search memories: {str(e)}"
            )
    
    # Context Operations
    
    async def save_context(self, request: ContextSaveRequest) -> Context:
        """Save agent context.
        
        Args:
            request: Context save request
            
        Returns:
            Saved context
        """
        try:
            context = request.context
            
            # Compress working memory if requested
            if request.compress:
                # Simple compression: remove null values and empty strings
                context.working_memory = {
                    k: v for k, v in context.working_memory.items()
                    if v is not None and v != ""
                }
            
            # Save to Neo4j
            context_id = await self.neo4j_client.save_context(context)
            context.id = context_id
            
            # Cache the context
            cache_key = f"context:{request.agent_id}"
            self.cache.put(cache_key, context)
            
            self.logger.info(f"Saved context for agent {request.agent_id}")
            return context
        
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error saving context: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save context: {str(e)}"
            )
    
    async def load_context(self, agent_id: str) -> ContextLoadResponse:
        """Load agent context.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Context load response
        """
        try:
            start_time = time.time()
            
            # Check cache first
            cache_key = f"context:{agent_id}"
            cached_context = self.cache.get(cache_key)
            
            if cached_context:
                context = cached_context
                self.logger.debug(f"Cache hit for context {agent_id}")
            else:
                # Load from Neo4j
                context = await self.neo4j_client.load_context(agent_id)
                if not context:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No active context found for agent {agent_id}"
                    )
                
                # Update cache
                self.cache.put(cache_key, context)
            
            # Load associated memories
            memories = []
            for memory_id in context.memories[:50]:  # Limit to 50 most recent
                try:
                    memory = await self.get_memory(memory_id)
                    memories.append(memory)
                except HTTPException:
                    pass  # Skip missing memories
            
            load_time_ms = (time.time() - start_time) * 1000
            
            return ContextLoadResponse(
                context=context,
                memories=memories,
                load_time_ms=load_time_ms,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error loading context for {agent_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load context: {str(e)}"
            )
    
    async def switch_context(self, from_context_id: str, to_context_id: str) -> bool:
        """Switch between contexts.
        
        Args:
            from_context_id: Current context ID
            to_context_id: Target context ID
            
        Returns:
            True if successful
        """
        try:
            success = await self.neo4j_client.switch_context(from_context_id, to_context_id)
            
            # Invalidate cache for affected contexts
            # (Would need to track agent IDs for proper cache invalidation)
            
            self.logger.info(f"Switched context from {from_context_id} to {to_context_id}")
            return success
        
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error switching context: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to switch context: {str(e)}"
            )
    
    async def merge_contexts(self, context_ids: List[str]) -> Context:
        """Merge multiple contexts.
        
        Args:
            context_ids: List of context IDs to merge
            
        Returns:
            Merged context
        """
        try:
            if len(context_ids) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least 2 contexts required for merge"
                )
            
            merged_context = await self.neo4j_client.merge_contexts(context_ids)
            if not merged_context:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to merge contexts"
                )
            
            self.logger.info(f"Merged {len(context_ids)} contexts")
            return merged_context
        
        except HTTPException:
            raise
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error merging contexts: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to merge contexts: {str(e)}"
            )
    
    # Memory Management
    
    async def prune_memories(self, request: MemoryPruneRequest) -> MemoryPruneResponse:
        """Prune old memories.
        
        Args:
            request: Prune request
            
        Returns:
            Prune response
        """
        try:
            # Get initial count for statistics
            # (Would need a count query for accuracy)
            initial_count = 1000  # Placeholder
            
            # Prune memories
            pruned_count = await self.neo4j_client.prune_memories(
                agent_id=request.agent_id,
                older_than_days=request.older_than_days,
                preserve_important=request.preserve_important,
                importance_threshold=request.importance_threshold,
            )
            
            # Clear relevant cache entries
            # (Would need to track which entries to clear)
            
            retained_count = initial_count - pruned_count
            freed_space_bytes = pruned_count * 1024  # Rough estimate
            
            self.logger.info(f"Pruned {pruned_count} memories")
            
            return MemoryPruneResponse(
                pruned_count=pruned_count,
                retained_count=retained_count,
                freed_space_bytes=freed_space_bytes,
            )
        
        except Exception as e:
            self.error_count += 1
            self.logger.exception(f"Error pruning memories: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to prune memories: {str(e)}"
            )
    
    def get_health(self) -> Dict[str, Any]:
        """Get service health status.
        
        Returns:
            Health status dictionary
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        cache_stats = self.cache.get_stats()
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "cache_stats": cache_stats,
            "neo4j_connected": self.neo4j_client._driver is not None,
        }


# Create service instance
mcp_service = MCPService()

# Create FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    await mcp_service.startup()
    yield
    await mcp_service.shutdown()


app = FastAPI(
    title="MCP Service",
    description="Memory Control Protocol REST API for Gadugi v0.3",
    version="0.3.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to track requests
@app.middleware("http")
async def track_requests(request, call_next):
    """Track request count and timing."""
    mcp_service.request_count += 1
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# API Endpoints

@app.get("/health")
async def health():
    """Health check endpoint."""
    return mcp_service.get_health()


@app.post("/memory", response_model=Memory)
async def create_memory(memory: Memory):
    """Create a new memory."""
    return await mcp_service.create_memory(memory)


@app.get("/memory/{memory_id}", response_model=Memory)
async def get_memory(memory_id: str):
    """Retrieve a memory by ID."""
    return await mcp_service.get_memory(memory_id)


@app.put("/memory/{memory_id}", response_model=Memory)
async def update_memory(memory_id: str, updates: Dict[str, Any]):
    """Update an existing memory."""
    return await mcp_service.update_memory(memory_id, updates)


@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory."""
    success = await mcp_service.delete_memory(memory_id)
    return {"success": success}


@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """Search memories semantically."""
    return await mcp_service.search_memories(request)


@app.post("/context/save", response_model=Context)
async def save_context(request: ContextSaveRequest):
    """Save agent context."""
    return await mcp_service.save_context(request)


@app.get("/context/load/{agent_id}", response_model=ContextLoadResponse)
async def load_context(agent_id: str):
    """Load agent context."""
    return await mcp_service.load_context(agent_id)


@app.post("/context/switch")
async def switch_context(from_context_id: str, to_context_id: str):
    """Switch between contexts."""
    success = await mcp_service.switch_context(from_context_id, to_context_id)
    return {"success": success}


@app.post("/context/merge", response_model=Context)
async def merge_contexts(context_ids: List[str]):
    """Merge multiple contexts."""
    return await mcp_service.merge_contexts(context_ids)


@app.post("/memory/prune", response_model=MemoryPruneResponse)
async def prune_memories(request: MemoryPruneRequest):
    """Prune old memories."""
    return await mcp_service.prune_memories(request)


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return mcp_service.cache.get_stats()


@app.post("/cache/clear")
async def clear_cache():
    """Clear the cache."""
    mcp_service.cache.clear()
    return {"success": True, "message": "Cache cleared"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "mcp_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )