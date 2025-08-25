# Team Coach Agent

The Team Coach Agent provides intelligent analysis of development sessions and generates actionable improvement recommendations. It integrates with the BaseAgent framework to provide comprehensive coaching capabilities for development teams.

## Features

- **Session Analysis**: Analyzes completed development sessions to extract key metrics and patterns
- **Improvement Identification**: Identifies areas for process, tooling, documentation, performance, and quality improvements
- **GitHub Integration**: Automatically creates issues for identified improvements (currently mocked)
- **Performance Tracking**: Tracks performance trends over time
- **Pattern Learning**: Learns from successful and unsuccessful workflow patterns
- **BaseAgent Integration**: Full integration with security, performance monitoring, and learning capabilities

## Installation

The Team Coach agent is located in `.claude/agents/teamcoach/` and can be used independently or as part of the larger agent framework.

```bash
# Navigate to the agent directory
cd .claude/agents/teamcoach/

# The main agent class is in team_coach.py
# Tests are available in tests/test_team_coach.py
# Recipe configuration is in .claude/recipes/team-coach/recipe.yaml
```

## Usage

### Basic Usage

```python
from .claude.agents.teamcoach.team_coach import TeamCoach

# Initialize the Team Coach
coach = TeamCoach()

# Analyze a development session
session_data = {
    "session_id": "project_session_001",
    "start_time": "2025-01-08T09:00:00Z",
    "end_time": "2025-01-08T12:00:00Z",
    "tasks": ["implement-feature-x", "fix-bug-y", "add-tests"],
    "errors": ["import-error", "type-error"],
    "test_failures": 1,
    "code_changes": 25,
    "pr_created": True,
    "review_comments": 3
}

# Execute session analysis
result = coach.execute({
    "action": "analyze_session",
    "session_data": session_data
})

print(f"Session performance score: {result['metrics']['performance_score']:.2f}")
```

### Improvement Identification

```python
# Identify improvements for a session
metrics_data = result["metrics"]
improvements_result = coach.execute({
    "action": "identify_improvements",
    "metrics": metrics_data
})

for suggestion in improvements_result["suggestions"]:
    print(f"Improvement: {suggestion['title']}")
    print(f"Priority: {suggestion['priority']}")
    print(f"Impact: {suggestion['estimated_impact']:.1%}")
    print(f"Steps: {', '.join(suggestion['implementation_steps'])}")
    print()
```

### Performance Trend Analysis

```python
# Track performance trends (requires multiple sessions)
trends_result = coach.execute({
    "action": "track_performance_trends"
})

for trend in trends_result["trends"]:
    print(f"Metric: {trend['metric_name']}")
    print(f"Direction: {trend['trend_direction']}")
    print(f"Change: {trend['change_percentage']:.1f}%")
```

### Coaching Report Generation

```python
# Generate a comprehensive coaching report
report_result = coach.execute({
    "action": "generate_coaching_report"
})

report = report_result["report"]
print(f"Sessions analyzed: {report['sessions_analyzed']}")
print(f"Average performance: {report['average_performance']:.2f}")
print("Recommendations:")
for rec in report["recommendations"]:
    print(f"  - {rec}")
```

### GitHub Issue Creation (Mock)

```python
# Create a GitHub issue for an improvement
suggestion_data = {
    "title": "Improve Error Handling",
    "description": "Session had high error rate, implement better error handling",
    "type": "tooling",
    "priority": "medium"
}

issue_result = coach.execute({
    "action": "create_improvement_issue",
    "suggestion": suggestion_data
})

print(f"Created issue: {issue_result['issue_url']}")
```

### Async Interface

The Team Coach also provides async methods for compatibility:

```python
import asyncio

async def example_async_usage():
    coach = TeamCoach()

    # Async session analysis
    metrics = await coach.analyze_session(session_data)
    print(f"Analyzed session: {metrics.session_id}")

    # Async improvement identification
    improvements = await coach.identify_improvements(metrics)
    print(f"Found {len(improvements)} improvement opportunities")

    # Async trend analysis
    trends = await coach.track_performance_trends()
    print(f"Generated {len(trends)} performance trends")

    # Async coaching report
    report = await coach.generate_coaching_report()
    print(f"Report generated at: {report['generated_at']}")

# Run async example
asyncio.run(example_async_usage())
```

