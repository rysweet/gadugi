# Start Event Router Service

## Objective
Start and maintain the Event Router service on port 8000 with proper health monitoring.

## Requirements

1. **Research Phase**:
   - Review Event Router service implementation in `gadugi/event_service/`
   - Understand service dependencies and configuration
   - Check existing service management patterns
   - Review health check endpoints

2. **Implementation Phase**:
   - Start the Event Router service on port 8000
   - Implement service persistence (stays running)
   - Add health status monitoring
   - Update service manager if needed
   - Handle port conflicts gracefully

3. **Testing Phase**:
   - Verify service starts successfully
   - Test health endpoint responses
   - Validate service stays running
   - Test restart/recovery scenarios
   - Check proper shutdown handling

## Technical Details

### Service Location
- Main service: `gadugi/event_service/service.py`
- CLI interface: `gadugi/event_service/cli.py`
- Configuration: `gadugi/event_service/config.py`

### Service Requirements
- Port: 8000 (configurable)
- Protocol: HTTP/REST API
- Health endpoint: `/health`
- Dependencies: Neo4j connection (optional)

### Implementation Approach
1. Create service startup script
2. Implement process management (systemd/supervisor style)
3. Add health monitoring loop
4. Integrate with service-check.sh hook
5. Add automatic restart on failure

## Success Criteria
- [ ] Service starts on port 8000
- [ ] Health endpoint responds correctly
- [ ] Service persists across sessions
- [ ] Automatic restart on failure
- [ ] Proper logging configured
- [ ] Integration with service-check.sh

## Testing Requirements
- Service startup tests
- Health endpoint validation
- Persistence testing
- Recovery scenario tests
- Load testing for stability

## Documentation Updates
- Service management guide
- Health monitoring documentation
- Troubleshooting guide
- Integration with other services
