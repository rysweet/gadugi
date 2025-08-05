# Implement Worktree and Claude Process Monitor Panel for Gadugi VS Code Extension

## Overview

Implement a VS Code sidebar panel that provides real-time monitoring of git worktrees and running Claude Code processes in the workspace. This panel will display current worktree status, running Claude processes with live runtime duration updates, and provide quick launch capabilities for new Claude instances. This feature is the second major functionality of the Gadugi VS Code extension and provides essential visibility into the multi-agent development environment.

---

## Problem Statement

### Current Limitations
- No visibility into active Claude Code processes across worktrees
- Developers must manually track which worktrees have active Claude sessions
- No centralized way to monitor process health and runtime duration
- Difficult to identify orphaned or stuck Claude processes
- No quick way to launch new Claude instances in existing worktrees

### Impact on Users
- **Lack of Visibility**: Developers lose track of active Claude sessions
- **Resource Management**: Difficult to manage multiple Claude processes efficiently
- **Workflow Inefficiency**: Time spent manually checking process status
- **Error Detection**: Hard to identify when Claude processes fail or become unresponsive
- **Process Cleanup**: Orphaned processes consume system resources

### Motivation for Change
The Gadugi system enables powerful parallel development through multiple Claude instances, but managing these processes manually creates operational overhead and reduces developer productivity. A centralized monitoring panel provides essential visibility and control over the parallel development environment, making it easier to manage complex multi-agent workflows effectively.

---

## Feature Requirements

### Functional Requirements

**Core Panel Functionality**:
- VS Code sidebar panel with tree view structure
- Real-time display of all git worktrees in workspace
- Live monitoring of running Claude Code processes
- Process runtime duration with automatic updates every few seconds
- Quick launch button for new Claude instances
- Process termination capabilities
- Manual refresh functionality

**Worktree Display Section**:
- List all detected git worktrees with hierarchical structure
- Show worktree name, path, and current branch
- Display status indicators (active/inactive, has Claude process)
- Show associated Claude process information if running
- Visual indicators for worktree health and status

**Process Monitor Section**:
- List all running Claude Code processes
- Display process ID, command line, and parent information
- Show runtime duration with live updates (HH:MM:SS format)
- Indicate associated worktree (if determinable)
- Process health status (running, stopped, error)
- Resource usage indicators (optional: CPU, memory)

**User Interaction Features**:
- Click worktree to focus/navigate in VS Code
- Launch new Claude instance button per worktree
- Terminate process functionality with confirmation
- Refresh/reload data manually
- Configurable auto-refresh intervals
- Context menus for additional actions

### Technical Requirements

**VS Code Integration**:
- Implement as VS Code TreeDataProvider
- Register as sidebar view container
- Use VS Code's built-in icons and theming
- Support VS Code command integration
- Follow VS Code extension UI guidelines

**Real-time Updates**:
- Efficient polling mechanism for process monitoring
- Configurable update intervals (default: 3 seconds)
- Event-driven updates for worktree changes
- Minimal performance impact on VS Code
- Proper cleanup of monitoring resources

**Cross-Platform Support**:
- Process detection on macOS, Linux, Windows
- Platform-specific process monitoring (ps, tasklist, etc.)
- Cross-platform path handling and display
- Shell integration for different operating systems

**Performance Requirements**:
- Panel updates complete in <500ms
- Memory usage <10MB for monitoring services
- CPU usage <2% during normal operation
- Responsive UI with large numbers of processes/worktrees
- Efficient data structures for process tracking

### Integration Requirements

**Gadugi System Integration**:
- Detect Claude processes started by Bloom command
- Integration with existing worktree management
- Support for OrchestratorAgent and WorkflowManager processes
- Compatibility with existing Gadugi terminal scripts

**VS Code Workspace Integration**:
- Respect VS Code workspace configuration
- Handle multi-root workspaces appropriately
- Integration with VS Code's git extension
- Support for workspace trust settings

---

## Technical Analysis

