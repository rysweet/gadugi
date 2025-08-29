#!/bin/bash

# Start Local Memory System for Gadugi v0.3 (No Docker Required)
# This script starts the SQLite-based MCP service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

echo "========================================="
echo "Starting Gadugi Memory System (Local)"
echo "========================================="

# Install dependencies if needed
echo "Checking Python dependencies..."
cd "$PROJECT_ROOT"

# Install required packages
if command -v uv >/dev/null 2>&1; then
    echo "Installing dependencies with uv..."
    uv add fastapi uvicorn aiosqlite --quiet 2>/dev/null || true
else
    echo "Installing dependencies with pip..."
    pip install fastapi uvicorn aiosqlite --quiet 2>/dev/null || true
fi

# Kill any existing MCP service
echo "Stopping any existing services..."
pkill -f "simple_mcp_service" 2>/dev/null || true

# Start MCP service
echo "Starting MCP service (SQLite backend)..."
cd "$SCRIPT_DIR"

if command -v uv >/dev/null 2>&1; then
    echo "Starting with uv..."
    uv run uvicorn simple_mcp_service:app --host 0.0.0.0 --port 8000 --reload &
else
    echo "Starting with Python..."
    python -m uvicorn simple_mcp_service:app --host 0.0.0.0 --port 8000 --reload &
fi

MCP_PID=$!
echo "MCP service started with PID: $MCP_PID"

# Save PID for later shutdown
echo $MCP_PID > "$SCRIPT_DIR/mcp.pid"

# Wait for service to start
echo "Waiting for service to be ready..."
max_attempts=10
attempt=0

while ! curl -s http://localhost:8000/health >/dev/null 2>&1; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Error: Service failed to start after $max_attempts attempts"
        exit 1
    fi
    echo "Waiting... (attempt $attempt/$max_attempts)"
    sleep 2
done

# Test the service
echo ""
echo "Testing MCP service..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ MCP service is healthy!"

    # Show stats
    echo ""
    echo "Database Statistics:"
    curl -s http://localhost:8000/health | python -m json.tool | grep -A 10 "stats"
else
    echo "⚠️  MCP service may not be ready yet"
fi

echo ""
echo "========================================="
echo "Memory System Started Successfully!"
echo "========================================="
echo "MCP API: http://localhost:8000"
echo "MCP Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo ""
echo "Database location: $PROJECT_ROOT/.claude/data/memory.db"
echo ""
echo "To stop the service: $SCRIPT_DIR/stop_local.sh"
echo "To test the system: $SCRIPT_DIR/test_local.py"
echo ""
