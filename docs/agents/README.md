# Agent Catalog

Complete catalog of all Gadugi agents with descriptions, usage examples, and patterns.

## Agent Hierarchy

```
Orchestration Layer (Coordination)
├── orchestrator-agent (Main coordinator)
├── task-analyzer (Dependency analysis)
├── worktree-manager (Environment isolation)
└── execution-monitor (Progress tracking)

Implementation Layer (Development)
├── workflow-manager (11-phase executor)
├── prompt-writer (Structured prompts)
├── test-writer (Test generation)
├── test-solver (Test diagnosis)
└── type-fix-agent (Type resolution)

Review Layer (Quality)
├── code-reviewer (PR reviews)
├── code-review-response (Feedback processing)
└── system-design-reviewer (Architecture review)

Maintenance Layer (Health)
├── pr-backlog-manager (PR queue)
├── agent-updater (Version management)
├── memory-manager (Context curation)
├── readme-agent (Documentation)
└── claude-settings-update (Configuration)
```

## Orchestration Layer Agents

### orchestrator-agent
**Purpose**: Coordinate parallel execution of multiple tasks

**Usage**:
```
/agent:orchestrator-agent

Execute these specific prompts in parallel:
- implement-feature-a.md
- fix-bug-b.md
- add-tests-c.md
```

**When to use**:
- Multiple independent tasks
- Need for parallel execution
- Complex multi-step workflows

### task-analyzer
**Purpose**: Analyze task dependencies and parallelization opportunities

**Usage**:
```
/agent:task-analyzer

Analyze these tasks for dependencies:
- Update database schema
- Migrate existing data
- Update API endpoints
```

**When to use**:
- Before orchestrating multiple tasks
- Understanding task relationships
- Optimizing execution order

### worktree-manager
**Purpose**: Create and manage isolated git worktree environments

**Usage**:
```
/agent:worktree-manager

Create a new git worktree for issue #123.
Branch name: feature/issue-123-description
```

**When to use**:
- Starting work on a new issue
- Need isolated development environment
- Parallel development tasks

### execution-monitor
**Purpose**: Monitor and track parallel execution progress

**Usage**:
```
/agent:execution-monitor

Monitor these executing tasks:
- task-id-123 in worktree-a
- task-id-456 in worktree-b
```

**When to use**:
- Tracking parallel executions
- Monitoring long-running tasks
- Coordinating results

## Implementation Layer Agents

### workflow-manager
**Purpose**: Execute complete 11-phase development workflows

**Usage**:
```
/agent:workflow-manager

Implement the user authentication feature described in issue #123.
This requires adding login/logout endpoints, session management, and tests.
```

**When to use**:
- ANY task requiring code changes
- Single feature implementation
- Bug fixes with full workflow

### prompt-writer
**Purpose**: Create structured prompts for complex tasks

**Usage**:
```
/agent:prompt-writer

Create a detailed prompt for implementing a caching system with Redis.
Include requirements, acceptance criteria, and test scenarios.
```

**When to use**:
- Complex feature planning
- Creating reusable task templates
- Documenting requirements

### test-writer
**Purpose**: Generate comprehensive test suites

**Usage**:
```
/agent:test-writer

Write unit tests for the authentication module.
Cover login, logout, session management, and error cases.
```

**When to use**:
- Adding test coverage
- TDD approach
- Regression test creation

### test-solver
**Purpose**: Diagnose and fix failing tests

**Usage**:
```
/agent:test-solver

Fix the failing tests in test_auth.py.
Tests are failing with "connection refused" errors.
```

**When to use**:
- Tests failing after changes
- Debugging test issues
- Test environment problems

### type-fix-agent
**Purpose**: Resolve type checking errors

**Usage**:
```
/agent:type-fix-agent

Fix all pyright type errors in the auth module.
Focus on proper type annotations and generics.
```

**When to use**:
- Type checker reporting errors
- Adding type annotations
- Improving type safety

## Review Layer Agents

### code-reviewer
**Purpose**: Perform automated code reviews on pull requests

