# Phase 11: Settings and Configuration Recommendations

Based on the system design review of Gadugi v0.3, the following settings and configurations should be updated:

## Immediate Configuration Updates

### 1. Test Infrastructure Settings
**File**: `pyproject.toml`
```toml
[tool.pytest.ini_options]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
testpaths = ["tests"]
# Add to fix import issues:
pythonpath = ["."]
```

### 2. Type Checking Configuration
**File**: `pyrightconfig.json`
```json
{
  "exclude": [
    "**/__pycache__",
    "**/*.md",
    ".venv",
    "build",
    "dist"
  ],
  "reportUnusedVariable": "warning",
  "reportUnusedImport": "warning"
}
```

### 3. Pre-commit Hooks Update
**File**: `.pre-commit-config.yaml`
- Current hooks are working correctly
- No updates needed at this time

## Environment Configuration

### 1. Neo4j Docker Configuration
**Action Required**: Create `docker-compose.yml` for Neo4j
```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5-community
    ports:
      - "7475:7474"  # HTTP for Gadugi
      - "7688:7687"  # Bolt for Gadugi
    environment:
      - NEO4J_AUTH=neo4j/gadugi123
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - ./neo4j/data:/data
      - ./neo4j/init:/init
```

### 2. GitHub Actions Configuration
**Recommendation**: Add workflow for automated validation
```yaml
name: System Validation
on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Run validation
        run: |
          uv sync --all-extras
          uv run python validate_v03_implementation.py
```

## Development Settings

### 1. VSCode Settings
**File**: `.vscode/settings.json`
```json
{
  "python.linting.enabled": false,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

### 2. UV Configuration
**File**: `pyproject.toml` (UV section)
- Current UV configuration is correct
- Dependencies are properly specified

## Priority Settings to Update

### High Priority (Fix Immediately)
1. **Test Infrastructure**: Add pythonpath to pytest configuration
2. **Import Resolution**: Update PYTHONPATH in development environment
3. **Type Stubs**: Install missing type stubs for test libraries

### Medium Priority (Within 1 Week)
1. **Neo4j Setup**: Create docker-compose configuration
2. **CI/CD Pipeline**: Add automated validation workflow
3. **Documentation**: Update README with validation instructions

### Low Priority (Future Enhancement)
1. **Performance Monitoring**: Add APM configuration
2. **Security Scanning**: Add security scanning tools
3. **Coverage Reporting**: Configure coverage thresholds

## Environment Variables

Create `.env.example` file:
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=gadugi123

# MCP Service
MCP_PORT=8000
MCP_HOST=0.0.0.0

# Event Router
EVENT_ROUTER_PORT=8001
EVENT_ROUTER_MAX_WORKERS=4

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

## Validation Script Integration

The `validate_v03_implementation.py` script should be:
1. Added to pre-commit hooks for automated validation
2. Integrated into CI/CD pipeline
3. Run before each release

## Summary

These configuration updates will:
- Fix the test infrastructure issues
- Improve type checking accuracy
- Enable Neo4j integration
- Automate validation processes
- Improve developer experience

**Next Action**: Implement high-priority settings updates to unblock development.

---

*Phase 11 Settings Update completed as part of the WorkflowManager workflow execution.*
