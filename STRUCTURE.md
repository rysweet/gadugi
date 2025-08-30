# Gadugi Repository Structure

## Clear Separation of Concerns

### `.gadugi/` - The Gadugi System
**Purpose:** Self-contained AI orchestration system with isolated Python environment

Contains all Gadugi runtime code:
- `agents/` - All AI agents (task-analyzer, pr-backlog-manager, etc.)
- `orchestrator/` - Task orchestration and workflow management
- `services/` - Event router, LLM proxy, and other services
- `shared/` - Shared utilities, interfaces, and common code
- `workflow-enforcement/` - Workflow validation and enforcement
- `events/` - Event system configuration
- `type-fixing-tools/` - Tools for fixing type errors
- `container_runtime/` - Container execution environment
- `monitoring/` - System monitoring and health checks
- `tests/` - All test files
- `pyproject.toml` & `uv.lock` - Python dependencies (isolated UV environment)

### `.claude/` - Claude AI Assistant Configuration
**Purpose:** Instructions and configuration for Claude AI assistant

Contains only Claude-specific files:
- `CLAUDE.md` - Main instructions for Claude AI
- `Guidelines.md` - Coding guidelines
- `instructions/` - Task-specific instructions loaded on demand
- `hooks/` - Git hooks and workflow scripts
- `settings.json` - Claude configuration
- Documentation and templates

### Root Directory - Clean Integration
Minimal files for easy integration into other projects:
- `gadugi` - CLI wrapper script (runs everything in isolated UV environment)
- `README.md` - Project documentation
- `CLAUDE.md` - Instructions for Claude AI
- `.git/` - Git repository
- Configuration files (pyrightconfig.json, etc.)

## Key Design Principles

1. **Complete Isolation**: Gadugi runs in its own UV environment (`.gadugi/.venv`), completely independent of the host project's dependencies.

2. **Clean Integration**: Only essential files in root directory, making it easy to add Gadugi to any project.

3. **Clear Boundaries**: 
   - `.gadugi/` = The system being built/maintained
   - `.claude/` = Instructions for the AI assistant

4. **No Symlinks**: All paths are properly configured, no symlinks needed.

## Usage

All Gadugi commands run through the `gadugi` CLI wrapper:
```bash
# Run tests
./gadugi test

# Run orchestrator
./gadugi orchestrator prompt.md

# Access Python environment
./gadugi python script.py

# Install/update dependencies
./gadugi install
```

## Import Structure

Within `.gadugi/` Python code:
```python
# Import from shared utilities
from shared.utils.error_handling import GadugiError
from shared.interfaces import AgentInterface

# Import from agents
from agents.task_analyzer.core import TaskAnalyzer

# Import from services
from services.event_router.router import EventRouter
```

## Test Organization

Tests mirror the source structure:
- `.gadugi/tests/agents/` - Tests for agents
- `.gadugi/tests/shared/` - Tests for shared utilities
- `.gadugi/tests/services/` - Tests for services
- `.gadugi/tests/integration/` - Integration tests

## Benefits of This Structure

1. **Portability**: Can be added to any project without dependency conflicts
2. **Clarity**: Clear separation between system code and AI instructions
3. **Maintainability**: All related code in one place
4. **Isolation**: No interference with host project
5. **Simplicity**: Single CLI entry point for all operations