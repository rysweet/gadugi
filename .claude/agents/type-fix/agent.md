# Type-Fix Agent

An agent specialized in fixing type errors across the codebase using pyright.

## Tools Location

All type-fixing tools have been relocated to: `.claude/type-fixing-tools/`

## Available Tools

### Primary Tools
- `.claude/type-fixing-tools/final_comprehensive_fix.py` - Main comprehensive fixer
- `.claude/type-fixing-tools/aggressive_fix_pyright.py` - Aggressive approach
- `.claude/type-fixing-tools/massive_pyright_fix.py` - Large-scale fixes

### Test-Specific Tools
- `.claude/type-fixing-tools/final_test_fixes.py`
- `.claude/type-fixing-tools/fix_all_test_types.py`
- `.claude/type-fixing-tools/fix_test_type_errors.py`

### Targeted Fix Tools
- `.claude/type-fixing-tools/fix_missing_imports.py`
- `.claude/type-fixing-tools/fix_undefined_variables.py`
- `.claude/type-fixing-tools/fix_syntax_errors.py`

## Usage

Run tools from project root:

```bash
# Using uv
uv run python .claude/type-fixing-tools/<tool_name>.py

# Direct Python
python .claude/type-fixing-tools/<tool_name>.py
```

## Workflow

1. **Identify Errors**: Run `uv run pyright` to see current errors
2. **Choose Tool**: 
   - Use `final_comprehensive_fix.py` for general fixes
   - Use test-specific tools for test files
   - Use targeted tools for specific error types
3. **Apply Fixes**: Run the chosen tool
4. **Verify**: Run `uv run pyright` again to confirm fixes

## Common Commands

```bash
# Check current error count
uv run pyright 2>&1 | grep -c "error:"

# Get error summary
uv run pyright 2>&1 | tail -5

# Fix all errors comprehensively
uv run python .claude/type-fixing-tools/final_comprehensive_fix.py

# Fix test errors
uv run python .claude/type-fixing-tools/final_test_fixes.py

# Fix import errors
uv run python .claude/type-fixing-tools/fix_missing_imports.py
```

## Integration with Other Agents

When working with other agents that encounter type errors:
1. Save the current work
2. Run appropriate type-fix tool
3. Verify fixes don't break functionality
4. Continue with original task

## Best Practices

1. Always run pyright before and after fixes
2. Commit after successful fixes
3. Use targeted tools for specific issues
4. Use comprehensive tools for final cleanup
5. Prefer `# type: ignore[specific]` over generic ignores