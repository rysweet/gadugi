# Gadugi Architecture

## System Overview

Gadugi is a multi-agent system designed for AI-assisted software development. It leverages Claude Code's capabilities through specialized agents that work together to automate development workflows.

## Core Principles

### 1. Agent Specialization
Each agent has a specific role and expertise, following the Unix philosophy of "do one thing well."

### 2. Workflow Orchestration
Complex tasks are broken down and coordinated through a sophisticated orchestration layer.

### 3. Isolation and Safety
All development work happens in isolated git worktrees, preventing conflicts and maintaining clean history.

### 4. Quality Gates
Mandatory testing and review phases ensure code quality before merging.

## Multi-Agent Architecture

### Layer 1: Orchestration Layer

**Purpose**: Coordinate and manage parallel execution of tasks

- **orchestrator-agent**: Main coordinator for parallel task execution
- **task-analyzer**: Analyzes task dependencies and parallelization opportunities
- **worktree-manager**: Creates and manages isolated git environments
- **execution-monitor**: Tracks progress of parallel executions

### Layer 2: Implementation Layer

**Purpose**: Execute actual development work

- **workflow-manager**: Executes complete 11-phase development workflows
- **prompt-writer**: Creates structured prompts for complex tasks
- **test-writer**: Generates comprehensive test suites
- **test-solver**: Diagnoses and fixes failing tests
- **type-fix-agent**: Resolves type checking errors

### Layer 3: Review Layer

**Purpose**: Ensure code quality and architectural compliance

- **code-reviewer**: Performs automated code reviews on PRs
- **code-review-response**: Processes and implements review feedback
- **system-design-reviewer**: Reviews architectural changes

### Layer 4: Maintenance Layer

**Purpose**: Maintain project health and documentation

- **pr-backlog-manager**: Manages PR queue and readiness
- **agent-updater**: Keeps agents updated to latest versions
- **memory-manager**: Maintains context and syncs with GitHub Issues
- **readme-agent**: Keeps README documentation current
- **claude-settings-update**: Manages configuration synchronization

## 11-Phase Workflow Process

Every task follows a mandatory 11-phase workflow:

### Phase 1: Initial Setup
- Environment validation
- Dependency checking
- Task initialization

### Phase 2: Issue Creation
- GitHub issue generation
- Milestone assignment
- Label application

### Phase 3: Branch Management
- Feature branch creation
- Git worktree setup
- Environment isolation

### Phase 4: Research & Planning
- Codebase analysis
- Dependency identification
- Implementation strategy

### Phase 5: Implementation
- Code changes
- Feature development
- Bug fixes

### Phase 6: Testing (Quality Gate)
- Unit test execution
- Linting and formatting
- Pre-commit hooks
- **Must pass to continue**

### Phase 7: Documentation
- Code comments
- API documentation
- README updates

### Phase 8: Pull Request
- PR creation
- Detailed description
- Issue linking

### Phase 9: Review (Mandatory)
- Automated code review
- **Always invoked after 30-second delay**
- Quality assessment

### Phase 10: Review Response
- Feedback processing
- Change implementation
- Review resolution

### Phase 11: Settings Update
- Configuration synchronization
- Settings merger
- State cleanup

## Worktree Isolation Model

### Purpose
Provide complete isolation for parallel development:

```
main repository/
├── .worktrees/
│   ├── issue-123/     # Isolated environment
│   ├── issue-456/     # Another isolated task
│   └── task-abc/      # Parallel execution
```

### Benefits
- No merge conflicts during development
- Clean git history
- Parallel execution safety
- Easy rollback and cleanup

## Communication Patterns

### Agent Invocation
```
/agent:[agent-name]

Task description and requirements
```

### Inter-Agent Communication
- Agents communicate through shared state files
- Task metadata stored in `.task/` directories
- Results passed through structured outputs

### State Management
- WorkflowStateManager tracks progress
- CheckpointManager enables recovery
- Memory.md provides persistent context

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **Package Manager**: UV
- **Version Control**: Git with worktrees
- **CI/CD**: GitHub Actions
- **Testing**: pytest
- **Linting**: ruff
- **Type Checking**: pyright/mypy

### Claude Code Integration
- Native tool usage (Read, Write, Edit, Bash, etc.)
- Task delegation for parallel execution
- Memory management for context persistence

## Security Considerations

### Code Isolation
- All changes in isolated worktrees
- No direct main branch modifications
- Mandatory PR workflow

### Quality Enforcement
- Pre-commit hooks
- Automated testing
- Code review requirements
- Type checking

### Access Control
- GitHub authentication required
- Claude settings control tool access
- Emergency procedures for critical issues

## Performance Characteristics

### Parallel Execution
- Multiple tasks execute simultaneously
- Independent worktrees prevent conflicts
- Orchestrator manages resource allocation

### Scalability
- Horizontal scaling through parallel agents
- Efficient state management
- Minimal overhead for coordination

## Extension Points

### Adding New Agents
1. Create agent specification in `.claude/agents/`
2. Define tools and capabilities
3. Implement workflow integration
4. Add to appropriate layer

### Custom Workflows
- Extend WorkflowManager phases
- Add domain-specific quality gates
- Integrate with external systems

## Best Practices

### Development
- Always use orchestrator for multiple tasks
- Follow the 11-phase workflow
- Maintain comprehensive tests
- Document all changes

### Operations
- Regular worktree cleanup
- Monitor resource usage
- Keep agents updated
- Review Memory.md regularly

## Future Enhancements

### Planned Features
- Distributed execution across multiple machines
- Advanced dependency analysis
- Machine learning for task optimization
- Enhanced monitoring and observability

### Research Areas
- Agent learning and adaptation
- Automated architecture decisions
- Self-healing workflows
- Performance optimization
