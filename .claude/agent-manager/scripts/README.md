# Agent Updater Scripts

This directory contains the implementation scripts for the Agent Updater functionality.

## Scripts

### agent-updater.sh
Main entry point for the agent-updater commands. Provides the following commands:
- `setup-hooks`: Configure Claude Code startup hooks in settings.json
- `check-updates`: Check for available agent updates
- `help`: Display help information

### check-updates.sh
Implements the check-updates functionality:
- Maintains a local cache of agent registry information
- Tracks last check timestamp to avoid excessive checks
- Compares installed agent versions with latest available versions
- Provides clear visual feedback about update status

### agent-command-handler.sh
Provides intuitive command parsing for natural language inputs:
- Handles direct commands like `check-updates`
- Understands natural language like "check for updates"
- Provides helpful feedback for unrecognized commands
- Routes commands to appropriate implementation scripts

### setup-hooks.sh
Configures startup hooks for Claude Code:
- Manages .gitignore entries
- Sets up automatic agent update checks on session start
- Configures agent-updater integration with Claude Code settings

## Usage

### Direct Command Line
```bash
# Check for updates
.claude/agent-updater/scripts/agent-updater.sh check-updates

# Force update check
.claude/agent-updater/scripts/agent-updater.sh check-updates --force

# Setup hooks
.claude/agent-updater/scripts/agent-updater.sh setup-hooks
```

### From Claude Code
```
/agent:agent-updater check-updates
/agent:agent-updater setup-hooks
```

### Natural Language
The agent-command-handler.sh supports natural language commands:
```bash
.claude/agent-updater/scripts/agent-command-handler.sh "check for updates"
.claude/agent-updater/scripts/agent-command-handler.sh "setup hooks"
```

## Implementation Details

### Cache Management
- Agent registry cached in `.claude/agent-updater/cache/agent-registry.json`
- Last check timestamp stored in `.claude/agent-updater/cache/last-check-timestamp`
- Default check interval: 24 hours (configurable)

### Version Comparison
- Semantic versioning support (MAJOR.MINOR.PATCH)
- Automatic detection of version updates
- Clear visual indicators for update status

### Error Handling
- Graceful handling of missing or malformed agent metadata
- Helpful error messages for unrecognized commands
- Fallback behavior when network is unavailable

## Security Considerations
- Scripts validate input to prevent injection attacks
- Cache files are gitignored to prevent accidental commits
- No sensitive data stored in cache or configuration files
