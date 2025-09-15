#!/bin/bash

# Start Memory System for Gadugi v0.3
# This script starts Neo4j and the MCP service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

echo "========================================="
echo "Starting Gadugi Memory System"
echo "========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start Neo4j container
echo "Starting Neo4j container..."
cd "$SCRIPT_DIR"

# Stop any existing container
docker-compose down 2>/dev/null || true

# Start Neo4j
docker-compose up -d

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0
while ! docker exec gadugi-neo4j cypher-shell -u neo4j -p "gadugi123!" "RETURN 1" >/dev/null 2>&1; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Error: Neo4j failed to start after $max_attempts attempts"
        exit 1
    fi
    echo "Waiting for Neo4j... (attempt $attempt/$max_attempts)"
    sleep 2
done

echo "Neo4j is ready!"

# Initialize schema
echo "Initializing Neo4j schema..."
docker exec gadugi-neo4j cypher-shell -u neo4j -p "gadugi123!" < "$PROJECT_ROOT/neo4j/schema.cypher" || {
    echo "Warning: Some schema constraints may already exist (this is normal)"
}

# Install Python dependencies if needed
echo "Checking Python dependencies..."
cd "$PROJECT_ROOT"
if [ -f "pyproject.toml" ] && command -v uv >/dev/null 2>&1; then
    echo "Installing dependencies with uv..."
    uv sync --all-extras
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies with pip..."
    pip install -r requirements.txt
fi

# Start MCP service
echo "Starting MCP service..."
cd "$PROJECT_ROOT/.claude/services/mcp"

# Kill any existing MCP service
pkill -f "uvicorn.*enhanced_mcp_service" 2>/dev/null || true

# Start MCP service in background
if command -v uv >/dev/null 2>&1; then
    echo "Starting MCP service with uv..."
    uv run uvicorn enhanced_mcp_service:app --host 0.0.0.0 --port 8000 --reload &
else
    echo "Starting MCP service with Python..."
    python -m uvicorn enhanced_mcp_service:app --host 0.0.0.0 --port 8000 --reload &
fi

MCP_PID=$!
echo "MCP service started with PID: $MCP_PID"

# Save PID for later shutdown
echo $MCP_PID > "$SCRIPT_DIR/mcp.pid"

# Wait a moment for service to start
sleep 5

# Test MCP service
echo "Testing MCP service..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ MCP service is healthy!"
else
    echo "⚠️  MCP service may not be fully ready yet"
fi

echo ""
echo "========================================="
echo "Memory System Started Successfully!"
echo "========================================="
echo "Neo4j UI: http://localhost:7474"
echo "Neo4j Bolt: bolt://localhost:7687"
echo "MCP API: http://localhost:8000"
echo "MCP Docs: http://localhost:8000/docs"
echo ""
echo "To stop the services, run: $SCRIPT_DIR/stop_memory_system.sh"
echo ""
