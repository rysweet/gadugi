# Agent Manager Directory Structure

This directory contains the Agent Manager's configuration, cache, and operational data.

## Directory Structure

```
.claude/agent-manager/
├── cache/
│   ├── repositories/          # Cached repository clones
│   ├── manifests/            # Cached manifest files
│   ├── agent-registry.json   # Registry of available agents
│   └── metadata.json         # Cache metadata and statistics
├── config/
│   └── (future: agent-specific configs)
├── logs/
│   └── (future: operation logs)
├── repos/
│   └── (future: repository metadata)
├── config.yaml               # Main configuration
├── preferences.yaml          # User preferences
└── README.md                # This file
```

## Configuration Files

### config.yaml
Main configuration file containing:
- Repository definitions
- Update settings
- Cache configuration
- Security settings
- Logging preferences

### preferences.yaml
User-specific preferences including:
- Version preferences for specific agents
- Auto-installation categories
- Update schedules
- Conflict resolution strategies

## Cache Directory

### repositories/
Contains cloned copies of registered agent repositories for offline access and performance.

### manifests/
Cached manifest files from repositories for quick agent discovery.

### agent-registry.json
Central registry tracking:
- Available agents across all repositories
- Version information
- Installation status
- Dependencies

### metadata.json
Cache statistics and operational metadata:
- Cache size and file counts
- Last operation timestamps
- Error logs
- Performance metrics

## Usage

The Agent Manager automatically manages this directory structure. Manual modification is not recommended but the files can be inspected for troubleshooting.

For Agent Manager usage, use:
```bash
/agent:agent-manager <command>
```

See the main Agent Manager documentation for available commands and operations.
