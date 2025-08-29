# Hierarchical Memory System

This directory contains the hierarchical Markdown-based memory system for the Gadugi multi-agent platform.

## Directory Structure

```
.memory/
├── project/              # Project-level memories (all agents need to know)
├── team/                # Coding team memories (workflow, guidelines)
├── agents/              # Agent-specific memories (individual agent knowledge)
├── organization/        # Cross-project organizational knowledge
├── knowledge/           # Reference documentation and troubleshooting
└── tasks/               # Temporary task memory (NOT checked into git)
```

## Memory Levels

### Project Memory (`project/`)
- Global project context and goals
- Architecture decisions
- Major milestones and priorities
- All agents can read, orchestration agents can write

### Team Memory (`team/`)
- Development workflow and practices
- Coding standards and guidelines
- Toolchain and environment setup
- Team-wide conventions

### Agent Memory (`agents/`)
- Individual agent-specific knowledge
- Agent learning and adaptations
- Performance history
- Each agent manages its own memory file

### Organization Memory (`organization/`)
- Cross-project best practices
- Architectural patterns
- Lessons learned
- Institutional knowledge

### Knowledge Memory (`knowledge/`)
- Library documentation
- API references
- Troubleshooting guides
- Technical reference material

### Task Memory (`tasks/`)
- Temporary working memory
- Current session state
- Not version controlled
- Cleared between sessions

## Memory Format

Each memory file follows a consistent Markdown format:

```markdown
# [Title]
*Last Updated: 2025-08-03T14:30:00-08:00*
*Memory Level: [level]*

## Overview
Brief description of the memory's purpose.

## [Section Name]
*Updated: 2025-08-03T14:25:00-08:00*

- 2025-08-03T14:25:00 - Entry with timestamp (most recent first)
- 2025-08-03T14:20:00 - Previous entry

---
*Memory managed by: [agent-name]*
*Security level: [public|team|restricted]*
```

## Usage

The memory system is accessed through the Python utilities in `.memory_utils/`:

- `memory_manager.py` - Core memory file operations
- `agent_interface.py` - Agent-specific memory access with permissions
- `security_manager.py` - Security and validation (Phase 2)
- `migration_tool.py` - Migration from old system (Phase 2)

### Python API Example

```python
from memory_utils.agent_interface import AgentMemoryInterface

# Create interface for an agent
agent = AgentMemoryInterface("agent-id", "OrchestratorAgent")

# Read project context
context = agent.get_project_context()

# Record agent memory
agent.record_agent_memory("Task Results", "Completed task successfully")

# Search memories
results = agent.search_accessible_memories("workflow")
```

### Command Line Usage

```bash
# List all memories
python .memory_utils/memory_manager.py list

# Read a specific memory
python .memory_utils/memory_manager.py read project context

# Add memory entry
python .memory_utils/memory_manager.py add team workflow "Development Process" "New guideline"

# Search memories
python .memory_utils/memory_manager.py search "orchestrator"
```

## Security

- No secrets or credentials should be stored in memory files
- XPIA protection through content validation
- Agent-specific permissions control read/write access
- Task memories are excluded from version control

## Migration

To migrate from the old Memory.md system:

1. Run the migration tool (Phase 2): `python .memory_utils/migration_tool.py`
2. Verify content was migrated correctly
3. Remove old `.github/Memory.md` and MemoryManager directory
4. Update agent configurations to use new system

## Best Practices

1. **Timestamps**: Always include timestamps for traceability
2. **Sections**: Organize memories into logical sections
3. **Conciseness**: Keep entries brief and focused
4. **Regular Updates**: Prune old entries periodically
5. **No Secrets**: Never store passwords, keys, or tokens
