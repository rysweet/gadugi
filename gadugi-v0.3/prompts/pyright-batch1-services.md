# Fix Pyright Errors - Batch 1: Services

## Task Description
Fix pyright errors in service files (107 errors total):

**Target Files:**
- `services/neo4j-graph/neo4j_graph_service.py` (44 errors)
- `services/cli/gadugi_cli_service.py` (33 errors) 
- `services/mcp/mcp_service.py` (17 errors)
- `services/llm-proxy/llm_proxy_service.py` (13 errors)

## Requirements
- Work on feature/gadugi-v0.3-regeneration branch
- Create feature branch: `fix/pyright-batch1-services`
- Fix actual type issues, don't just add ignore comments
- Common error patterns to fix:
  - Missing type annotations
  - Import resolution issues (add sys.path adjustments)
  - Undefined variables
  - Type mismatches
  - Missing return types
- Ensure pyright passes for these files after fixes
- Create PR to feature/gadugi-v0.3-regeneration branch

## Success Criteria
- All 107 errors in service files are resolved
- No new pyright errors introduced
- All files maintain functionality
- Clean, type-safe code with proper annotations