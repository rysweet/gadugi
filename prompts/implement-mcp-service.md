# Task: Implement MCP Service

## Description
Implement the MCP (Memory Control Protocol) service as frontend to Neo4j for memory management.

## Requirements
1. **Location**: `.claude/services/mcp/`
2. **Recipe**: `.claude/recipes/memory-system/requirements.md`
3. **Integration**: Neo4j database client

## Implementation Requirements
- REST API for memory operations (CRUD)
- Caching layer with in-memory LRU cache
- Context retrieval by relevance using semantic search
- Integration with Neo4j client for persistent storage
- Memory pruning capabilities for old/irrelevant memories
- Session context tracking and restoration

## Memory Types to Support
- Episodic memories (specific events and interactions)
- Semantic memories (facts and knowledge)
- Procedural memories (how-to knowledge)
- Working memories (current task context)
- Shared memories (team knowledge base)

## API Endpoints
- `POST /memory` - Store new memory
- `GET /memory/{id}` - Retrieve specific memory
- `PUT /memory/{id}` - Update memory
- `DELETE /memory/{id}` - Delete memory
- `POST /memory/search` - Search memories semantically
- `POST /context/save` - Save session context
- `GET /context/load/{agent_id}` - Load session context
- `POST /memory/prune` - Prune old memories

## Quality Requirements
- All Python code must use `uv run` for commands
- Code must be pyright clean
- Code must be ruff formatted
- All tests must pass
- Sub-100ms response time for recent items

## Files to Create/Modify
1. `.claude/services/mcp/mcp_service.py` - Main MCP service with FastAPI
2. `.claude/services/mcp/models.py` - Memory and context models
3. `.claude/services/mcp/cache.py` - LRU cache implementation
4. `.claude/services/mcp/neo4j_client.py` - Neo4j integration
5. `.claude/services/mcp/tests/test_mcp_service.py` - Unit tests
6. `.claude/services/mcp/__init__.py` - Module exports