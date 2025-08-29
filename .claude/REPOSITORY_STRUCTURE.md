# Repository Structure

This document describes the organization of the Gadugi repository after cleanup.

## Root Directory

The root directory contains only essential files:

### Configuration Files
- `.gitignore` - Git ignore patterns
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `pyproject.toml` - Python project configuration
- `pyrightconfig.json` - Type checking configuration
- `uv.lock` - UV dependency lock file
- `docker-compose.yml` - Main Docker configuration
- `docker-compose.gadugi.yml` - Gadugi-specific Docker configuration

### JavaScript/TypeScript (if needed)
- `package.json`, `package-lock.json` - Node dependencies
- `tsconfig.json` - TypeScript configuration
- `.eslintrc.json` - ESLint configuration

### Documentation
- `README.md` - Project readme
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - Project license
- `CLAUDE.md` - Claude AI instructions (main)

### Other
- `.env.example` - Environment variable template
- `.secrets.baseline` - Secret scanning baseline
- `.vscodeignore` - VS Code ignore patterns

## .claude Directory

The `.claude` directory contains all Claude/Gadugi-specific functionality:

### Core Directories
- `.claude/agents/` - All agent definitions
- `.claude/engines/` - Python engine implementations
- `.claude/executors/` - Executor implementations
- `.claude/services/` - Service layer (MCP, Neo4j, event-router)
- `.claude/shared/` - Shared utilities and modules
- `.claude/instructions/` - Modular instruction files
- `.claude/orchestrator/` - Orchestrator implementation
- `.claude/framework/` - Framework components

### Tool Directories
- `.claude/type-fixing-tools/` - All type-fixing Python scripts
- `.claude/type-fixing-artifacts/` - Type-fixing artifacts and archives
- `.claude/agent-manager/` - Agent management tools
- `.claude/utils/` - Various utility scripts

### Documentation
- `.claude/Guidelines.md` - Development guidelines
- `.claude/REPOSITORY_STRUCTURE.md` - This file
- `.claude/claude-generic-instructions.md` - Generic instructions
- `.claude/CLAUDE-legacy.md` - Legacy instructions for reference

## Other Directories

### Documentation
- `docs/` - General documentation
- `docs/misc/` - Miscellaneous docs (reports, summaries, analyses)

### Prompts
- `prompts/` - Active prompts and recipes
- `prompts/archive/` - Archived prompts and plans

### Scripts
- `scripts/` - Utility scripts
- `scripts/orchestrator/` - Orchestrator-related scripts
- `scripts/pr-management/` - PR management tools
- `scripts/testing/` - Testing and validation scripts

### Code
- `gadugi/` - Main Python package (if applicable)
- `src/` - Source code
- `tests/` - Test files
- `neo4j/` - Neo4j database files
- `container_runtime/` - Container runtime files

### Git
- `.github/` - GitHub-specific files (workflows, Memory.md)
- `.worktrees/` - Git worktrees (excluded from pyright)

## Design Intent

The organization follows these principles:

1. **Clean Root**: Only essential configuration files at root
2. **Claude Isolation**: All Claude/Gadugi-specific code in `.claude/`
3. **Portability**: The `.claude/` directory can be copied to other repos
4. **Tool Organization**: Related tools grouped in dedicated directories
5. **Clear Separation**: Documentation, prompts, and scripts separated

## Type-Fixing Tools

All type-fixing tools are now in `.claude/type-fixing-tools/`:
- Main tool: `final_comprehensive_fix.py`
- Test fixes: `final_test_fixes.py`
- Import fixes: `fix_missing_imports.py`
- See `.claude/type-fixing-tools/README.md` for complete list

## Finding Files

### Quick Reference
- Type-fixing tools: `.claude/type-fixing-tools/`
- Agent definitions: `.claude/agents/`
- Services: `.claude/services/`
- Documentation: `docs/` and `.claude/` for Claude-specific
- Scripts: `scripts/` organized by purpose
- Prompts: `prompts/` for active, `prompts/archive/` for historical