### Current Implementation Review

**Existing Gadugi Monitoring**:
- No existing centralized process monitoring
- Terminal management through shell scripts
- Manual process tracking and cleanup
- Limited visibility into parallel execution state

**VS Code Extension Ecosystem**:
- Process Manager extensions for reference
- Git extension integration patterns
- Terminal management extension examples
- Real-time panel update patterns

### Proposed Technical Approach

**Extension Architecture**:
```typescript
src/
├── extension.ts                    // Main extension entry point
├── panels/
│   ├── monitorPanel.ts            // Main panel controller
│   ├── worktreeTreeProvider.ts    // Worktree tree data provider
│   └── processTreeProvider.ts     // Process tree data provider
├── services/
│   ├── worktreeMonitor.ts         // Git worktree monitoring service
│   ├── processMonitor.ts          // Claude process monitoring service
│   ├── updateManager.ts           // Real-time update coordination
│   └── launchService.ts           // Claude instance launcher
├── models/
│   ├── worktree.ts               // Worktree data model
│   ├── process.ts                // Process data model
│   └── panelState.ts             // Panel state management
├── utils/
│   ├── processUtils.ts           // Cross-platform process utilities
│   ├── timeUtils.ts              // Duration formatting and calculation
│   └── iconUtils.ts              // VS Code icon and theming
└── types/
    └── index.ts                  // TypeScript type definitions
```

**Key Components**:

1. **MonitorPanel**: Main panel controller and coordinator
   - Manages panel lifecycle and state
   - Coordinates between data providers
   - Handles user interactions and commands

2. **WorktreeTreeProvider**: VS Code TreeDataProvider for worktrees
   - Discovers and monitors git worktrees
   - Provides hierarchical tree structure
   - Updates on filesystem changes

3. **ProcessTreeProvider**: VS Code TreeDataProvider for processes
   - Monitors running Claude processes
   - Provides process hierarchy and details
   - Real-time updates with duration tracking

4. **WorktreeMonitor**: Service for git worktree operations
   - Discovers worktrees using git commands
   - Monitors worktree changes and updates
   - Associates worktrees with processes

5. **ProcessMonitor**: Service for Claude process monitoring
   - Cross-platform process discovery
   - Runtime duration tracking
   - Process health monitoring

6. **UpdateManager**: Coordinates real-time updates
   - Manages update intervals and scheduling
   - Optimizes refresh cycles for performance
   - Handles subscription and cleanup

### Architecture and Design Decisions

**Tree View Structure**:
```
📁 Worktrees
├── 🏠 main (main branch)
│   ├── 📍 /Users/user/project
│   └── ⚡ Claude: main (PID: 1234, 02:34:12)
├── 🌿 feature-branch (feature-branch)
│   ├── 📍 /Users/user/project/.worktrees/feature-branch
│   └── ❌ No Claude process
└── 🔧 bugfix-123 (bugfix-123)
    ├── 📍 /Users/user/project/.worktrees/bugfix-123
    └── ⚡ Claude: bugfix-123 (PID: 5678, 00:45:33)

⚡ Claude Processes
├── 🟢 claude --resume (PID: 1234)
│   ├── 📁 Worktree: main
│   ├── ⏱️ Runtime: 02:34:12
│   └── 💾 Memory: 45.2 MB
└── 🟢 claude --resume (PID: 5678)
    ├── 📁 Worktree: bugfix-123
    ├── ⏱️ Runtime: 00:45:33
    └── 💾 Memory: 38.7 MB
```

**Process Discovery Strategy**:
- Use platform-specific commands (ps, tasklist, Get-Process)
- Filter processes by command name containing "claude"
- Parse command line arguments to identify Claude Code instances
- Associate processes with worktrees through working directory analysis

**Real-time Update Strategy**:
- Configurable polling interval (default: 3 seconds)
- Efficient diff-based updates to minimize UI refreshes
- Event-driven updates for filesystem changes
- Background processing to avoid blocking VS Code UI

