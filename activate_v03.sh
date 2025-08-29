#!/bin/bash
# Activate Gadugi v0.3 for Development

set -e

echo "🚀 Activating Gadugi v0.3 for Development"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in Gadugi project root"
    exit 1
fi

# 1. Start Memory System (SQLite version)
echo "📦 Starting Memory System..."
if [ -f ".claude/services/memory/start_local.sh" ]; then
    .claude/services/memory/start_local.sh &
    MEMORY_PID=$!
    echo "   Memory system starting (PID: $MEMORY_PID)..."
    sleep 3
else
    echo "   ⚠️  Memory system not found, skipping..."
fi

# 2. Verify orchestrator is available
echo "🎭 Checking Orchestrator..."
if [ -d "./scripts/orchestrator" ]; then
    echo "   ✅ Orchestrator available"
    echo "   Run tasks with: ./scripts/orchestrator/execute_orchestrator.sh [task]"
else
    echo "   ⚠️  Orchestrator not found"
fi

# 3. Check for agents
echo "🤖 Available Agents:"
if [ -d ".claude/agents" ]; then
    for agent in .claude/agents/*/agent.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename $(dirname "$agent"))
            echo "   - $agent_name"
        fi
    done
else
    echo "   ⚠️  No agents found"
fi

# 4. Create helper functions
cat > ~/.gadugi_v03_helpers.sh << 'EOF'
# Gadugi v0.3 Helper Functions

# Execute task with orchestrator
v03_task() {
    if [ -z "$1" ]; then
        echo "Usage: v03_task 'description of task'"
        return 1
    fi
    ./scripts/orchestrator/execute_orchestrator.sh "$1"
}

# Store in memory
v03_remember() {
    if [ -z "$1" ]; then
        echo "Usage: v03_remember 'information to store'"
        return 1
    fi
    curl -X POST http://localhost:8000/memory/agent/store \
        -H "Content-Type: application/json" \
        -d "{\"agent_id\": \"user\", \"content\": \"$1\", \"memory_type\": \"semantic\"}"
}

# Query memory
v03_recall() {
    curl -s http://localhost:8000/memory/agent/user | python -m json.tool
}

# Check v0.3 status
v03_status() {
    echo "Gadugi v0.3 Status:"
    echo "=================="

    # Check memory
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Memory System: Running"
    else
        echo "❌ Memory System: Not running"
    fi

    # Check orchestrator
    if [ -f "./scripts/orchestrator/execute_orchestrator.sh" ]; then
        echo "✅ Orchestrator: Available"
    else
        echo "❌ Orchestrator: Not found"
    fi

    # Show recent memories
    echo ""
    echo "Recent Memories:"
    curl -s http://localhost:8000/memory/agent/user 2>/dev/null | head -5 || echo "  No memories yet"
}

echo "Gadugi v0.3 helpers loaded. Commands:"
echo "  v03_task 'description'  - Run task with orchestrator"
echo "  v03_remember 'info'     - Store in memory"
echo "  v03_recall              - Query memories"
echo "  v03_status              - Check v0.3 status"
EOF

echo ""
echo "✅ Gadugi v0.3 Activated!"
echo ""
echo "Quick Commands:"
echo "  source ~/.gadugi_v03_helpers.sh   # Load helper functions"
echo "  v03_status                         # Check status"
echo "  v03_task 'your task'               # Execute with orchestrator"
echo ""
echo "In Claude, request:"
echo "  'Use v0.3 orchestrator to...'"
echo "  'Store this in v0.3 memory...'"
echo "  'Use parallel execution for...'"
echo ""
echo "To deactivate:"
echo "  .claude/services/memory/stop_local.sh"
echo ""
