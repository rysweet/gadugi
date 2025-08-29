# Dependency Analysis Knowledge Base


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

This document provides comprehensive knowledge for intelligent dependency detection and analysis in the Orchestrator V0.3. It combines learned patterns, static analysis techniques, and dynamic dependency discovery to optimize parallel execution.

## Dependency Types and Detection

### 1. Explicit Dependencies
These are explicitly declared dependencies in task definitions.

**Detection Method**: Direct parsing of task dependency lists
**Confidence**: 100%
**Examples**:
- "Task B depends on Task A completion"
- "Integration tests require implementation to be complete"

### 2. File-Based Dependencies
Dependencies arising from tasks that read/write the same files.

**Detection Patterns**:
```python
# Sequential dependency (write-then-read)
task_a_writes = ["src/module.py", "tests/test_module.py"]
task_b_reads = ["src/module.py"]  # Depends on task_a

# Conflict dependency (write-write)
task_a_writes = ["config.json"]
task_b_writes = ["config.json"]  # Cannot run simultaneously
```

**Confidence Levels**:
- Same exact file: 95% confidence
- Same directory: 70% confidence
- Related file extensions: 50% confidence

**Common Patterns**:
- Implementation → Testing (implementation files → test files)
- Code Generation → Compilation (generated files → build process)
- Configuration → Deployment (config files → deployment scripts)

### 3. Import/Module Dependencies
Dependencies based on Python import relationships.

**Detection Algorithm**:
1. Parse Python files for import statements
2. Map imports to module creation tasks
3. Create dependencies: module users depend on module creators

**Example Patterns**:
```python
# Task A creates module 'auth.py'
# Task B imports auth -> Task B depends on Task A

# Common import patterns:
from_imports = ["from auth import login", "from utils import helper"]
direct_imports = ["import auth", "import utils.config"]
relative_imports = ["from .models import User", "from ..utils import log"]
```

**Confidence Scoring**:
- Direct module imports: 90%
- Package imports: 85%
- Relative imports: 95%
- Wildcard imports: 60%

### 4. Resource Dependencies
Dependencies on shared resources (databases, APIs, hardware).

**Resource Categories**:

#### Database Resources
```yaml
resource_type: "database"
indicators: ["db", "database", "sql", "postgresql", "mysql"]
conflict_types:
  - "schema_migration": exclusive access required
  - "data_seeding": sequential execution needed
  - "backup_restore": blocks all other operations
```

#### API Dependencies
```yaml
resource_type: "api_endpoint"
indicators: ["api/", "endpoint", "rest", "graphql"]
conflict_types:
  - "rate_limiting": shared rate limit pool
  - "authentication": shared auth tokens
  - "data_consistency": sequential writes needed
```

#### Hardware Resources
```yaml
resource_type: "hardware"
indicators: ["gpu", "memory_intensive", "cpu_bound"]
conflict_types:
  - "memory_limit": combined memory usage limits
  - "cpu_cores": optimal core allocation
  - "gpu_compute": exclusive GPU access
```

### 5. Semantic Dependencies
Dependencies inferred from task descriptions and context.

**Detection Methods**:

#### Keyword Pattern Matching
```python
dependency_patterns = {
    "setup_before_implementation": {
        "prerequisite_keywords": ["setup", "configure", "initialize"],
        "dependent_keywords": ["implement", "build", "create"],
        "confidence": 0.8
    },
    "implementation_before_testing": {
        "prerequisite_keywords": ["implement", "code", "develop"],
        "dependent_keywords": ["test", "verify", "validate"],
        "confidence": 0.85
    },
    "testing_before_deployment": {
        "prerequisite_keywords": ["test", "verify", "validate"],
        "dependent_keywords": ["deploy", "release", "publish"],
        "confidence": 0.9
    }
}
```

#### Temporal Sequence Analysis
- Analyze common task ordering patterns from historical data
- Identify tasks that typically follow others
- Learn from successful execution sequences

**Example Learned Sequences**:
1. Design → Implementation → Testing → Documentation
2. Setup → Configuration → Deployment → Validation
3. Analysis → Planning → Execution → Review

### 6. Data Flow Dependencies
Dependencies based on data production and consumption.

