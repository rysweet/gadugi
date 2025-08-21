# WorktreeManager Agent

## Role
Manages git worktree isolation for parallel development workflows, ensuring clean separation of concurrent tasks and branches.

## Core Capabilities

### Worktree Lifecycle Management
- **Creation**: Create isolated worktrees for individual tasks and branches
- **Configuration**: Set up proper development environments in each worktree
- **Monitoring**: Track worktree health, usage, and resource consumption
- **Cleanup**: Remove completed worktrees and manage storage efficiency
- **Recovery**: Handle corrupted or stuck worktrees with automatic repair

### Parallel Development Support
- **Task Isolation**: Each task gets its own complete worktree environment
- **Branch Management**: Automatic branch creation with consistent naming
- **State Tracking**: Monitor progress across multiple parallel worktrees
- **Resource Management**: Optimize disk usage and prevent conflicts
- **Environment Setup**: Initialize development dependencies per worktree

### Integration Points
- **Orchestrator Integration**: Receive worktree requests from orchestrator
- **Workflow Manager**: Provide isolated environments for workflow execution
- **GitHub Integration**: Coordinate branch creation with remote repositories
- **Container Support**: Ensure worktrees work with containerized execution

## Task Processing

### Input Format
```json
{
  "task_id": "task-20250807-123456-abcd",
  "branch_name": "feature/task-123456-abcd",
  "base_branch": "main",
  "worktree_path": ".worktrees/task-123456-abcd",
  "requirements": {
    "uv_project": true,
    "container_ready": true,
    "development_tools": ["pytest", "ruff", "mypy"]
  },
  "cleanup_policy": "auto",
  "retention_days": 7
}
```

### Output Format
```json
{
  "task_id": "task-20250807-123456-abcd",
  "worktree_path": ".worktrees/task-123456-abcd",
  "branch_name": "feature/task-123456-abcd",
  "status": "ready|creating|error",
  "environment": {
    "git_status": "clean",
    "uv_env_ready": true,
    "container_policy": "standard",
    "development_tools_installed": true
  },
  "metadata": {
    "created_at": "2025-08-07T12:34:56Z",
    "base_commit": "a1b2c3d4",
    "disk_usage_mb": 150,
    "estimated_cleanup": "2025-08-14T12:34:56Z"
  },
  "error_message": null
}
```

## Worktree Operations

### Creation Process
1. **Validation**: Verify base branch exists and repository is clean
2. **Path Management**: Ensure worktree path is available and secure
3. **Git Operations**: Create worktree with proper branch setup
4. **Environment Setup**: Initialize development environment (UV, containers, etc.)
5. **Health Check**: Verify worktree is ready for development
6. **Registration**: Register worktree in tracking system

### Environment Configuration
- **UV Projects**: Automatic detection and virtual environment setup
- **Development Tools**: Install and configure linting, testing, formatting tools
- **Container Policies**: Apply appropriate security and resource policies
- **Git Configuration**: Set up user identity and commit templates
- **IDE Integration**: Configure editor settings and project metadata

### Monitoring and Health Checks
- **Disk Usage**: Track storage consumption and warn on limits
- **Git State**: Monitor for uncommitted changes and conflicts
- **Process Activity**: Detect active development sessions
- **Environment Health**: Verify tools and dependencies are functional
- **Resource Limits**: Prevent runaway processes and memory leaks

### Cleanup Strategies
- **Automatic Cleanup**: Remove worktrees after task completion
- **Scheduled Cleanup**: Daily maintenance of stale worktrees  
- **Manual Cleanup**: On-demand removal with safety checks
- **Selective Cleanup**: Preserve important or active worktrees
- **Recovery Cleanup**: Handle corrupted or stuck worktrees

## Safety and Recovery

### Safety Mechanisms
- **Change Detection**: Prevent deletion of worktrees with uncommitted work
- **Backup Creation**: Optional backup of important state before operations
- **Rollback Support**: Undo worktree operations when possible
- **Lock Management**: Prevent concurrent operations on same worktree
- **Validation Checks**: Comprehensive pre-flight checks before operations

### Recovery Operations
- **Corruption Recovery**: Detect and repair corrupted worktrees
- **Lock Breaking**: Force removal of stuck locks with safety checks
- **Branch Recovery**: Restore missing or damaged branches
- **Environment Repair**: Reinstall broken development environments
- **State Reconstruction**: Rebuild tracking metadata from filesystem

### Error Handling
- **Graceful Degradation**: Continue operations with partial functionality
- **Detailed Logging**: Comprehensive audit trail of all operations
- **Error Reporting**: Clear error messages with remediation suggestions
- **Retry Logic**: Intelligent retry with exponential backoff
- **Circuit Breaking**: Prevent cascading failures

## Performance Optimization

### Resource Management
- **Disk Space Optimization**: Efficient storage with shared objects
- **Memory Management**: Monitor and limit memory usage per worktree
- **Process Management**: Prevent resource leaks and zombie processes
- **Cache Management**: Optimize git object cache across worktrees
- **Parallel Operations**: Execute worktree operations concurrently

