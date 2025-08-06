# Import Path Issue: .claude as a Python Package

## Problem

The `.claude` directory is used as a package for agent code, but its leading dot makes it a hidden directory and not a standard Python package name. This causes import issues when running tests or when other projects try to use Gadugi as a dependency, because Python does not recognize `.claude` as a top-level package by default.

## Symptoms
- Import errors like `ModuleNotFoundError: No module named 'claude'` or `No module named 'system_design_reviewer.claude'` when running tests or importing agents.
- Users must manually add `.claude` to `PYTHONPATH` or use custom sys.path hacks.
- Not portable for users who want to use Gadugi as a dependency or submodule.

## Workaround (Current)
- A `conftest.py` in the `tests/` directory prepends `.claude` to `sys.path` for all tests, allowing absolute imports like `from agents.system_design_reviewer.core import ...` to work.
- All test imports should use `from agents.system_design_reviewer...` (not `from .claude...`).

## Long-Term Solution
- Consider renaming `.claude` to `claude` to follow Python packaging conventions and maximize portability.
- Update all imports to use `from claude.agents.system_design_reviewer...`.
- Document the need to add the project root to `PYTHONPATH` or install Gadugi as a package for downstream users.

## References
- See https://gist.github.com/adamheins/6ea490795618776e8412 for a sys.path workaround example.

---
*This issue was created by GitHub Copilot to track the import path/package portability problem for Gadugi.*
