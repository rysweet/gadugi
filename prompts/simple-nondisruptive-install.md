# Simple Non-Disruptive Gadugi Installation

Based on Gadugi Guidelines: **Ruthless Simplicity**, **Zero BS**, **No Future-Proofing**

## Core Requirement
Install Gadugi into any repository without polluting it. Everything goes in `.claude/` directory.

## Simple Solution - One Script

### `install.sh` (in repo root)
```bash
#!/bin/bash
# Simple, direct installation - no BS

# 1. Create .claude directory structure
mkdir -p .claude/{agents,scripts,config}

# 2. Install UV if needed (simple check)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# 3. Create Python environment in .claude
cd .claude
uv venv
uv pip install gadugi

# 4. Copy agents from GitHub
curl -fsSL https://github.com/rysweet/gadugi/archive/main.tar.gz | tar xz --strip=2 "gadugi-main/.claude/agents"

# 5. Create simple bootstrap script
cat > scripts/gadugi << 'EOF'
#!/bin/bash
source .claude/.venv/bin/activate
python -m gadugi "$@"
EOF
chmod +x scripts/gadugi

echo "✅ Gadugi installed in .claude/"
echo "Run: .claude/scripts/gadugi --help"
```

## That's It

No:
- Uninstall script (just rm -rf .claude if needed)
- Complex fallbacks
- Version management
- Health checks
- Repair scripts
- Progress bars
- Parallel downloads
- Checksum verification

Just:
1. Make directories
2. Install UV
3. Install Python package
4. Get agents
5. Create runner script

## Installation Instructions for README

### Installation
```bash
curl -fsSL https://raw.githubusercontent.com/rysweet/gadugi/main/install.sh | sh
```

### Usage
```bash
.claude/scripts/gadugi agent-manager bootstrap
```

## Directory Structure (Simple)
```
your-repo/
├── .claude/
│   ├── .venv/          # Python environment
│   ├── agents/         # Agent definitions
│   ├── scripts/        # gadugi runner
│   └── config/         # Future config (if needed)
└── [your files unchanged]
```

## Testing Plan
1. Run install.sh in empty directory
2. Verify .claude created
3. Run gadugi command
4. Verify no files outside .claude

## Implementation Tasks
1. Create install.sh with above content
2. Test it works
3. Update README Installation section
4. Done

Following Guidelines:
- **Ruthless Simplicity**: One script, direct implementation
- **Zero BS**: Everything works or fails clearly
- **No Future-Proofing**: Solves today's problem only
- **Trust External Systems**: Direct curl, no elaborate error handling
- **Present-Moment Focus**: Install what's needed now
