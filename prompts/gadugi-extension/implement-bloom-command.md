# Implement Bloom Command for Gadugi VS Code Extension

## Overview

Implement a VS Code command called "Bloom" that automatically detects all git worktrees in the workspace, creates a new terminal for each worktree, navigates to the worktree directory, and executes `claude --resume` to start Claude Code instances. This feature is the first major functionality of the new Gadugi VS Code extension and directly supports the parallel development workflow enabled by the Gadugi multi-agent system.

---

## Problem Statement

### Current Limitations
- Developers working with multiple git worktrees must manually create terminals for each worktree
- Starting Claude Code instances across multiple worktrees is a repetitive, time-consuming process
- No streamlined way to resume Claude sessions across all active worktrees simultaneously
- Manual setup introduces errors and inconsistencies in parallel development workflows

### Impact on Users
- **Development Inefficiency**: Significant time spent on setup rather than actual development
- **Human Error**: Manual processes lead to missed worktrees or incorrect directory navigation
- **Workflow Disruption**: Context switching between worktrees breaks development flow
- **Barrier to Adoption**: Complex setup discourages use of parallel development capabilities

### Motivation for Change
The Gadugi system enables powerful parallel development through orchestrated multi-agent workflows, but the current manual setup process creates friction that reduces adoption and effectiveness. The Bloom command removes this friction by automating the entire setup process, making parallel development as easy as executing a single command.

---

## Feature Requirements

### Functional Requirements

**Core Functionality**:
- Command registration in VS Code Command Palette with name: "Bloom: start a new terminal for each worktree and then resume claude in that worktree"
- Automatic detection of all git worktrees in the current workspace
- Creation of one VS Code integrated terminal per detected worktree
- Automatic navigation to the correct directory in each terminal
- Execution of `claude --resume` command in each terminal
- Descriptive terminal naming convention: "Claude: [worktree-name]"

**User Experience**:
- Single command execution starts entire parallel development environment
- Clear feedback during execution (progress indicators, success/error messages)
- Graceful handling of edge cases with informative user messaging
- Non-blocking operation that allows continued VS Code usage during setup

### Technical Requirements

**VS Code Integration**:
- Use VS Code Extension API for command registration
- Integrate with VS Code's integrated terminal system
- Follow VS Code extension best practices and conventions
- Support VS Code themes and user terminal preferences

**Git Integration**:
- Execute `git worktree list` to discover worktrees
- Parse git worktree output to extract paths and branch names
- Handle various git worktree configurations and states
- Validate git repository context before execution

**Claude Code Integration**:
- Verify Claude Code is installed and accessible
- Execute `claude --resume` with proper error handling
- Handle cases where Claude Code fails to start
- Support different Claude Code installation methods

**Cross-Platform Compatibility**:
- Support macOS, Linux, and Windows environments
- Handle platform-specific path formats and shell commands
- Use appropriate shell/terminal for each platform
- Account for different git and Claude Code installation locations

### Integration Requirements

**Workspace Integration**:
- Detect VS Code workspace configuration
- Handle multi-root workspaces appropriately
- Respect VS Code workspace settings and preferences
- Integrate with VS Code's file explorer and git integration

**Gadugi System Integration**:
- Compatible with existing Gadugi multi-agent workflows
- Support for worktrees created by OrchestratorAgent
- Integration with WorkflowManager execution patterns
- Coordination with existing Gadugi terminal management scripts

---

## Technical Analysis

### Current Implementation Review

**Existing Gadugi Terminal Management**:
- `scripts/launch-claude-terminals.sh`: Bash script for terminal creation
- `scripts/launch-claude-vscode.py`: Python script for VS Code integration
- `scripts/restart-claude-worktrees.sh`: Worktree restart functionality
- `config/vscode-claude-terminals.json`: Configuration for terminal management

**VS Code Extension Ecosystem**:
- No existing Gadugi VS Code extension
- Opportunity to create first-class VS Code integration
- Can leverage existing terminal management logic as reference

### Proposed Technical Approach

