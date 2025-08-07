# Claude Code Generic Instructions

## Required Context

**CRITICAL - MUST DO AT START OF EVERY SESSION**:
1. **READ** `.github/Memory.md` for current context
2. **UPDATE** `.github/Memory.md` after completing any significant task
3. **COMMIT** Memory.md changes regularly to preserve context
4. **NEW**: Memory.md automatically syncs with GitHub Issues for better project visibility

**Memory.md is your persistent brain across sessions - USE IT!**
**NEW**: Tasks in Memory.md are automatically converted to GitHub Issues for collaboration and tracking.

**WHEN WORKING ON CLAUDE AGENTS OR INSTRUCTIONS**:
- **READ** https://docs.anthropic.com/en/docs/claude-code/memory for proper import syntax
- **READ** https://docs.anthropic.com/en/docs/claude-code/sub-agents for agent patterns
- **USE** `@` syntax for imports, not manual includes

## Using GitHub CLI for Issue and PR Management

**IMPORTANT**: When creating issues, PRs, or comments using `gh` CLI, always include a note that the action was performed by an AI agent on behalf of the repository owner. Add "*Note: This [issue/PR/comment] was created by an AI agent on behalf of the repository owner.*" to the body.

### Issues
```bash
# Create a new issue
gh issue create --title "Issue title" --body "Issue description"

# List open issues
gh issue list

# View issue details
gh issue view <issue-number>

# Update issue
gh issue edit <issue-number>

# Close issue
gh issue close <issue-number>
```

### Pull Requests
```bash
# Create a PR
gh pr create --base main --head feature-branch --title "PR title" --body "PR description"

# List PRs
gh pr list

# View PR details
gh pr view <pr-number>

# Check PR status
gh pr checks <pr-number>

# Merge PR
gh pr merge <pr-number>
```

### Workflows
```bash
# List workflow runs
gh workflow run list

# View workflow run details
gh run view <run-id>

# Watch workflow run in real-time
gh run watch <run-id>
```

## Best Practices for AI-Enhanced Development

### 1. Clear Documentation
- Maintain documentation files with up-to-date instructions and context
- Document all major decisions and architectural choices
- Include examples and edge cases in documentation

### 2. Structured Task Management
- Break down complex features into smaller, manageable tasks
- Use GitHub issues to track all work items
- Create detailed implementation plans before coding

### 3. Iterative Improvement
- Start with a working prototype and iterate
- Use test-driven development when possible
- Course-correct early based on test results

### 4. Context Management
- Use `/clear` command to reset context when switching tasks
- Keep focused on one feature at a time
- Reference specific files when discussing code changes

### 5. Subagents
- Subagents are documented at https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Utilize specialized agents for repetitive tasks
- Create new agents for common patterns or issues
- Document agent capabilities and usage patterns
- Subagents can be used to pass scoped or limited context to specialized agents for focused tasks

## Memory Storage Instructions

### Regular Memory Updates
You should regularly update the memory file at `.github/Memory.md` with:
- Current date and time
- Consolidated summary of completed tasks
- Current todo list with priorities
- Important context and decisions made
- Any blockers or issues encountered

### Memory File Format
```markdown
# AI Assistant Memory
Last Updated: [ISO 8601 timestamp]

## Current Goals
[List of active goals]

## Todo List
[Current tasks with status]

## Recent Accomplishments
[What was completed recently]

## Important Context
[Key decisions, patterns, or information to remember]

## Reflections
[Insights and improvements]
```

### When to Update Memory
**MANDATORY UPDATE TRIGGERS:**
- ✅ After completing ANY task from todo list
- ✅ When creating or merging a PR
- ✅ When discovering important technical details
- ✅ After fixing any bugs
- ✅ Every 30 minutes during long sessions
- ✅ BEFORE ending any conversation

**Set a mental reminder: "Did I update Memory.md in the last 30 minutes?"**

### Memory Pruning and GitHub Integration (NEW!)
Keep the memory file concise and synced with GitHub Issues:

**Automatic Pruning**:
- Removing completed tasks older than 7 days (configurable)
- Consolidating similar context items
- Archiving detailed reflections after incorporating improvements
- Keeping only the most recent 5-10 accomplishments