### Dependencies and Integration Points

**VS Code Extension Dependencies**:
- `@types/vscode`: VS Code extension API types
- `@vscode/test-electron`: Testing framework
- `chokidar`: File system watching (optional)
- Platform-specific process utilities

**Runtime Dependencies**:
- Git (for worktree operations)
- Platform process monitoring tools
- VS Code TreeView and WebView APIs

**Integration with Existing Components**:
- Complements Bloom command functionality
- Uses same GitService for worktree discovery
- Integrates with existing terminal management
- Supports Gadugi parallel execution patterns

### Performance Considerations

**Efficient Monitoring**:
- Incremental updates instead of full refreshes
- Caching of process and worktree information
- Debounced UI updates to prevent flicker
- Optimized process filtering and parsing

**Resource Management**:
- Proper cleanup of monitoring intervals
- Memory-efficient data structures
- CPU throttling during intensive operations
- Configurable performance settings

---

## Implementation Plan

### Phase 1: Panel Foundation (Days 1-2)
**Deliverables**:
- VS Code TreeView panel structure
- Basic worktree tree provider
- Panel registration and lifecycle management
- Initial UI structure and theming

**Tasks**:
1. Create MonitorPanel class with VS Code integration
2. Implement basic WorktreeTreeProvider
3. Register panel in VS Code sidebar
4. Set up basic tree view structure
5. Configure VS Code icons and theming

### Phase 2: Worktree Monitoring (Days 2-3)
**Deliverables**:
- Complete worktree discovery and monitoring
- Worktree data model and state management
- Filesystem change detection
- Worktree-specific UI elements

**Tasks**:
1. Implement WorktreeMonitor service
2. Create Worktree data model
3. Add filesystem watching for worktree changes
4. Implement worktree tree display
5. Add worktree status indicators

### Phase 3: Process Monitoring (Days 3-5)
**Deliverables**:
- Cross-platform process discovery
- Process monitoring and tracking service
- Runtime duration calculation
- Process tree provider implementation

**Tasks**:
1. Implement cross-platform process discovery
2. Create ProcessMonitor service
3. Add runtime duration tracking
4. Implement ProcessTreeProvider
5. Create Process data model

### Phase 4: Real-time Updates (Days 5-6)
**Deliverables**:
- UpdateManager for coordinated refreshes
- Configurable update intervals
- Efficient update mechanisms
- Performance optimization

**Tasks**:
1. Implement UpdateManager coordination
2. Add configurable refresh intervals
3. Optimize update performance
4. Implement diff-based UI updates
5. Add performance monitoring

### Phase 5: User Interactions (Days 6-7)
**Deliverables**:
- Launch new Claude instance functionality
- Process termination capabilities
- Navigation and focus features
- Context menus and commands

**Tasks**:
1. Implement LaunchService for new Claude instances
2. Add process termination with confirmation
3. Create worktree navigation functionality
4. Implement context menus
5. Add keyboard shortcuts and commands

### Phase 6: Testing and Polish (Days 7-8)
**Deliverables**:
- Comprehensive test suite
- Performance optimization
- Error handling and edge cases
- Documentation and examples

**Tasks**:
1. Create unit tests for all services
2. Add integration tests for panel functionality
3. Performance testing and optimization
4. Comprehensive error handling
5. User documentation and examples

---

## Testing Requirements

### Unit Testing Strategy

**WorktreeMonitor Tests**:
- Mock git command execution
- Test worktree discovery and parsing
- Verify filesystem change detection
- Test error handling for git failures

**ProcessMonitor Tests**:
- Mock cross-platform process commands
- Test process discovery and filtering
- Verify runtime duration calculation
- Test process health monitoring

**UpdateManager Tests**:
- Mock timer and scheduling functionality
- Test update coordination and performance
- Verify proper cleanup and resource management
- Test configurable intervals

**Panel Provider Tests**:
- Mock VS Code TreeDataProvider APIs
- Test tree structure and hierarchy
- Verify data refresh and updates
- Test user interaction handling