**Data Flow Patterns**:
```python
data_flow_dependencies = {
    "producer_consumer": {
        "producer": "generates user_data.json",
        "consumer": "processes user_data.json",
        "dependency_type": "sequential"
    },
    "aggregation": {
        "producers": ["task_a.csv", "task_b.csv", "task_c.csv"],
        "consumer": "merge_all_data.py",
        "dependency_type": "fan_in"
    },
    "broadcast": {
        "producer": "shared_config.json",
        "consumers": ["service_a", "service_b", "service_c"],
        "dependency_type": "fan_out"
    }
}
```

## Dependency Analysis Algorithms

### 1. Static Dependency Analysis

**File Dependency Analysis**:
```python
def analyze_file_dependencies(tasks):
    file_writers = defaultdict(list)  # file -> tasks that write
    file_readers = defaultdict(list)  # file -> tasks that read

    dependencies = []

    for task in tasks:
        files_written = extract_output_files(task)
        files_read = extract_input_files(task)

        # Create read-after-write dependencies
        for file in files_read:
            for writer_task in file_writers[file]:
                dependencies.append(TaskDependency(
                    dependent_id=task.id,
                    prerequisite_id=writer_task.id,
                    dependency_type="file_read_after_write",
                    confidence=0.9
                ))

        # Create write-after-write conflicts (serialize)
        for file in files_written:
            for writer_task in file_writers[file]:
                dependencies.append(TaskDependency(
                    dependent_id=task.id,
                    prerequisite_id=writer_task.id,
                    dependency_type="file_write_conflict",
                    confidence=0.95
                ))

        # Update tracking
        for file in files_written:
            file_writers[file].append(task)
        for file in files_read:
            file_readers[file].append(task)

    return dependencies
```

**Import Dependency Analysis**:
```python
def analyze_import_dependencies(tasks):
    module_creators = {}  # module_name -> task_id
    dependencies = []

    for task in tasks:
        # Find modules created by this task
        created_modules = extract_created_modules(task)
        for module in created_modules:
            module_creators[module] = task.id

        # Find modules imported by this task
        imported_modules = extract_imported_modules(task)
        for module in imported_modules:
            if module in module_creators:
                dependencies.append(TaskDependency(
                    dependent_id=task.id,
                    prerequisite_id=module_creators[module],
                    dependency_type="import",
                    confidence=0.9
                ))

    return dependencies
```

### 2. Dynamic Dependency Discovery

**Learning from Execution Patterns**:
```python
def learn_dependencies_from_execution(execution_history):
    # Analyze successful executions to find common patterns
    dependency_patterns = defaultdict(int)

    for execution in execution_history:
        if execution.success_rate > 0.8:  # Only learn from successful runs
            # Extract task ordering patterns
            for i, task_a in enumerate(execution.tasks):
                for j, task_b in enumerate(execution.tasks[i+1:], i+1):
                    # If task_a consistently runs before task_b
                    pattern_key = (
                        classify_task_type(task_a),
                        classify_task_type(task_b)
                    )
                    dependency_patterns[pattern_key] += 1

    # Convert patterns to dependency rules
    learned_dependencies = []
    for (type_a, type_b), frequency in dependency_patterns.items():
        if frequency >= 5:  # Seen at least 5 times
            confidence = min(0.8, frequency / 10.0)
            learned_dependencies.append({
                "prerequisite_type": type_a,
                "dependent_type": type_b,
                "confidence": confidence,
                "frequency": frequency
            })

    return learned_dependencies
```

### 3. Semantic Dependency Analysis