**Usage**:
```
/agent:code-reviewer

Review PR #123 - Authentication feature implementation
Focus on security, code quality, and test coverage.
```

**When to use**:
- After PR creation (automatic in Phase 9)
- Manual review requests
- Security audits

### code-review-response
**Purpose**: Process and implement code review feedback

**Usage**:
```
/agent:code-review-response

Address the code review feedback for PR #123.
Implement requested changes and respond to comments.
```

**When to use**:
- After receiving review feedback
- Implementing requested changes
- Resolving review discussions

### system-design-reviewer
**Purpose**: Review architectural changes and system design

**Usage**:
```
/agent:system-design-reviewer

Review the proposed microservices architecture in PR #123.
Evaluate scalability, maintainability, and design patterns.
```

**When to use**:
- Major architectural changes
- New system components
- Design pattern implementations

## Maintenance Layer Agents

### pr-backlog-manager
**Purpose**: Manage PR queue and assess readiness

**Usage**:
```
/agent:pr-backlog-manager

Analyze all open PRs and prioritize for review.
Check for conflicts, CI status, and review readiness.
```

**When to use**:
- Managing multiple open PRs
- Prioritizing review queue
- Identifying blocked PRs

### agent-updater
**Purpose**: Check for and apply agent updates

**Usage**:
```
/agent:agent-updater

Check for updates to all agents and apply if available.
Verify compatibility and run tests after updates.
```

**When to use**:
- Regular maintenance
- Before major releases
- Agent behavior issues

### memory-manager
**Purpose**: Maintain Memory.md and sync with GitHub Issues

**Usage**:
```
/agent:memory-manager

Prune old entries from Memory.md and sync with GitHub Issues.
Keep only relevant context and active tasks.
```

**When to use**:
- Memory.md getting large
- Syncing tasks with issues
- Context cleanup

### readme-agent
**Purpose**: Maintain and update README documentation

**Usage**:
```
/agent:readme-agent

Update README.md with new feature documentation.
Add installation instructions for the new authentication module.
```

**When to use**:
- After feature completion
- Documentation updates
- README maintenance

### claude-settings-update
**Purpose**: Merge and maintain Claude settings configuration

**Usage**:
```
/agent:claude-settings-update

Merge settings.local.json into settings.json.
Maintain alphabetical sorting of allow-lists.
```

**When to use**:
- Settings conflicts
- Configuration updates
- Tool permission changes

## Common Agent Patterns

### Sequential Execution
```
1. /agent:workflow-manager - Implement feature
2. /agent:test-writer - Add tests
3. /agent:code-reviewer - Review changes
```

### Parallel Execution
```
/agent:orchestrator-agent

Execute in parallel:
- Feature A implementation
- Feature B implementation
- Documentation updates
```

### Review Workflow
```
1. Create PR (automatic from workflow-manager)
2. /agent:code-reviewer - Automated review
3. /agent:code-review-response - Address feedback
4. Merge when approved
```

### Maintenance Routine
```
/agent:memory-manager - Clean context
/agent:agent-updater - Update agents
/agent:pr-backlog-manager - Review PR queue
```

## Agent Selection Guide

| If you need to... | Use this agent |
|------------------|----------------|
| Execute multiple tasks | orchestrator-agent |
| Implement a single feature | workflow-manager |
| Fix failing tests | test-solver |
| Review code | code-reviewer |
| Update documentation | readme-agent |
| Analyze task dependencies | task-analyzer |
| Create test suite | test-writer |
| Fix type errors | type-fix-agent |
| Manage PRs | pr-backlog-manager |
| Clean up context | memory-manager |

## Best Practices

1. **Always use orchestrator** for multiple tasks
2. **Follow the workflow** - Don't skip phases
3. **Document changes** - Keep README current
4. **Test thoroughly** - Use test-writer for coverage
5. **Review regularly** - Invoke code-reviewer
6. **Maintain context** - Update Memory.md
7. **Clean up** - Remove worktrees after merge