### Integration Testing Strategy

**VS Code Panel Integration**:
- Test panel registration and display
- Verify tree view functionality
- Test command integration
- Validate theming and icons

**Real-time Monitoring Integration**:
- Test with actual git worktrees
- Verify process monitoring accuracy
- Test performance with multiple processes
- Validate cross-platform behavior

**Gadugi System Integration**:
- Test with Bloom command integration
- Verify WorkflowManager process detection
- Test OrchestratorAgent compatibility
- Validate existing script integration

### Performance Testing Requirements

**Scalability Testing**:
- Test with varying numbers of worktrees (1-50)
- Verify performance with multiple Claude processes
- Test update frequency impact
- Measure resource usage under load

**Real-time Performance**:
- Measure update latency and consistency
- Test UI responsiveness during updates
- Verify memory usage over time
- Test for memory leaks and resource cleanup

### Edge Cases and Error Scenarios

**Worktree Edge Cases**:
- Corrupted or missing worktrees
- Permission issues accessing worktree directories
- Network-based repository scenarios
- Rapidly changing worktree configurations

**Process Monitoring Edge Cases**:
- Claude processes without associated worktrees
- Processes with unusual command line arguments
- Rapid process creation and termination
- System performance impact scenarios

**VS Code Integration Edge Cases**:
- Panel disabled or hidden by user
- VS Code performance degradation
- Extension conflicts and interactions
- Workspace trust and security restrictions

### Test Coverage Expectations

**Coverage Requirements**:
- Unit tests: >90% line coverage
- Integration tests: >85% workflow coverage
- Error scenarios: 100% error path coverage
- Performance tests: All critical paths tested

**Quality Gates**:
- All automated tests must pass
- Manual testing completed on all platforms
- Performance benchmarks met
- No critical security vulnerabilities

---

## Success Criteria

### Functional Success Metrics

**Core Functionality**:
- ✅ Panel appears correctly in VS Code sidebar
- ✅ Displays all worktrees with accurate information
- ✅ Shows all running Claude processes
- ✅ Runtime duration updates every 3 seconds
- ✅ Launch functionality creates new Claude instances
- ✅ Process termination works correctly

**User Experience Metrics**:
- ✅ Panel updates complete in <500ms
- ✅ UI remains responsive during all operations
- ✅ Clear visual indicators for all states
- ✅ Intuitive navigation and interaction
- ✅ >95% user satisfaction in testing

### Technical Success Metrics

**Performance Benchmarks**:
- ✅ Panel refresh time: <500ms for 20 worktrees
- ✅ Process discovery: <1 second cross-platform
- ✅ Memory usage: <10MB for monitoring services
- ✅ CPU usage: <2% during normal operation
- ✅ Update accuracy: >99% correct process information

**Quality Metrics**:
- ✅ >90% unit test coverage
- ✅ >85% integration test coverage
- ✅ Zero critical security vulnerabilities
- ✅ Passes VS Code extension guidelines
- ✅ Cross-platform compatibility verified

**Reliability Metrics**:
- ✅ >99% uptime for monitoring services
- ✅ Graceful error handling in 100% of scenarios
- ✅ Proper resource cleanup on extension deactivation
- ✅ No memory leaks during extended operation

### Integration Success Metrics

**VS Code Integration**:
- ✅ Panel integrates seamlessly with VS Code UI
- ✅ Respects VS Code themes and user preferences
- ✅ Commands appear in Command Palette appropriately
- ✅ No conflicts with other extensions
- ✅ Proper workspace trust handling

**Gadugi System Integration**:
- ✅ Detects processes started by Bloom command
- ✅ Compatible with existing Gadugi workflows
- ✅ Supports OrchestratorAgent and WorkflowManager
- ✅ Integrates with existing terminal management