## Agent Actions

The Team Coach supports these actions through the `execute()` method:

| Action | Description | Input | Output |
|--------|-------------|-------|---------|
| `analyze_session` | Analyze a development session | `session_data` dict | Session metrics |
| `identify_improvements` | Find improvement opportunities | `metrics` dict | List of suggestions |
| `create_improvement_issue` | Create GitHub issue | `suggestion` dict | Issue URL |
| `track_performance_trends` | Analyze performance trends | None | List of trends |
| `generate_coaching_report` | Generate coaching report | None | Comprehensive report |
| `learn_from_patterns` | Learn from session patterns | `sessions` list | Pattern insights |

## Configuration

The Team Coach can be configured through the constructor:

```python
config = {
    "performance_thresholds": {
        "max_execution_time": 600
    },
    "learning_enabled": True
}

coach = TeamCoach(config)
```

## Testing

Comprehensive tests are available in `tests/test_team_coach.py`:

```bash
# Run Team Coach tests
uv run pytest tests/test_team_coach.py -v

# Run with coverage
uv run pytest tests/test_team_coach.py --cov=.claude.agents.teamcoach
```

## Integration with BaseAgent Framework

The Team Coach inherits from `IntegratedAgent` which provides:

- **Security Validation**: Input validation against dangerous patterns
- **Performance Monitoring**: Automatic execution time and resource tracking
- **Learning Capabilities**: Pattern recognition and adaptive behavior
- **Error Handling**: Comprehensive error handling with logging

```python
# Example of inherited capabilities
coach = TeamCoach()

# Security validation
is_safe = coach.validate_input({"action": "analyze_session", "data": "clean"})

# Performance monitoring
coach.start_monitoring()
result = coach.execute(context)
coach.stop_monitoring()

# Learning summary
learning_summary = coach.get_learning_summary()
print(f"Total executions: {learning_summary['total_executions']}")
```

## Performance Scoring Algorithm

The Team Coach uses a weighted scoring algorithm for session performance:

- **Task Completion** (up to 40%): +0.1 per task completed (max 0.4)
- **PR Creation** (30%): +0.3 if PR was created
- **Error Penalty** (up to 30%): -0.05 per error (max penalty 0.3)
- **Test Failure Penalty** (up to 20%): -0.1 per test failure (max penalty 0.2)

Score range: 0.0 to 1.0

## Improvement Categories

The Team Coach identifies improvements in these categories:

- **PROCESS**: Workflow optimization, task decomposition
- **TOOLING**: Agent improvements, automation opportunities
- **DOCUMENTATION**: Missing or outdated documentation
- **PERFORMANCE**: Execution efficiency, resource usage
- **QUALITY**: Test coverage, error rates, code quality

## Status and Monitoring

Get current agent status:

```python
status = coach.get_status_summary()
print(f"Agent: {status['name']}")
print(f"Sessions analyzed: {status['sessions_analyzed']}")
print(f"Improvements identified: {status['improvements_identified']}")
print(f"Last analysis: {status['last_analysis']}")
```

## Error Handling

The Team Coach handles errors gracefully:

```python
# Invalid action
result = coach.execute({"action": "invalid_action"})
# Returns: {"success": False, "error": "Unknown action: invalid_action", "available_actions": [...]}

# Malformed data
result = coach.execute({"action": "analyze_session", "session_data": None})
# Handles gracefully without crashing
```

## Recipe Configuration

The Team Coach uses a recipe-based configuration system in `.claude/recipes/team-coach/recipe.yaml` that defines:

- Capabilities and triggers
- Metrics collection
- Improvement categories
- GitHub integration templates
- Security and performance settings

See the recipe file for detailed configuration options.

## Future Enhancements

The current implementation provides a solid foundation for:

- Real GitHub API integration (currently mocked)
- Integration with existing Phase 1-3 implementations
- Neo4j storage for pattern persistence
- Advanced machine learning for pattern recognition
- Extended metric collection and analysis
- Real-time coaching during development sessions

## Contributing

When extending the Team Coach:

1. Add new actions to the `_execute_core` method
2. Implement corresponding handler methods
3. Add comprehensive tests for new functionality
4. Update this documentation
5. Ensure all quality gates pass (pyright, ruff, pytest)

## License

This implementation is part of the Gadugi project and follows the project's licensing terms.
