# Task Decomposer Module


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

## Overview

The Task Decomposer is an intelligent agent that breaks down complex tasks into manageable subtasks, identifies dependencies, and estimates parallelization potential. It uses pattern learning to improve decomposition quality over time.

## Features

- **Task Analysis**: Breaks complex tasks into atomic, executable subtasks
- **Dependency Detection**: Identifies and models dependencies between subtasks
- **Parallelization Optimization**: Estimates potential for parallel execution (0-1 scale)
- **Pattern Learning**: Learns from successful decompositions to improve future results
- **Resource Estimation**: Estimates time and complexity for each subtask

## Installation

The module is included as part of the Gadugi project. Ensure you have the project dependencies installed:

```bash
uv sync --all-extras
```

## Usage

### Basic Task Decomposition

```python
from decomposer import TaskDecomposer

# Initialize the decomposer
decomposer = TaskDecomposer()

# Decompose a complex task
task = "Implement user authentication with OAuth2, JWT tokens, and role-based access control"
result = await decomposer.decompose_task(task)

# Access decomposition results
print(f"Original task: {result.original_task}")
print(f"Number of subtasks: {len(result.subtasks)}")
print(f"Parallelization potential: {result.parallelization_score:.2f}")
print(f"Estimated total time: {result.estimated_total_time} minutes")

# Examine subtasks
for subtask in result.subtasks:
    print(f"- {subtask.name} (complexity: {subtask.complexity})")
    if subtask.dependencies:
        print(f"  Depends on: {', '.join(subtask.dependencies)}")
```

### Pattern-Based Decomposition

The decomposer recognizes common task patterns and applies appropriate decomposition strategies:

- **Feature Implementation**: Design → Implement → Test → Document → Review
- **Bug Fix**: Reproduce → Diagnose → Fix → Test → Verify
- **Refactoring**: Analyze → Plan → Refactor → Test → Validate
- **Testing**: Setup → Execute → Analyze → Report → Cleanup
- **Documentation**: Outline → Draft → Review → Revise → Publish

### Learning from Execution

```python
# After executing the decomposed tasks, provide feedback
success_metrics = {
    "success": True,
    "execution_time": 150,  # Actual time in minutes
    "quality_score": 0.9
}

# The decomposer learns from this feedback
await decomposer.learn_pattern(result, success_metrics)
```

### Finding Similar Patterns

```python
# Find patterns similar to a new task
similar_patterns = await decomposer.find_similar_patterns(
    "Build a REST API with authentication"
)

print(f"Similar patterns found: {similar_patterns}")
```

## API Reference

### Classes

#### `TaskDecomposer`

Main class for task decomposition.

**Methods:**

- `decompose_task(task_description: str, context: Optional[Dict] = None) -> DecompositionResult`
  - Decomposes a task into subtasks with dependency analysis

- `analyze_dependencies(subtasks: List[SubTask]) -> Dict[str, List[str]]`
  - Analyzes and returns dependencies between subtasks

- `estimate_parallelization(subtasks: List[SubTask], dependencies: Dict) -> float`
  - Estimates parallelization potential (0.0 = sequential, 1.0 = fully parallel)

- `learn_pattern(result: DecompositionResult, success_metrics: Dict) -> None`
  - Learns from successful decomposition patterns

- `find_similar_patterns(task_description: str) -> List[str]`
  - Finds patterns similar to the given task

#### `SubTask`

Represents a single subtask within a decomposition.

**Attributes:**
- `id`: Unique identifier
- `name`: Task name
- `description`: Detailed description
- `dependencies`: List of subtask IDs this depends on
- `estimated_time`: Estimated time in minutes
- `complexity`: "low", "medium", or "high"
- `can_parallelize`: Whether this can run in parallel
- `resource_requirements`: Dictionary of required resources

#### `DecompositionResult`

Result of a task decomposition operation.

**Attributes:**
- `original_task`: The original task description
- `subtasks`: List of SubTask objects
- `dependency_graph`: Dictionary mapping task IDs to dependencies
- `parallelization_score`: Score from 0.0 to 1.0
- `estimated_total_time`: Total estimated time in minutes
- `decomposition_pattern`: Name of the pattern used (if any)

## Pattern Database

The decomposer maintains a pattern database that evolves over time:

- Patterns are stored in `.decomposer_patterns.json`
- Each pattern includes triggers, subtask templates, and success metrics
- Patterns are updated based on execution feedback
- New patterns are learned from successful decompositions

## Testing

Run the test suite:

```bash
uv run pytest tests/test_task_decomposer.py -v
```

Run with coverage:

```bash
uv run pytest tests/test_task_decomposer.py --cov=decomposer --cov-report=html
```

## Integration with Orchestrator

The Task Decomposer is designed to work with the Orchestrator Agent for parallel task execution:

1. Orchestrator sends complex task to decomposer
2. Decomposer returns subtasks and dependency graph
3. Orchestrator executes subtasks respecting dependencies
4. Results are fed back to decomposer for learning

## Contributing

When extending the Task Decomposer:

1. Add new patterns to the default patterns in `PatternDatabase`
2. Ensure all code passes type checking: `uv run pyright decomposer/`
3. Format code with ruff: `uv run ruff format decomposer/`
4. Add comprehensive tests for new functionality
5. Update this documentation

## License

Part of the Gadugi project.
