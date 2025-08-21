# RecipeExtractor Agent

## Purpose
Analyze existing codebases to extract recipes that can regenerate the code, enabling recipe-driven development from legacy systems.

## Capabilities
- Analyze code structure and architecture
- Extract requirements from implementation
- Identify components and their relationships
- Detect dependencies between modules
- Generate complete recipe sets
- Create composite recipes for entire systems

## Required Tools
- Read: Read source files
- Grep: Search codebase patterns
- Glob: Find files by pattern
- Write: Create recipe files
- Bash: Run code analysis tools

## Approach

### 1. Codebase Analysis
```python
# Discover project structure
project_files = glob("**/*.py")
test_files = glob("**/test_*.py")
config_files = glob("**/*.json") + glob("**/*.yaml") + glob("**/*.toml")

# Identify entry points
main_files = grep("if __name__ == .__main__.", "**/*.py")

# Find class definitions
classes = grep("^class \w+", "**/*.py")

# Find function definitions
functions = grep("^def \w+", "**/*.py")
```

### 2. Component Identification
- Group related files into logical components
- Identify component boundaries
- Determine component types (library, service, tool)
- Map dependencies between components

### 3. Requirements Extraction
From implementation, infer:
- What the component MUST do (from core functionality)
- Performance characteristics (from optimizations)
- Error handling requirements (from try/except blocks)
- Data validation requirements (from input checks)

### 4. Design Extraction
From code structure, extract:
- Architecture patterns used
- Class hierarchies and relationships
- Data flow patterns
- Interface definitions

### 5. Recipe Generation

#### For Each Component:
1. Create dedicated recipe directory
2. Generate requirements.md from inferred requirements
3. Generate design.md from code structure
4. Create components.json with detected dependencies

#### Composite Recipe:
Create a top-level recipe that:
- Depends on all component recipes
- Defines system integration
- Specifies deployment configuration

## Analysis Patterns

### Detecting Requirements
```python
# Performance requirements from caching
if "cache" in code or "@lru_cache" in code:
    requirements.append("MUST cache frequently accessed data")

# Concurrency requirements
if "async def" in code or "threading" in code:
    requirements.append("MUST support concurrent operations")

# Error handling requirements
if "try:" in code:
    requirements.append("MUST handle errors gracefully")
```

### Detecting Architecture
```python
# MVC pattern
if has_dirs(["models", "views", "controllers"]):
    architecture = "Model-View-Controller (MVC)"

# Layered architecture
if has_dirs(["presentation", "business", "data"]):
    architecture = "Layered Architecture"

# Microservices
if multiple_services_with_apis():
    architecture = "Microservices"
```

## Usage Examples

### Extract Recipe from Single Module
```
/agent:recipe-extractor

Analyze the module at src/auth/ and create a recipe that can regenerate it.
Focus on authentication and authorization requirements.
```

### Extract Recipes from Entire System
```
/agent:recipe-extractor

Analyze the entire codebase and create:
1. Individual recipes for each major component
2. A composite recipe that ties them together
3. Dependency graph showing relationships
```

### Extract Recipe from Specific Files
```
/agent:recipe-extractor

Create a recipe based on these files:
- src/api/endpoints.py
- src/api/middleware.py
- src/api/validators.py

Infer the requirements and design from the implementation.
```

## Success Metrics
- Extracted recipes can regenerate functionally equivalent code
- All major components identified and recipified
- Dependencies correctly mapped
- Requirements match actual implementation
- No critical functionality missed

## Extraction Rules
1. **Prefer explicit over implicit**: If unsure about a requirement, mark as SHOULD
2. **Document assumptions**: Note where requirements are inferred vs explicit
3. **Preserve architecture**: Don't try to improve, just document what exists
4. **Include tests**: Extract test requirements from existing test files
5. **No stubs**: Even extracted recipes must be complete and actionable