# Common Workflows

This guide covers typical development workflows using Gadugi agents.

## Single Task Execution

### Basic Feature Implementation

```bash
# 1. Create an issue
gh issue create --title "Add user profile page" --body "Create a profile page with user details"

# 2. Execute the workflow
/agent:workflow-manager

Implement the user profile page feature for issue #123.
Create the page component, add routing, include user details display, and write tests.
```

The workflow-manager will:
1. Create a feature branch
2. Set up isolated worktree
3. Research existing code
4. Implement the feature
5. Run tests
6. Create PR
7. Invoke code review

### Bug Fix Workflow

```bash
# Quick bug fix
/agent:workflow-manager

Fix the null pointer exception in the user service (issue #456).
The error occurs when user.email is undefined. Add proper null checking.
```

## Parallel Task Orchestration

### Multiple Independent Features

```bash
/agent:orchestrator-agent

Execute these tasks in parallel:
- Implement user profile page (issue #123)
- Add email notifications (issue #124)
- Update API documentation (issue #125)
```

The orchestrator will:
- Analyze task dependencies
- Create separate worktrees
- Execute tasks in parallel
- Monitor progress
- Coordinate PR creation

### Batch Testing Updates

```bash
/agent:orchestrator-agent

Add comprehensive tests for these modules:
- Authentication module
- User service
- API endpoints
```

## Code Review Workflow

### Automated Review Process

After any PR is created, the system automatically:

1. **Waits 30 seconds** for PR to propagate
2. **Invokes code-reviewer** (Phase 9)
3. **Posts review comments**

### Manual Review Request

```bash
/agent:code-reviewer

Review PR #789 for security vulnerabilities and code quality.
Pay special attention to SQL injection risks and input validation.
```

### Responding to Review Feedback

```bash
/agent:code-review-response

Address the review feedback for PR #789:
- Add input validation as requested
- Improve error handling
- Add missing tests
```

## Emergency Procedures

### Hotfix Workflow

For critical production issues:

```bash
# 1. Document emergency
gh issue create --title "EMERGENCY: Database connection failing" --label "emergency"

# 2. Create hotfix branch
git checkout -b hotfix/emergency-db-fix

# 3. Make minimal fix
# ... edit files ...

# 4. Commit with emergency flag
git commit -m "EMERGENCY: Fix database connection timeout

Emergency hotfix bypassing normal workflow.
Production system was down.

Fixes: #999"

# 5. Push and create PR
git push origin hotfix/emergency-db-fix
gh pr create --title "EMERGENCY: Fix database connection" --label "emergency"

# 6. After merge, create follow-up
gh issue create --title "Follow-up: Add tests for emergency DB fix"
```

### Recovery from Failed Workflow

If a workflow fails mid-execution:

```bash
# 1. Check worktree state
git worktree list
cd .worktrees/[failed-task]/

# 2. Check current status
git status
git log --oneline -5

# 3. Resume or restart
/agent:workflow-manager

Resume the failed task in worktree .worktrees/[failed-task].
Continue from implementation phase, tests are still needed.
```

## Testing Workflows

### Adding Test Coverage

```bash
/agent:test-writer

Write comprehensive tests for the authentication module.
Include:
- Unit tests for all methods
- Integration tests for login flow
- Edge cases and error conditions
- Performance tests for concurrent logins
```

### Fixing Failing Tests

```bash
/agent:test-solver

Fix the failing tests in test_user_service.py.
Error: "Cannot read property 'id' of undefined"
This started after the recent refactoring.
```

## Documentation Workflows

### Updating README

```bash
/agent:readme-agent

Update README.md with:
- New authentication feature documentation
- Updated installation instructions
- API changes for v2.0
- Example code for new features
```

### Creating Technical Docs

```bash
/agent:prompt-writer

Create comprehensive documentation for the new caching system.
Include architecture decisions, configuration options, and usage examples.
```

## Maintenance Workflows

### Regular Maintenance Routine

```bash
# Weekly maintenance
/agent:memory-manager
Clean up Memory.md and sync with GitHub issues

/agent:agent-updater
Check for and apply agent updates

/agent:pr-backlog-manager
Review and prioritize open PRs
```

### Worktree Cleanup

```bash
# List all worktrees
git worktree list

# Remove merged worktrees
git worktree remove .worktrees/completed-task/
git worktree prune
```

## Advanced Workflows

### Feature with Dependencies

```bash
/agent:task-analyzer

Analyze dependencies for:
1. Update database schema
2. Migrate existing data
3. Update API to use new schema
4. Update frontend to handle new fields

Then execute in correct order.
```

### Refactoring Workflow

```bash
/agent:workflow-manager

Refactor the user service to use dependency injection.
- Extract interfaces
- Implement dependency injection
- Update all consumers
- Maintain backward compatibility
- Comprehensive testing
```

### Performance Optimization

```bash
/agent:orchestrator-agent

Optimize application performance:
- Profile and identify bottlenecks
- Optimize database queries
- Add caching layer
- Implement lazy loading
- Add performance tests
```

## Workflow Patterns

### TDD Pattern
1. Write tests first (`test-writer`)
2. Implement feature (`workflow-manager`)
3. Refactor if needed
4. Review (`code-reviewer`)

### Documentation-First Pattern
1. Write documentation (`prompt-writer`)
2. Get approval on design
3. Implement (`workflow-manager`)
4. Update docs (`readme-agent`)

### Parallel Development Pattern
1. Analyze dependencies (`task-analyzer`)
2. Orchestrate parallel work (`orchestrator-agent`)
3. Monitor progress (`execution-monitor`)
4. Integrate results

## Best Practices

1. **Always create issues first** - Provides tracking and context
2. **Use appropriate agents** - Don't use orchestrator for single tasks
3. **Let workflow complete** - Don't interrupt the 11 phases
4. **Review regularly** - Check PRs promptly
5. **Clean up worktrees** - Remove after PR merge
6. **Update documentation** - Keep README current
7. **Monitor Memory.md** - Maintain context

## Common Commands Quick Reference

```bash
# Create issue
gh issue create --title "Title" --body "Description"

# List issues
gh issue list --assignee @me

# Create PR
gh pr create --title "Title" --body "Description"

# List PRs
gh pr list --state open

# Check PR status
gh pr checks

# List worktrees
git worktree list

# Remove worktree
git worktree remove .worktrees/[name]/
```