**Extension Architecture**:
```typescript
src/
├── extension.ts          // Main extension entry point
├── commands/
│   └── bloomCommand.ts   // Bloom command implementation
├── services/
│   ├── gitService.ts     // Git worktree operations
│   ├── terminalService.ts // VS Code terminal management
│   └── claudeService.ts  // Claude Code integration
├── utils/
│   ├── pathUtils.ts      // Cross-platform path handling
│   └── errorUtils.ts     // Error handling utilities
└── types/
    └── index.ts          // TypeScript type definitions
```

**Key Components**:

1. **GitService**: Handles git worktree discovery and parsing
   - Execute `git worktree list --porcelain` for structured output
   - Parse worktree paths, branches, and states
   - Validate git repository context

2. **TerminalService**: Manages VS Code terminal creation and configuration
   - Create terminals with descriptive names
   - Set working directory for each terminal
   - Configure terminal options (shell, environment)

3. **ClaudeService**: Handles Claude Code integration
   - Verify Claude installation and accessibility
   - Execute `claude --resume` with proper error handling
   - Monitor Claude startup and provide feedback

4. **BloomCommand**: Orchestrates the complete workflow
   - Coordinate between all services
   - Provide user feedback and progress updates
   - Handle errors and edge cases gracefully

### Architecture and Design Decisions

**Command Registration**:
```typescript
vscode.commands.registerCommand('gadugi.bloom', async () => {
  const bloomCommand = new BloomCommand();
  await bloomCommand.execute();
});
```

**Terminal Naming Strategy**:
- Format: "Claude: [worktree-name]"
- Use git branch name or directory name for clarity
- Handle duplicate names with numbering
- Preserve existing terminal names when possible

**Error Handling Strategy**:
- Graceful degradation for individual worktree failures
- Clear error messages with actionable guidance
- Logging for debugging and troubleshooting
- User choice to continue or abort on errors

### Dependencies and Integration Points

**VS Code Extension Dependencies**:
- `@types/vscode`: VS Code extension API types
- `@vscode/test-electron`: Testing framework
- TypeScript compiler and toolchain

**Runtime Dependencies**:
- Git (required for worktree operations)
- Claude Code CLI (required for resume functionality)
- VS Code integrated terminal system

**Integration with Existing Gadugi Components**:
- Compatible with existing worktree management scripts
- Leverages existing terminal configuration patterns
- Maintains consistency with current Gadugi workflows

### Performance Considerations

**Concurrent Operations**:
- Terminal creation can be parallelized
- Limit concurrent operations to prevent system overload
- Provide progress feedback for long-running operations

**Resource Management**:
- Avoid creating excessive terminals
- Clean up failed terminals automatically
- Respect VS Code's terminal limits

---

## Implementation Plan

### Phase 1: Extension Foundation (Days 1-2)
**Deliverables**:
- VS Code extension project structure
- Basic command registration
- TypeScript configuration and build system
- Initial testing framework setup

**Tasks**:
1. Create extension project with `yo code` generator
2. Configure TypeScript compilation and bundling
3. Implement basic command registration
4. Set up testing infrastructure
5. Create initial package.json with proper metadata

### Phase 2: Git Worktree Service (Days 2-3)
**Deliverables**:
- GitService class with worktree discovery
- Comprehensive worktree parsing logic
- Error handling for git operations
- Unit tests for git functionality

**Tasks**:
1. Implement git worktree list execution
2. Parse git worktree output (both formats)
3. Handle edge cases (no worktrees, git errors)
4. Add comprehensive error handling
5. Create unit tests for all git operations

### Phase 3: Terminal Management Service (Days 3-4)
**Deliverables**:
- TerminalService class for VS Code integration
- Terminal creation and configuration logic
- Cross-platform terminal handling
- Unit tests for terminal operations

**Tasks**:
1. Implement VS Code terminal creation
2. Add terminal naming and configuration
3. Handle cross-platform differences
4. Implement error recovery for terminal failures
5. Create comprehensive terminal tests

### Phase 4: Claude Code Integration (Days 4-5)
**Deliverables**:
- ClaudeService class for Claude integration
- Claude installation detection
- Resume command execution with error handling
- Integration tests with actual Claude instances

**Tasks**:
1. Implement Claude installation detection
2. Add claude --resume execution logic
3. Handle Claude startup errors and timeouts
4. Create monitoring for Claude process health
5. Add integration tests with Claude

