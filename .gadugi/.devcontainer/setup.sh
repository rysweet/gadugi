#!/bin/bash
# DevContainer setup script for Gadugi PR Backlog Manager

set -e

echo "🚀 Setting up Gadugi PR Backlog Manager development environment..."

# Update package lists
sudo apt-get update

# Install additional system dependencies
sudo apt-get install -y \
    curl \
    jq \
    git \
    build-essential \
    software-properties-common

# Install Claude Code CLI
echo "📦 Installing Claude Code CLI..."
curl -fsSL https://claude.ai/cli/install.sh | bash
echo 'export PATH="$HOME/.claude/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.claude/bin:$PATH"' >> ~/.zshrc

# Make Claude Code CLI available immediately
export PATH="$HOME/.claude/bin:$PATH"

# Configure Claude Code for GitHub Actions environment
echo "⚙️  Configuring Claude Code for container environment..."
mkdir -p ~/.claude
cat > ~/.claude/config.yml << EOF
auto_approve: true
github_actions: true
log_level: info
workspace: /workspaces/gadugi
EOF

# Install Python dependencies for shared modules
echo "🐍 Installing Python dependencies..."
cd /workspaces/gadugi
pip3 install --upgrade pip
pip3 install \
    pytest \
    pytest-cov \
    pytest-mock \
    requests \
    pyyaml \
    typing-extensions \
    dataclasses

# Set up pre-commit hooks for development
echo "🔧 Setting up development tools..."
pip3 install pre-commit black pylint mypy
pre-commit install || echo "Pre-commit setup skipped (not in git repo)"

# Create logs directory for debugging
mkdir -p ~/.claude/logs
mkdir -p /workspaces/gadugi/.github/workflow-states

# Set up environment variables
echo "🌍 Setting up environment variables..."
cat >> ~/.bashrc << EOF
export CLAUDE_AUTO_APPROVE=true
export CLAUDE_GITHUB_ACTIONS=true
export PYTHONPATH="/workspaces/gadugi/.claude/shared:\$PYTHONPATH"
EOF

cat >> ~/.zshrc << EOF
export CLAUDE_AUTO_APPROVE=true
export CLAUDE_GITHUB_ACTIONS=true
export PYTHONPATH="/workspaces/gadugi/.claude/shared:\$PYTHONPATH"
EOF

# Validate installation
echo "✅ Validating installation..."
which gh || echo "❌ GitHub CLI not found"
which python3 || echo "❌ Python 3 not found"
which pip3 || echo "❌ pip3 not found"

# Test Claude Code CLI (if API key is available)
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "🧪 Testing Claude Code CLI..."
    claude --version || echo "⚠️  Claude Code CLI test failed (expected without API key)"
else
    echo "⚠️  ANTHROPIC_API_KEY not set, Claude Code CLI test skipped"
fi

echo "🎉 Gadugi PR Backlog Manager development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Set ANTHROPIC_API_KEY environment variable"
echo "   2. Configure GitHub CLI: gh auth login"
echo "   3. Run tests: pytest tests/"
echo "   4. Start developing!"
echo ""
