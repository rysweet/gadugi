# Ephemeral Agent: Prompt Conflict and Consistency Reviewer

## Agent Purpose
This is a specialized ephemeral agent designed to review multiple development prompts for potential conflicts, overlaps, and opportunities for consistency and reuse before parallel execution.

## Task Description

### Objective
Review all prompts created for issue #9 implementation to ensure:
1. No conflicting implementations that would cause merge conflicts
2. Consistent approaches across similar functionality
3. Identification of shared components and reuse opportunities
4. Proper dependency sequencing
5. Consistent naming conventions and architectural patterns

### Prompts to Review

#### Phase 1 Prompts (Parallel Execution)
1. `implement-xpia-defense-agent.md` - XPIA defense system
2. `setup-container-execution-environment.md` - Container execution
3. `integrate-memory-github-issues.md` - Memory management refactoring
4. `enhance-task-decomposition-analyzer.md` - Task analysis enhancement

#### Phase 2 Prompts (Sequential)
5. `analyze-orchestrator-workflowmaster-architecture.md` - Architecture analysis

#### Phase 3 Prompts (Parallel Execution)
6. `fix-workflowmaster-brittleness-issues.md` - WorkflowManager robustness
7. `implement-teamcoach-agent.md` - Team intelligence
8. `create-systematic-agent-creation-system.md` - Agent creation
9. `enhance-claude-code-hooks-integration.md` - Hooks integration

### Review Criteria

#### 1. Conflict Detection
- File modification overlaps
- Shared resource contention
- API/interface conflicts
- Configuration file conflicts
- Git branch/merge conflicts

#### 2. Consistency Opportunities
- Common utility functions
- Shared data structures
- Consistent error handling patterns
- Unified logging approaches
- Common testing frameworks

#### 3. Architectural Alignment
- Naming convention consistency
- Module structure patterns
- Interface design standards
- Documentation format alignment
- Code style consistency

#### 4. Dependency Validation
- Proper phase sequencing
- Inter-prompt dependencies
- Shared component availability
- Integration point readiness

#### 5. Reuse Identification
- Common agent base classes
- Shared hook implementations
- Utility function libraries
- Testing helper modules
- Configuration templates

### Required Actions

1. **Read and analyze each prompt file**
2. **Create a conflict matrix** identifying potential issues
3. **Document consistency recommendations**
4. **Identify reusable components** that should be extracted
5. **Validate dependency sequencing** is correct
6. **Provide specific recommendations** for each identified issue

### Output Format

Generate a comprehensive report with:

```markdown
# Prompt Review Report

## Executive Summary
- Total prompts reviewed: 9
- Critical conflicts found: X
- Consistency opportunities: Y
- Reuse recommendations: Z

## Conflict Analysis
### Critical Conflicts
1. [Prompt A] vs [Prompt B]: Description of conflict

### Potential Issues
1. [Issue description and affected prompts]

## Consistency Recommendations
### Naming Conventions
- Recommendation 1
- Recommendation 2

### Shared Components
- Component 1: Used by [prompts]
- Component 2: Used by [prompts]

## Reuse Opportunities
### Base Classes
- BaseAgent: Common functionality for all agents
- BaseHook: Shared hook implementation

### Utility Libraries
- prompt_utils.py: Common prompt handling
- memory_utils.py: Shared memory operations

## Dependency Validation
✅ Phase 1 → Phase 2 → Phase 3 sequencing correct
⚠️ [Any dependency issues found]

## Specific Recommendations
### For implement-xpia-defense-agent.md
- [Specific recommendations]

[Continue for each prompt]

## Implementation Priority
1. Create shared base classes first
2. Implement utility libraries
3. Proceed with parallel execution as planned
```

### Success Criteria
- All potential conflicts identified and documented
- Clear recommendations for consistency improvements
- Reusable components properly identified
- No critical conflicts that would prevent parallel execution
- Actionable recommendations for each issue found

### Time Limit
This ephemeral agent should complete its review within 15-20 minutes and self-terminate after delivering the report.

## Execution
This agent should be invoked immediately before orchestrator-agent execution to ensure all prompts are properly reviewed and any critical issues are addressed before parallel implementation begins.
