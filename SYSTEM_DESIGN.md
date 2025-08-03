# Gadugi Multi-Agent System Design Document

## Executive Summary

Gadugi is a multi-agent orchestration platform designed to accelerate software development through parallel task execution and intelligent workflow automation. The system enables 3-5x development speed improvements by coordinating multiple AI agents working simultaneously on independent tasks.

## System Overview

### Core Architecture Components

1. **Agent Hierarchy**
   - Program Manager: Project health maintenance and issue pipeline management
   - OrchestratorAgent: Parallel task coordinator for multiple workflows
   - WorkflowManager: Sequential workflow executor for individual tasks
   - Specialized Sub-Agents: Task-specific agents for analysis, execution, and monitoring

2. **Enhanced Separation Architecture**
   - Shared modules for code reuse across agents
   - Standardized interfaces and protocols
   - Centralized error handling and state management

3. **Container Execution Environment**
   - Secure containerized execution replacing shell commands
   - Policy-based security with resource management
   - Multi-runtime support (Python, Node.js, Shell)

4. **Memory Management System**
   - Hierarchical memory structure (project/agents/context)
   - GitHub Issues integration for task synchronization
   - Persistent state tracking across sessions

## Detailed Architecture

### 1. Agent System Architecture

#### Agent Hierarchy
```
┌─────────────────────────┐
│   Program Manager       │ ← Maintains project health
│ (Project Orchestrator)  │
└───────────┬─────────────┘
            │
            ├─── Manages → Issue Pipeline (triage, labeling)
            ├─── Updates → Project Priorities (.memory)
            ├─── Maintains → README & Documentation
            │
            └─── Coordinates with ↓

┌─────────────────────────┐
│   OrchestratorAgent     │ ← Coordinates parallel execution
│ (Parallel Coordinator)  │
└───────────┬─────────────┘
            │
            ├─── Invokes → TaskAnalyzer (dependency analysis)
            ├─── Invokes → WorktreeManager (git isolation)
            ├─── Invokes → ExecutionMonitor (parallel tracking)
            │
            └─── Spawns multiple ↓
                        
┌─────────────────────────┐
│    WorkflowManager      │ ← Executes individual workflows
│  (Workflow Executor)    │
└───────────┬─────────────┘
            │
            └─── Executes 9 workflow phases
```

#### Agent Types

1. **Orchestration Agents**
   - OrchestratorAgent: Parallel workflow coordination
   - WorkflowManager: Sequential workflow execution
   - ExecutionMonitor: Process monitoring and management
   - WorktreeManager: Git worktree isolation

2. **Analysis Agents**
   - TaskAnalyzer: Enhanced task decomposition and analysis
   - TaskBoundsEval: Task understanding evaluation
   - TaskDecomposer: Complex task breakdown
   - TaskResearchAgent: Unknown task research

3. **Development Agents**
   - CodeReviewer: PR review automation
   - CodeReviewResponse: Review feedback processing
   - TestWriter: Test creation and coverage
   - TestSolver: Test failure resolution

4. **Management Agents**
   - ProgramManager: Project health maintenance
   - PRBacklogManager: PR pipeline management
   - TeamCoach: Team optimization and performance
   - MemoryManager: Memory synchronization

### 2. Enhanced Separation Architecture

The system uses a shared module architecture to eliminate code duplication:

#### Shared Modules
- **github_operations.py**: GitHub API interactions with retry logic
- **state_management.py**: Workflow state persistence and recovery
- **error_handling.py**: Circuit breakers and retry strategies
- **task_tracking.py**: TodoWrite integration and phase tracking
- **interfaces.py**: Abstract interfaces and protocols

#### Benefits
- 70% reduction in code duplication
- Consistent error handling across agents
- Centralized state management
- Standardized GitHub operations

### 3. Container Execution Environment

#### Architecture
```
┌─────────────────────────────────────────┐
│         ExecutionEngine API             │
├─────────────────────────────────────────┤
│  SecurityPolicyEngine │ ResourceManager │
├─────────────────────────────────────────┤
│        ContainerManager (Docker)         │
├─────────────────────────────────────────┤
│  ImageManager │ AuditLogger │ Monitor   │
└─────────────────────────────────────────┘
```

