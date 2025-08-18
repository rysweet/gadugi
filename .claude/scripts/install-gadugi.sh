#!/bin/bash
# Gadugi Installation Script
# This script is downloaded and run by the gadugi-updater agent

set -e

echo "🚀 Installing Gadugi Multi-Agent System..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p .claude/gadugi/{scripts,config,cache}
mkdir -p .claude/agents

# Check for UV and install if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
cd .claude/gadugi
uv venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "📚 Installing dependencies..."
uv pip install pyyaml requests click rich pytest ruff

# Download all Gadugi agents
echo "🤖 Downloading Gadugi agents..."
cd ../..

# List of core agents to install
agents=(
    "orchestrator-agent"
    "workflow-manager"
    "code-reviewer"
    "code-review-response"
    "worktree-manager"
    "task-analyzer"
    "execution-monitor"
    "prompt-writer"
    "test-writer"
    "test-solver"
    "type-fix-agent"
    "memory-manager"
    "pr-backlog-manager"
    "system-design-reviewer"
    "readme-agent"
)

# Download each agent
for agent in "${agents[@]}"; do
    echo "  📥 Downloading $agent..."
    # Log curl errors to install log instead of suppressing
    if ! curl -fsSL "https://raw.githubusercontent.com/rysweet/gadugi/main/.claude/agents/$agent.md" \
         -o ".claude/agents/$agent.md" 2>>.claude/gadugi/install.log; then
        echo "    ⚠️  $agent download failed, check .claude/gadugi/install.log for details"
    fi
done

# Create configuration file
echo "⚙️  Creating configuration..."
cat > .claude/gadugi/config/gadugi.yaml << 'EOF'
version: "0.3.0"
installation:
  date: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  method: "gadugi-updater"
environment:
  python_path: ".claude/gadugi/.venv/bin/python"
  agents_path: ".claude/agents"
settings:
  auto_update: false
  update_check_interval: "7d"
EOF

echo ""
echo "✅ Gadugi installation complete!"
echo ""
echo "📦 Installed components:"
echo "  • $(ls -1 .claude/agents/*.md 2>&1 | grep -v "No such file" | wc -l) agents in .claude/agents/"
echo "  • Python environment in .claude/gadugi/.venv/"
echo "  • Configuration in .claude/gadugi/config/"
echo ""
echo "🎯 To get started, try:"
echo "  /agent:orchestrator-agent"
echo "  /agent:workflow-manager"
echo "  /agent:code-reviewer"
