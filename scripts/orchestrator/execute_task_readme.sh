#!/bin/bash

# Parallel execution script for README Humility Update
# Working directory: /Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a8532ccb

cd "/Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a8532ccb" || exit 1

echo "Starting WorkflowManager for README Humility Update in $(pwd)"

# Execute WorkflowManager for README Humility Update
claude -p - <<'EOF'
/agent:workflow-manager

## Task Context
Task ID: task-20250807-132118-a8532ccb
Task: README Humility Update - Remove Performance Claims
Branch: feature/readme-humility-update-parallel
Worktree: /Users/ryan/src/gadugi2/gadugi/.worktrees/task-20250807-132118-a8532ccb

## UV Project Configuration
**UV PROJECT DETECTED**: This is a UV Python project.

CRITICAL REQUIREMENTS:
- UV environment is already set up with `uv sync --all-extras`
- Use 'uv run' prefix for ALL Python commands
- Examples: 'uv run pytest tests/', 'uv run python script.py'
- NEVER run Python commands directly (will fail)

## Task Requirements
Execute the complete 11-phase workflow to update README.md by:

1. **Analysis Phase**: Analyze current README.md for performance claims
2. **Issue Creation Phase**: Create GitHub issue for README humility update
3. **Branch Management Phase**: Working in feature/readme-humility-update-parallel
4. **Research Phase**: Review tone guidelines and identify sections to modify
5. **Implementation Phase**:
   - Remove unsubstantiated performance claims ("3-5x faster")
   - Remove "production ready" and "enterprise grade" references
   - Remove UV performance comparison section if it contains unverified claims
   - Update tone to be professional but modest
   - Focus on actual features rather than performance claims
6. **Testing Phase**:
   - Run `uv run pytest tests/` to ensure no test references are broken
   - Run `uv run ruff check .` for linting
   - Verify README.md is well-formatted
7. **Documentation Phase**: Document changes made
8. **PR Creation Phase**: Create PR for README humility update
9. **Review Phase**: Invoke code-reviewer agent
10. **Review Response Phase**: Address any review feedback
11. **Settings Update Phase**: Update Memory.md

## Specific Changes Required
- Remove any "3-5x faster" or similar performance multipliers
- Remove "production ready" claims
- Remove "enterprise grade" references
- Remove comparative performance statements
- Change "Achieves 3-5x performance improvements" to "Designed to improve development efficiency"
- Change "Production-ready enterprise system" to "Multi-agent development framework"
- Change "Blazing fast performance with UV" to "Uses UV for Python dependency management"

## Search Patterns to Review
- "performance", "faster", "speed", "enterprise", "production", "blazing", "efficient", "optimiz", "3-5x", "improvement"

## Success Criteria
- No unverified performance claims remain
- No "production ready" or "enterprise" claims
- Tone is professional but humble
- Focus is on features and capabilities
- README remains informative and useful

Please execute all 11 phases systematically, ensuring proper UV command usage throughout.
EOF

echo "✅ README humility update WorkflowManager execution completed"