#### Security Policies
- **minimal**: Development with basic isolation
- **standard**: Default balanced security
- **hardened**: Production with strict limits
- **paranoid**: Maximum security isolation

#### Features
- Container isolation for all code execution
- Resource limits (CPU, memory, disk, network)
- Audit logging with integrity verification
- Multi-runtime support

### 4. Workflow Execution Pattern

#### WorkflowManager Phases
1. **Setup Phase**: Task initialization and state recovery
2. **Issue Creation**: GitHub issue with requirements
3. **Branch Management**: Feature branch creation
4. **Research Phase**: Codebase analysis
5. **Implementation**: Code development
6. **Testing**: Test creation and validation
7. **Documentation**: Update docs and README
8. **PR Creation**: Pull request with changes
9. **Code Review**: Automated review invocation

#### Parallel Execution Flow
1. User provides multiple prompt files
2. OrchestratorAgent analyzes for dependencies
3. TaskAnalyzer evaluates complexity and decomposition needs
4. WorktreeManager creates isolated environments
5. ExecutionMonitor spawns parallel WorkflowManagers
6. Results aggregated and integrated

### 5. State Management System

#### Hierarchical State Structure
```
.github/workflow-states/
├── task-YYYYMMDD-HHMMSS-XXXX/
│   ├── state.json
│   ├── checkpoints/
│   └── backups/
└── orphaned-workflows.json
```

#### State Features
- Automatic checkpoint creation
- State validation and recovery
- Orphaned workflow detection
- Atomic state updates

### 6. Memory Management

#### Memory Hierarchy
```
.github/Memory.md          ← Main memory file
.memory/
├── project/
│   ├── context.md        ← Project context
│   └── priorities.md     ← Top priorities
└── agents/
    └── {agent_name}.md   ← Agent-specific memory
```

#### GitHub Integration
- Automatic issue creation from Memory.md tasks
- Bidirectional synchronization
- Issue lifecycle management
- Automated labeling and tracking

## Design Patterns and Principles

### 1. Dependency Injection
All agents use constructor injection for shared modules, enabling:
- Easy testing with mock dependencies
- Flexible runtime configuration
- Clear dependency boundaries

### 2. Circuit Breaker Pattern
Prevents cascading failures through:
- Failure threshold monitoring
- Automatic circuit opening
- Recovery timeout management
- Graceful degradation

### 3. Retry Strategies
Multiple backoff strategies:
- Exponential backoff for transient failures
- Linear backoff for rate limiting
- Immediate retry for network glitches
- Maximum attempt limits

### 4. Event-Driven Architecture
Agents communicate through:
- State change events
- Phase completion notifications
- Error propagation
- Performance metrics

## Performance Characteristics

### Parallel Execution
- 3-5x speed improvement for independent tasks
- Automatic load balancing
- Resource-aware scheduling
- Failure isolation

### Optimization Features
- TeamCoach performance analytics
- ML-based task classification
- Historical pattern recognition
- Continuous improvement

### Resource Management
- Container resource limits
- Memory usage monitoring
- CPU throttling
- Disk space management

## Security Architecture

### Container Security
- Process isolation
- Filesystem restrictions
- Network segmentation
- Capability dropping

### Audit System
- Comprehensive execution logs
- Tamper-evident storage
- Activity monitoring
- Compliance reporting

### Policy Framework
- Environment-specific policies
- Runtime restrictions
- Resource quotas
- Access controls

## Integration Points

### Claude Code CLI
- Agent invocation via `/agent:` commands
- Non-interactive execution mode
- JSON progress reporting
- Error handling

### GitHub API
- Issue and PR management
- Branch operations
- Repository interactions
- Rate limit handling

### File System
- State persistence
- Log storage
- Configuration files
- Temporary workspaces

## Deployment Architecture

### System Requirements
- Python 3.11+
- Docker or containerd
- Git with worktree support
- GitHub CLI (`gh`)

### Configuration
- YAML-based security policies
- Environment variables
- Agent configuration files
- Runtime parameters

## Future Enhancements

### Planned Features
1. XPIA defense implementation
2. Claude Code hooks integration
3. Enhanced ML capabilities
4. Distributed execution

### Scalability Considerations
- Horizontal scaling of agents
- Distributed state management
- Cloud-native deployment
- Kubernetes integration