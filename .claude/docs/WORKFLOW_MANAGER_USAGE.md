# WorkflowManager Usage Guide

## Overview

WorkflowManager is a specialized sub-agent that orchestrates complete development workflows from prompt files. It ensures consistent execution of all development phases from issue creation through PR review.

**🚨 NEW: Enhanced Consistency and Phase 9 Enforcement**

WorkflowManager now includes multiple enforcement mechanisms to ensure 100% reliable code review execution and prevent early workflow termination. See [WORKFLOW_MANAGER_CONSISTENCY.md](./WORKFLOW_MANAGER_CONSISTENCY.md) for complete details.

## Invocation

```
/agent:WorkflowManager

Execute the workflow from: /prompts/FeatureName.md
```

## What WorkflowManager Does

1. **Reads and parses** the specified prompt file
2. **Creates a comprehensive task list** using TodoWrite
3. **Executes each phase** systematically:
   - Creates GitHub issue
   - Creates feature branch
   - Researches and plans
   - Implements incrementally
   - Writes tests
   - Updates documentation
   - Creates pull request
   - Coordinates review

4. **Tracks progress** throughout execution
5. **Handles errors** gracefully
6. **Saves state** if interrupted

## Example Session

```
User: /agent:WorkflowManager
      Execute the workflow from: /prompts/AddCacheFeature.md

WorkflowManager: I'll execute the workflow described in `/prompts/AddCacheFeature.md`.

[Creates task list with TodoWrite]

Starting Phase 1: Issue Creation
[Creates GitHub issue #42]

Starting Phase 2: Branch Management
[Creates branch feature/add-cache-42]

Starting Phase 3: Research and Planning
[Analyzes codebase, updates Memory.md]

[... continues through all phases ...]

Starting Phase 9: Review
[Invokes CodeReviewer sub-agent]

Workflow complete! Feature delivered from issue #42 to PR #99.
```

## Integration with Other Agents

### PromptWriter
- Creates the structured prompts that WorkflowManager executes
- Ensures prompts include all necessary workflow information

### CodeReviewer
- Invoked by WorkflowManager during the review phase
- Provides comprehensive PR feedback

## Error Handling

WorkflowManager handles common issues:
- Git conflicts
- Test failures
- CI/CD issues
- Review feedback

Each error includes:
- Clear explanation
- Suggested resolution
- Updated task status

## State Management

If interrupted, WorkflowManager saves state to `.github/Memory.md`:
- Current phase
- Completed tasks
- Next steps
- Any blockers

## Best Practices

1. **Always provide a valid prompt file** from `/prompts/`
2. **Ensure clean working directory** before invocation
3. **Monitor progress** via task updates
4. **Allow WorkflowManager to complete** all phases
5. **Review the final PR** before merging

## Workflow Templates

See `.claude/agents/workflow-templates/` for examples:
- `standard-feature.md` - Standard feature development
- `bug-fix.md` - Bug fix workflow
- More templates for specific scenarios

## Troubleshooting

### "Prompt file not found"
- Ensure the prompt file exists in `/prompts/`
- Check the file path spelling

### "Git working directory not clean"
- Commit or stash current changes
- Run `git status` to check

### "Tests failing"
- WorkflowManager will attempt to fix
- May need manual intervention for complex issues

### "CI/CD failures"
- Check pipeline logs
- WorkflowManager will attempt common fixes

## Success Metrics

WorkflowManager aims for:
- 95%+ workflow completion rate
- All phases executed in order
- Clean git history
- Comprehensive PRs
- Passing reviews

## Future Enhancements

### Short-term (1-2 weeks)
- **Priority 1**: Integration test suite for WorkflowManager
  - Test prompt validation mechanism
  - Verify TodoWrite task structure validation
  - End-to-end workflow execution tests
- **Priority 2**: Additional workflow templates
  - Documentation updates workflow
  - Refactoring workflow
  - Performance optimization workflow

### Medium-term (1 month)
- **Priority 1**: Enhanced error recovery
  - Automatic retry mechanisms for transient failures
  - Smarter conflict resolution for git operations
  - Better handling of partial workflow completion
- **Priority 2**: Metrics and reporting
  - Workflow execution time tracking
  - Success/failure rate monitoring
  - Common failure pattern identification

### Long-term (3+ months)
- **Priority 1**: AI-powered workflow optimization
  - Learn from successful workflows
  - Suggest workflow improvements
  - Adaptive task prioritization
- **Priority 2**: Multi-agent coordination
  - Parallel task execution where possible
  - Complex workflow orchestration
  - Cross-repository workflow support
