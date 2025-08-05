# Fix Core Module Type Errors (Priority P1)

## Context
Fix type errors in core modules (.claude/shared/, core agent files) after import errors have been resolved. These are high-priority fixes as they affect the fundamental functionality of the Gadugi system.

## Requirements

### 1. Core Module Type Fixes
Target these critical modules:
- `.claude/shared/` modules (interfaces, state_management, error_handling, etc.)
- Main agent implementations (orchestrator, workflow-master, etc.)
- Core utility modules and base classes
- GitHub integration and state management components

### 2. Type Annotation Strategy
Systematically add type annotations:
- Function parameters and return types
- Class attributes and methods
- Generic type parameters where appropriate
- Protocol implementations and abstract methods

### 3. Type Safety Improvements
Enhance type safety:
- Replace `Any` types with specific types where possible
- Add proper generic type constraints
- Implement missing abstract methods
- Fix type compatibility issues

## Implementation Strategy

### Phase 1: Shared Module Type Fixes
Focus on `.claude/shared/` modules as they're used throughout the system:

1. **interfaces.py**
   - Add missing type annotations for protocols
   - Fix generic type parameter usage
   - Ensure abstract method implementations

2. **state_management.py**
   - Add type annotations for state handling methods
   - Fix JSON serialization type issues
   - Properly type file operations and locking

3. **error_handling.py**
   - Type exception handling properly
   - Add type annotations for retry mechanisms
   - Fix circuit breaker typing

4. **task_tracking.py**
   - Type TodoWrite integration properly
   - Add type annotations for task metadata
   - Fix workflow phase typing

5. **github_operations.py**
   - Type GitHub API interactions
   - Add proper response type annotations
   - Fix batch operation typing

### Phase 2: Agent Implementation Type Fixes
Fix core agent files:

1. **OrchestratorAgent components**
   - Type parallel execution framework
   - Fix task coordination typing
   - Add proper result aggregation types

2. **WorkflowMaster components**
   - Type workflow orchestration
   - Fix state management integration
   - Add proper phase transition typing

3. **Base classes and utilities**
   - Fix inheritance type issues
   - Add proper abstract method implementations
   - Type utility functions properly

### Phase 3: Advanced Type Features
Implement advanced typing features:

1. **Generic Types**
   - Add proper type parameters to generic classes
   - Fix type variable constraints
   - Implement proper covariance/contravariance

2. **Protocol Implementation**
   - Implement missing protocol methods
   - Add runtime checkable protocols where appropriate
   - Fix structural typing issues

3. **Type Guards and Narrowing**
   - Add type guards for runtime type checking
   - Implement proper type narrowing
   - Use TypedDict for structured data

## Automated Tools

### type_annotator.py
```python
# Automated type annotation addition
def add_basic_type_annotations(file_path):
    """Add basic type annotations for common patterns"""

def infer_return_types(file_path):
    """Infer and add return type annotations"""

def fix_generic_usage(file_path):
    """Fix generic type parameter usage"""
```

### type_validator.py
```python
# Type validation and checking
def validate_protocol_implementation(file_path):
    """Check protocol implementation completeness"""

def check_type_compatibility(file_path):
    """Validate type compatibility across modules"""

def verify_abstract_methods(file_path):
    """Ensure abstract methods are implemented"""
```

## Specific Fix Patterns

### Common Type Annotation Patterns
```python
# Function parameters and return types
def process_data(data: List[Dict[str, Any]]) -> OperationResult[ProcessedData]:
    pass

# Class attributes
class TaskManager:
    tasks: Dict[str, Task]
    metrics: TaskMetrics

# Generic classes
class OperationResult(Generic[T]):
    data: T
    success: bool
```

### Protocol Implementation
```python
# Runtime checkable protocols
@runtime_checkable
class Serializable(Protocol):
    def serialize(self) -> Dict[str, Any]: ...
    def deserialize(self, data: Dict[str, Any]) -> None: ...
```

### Type Guards
```python
def is_task_completed(task: Task) -> TypeGuard[CompletedTask]:
    return task.status == TaskStatus.COMPLETED
```

## Validation Process

### Pre-Fix Analysis
1. Identify all type errors in core modules
2. Categorize by complexity and fix type
3. Document current type coverage

### Fix Implementation
1. Apply fixes in dependency order
2. Run pyright after each module fix
3. Ensure tests pass after each change

### Post-Fix Validation
1. Verify pyright error reduction
2. Run comprehensive test suite
3. Check type coverage improvements
4. Validate runtime behavior unchanged

## Success Criteria
- Reduce core module type errors by 90%+
- All shared modules have comprehensive type annotations
- Core agents properly typed with no critical type errors
- 100% test pass rate maintained throughout
- Type coverage significantly improved for core functionality

## Deliverables
1. **Type-Fixed Core Modules**
   - All `.claude/shared/` modules with comprehensive typing
   - Core agent files with proper type annotations
   - Base classes with complete type safety

2. **Type Annotation Standards**
   - Project-specific typing conventions
   - Guidelines for future development
   - Common patterns documentation

3. **Automated Type Tools**
   - Scripts for common type annotation tasks
   - Validation tools for type checking
   - Type coverage measurement tools

4. **Type Fix Documentation**
   - Record of all type changes made
   - Patterns and conventions established
   - Troubleshooting guide for complex type issues
