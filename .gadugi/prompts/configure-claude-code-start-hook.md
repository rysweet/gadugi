# Configure Claude Code Start Hook

## Objective
Configure Claude Code to automatically run `.claude/hooks/service-check.sh` at task start.

## Requirements

1. **Research Phase**:
   - Investigate where Claude Code hooks are configured
   - Check existing hook configuration patterns
   - Understand the hook execution lifecycle
   - Review `.claude/settings.json` and `.claude/settings.local.json`

2. **Implementation Phase**:
   - Configure the service-check.sh hook to run at task start
   - Ensure proper permissions and execution context
   - Add appropriate error handling
   - Ensure the hook runs before any other task activities

3. **Testing Phase**:
   - Test that the hook runs automatically when Claude Code starts
   - Verify service check output appears in logs
   - Test failure scenarios (missing script, permission issues)
   - Validate that services are properly checked

## Technical Details

### Current Hook Structure
- Hook location: `.claude/hooks/service-check.sh`
- Purpose: Check status of required services (Event Router, Neo4j, etc.)
- Output: Logs to `service-check.log`

### Implementation Approach
1. Update Claude Code settings to include sessionStart hook
2. Configure proper hook invocation mechanism
3. Add logging and monitoring
4. Ensure non-blocking execution

## Success Criteria
- [ ] Hook configured in Claude Code settings
- [ ] Automatically runs at task start
- [ ] Service status properly checked
- [ ] Logs captured appropriately
- [ ] No performance impact on task startup
- [ ] Documentation updated

## Testing Requirements
- Unit tests for hook configuration
- Integration test for automatic execution
- Error handling tests
- Performance impact validation

## Documentation Updates
- Update `.claude/README.md` with hook configuration
- Document in `.claude/hooks/` directory
- Add troubleshooting guide