**GitHub Issues Integration**:
- Memory.md tasks automatically create GitHub Issues
- Bidirectional synchronization keeps both systems updated
- Issues labeled with "memory-sync", "ai-assistant"
- Completed tasks automatically close corresponding issues
- Use `/agent:memory-manager` for manual sync and maintenance

**Memory Manager CLI**:
```bash
# Initialize Memory Manager configuration
python3 .github/memory-manager/memory_manager.py init

# Check current sync status
python3 .github/memory-manager/memory_manager.py status

# Manual synchronization (dry-run first)
python3 .github/memory-manager/memory_manager.py sync --dry-run
python3 .github/memory-manager/memory_manager.py sync

# Prune old entries
python3 .github/memory-manager/memory_manager.py prune --dry-run
python3 .github/memory-manager/memory_manager.py prune
```

## Task Completion Reflection

After completing each task, reflect on:

### What Worked Well
- Successful approaches and techniques
- Effective tool usage
- Good architectural decisions

### Areas for Improvement
- What could have been done more efficiently
- Any confusion or missteps
- Missing documentation or context

### User Feedback Integration
If the user expressed frustration or provided feedback:
- Document the specific issue
- Propose improvements to documentation
- Update relevant sections to prevent recurrence
- Add new best practices based on learnings

### Continuous Improvement
- Update documentation with new patterns discovered
- Add commonly used commands
- Document project-specific conventions
- Include solutions to recurring problems

## Git Workflow Best Practices

### General Git Workflow
1. **Always fetch latest before creating branches**: `git fetch origin && git reset --hard origin/main`
2. Create feature branches from main: `feature-<issue-number>-description`
3. Make atomic commits with clear messages
4. Always create PRs for code review
5. Ensure CI/CD passes before merging

### Git Safety Instructions (CRITICAL)
**ALWAYS follow these steps to prevent accidental file deletion:**

1. **Check git status before ANY branch operations**:
   ```bash
   git status  # ALWAYS run this first
   ```

2. **Preserve uncommitted files when switching branches**:
   ```bash
   # If uncommitted files exist:
   git stash push -m "Preserving work before branch switch"
   git checkout -b new-branch
   git stash pop
   ```

3. **Verify repository context**:
   ```bash
   git remote -v  # Ensure working with correct repository
   ```

4. **Before creating new branches**:
   - Run `git status` to check for uncommitted changes
   - Commit or stash any important files
   - Verify the base branch contains all expected files

5. **If files go missing**:
   ```bash
   # Find when files existed
   git log --all --full-history -- <missing-file-path>
   # Restore from specific commit
   git checkout <commit-hash> -- <file-path>
   ```

## Using and Creating Reusable Agents

### CRITICAL: Use Agents for Workflows

**If a task involves creating issues, branches, code changes, and PRs, you MUST use an orchestration agent (like WorkflowManager) rather than executing steps manually.**

### Using Agents
To invoke a reusable agent, use the following pattern:
```
/agent:[agent-name]

Context: [Provide specific context about the problem]
Requirements: [What needs to be achieved]
```

### Common Workflow Agents (in hierarchical order)
- **orchestrator-agent**: Top-level coordinator for parallel task execution (use FIRST for multiple tasks)
- **workflow-manager**: Orchestrates individual development workflows from issue to PR
- **memory-manager**: Manages Memory.md pruning, curation, and GitHub Issues sync (NEW!)
- **code-reviewer**: Reviews pull requests (invoked by WorkflowManager in Phase 9)
- **prompt-writer**: Creates structured prompts
- **task-analyzer**: Analyzes dependencies (invoked by OrchestratorAgent)
- **worktree-manager**: Manages git worktrees (invoked by OrchestratorAgent)
- **execution-monitor**: Monitors parallel execution (invoked by OrchestratorAgent)

### Creating New Agents
New specialized agents can be added to `.github/agents/` or `.claude/agents/` following the existing template structure. Each agent should have:
- Clear specialization and purpose
- Documented approaches and methods
- Success metrics and validation criteria
- Required tools listed in frontmatter

## Git Guidelines

### Git Workflow Rules
- **Never commit directly to main**
- **Use meaningful commit messages**
- **Include co-authorship for AI-generated commits**:
  ```
  🤖 Generated with [Claude Code](https://claude.ai/code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
