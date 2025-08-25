# Orchestrator Agent Invocation

/agent:orchestrator-agent

Execute the following task in an isolated worktree environment:

**Task**: Implement Team Coach as Phase 13 in the development workflow

**Prompt File**: implement-team-coach-phase13.md

**Requirements**:
1. Use worktree-manager to create an isolated environment
2. Delegate to WorkflowManager for proper workflow execution
3. Follow all 12 phases (current) to implement the 13th phase
4. Ensure proper testing and validation
5. Create PR with the implementation

**Context**: 
The Team Coach agent is already implemented and functional. This task adds it as a mandatory Phase 13 that executes automatically at the end of every workflow session to provide performance analysis and improvement recommendations.

**Expected Changes**:
- CLAUDE.md: Add Phase 13 documentation
- workflow-manager.md: Add Phase 13 execution logic
- orchestrator-agent.md: Add Phase 13 validation
- Test files to validate the integration

Please execute this task following the complete workflow process.