**Cross-Platform Compatibility**:
- ✅ Identical functionality on macOS, Linux, Windows
- ✅ Accurate process detection on all platforms
- ✅ Proper path handling and display
- ✅ Platform-specific optimizations work correctly

---

## Implementation Steps

### GitHub Issue Creation

**Issue Title**: "Feature: Worktree and Claude Process Monitor Panel for Gadugi VS Code Extension"

**Issue Description**:
```markdown
## Summary
Implement a VS Code sidebar panel that provides real-time monitoring of git worktrees and running Claude Code processes, with live runtime tracking and quick launch capabilities.

## Requirements
- VS Code sidebar panel with tree view structure
- Real-time display of all git worktrees in workspace
- Live monitoring of running Claude Code processes
- Process runtime duration with updates every few seconds
- Quick launch button for new Claude instances
- Process termination capabilities
- Cross-platform compatibility (macOS, Linux, Windows)

## UI Structure
**Worktree Section:**
- List all worktrees with status indicators
- Show current branch and associated Claude process
- Click to navigate, launch new instances

**Process Section:**
- Display running Claude processes with details
- Show PID, runtime duration, associated worktree
- Terminate process functionality

## Acceptance Criteria
- [ ] Panel appears in VS Code sidebar
- [ ] Accurately displays all worktrees and processes
- [ ] Live updates work reliably (every 3 seconds)
- [ ] Launch functionality creates new Claude instances
- [ ] Performance remains smooth with multiple items
- [ ] Cross-platform process detection works
- [ ] >90% test coverage achieved
- [ ] UI is intuitive and responsive

## Related
- GitHub issue #53: Feature specification
- Complements Bloom command functionality
- Part of Gadugi VS Code extension initiative
```

**Issue Labels**: `enhancement`, `vscode-extension`, `monitoring`

### Branch Management

**Branch Creation**:
```bash
git checkout main
git pull origin main
git checkout -b feature/monitor-panel-implementation
```

**Branch Naming Convention**: `feature/monitor-panel-implementation`

### Research Phase

**Technology Research**:
1. VS Code TreeDataProvider API and best practices
2. Cross-platform process monitoring techniques
3. Real-time update patterns in VS Code extensions
4. Performance optimization for monitoring panels

**Codebase Analysis**:
1. Examine existing Bloom command implementation
2. Review git worktree integration patterns
3. Study Claude process characteristics and detection
4. Analyze VS Code extension architecture patterns

### Implementation Phases

**Phase 1: Panel Foundation**
1. Create VS Code panel structure and registration
2. Implement basic TreeDataProvider interfaces
3. Set up panel lifecycle management
4. Configure VS Code theming and icons

**Phase 2: Worktree Monitoring**
1. Implement worktree discovery and monitoring
2. Create worktree data models and state management
3. Add filesystem change detection
4. Build worktree tree display and UI

**Phase 3: Process Monitoring**
1. Implement cross-platform process discovery
2. Create process monitoring and tracking services
3. Add runtime duration calculation and formatting
4. Build process tree display and management

**Phase 4: Real-time Updates**
1. Implement update coordination and scheduling
2. Add configurable refresh intervals
3. Optimize update performance and efficiency
4. Create diff-based UI update mechanisms

**Phase 5: User Interactions**
1. Implement launch and termination functionality
2. Add navigation and focus capabilities
3. Create context menus and keyboard shortcuts
4. Build command integration and accessibility

**Phase 6: Testing and Optimization**
1. Create comprehensive test suite
2. Perform cross-platform testing and validation
3. Optimize performance and resource usage
4. Add documentation and usage examples

### Testing and Validation

**Automated Testing**:
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# Performance tests
npm run test:performance

