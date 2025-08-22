# Fix Orchestrator Dashboard Dependencies and Syntax Errors

## Objective
Fix the orchestrator monitoring dashboard to enable real-time monitoring of parallel workflow execution.

## Context
The orchestrator dashboard at `.claude/orchestrator/monitoring/dashboard.py` currently fails to run due to:
1. **Syntax error in aiohttp dependency**: `from typing import (, Any, Dict, List, Optional, Set, Tuple` - malformed typing import
2. **Deprecated websockets import**: `websockets.server.WebSocketServerProtocol is deprecated`
3. **Missing dependency handling**: Dashboard fails when dependencies are unavailable

## Current Error
```
File "/Users/ryan/src/gadugi2/gadugi/.venv/lib/python3.13/site-packages/aiohttp/client.py", line 13
    from typing import (, Any, Dict, List, Optional, Set, Tuple
                        ^
SyntaxError: invalid syntax
```

## Requirements

### Phase 1: Dependency Analysis and Fixes
1. **Investigate aiohttp syntax error**: Check if it's a version compatibility issue with Python 3.13
2. **Update UV dependencies**: Ensure compatible versions in `pyproject.toml`
3. **Fix websockets deprecation**: Update to current websockets API
4. **Add fallback handling**: Graceful degradation when dependencies unavailable

### Phase 2: Dashboard Functionality Restoration
1. **Test basic dashboard startup**: Ensure it runs without crashes
2. **Verify WebSocket functionality**: Real-time updates working
3. **Validate monitoring features**: Container status, log streaming, progress tracking
4. **Test with current orchestrator**: Monitor the parallel workflows currently running

### Phase 3: Enhanced Monitoring Features
1. **Add current process monitoring**: Show running Claude processes with PIDs
2. **Worktree status display**: Show active orchestrator worktrees and their tasks
3. **GitHub integration monitoring**: Display recent issues/PRs created by workflows
4. **Performance metrics**: Runtime, CPU, memory usage tracking

## Technical Requirements
- **UV Environment**: Must work in UV Python project with `uv run python`
- **Dependency Management**: Handle missing dependencies gracefully
- **Web Interface**: Functional HTTP server with WebSocket support
- **Real-time Updates**: Live monitoring of orchestrator processes
- **Error Handling**: Robust error handling and logging

## Success Criteria
- Dashboard starts without syntax errors
- Web interface accessible at specified port
- Real-time monitoring of current orchestrator processes
- WebSocket updates working correctly
- Compatible with UV Python environment
- Clean dependency management

## Priority
**HIGH** - Essential for monitoring and debugging orchestrator parallel execution

## Implementation Strategy
1. **Execute via WorkflowManager**: Full 11-phase workflow for proper testing
2. **Quality gates**: All tests must pass, proper type checking
3. **UV compatibility**: Ensure all commands use `uv run` prefix
4. **No breaking changes**: Maintain existing dashboard API and functionality

## Current Context
- Orchestrator currently running 2 parallel workflows (30+ minutes runtime)
- Need working dashboard to monitor these and future parallel executions
- Dashboard is critical infrastructure for orchestrator debugging and optimization

Begin workflow execution immediately.
