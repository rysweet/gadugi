# Implement Team Coach - Performance Analytics

## Objective
Implement the missing Team Coach component for Gadugi v0.3's performance analytics and optimization.

## Requirements
1. **Core Functionality**
   - Performance metrics collection
   - Pattern recognition
   - Optimization suggestions
   - Team coordination insights

2. **Location**
   - `.claude/agents/TeamCoach/`
   - Must integrate with WorkflowManager Phase 13

3. **Components**
   ```
   .claude/agents/TeamCoach/
   ├── __init__.py
   ├── coach.py           # Main Team Coach implementation
   ├── metrics.py         # Performance metrics collection
   ├── analyzer.py        # Pattern analysis
   ├── optimizer.py       # Optimization engine
   ├── team_coach.md      # Agent specification
   └── tests/
       └── test_coach.py  # Unit tests
   ```

## Integration Points
1. **WorkflowManager Phase 13**
   - Hook into workflow completion
   - Collect performance data
   - Generate insights

2. **Neo4j Integration**
   - Store performance metrics
   - Query historical patterns
   - Track team patterns

3. **Event Router**
   - Subscribe to workflow events
   - Emit optimization suggestions

## Implementation Details
```python
# coach.py
class TeamCoach:
    """Performance analytics and team optimization."""

    def analyze_workflow(self, workflow_id: str) -> dict:
        """Analyze completed workflow performance."""
        pass

    def suggest_optimizations(self, metrics: dict) -> list:
        """Generate optimization suggestions."""
        pass

    def track_patterns(self, team_data: dict) -> dict:
        """Identify team collaboration patterns."""
        pass
```

## Metrics to Track
- Workflow completion time
- Error rates by phase
- Code quality metrics
- Review cycle time
- Test coverage changes
- Parallel execution efficiency

## Testing
```bash
# Run Team Coach tests
uv run pytest .claude/agents/TeamCoach/tests/ -v

# Integration test with WorkflowManager
uv run python -m pytest tests/integration/test_team_coach_integration.py
```

## Success Criteria
- Team Coach properly integrated in Phase 13
- Metrics collection working
- Pattern recognition functional
- Tests passing
- Zero pyright errors
- Can generate meaningful insights

This is a UV project - use `uv run` for all Python commands.

Create PR when complete.
