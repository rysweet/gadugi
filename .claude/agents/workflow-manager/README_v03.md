# Workflow Manager Agent v0.3


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview

The Workflow Manager Agent v0.3 is a production-ready, memory-aware agent that inherits from the V03Agent base class. It provides comprehensive workflow management capabilities with learning, error recovery, and collaboration features.

## Key Features

### 🧠 Memory Integration
- **Persistent memory** across sessions using the V03Agent base class
- **Learning from similar workflows** to improve future execution
- **Knowledge base loading** from markdown files in the knowledge/ directory
- **Experience-based optimization** and pattern recognition

### 🔄 13-Phase Workflow Execution
1. **Requirements Analysis** - Parse and understand task requirements
2. **Design Planning** - Create architectural approach
3. **Task Decomposition** - Break down into manageable subtasks
4. **Environment Setup** - Prepare development environment and branches
5. **Implementation** - Core development work
6. **Testing** - Comprehensive test execution
7. **Code Review Prep** - Prepare code for review (linting, formatting)
8. **Quality Gates** - Type checking, security scans, coverage validation
9. **Documentation** - Update documentation as needed
10. **PR Creation** - Create pull request with comprehensive description
11. **CI/CD Validation** - Monitor and validate pipeline execution
12. **Review Response** - Handle and learn from PR review feedback
13. **Merge & Cleanup** - Final merge and branch cleanup

### 🛡️ Production-Ready Error Handling
- **Phase-level error recovery** with checkpoint system
- **Pattern recognition** for common error types
- **Automated recovery strategies** for known issues
- **Comprehensive logging** with structured output
- **Graceful failure handling** with detailed error reporting

### 📚 Knowledge Base Integration
The agent automatically loads knowledge from markdown files:

- **`workflow_phases.md`** - Detailed 13-phase workflow documentation
- **`pr_best_practices.md`** - Pull request creation and management best practices
- **`git_workflow.md`** - Comprehensive Git workflow and best practices
- **`error_patterns.md`** - Common workflow errors and recovery solutions
- **`ci_cd_patterns.md`** - CI/CD pipeline patterns and best practices

### 🎯 PR Review Feedback Learning
- **Feedback processing** - Analyze and categorize PR review comments
- **Pattern extraction** - Learn common feedback patterns
- **Proactive recommendations** - Suggest improvements based on past feedback
- **Continuous improvement** - Adapt workflow based on review insights

## Installation and Setup

### Prerequisites
- Python 3.9+
- UV package manager (for UV projects) or pip
- Git
- Memory system (MCP service running on localhost:8000)

### Basic Usage

```python
import asyncio
from workflow_manager_v03 import WorkflowManagerV03

async def main():
    # Create and initialize agent
    agent = WorkflowManagerV03("my_workflow_manager")

    try:
        # Initialize with memory system
        await agent.initialize()

        # Start a workflow task
        task_id = await agent.start_task("Implement user authentication feature")

        # Execute the workflow
        outcome = await agent.execute_task({
            'task_id': task_id,
            'description': 'Implement user authentication feature',
            'repository_path': '/path/to/repo',
            'target_branch': 'main',
            'success_criteria': ['Users can log in securely'],
            'constraints': ['Must use JWT tokens']
        })

        # Learn from the outcome
        await agent.learn_from_outcome(outcome)

        print(f"Workflow completed: {'SUCCESS' if outcome.success else 'FAILED'}")

    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

### Memory-Aware Execution
The agent automatically:
- Searches for similar past workflows
- Applies learned patterns and best practices
- Avoids previously encountered errors
- Stores new experiences for future use

### Collaborative Decision Making
- Writes decisions and progress to shared whiteboard
- Shares expertise with other agents
- Collaborates through the memory system

### Error Recovery and Checkpoints
- Saves state after each successful phase
- Can resume from checkpoints after failures
- Implements recovery strategies for common errors
- Learns from error patterns for future prevention

### PR Review Integration
```python
# Process PR review feedback
feedback = [
    PRReviewFeedback(
        reviewer="senior_dev",
        comment="Please add error handling",
        severity="major"
    )
]

