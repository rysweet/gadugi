#!/bin/bash
# Start the Event Router service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "🚀 Starting Gadugi Event Router Service"
echo "=================================================="
echo "Service directory: $SCRIPT_DIR"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Change to service directory
cd "$SCRIPT_DIR"

# Create required directories
mkdir -p logs data

echo "📦 Installing requirements..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt > logs/install.log 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Requirements installed successfully"
    else
        echo "⚠️  Some requirements may have failed to install (see logs/install.log)"
    fi
fi

echo "🚀 Starting service..."
echo "💡 Service will be available at http://localhost:8000"
echo "💡 Health check: curl http://localhost:8000/health"
echo

# Start the service
python3 start_event_router.py
