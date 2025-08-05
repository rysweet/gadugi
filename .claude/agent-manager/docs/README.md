# Agent Manager Documentation

This directory contains documentation for the Agent Manager sub-agent.

## Structure

```
.claude/agent-manager/
├── cache/                  # Local cache for downloaded agents
├── config/                 # Configuration files
├── docs/                   # Documentation
├── templates/              # Configuration templates
└── tests/                  # Agent-specific tests
```

## Main Documentation

The primary usage documentation is located at:
- `/docs/AGENT_MANAGER_USAGE.md` - Comprehensive usage guide

## Agent File

The agent implementation is at:
- `.claude/agents/agent-manager.md` - Main agent file

## Testing

To run agent-manager specific tests:
```bash
python .claude/agent-manager/tests/test_structure.py
```
