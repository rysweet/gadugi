# Fix SessionStart:startup Hook Issue (#3)

## Overview

This prompt addresses issue #3 where the SessionStart:startup hook fails when attempting to invoke the agent-manager using `/agent:agent-manager` syntax. The shell interprets this as a file path rather than an agent invocation, resulting in a "No such file or directory" error (code 127).

## Problem Statement

### Current Behavior
- Hook command: `echo 'Checking for agent updates...' && /agent:agent-manager check-and-update-agents`
- Error: `/bin/sh: /agent:agent-manager: No such file or directory`
- Status code: 127 (command not found)
- Hook type: SessionStart:startup

### Root Cause
The `/agent:agent-manager` syntax is specific to Claude Code's agent invocation system and is not recognized by the shell when executed in hooks. Hooks run in a standard shell environment where this syntax is interpreted as a filesystem path.

## Technical Analysis

### Hook Execution Environment
1. **Hook Context**: SessionStart:startup hooks execute in a shell subprocess
2. **Shell Interpretation**: `/agent:agent-manager` is treated as an absolute file path
3. **Agent Invocation**: The `/agent:` syntax requires Claude Code's interpreter context

### Investigation Areas
1. How Claude Code processes agent invocations vs shell commands
2. Whether hooks support special syntax or require wrapper scripts
3. Current agent-manager implementation and alternative invocation methods
4. Documentation gaps around hook + agent integration

## Implementation Plan

### Phase 1: Research and Analysis
1. **Examine hook implementation**:
   - Review `.claude/settings.json` hook configuration
   - Understand hook execution environment and limitations
   - Identify if hooks can access Claude Code's agent system

2. **Investigate agent invocation methods**:
   - Research how agents are typically invoked outside of direct chat
   - Check if there are CLI or script-based agent invocation methods
   - Examine agent-manager specifically for startup/background usage

3. **Review documentation**:
   - Check existing documentation for hook + agent patterns
   - Identify missing documentation areas
   - Review similar issues or patterns in the codebase

### Phase 2: Solution Design
Based on research, implement one of these approaches:

#### Option A: Wrapper Script Approach
- Create a shell script that can invoke agents from hooks
- Script translates `/agent:agent-name` syntax to proper invocation
- Hook calls the wrapper script instead of direct agent syntax

#### Option B: Documentation and Syntax Update
- Document the correct way to invoke agents from hooks
- Update hook configuration with proper syntax
- Provide examples for common agent invocations in hooks

#### Option C: Hook Enhancement
- If feasible, enhance hook processing to support agent syntax
- Modify hook execution to recognize and handle `/agent:` syntax
- Maintain backward compatibility with standard shell commands

### Phase 3: Implementation
1. **Create the solution** (based on chosen approach)
2. **Update hook configuration** in `.claude/settings.json`
3. **Test the fix** thoroughly
4. **Document the solution** for future reference

### Phase 4: Testing and Validation
1. **Test hook execution**:
   - Verify SessionStart:startup hook runs without errors
   - Confirm agent-manager is properly invoked
   - Test hook functionality end-to-end

2. **Test edge cases**:
   - Different agent invocations in hooks
   - Various hook types (if applicable)
   - Error handling and fallback behavior

3. **Verify documentation**:
   - Ensure examples work as documented
   - Confirm clarity and completeness

## Success Criteria

### Primary Success Criteria
- [X] SessionStart:startup hook executes without error code 127
- [X] Agent-manager can be successfully invoked from the hook
- [X] Hook functionality works as originally intended
- [X] Solution is documented for future use

### Secondary Success Criteria
- [X] Solution works for other agent invocations in hooks
- [X] Documentation includes clear examples and troubleshooting
- [X] Implementation follows project patterns and conventions
- [X] Error messages are helpful if invocation fails

## Implementation Steps

### Step 1: Environment Analysis
```bash
# Examine current hook configuration
cat .claude/settings.json | jq '.hooks'

# Test hook execution environment
# Create a test hook to understand execution context
```

### Step 2: Agent Investigation
```bash
# Research agent-manager implementation
find . -name "*agent*" -type f | head -10
grep -r "agent-manager" . --include="*.md" --include="*.json"

# Check for existing agent invocation patterns
grep -r "/agent:" . --include="*.md"
```

### Step 3: Solution Implementation
Based on findings, implement the appropriate solution:

- **If wrapper needed**: Create executable script for agent invocation
- **If syntax issue**: Update documentation and hook configuration
- **If enhancement needed**: Modify hook processing (if feasible)

### Step 4: Testing Protocol
```bash
# Test the updated hook
# Verify agent-manager invocation works
# Check for any error conditions or edge cases
```

## Testing Requirements

### Functional Tests
1. **Hook Execution Test**:
   - Start Claude Code session
   - Verify SessionStart:startup hook executes
   - Confirm no error code 127
   - Validate agent-manager runs successfully

2. **Agent Invocation Test**:
   - Test direct agent-manager invocation (outside hook)
   - Test hook-based agent-manager invocation
   - Compare behavior and results

3. **Error Handling Test**:
   - Test with invalid agent names
   - Test with malformed syntax
   - Verify graceful error messages

### Integration Tests
1. **End-to-End Test**:
   - Full Claude Code startup process
   - Hook execution and agent updates
   - Normal session functionality

2. **Documentation Test**:
   - Follow documented examples step-by-step
   - Verify all examples work as documented
   - Test troubleshooting guidance

## Documentation Updates

### Required Documentation
1. **Hook + Agent Integration Guide**:
   - Proper syntax for invoking agents from hooks
   - Examples for common use cases
   - Troubleshooting guide for common issues

2. **Agent-Manager Startup Guide**:
   - How to configure automatic agent updates
   - SessionStart:startup hook examples
   - Best practices for agent management

3. **Hook Reference Update**:
   - Add agent invocation section
   - Include examples and patterns
   - Document limitations and workarounds

## Files to Modify

### Expected File Changes
- `.claude/settings.json` - Update hook configuration
- `README.md` or docs - Add hook + agent documentation
- Possibly create wrapper script (e.g., `scripts/invoke-agent.sh`)
- Update any existing agent documentation

### New Files (if needed)
- Shell wrapper script for agent invocation
- Hook examples documentation
- Troubleshooting guide for hook issues

## Notes and Considerations

### Technical Constraints
- Hooks execute in shell environment, not Claude Code context
- Agent invocation may require specific Claude Code runtime
- Shell escaping and syntax considerations for complex agent commands

### User Experience
- Solution should be simple and intuitive
- Error messages should be clear and actionable
- Documentation should prevent future similar issues

### Maintenance
- Solution should be robust and maintainable
- Consider future agent system changes
- Ensure compatibility with different shell environments
