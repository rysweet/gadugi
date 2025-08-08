# Gadugi Installation Structure

## Directory Layout

To avoid conflicts with user's Python projects, Gadugi installs everything in a nested structure:

```
your-repo/
├── .venv/                      # User's own Python virtual environment (if exists)
├── .claude/
│   └── gadugi/                 # Complete isolation from user's project
│       ├── .venv/              # Gadugi's Python virtual environment
│       ├── agents/             # All agent definitions
│       ├── scripts/            # Gadugi scripts
│       ├── config/             # Configuration files
│       └── cache/              # Downloaded components
└── [user's project files]
```

## Benefits

1. **No Conflicts**: User's `.venv` and Gadugi's `.claude/gadugi/.venv` are completely separate
2. **Clean Namespace**: Everything Gadugi-related is under `.claude/gadugi/`
3. **Easy Removal**: `rm -rf .claude/gadugi` removes everything
4. **UV Isolation**: Gadugi's UV setup doesn't affect user's Python environment

## Installation Commands

When the agent-updater runs, it will:
- Create virtual environment at `.claude/gadugi/.venv`
- Install agents to `.claude/gadugi/agents/`
- Place scripts in `.claude/gadugi/scripts/`

This ensures complete isolation from the user's project while maintaining all functionality.
