# Update All Agents to Use model: inherit

## Objective
Standardize all agent files in `.claude/agents/` to use `model: inherit` in their frontmatter, ensuring consistent model inheritance across the entire agent ecosystem.

## Background
Currently, agent files have inconsistent model specifications in their frontmatter. We need to standardize all agents to use `model: inherit` to ensure they properly inherit the model from the parent context.

## Requirements

### 1. Update Frontmatter
- Add or update the `model:` field to be `model: inherit` in all agent files
- Preserve all other existing frontmatter fields
- Maintain proper YAML frontmatter format

### 2. Files to Update
All 28 agent files in `.claude/agents/`:
- AgentUpdater.md
- ClaudeSettingsUpdate.md
- CodeReviewResponse.md
- CodeReviewer.md
- ExecutionMonitor.md
- gadugi.md
- MemoryManager.md
- OrchestratorAgent.md
- PrBacklogManager.md
- ProgramManager.md
- PromptWriter.md
- ReadmeAgent.md
- SystemDesignReviewer.md
- TaskAnalyzer.md
- TaskBoundsEval.md
- TaskDecomposer.md
- TaskResearchAgent.md
- TeamCoach.md
- TeamcoachAgent.md
- TestSolver.md
- TestWriter.md
- TypeFixAgent.md
- WorkflowManagerPhase9Enforcement.md
- WorkflowManagerSimplified.md
- WorkflowManager.md
- WorkflowPhaseReflection.md
- WorktreeManager.md
- XpiaDefenseAgent.md

### 3. Frontmatter Format
Ensure all agent files follow this structure:
```yaml
---
name: agent-name
model: inherit
tools: [list, of, tools]
# any other existing fields preserved
---
```

## Implementation Steps

1. **Analyze Current State**
   - Check each agent file's current frontmatter
   - Identify which files need updates
   - Document current model settings

2. **Update Frontmatter**
   - For files without `model:` field: add `model: inherit` after `name:` field
   - For files with existing `model:` field: update value to `inherit`
   - Preserve all other frontmatter content and ordering

3. **Validation**
   - Verify all files have valid YAML frontmatter
   - Confirm `model: inherit` is present in all files
   - Ensure no content outside frontmatter is modified

## Success Criteria
- All 28 agent files have `model: inherit` in their frontmatter
- No other content is modified
- All frontmatter remains valid YAML
- Git history shows clean, atomic commits for the changes

## Testing
- Verify agents can still be invoked correctly
- Check that model inheritance works as expected
- Ensure no syntax errors in frontmatter

## Notes
- This is a standardization effort to ensure consistent behavior across all agents
- The `inherit` value allows agents to use the model specified by the parent context
- This change should not affect agent functionality, only improve consistency