**Natural Language Processing for Dependencies**:
```python
def analyze_semantic_dependencies(tasks):
    dependencies = []

    for i, task_a in enumerate(tasks):
        for j, task_b in enumerate(tasks):
            if i != j:
                # Check if task descriptions suggest a dependency
                dependency_score = calculate_semantic_dependency(
                    task_a.description,
                    task_b.description
                )

                if dependency_score > 0.6:
                    dependencies.append(TaskDependency(
                        dependent_id=task_b.id,
                        prerequisite_id=task_a.id,
                        dependency_type="semantic",
                        confidence=dependency_score,
                        reason=f"Semantic analysis: {dependency_score:.2f}"
                    ))

    return dependencies

def calculate_semantic_dependency(desc_a, desc_b):
    # Keyword-based semantic analysis

    # Strong dependency indicators
    strong_patterns = [
        (["setup", "configure", "initialize"], ["implement", "build"]),
        (["implement", "create", "develop"], ["test", "verify"]),
        (["test", "verify"], ["deploy", "release"]),
        (["design", "plan"], ["implement", "build"]),
    ]

    desc_a_lower = desc_a.lower()
    desc_b_lower = desc_b.lower()

    for prereq_words, dependent_words in strong_patterns:
        if (any(word in desc_a_lower for word in prereq_words) and
            any(word in desc_b_lower for word in dependent_words)):
            return 0.8

    # Moderate dependency indicators
    moderate_patterns = [
        (["analyze", "research"], ["implement", "design"]),
        (["create", "generate"], ["process", "use"]),
        (["compile", "build"], ["test", "run"]),
    ]

    for prereq_words, dependent_words in moderate_patterns:
        if (any(word in desc_a_lower for word in prereq_words) and
            any(word in desc_b_lower for word in dependent_words)):
            return 0.6

    return 0.0
```

## Dependency Optimization Strategies

### 1. Critical Path Analysis

**Critical Path Identification**:
```python
def find_critical_path(tasks, dependencies):
    # Build dependency graph
    graph = build_dependency_graph(tasks, dependencies)

    # Calculate longest path (critical path)
    longest_paths = {}

    def calculate_longest_path(task_id):
        if task_id in longest_paths:
            return longest_paths[task_id]

        task = find_task_by_id(tasks, task_id)
        task_duration = task.predicted_duration

        # Find maximum path through dependencies
        max_dependency_path = 0
        for dependency in dependencies:
            if dependency.dependent_id == task_id:
                prereq_path = calculate_longest_path(dependency.prerequisite_id)
                max_dependency_path = max(max_dependency_path, prereq_path)

        longest_path = task_duration + max_dependency_path
        longest_paths[task_id] = longest_path
        return longest_path

    # Calculate for all tasks
    for task in tasks:
        calculate_longest_path(task.id)

    # Find critical path
    critical_tasks = []
    max_path_length = max(longest_paths.values())

    # Trace back critical path
    for task_id, path_length in longest_paths.items():
        if path_length == max_path_length:
            critical_tasks.append(task_id)
            # TODO: Add full path tracing

    return critical_tasks, max_path_length
```

### 2. Dependency Reduction Techniques

**Dependency Breaking Strategies**:
```python
dependency_reduction_strategies = {
    "file_isolation": {
        "description": "Use separate files/directories to avoid conflicts",
        "applicable_to": ["file_write_conflict"],
        "effectiveness": 0.9
    },
    "interface_splitting": {
        "description": "Split interfaces to reduce coupling",
        "applicable_to": ["import", "semantic"],
        "effectiveness": 0.7
    },
    "async_processing": {
        "description": "Use async patterns to reduce blocking",
        "applicable_to": ["resource", "api_endpoint"],
        "effectiveness": 0.8
    },
    "caching_strategy": {
        "description": "Cache results to break data dependencies",
        "applicable_to": ["data_flow", "file_read_after_write"],
        "effectiveness": 0.6
    }
}
```

### 3. Parallel Execution Optimization

