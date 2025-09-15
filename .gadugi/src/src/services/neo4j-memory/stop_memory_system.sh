#!/bin/bash

# Stop Memory System for Gadugi v0.3

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Stopping Gadugi Memory System"
echo "========================================="

# Stop MCP service
if [ -f "$SCRIPT_DIR/mcp.pid" ]; then
    MCP_PID=$(cat "$SCRIPT_DIR/mcp.pid")
    if ps -p $MCP_PID > /dev/null 2>&1; then
        echo "Stopping MCP service (PID: $MCP_PID)..."
        kill $MCP_PID 2>/dev/null || true
    fi
    rm "$SCRIPT_DIR/mcp.pid"
else
    # Try to find and kill by process name
    echo "Stopping any running MCP services..."
    pkill -f "uvicorn.*enhanced_mcp_service" 2>/dev/null || true
fi

# Stop Neo4j container
echo "Stopping Neo4j container..."
cd "$SCRIPT_DIR"
docker-compose down

echo ""
echo "========================================="
echo "Memory System Stopped"
echo "========================================="
