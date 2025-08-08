# WorkflowManager Task Execution

## Task Information
- **Task ID**: implement-task-decomposer-agent
- **Task Name**: implement-task-decomposer-agent
- **Original Prompt**: /Users/ryan/src/gadugi2/gadugi/.worktrees/task-implement-task-decomposer-agent/prompts/implement-task-decomposer-agent-workflow.md
- **Phase Focus**: Full Implementation

## Implementation Requirements

### Location
- Agent directory: `.claude/agents/task-decomposer/`
- Recipe directory: `.claude/recipes/task-decomposer/`

### Core Functionality
1. **Task Analysis**
   - Break complex tasks into atomic subtasks
   - Identify task dependencies and ordering requirements
   - Estimate complexity and resource requirements
   - Detect parallelization opportunities

2. **Pattern Learning**
   - Learn from decomposition patterns over time
   - Store successful patterns in Neo4j graph database
   - Retrieve similar patterns for new tasks
   - Improve decomposition quality through experience

3. **Integration Requirements**
   - Must inherit from BaseAgent framework in `.claude/framework/`
   - Integrate with Event Router for communication
   - Use Memory System for pattern storage
   - Work with Orchestrator Agent for parallel execution

### Implementation Details

#### Agent Structure
```python
# .claude/agents/task-decomposer/task_decomposer.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...framework.base_agent import BaseAgent
from ...framework.events import Event, EventType
from ...framework.memory import MemorySystem

@dataclass
class SubTask:
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None
    complexity: str = "medium"
    can_parallelize: bool = True
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecompositionResult:
    original_task: str
    subtasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]
    parallelization_score: float
    estimated_total_time: int
    decomposition_pattern: Optional[str] = None

class TaskDecomposer(BaseAgent):
    """Intelligently decomposes complex tasks into manageable subtasks"""

    def __init__(self):
        super().__init__("TaskDecomposer")
        self.patterns_db = self._init_patterns_db()

    async def decompose_task(self, task_description: str) -> DecompositionResult:
        """Main decomposition logic"""
        pass

    async def analyze_dependencies(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """Identify dependencies between subtasks"""
        pass

    async def estimate_parallelization(self, subtasks: List[SubTask], dependencies: Dict) -> float:
        """Calculate parallelization potential (0-1 scale)"""
        pass

    async def learn_pattern(self, result: DecompositionResult, success_metrics: Dict):
        """Store successful decomposition patterns"""
        pass

    async def find_similar_patterns(self, task_description: str) -> List[str]:
        """Retrieve similar decomposition patterns from history"""
        pass
```

#### Recipe Structure
```yaml
# .claude/recipes/task-decomposer/recipe.yaml
name: task-decomposer
version: 1.0.0
description: Intelligent task decomposition and parallelization analysis

capabilities:
  - task_analysis
  - dependency_detection
  - parallelization_estimation
  - pattern_learning
  - subtask_generation

inputs:
  task_description:
    type: string
    required: true
    description: Complex task to decompose

  context:
    type: object
    required: false
    description: Additional context for decomposition

outputs:
  subtasks:
    type: array
    description: List of atomic subtasks

  dependency_graph:
    type: object
    description: Dependencies between subtasks

  parallelization_score:
    type: number
    description: Score indicating parallelization potential (0-1)

patterns:
  - name: feature_implementation
    triggers: ["implement", "create", "build", "develop"]
    subtasks: ["design", "implement", "test", "document", "review"]

  - name: bug_fix
    triggers: ["fix", "resolve", "debug", "patch"]
    subtasks: ["reproduce", "diagnose", "fix", "test", "verify"]

  - name: refactoring
    triggers: ["refactor", "optimize", "improve", "enhance"]
    subtasks: ["analyze", "plan", "refactor", "test", "validate"]
```

### Quality Requirements
1. **Type Safety**
   - Must pass `uv run pyright` with zero errors
   - Use proper type hints for all functions and variables
   - Handle Optional types correctly

2. **Code Quality**
   - Must be ruff formatted
   - Follow PEP 8 style guidelines
   - Include comprehensive docstrings

3. **Testing**
   - Include unit tests in `tests/test_task_decomposer.py`
   - Test decomposition logic
   - Test pattern learning and retrieval
   - Test Neo4j integration

4. **Neo4j Integration**
   - Store patterns as nodes with relationships
   - Query for similar patterns using graph traversal
   - Update pattern success metrics

