#!/bin/bash
# Gadugi Simple Installation - Following Guidelines philosophy
# Ruthless Simplicity, Zero BS, Direct Implementation

set -e  # Exit on error

echo "Installing Gadugi in .claude/ directory..."

# 1. Create .claude directory structure
mkdir -p .claude/{agents,scripts,config}

# 2. Install UV if needed (simple check)
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 3. Create Python environment in .claude
echo "Setting up Python environment..."
cd .claude
uv venv
source .venv/bin/activate

# 4. Install Gadugi (when package is available)
# For now, just install dependencies
uv pip install pyyaml requests

# 5. Download agents from GitHub
echo "Downloading agents..."
curl -fsSL https://github.com/rysweet/gadugi/archive/main.tar.gz | \
    tar xz --strip-components=2 "gadugi-main/.claude/agents" 2>/dev/null || true

# 6. Create bootstrap runner script
cat > scripts/gadugi << 'EOF'
#!/bin/bash
# Gadugi runner script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.venv/bin/activate"

# For now, just show help
echo "Gadugi - Multi-agent Development System"
echo "Usage: gadugi [command]"
echo ""
echo "Commands:"
echo "  agent-manager    Manage Gadugi agents"
echo "  help            Show this help"
EOF
chmod +x scripts/gadugi

# 7. Create agent-manager bootstrap
cat > scripts/agent-manager << 'EOF'
#!/bin/bash
# Agent Manager Bootstrap
echo "Gadugi Agent Manager"
echo "Agents available in .claude/agents/"
ls -1 .claude/agents/*.md 2>/dev/null | head -10
EOF
chmod +x scripts/agent-manager

echo ""
echo "✅ Gadugi installed successfully in .claude/"
echo ""
echo "To get started:"
echo "  .claude/scripts/gadugi help"
echo ""
echo "To bootstrap agents:"
echo "  .claude/scripts/agent-manager"