### Phase 5: Command Orchestration (Days 5-6)
**Deliverables**:
- BloomCommand class orchestrating all services
- User feedback and progress reporting
- Comprehensive error handling and recovery
- End-to-end integration tests

**Tasks**:
1. Implement BloomCommand coordination logic
2. Add user feedback and progress indicators
3. Implement comprehensive error handling
4. Create end-to-end workflow tests
5. Add performance optimization

### Phase 6: Testing and Documentation (Days 6-7)
**Deliverables**:
- Complete test suite with high coverage
- Extension documentation and examples
- Performance testing and optimization
- Release preparation

**Tasks**:
1. Achieve >90% test coverage across all components
2. Create user documentation and examples
3. Perform manual testing across platforms
4. Optimize performance and resource usage
5. Prepare extension for VS Code marketplace

---

## Testing Requirements

### Unit Testing Strategy

**GitService Tests**:
- Mock git command execution and output parsing
- Test various git worktree list output formats
- Verify error handling for git failures
- Test edge cases (no git, no worktrees, invalid repos)

**TerminalService Tests**:
- Mock VS Code terminal API interactions
- Test terminal creation with various configurations
- Verify terminal naming and deduplication logic
- Test cross-platform path handling

**ClaudeService Tests**:
- Mock Claude command execution
- Test Claude installation detection
- Verify error handling for Claude failures
- Test timeout and process monitoring

**BloomCommand Tests**:
- Mock all service dependencies
- Test complete workflow orchestration
- Verify error propagation and handling
- Test user feedback and progress reporting

### Integration Testing Strategy

**VS Code Extension Integration**:
- Test command registration and execution in VS Code
- Verify terminal creation and configuration
- Test with real VS Code workspace configurations
- Validate cross-platform behavior

**Git Worktree Integration**:
- Test with real git repositories and worktrees
- Verify handling of various worktree states
- Test with different git configurations
- Validate path handling and navigation

**Claude Code Integration**:
- Test with real Claude Code installations
- Verify claude --resume functionality
- Test error scenarios (Claude not installed, network issues)
- Validate process monitoring and feedback

### Performance Testing Requirements

**Scalability Testing**:
- Test with varying numbers of worktrees (1, 5, 10, 20+)
- Measure terminal creation time and resource usage
- Test concurrent operation limits
- Verify graceful degradation under load

**Resource Usage Testing**:
- Monitor memory usage during execution
- Test CPU usage with multiple concurrent operations
- Verify proper cleanup of resources
- Test for memory leaks in long-running scenarios

### Edge Cases and Error Scenarios

**Git Edge Cases**:
- No git repository in workspace
- Empty git repository (no worktrees)
- Corrupted or locked git repository
- Network-based git repositories

**VS Code Edge Cases**:
- No workspace open
- Multi-root workspaces
- Workspace on network drives
- Limited terminal creation permissions

**Claude Code Edge Cases**:
- Claude not installed or not in PATH
- Claude license/authentication issues
- Network connectivity problems
- Claude process crashes during startup

**System Edge Cases**:
- Insufficient permissions for terminal creation
- Disk space limitations
- Network drive access issues
- Antivirus interference with process execution

### Test Coverage Expectations

**Minimum Coverage Requirements**:
- Unit tests: >90% line coverage
- Integration tests: >80% workflow coverage
- Error scenarios: 100% error path coverage
- Cross-platform: All major platforms tested

**Quality Gates**:
- All tests must pass before release
- No critical or high-severity security issues
- Performance requirements met across all test scenarios
- Manual testing validation on all supported platforms

---

## Success Criteria

### Functional Success Metrics

**Core Functionality**:
- ✅ Command appears in VS Code Command Palette
- ✅ Successfully detects all worktrees in workspace (100% accuracy)
- ✅ Creates exactly one terminal per worktree
- ✅ All terminals have correct working directory
- ✅ Claude --resume executes successfully in all terminals
- ✅ Terminal names follow specified convention

**User Experience Metrics**:
- ✅ Command execution completes in <30 seconds for 10 worktrees
- ✅ Clear progress feedback provided during execution
- ✅ Error messages are actionable and user-friendly
- ✅ No VS Code UI blocking during command execution
- ✅ >95% user satisfaction in initial testing

### Technical Success Metrics

