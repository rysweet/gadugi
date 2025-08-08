#!/bin/bash
# Gadugi Bootstrap - Minimal
# Download agent-updater and let it handle everything

set -e

echo "🚀 Bootstrapping Gadugi..."

# Create minimal .claude structure (agents must be in .claude/agents for Claude)
mkdir -p .claude/agents
mkdir -p .claude/gadugi

# Download the agent-updater (it will handle everything else)
echo "📦 Downloading agent-updater..."
curl -fsSL https://raw.githubusercontent.com/rysweet/gadugi/main/.claude/agents/agent-updater.md \
     -o .claude/agents/agent-updater.md

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Bootstrap complete!"
    echo ""
    echo "To complete installation, run:"
    echo "  /agent:agent-updater"
    echo ""
    echo "The agent-updater will:"
    echo "  • Check for and install all agents"
    echo "  • Set up the environment"
    echo "  • Configure everything needed"
else
    echo "❌ Failed to download agent-updater"
    exit 1
fi
