# How to Run and Test Gadugi v0.3

This guide shows how to start, run, and test the Gadugi v0.3 system.

## Option 1: Quick Test (No Docker Required)

For a quick test without Docker, run:

```bash
# Quick test of core functionality
uv run python quick_test_v03.py
```

This demonstrates all v0.3 features using a local SQLite database.

## Option 2: Full System (Requires Docker)

### Prerequisites

1. **Docker** - Required for Neo4j
2. **Python 3.12** - Required for the system
3. **UV** - Package manager (or use pip)

```bash
# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras
```

## Quick Start (All Services)

### 1. Start the Memory System (Neo4j + MCP)

```bash
# Start Neo4j and MCP service
.claude/services/neo4j-memory/start_memory_system.sh

# This starts:
# - Neo4j on port 7474 (UI) and 7687 (Bolt)
# - MCP API on port 8000
```

**Verify:**
- Neo4j UI: http://localhost:7474 (login: neo4j/gadugi123!)
- MCP API Docs: http://localhost:8000/docs
- Health Check: `curl http://localhost:8000/health`

### 2. Start the Event Router (Optional)

```bash
# Terminal 1 - Start the event router
cd .claude/services/event-router
uv run python main.py

# Runs on port 5000
```

**Verify:**
- Event Router: http://localhost:5000/health

### 3. Start the LLM Proxy (Optional)

```bash
# Terminal 2 - Start LLM proxy
cd .claude/services/llm-proxy/claude-code-proxy
uv run python src/main.py

# Runs on port 8080
```

## Testing Individual Components

### Test Memory System

```python
# Run the memory integration test
uv run pytest tests/test_memory_system_integration.py -v

# Or test manually with Python
uv run python
```

```python
import asyncio
from .claude.shared.memory_integration import AgentMemoryInterface

async def test_memory():
    async with AgentMemoryInterface(agent_id="test_agent") as memory:
        # Store short-term memory
        mem_id = await memory.remember_short_term("Testing v0.3")
        print(f"Stored memory: {mem_id}")

        # Recall memories
        memories = await memory.recall_memories()
        print(f"Retrieved {len(memories)} memories")

        # Create knowledge
        knowledge_id = await memory.add_knowledge(
            "Gadugi v0.3",
            "A self-hosting AI system"
        )
        print(f"Added knowledge: {knowledge_id}")

asyncio.run(test_memory())
```

### Test Agent with Memory

```python
# Example agent usage
from .claude.shared.memory_integration import MemoryEnabledAgent
import asyncio

async def run_agent():
    # Create agent
    agent = MemoryEnabledAgent(
        agent_id="demo_agent_001",
        project_id="gadugi_v03"
    )

    await agent.initialize()

    # Start a task
    await agent.start_task("task_001", "Test v0.3 functionality")

    # Learn something
    await agent.learn_from_experience(
        "Tested the memory system",
        "Memory system works correctly with Neo4j"
    )

    # Collaborate via whiteboard
    await agent.collaborate(
        "V0.3 is running successfully",
        decision="System is ready for use"
    )

    # End task
    await agent.end_task("Successfully tested v0.3")

asyncio.run(run_agent())
```

## Running the Orchestrator

### Simple Task Execution

```bash
# Run a simple task with orchestrator
cd scripts/orchestrator
./execute_orchestrator.sh "Create a hello world Python script"
```

### Parallel Task Execution

```python
# Run parallel tasks
uv run python scripts/orchestrator/run_parallel_tasks.py
```

## API Testing with curl

### Memory Operations

```bash
# Store agent memory
curl -X POST http://localhost:8000/memory/agent/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "content": "Testing v0.3 system",
    "memory_type": "semantic",
    "importance_score": 0.8
  }'

# Get agent memories
curl http://localhost:8000/memory/agent/test_agent

# Create whiteboard
curl -X POST http://localhost:8000/whiteboard/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_123",
    "agent_id": "test_agent"
  }'

# Add knowledge
curl -X POST http://localhost:8000/knowledge/node/create \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "concept": "Testing",
    "description": "Process of validating functionality",
    "confidence": 0.95
  }'
```

## Full System Test

```bash
# 1. Start all services
.claude/services/neo4j-memory/start_memory_system.sh

# 2. Run integration tests
uv run pytest tests/ -v -k "integration"

# 3. Test type safety
uv run pyright

# 4. Run pre-commit checks
uv run pre-commit run --all-files
```

## Interactive Testing with API Docs

1. Start the MCP service (as above)
2. Open http://localhost:8000/docs
3. Use the interactive Swagger UI to test all endpoints