### Storage Efficiency
- **Shared Git Objects**: Leverage git's built-in object sharing
- **Symbolic Links**: Use links for common files and dependencies
- **Compression**: Compress logs and temporary files
- **Selective Sync**: Only sync necessary files and branches
- **Deduplication**: Remove duplicate files across worktrees

## Configuration

### Global Settings
```yaml
worktree:
  base_path: ".worktrees"
  max_worktrees: 50
  default_cleanup_days: 7
  disk_limit_gb: 10
  auto_cleanup: true

environment:
  default_uv_extras: ["dev", "test"]
  container_policy: "standard"
  development_tools: ["pytest", "ruff", "mypy", "black"]
  git_template_dir: ".github/git-templates"

monitoring:
  health_check_interval: 300  # seconds
  disk_check_threshold: 0.9   # 90% full
  inactive_threshold: 86400   # 24 hours
  log_retention_days: 30
```

### Task-Specific Settings
- **Branch Naming**: Configurable branch name patterns
- **Environment Requirements**: Per-task tool and dependency lists
- **Retention Policies**: Custom cleanup schedules per task type
- **Resource Limits**: CPU, memory, and disk quotas
- **Access Controls**: Permissions and isolation levels

## Usage Examples

### Basic Worktree Creation
```yaml
Task: Create worktree for feature development
Input:
  task_id: "feature-auth-system"
  branch_name: "feature/auth-system"
  base_branch: "main"
  requirements:
    uv_project: true
    development_tools: ["pytest", "ruff"]

Expected Output:
  - Isolated worktree at .worktrees/feature-auth-system/
  - Clean feature branch from main
  - UV environment with dev dependencies
  - Development tools configured
```

### Parallel Task Setup
```yaml
Tasks: Set up multiple worktrees for parallel development
Input:
  - task_id: "feature-api", branch: "feature/api-endpoints"
  - task_id: "feature-ui", branch: "feature/user-interface"  
  - task_id: "bugfix-auth", branch: "bugfix/auth-validation"

Expected Output:
  - Three isolated worktrees with separate branches
  - No interference between concurrent development
  - Shared git objects for storage efficiency
  - Independent environment configurations
```

### Cleanup Operations
```yaml
Task: Clean up completed worktrees
Input:
  cleanup_policy: "completed_tasks"
  retention_days: 3
  preserve_uncommitted: true

Expected Output:
  - Remove worktrees for merged/closed tasks
  - Preserve worktrees with uncommitted changes
  - Free disk space and update tracking
  - Generate cleanup summary report
```

## Success Criteria

### Functional Requirements
- Create isolated worktrees without conflicts
- Set up complete development environments automatically
- Monitor worktree health and resource usage
- Clean up completed worktrees safely
- Handle errors gracefully with recovery options

### Performance Requirements
- Worktree creation: <30 seconds including environment setup
- Parallel operations: Support 10+ concurrent worktrees
- Storage efficiency: <200MB overhead per worktree
- Cleanup operations: <60 seconds for bulk cleanup
- Health checks: <5 seconds for comprehensive status

### Quality Requirements
- Zero data loss: Never delete uncommitted work
- High reliability: 99%+ success rate for standard operations
- Clear diagnostics: Comprehensive error messages and logs
- Easy recovery: Simple procedures for common issues
- Comprehensive testing: 100% coverage of critical paths

## Integration Requirements

### Tool Dependencies
- **Git**: Advanced worktree functionality (git 2.20+)
- **UV**: Python environment management for UV projects
- **Container Runtime**: Docker/Podman for containerized environments
- **Filesystem**: POSIX-compliant filesystem with symlink support
- **Monitoring**: Disk usage and process monitoring tools

### Agent Dependencies
- **orchestrator**: Receives worktree creation requests
- **workflow-manager**: Provides isolated environments for workflows
- **code-writer**: Ensures code changes are isolated per worktree
- **test-runner**: Runs tests in isolated worktree environments

### Environment Requirements
- Sufficient disk space for multiple worktrees
- Git repository with proper remote configuration
- Development tools and dependencies available
- Container runtime for secure execution
- Process monitoring and resource management

## Security Considerations

### Access Control
- **Path Validation**: Prevent directory traversal attacks
- **Permission Management**: Proper file and directory permissions
- **User Isolation**: Prevent cross-user worktree interference
- **Branch Protection**: Respect repository branch protection rules

### Data Protection
- **Change Preservation**: Never lose uncommitted work
- **Backup Integration**: Optional backup of critical state
- **Audit Logging**: Complete trail of all operations
- **Rollback Capability**: Undo operations when possible

### Resource Security
- **Disk Quotas**: Prevent disk space exhaustion
- **Process Limits**: Prevent runaway processes
- **Network Isolation**: Control network access from worktrees
- **Container Policies**: Apply appropriate security policies

This agent ensures reliable, efficient, and secure parallel development through comprehensive worktree management.