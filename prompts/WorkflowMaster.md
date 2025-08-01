# WorkflowMaster Sub-Agent Implementation Prompt

## Overview

We need to implement a specialized workflow orchestration sub-agent for the Blarify project that executes the complete development workflow described in prompt files. This sub-agent will ensure consistent execution of all development phases from issue creation through PR review, following the established patterns in the `/prompts/` directory.

## Motivation

While we have well-structured prompts that describe features and workflows, executing these consistently requires careful orchestration. Manual execution can lead to:
1. Skipped workflow steps (forgetting to create issues, branches, or PRs)
2. Incomplete testing or documentation
3. Inconsistent commit practices
4. Missing code review steps
5. Poor progress tracking and communication

A specialized WorkflowMaster sub-agent can:
1. Execute complete workflows systematically
2. Ensure no steps are missed or shortcuts taken
3. Maintain consistent git practices and PR quality
4. Coordinate with other sub-agents (like code-reviewer)
5. Track progress and handle interruptions gracefully

## Requirements

### Technical Requirements

1. **Claude Code Sub-Agent**: Must follow Claude Code sub-agent patterns with proper YAML frontmatter
2. **Tool Access**: Needs Read, Write, Edit, Bash, Grep, LS, TodoWrite, Task tools for full workflow execution
3. **Git Integration**: Must handle all git operations properly
4. **GitHub CLI**: Must use `gh` commands for issues and PRs
5. **Sub-Agent Coordination**: Must invoke other agents like code-reviewer

### Functional Requirements

The sub-agent should:

1. **Parse Prompt Files**: Extract workflow steps and requirements from prompts
2. **Execute Workflow Phases**:
   - Create GitHub issue with comprehensive description
   - Create and checkout feature branch
   - Research and plan implementation
   - Implement features incrementally
   - Write and run tests
   - Create pull request
   - Invoke code review sub-agent
3. **Track Progress**: Use TodoWrite to maintain task list
4. **Handle Interruptions**: Save state and resume gracefully
5. **Ensure Quality**: Verify each phase meets success criteria

### Workflow Execution Pattern

The standard workflow that WorkflowMaster follows:

1. **Issue Creation Phase**
   - Parse requirements from prompt
   - Create detailed GitHub issue
   - Assign appropriate labels
   - Reference in subsequent commits

2. **Branch Management Phase**
   - Create feature branch with issue number
   - Ensure clean working directory
   - Set up proper tracking

3. **Research and Planning Phase**
   - Analyze existing codebase
   - Identify affected modules
   - Create detailed implementation plan
   - Update Memory.md with findings

4. **Implementation Phase**
   - Break work into small, focused commits
   - Follow TDD when applicable
   - Maintain code quality standards
   - Regular progress updates

5. **Testing Phase**
   - Write comprehensive tests
   - Ensure test isolation
   - Verify coverage targets
   - Run full test suite

6. **Documentation Phase**
   - Update relevant documentation
   - Add inline code comments
   - Update README if needed
   - Document API changes

7. **Pull Request Phase**
   - Create PR with detailed description
   - Link to original issue
   - Summarize changes and testing
   - Request reviews

8. **Review Phase**
   - Invoke code-reviewer sub-agent
   - Address feedback
   - Ensure CI passes
   - Final verification

## Implementation Plan

### Phase 1: Create WorkflowMaster Sub-Agent

1. Create `.claude/agents/workflow-master.md` with:
   - Proper YAML frontmatter
   - Clear workflow execution instructions
   - Error handling procedures
   - Progress tracking methods

2. Define execution checklist:
   - All workflow phases included
   - Git operations verified
   - Tests passing
   - Documentation updated
   - PR created successfully

### Phase 2: Workflow Parsing

1. Implement prompt parsing to extract:
   - Issue title and description
   - Branch naming
   - Implementation steps
   - Test requirements
   - Success criteria

2. Create execution plan:
   - Ordered task list
   - Dependencies identified
   - Time estimates
   - Checkpoints defined

### Phase 3: State Management

1. Progress tracking using TodoWrite:
   - Create tasks for each phase
   - Update status in real-time
   - Track blockers and issues
   - Maintain completion history

2. Interruption handling:
   - Save current state to Memory.md
   - Document incomplete tasks
   - Provide resumption instructions
   - Maintain git cleanliness

### Phase 4: Quality Gates

1. Phase validation:
   - Issue created and accessible
   - Branch properly set up
   - Tests written and passing
   - Documentation complete
   - PR checks passing

2. Sub-agent coordination:
   - Invoke code-reviewer at appropriate time
   - Handle reviewer feedback
   - Coordinate fixes and updates
   - Verify final approval

## Expected Outcomes

1. **Consistent Execution**: All workflows follow the same high-quality pattern
2. **Complete Delivery**: No phases skipped or forgotten
3. **Quality Assurance**: Built-in checks at each phase
4. **Progress Visibility**: Clear tracking of work status
5. **Smooth Coordination**: Seamless integration with other agents

## Success Criteria

- WorkflowMaster successfully executes complete workflows from prompt files
- All required phases are completed in order
- Git history is clean and well-documented
- PRs include comprehensive descriptions and pass reviews
- 95%+ workflow completion rate without manual intervention
- Clear progress tracking throughout execution

## Error Handling

WorkflowMaster should handle common issues:
- Git conflicts during branch creation
- Test failures requiring fixes
- CI/CD pipeline failures
- PR review feedback requiring changes
- Network issues during GitHub operations

Each error should:
- Be clearly communicated
- Include suggested resolution
- Update task status appropriately
- Allow for graceful recovery

## Integration with PromptWriter

WorkflowMaster works hand-in-hand with PromptWriter:
1. PromptWriter creates structured prompts
2. WorkflowMaster executes those prompts
3. Feedback from execution improves future prompts
4. Patterns identified enhance both agents

## Example Execution

When invoked with a prompt file:

1. WorkflowMaster reads and parses the prompt
2. Creates comprehensive task list with TodoWrite
3. Executes each phase systematically
4. Tracks progress and handles issues
5. Coordinates with other agents as needed
6. Delivers complete feature from issue to merged PR

## Next Steps

1. Create GitHub issue for WorkflowMaster implementation
2. Create feature branch
3. Implement the sub-agent in `.claude/agents/workflow-master.md`
4. Create workflow templates and examples
5. Test with various prompt types
6. Document usage patterns
7. Create PR and invoke code reviewer