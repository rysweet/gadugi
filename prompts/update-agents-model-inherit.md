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
- agent-updater.md
- claude-settings-update.md
- code-review-response.md
- code-reviewer.md
- execution-monitor.md
- gadugi.md
- memory-manager.md
- orchestrator-agent.md
- pr-backlog-manager.md
- program-manager.md
- prompt-writer.md
- readme-agent.md
- system-design-reviewer.md
- task-analyzer.md
- task-bounds-eval.md
- task-decomposer.md
- task-research-agent.md
- team-coach.md
- teamcoach-agent.md
- test-solver.md
- test-writer.md
- type-fix-agent.md
- workflow-manager-phase9-enforcement.md
- workflow-manager-simplified.md
- workflow-manager.md
- workflow-phase-reflection.md
- worktree-manager.md
- xpia-defense-agent.md

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
