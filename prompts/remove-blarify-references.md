# Remove All Blarify References from Codebase

## Objective
Remove all references to "Blarify" or "blarify" from the entire codebase, including agent files, documentation, tests, and prompts.

## Context
The codebase contains references to "Blarify" that need to be completely removed. These references appear in 18 files across various directories including agents, documentation, tests, and prompts.

## Requirements
1. Search and identify all occurrences of "Blarify" or "blarify" (case-insensitive)
2. Remove or replace these references appropriately based on context
3. Ensure all affected files remain functional after removal
4. Maintain proper formatting and structure in all modified files

## Files to Update
The following files contain Blarify references:
- `.claude/agents/workflow-manager.md`
- `.claude/agents/code-review-response.md`
- `.claude/agents/code-reviewer.md`
- `.claude/agents/task-analyzer.md`
- `.claude/agents/prompt-writer.md`
- `.claude/agents/orchestrator-agent.md`
- `.claude/orchestrator/components/task_analyzer.py`
- `.claude/orchestrator/tests/test_task_analyzer.py`
- `.claude/orchestrator/README.md`
- `.claude/docs/test-workflow-execution.md`
- `.claude/docs/PROMPT_WRITER_USAGE.md`
- `prompts/fix-orchestrator-workflowmaster-implementation-issue-1.md`
- `prompts/WorkflowMaster.md`
- `prompts/PromptWriter.md`
- `prompts/OrchestratorAgent.md`
- `prompts/CodeReviewResponseAgent.md`
- `prompts/CodeReviewSubAgent.md`
- `AGENT_HIERARCHY.md`

## Implementation Steps
1. Create a new branch for this cleanup task
2. Systematically review each file and remove Blarify references
3. Update any examples to use generic or project-specific references instead
4. Ensure all agent definitions remain valid after changes
5. Run any applicable tests to verify functionality
6. Create a PR with all changes

## Success Criteria
- All references to "Blarify" or "blarify" are removed from the codebase
- All agent files remain syntactically valid
- Documentation is updated to use appropriate alternative examples
- No broken functionality after removal
- Clean commit history showing the systematic removal

## Notes
- Replace Blarify references with generic examples or Gadugi-specific content where appropriate
- Maintain the integrity of code examples and agent instructions
- Ensure consistency across all modified files