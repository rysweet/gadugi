# Team Coach Hooks Disabled

## Why Were These Hooks Disabled?

The team coach hooks (`teamcoach-stop.py` and `teamcoach-subagent-stop.py`) have been temporarily disabled due to the following issues:

### Problem
1. **Infinite Process Spawning**: The hooks spawn new Claude Code sessions using `claude /agent:teamcoach`
2. **No Termination**: These sessions run indefinitely without producing output
3. **Resource Drain**: Multiple Claude sessions accumulate, consuming system resources

### Root Cause
The fundamental issue is architectural:
- Hooks are designed for quick, synchronous operations
- Spawning full Claude Code sessions from hooks creates cascading processes
- The `/agent:teamcoach` command requires an actual Claude Code agent implementation

### Temporary Solution
Both hooks have been removed from `.claude/settings.json` to prevent:
- Indefinite process spawning
- System resource exhaustion
- Cascading hook invocations

### Recommended Fix
For a proper reflection loop that improves prompts and agents:

1. **Lightweight Metrics Collection**: Hooks should only collect and log performance data
2. **Asynchronous Analysis**: Use a separate process to analyze collected metrics
3. **Manual Trigger**: Create a dedicated command for team performance analysis
4. **External Service**: Consider webhooks or external analytics services

## Original Hook Files
The original hook files remain in place but are not referenced in settings.json:
- `.claude/hooks/teamcoach-stop.py`
- `.claude/hooks/teamcoach-subagent-stop.py`

## Re-enabling Hooks
To re-enable (not recommended without fixes):
1. Edit `.claude/settings.json`
2. Add the hooks configuration back
3. Ensure proper cascade prevention and termination logic

## Related Issue
See GitHub Issue #74 for full analysis and long-term solution planning.
