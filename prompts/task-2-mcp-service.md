# Task 2: Implement MCP Service

## Objective
Create a REAL, working FastAPI MCP (Model Context Protocol) service that integrates with Neo4j.

## Requirements
1. Must be a REAL FastAPI service, not a stub
2. Must connect to Neo4j on port 7475
3. Must implement MCP protocol endpoints
4. Must actually run with uvicorn
5. Use Recipe Executor to generate from recipe if available

## Technical Details
- Location: `.claude/services/mcp/`
- Framework: FastAPI
- Database: Neo4j (port 7475)
- Server: uvicorn
- Python async/await patterns

## Implementation Components
1. **Main Service** (`mcp_service.py`):
   - FastAPI app initialization
   - MCP protocol endpoints
   - Neo4j connection management
   - Context storage and retrieval

2. **Models** (`models.py`):
   - Pydantic models for MCP protocol
   - Request/Response schemas
   - Neo4j entity models

3. **Database** (`database.py`):
   - Neo4j connection pool
   - Query methods
   - Transaction handling

4. **Config** (`config.py`):
   - Environment variables
   - Neo4j connection settings
   - Service configuration

## MCP Endpoints to Implement
- `POST /context/store` - Store context in Neo4j
- `GET /context/retrieve` - Retrieve context by ID
- `POST /context/search` - Search contexts
- `GET /health` - Health check with Neo4j status
- `GET /metrics` - Service metrics

## Success Criteria
- Service starts with `uvicorn mcp_service:app`
- All endpoints return proper responses
- Neo4j integration works
- Can store and retrieve context data
- Health check confirms Neo4j connection

## Files to Create
- `.claude/services/mcp/mcp_service.py`
- `.claude/services/mcp/models.py`
- `.claude/services/mcp/database.py`
- `.claude/services/mcp/config.py`
- `.claude/services/mcp/requirements.txt`
- `.claude/services/mcp/test_mcp_service.py`