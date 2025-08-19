# Pyright Error Fix Strategy - Achieve Zero Errors

## Current Status
- **Total Errors**: 1213
- **Total Warnings**: 362
- **Files Checked**: 397

## Error Categories & Fix Strategy

### 1. Missing Import Errors (Top Priority - ~400+ errors)

#### Mock/Testing Imports (282 errors)
- **188 "patch" is not defined**
- **94 "Mock" is not defined**
- **8 "AsyncMock" is not defined**
- **4 "MagicMock" is not defined**

**Fix Strategy**:
```python
# Add to files using these:
from unittest.mock import Mock, patch, AsyncMock, MagicMock
```

#### Standard Library Imports (51+ errors)
- **51 "datetime" is not defined**
- **8 "shutil" is not defined**
- **4 "os" is not defined**

**Fix Strategy**:
```python
# Add imports as needed:
import datetime
import shutil
import os
import sys
```

#### Typing Imports (40+ errors)
- **20 "Set" is not accessed** (unused)
- **12 "Optional" is not defined**
- **12 "Dict" is not defined**
- **9 "List" is not accessed** (unused)

**Fix Strategy**:
```python
# Add proper typing imports:
from typing import Dict, List, Optional, Set, Any, Tuple
# Remove unused imports
```

### 2. Undefined Classes/Functions (~200+ errors)

#### Event System Definitions (39+ errors)
- **39 "create_github_event" is not defined**
- **14 "Event" is not defined**
- **8 "create_local_event" is not defined**

**Fix Strategy**: Create proper stubs or fix import paths

#### Task Management Classes (29+ errors)
- **29 "SubTask" is not defined**
- **7 "PatternDatabase" is not defined**
- **7 "DecompositionResult" is not defined**
- **4 "TaskDecomposer" is not defined**

**Fix Strategy**: Implement missing classes or fix import paths

#### Container Runtime Classes (26+ errors)
- **16 "ContainerConfig" is not defined**
- **10 "ContainerManager" is not defined**

**Fix Strategy**: Fix imports from container_runtime module

### 3. Syntax Errors (~60+ errors)

#### Indentation Issues (34 errors)
- **16 Statements must be separated by newlines or semicolons**
- **10 Unindent amount does not match previous indent**
- **8 Unexpected indentation**

**Fix Strategy**: Manual syntax fixes

#### Missing Code Blocks (18+ errors)
- **16 Expected one or more symbol names after "import"**
- **2 Expected indented block**

**Fix Strategy**: Complete incomplete code blocks

### 4. Optional Type Handling (~50+ errors)

#### None Object Access (43+ errors)
- **28 "status" is not a known attribute of "None"**
- **15 Object of type "None" is not subscriptable**

**Fix Strategy**:
```python
# Before:
result.status  # where result might be None

# After:
if result is not None:
    result.status
# Or use Optional type hints properly
```

### 5. Function Call Issues (~30+ errors)

#### Parameter Mismatches
- **8 No parameter named "name"**
- **8 No parameter named "invocation"**
- **8 No parameter named "filter"**

**Fix Strategy**: Fix function signatures and calls

## Implementation Order

### Phase 1: Quick Wins (Target: -500 errors)
1. **Add missing imports** for Mock, patch, datetime, typing
2. **Remove unused imports** (Set, List when unused)
3. **Fix simple syntax errors** (indentation, semicolons)

### Phase 2: Module Resolution (Target: -300 errors)
1. **Fix import paths** for shared modules
2. **Create missing stub files** for undefined classes
3. **Resolve relative import issues**

### Phase 3: Type Safety (Target: -200 errors)
1. **Add Optional type handling**
2. **Fix function signatures**
3. **Add proper type annotations**

### Phase 4: Missing Implementations (Target: -150 errors)
1. **Implement missing classes** (SubTask, Event, etc.)
2. **Create proper interfaces**
3. **Fix container runtime imports**

### Phase 5: Final Cleanup (Target: -63 errors)
1. **Fix remaining syntax errors**
2. **Clean up unused variables**
3. **Validate all fixes**

## Validation Strategy

After each phase:
```bash
cd /Users/ryan/src/gadugi2/gadugi/.worktrees/task-zero-pyright-errors
uv run pyright --stats
```

Target: **0 errors, 0 warnings**

## Files Requiring Major Fixes

Based on error concentration:
1. `.claude/agents/shared_test_instructions.py` - Multiple syntax errors
2. Test files with missing Mock imports
3. Container runtime modules
4. Event system modules
5. Task decomposer modules

## Success Criteria
- [ ] Zero pyright errors (`uv run pyright` shows 0 errors)
- [ ] Zero pyright warnings
- [ ] All tests still pass (`uv run pytest`)
- [ ] No functional regressions
- [ ] Proper type safety maintained
