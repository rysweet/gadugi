#!/bin/bash
# Start test memory service that actually works
# This bypasses the corrupted uvicorn/fastapi packages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill any existing service
pkill -f "simple_test_service.py" 2>/dev/null || true

# Start the test service
echo "Starting Memory Test Service on port 5000..."
cd "$SCRIPT_DIR"
nohup python3 simple_test_service.py > /tmp/memory-test-service.log 2>&1 &
PID=$!
echo $PID > "$SCRIPT_DIR/test_service.pid"

# Wait for it to start
sleep 2

# Check if it's running
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Memory Test Service started successfully (PID: $PID)"
    echo "Health endpoint: http://localhost:5000/health"
else
    echo "❌ Failed to start Memory Test Service"
    exit 1
fi
