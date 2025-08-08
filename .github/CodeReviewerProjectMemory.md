## Code Review Memory - 2025-01-08

### PR #224: Orchestrator Prompt Handling Improvements

#### What I Learned
- **Gadugi Architecture**: Multi-agent orchestration system with parallel execution capabilities
- **ExecutionEngine Component**: Manages parallel task execution with both containerized and subprocess fallback modes
- **Agent Invocation Pattern**: System previously designed to use `/agent:workflow-manager` instead of generic `-p` prompts
- **CLI Length Limitations**: Claude CLI has command-line argument length limits that cause failures with large prompts
- **Test-Driven Architecture**: Comprehensive test suite exists with regression prevention tests
- **Worktree Management**: System uses git worktrees for isolated task execution environments

#### Patterns to Watch
- **Agent vs Generic Invocation**: Architectural tension between agent-specific invocation and generic prompt handling
- **CLI Command Construction**: Need to balance agent architecture with practical CLI limitations
- **Test Regression Risk**: Changes to command patterns can break existing test expectations
- **File-based vs In-memory**: Trade-offs between passing content directly vs. file references
- **Container vs Subprocess**: Dual execution modes requiring consistent command patterns

#### Critical Design Decisions Observed
- **WorkflowManager Integration**: System specifically designed around WorkflowManager agents for task execution
- **Resource Management**: Sophisticated resource monitoring and concurrency control
- **Prompt Generation**: Dynamic prompt creation with context-aware WorkflowManager instructions
- **State Management**: Worktree-based isolation with proper cleanup and resource tracking

#### Security Considerations Noted
- **Path Validation**: File path handling needs validation to prevent traversal attacks
- **Resource Limits**: Comprehensive resource monitoring prevents system overload
- **Process Isolation**: Both containerized and subprocess modes with proper isolation
- **Cleanup Management**: Important to clean up temporary files and worktrees

#### Architecture Quality Assessment
- **Strength**: Well-architected with clear separation of concerns
- **Strength**: Comprehensive error handling and fallback mechanisms
- **Strength**: Extensive test coverage with regression prevention
- **Concern**: CLI limitations forcing architectural compromises
- **Concern**: Complexity in maintaining dual execution modes
EOF < /dev/null
