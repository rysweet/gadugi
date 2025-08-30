#!/bin/bash

# Stop Local Memory System

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping Gadugi Memory System..."

# Stop MCP service
if [ -f "$SCRIPT_DIR/mcp.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/mcp.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Stopped MCP service (PID: $PID)"
    else
        echo "MCP service not running"
    fi
    rm "$SCRIPT_DIR/mcp.pid"
else
    # Try to find and kill by process name
    pkill -f "simple_mcp_service" 2>/dev/null && echo "✅ Stopped MCP service" || echo "MCP service not running"
fi

echo "Memory system stopped."
