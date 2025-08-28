# Complete Recipe Executor Model Implementation

## Objective
Implement a complete Recipe model that satisfies ALL requirements from the recipe-executor-recipe-model recipe, with NO STUBS and COMPLETE functionality.

## Context
The Recipe Executor model in `src/recipe_executor/recipe_model.py` needs significant enhancements to meet all recipe requirements. The detailed requirements are specified in `.recipe_build/prompts/prompt_fix-recipe-executor-model_20250827.md`.

## Required Changes

### 1. Add New Model Classes
- **DesignPattern**: Represents reusable design patterns with templates
- **RecipeComplexity**: Complexity analysis and decomposition recommendations
- **DependencyGraph**: Dependency relationships with circular detection
- **BuildState**: Tracks build state for incremental builds

### 2. Enhance Recipe Class
- Add pattern field for design pattern support
- Add complexity field for complexity analysis
- Add methods for dependency validation and circular detection
- Add methods for pattern merging
- Add checksum calculation for change detection
- Add self-hosting protection

### 3. Create Supporting Modules
- `pattern_loader.py`: Design pattern loading and management
- `dependency_graph.py`: Dependency graph construction and analysis
- `complexity_analyzer.py`: Recipe complexity evaluation
- Enhance tests in `test_recipe_model.py`

## Implementation Requirements

### Core Model Enhancements Needed

1. **Design Pattern Support** (req_33, req_34, req_35, req_39, req_40)
   - Add DesignPattern dataclass for pattern definitions
   - Add pattern field to Recipe class for inherited patterns
   - Add methods to merge pattern requirements with recipe requirements
   - Add methods to apply pattern design decisions

2. **Enhanced Dependency Management** (req_17, req_18, req_19, req_20, req_21, req_23)
   - Add dependency graph representation
   - Add circular dependency detection using DFS
   - Add topological sorting for build order
   - Add validation that dependencies exist
   - Clearly separate recipe dependencies from Python dependencies

3. **Incremental Build Support** (req_28, req_29, req_30, req_32)
   - Add checksum field to Recipe and RecipeMetadata
   - Add change detection methods
   - Add methods to determine affected recipes
   - Add build state tracking

4. **Recipe Complexity Evaluation** (req_43, req_44, req_47, req_48)
   - Add RecipeComplexity dataclass
   - Add complexity scoring methods
   - Add decomposition recommendation logic
   - Add automatic splitting support

5. **Self-Hosting Protection** (req_97, req_98)
   - Add self-overwrite detection
   - Add protection logic for src/recipe_executor path
   - Add clear error messaging

## Quality Requirements
- NO STUBS - all methods must have complete implementations
- Minimum 5-10 lines of real logic per method
- Proper error handling and validation
- Full type hints on all functions
- >80% test coverage
- All 43 functional requirements from the recipe must be satisfied

## Files to Modify/Create
1. `src/recipe_executor/recipe_model.py` - Enhance with all new classes and methods
2. `src/recipe_executor/pattern_loader.py` - NEW: Design pattern loading
3. `src/recipe_executor/dependency_graph.py` - NEW: Dependency analysis  
4. `src/recipe_executor/complexity_analyzer.py` - NEW: Complexity evaluation
5. `tests/recipe_executor/test_recipe_model.py` - Comprehensive tests

## Success Criteria
- All new model classes implemented with full functionality
- Enhanced Recipe class with all required methods
- Supporting modules created with real implementations
- Comprehensive test coverage
- No stub methods or placeholder returns
- Circular dependency detection works correctly
- Design patterns can be loaded and merged
- Complexity evaluation produces accurate scores
- Incremental build detection works properly
- Self-hosting protection prevents overwriting