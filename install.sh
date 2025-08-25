#!/bin/bash
# Gadugi Bootstrap - Downloads gadugi-updater agent only

set -e

# Create agents directory if it doesn't exist
mkdir -p .claude/agents

# Download the gadugi-updater agent
curl -fsSL https://raw.githubusercontent.com/rysweet/gadugi/main/.claude/agents/gadugi-updater.md \
     -o .claude/agents/gadugi-updater.md

if [ $? -eq 0 ]; then
    echo "✅ Gadugi updater downloaded to .claude/agents/"
    echo ""
    echo "To install Gadugi, run:"
    echo "  /agent:gadugi-updater install"
else
    echo "❌ Failed to download gadugi-updater"
    exit 1
fi
