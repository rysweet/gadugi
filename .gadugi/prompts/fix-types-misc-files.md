# Fix Type Errors in Miscellaneous Files

## Objective
Fix remaining type errors in various files across the codebase.

## Target Files
- benchmark_performance.py (import errors)
- src/agents/program_manager.py (7 errors)
- tests/test_teamcoach_hooks_comprehensive.py (13 errors)
- tests/agents/test_test_agents_basic.py (9 errors)
- Various other files with 1-5 errors each

## Focus Areas
1. **Import resolution**: Fix import paths for moved modules
2. **Type annotations**: Add missing function and variable annotations
3. **Generic types**: Specify generic type parameters
4. **Protocol compliance**: Ensure classes implement required protocols

## Strategy
1. Fix all import errors by updating to correct paths
2. Add comprehensive type annotations to all functions
3. Specify generic types for collections (List, Dict, etc.)
4. Use Union types where multiple types are accepted
5. Add dataclass annotations where appropriate

## Specific Issues
- benchmark_performance.py: Update imports to use .claude.shared paths
- program_manager.py: Add type hints to agent coordination methods
- Hook tests: Fix mock type annotations and assertions
- Basic agent tests: Add proper fixture typing

## Requirements
- All functionality must be preserved
- Performance benchmarks must still run correctly
- Agent behavior must remain unchanged
- All tests must continue to pass
