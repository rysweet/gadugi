# Pyright Type Safety Enforcement Setup

## Task: Establish Permanent Type Safety

### 1. Update pyrightconfig.json
Ensure strict type checking:

```json
{
  "include": ["gadugi-v0.3/**/*.py"],
  "exclude": ["**/node_modules", "**/__pycache__", "**/.*"],
  "strict": ["gadugi-v0.3/src/**/*.py"],
  "typeCheckingMode": "strict",
  "reportMissingImports": "error",
  "reportMissingTypeStubs": "warning",
  "reportUnusedImport": "error",
  "reportUnusedClass": "error",
  "reportUnusedFunction": "error",
  "reportUnusedVariable": "error",
  "reportDuplicateImport": "error",
  "reportOptionalMemberAccess": "error",
  "reportOptionalCall": "error",
  "reportUntypedFunctionDecorator": "warning",
  "reportUntypedClassDecorator": "warning",
  "reportUntypedBaseClass": "warning",
  "reportGeneralTypeIssues": "error",
  "pythonVersion": "3.9",
  "pythonPlatform": "All",
  "executionEnvironments": [
    {
      "root": "gadugi-v0.3",
      "pythonVersion": "3.9",
      "extraPaths": ["gadugi-v0.3/src", "gadugi-v0.3/src/orchestrator"]
    }
  ]
}
```

### 2. Update Pre-commit Hooks
Add to .pre-commit-config.yaml:

```yaml
repos:
  - repo: https://github.com/microsoft/pyright
    rev: v1.1.354
    hooks:
      - id: pyright
        name: pyright type check v0.3
        files: ^gadugi-v0.3/.*\.py$
        pass_filenames: false
        additional_dependencies: ['pyright@1.1.354']
        args: ['gadugi-v0.3']
```

### 3. Update CI Workflow
Add to .github/workflows/test.yml:

```yaml
  pyright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r gadugi-v0.3/requirements.txt
          npm install -g pyright
      - name: Run pyright
        run: |
          pyright gadugi-v0.3
```

### 4. Update Agent Shared Instructions
Create gadugi-v0.3/AGENT_INSTRUCTIONS.md:

```markdown
# Agent Code Generation Instructions

## Type Safety Requirements

ALL agents generating Python code for Gadugi v0.3 MUST:

1. **Include Type Annotations**
   - All function parameters must have type hints
   - All function returns must have type annotations
   - Use `from typing import` for complex types

2. **Handle Optional Types Properly**
   ```python
   # WRONG
   if self.config:
       use_config()
   
   # CORRECT
   if self.config is not None:
       use_config()
   ```

3. **Use Proper Async Types**
   ```python
   from typing import AsyncGenerator, Coroutine
   
   async def process() -> None:
       pass
   
   async def stream() -> AsyncGenerator[str, None]:
       yield "data"
   ```

4. **Initialize Dataclass Fields Correctly**
   ```python
   from dataclasses import dataclass, field
   
   @dataclass
   class Config:
       items: List[str] = field(default_factory=list)
       # NOT: items: List[str] = []
   ```

5. **Test Import Paths**
   ```python
   # In test files
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
   ```

## Validation Before Commit

Before committing any Python code:
1. Run `pyright gadugi-v0.3` locally
2. Fix all errors (not just warnings)
3. Ensure CI will pass

## Type Checking Tools

Use these commands:
- Check all: `pyright gadugi-v0.3`
- Check file: `pyright gadugi-v0.3/path/to/file.py`
- Auto-fix imports: `isort gadugi-v0.3`
```

### 5. Update CLAUDE.md
Add to the Gadugi v0.3 section:

```markdown
## Type Safety Requirements for v0.3

**CRITICAL**: All Python code in gadugi-v0.3 MUST be pyright type-safe.

When generating or modifying Python code:
1. Include full type annotations
2. Handle Optional types with `is not None` checks
3. Use proper async type hints
4. Initialize dataclass fields with field(default_factory=...)
5. Test files must set up sys.path correctly

Run `pyright gadugi-v0.3` before committing any Python changes.
```

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-enforcement-setup
- Update all configuration files
- Test that enforcement works
- Document for future developers