### Key Endpoints to Test:
- `POST /memory/agent/store` - Store agent memory
- `GET /memory/agent/{agent_id}` - Get agent memories
- `POST /whiteboard/create` - Create task whiteboard
- `POST /whiteboard/update` - Update whiteboard
- `POST /knowledge/node/create` - Add knowledge node
- `GET /knowledge/graph/{agent_id}` - Get knowledge graph
- `POST /memory/project/store` - Store project memory
- `POST /memory/procedural/store` - Store procedure

## Monitoring

### Check Neo4j

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs gadugi-neo4j

# Connect to Neo4j browser
# http://localhost:7474
# Login: neo4j / gadugi123!

# Run Cypher query to see nodes
MATCH (n) RETURN n LIMIT 25
```

### Check MCP Service

```bash
# Check health
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics

# Check logs (if running in foreground)
# Will show in terminal
```

## Example Workflow

```bash
# 1. Start the system
.claude/services/neo4j-memory/start_memory_system.sh

# 2. Create a test agent and run tasks
cat > test_v03.py << 'EOF'
import asyncio
import httpx
from datetime import datetime

async def test_v03_workflow():
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(base_url=base_url) as client:
        # Create agent memory
        agent_id = "workflow_agent_001"
        task_id = "task_" + datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"Testing agent: {agent_id}")
        print(f"Task ID: {task_id}")

        # Store initial memory
        response = await client.post("/memory/agent/store", json={
            "agent_id": agent_id,
            "content": "Starting v0.3 workflow test",
            "memory_type": "episodic",
            "task_id": task_id,
            "importance_score": 0.9
        })
        print(f"Stored memory: {response.json()['id']}")

        # Create whiteboard
        response = await client.post("/whiteboard/create", json={
            "task_id": task_id,
            "agent_id": agent_id
        })
        print(f"Created whiteboard: {response.json()['id']}")

        # Add knowledge
        response = await client.post("/knowledge/node/create", json={
            "agent_id": agent_id,
            "concept": "V0.3 Testing",
            "description": "Successfully tested Gadugi v0.3",
            "confidence": 1.0
        })
        print(f"Added knowledge: {response.json()['id']}")

        # Store procedure
        response = await client.post("/memory/procedural/store", json={
            "agent_id": agent_id,
            "procedure_name": "test_v03",
            "steps": [
                "Start memory system",
                "Create agent",
                "Store memories",
                "Create whiteboard",
                "Add knowledge"
            ],
            "context": "Testing Gadugi v0.3"
        })
        print(f"Stored procedure: {response.json()['id']}")

        # Get all memories
        response = await client.get(f"/memory/agent/{agent_id}")
        memories = response.json()
        print(f"\nAgent has {len(memories)} memories")

        # Get metrics
        response = await client.get("/metrics")
        metrics = response.json()
        print(f"\nSystem metrics: {metrics}")

        print("\n✅ V0.3 workflow test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_v03_workflow())
EOF

uv run python test_v03.py

# 3. View results in Neo4j browser
# http://localhost:7474
# Run: MATCH (n) RETURN n
```

## Stopping Services

```bash
# Stop memory system (Neo4j + MCP)
.claude/services/neo4j-memory/stop_memory_system.sh

# Stop other services (Ctrl+C in their terminals)
```

## Troubleshooting

### Neo4j Won't Start
```bash
# Check if port is in use
lsof -i :7474
lsof -i :7687

# Remove old container
docker rm -f gadugi-neo4j

# Try again
.claude/services/neo4j-memory/start_memory_system.sh
```

### MCP Service Issues
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill old process
pkill -f "uvicorn.*enhanced_mcp_service"

# Check Python path
python -c "import sys; print(sys.path)"
```

### Type Errors
```bash
# Fix any type errors
uv run python .claude/type-fixing-tools/final_comprehensive_fix.py

# Verify
uv run pyright
```

## What's Working in v0.3

✅ **Memory System**
- Neo4j graph database
- MCP API service
- All memory types (short/long-term, procedural, shared, whiteboard)
- Knowledge graphs per agent
- Memory consolidation

✅ **Type Safety**
- Zero pyright errors
- Complete type coverage
- Type-fix tools available

✅ **Infrastructure**
- Docker support
- Pre-commit hooks
- CI/CD configuration
- Clean repository structure

✅ **Agent Integration**
- Memory-enabled agents
- Agent memory interface
- Example implementations

## Next Steps

1. Start implementing actual agents using the memory system
2. Build workflows that leverage the whiteboard
3. Create procedures and store them
4. Build knowledge graphs for specialized domains
5. Test parallel task execution with memory persistence

---

**Quick Test Command:**
```bash
# One command to test if everything works
.claude/services/neo4j-memory/start_memory_system.sh && \
sleep 10 && \
curl http://localhost:8000/health && \
echo "✅ V0.3 is running!"
```