**Quality Metrics**:
- ✅ >90% unit test coverage across all components
- ✅ >80% integration test coverage
- ✅ Zero critical security vulnerabilities
- ✅ Passes all VS Code extension marketplace requirements
- ✅ Performance requirements met (see below)

**Performance Benchmarks**:
- ✅ Terminal creation: <2 seconds per worktree
- ✅ Git worktree discovery: <5 seconds regardless of count
- ✅ Claude startup monitoring: <10 seconds timeout
- ✅ Memory usage: <50MB additional during execution
- ✅ CPU usage: <10% average during execution

**Reliability Metrics**:
- ✅ >99% success rate in normal operation scenarios
- ✅ Graceful error handling in 100% of error scenarios
- ✅ No data loss or corruption in any scenario
- ✅ Proper resource cleanup in all execution paths

### Integration Success Metrics

**VS Code Integration**:
- ✅ Extension loads successfully on all supported VS Code versions
- ✅ Command appears correctly in Command Palette
- ✅ Terminals integrate properly with VS Code terminal system
- ✅ Respects VS Code themes and user preferences
- ✅ No conflicts with other installed extensions

**Gadugi System Integration**:
- ✅ Compatible with existing Gadugi workflows
- ✅ Works with OrchestratorAgent-created worktrees
- ✅ Maintains consistency with existing terminal scripts
- ✅ Supports WorkflowManager execution patterns

**Cross-Platform Compatibility**:
- ✅ Functionality identical across macOS, Linux, Windows
- ✅ Proper path handling on all platforms
- ✅ Shell command execution works correctly
- ✅ Git integration functions on all platforms

---

## Implementation Steps

### GitHub Issue Creation

**Issue Title**: "Feature: Implement Bloom Command for Gadugi VS Code Extension"

**Issue Description**:
```markdown
## Summary
Implement the "Bloom" command as the first major feature of the Gadugi VS Code extension. This command automatically detects git worktrees, creates VS Code terminals for each, and starts Claude Code instances.

## Requirements
- Command: "Bloom: start a new terminal for each worktree and then resume claude in that worktree"
- Automatic git worktree detection using `git worktree list`
- Terminal creation with proper naming: "Claude: [worktree-name]"
- Execute `claude --resume` in each terminal
- Comprehensive error handling and user feedback
- Cross-platform compatibility

## Acceptance Criteria
- [ ] Command registered in VS Code Command Palette
- [ ] Successfully detects all git worktrees
- [ ] Creates one terminal per worktree
- [ ] Executes claude --resume in each terminal
- [ ] Provides clear user feedback
- [ ] Handles edge cases gracefully
- [ ] >90% test coverage
- [ ] Works on macOS, Linux, Windows

## Related
- GitHub issue #52: Feature specification
- Part of Gadugi VS Code extension initiative
```

**Issue Labels**: `enhancement`, `vscode-extension`, `good first issue`

### Branch Management

**Branch Creation**:
```bash
git checkout main
git pull origin main
git checkout -b feature/bloom-command-implementation
```

**Branch Naming Convention**: `feature/bloom-command-implementation`

### Research Phase

**Codebase Analysis**:
1. Examine existing terminal management scripts:
   - `scripts/launch-claude-terminals.sh`
   - `scripts/launch-claude-vscode.py`
   - `scripts/restart-claude-worktrees.sh`
2. Review VS Code extension patterns and best practices
3. Analyze git worktree integration requirements
4. Study Claude Code CLI interface and options

**Technology Research**:
1. VS Code Extension API documentation
2. TypeScript best practices for VS Code extensions
3. Git worktree command options and output formats
4. Cross-platform terminal and shell handling

### Implementation Phases

**Phase 1: Project Setup**
1. Create VS Code extension project structure
2. Configure TypeScript and build system
3. Set up testing framework and CI/CD
4. Create initial package.json and manifest

**Phase 2: Service Implementation**
1. Implement GitService for worktree discovery
2. Create TerminalService for VS Code integration
3. Build ClaudeService for Claude Code integration
4. Add comprehensive unit tests for each service

**Phase 3: Command Implementation**
1. Create BloomCommand orchestration class
2. Implement user feedback and progress reporting
3. Add comprehensive error handling
4. Create integration tests for complete workflow

