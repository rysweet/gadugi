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
   - **WorkflowManager**: Handles individual workflow execution (MANDATORY for all tasks)
   - **Code-Reviewer**: Executes Phase 9 reviews

**⚠️ GOVERNANCE ENFORCEMENT**: The OrchestratorAgent MUST ALWAYS delegate ALL task execution to WorkflowManager instances. Direct execution is PROHIBITED to ensure complete workflow phases are followed (Issue #148).

5. **Automated Workflow Handling**:
   - Issue creation
   - Worktree and branch management
   - Implementation tracking
   - PR creation
   - Code review invocation (Phase 9)
   - State management

6. **Mandatory 11-Phase Workflow** (ALL tasks MUST follow):
   - Phase 1: Initial Setup
   - Phase 2: Issue Creation
   - Phase 3: Branch Management
   - Phase 4: Research and Planning
   - Phase 5: Implementation
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request
   - Phase 9: Review (code-reviewer invocation)
   - Phase 10: Review Response
   - Phase 11: Settings Update

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

**Workflow Validation Requirements**:
- Orchestrator MUST delegate ALL tasks to WorkflowManager
- ALL 11 workflow phases MUST be executed for every task
- NO direct execution bypassing workflow phases
- State tracking MUST be maintained throughout all phases
- Quality gates MUST be validated at each phase transition

### Emergency Procedures (Critical Production Issues)

⚠️ **EMERGENCY HOTFIX EXCEPTION** ⚠️

For **CRITICAL PRODUCTION ISSUES** requiring immediate fixes (security vulnerabilities, system downtime, data corruption), you may bypass the orchestrator requirement:

**Emergency Criteria** (ALL must be true):
- Production system is down or compromised
- Issue poses immediate security risk or data loss
- Fix is simple and well-understood (< 10 lines of code)
- No time for full workflow due to business impact

**Emergency Procedure**:
1. **Document the emergency**: Create issue with `emergency` label
2. **Work directly on main branch** (exception to normal branching)
3. **Make minimal, focused changes only**
4. **Commit with clear emergency attribution**:
   ```bash
   git commit -m "EMERGENCY: fix critical [issue description]
   
   Emergency hotfix bypassing normal orchestrator workflow
   due to production impact. Full workflow to follow.
   
   Fixes: [issue-number]"
   ```
5. **Immediately create follow-up issue** for proper workflow implementation
6. **Return to orchestrator requirement** for all subsequent changes

**Post-Emergency Actions**:
- Conduct immediate post-mortem
- Implement proper tests via orchestrator workflow
- Update documentation to prevent recurrence
- Review emergency decision in next team meeting

**Important**: Emergency exception should be used < 1% of the time. If used frequently, reassess development practices.

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

## Troubleshooting: Orchestrator and Worktree Failures

When the mandatory orchestrator workflow encounters issues, use these troubleshooting procedures:

### Common Orchestrator Failures

#### 1. Orchestrator Agent Not Found
**Symptoms**: `/agent:orchestrator-agent` returns "agent not found" error
**Solution**:
```bash
# Check if orchestrator files exist
ls -la .claude/agents/orchestrator-agent.md
ls -la src/orchestrator/

# If missing, restore from main branch
git checkout main -- .claude/agents/orchestrator-agent.md
git checkout main -- src/orchestrator/
```

#### 2. Orchestrator Hangs or Times Out
**Symptoms**: Orchestrator starts but never completes, no progress updates
**Solution**:
```bash
# Kill hung orchestrator processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Check system resources
df -h  # Disk space
free -h  # Memory (Linux) or vm_stat (macOS)

# Restart with verbose logging
/agent:orchestrator-agent
# Add troubleshooting flag if available
```

#### 3. Task Analysis Fails
**Symptoms**: Orchestrator fails during task decomposition phase
**Fallback Procedure**:
1. Try simpler task breakdown manually
2. Use WorkflowManager directly for single tasks:
   ```
   /agent:workflow-manager
   
   Task: Execute workflow for /prompts/[single-prompt].md
   ```
3. Execute critical tasks manually as last resort (document as emergency)

### Common Worktree Failures

#### 1. Worktree Creation Fails
**Symptoms**: "fatal: cannot create worktree" or permission errors
**Solution**:
```bash
# Check git repository status
git status
git worktree list

# Clean up existing worktrees if needed
git worktree prune

# Check disk space and permissions
df -h
ls -la .worktrees/

# Create worktree manually as fallback
git worktree add .worktrees/manual-fix-$(date +%s) -b manual-fix-branch
```

#### 2. Worktree Branch Conflicts
**Symptoms**: Branch already exists or checkout fails
**Solution**:
```bash
# List existing branches
git branch -a

# Remove conflicting remote branch
git push origin --delete conflicting-branch-name

# Clean up local references
git worktree prune
git branch -D conflicting-branch-name

# Try worktree creation again
```

#### 3. Worktree Cleanup Issues
**Symptoms**: Cannot remove worktree, "worktree locked" errors
**Solution**:
```bash
# Force unlock worktree
git worktree unlock .worktrees/stuck-worktree/

# Force remove worktree
git worktree remove --force .worktrees/stuck-worktree/

# Manual cleanup if needed
rm -rf .worktrees/stuck-worktree/
git worktree prune
```

### Fallback Strategies

#### 1. Orchestrator Unavailable - Use WorkflowManager
When orchestrator completely fails, use WorkflowManager for individual tasks:
```
/agent:workflow-manager

Task: [describe specific task]
Emergency fallback from orchestrator failure: [brief reason]
```

#### 2. WorkflowManager Unavailable - Manual Workflow
When both orchestrator and WorkflowManager fail:
1. **Document the failure** in an issue immediately
2. **Work in a regular branch** (not main):
   ```bash
   git checkout -b emergency-manual-fix-$(date +%s)
   ```
3. **Follow manual workflow**:
   - Make minimal, focused changes
   - Test thoroughly
   - Create PR with detailed explanation
   - Tag as `emergency` and `manual-workflow`

#### 3. Complete Agent System Failure
For extreme cases where all agents are unavailable:
1. **Create emergency issue** documenting the system failure
2. **Work carefully on feature branch** with manual procedures
3. **Document all steps taken** for post-incident analysis
4. **Restore agent system** before continuing normal development
5. **Conduct post-mortem** to prevent recurrence

### Recovery Procedures

#### 1. State Recovery
If orchestrator fails mid-execution:
```bash
# Check for state files
find . -name "*.orchestrator.state" -o -name "*.workflow.state"

# Review partial progress
cat .task/progress.json  # If exists

# Clean up partial work
git worktree list
# Remove failed worktrees as needed
```

#### 2. Resource Recovery
Clean up after failed orchestrator runs:
```bash
# Clean up processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Clean up temporary files
find /tmp -name "*orchestrator*" -mtime +1 -delete
find /tmp -name "*worktree*" -mtime +1 -delete

# Clean up git worktrees
git worktree prune
```

#### 3. System Health Check
Before retrying failed operations:
```bash
# Check system resources
df -h                    # Disk space
ps aux | grep claude     # Running processes
git status              # Repository state
git worktree list       # Active worktrees

# Test basic agent functionality
/agent:task-analyzer
Simple test task analysis
```

### Prevention Measures

1. **Regular Maintenance**:
   - Run `git worktree prune` weekly
   - Monitor disk space before large operations
   - Keep agents updated with latest versions

2. **Monitoring**:
   - Watch for repeated failures in similar scenarios
   - Document failure patterns for system improvements
   - Monitor system resource usage during orchestration

3. **Backup Strategies**:
   - Keep known-good versions of agent files
   - Maintain manual procedure documentation
   - Regular testing of fallback procedures

### When to Escalate

Escalate to system maintainers when:
- Same failure occurs > 3 times
- Worktree system becomes completely unusable
- Agent files appear corrupted or missing
- System resource issues prevent normal operation
- Manual fallbacks also fail consistently

Remember: The goal is to maintain development velocity while preserving quality and safety standards.

## Memories and Best Practices

- Remember to not use artificial dev timescales in planning or estimating.
