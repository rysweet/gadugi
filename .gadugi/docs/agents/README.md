# Agent Catalog

Complete catalog of all Gadugi agents with descriptions, usage examples, and patterns.

## Agent Hierarchy

```
Orchestration Layer (Coordination)
├── OrchestratorAgent (Main coordinator)
├── TaskAnalyzer (Dependency analysis)
├── WorktreeManager (Environment isolation)
└── ExecutionMonitor (Progress tracking)

Implementation Layer (Development)
├── WorkflowManager (11-phase executor)
├── PromptWriter (Structured prompts)
├── TestWriter (Test generation)
├── TestSolver (Test diagnosis)
└── TypeFixAgent (Type resolution)

Review Layer (Quality)
├── CodeReviewer (PR reviews)
├── CodeReviewResponse (Feedback processing)
└── SystemDesignReviewer (Architecture review)

Maintenance Layer (Health)
├── PrBacklogManager (PR queue)
├── AgentUpdater (Version management)
├── MemoryManager (Context curation)
├── ReadmeAgent (Documentation)
└── ClaudeSettingsUpdate (Configuration)
```

## Orchestration Layer Agents

### OrchestratorAgent
**Purpose**: Coordinate parallel execution of multiple tasks

**Usage**:
```
/agent:OrchestratorAgent

Execute these specific prompts in parallel:
- implement-feature-a.md
- fix-bug-b.md
- add-tests-c.md
```

**When to use**:
- Multiple independent tasks
- Need for parallel execution
- Complex multi-step workflows

### TaskAnalyzer
**Purpose**: Analyze task dependencies and parallelization opportunities

**Usage**:
```
/agent:TaskAnalyzer

Analyze these tasks for dependencies:
- Update database schema
- Migrate existing data
- Update API endpoints
```

**When to use**:
- Before orchestrating multiple tasks
- Understanding task relationships
- Optimizing execution order

### WorktreeManager
**Purpose**: Create and manage isolated git worktree environments

**Usage**:
```
/agent:WorktreeManager

Create a new git worktree for issue #123.
Branch name: feature/issue-123-description
```

**When to use**:
- Starting work on a new issue
- Need isolated development environment
- Parallel development tasks

### ExecutionMonitor
**Purpose**: Monitor and track parallel execution progress

**Usage**:
```
/agent:ExecutionMonitor

Monitor these executing tasks:
- task-id-123 in worktree-a
- task-id-456 in worktree-b
```

**When to use**:
- Tracking parallel executions
- Monitoring long-running tasks
- Coordinating results

## Implementation Layer Agents

### WorkflowManager
**Purpose**: Execute complete 11-phase development workflows

**Usage**:
```
/agent:WorkflowManager

Implement the user authentication feature described in issue #123.
This requires adding login/logout endpoints, session management, and tests.
```

**When to use**:
- ANY task requiring code changes
- Single feature implementation
- Bug fixes with full workflow

### PromptWriter
**Purpose**: Create structured prompts for complex tasks

**Usage**:
```
/agent:PromptWriter

Create a detailed prompt for implementing a caching system with Redis.
Include requirements, acceptance criteria, and test scenarios.
```

**When to use**:
- Complex feature planning
- Creating reusable task templates
- Documenting requirements

### TestWriter
**Purpose**: Generate comprehensive test suites

**Usage**:
```
/agent:TestWriter

Write unit tests for the authentication module.
Cover login, logout, session management, and error cases.
```

**When to use**:
- Adding test coverage
- TDD approach
- Regression test creation

### TestSolver
**Purpose**: Diagnose and fix failing tests

**Usage**:
```
/agent:TestSolver

Fix the failing tests in test_auth.py.
Tests are failing with "connection refused" errors.
```

**When to use**:
- Tests failing after changes
- Debugging test issues
- Test environment problems

### TypeFixAgent
**Purpose**: Resolve type checking errors

**Usage**:
```
/agent:TypeFixAgent

Fix all pyright type errors in the auth module.
Focus on proper type annotations and generics.
```

