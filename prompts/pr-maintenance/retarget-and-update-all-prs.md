# Retarget and Update All v0.3 PRs to Regeneration Branch

## Task Overview
Systematically update all 15 open PRs that should target the v0.3 regeneration branch but currently target main.

## PRs to Process

### High Priority Infrastructure PRs
1. **PR #287**: Fix Orchestrator Subprocess Execution
2. **PR #280**: Fix Event Router Type Errors (67 errors)
3. **PR #278**: Fix Test Infrastructure Collection Errors

### Pyright Error Reduction PRs (Need Consolidation)
4. **PR #279**: Systematic pyright error reduction
5. **PR #270**: Reduce pyright errors 442→178 (60% reduction)
6. **PR #286**: Code quality compliance (24% reduction)
7. **PR #293**: Comprehensive pyright error fixes

### Feature Implementation PRs
8. **PR #282**: Neo4j service implementation
9. **PR #281**: Team Coach agent
10. **PR #247**: Task Decomposer agent

### Dashboard and Monitoring
11. **PR #295**: Enhanced Orchestrator Dashboard
12. **PR #294**: Systematic PR Review Workflow

### System Design and Testing
13. **PR #269**: System Design Review
14. **PR #268**: Complete Testing Suite

### Main v0.3 Branch
15. **PR #184**: Complete v0.3 Regeneration (already targets regeneration)

## Required Actions for Each PR

1. **Change base branch** from `main` to `feature/gadugi-v0.3-regeneration`
2. **Fetch and merge** latest regeneration branch to resolve conflicts
3. **Push updates** to remote
4. **Trigger code review** via CodeReviewer agent

## Execution Strategy

### Phase 1: Retarget PRs
```bash
gh pr edit <PR_NUMBER> --base feature/gadugi-v0.3-regeneration
```

### Phase 2: Update Each Branch
For each PR:
```bash
# Checkout PR branch
gh pr checkout <PR_NUMBER>

# Fetch latest regeneration branch
git fetch origin feature/gadugi-v0.3-regeneration

# Merge regeneration branch
git merge origin/feature/gadugi-v0.3-regeneration

# Resolve conflicts if any (keeping v0.3 changes generally)
# Push updates
git push
```

### Phase 3: Code Reviews
Invoke CodeReviewer agent for each updated PR

## Priority Order
1. Infrastructure fixes first (287, 280, 278)
2. Consolidate pyright PRs (279, 270, 286, 293)
3. Feature PRs (282, 281, 247)
4. Dashboard/monitoring (295, 294)
5. System/testing (269, 268)

## Success Criteria
- All PRs target feature/gadugi-v0.3-regeneration
- All merge conflicts resolved
- All PRs have updated code reviews
- CI/CD checks passing