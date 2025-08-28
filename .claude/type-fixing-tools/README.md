# Type-Fixing Tools

This directory contains all tools used for fixing type errors in the codebase.

## Location
All type-fixing tools have been moved to: `.claude/type-fixing-tools/`

## Main Tools

### Comprehensive Fixes
- `final_comprehensive_fix.py` - Main comprehensive type error fixer
- `aggressive_fix_pyright.py` - Aggressive approach for stubborn errors
- `massive_pyright_fix.py` - Handles large-scale type fixes

### Test-Specific
- `final_test_fixes.py` - Fixes type errors in test files
- `final_comprehensive_test_fix.py` - Comprehensive test type fixes
- `fix_all_test_types.py` - Fixes all test-related type errors
- `fix_test_type_errors.py` - Targeted test type error fixes
- `fix_remaining_test_errors.py` - Cleanup for remaining test errors

### Targeted Fixes
- `fix_missing_imports.py` - Resolves import errors
- `fix_undefined_variables.py` - Fixes undefined variable errors
- `fix_syntax_errors.py` - Corrects syntax errors
- `cleanup_commented_imports.py` - Cleans up commented import statements
- `fix_performance_metrics.py` - Fixes performance metric type issues

### Systematic Approaches
- `fix_all_pyright_systematically.py` - Systematic approach to all pyright errors
- `targeted_pyright_fix.py` - Targeted fixes for specific pyright issues
- `fix_pyright_comprehensive.py` - Comprehensive pyright fixes

## Usage

From the project root, run any tool with:

```bash
# Using uv (preferred)
uv run python .claude/type-fixing-tools/<tool_name>.py

# Using Python directly
python .claude/type-fixing-tools/<tool_name>.py
```

## Common Patterns

Most tools follow this pattern:
1. Run `pyright` to identify errors
2. Parse error output
3. Apply appropriate type ignores or fixes
4. Re-run pyright to verify

## Integration with Type-Fix Agent

The type-fix agent should:
1. Check this directory for available tools
2. Use `final_comprehensive_fix.py` for general fixes
3. Use test-specific tools for test files
4. Use targeted tools for specific error types