**Batch Optimization Algorithm**:
```python
def optimize_parallel_batches(tasks, dependencies, max_parallel=8):
    # Topological sort with level extraction
    batches = []
    remaining_tasks = set(task.id for task in tasks)
    task_map = {task.id: task for task in tasks}

    # Build in-degree count
    in_degree = {task.id: 0 for task in tasks}
    for dep in dependencies:
        if dep.confidence > 0.5:  # Only consider high-confidence deps
            in_degree[dep.dependent_id] += 1

    while remaining_tasks:
        # Find tasks with no dependencies
        ready_tasks = [
            task_id for task_id in remaining_tasks
            if in_degree[task_id] == 0
        ]

        if not ready_tasks:
            # Handle circular dependencies
            # Choose task with lowest confidence dependencies
            min_confidence_task = min(
                remaining_tasks,
                key=lambda tid: min(
                    (dep.confidence for dep in dependencies
                     if dep.dependent_id == tid),
                    default=1.0
                )
            )
            ready_tasks = [min_confidence_task]

        # Optimize batch composition
        current_batch = optimize_batch_composition(
            ready_tasks, task_map, max_parallel
        )

        batches.append(current_batch)

        # Update for next iteration
        for task_id in current_batch:
            remaining_tasks.remove(task_id)
            # Reduce in-degree for dependent tasks
            for dep in dependencies:
                if dep.prerequisite_id == task_id:
                    in_degree[dep.dependent_id] -= 1

    return batches

def optimize_batch_composition(ready_tasks, task_map, max_parallel):
    """Optimize which tasks to include in current batch."""
    if len(ready_tasks) <= max_parallel:
        return ready_tasks

    # Score tasks by priority and resource efficiency
    task_scores = []
    for task_id in ready_tasks:
        task = task_map[task_id]
        score = (
            task.priority * 0.4 +
            (1.0 / max(task.predicted_duration, 1)) * 0.3 +  # Favor shorter tasks
            task.predicted_success_rate * 0.3
        )
        task_scores.append((task_id, score))

    # Sort by score and take top tasks
    task_scores.sort(key=lambda x: x[1], reverse=True)
    return [task_id for task_id, _ in task_scores[:max_parallel]]
```

## Learning and Adaptation

### 1. Dependency Pattern Learning

**Pattern Discovery from Execution History**:
- Track which dependencies actually mattered in executions
- Identify false positive dependencies (detected but didn't impact execution)
- Learn new dependency patterns from failed parallelizations

### 2. Confidence Score Updates

**Bayesian Update for Dependency Confidence**:
```python
def update_dependency_confidence(dependency, execution_outcome):
    # Bayesian update based on execution results
    prior_confidence = dependency.confidence

    if execution_outcome.parallel_success:
        # Dependency was correctly identified or wasn't needed
        if dependency.dependency_type in execution_outcome.critical_dependencies:
            # Dependency was critical - increase confidence
            new_confidence = prior_confidence * 1.1
        else:
            # Dependency wasn't critical - slight decrease
            new_confidence = prior_confidence * 0.95
    else:
        # Execution failed - analyze if dependency was related
        if dependency.dependency_type in execution_outcome.failure_causes:
            # Dependency violation caused failure - increase confidence
            new_confidence = prior_confidence * 1.2
        else:
            # Unrelated failure - maintain confidence
            new_confidence = prior_confidence

    # Clamp to valid range
    dependency.confidence = max(0.1, min(1.0, new_confidence))
```

### 3. Adaptive Thresholds

**Dynamic Confidence Thresholds**:
- Start with conservative thresholds (0.5)
- Increase threshold if too many false positives detected
- Decrease threshold if missing important dependencies

## Common Dependency Anti-Patterns

### 1. Over-Sequencing
**Problem**: Creating unnecessary sequential dependencies
**Detection**: Tasks that could run in parallel are forced sequential
**Solution**: Use confidence thresholds and pattern learning

### 2. Circular Dependencies
**Problem**: Tasks that depend on each other cyclically
**Detection**: Cycle detection in dependency graph
**Solution**: Break cycles by splitting tasks or removing low-confidence dependencies

### 3. Resource Bottlenecks
**Problem**: All tasks depend on single resource
**Detection**: Single resource with many dependent tasks
**Solution**: Resource pooling, async patterns, or task splitting

### 4. False File Dependencies
**Problem**: Tasks flagged as conflicting but use different parts of same file
**Detection**: High file dependency confidence but successful parallel execution
**Solution**: Finer-grained file analysis, line-level dependency tracking

## Best Practices

### 1. Dependency Detection
- Combine multiple detection methods for higher accuracy
- Use confidence scores to make trade-offs
- Continuously learn from execution outcomes
- Validate dependencies against actual execution results

### 2. Performance Optimization
- Focus on critical path optimization
- Balance parallelism with resource constraints
- Consider both task duration and success probability
- Monitor and adapt to changing patterns

### 3. Error Handling
- Gracefully handle circular dependencies
- Provide fallback strategies when dependencies are unclear
- Log dependency decisions for later analysis
- Enable manual override for special cases

This knowledge base is continuously updated based on dependency analysis results and execution feedback.
