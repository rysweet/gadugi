# AI Assistant Instructions

This file combines generic Claude Code best practices with project-specific instructions for the AI-SIP workshop repository.

⚠️ **FIRST ACTION**: Check and update @.github/Memory.md ! ⚠️
⚠️ **NEW**: Memory.md now syncs with GitHub Issues via MemoryManagerAgent! ⚠️

⚠️ **SECOND ACTION**: When working on Claude agents or instructions, read https://docs.anthropic.com/en/docs/claude-code/memory ! ⚠️

---

## CRITICAL: Workflow Execution Pattern

⚠️ **MANDATORY ORCHESTRATOR USAGE** ⚠️

**ALL requests that will result in changes to version-controlled files MUST use the orchestrator agent.**

This ensures:
- Proper worktree isolation for all changes
- Consistent branch management
- Complete workflow tracking
- Parallel execution when possible
- Professional development practices

**For ANY task that modifies code, configuration, or documentation files:**

1. **NEVER manually edit files directly**
2. **ALWAYS use the orchestrator agent as the entry point**:

   ```
   /agent:orchestrator-agent

   Execute the following task:
   - [description of changes needed]
   ```

3. **The Orchestrator will automatically**:
   - Invoke the worktree-manager to create isolated environments
   - Delegate to appropriate sub-agents (WorkflowManager, etc.)
   - Coordinate parallel execution when multiple tasks exist
   - Ensure proper branch creation and PR workflow

4. **Agent Hierarchy**:
   - **OrchestratorAgent**: REQUIRED entry point for ALL code changes
   - **WorktreeManager**: Automatically invoked by orchestrator for isolation
   - **WorkflowManager**: Handles individual workflow execution
   - **Code-Reviewer**: Executes Phase 9 reviews

5. **Automated Workflow Handling**:
   - Issue creation
   - Worktree and branch management
   - Implementation tracking
   - PR creation
   - Code review invocation (Phase 9)
   - State management

**Only execute manual steps for**:
- Read-only operations (searching, viewing files)
- Answering questions about the codebase
- Running tests or builds without changes
- Direct user requests for specific read-only actions

**Before ANY task, ask yourself**:
- Will this change version-controlled files? → MUST use OrchestratorAgent
- Multiple related tasks? → Use OrchestratorAgent
- Single task with code changes? → Use OrchestratorAgent
- Read-only investigation? → Can execute manually

---

## Generic Claude Code Instructions

@claude-generic-instructions.md

## Project-Specific Instructions

@claude-project-specific.md

---

## Worktree Lifecycle Management

**IMPORTANT**: Use the worktree-manager agent for creating isolated development environments for issues.

### When to Use Worktrees

Use worktrees for:
- Working on individual issues that require code changes
- Isolating development work from the main repository
- Preventing conflicts when multiple issues are being worked on
- Creating clean environments for testing and validation

### Worktree Lifecycle

1. **Creation Phase**:
   ```
   /agent:worktree-manager

   Create a new git worktree for issue [number].
   Branch name: [type]/issue-[number]-[description]
   ```
   - Creates isolated worktree in `.worktrees/issue-[number]/`
   - Sets up new branch from main
   - Initializes task metadata in `.task/` directory

2. **Development Phase**:
   - Navigate to worktree: `cd .worktrees/issue-[number]/`
   - All development happens in isolated environment
   - Changes don't affect main repository or other worktrees
   - Commit changes regularly with descriptive messages

3. **PR Creation Phase**:
   - Push branch from within worktree
   - Create PR using `gh pr create` from worktree directory
   - Reference issue number in PR description

4. **Cleanup Phase**:
   - After PR is merged, remove worktree:
     ```bash
     git worktree remove .worktrees/issue-[number]/
     ```
   - Delete remote branch if not auto-deleted

### Worktree Best Practices

1. **One Issue, One Worktree**: Each issue gets its own isolated worktree
2. **Clean State**: Always start worktrees from latest main
3. **Regular Commits**: Commit progress frequently within worktree
4. **Task Metadata**: Use `.task/` directory for tracking progress
5. **Proper Cleanup**: Remove worktrees after PR merge to save space

### Example Workflow

```bash
# 1. Create worktree for issue 44
/agent:worktree-manager
Create worktree for issue 44 about documenting lifecycle

# 2. Navigate to worktree
cd .worktrees/issue-44/

# 3. Make changes
# ... edit files ...

# 4. Commit changes
git add .
git commit -m "docs: add worktree lifecycle documentation

- Document when to use worktrees
- Add lifecycle phases
- Include best practices
- Provide example workflow"

# 5. Push and create PR
git push -u origin docs/issue-44-worktree-lifecycle
gh pr create --base main --title "docs: add worktree lifecycle documentation" \
  --body "Closes #44

Added comprehensive documentation for worktree lifecycle management."

# 6. After merge, cleanup
cd ../..
git worktree remove .worktrees/issue-44/
```

### Worktree Agent Integration

The worktree-manager agent handles:
- Automatic branch naming based on issue type
- Task metadata initialization
- Proper isolation from main repository
- State tracking for development progress
- Integration with orchestrator for parallel work

Use worktrees whenever working on issues to maintain clean, isolated development environments.

## Memories and Best Practices

- Remember to not use artificial dev timescales in planning or estimating.
