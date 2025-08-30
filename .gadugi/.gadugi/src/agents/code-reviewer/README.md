# Code Reviewer Agent V0.3


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

A production-grade code reviewer agent that learns from past reviews and adapts its recommendations based on developer and module patterns. Built on the V03Agent base class with comprehensive memory integration.

## Features

### 🧠 **Memory-Enabled Learning**
- Persistent memory across sessions using the Gadugi memory system
- Long-term pattern recognition and adaptation
- Knowledge base loading from markdown files
- Collaborative whiteboard for team coordination

### 📊 **Adaptive Review System**
- Learns which issues developers accept/reject
- Adjusts severity scoring based on historical patterns
- Tracks recurring issues by developer and module
- Provides contextual recommendations

### 🔍 **Comprehensive Code Analysis**
- Integrates with existing CodeReviewerEngine
- Multi-dimensional analysis (quality, security, performance)
- Supports multiple programming languages
- Automated tool integration (ruff, mypy, bandit)

### 👥 **Developer Pattern Tracking**
- Per-developer issue preferences
- Common issue identification
- Ignored rule tracking
- Preferred pattern recognition

### 📁 **Module Pattern Recognition**
- Recurring issues by file/module
- Complexity trend tracking
- Security hotspot identification
- Performance pattern analysis

## Architecture

```
CodeReviewerV03 (inherits from V03Agent)
├── Memory Integration (AgentMemoryInterface)
├── Code Analysis Engine (CodeReviewerEngine)
├── Pattern Tracking
│   ├── Developer Patterns
│   └── Module Patterns
└── Knowledge Base
    ├── code_quality_patterns.md
    ├── security_patterns.md
    ├── performance_patterns.md
    └── review_checklist.md
```

## Quick Start

### Basic Usage

```python
from code_reviewer_v03 import CodeReviewerV03

async def review_code():
    # Create and initialize reviewer
    reviewer = CodeReviewerV03()
    await reviewer.initialize()

    # Start a review task
    task_id = await reviewer.start_task("Review PR #123 changes")

    # Review files
    review_task = {
        "type": "review_files",
        "files": ["src/auth.py", "src/validation.py"],
        "author": "alice_developer"
    }

    outcome = await reviewer.execute_task(review_task)

    if outcome.success:
        print("✅ Review completed!")
        print(f"Steps: {outcome.steps_taken}")

    # Learn from the outcome
    await reviewer.learn_from_outcome(outcome)

    # Clean shutdown
    await reviewer.shutdown()
```

### Learning from Feedback

```python
# Teach the agent from human feedback
feedback_task = {
    "type": "learn_from_feedback",
    "feedback": [
        {
            "issue_id": "review_123_issue_1",
            "rule_id": "E501",  # Line too long
            "developer": "alice_developer",
            "file_path": "src/validation.py",
            "accepted": False,
            "reason": "Our team prefers longer lines for SQL queries"
        }
    ]
}

await reviewer.execute_task(feedback_task)
```

### Getting Developer Insights

```python
# Get insights about a developer's patterns
insights = await reviewer.get_developer_insights("alice_developer")

print(f"Common issues: {insights['common_issues']}")
print(f"Ignored rules: {insights['ignored_rules']}")
print(f"Total reviews: {insights['total_reviews']}")
```

## Task Types

### 1. `review_files`
Reviews a list of files with adaptive scoring based on learned patterns.

**Parameters:**
- `files`: List of file paths to review
- `author`: Developer who made the changes
- `description`: (optional) Description of the changes

**Example:**
```python
task = {
    "type": "review_files",
    "files": ["src/auth.py", "tests/test_auth.py"],
    "author": "bob_developer",
    "description": "Added OAuth2 authentication"
}
```

### 2. `learn_from_feedback`
Learns from human feedback on previous review issues.

**Parameters:**
- `feedback`: List of feedback objects

**Feedback Object:**
```python
{
    "issue_id": "unique_issue_id",
    "rule_id": "E501",  # Rule that triggered the issue
    "issue_type": "warning",
    "category": "style",
    "developer": "developer_name",
    "file_path": "path/to/file.py",
    "accepted": True,  # Whether developer accepted the issue
    "reason": "Explanation for accept/reject"
}
```

### 3. `analyze_patterns`
Analyzes current patterns and generates insights about team trends.

**Example:**
```python
task = {"type": "analyze_patterns"}
outcome = await reviewer.execute_task(task)
# Returns insights about developer and module patterns
```

## Knowledge Base

The agent loads knowledge from markdown files in the `knowledge/` directory:

### `code_quality_patterns.md`
- Structural issues (complex functions, code duplication)
- Design issues (tight coupling, SRP violations)
- Error handling patterns
- Performance issues
- Maintainability problems
- Testing issues

### `security_patterns.md`
- Input validation vulnerabilities
- Authentication/authorization issues
- Data protection problems
- Web application security (XSS, CSRF)
- API security issues
- Common security anti-patterns

### `performance_patterns.md`
- Algorithm and data structure inefficiencies
- String processing issues
- Database and I/O problems
- Memory usage issues
- Caching opportunities
- Framework-specific performance