### Example Usage
```python
decomposer = TaskDecomposer()

# Complex task
task = "Implement a new authentication system with OAuth2, JWT tokens, and role-based access control"

# Decompose
result = await decomposer.decompose_task(task)

# Result contains:
# - 8-10 subtasks (design auth flow, implement OAuth2, create JWT service, etc.)
# - Dependency graph showing which tasks must complete before others
# - Parallelization score of 0.7 (high parallelization potential)
# - Reference to similar pattern from previous implementations
```

### Testing Requirements
Create comprehensive tests that verify:
- Correct subtask generation for various task types
- Accurate dependency detection
- Parallelization scoring accuracy
- Pattern storage and retrieval
- Integration with BaseAgent framework
- Event handling capabilities

## Technical Specifications

See original prompt for technical details.

## Implementation Plan

Follow the implementation steps from the original prompt.

## Success Criteria

- ✅ Agent inherits from BaseAgent framework
- ✅ Passes pyright with zero errors
- ✅ Comprehensive test coverage
- ✅ Neo4j integration for pattern storage
- ✅ Event Router integration
- ✅ Recipe properly configured
- ✅ Documentation complete
```

---

**Execute the complete WorkflowManager workflow for this task.**

## Execution Instructions

**CRITICAL**: You are executing as WorkflowManager in a parallel execution environment.

1. **Complete All 9 Phases**: Execute the full WorkflowManager workflow
   - Phase 1: Initial Setup (analyze this prompt)
   - Phase 2: Issue Management (link to existing issue if provided)
   - Phase 3: Branch Management (you're already in the correct branch)
   - Phase 4: Research and Planning
   - Phase 5: **IMPLEMENTATION** (CREATE ACTUAL FILES - this is critical)
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request Creation
   - Phase 9: Code Review

2. **File Creation is Mandatory**: You MUST create actual implementation files, not just update Memory.md

3. **Context Preservation**: All implementation context is provided above

4. **Worktree Awareness**: You are executing in an isolated worktree environment

## Target Files
Target files will be determined during implementation phase.

## Dependencies
No specific dependencies identified.

## Original Prompt Content

```markdown
# WorkflowManager Task Execution

