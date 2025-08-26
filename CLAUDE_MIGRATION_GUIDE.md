# CLAUDE.md Refactoring Migration Guide

## Overview
The original CLAUDE.md (1,103 lines) has been refactored into:
- **CLAUDE_REFACTORED.md** (~100 lines) - Core essentials only
- **6 modular instruction files** - Task-specific details

## Benefits of Refactoring

### 1. Reduced Context Usage
- **Before**: 1,103 lines loaded every time
- **After**: ~100 lines base + ~200 lines when needed
- **Savings**: 80-90% context reduction

### 2. Improved Performance
- Faster initial load
- Selective instruction loading
- Better parallel execution guidance

### 3. Better Maintainability
- Modular updates
- Clear separation of concerns
- Easier to find specific instructions

## File Structure

```
CLAUDE_REFACTORED.md (100 lines)
├── Core essentials every agent needs
├── Parallel execution as default
└── References to load specific modules

.claude/instructions/
├── orchestration.md     - Workflow & orchestrator patterns
├── testing-qa.md        - Testing, quality gates, type fixes
├── git-worktree.md      - Git operations, worktree management
├── uv-environment.md    - UV Python environment setup
├── troubleshooting.md   - Recovery, debugging, fallbacks
└── agent-development.md - Creating and modifying agents
```

## Migration Steps

### 1. Backup Original
```bash
cp CLAUDE.md CLAUDE_LEGACY.md
```

### 2. Replace with Refactored Version
```bash
mv CLAUDE_REFACTORED.md CLAUDE.md
```

### 3. Update Agent References
Agents should now load specific instructions as needed:
```bash
# In agent code, load only what's needed
cat .claude/instructions/testing-qa.md  # When running tests
cat .claude/instructions/orchestration.md  # When orchestrating
```

## Key Changes

### Parallel Execution as Default
The refactored version emphasizes parallel task execution:
- Always analyze for parallelization first
- Use Task tool for multiple Claude instances
- Examples show parallel patterns prominently

### Modular Loading Pattern
```markdown
## When working with tests:
Load: .claude/instructions/testing-qa.md

## When orchestrating:
Load: .claude/instructions/orchestration.md
```

### Quick Decision Tree
Added decision tree for quick navigation:
- Multiple tasks? → Parallel execution
- Tests failing? → Load testing-qa.md
- Orchestrator issues? → Load troubleshooting.md

## Backward Compatibility

### Legacy Support
- Original saved as CLAUDE_LEGACY.md
- All content preserved in modular files
- No functionality lost

### Gradual Migration
1. Start using CLAUDE_REFACTORED.md
2. Load modules as needed
3. Update agents gradually
4. Remove CLAUDE_LEGACY.md when comfortable

## Usage Examples

### Before (Sequential)
```python
# Old approach - everything sequential
fix_file_1()
fix_file_2() 
fix_file_3()
```

### After (Parallel by Default)
```python
# New approach - parallel first
Task("Fix module A", prompt_a)
Task("Fix module B", prompt_b)
Task("Fix module C", prompt_c)
# All execute simultaneously
```

## Validation

### Test the Refactored Version
```bash
# Ensure core functionality works
cat CLAUDE_REFACTORED.md | head -50

# Verify modules exist
ls -la .claude/instructions/

# Test selective loading
cat .claude/instructions/testing-qa.md
```

## Rollback Plan

If issues arise:
```bash
# Restore original
cp CLAUDE_LEGACY.md CLAUDE.md

# Keep modules for gradual adoption
# Can reference both old and new
```

## Next Steps

1. Review CLAUDE_REFACTORED.md
2. Test with a simple task
3. Verify parallel execution works
4. Gradually adopt modular loading
5. Remove legacy file when confident

## Summary

**From**: 1,103 lines monolithic file
**To**: 100 lines core + 6 modular files
**Result**: 80-90% context savings, better performance, clearer organization