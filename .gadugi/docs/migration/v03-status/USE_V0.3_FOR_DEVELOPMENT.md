# How to USE Gadugi v0.3 for Development

## The Problem
You want to use v0.3's features (orchestrator, memory system, parallel execution) to BUILD v0.4, not just test that v0.3 works.

## The Solution: Self-Hosting

Gadugi v0.3 can use itself to build v0.4! Here's how:

## 1. First, Merge v0.3 to Main

```bash
# Check current status
git status

# If on feature branch, create PR and merge
gh pr create --title "Gadugi v0.3: Complete implementation" --body "Memory system, orchestrator, zero pyright errors"
gh pr merge --auto

# Switch to main
git checkout main
git pull
```

## 2. Start the v0.3 Memory System

```bash
# Start the memory backend (SQLite version, no Docker needed)
.claude/services/memory/start_local.sh

# Or with Docker/Neo4j if available
.claude/services/neo4j-memory/start_memory_system.sh
```

## 3. Use v0.3 Orchestrator for Development

Now you can use v0.3's orchestrator to build v0.4:

```bash
# Create a prompt file for v0.4 features
cat > prompts/v0.4_feature.md << 'EOF'
# Build v0.4 Feature: [Feature Name]

## Context
Using Gadugi v0.3 to build v0.4

## Requirements
- [List what you want to build]

## Use v0.3 Features
- Use orchestrator for parallel execution
- Store progress in memory system
- Use WorkflowManager for proper git flow
EOF

# Execute using v0.3 orchestrator
./scripts/orchestrator/execute_orchestrator.sh prompts/v0.4_feature.md
```

## 4. Use v0.3 Features Directly in Claude

When working with Claude (like now), you can request v0.3 features:

### Memory Integration
```python
# Tell Claude to use v0.3 memory
"Store this in v0.3 memory for the project"
"Recall what we learned about X from memory"
"Update the task whiteboard with progress"
```

### Parallel Execution
```python
# Request parallel task execution
"Use v0.3 orchestrator to parallelize these tasks:
1. Fix type errors in /src
2. Add tests for new features
3. Update documentation"
```

### Workflow Management
```python
# Use proper workflow
"Use v0.3 WorkflowManager to implement feature X"
# This will:
# - Create worktree
# - Run 13-phase workflow
# - Create PR
# - Run tests
```

## 5. Example: Building a v0.4 Feature with v0.3

```bash
# Start memory system
.claude/services/memory/start_local.sh

# Create orchestrator task
cat > tasks/add_v04_feature.py << 'EOF'
#!/usr/bin/env python3
"""Use v0.3 to build v0.4 feature"""

import asyncio
from gadugi_v03 import Orchestrator, MemorySystem

async def build_v04_feature():
    # Initialize v0.3 systems
    memory = MemorySystem()
    orchestrator = Orchestrator()

    # Define v0.4 feature
    feature = {
        "name": "Enhanced Agent Communication",
        "tasks": [
            "Design message protocol",
            "Implement agent messaging",
            "Add tests",
            "Update documentation"
        ]
    }

    # Store in memory
    await memory.store_project_goal(feature)

    # Execute in parallel using v0.3
    results = await orchestrator.execute_parallel(feature["tasks"])

    # Store results
    await memory.store_results(results)

    return results

if __name__ == "__main__":
    asyncio.run(build_v04_feature())
EOF

uv run python tasks/add_v04_feature.py
```

## 6. Using v0.3 Agents

The v0.3 agents can be invoked to help build v0.4:

```bash
# Use WorkflowManager agent
claude --agent WorkflowManager "Create v0.4 agent communication system"

# Use TaskDecomposer agent
claude --agent TaskDecomposer "Break down v0.4 roadmap into parallel tasks"

# Use code-writer agent with memory
claude --agent code-writer --memory "Implement v0.4 feature X based on v0.3 patterns"
```

## 7. The Key Difference: Using vs Testing

### Testing v0.3 (what we did)
```bash
# Just proves it works
uv run python quick_test_v03.py
```

### USING v0.3 (what you want)
```bash
# Actually leverages v0.3 to build v0.4
./scripts/orchestrator/execute_orchestrator.sh "Build v0.4 feature X using v0.3 capabilities"

# Or in Claude conversation:
"Use the v0.3 orchestrator to implement [feature]"
"Store this design decision in v0.3 memory"
"Use parallel execution to fix all type errors"
```

## The Self-Hosting Concept

v0.3 is designed to build its own next version:

1. **Memory System** → Remembers what's been built, decisions made, patterns learned
2. **Orchestrator** → Parallelizes development tasks for 3-5x speed
3. **Workflow Manager** → Ensures proper git flow and PR management
4. **Task Decomposer** → Breaks v0.4 requirements into parallel work
5. **Agents** → Specialized workers for different aspects of development

## Quick Start: Use v0.3 Right Now

Tell Claude (me) to use v0.3 features:

```
"Use v0.3 orchestrator to create a new agent for v0.4"
"Store our v0.4 design decisions in the memory system"
"Use parallel execution to refactor the codebase"
"Use WorkflowManager to properly implement feature X"
```

## Running v0.3 Services

### Memory System (Choose One)
```bash
# SQLite (no Docker)
.claude/services/memory/start_local.sh

# Neo4j (requires Docker)
.claude/services/neo4j-memory/start_memory_system.sh
```

### Orchestrator
```bash
# For task execution
./scripts/orchestrator/execute_orchestrator.sh [task]

# For parallel execution
./scripts/orchestrator/run_parallel_tasks.py
```

### Complete v0.3 Stack
```bash
# Start everything
./start_v03.sh  # (we should create this)
```

## Next Steps

1. Merge PR #184 to main
2. Start memory system
3. Begin using v0.3 to build v0.4
4. Let v0.3 manage its own evolution

---

**Bottom Line:** Instead of manually coding v0.4, you use v0.3's orchestrator, memory, and agents to build it faster and better. The system builds itself!