analysis = await agent.process_pr_feedback(feedback)
recommendations = await agent.get_proactive_recommendations("Add API endpoint")
```

## Configuration

### Environment Variables
- `WORKFLOW_LOG_LEVEL` - Set logging level (default: INFO)
- `MCP_BASE_URL` - Memory system URL (default: http://localhost:8000)
- `WORKFLOW_MAX_RETRIES` - Maximum retry attempts per phase (default: 3)

### Agent Capabilities
The agent is configured with these capabilities:
- **Parallelization**: Up to 5 parallel tasks
- **PR Creation**: Full GitHub integration
- **Code Writing**: Can coordinate with code writers
- **Code Review**: Can perform code review
- **Testing**: Comprehensive test execution
- **Documentation**: Can update documentation

## Testing

Run the test suite to verify functionality:

```bash
cd .claude/agents/WorkflowManager
python test_workflow_manager_v03.py
```

The test suite validates:
- Basic agent functionality
- Workflow phase execution
- Helper method operations
- Error pattern detection
- PR feedback processing

## Knowledge Base

The agent's knowledge base includes:

### Git Workflow (`git_workflow.md`)
- Branch management and naming conventions
- Commit message standards
- Worktree management
- Conflict resolution strategies
- Advanced Git techniques

### Error Patterns (`error_patterns.md`)
- Common workflow errors and solutions
- Recovery patterns and strategies
- Prevention techniques
- Automated error detection

### CI/CD Patterns (`ci_cd_patterns.md`)
- Pipeline architecture best practices
- Testing strategies and patterns
- Deployment patterns (blue-green, canary, rolling)
- Security and monitoring integration

## Architecture

### Class Hierarchy
```
V03Agent (base class)
├── Memory integration
├── Knowledge base loading
├── Learning capabilities
└── Collaboration features
    │
    └── WorkflowManagerV03
        ├── 13-phase workflow execution
        ├── Error recovery and checkpoints
        ├── PR review feedback learning
        └── Production error handling
```

### Key Components
- **WorkflowPhase** - Enumeration of 13 workflow phases
- **WorkflowContext** - State management for workflow execution
- **PRReviewFeedback** - Structure for PR review data
- **Error pattern detection** - Automated error categorization
- **Checkpoint system** - State persistence and recovery

## Monitoring and Metrics

The agent provides comprehensive monitoring:
- **Phase completion rates** - Track which phases succeed/fail
- **Error patterns** - Monitor common failure points
- **Performance metrics** - Execution times and resource usage
- **Learning metrics** - Knowledge acquisition and application

## Production Deployment

### Best Practices
1. **Memory System**: Ensure MCP service is running and accessible
2. **Knowledge Base**: Keep knowledge files updated with latest practices
3. **Monitoring**: Set up alerts for workflow failures
4. **Backup**: Regular backup of agent memory and checkpoints
5. **Updates**: Regular updates to error patterns and recovery strategies

### Scaling Considerations
- The agent can handle multiple concurrent workflows
- Memory system should be scaled for high-throughput scenarios
- Consider load balancing for multiple agent instances
- Monitor resource usage during peak workflow execution

## Contributing

When extending the workflow manager:

1. **Add new phases** by extending the WorkflowPhase enum
2. **Add recovery patterns** to the error handling system
3. **Update knowledge base** with new best practices
4. **Add tests** for new functionality
5. **Update documentation** to reflect changes

## License

This agent is part of the Gadugi v0.3 system and follows the project's licensing terms.

---

**Status**: ✅ Production Ready
**Version**: 0.3.0
**Last Updated**: 2025-08-28
**Test Status**: All tests passing
**Memory Integration**: ✅ Complete
**Knowledge Base**: ✅ Comprehensive (5 knowledge files)
**Error Handling**: ✅ Production-ready
**PR Learning**: ✅ Fully implemented
