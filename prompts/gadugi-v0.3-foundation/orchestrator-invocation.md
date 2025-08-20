# Orchestrator Invocation for Gadugi v0.3 Foundation Tasks

## Execution Request

Execute the following foundation tasks in parallel for Gadugi v0.3 implementation:

### Batch 1: Foundation Tasks (No Dependencies)

1. **qa-framework-setup.md** - Issue #242
   - Set up UV, ruff, pyright, pytest, and pre-commit hooks
   - Ensure all Python commands use `uv run` prefix
   - Focus on correctness and quality

2. **create-recipe-definitions.md** - Issue #234  
   - Create recipe structure in `.claude/recipes/`
   - Define requirements, design, and dependencies for all components
   - Follow new v0.3 requirements, not current implementation

3. **define-protobuf-schemas.md**
   - Create protobuf definitions in `.claude/protos/`
   - Generate Python bindings
   - Focus on new event system design

4. **neo4j-setup.md**
   - Set up Neo4j with docker-compose
   - Define graph schema for agents, memories, knowledge
   - Create Python client and test connection

## Execution Guidelines

- These tasks have no interdependencies and can run fully in parallel
- Each task should work in its own isolated worktree
- Focus on the NEW v0.3 requirements, not preserving current implementation
- Prioritize correctness and functionality over optimization
- All Python code must use UV for dependency management
- Ensure all tests pass before marking tasks complete

## Expected Outcomes

- QA framework fully configured and operational
- Complete recipe definitions for all v0.3 components
- Protobuf schemas defined with Python bindings generated
- Neo4j database running and accessible
- All code pyright clean and ruff formatted
- Tests passing for all implemented functionality