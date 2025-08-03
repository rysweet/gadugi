# Team Coach Hook Analysis

## Problem Summary

The team coach hooks are causing indefinite processes because they:

1. **Spawn new Claude sessions**: The hooks call `claude /agent:teamcoach` which creates entirely new Claude Code sessions
2. **Risk infinite recursion**: If the new session also has team coach hooks enabled, it creates a cascade
3. **No actual implementation**: The teamcoach agent needs to be available as a Claude Code agent, not just markdown docs

## Current Implementation Issues

### Hook Design Problems

1. **teamcoach-stop.py**:
   - Runs on every Claude session end
   - Creates a new Claude session with 5-minute timeout
   - The new session might also trigger its own stop hook

2. **teamcoach-subagent-stop.py**:
   - Runs when any subagent completes
   - Also spawns new Claude sessions (3-minute timeout)
   - Could trigger multiple times per session

### Cascade Prevention

The hooks do have cascade prevention logic:
```python
if os.environ.get('CLAUDE_HOOK_EXECUTION', '0') == '1':
    print("🛡️ Cascade prevention: TeamCoach hook skipped during hook execution")
    return True
```

However, this only works if the spawned Claude session inherits the environment variable.

## Root Cause

The fundamental issue is architectural:
- Hooks are meant for simple, quick operations
- Spawning full Claude sessions from hooks is problematic
- The teamcoach "agent" isn't actually available as a Claude Code agent

## Recommendations

### Immediate Fix
1. Disable both team coach hooks to stop the indefinite processes
2. Remove them from `.claude/settings.json`

### Proper Implementation
For a simple reflection loop that improves prompts and agents:

1. **Log-based approach**: 
   - Hooks write performance data to log files
   - Separate analysis process reads logs periodically
   
2. **Lightweight analysis**:
   - Hooks perform simple metrics collection
   - Store results in JSON/CSV for later analysis
   
3. **Manual trigger**:
   - Create a dedicated command/script for team analysis
   - Run it manually when needed, not automatically

4. **Webhook integration**:
   - Send metrics to an external service
   - Perform analysis asynchronously

## Next Steps

1. PR to disable team coach hooks (in progress via workflow manager)
2. Design a proper reflection system that doesn't spawn Claude sessions
3. Implement lightweight metrics collection
4. Create manual analysis tools