### `review_checklist.md`
- Comprehensive review checklist by priority
- Critical, high, medium, and low priority issues
- Language-specific checks
- Security deep dive
- Performance considerations
- Testing requirements

## Pattern Tracking

### Developer Patterns

The agent tracks patterns for each developer:

```python
class DeveloperPattern:
    developer: str
    common_issues: Dict[str, int]      # Rules frequently triggered
    ignored_rules: Set[str]            # Rules often rejected
    preferred_patterns: List[str]      # Patterns they use well
    last_reviewed: Optional[datetime]
```

### Module Patterns

The agent tracks patterns for each module/file:

```python
class ModulePattern:
    module_path: str
    frequent_issues: Dict[str, int]    # Common issues in this module
    complexity_trends: List[float]     # Complexity over time
    security_hotspots: List[str]       # Files with security issues
    last_reviewed: Optional[datetime]
```

## Adaptive Scoring

The agent adjusts issue severity based on learned patterns:

- **Developer Context**: If a developer consistently ignores a rule, reduce its severity for them
- **Module Context**: If a module frequently has certain issues, increase severity to catch patterns
- **Historical Context**: Learn from which issues get accepted vs rejected
- **Team Context**: Adapt to team preferences and standards

## Integration with Existing Systems

### Memory System Integration
```python
# The agent automatically integrates with the Gadugi memory system
await reviewer.initialize(mcp_url="http://localhost:8000")

# Stores memories of reviews, patterns, and learning
await reviewer.memory.remember_long_term(
    content="Review completed successfully",
    tags=["review", "success", developer],
    importance=0.8
)
```

### Code Review Engine
```python
# Uses the existing CodeReviewerEngine for analysis
self.review_engine = CodeReviewerEngine()
review_result = await self.review_engine.review_files(files)

# Then applies adaptive scoring
adapted_result = await self._apply_adaptive_scoring(
    review_result, author, files
)
```

### Collaboration System
```python
# Shares decisions via whiteboard
await reviewer.collaborate(
    "Code review completed. Security looks good, minor style issues.",
    decision="APPROVE_WITH_SUGGESTIONS"
)
```

## Configuration

The agent supports various configuration options:

```python
reviewer.config = {
    "learning_enabled": True,
    "pattern_tracking_enabled": True,
    "min_feedback_for_pattern": 3,
    "pattern_confidence_threshold": 0.7,
    "adaptive_scoring": True
}
```

## Testing

Run the test suite:

```bash
python test_code_reviewer_v03.py
```

The tests cover:
- Agent initialization and capabilities
- Task execution (review, learning, analysis)
- Pattern tracking and updating
- Integration with memory system
- Developer and module insights

## Examples

See `example_usage.py` for comprehensive examples:

1. **Basic Review**: Simple file review with learning
2. **Learning from Feedback**: Teaching the agent from human feedback
3. **Adaptive Scoring**: Demonstrating pattern-based adaptation
4. **Pattern Analysis**: Team-wide pattern analysis
5. **Production Workflow**: End-to-end production scenario

## Performance Considerations

### Memory Usage
- Patterns are stored in memory for fast access
- Old patterns are periodically cleaned up
- Memory interface handles persistence

### Scalability
- Can review multiple files in parallel (`max_parallel_tasks=5`)
- Patterns are indexed for efficient lookup
- Async operations throughout for responsiveness

### Learning Efficiency
- Requires minimum feedback items before establishing patterns
- Uses confidence thresholds to avoid overfitting
- Gradual adaptation rather than sudden changes

## Monitoring and Observability

The agent provides comprehensive logging and metrics:

```python
# Built-in performance monitoring
self.tasks_completed += 1
self.success_rate = (
    (self.success_rate * (self.tasks_completed - 1) + 1.0)
    / self.tasks_completed
)

# Memory of outcomes for analysis
await self.learn_from_outcome(outcome)
```

## Best Practices

### For Teams
1. **Provide Regular Feedback**: The more feedback, the better the learning
2. **Be Consistent**: Consistent feedback helps establish reliable patterns
3. **Review Insights**: Regularly check developer and module insights
4. **Update Knowledge Base**: Keep markdown knowledge files current

### For Integration
1. **Initialize Once**: Create one reviewer instance and reuse it
2. **Proper Shutdown**: Always call `shutdown()` to persist state
3. **Handle Errors**: The agent handles failures gracefully
4. **Monitor Performance**: Track review times and success rates

### For Customization
1. **Extend Knowledge Base**: Add domain-specific patterns
2. **Custom Rules**: Implement custom analysis rules
3. **Team Conventions**: Adapt patterns to team preferences
4. **Integration**: Connect with existing review systems

## Future Enhancements

- **Multi-language Support**: Extend beyond Python
- **Advanced Analytics**: More sophisticated pattern analysis
- **Team Dashboards**: Visual insights into team patterns
- **Automated Training**: Continuous learning from merged PRs
- **Integration APIs**: REST/GraphQL APIs for external tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update knowledge base as needed
5. Submit a pull request

## License

This code is part of the Gadugi project and follows the project's licensing terms.