# Cross-platform tests
npm run test:platforms
```

**Manual Testing Scenarios**:
1. Test with various worktree configurations
2. Validate real-time updates and performance
3. Test process launch and termination
4. Verify cross-platform compatibility

### Documentation Phase

**User Documentation**:
1. Panel usage guide with screenshots
2. Configuration options and customization
3. Troubleshooting guide for common issues
4. Integration with existing Gadugi workflows

**Technical Documentation**:
1. Architecture documentation and diagrams
2. API documentation for extension interfaces
3. Performance tuning and optimization guide
4. Development and contribution guidelines

### PR Creation

**Pull Request Title**: "feat: implement worktree and Claude process monitor panel"

**Pull Request Description**:
```markdown
## Summary
Implements a VS Code sidebar panel for real-time monitoring of git worktrees and Claude Code processes. Provides live runtime tracking, process management, and quick launch capabilities.

## Features
- ✅ Real-time worktree and process monitoring
- ✅ Live runtime duration tracking (updates every 3s)
- ✅ Cross-platform process detection (macOS, Linux, Windows)
- ✅ Quick launch Claude instances in worktrees
- ✅ Process termination with confirmation
- ✅ Intuitive tree view with status indicators
- ✅ Performance optimized for large numbers of items

## Implementation
- ✅ VS Code TreeDataProvider architecture
- ✅ Cross-platform process monitoring services
- ✅ Efficient real-time update coordination
- ✅ Comprehensive error handling and edge cases
- ✅ Integration with existing Gadugi workflows

## Testing
- ✅ 178 unit tests passing (>90% coverage)
- ✅ 31 integration tests passing
- ✅ Cross-platform compatibility verified
- ✅ Performance testing with up to 50 worktrees
- ✅ Manual testing on all supported platforms

## Performance
- Panel refresh: <500ms for 20 worktrees
- Memory usage: <10MB for monitoring
- CPU usage: <2% during operation
- Real-time updates: 99.9% accuracy

## Documentation
- ✅ Complete user guide with examples
- ✅ Technical architecture documentation
- ✅ Performance optimization guide
- ✅ Troubleshooting and FAQ

Closes #53

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Code Review Process

**Code Review Agent Invocation**:
```
/agent:code-reviewer

Please conduct a comprehensive review of this monitor panel implementation for the Gadugi VS Code extension. Focus on:

1. VS Code TreeDataProvider implementation and best practices
2. Cross-platform process monitoring accuracy and reliability
3. Real-time update performance and resource efficiency
4. User experience and interface design
5. Error handling and edge case management
6. Integration with existing Gadugi system components
7. Test coverage and quality assurance
8. Security considerations for process monitoring

The implementation should meet all requirements from the original prompt and GitHub issue #53.
```

---

## Additional Considerations

### Security Considerations

**Process Monitoring Security**:
- Validate process access permissions
- Sanitize process information display
- Protect against privilege escalation
- Handle sensitive process information appropriately

**Extension Security**:
- Follow VS Code security guidelines
- Validate user inputs and commands
- Handle untrusted workspace scenarios
- Minimize required permissions

### Accessibility Considerations

**Screen Reader Support**:
- Provide descriptive aria labels
- Support keyboard navigation
- Announce state changes appropriately
- Use semantic tree structure

**Visual Accessibility**:
- Support high contrast themes
- Use appropriate color coding
- Provide alternative text indicators
- Support zoom and text scaling

### Future Enhancement Opportunities

**Advanced Monitoring Features**:
- Process resource usage graphs
- Historical runtime tracking
- Performance alerts and notifications
- Integration with VS Code tasks

**Advanced Management Features**:
- Batch process operations
- Custom launch configurations
- Integration with debug and profiling tools
- Remote worktree and process monitoring

### Performance Optimization Strategies

**Efficient Data Structures**:
- Use Map and Set for fast lookups
- Implement proper caching mechanisms
- Optimize tree traversal algorithms
- Minimize object allocation in hot paths

**Update Optimization**:
- Implement intelligent diff algorithms
- Use debouncing for rapid changes
- Cache unchanged data between updates
- Optimize render cycles and DOM updates

This comprehensive prompt provides all necessary details for implementing the Worktree and Claude Process Monitor Panel feature, ensuring a complete development workflow with proper testing, documentation, and integration considerations.
