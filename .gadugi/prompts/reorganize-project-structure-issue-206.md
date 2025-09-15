# Reorganize Project Structure for v0.1 Milestone

## Issue Reference
- Issue #206: Reorganize project structure - move docs, scripts, and Python files from root
- Milestone: v0.1

## Overview
The project root directory is currently cluttered with various files that should be properly organized into subdirectories. This reorganization is critical for the v0.1 release to present a clean, professional project structure that follows Python packaging best practices.

## Current Problems
1. Documentation files scattered in root directory
2. Python scripts and modules not properly organized
3. Utility scripts mixed with source code
4. Poor separation of concerns
5. Difficult navigation for new contributors
6. Unprofessional appearance for v0.1 release

## Objectives
1. Create a clean, organized project structure
2. Move all non-essential files from root to appropriate subdirectories
3. Update ALL references to moved files
4. Maintain full functionality
5. Follow Python packaging best practices
6. Improve project navigability

## Detailed Reorganization Plan

### Files to KEEP in Root (Essential Only)
```
README.md                 # Project documentation
LICENSE                   # License file
pyproject.toml           # Python project configuration
uv.lock                  # UV lock file
.gitignore               # Git ignore rules
.pre-commit-config.yaml  # Pre-commit configuration
CLAUDE.md                # Primary AI instructions (special case)
Dockerfile               # If exists
.env.example            # If exists
```

### Files to MOVE from Root

#### To `docs/` directory:
- `claude-generic-instructions.md` → `docs/ai-instructions/claude-generic-instructions.md`
- `claude-project-specific.md` → `docs/ai-instructions/claude-project-specific.md`
- `SYSTEM_DESIGN.md` → `docs/architecture/SYSTEM_DESIGN.md`
- `DESIGN_ISSUES.md` → `docs/architecture/DESIGN_ISSUES.md`
- `AGENTIC_SEARCH.md` → `docs/architecture/AGENTIC_SEARCH.md`
- `DEPENDENCY_MANAGEMENT.md` → `docs/guides/DEPENDENCY_MANAGEMENT.md`
- `DEVELOPER_GUIDE.md` → `docs/guides/DEVELOPER_GUIDE.md`
- `PROMPT_TEMPLATE.md` → `docs/templates/PROMPT_TEMPLATE.md`
- Any other `.md` files (except README.md and CLAUDE.md)

#### To `scripts/` directory:
- `check_imports.py` → `scripts/check_imports.py`
- `setup.py` → `scripts/setup.py` (if not needed for packaging)
- `run_tests.py` → `scripts/run_tests.py`
- Any other utility Python scripts

#### To `src/gadugi/` directory (Python package):
- Any Python modules currently in root
- Consider if any should be part of the main package

## Implementation Steps

### Phase 1: Analysis
1. List all files in root directory
2. Categorize each file (keep/move/delete)
3. Identify all references to files that will be moved
4. Create comprehensive reference update plan

### Phase 2: Directory Structure Creation
```bash
mkdir -p docs/ai-instructions
mkdir -p docs/architecture
mkdir -p docs/guides
mkdir -p docs/templates
mkdir -p scripts
mkdir -p src/gadugi  # If needed
```

### Phase 3: File Movement (using git mv)
```bash
# Example commands (adjust based on actual files)
git mv claude-generic-instructions.md docs/ai-instructions/
git mv claude-project-specific.md docs/ai-instructions/
git mv SYSTEM_DESIGN.md docs/architecture/
git mv DESIGN_ISSUES.md docs/architecture/
git mv check_imports.py scripts/
```

### Phase 4: Reference Updates

#### Update CLAUDE.md references:
- Change `@claude-generic-instructions.md` to `@docs/ai-instructions/claude-generic-instructions.md`
- Change `@claude-project-specific.md` to `@docs/ai-instructions/claude-project-specific.md`

#### Update Python imports:
- Find all imports of moved Python files
- Update import statements to reflect new locations

#### Update documentation references:
- Search for all markdown links to moved files
- Update relative paths in all documentation

#### Update script references:
- Update any scripts that reference moved files
- Update CI/CD configurations if they reference moved files

### Phase 5: Testing & Validation
1. Run all tests to ensure nothing is broken
2. Verify all imports work correctly
3. Check that documentation links are not broken
4. Ensure CI/CD pipelines still work
5. Test the development workflow end-to-end

## Search Patterns for Reference Updates

### Find markdown references:
```regex
\[.*\]\(((?!http|https).*\.md)\)
\@[\w-]+\.md
```

### Find Python imports:
```regex
^from [\w_]+ import
^import [\w_]+
```

### Find script executions:
```regex
python3? [\w_]+\.py
\.\/[\w_]+\.py
```

## Success Criteria
- [ ] Root directory contains only essential files (10-12 files max)
- [ ] All documentation properly organized in docs/
- [ ] All scripts organized in scripts/
- [ ] All Python modules properly packaged
- [ ] Zero broken imports or references
- [ ] All tests passing
- [ ] All workflows functioning
- [ ] Git history preserved for all moved files
- [ ] README updated with new structure documentation

## Testing Requirements
1. **Pre-move testing**: Capture current test results as baseline
2. **Post-move testing**:
   - `uv sync --all-extras`
   - `uv run pytest tests/`
   - `uv run ruff check .`
   - `uv run pre-commit run --all-files`
3. **Import verification**: Run check_imports.py after moving
4. **Documentation verification**: Check all markdown links
5. **Workflow verification**: Test agent workflows still function

## Risk Mitigation
1. **Create inventory first**: List all files and their references before moving
2. **Move in batches**: Group related files and update references together
3. **Test after each batch**: Ensure nothing breaks incrementally
4. **Use git mv**: Preserve file history
5. **Comprehensive search**: Use multiple search methods to find all references
6. **Backup branch**: Work in isolated branch with ability to rollback

## Expected Outcome
A clean, professional project structure ready for v0.1 release:
```
gadugi/
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .pre-commit-config.yaml
├── CLAUDE.md
├── docs/
│   ├── ai-instructions/
│   │   ├── claude-generic-instructions.md
│   │   └── claude-project-specific.md
│   ├── architecture/
│   │   ├── SYSTEM_DESIGN.md
│   │   └── DESIGN_ISSUES.md
│   └── guides/
│       └── DEVELOPER_GUIDE.md
├── scripts/
│   ├── check_imports.py
│   └── [other utility scripts]
├── src/
│   └── gadugi/
│       └── [Python modules if any]
└── [other essential directories]
```

## Notes
- This is a HIGH PRIORITY task for v0.1 milestone
- Requires careful attention to detail to avoid breaking references
- Must maintain full functionality throughout the reorganization
- Consider impact on any external tools or documentation that reference current structure
