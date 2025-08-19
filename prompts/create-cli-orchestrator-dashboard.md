# Create CLI Orchestrator Dashboard with Auto-Refresh

## Objective
Create a real-time CLI dashboard for monitoring orchestrator parallel workflow execution with auto-refresh, clickable links, and log file access.

## Context
The orchestrator successfully spawns parallel WorkflowManager processes, but we need a better CLI monitoring interface. The current web dashboard (being fixed in Issue #292) is useful for detailed analysis, but day-to-day monitoring needs a terminal-based interface.

## Current Orchestrator Status
- **3 active workflows** running parallel (43+ minutes runtime)
- **Direct subprocess execution** (not containers) via direct_executor.py
- **GitHub integration** working (Issues #289, #290, #292 auto-created)
- **Worktree isolation** functioning (`.worktrees/orchestrator-*`, `.worktrees/task-*`)

## Requirements

### Phase 1: Core CLI Dashboard Implementation
1. **Real-time process monitoring**: Track running Claude processes with PIDs, task names, runtime
2. **Auto-refresh interface**: Update every 2 seconds without manual intervention (like htop)
3. **GitHub activity tracking**: Show recent issues/PRs created by workflows
4. **Worktree status display**: List active worktrees with task information
5. **Terminal-friendly output**: Clean, readable formatting that works in any terminal

### Phase 2: Interactive Features
1. **Clickable GitHub links**: Open issues/PRs in browser when clicked
2. **Log file access**: Direct links to tail workflow logs
3. **Keyboard shortcuts**: [l]ogs, [g]ithub, [q]uit commands
4. **Error highlighting**: Show failed/stuck processes in red
5. **Status indicators**: Visual indicators for workflow phases

### Phase 3: Advanced Monitoring
1. **Process health detection**: Identify hung or failed workflows
2. **Resource tracking**: Monitor for processes consuming excessive resources
3. **Historical tracking**: Show completed workflows and their outcomes
4. **Alert system**: Highlight critical issues requiring attention

## Technical Requirements

### CLI Dashboard Features
```bash
=== Orchestrator Monitor === (Auto-refresh: 2s)       Last Updated: 14:06:30

┌──────────────────────────────────────────────────────────────────────────────┐
│ PID   │ Task                     │ Runtime │ GitHub Issue/PR    │ Log File    │
├──────────────────────────────────────────────────────────────────────────────┤
│ 99151 │ systematic-pr-review     │  43m    │ Issue #289        │ workflow.log │
│ 99312 │ achieve-zero-pyright     │  43m    │ Issue #290        │ pyright.log  │
│ 27893 │ fix-dashboard            │  11m    │ Issue #292        │ setup.log    │
└──────────────────────────────────────────────────────────────────────────────┘

Recent GitHub Activity:
- 20:55 Issue #292: Fix Orchestrator Dashboard Dependencies
- 20:51 Issue #291: Systematic PR Review and Response Workflow
- 20:24 Issue #290: CRITICAL: Achieve Zero Pyright Errors

Worktrees:
- .worktrees/orchestrator-systematic-pr-review-db011048 → tail -f workflow.log
- .worktrees/orchestrator-achieve-zero-pyright-aca31aeb → tail -f pyright.log
- .worktrees/task-fix-orchestrator-dashboard → tail -f setup.log

Commands: [l]ogs [g]ithub [q]uit                    ⟳ Refreshing automatically...
```

### Implementation Architecture
- **File location**: `.claude/orchestrator/cli_dashboard.py`
- **Dependencies**: Only standard library (no external deps)
- **Auto-refresh**: Terminal clearing with cursor positioning
- **Process detection**: Parse `ps aux` output for Claude processes
- **GitHub integration**: Use `gh` CLI for recent activity
- **Log file mapping**: Connect PIDs to worktree log files

### Key Functions
1. **`get_orchestrator_processes()`**: Detect active Claude/orchestrator processes
2. **`get_github_activity()`**: Fetch recent issues/PRs from workflows
3. **`get_worktree_status()`**: List active worktrees and their tasks
4. **`render_dashboard()`**: Generate formatted terminal output
5. **`auto_refresh_loop()`**: Main loop with 2-second updates
6. **`handle_keyboard_input()`**: Process user commands without blocking refresh

### UV Environment Compatibility
- **Use `uv run python`** for execution in UV projects
- **Standard library only**: No additional dependencies to install
- **Cross-platform**: Work on macOS, Linux, Windows
- **Terminal detection**: Adapt to different terminal sizes

## Success Criteria
- CLI dashboard starts without errors and shows current orchestrator processes
- Auto-refresh updates every 2 seconds showing real-time status
- GitHub links are properly formatted and clickable in supported terminals
- Log file paths are accurate and accessible
- Keyboard shortcuts work correctly
- Clean shutdown with 'q' command
- No impact on running orchestrator processes

## Priority
**MEDIUM** - Useful for monitoring but not blocking current workflows

## Implementation Strategy
1. **Execute via WorkflowManager**: Full 11-phase workflow for proper testing
2. **Minimal dependencies**: Use only Python standard library
3. **UV compatibility**: Ensure works with `uv run python` execution
4. **Terminal agnostic**: Work in any terminal environment

## Current Context
- Multiple orchestrator workflows actively running (43+ minutes)
- Web dashboard fix in progress (Issue #292)
- Need CLI interface for real-time monitoring during development
- Should complement, not replace, the web dashboard

Begin workflow execution immediately.
