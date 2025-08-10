# Implement Team Coach Agent

## Task Description
Implement the Team Coach agent for session analysis and performance tracking.

## Requirements
1. Create full implementation in .claude/agents/team-coach/
2. Implement session analysis capabilities
3. Add GitHub integration for tracking
4. Performance metrics collection
5. Integration with workflow Phase 13

## Implementation Details
- Main file: team_coach.py
- Session analysis: Analyze completed workflows
- Metrics: Track success rates, duration, quality
- GitHub: Create issues for improvements
- Memory: Update Memory.md with insights

## Technical Requirements
- Must be pyright clean (0 errors)
- Must have comprehensive tests
- Must integrate with existing framework
- Use BaseAgent from .claude/framework/

## Execution Requirements
- Use `uv run` for all Python commands
- Run `uv run pyright .claude/agents/team-coach/`
- Create and run tests
- Clean up worktree after completion

/agent:workflow-manager

Execute complete workflow to implement Team Coach agent