**Phase 4: Testing and Validation**
1. Achieve target test coverage (>90%)
2. Perform manual testing across platforms
3. Conduct performance testing and optimization
4. Validate against all success criteria

### Testing and Validation

**Automated Testing**:
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# Coverage reporting
npm run test:coverage

# Cross-platform testing
npm run test:all-platforms
```

**Manual Testing Scenarios**:
1. Test with various worktree configurations
2. Validate error handling with different failure modes
3. Verify performance with multiple worktrees
4. Test cross-platform compatibility

### Documentation Phase

**Extension Documentation**:
1. README.md with installation and usage instructions
2. CONTRIBUTING.md for development guidelines
3. API documentation for extension interfaces
4. User guide with examples and troubleshooting

**Code Documentation**:
1. Comprehensive inline code comments
2. JSDoc documentation for all public interfaces
3. Architecture documentation and diagrams
4. Deployment and release notes

### PR Creation

**Pull Request Title**: "feat: implement Bloom command for Gadugi VS Code extension"

**Pull Request Description**:
```markdown
## Summary
Implements the Bloom command as the first major feature of the Gadugi VS Code extension. This command automates the setup of Claude Code instances across all git worktrees in the workspace.

## Changes
- ✅ New VS Code extension with TypeScript
- ✅ GitService for worktree discovery and parsing
- ✅ TerminalService for VS Code terminal management
- ✅ ClaudeService for Claude Code integration
- ✅ BloomCommand for workflow orchestration
- ✅ Comprehensive test suite (>90% coverage)
- ✅ Cross-platform compatibility (macOS, Linux, Windows)
- ✅ Error handling and user feedback

## Testing
- ✅ 156 unit tests passing
- ✅ 23 integration tests passing
- ✅ Manual testing on all platforms
- ✅ Performance testing with up to 20 worktrees

## Performance
- Terminal creation: <2s per worktree
- Memory usage: <50MB during execution
- Success rate: >99% in normal scenarios

## Documentation
- ✅ Complete user documentation
- ✅ API documentation
- ✅ Architecture documentation
- ✅ Troubleshooting guide

Closes #52

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Code Review Process

**Review Checklist**:
- [ ] All requirements implemented correctly
- [ ] Code quality meets project standards
- [ ] Test coverage >90% achieved
- [ ] Documentation complete and accurate
- [ ] Performance requirements met
- [ ] Security review completed
- [ ] Cross-platform compatibility verified

**Code Review Agent Invocation**:
```
/agent:CodeReviewer

Please conduct a comprehensive review of this Bloom command implementation for the Gadugi VS Code extension. Focus on:

1. VS Code extension best practices and API usage
2. Git integration correctness and error handling
3. Cross-platform compatibility
4. TypeScript code quality and type safety
5. Test coverage and quality
6. Performance and resource usage
7. User experience and error messaging
8. Integration with existing Gadugi workflows

The implementation should meet all requirements from the original prompt and GitHub issue #52.
```

---

## Additional Considerations

### Security Considerations

**Code Execution Security**:
- Validate all git commands before execution
- Sanitize user input and file paths
- Use parameterized commands to prevent injection
- Limit permissions for spawned processes

**VS Code Extension Security**:
- Follow VS Code security best practices
- Minimize required permissions
- Validate workspace trust settings
- Handle untrusted workspace scenarios

### Accessibility Considerations

**User Interface Accessibility**:
- Provide screen reader compatible feedback
- Use appropriate contrast and colors
- Support keyboard-only navigation
- Provide alternative text for visual indicators

**Error Messaging Accessibility**:
- Clear, descriptive error messages
- Provide actionable guidance for resolution
- Support multiple output formats
- Consider internationalization needs

### Future Enhancement Opportunities

**Advanced Features**:
- Configuration options for terminal preferences
- Integration with VS Code tasks and launch configurations
- Support for custom Claude commands beyond --resume
- Batch operations and terminal management

**Monitoring and Analytics**:
- Usage analytics and performance metrics
- Error reporting and diagnostics
- User feedback collection
- Performance optimization insights

This comprehensive prompt provides all necessary details for implementing the Bloom command feature, ensuring a complete development workflow from issue creation to final code review.
