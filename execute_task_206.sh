#!/bin/bash

# Parallel execution script for Issue #206 Project Reorganization
# Working directory: /Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a66f199e

cd "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a66f199e" || exit 1

echo "Starting WorkflowManager for Issue #206 in $(pwd)"

# Execute WorkflowManager for Issue #206
claude -p - <<'EOF'
/agent:workflow-manager

## Task Context
Task ID: task-20250807-132118-a66f199e
Issue: #206 - Reorganize project structure for v0.1 milestone
Branch: feature/issue-206-project-reorganization-parallel
Worktree: /Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a66f199e

## UV Project Configuration
**UV PROJECT DETECTED**: This is a UV Python project.

CRITICAL REQUIREMENTS:
- UV environment is already set up with `uv sync --all-extras`
- Use 'uv run' prefix for ALL Python commands
- Examples: 'uv run pytest tests/', 'uv run python script.py'
- NEVER run Python commands directly (will fail)

## Task Requirements
Execute the complete 11-phase workflow to reorganize project structure by:

1. **Analysis Phase**: Analyze current root directory structure
2. **Issue Creation Phase**: Reference existing Issue #206
3. **Branch Management Phase**: Working in feature/issue-206-project-reorganization-parallel
4. **Research Phase**: Review project organization requirements
5. **Implementation Phase**:
   - Create directory structure (docs/, scripts/)
   - Move files using git mv to preserve history
   - Update all references in CLAUDE.md and other files
6. **Testing Phase**:
   - Run `uv run pytest tests/` to ensure imports work
   - Run `uv run ruff check .` for linting
   - Verify all moved file references are updated
7. **Documentation Phase**: Update any affected documentation
8. **PR Creation Phase**: Create PR for Issue #206
9. **Review Phase**: Invoke code-reviewer agent
10. **Review Response Phase**: Address any review feedback
11. **Settings Update Phase**: Update Memory.md

## Success Criteria
- Root directory contains only essential files (10-12 files max)
- All documentation properly organized in docs/ subdirectories
- All scripts organized in scripts/
- Zero broken imports or references
- All tests passing with `uv run pytest tests/`
- All workflows functioning
- Git history preserved for all moved files

Please execute all 11 phases systematically, ensuring proper UV command usage throughout.
EOF

echo "✅ Task 206 WorkflowManager execution completed"
