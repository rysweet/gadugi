# Gadugi Installation Structure

## Directory Layout

To avoid conflicts with user's Python projects while maintaining Claude compatibility:

```
your-repo/
├── .venv/                      # User's own Python virtual environment (if exists)
├── .claude/
│   ├── agents/                 # Agent markdown files (MUST be here for Claude)
│   │   ├── orchestrator-agent.md
│   │   ├── workflow-manager.md
│   │   └── ... (other agents)
│   └── gadugi/                 # Gadugi-specific files isolated here
│       ├── .venv/              # Gadugi's Python virtual environment
│       ├── scripts/            # Gadugi scripts and tools
│       ├── config/             # Configuration files
│       └── cache/              # Downloaded components
└── [user's project files]
```

## Benefits

1. **No Conflicts**: User's `.venv` and Gadugi's `.claude/gadugi/.venv` are completely separate
2. **Claude Compatibility**: Agents remain in `.claude/agents/` where Claude expects them
3. **Clean Separation**: Python environment and tools isolated in `.claude/gadugi/`
4. **Easy Removal**: `rm -rf .claude/gadugi` removes Gadugi tools, `rm -rf .claude/agents` removes agents
5. **UV Isolation**: Gadugi's UV setup doesn't affect user's Python environment

## Installation Commands

When the agent-updater runs, it will:
- Create virtual environment at `.claude/gadugi/.venv`
- Install agents to `.claude/agents/` (for Claude compatibility)
- Place scripts in `.claude/gadugi/scripts/`
- Store config in `.claude/gadugi/config/`

This ensures complete isolation from the user's project while maintaining Claude functionality.
