# Claude Code Hooks

This directory contains hooks that are executed by Claude Code at various points in the execution lifecycle.

## SessionStart Hook

The `service-check.sh` script is configured to run automatically when a Claude Code session starts.

### Configuration

The hook is configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/service-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Service Check Script

The `service-check.sh` script performs the following tasks:

1. **Service Status Check**: Verifies the status of core Gadugi services:
   - Neo4j Database (ports 7475/7689)
   - Memory Service (port 5000)
   - Event Router (port 8000)

2. **Auto-Start**: If services are down and `GADUGI_SERVICE_CHECK_AUTO_START=true` (default), attempts to start them

3. **Logging**: Logs all activity to `service-check.log`

### Environment Variables

Configure the service check behavior with these environment variables:

- `GADUGI_SERVICE_CHECK_ENABLED` - Enable/disable service check (default: true)
- `GADUGI_SERVICE_CHECK_VERBOSE` - Enable verbose output (default: false)
- `GADUGI_SERVICE_CHECK_AUTO_START` - Auto-start down services (default: true)
- `GADUGI_SERVICE_CHECK_TIMEOUT` - Check timeout in seconds (default: 30)
- `GADUGI_SERVICE_CHECK_REQUIRED_ONLY` - Only fail on critical services (default: false)

### Manual Execution

To run the service check manually:

```bash
bash .claude/hooks/service-check.sh
```

### Troubleshooting

If the hook is not executing:

1. Verify `.claude/settings.json` contains the SessionStart hook configuration
2. Check that the script has execute permissions: `chmod +x .claude/hooks/service-check.sh`
3. Review logs in `.claude/hooks/service-check.log`
4. Test manual execution with verbose mode: `GADUGI_SERVICE_CHECK_VERBOSE=true bash .claude/hooks/service-check.sh`

## Other Hooks

- `check-services.py` - Python script used by service-check.sh to check service status
- `xpia_web_validator.py` - XPIA defense validation for web operations
- `teamcoach-stop.py` - Team coach stop hook
- `teamcoach-subagent-stop.py` - Team coach subagent stop hook