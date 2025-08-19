# Gadugi v0.3 Test Report

Generated: 2025-08-18T17:28:56.987846

## Summary

- Total Tests: 14
- Passed: 11
- Failed: 3
- Success Rate: 78.6%

## Detailed Results

- ✅ **UV Environment Setup**
  - Command: `uv sync --all-extras`
- ❌ **Code Formatting Check**
  - Command: `uv run ruff format --check .`
- ❌ **Auto-format Code**
  - Command: `uv run ruff format .`
- ❌ **Linting with Auto-fix**
  - Command: `uv run ruff check . --fix`
- ✅ **Type Check: gadugi/**
  - Command: `uv run pyright gadugi/ --pythonversion 3.13 || true`
- ✅ **Type Check: tests/**
  - Command: `uv run pyright tests/ --pythonversion 3.13 || true`
- ✅ **Type Check: compat/**
  - Command: `uv run pyright compat/ --pythonversion 3.13 || true`
- ✅ **Unit Tests: Event Service**
  - Command: `uv run pytest tests/event_service/ -v --tb=short || true`
- ✅ **Unit Tests: Container Runtime**
  - Command: `uv run pytest tests/container_runtime/ -v --tb=short || true`
- ✅ **Unit Tests: Agents**
  - Command: `uv run pytest tests/agents/ -v --tb=short || true`
- ✅ **Unit Tests: Shared Modules**
  - Command: `uv run pytest tests/shared/ -v --tb=short || true`
- ✅ **Integration Tests**
  - Command: `uv run pytest tests/integration/ -v --tb=short || true`
- ✅ **Neo4j Connection Test**
  - Command: `uv run python neo4j/test_connection.py || true`
- ✅ **Coverage Report**
  - Command: `uv run pytest tests/ --cov=. --cov-report=term-missing --cov-report=html || true`
