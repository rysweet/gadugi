#!/bin/bash
# Gadugi Bootstrap - Download agent-updater only
# The actual installation happens via /agent:agent-updater

set -e

# Just download the agent-updater, nothing else
mkdir -p .claude/agents

curl -fsSL https://raw.githubusercontent.com/rysweet/gadugi/main/.claude/agents/agent-updater.md \
     -o .claude/agents/agent-updater.md

if [ $? -eq 0 ]; then
    echo "✅ Agent-updater downloaded to .claude/agents/"
    echo ""
    echo "To install Gadugi, run:"
    echo "  /agent:agent-updater install"
else
    echo "❌ Failed to download agent-updater"
    exit 1
fi