## Task Information
- **Task ID**: implement-task-decomposer-agent
- **Task Name**: Implement Task Decomposer Agent (#240)
- **Original Prompt**: /Users/ryan/src/gadugi2/gadugi/prompts/implement-task-decomposer-agent.md
- **Phase Focus**: Full Implementation

## Implementation Requirements

### Location
- Agent directory: `.claude/agents/task-decomposer/`
- Recipe directory: `.claude/recipes/task-decomposer/`

### Core Functionality
1. **Task Analysis**
   - Break complex tasks into atomic subtasks
   - Identify task dependencies and ordering requirements
   - Estimate complexity and resource requirements
   - Detect parallelization opportunities

2. **Pattern Learning**
   - Learn from decomposition patterns over time
   - Store successful patterns in Neo4j graph database
   - Retrieve similar patterns for new tasks
   - Improve decomposition quality through experience

3. **Integration Requirements**
   - Must inherit from BaseAgent framework in `.claude/framework/`
   - Integrate with Event Router for communication
   - Use Memory System for pattern storage
   - Work with Orchestrator Agent for parallel execution

### Implementation Details

#### Agent Structure
```python
# .claude/agents/task-decomposer/task_decomposer.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...framework.base_agent import BaseAgent
from ...framework.events import Event, EventType
from ...framework.memory import MemorySystem

@dataclass
class SubTask:
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None
    complexity: str = "medium"
    can_parallelize: bool = True
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecompositionResult:
    original_task: str
    subtasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]
    parallelization_score: float
    estimated_total_time: int
    decomposition_pattern: Optional[str] = None

class TaskDecomposer(BaseAgent):
    """Intelligently decomposes complex tasks into manageable subtasks"""

    def __init__(self):
        super().__init__("TaskDecomposer")
        self.patterns_db = self._init_patterns_db()

    async def decompose_task(self, task_description: str) -> DecompositionResult:
        """Main decomposition logic"""
        pass

    async def analyze_dependencies(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """Identify dependencies between subtasks"""
        pass

    async def estimate_parallelization(self, subtasks: List[SubTask], dependencies: Dict) -> float:
        """Calculate parallelization potential (0-1 scale)"""
        pass

    async def learn_pattern(self, result: DecompositionResult, success_metrics: Dict):
        """Store successful decomposition patterns"""
        pass

    async def find_similar_patterns(self, task_description: str) -> List[str]:
        """Retrieve similar decomposition patterns from history"""
        pass
```

#### Recipe Structure
```yaml
# .claude/recipes/task-decomposer/recipe.yaml
name: task-decomposer
version: 1.0.0
description: Intelligent task decomposition and parallelization analysis

capabilities:
  - task_analysis
  - dependency_detection
  - parallelization_estimation
  - pattern_learning
  - subtask_generation

inputs:
  task_description:
    type: string
    required: true
    description: Complex task to decompose

  context:
    type: object
    required: false
    description: Additional context for decomposition

outputs:
  subtasks:
    type: array
    description: List of atomic subtasks

  dependency_graph:
    type: object
    description: Dependencies between subtasks

  parallelization_score:
    type: number
    description: Score indicating parallelization potential (0-1)

patterns:
  - name: feature_implementation
    triggers: ["implement", "create", "build", "develop"]
    subtasks: ["design", "implement", "test", "document", "review"]

  - name: bug_fix
    triggers: ["fix", "resolve", "debug", "patch"]
    subtasks: ["reproduce", "diagnose", "fix", "test", "verify"]

  - name: refactoring
    triggers: ["refactor", "optimize", "improve", "enhance"]
    subtasks: ["analyze", "plan", "refactor", "test", "validate"]
```

### Quality Requirements
1. **Type Safety**
   - Must pass `uv run pyright` with zero errors
   - Use proper type hints for all functions and variables
   - Handle Optional types correctly

2. **Code Quality**
   - Must be ruff formatted
   - Follow PEP 8 style guidelines
   - Include comprehensive docstrings

3. **Testing**
   - Include unit tests in `tests/test_task_decomposer.py`
   - Test decomposition logic
   - Test pattern learning and retrieval
   - Test Neo4j integration

4. **Neo4j Integration**
   - Store patterns as nodes with relationships
   - Query for similar patterns using graph traversal
   - Update pattern success metrics

### Example Usage
```python
decomposer = TaskDecomposer()

# Complex task
task = "Implement a new authentication system with OAuth2, JWT tokens, and role-based access control"

# Decompose
result = await decomposer.decompose_task(task)

# Result contains:
# - 8-10 subtasks (design auth flow, implement OAuth2, create JWT service, etc.)
# - Dependency graph showing which tasks must complete before others
# - Parallelization score of 0.7 (high parallelization potential)
# - Reference to similar pattern from previous implementations
```

### Testing Requirements
Create comprehensive tests that verify:
- Correct subtask generation for various task types
- Accurate dependency detection
- Parallelization scoring accuracy
- Pattern storage and retrieval
- Integration with BaseAgent framework
- Event handling capabilities

## Technical Specifications

See original prompt for technical details.

## Implementation Plan

Follow the implementation steps from the original prompt.

## Success Criteria

- ✅ Agent inherits from BaseAgent framework
- ✅ Passes pyright with zero errors
- ✅ Comprehensive test coverage
- ✅ Neo4j integration for pattern storage
- ✅ Event Router integration
- ✅ Recipe properly configured
- ✅ Documentation complete

## Execution Instructions

**CRITICAL**: You are executing as WorkflowManager in a parallel execution environment.

1. **Complete All 9 Phases**: Execute the full WorkflowManager workflow
   - Phase 1: Initial Setup (analyze this prompt)
   - Phase 2: Issue Management (link to existing issue if provided)
   - Phase 3: Branch Management (you're already in the correct branch)
   - Phase 4: Research and Planning
   - Phase 5: **IMPLEMENTATION** (CREATE ACTUAL FILES - this is critical)
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request Creation
   - Phase 9: Code Review

2. **File Creation is Mandatory**: You MUST create actual implementation files, not just update Memory.md

3. **Context Preservation**: All implementation context is provided above

4. **Worktree Awareness**: You are executing in an isolated worktree environment

## Target Files
Expected files to be created/modified:
- `decomposer/task_decomposer.py`
- `tests/test_task_decomposer.py`


## Dependencies
No specific dependencies identified.

## Original Prompt Content

```markdown
# Implement Task Decomposer Agent (#240)

## Overview
Create the Task Decomposer agent that intelligently breaks down complex tasks into subtasks, identifies dependencies, and estimates parallelization potential.

## Requirements

### Location
- Agent directory: `.claude/agents/task-decomposer/`
- Recipe directory: `.claude/recipes/task-decomposer/`

### Core Functionality
1. **Task Analysis**
   - Break complex tasks into atomic subtasks
   - Identify task dependencies and ordering requirements
   - Estimate complexity and resource requirements
   - Detect parallelization opportunities

2. **Pattern Learning**
   - Learn from decomposition patterns over time
   - Store successful patterns in Neo4j graph database
   - Retrieve similar patterns for new tasks
   - Improve decomposition quality through experience

3. **Integration Requirements**
   - Must inherit from BaseAgent framework in `.claude/framework/`
   - Integrate with Event Router for communication
   - Use Memory System for pattern storage
   - Work with Orchestrator Agent for parallel execution

### Implementation Details

#### Agent Structure
```python
# .claude/agents/task-decomposer/task_decomposer.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...framework.base_agent import BaseAgent
from ...framework.events import Event, EventType
from ...framework.memory import MemorySystem

@dataclass
class SubTask:
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None
    complexity: str = "medium"
    can_parallelize: bool = True
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecompositionResult:
    original_task: str
    subtasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]
    parallelization_score: float
    estimated_total_time: int
    decomposition_pattern: Optional[str] = None

class TaskDecomposer(BaseAgent):
    """Intelligently decomposes complex tasks into manageable subtasks"""

    def __init__(self):
        super().__init__("TaskDecomposer")
        self.patterns_db = self._init_patterns_db()

    async def decompose_task(self, task_description: str) -> DecompositionResult:
        """Main decomposition logic"""
        pass

    async def analyze_dependencies(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """Identify dependencies between subtasks"""
        pass

    async def estimate_parallelization(self, subtasks: List[SubTask], dependencies: Dict) -> float:
        """Calculate parallelization potential (0-1 scale)"""
        pass

    async def learn_pattern(self, result: DecompositionResult, success_metrics: Dict):
        """Store successful decomposition patterns"""
        pass

    async def find_similar_patterns(self, task_description: str) -> List[str]:
        """Retrieve similar decomposition patterns from history"""
        pass
```

#### Recipe Structure
```yaml
# .claude/recipes/task-decomposer/recipe.yaml
name: task-decomposer
version: 1.0.0
description: Intelligent task decomposition and parallelization analysis

capabilities:
  - task_analysis
  - dependency_detection
  - parallelization_estimation
  - pattern_learning
  - subtask_generation

inputs:
  task_description:
    type: string
    required: true
    description: Complex task to decompose

  context:
    type: object
    required: false
    description: Additional context for decomposition

outputs:
  subtasks:
    type: array
    description: List of atomic subtasks

  dependency_graph:
    type: object
    description: Dependencies between subtasks

  parallelization_score:
    type: number
    description: Score indicating parallelization potential (0-1)

patterns:
  - name: feature_implementation
    triggers: ["implement", "create", "build", "develop"]
    subtasks: ["design", "implement", "test", "document", "review"]

  - name: bug_fix
    triggers: ["fix", "resolve", "debug", "patch"]
    subtasks: ["reproduce", "diagnose", "fix", "test", "verify"]

  - name: refactoring
    triggers: ["refactor", "optimize", "improve", "enhance"]
    subtasks: ["analyze", "plan", "refactor", "test", "validate"]
```

### Quality Requirements
1. **Type Safety**
   - Must pass `uv run pyright` with zero errors
   - Use proper type hints for all functions and variables
   - Handle Optional types correctly

2. **Code Quality**
   - Must be ruff formatted
   - Follow PEP 8 style guidelines
   - Include comprehensive docstrings

3. **Testing**
   - Include unit tests in `tests/test_task_decomposer.py`
   - Test decomposition logic
   - Test pattern learning and retrieval
   - Test Neo4j integration

4. **Neo4j Integration**
   - Store patterns as nodes with relationships
   - Query for similar patterns using graph traversal
   - Update pattern success metrics

### Example Usage
```python
decomposer = TaskDecomposer()

# Complex task
task = "Implement a new authentication system with OAuth2, JWT tokens, and role-based access control"

# Decompose
result = await decomposer.decompose_task(task)

# Result contains:
# - 8-10 subtasks (design auth flow, implement OAuth2, create JWT service, etc.)
# - Dependency graph showing which tasks must complete before others
# - Parallelization score of 0.7 (high parallelization potential)
# - Reference to similar pattern from previous implementations
```

### Testing Requirements
Create comprehensive tests that verify:
- Correct subtask generation for various task types
- Accurate dependency detection
- Parallelization scoring accuracy
- Pattern storage and retrieval
- Integration with BaseAgent framework
- Event handling capabilities

## Success Criteria
- ✅ Agent inherits from BaseAgent framework
- ✅ Passes pyright with zero errors
- ✅ Comprehensive test coverage
- ✅ Neo4j integration for pattern storage
- ✅ Event Router integration
- ✅ Recipe properly configured
- ✅ Documentation complete
```

---

**Execute the complete WorkflowManager workflow for this task.**

```

---

**Execute the complete WorkflowManager workflow for this task.**