**When to use**:
- Type checker reporting errors
- Adding type annotations
- Improving type safety

## Review Layer Agents

### CodeReviewer
**Purpose**: Perform automated code reviews on pull requests

**Usage**:
```
/agent:CodeReviewer

Review PR #123 - Authentication feature implementation
Focus on security, code quality, and test coverage.
```

**When to use**:
- After PR creation (automatic in Phase 9)
- Manual review requests
- Security audits

### CodeReviewResponse
**Purpose**: Process and implement code review feedback

**Usage**:
```
/agent:CodeReviewResponse

Address the code review feedback for PR #123.
Implement requested changes and respond to comments.
```

**When to use**:
- After receiving review feedback
- Implementing requested changes
- Resolving review discussions

### SystemDesignReviewer
**Purpose**: Review architectural changes and system design

**Usage**:
```
/agent:SystemDesignReviewer

Review the proposed microservices architecture in PR #123.
Evaluate scalability, maintainability, and design patterns.
```

**When to use**:
- Major architectural changes
- New system components
- Design pattern implementations

## Maintenance Layer Agents

### PrBacklogManager
**Purpose**: Manage PR queue and assess readiness

**Usage**:
```
/agent:PrBacklogManager

Analyze all open PRs and prioritize for review.
Check for conflicts, CI status, and review readiness.
```

**When to use**:
- Managing multiple open PRs
- Prioritizing review queue
- Identifying blocked PRs

### AgentUpdater
**Purpose**: Check for and apply agent updates

**Usage**:
```
/agent:AgentUpdater

Check for updates to all agents and apply if available.
Verify compatibility and run tests after updates.
```

**When to use**:
- Regular maintenance
- Before major releases
- Agent behavior issues

### MemoryManager
**Purpose**: Maintain Memory.md and sync with GitHub Issues

**Usage**:
```
/agent:MemoryManager

Prune old entries from Memory.md and sync with GitHub Issues.
Keep only relevant context and active tasks.
```

**When to use**:
- Memory.md getting large
- Syncing tasks with issues
- Context cleanup

### ReadmeAgent
**Purpose**: Maintain and update README documentation

**Usage**:
```
/agent:ReadmeAgent

Update README.md with new feature documentation.
Add installation instructions for the new authentication module.
```

**When to use**:
- After feature completion
- Documentation updates
- README maintenance

### ClaudeSettingsUpdate
**Purpose**: Merge and maintain Claude settings configuration

**Usage**:
```
/agent:ClaudeSettingsUpdate

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
1. /agent:WorkflowManager - Implement feature
2. /agent:TestWriter - Add tests
3. /agent:CodeReviewer - Review changes
```

### Parallel Execution
```
/agent:OrchestratorAgent

Execute in parallel:
- Feature A implementation
- Feature B implementation
- Documentation updates
```

### Review Workflow
```
1. Create PR (automatic from WorkflowManager)
2. /agent:CodeReviewer - Automated review
3. /agent:CodeReviewResponse - Address feedback
4. Merge when approved
```

### Maintenance Routine
```
/agent:MemoryManager - Clean context
/agent:AgentUpdater - Update agents
/agent:PrBacklogManager - Review PR queue
```

## Agent Selection Guide

| If you need to... | Use this agent |
|------------------|----------------|
| Execute multiple tasks | OrchestratorAgent |
| Implement a single feature | WorkflowManager |
| Fix failing tests | TestSolver |
| Review code | CodeReviewer |
| Update documentation | ReadmeAgent |
| Analyze task dependencies | TaskAnalyzer |
| Create test suite | TestWriter |
| Fix type errors | TypeFixAgent |
| Manage PRs | PrBacklogManager |
| Clean up context | MemoryManager |

## Best Practices

1. **Always use orchestrator** for multiple tasks
2. **Follow the workflow** - Don't skip phases
3. **Document changes** - Keep README current
4. **Test thoroughly** - Use TestWriter for coverage
5. **Review regularly** - Invoke CodeReviewer
6. **Maintain context** - Update Memory.md
7. **Clean up** - Remove worktrees after merge
