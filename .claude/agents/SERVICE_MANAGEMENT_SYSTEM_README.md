# Gadugi v0.3 Service Management System


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

## Overview
Comprehensive service management system for Gadugi v0.3 with individual service managers, centralized coordination, and automated startup hooks.

## System Architecture

```
Service Management System
├── Individual Service Managers
│   ├── Neo4jServiceManager.md
│   ├── MemoryServiceManager.md
│   └── EventRouterServiceManager.md
├── Central Coordinator
│   └── GadugiCoordinator.md
└── Startup Hook
    └── service-check.sh
```

## Components

### 1. Neo4j Service Manager (`Neo4jServiceManager.md`)
- **Purpose**: Manages Neo4j Docker container lifecycle
- **Features**:
  - Container status monitoring
  - Health check validation
  - Start/stop/restart operations
  - Connection testing (HTTP & Bolt)
  - Resource usage monitoring
  - Automated recovery strategies

### 2. Memory Service Manager (`MemoryServiceManager.md`)
- **Purpose**: Manages hierarchical memory system with fallback chain
- **Features**:
  - Neo4j primary backend monitoring
  - SQLite fallback management
  - In-memory cache coordination
  - Fallback chain health monitoring
  - Performance statistics
  - Automatic backend switching

### 3. Event Router Service Manager (`EventRouterServiceManager.md`)
- **Purpose**: Manages Event Router service lifecycle
- **Features**:
  - HTTP server monitoring (webhooks)
  - Unix socket server monitoring
  - GitHub API integration testing
  - Process management
  - Endpoint health checks
  - Event submission testing

### 4. Gadugi Coordinator (`GadugiCoordinator.md`)
- **Purpose**: Central coordination of all service managers
- **Features**:
  - Unified status aggregation
  - Service dependency management
  - Automated service startup
  - Comprehensive health reporting
  - Agent update coordination
  - Recommendation generation

### 5. Service Check Hook (`service-check.sh`)
- **Purpose**: Startup hook for automated service validation
- **Features**:
  - Task startup integration
  - Environment-based configuration
  - Verbose/quiet operation modes
  - Auto-start capabilities
  - Configurable timeout and retry logic

## Usage Examples

### Individual Service Management

#### Neo4j Service
```bash
# Check Neo4j status
./.claude/agents/Neo4jServiceManager.md status

# Start Neo4j
./.claude/agents/Neo4jServiceManager.md start

# Restart Neo4j
./.claude/agents/Neo4jServiceManager.md restart
```

#### Memory Service
```bash
# Check memory system status
./.claude/agents/MemoryServiceManager.md status

# Test memory operations
./.claude/agents/MemoryServiceManager.md test

# Force restart
./.claude/agents/MemoryServiceManager.md restart
```

#### Event Router Service
```bash
# Check Event Router status
./.claude/agents/EventRouterServiceManager.md status

# Test all endpoints
./.claude/agents/EventRouterServiceManager.md test

# Start service
./.claude/agents/EventRouterServiceManager.md start
```

### Centralized Management

#### Gadugi Coordinator
```bash
# Comprehensive status check
./.claude/agents/GadugiCoordinator.md status

# Start all services
./.claude/agents/GadugiCoordinator.md start

# JSON output for automation
./.claude/agents/GadugiCoordinator.md json
```

### Automated Hook Integration

#### Service Check Hook
```bash
# Basic service check
./.claude/hooks/service-check.sh

# Verbose output
GADUGI_SERVICE_CHECK_VERBOSE=true ./.claude/hooks/service-check.sh

# Disable auto-start
GADUGI_SERVICE_CHECK_AUTO_START=false ./.claude/hooks/service-check.sh

# Show configuration
./.claude/hooks/service-check.sh config
```

## Configuration

### Environment Variables

#### Global Settings
```bash
# Enable/disable entire service management system
export GADUGI_SERVICE_CHECK_ENABLED=true

# Enable verbose logging
export GADUGI_SERVICE_CHECK_VERBOSE=false

# Auto-start stopped services
export GADUGI_SERVICE_CHECK_AUTO_START=true

# Service check timeout
export GADUGI_SERVICE_CHECK_TIMEOUT=30

# Only check critical services
export GADUGI_SERVICE_CHECK_REQUIRED_ONLY=false
```

#### Service-Specific Settings
```bash
# Neo4j Configuration
export NEO4J_AUTH="neo4j/changeme"
export NEO4J_PAGECACHE_SIZE="1G"
export NEO4J_HEAP_MAX_SIZE="2G"

# Memory Service Configuration
export GADUGI_MEMORY_PRIMARY="neo4j"
export GADUGI_MEMORY_FALLBACK="true"
export GADUGI_SQLITE_PATH=".claude/memory/fallback.db"

# Event Router Configuration
export GADUGI_EVENT_PORT=8000
export GADUGI_EVENT_SOCKET="/tmp/gadugi-events.sock"
export GITHUB_TOKEN="your_github_token"
```

## Status Output Format

### Coordinator Status Summary
```
## Gadugi v0.3 Services Status

### Core Services:
✅ Neo4j Database - Running (Port 7475/7689)
⚠️ Memory Service - Using SQLite fallback
✅ Event Router - Running (Port 8000)

### Agent Updates:
✅ All agents up to date

### Overall Status: PARTIALLY OPERATIONAL

### Recommendations:
- Restore Neo4j connection for optimal memory performance
```

### JSON Status Format
```json
{
  "timestamp": "2024-08-29T12:00:00.000Z",
  "overall_status": "PARTIALLY_OPERATIONAL",
  "services": {
    "neo4j": {
      "name": "Neo4j Database",
      "status": "HEALTHY",
      "message": "Running and accessible",
      "details": {
        "container_status": "Up 2 hours",
        "http_port": 7475,
        "bolt_port": 7689
      }
    },
    "memory": {
      "name": "Memory System",
      "status": "DEGRADED", 
      "message": "Using SQLite fallback",
      "details": {
        "active_backend": "sqlite",
        "fallback_active": true
      }
    },
    "event-router": {
      "name": "Event Router",
      "status": "HEALTHY",
      "message": "Fully operational",
      "details": {
        "process": {"pid": 12345},
        "http_endpoint": "http://localhost:8000"
      }
    }
  },
  "summary": {
    "total_services": 3,
    "healthy": 2,
    "degraded": 1,
    "down": 0
  }
}
```

## Integration Points

### Claude Code Hook Integration
Add to `.claude/hooks/` directory and configure as session start hook:

```bash
# In .claude/settings.json
{
  "hooks": {
    "session_start": [".claude/hooks/service-check.sh"]
  }
}
```

### Orchestrator Integration
The service management system integrates with the Gadugi orchestrator:

```python
# In orchestrator workflow
from gadugi_coordinator import coordinator

# Ensure services before task execution
await coordinator.ensure_services_running()

# Get service status for context
status = await coordinator.get_comprehensive_status()
```

### GitHub Actions Integration
For CI/CD pipelines:

```yaml
# In .github/workflows/
- name: Check Gadugi Services
  run: |
    ./.claude/hooks/service-check.sh
    if [ $? -ne 0 ]; then
      echo "Service issues detected"
      exit 1
    fi
```

## Troubleshooting

### Common Issues

#### Neo4j Not Starting
```bash
# Check Docker
docker --version

# Check compose file
cat docker-compose.gadugi.yml

# Manual start
docker-compose -f docker-compose.gadugi.yml up -d neo4j

# Check logs
docker logs gadugi-neo4j
```

#### Memory Service Issues
```bash
# Check fallback directory
ls -la .claude/memory/

# Test SQLite manually
sqlite3 .claude/memory/fallback.db "SELECT 1;"

# Reset memory system
rm -rf .claude/memory/
./.claude/agents/MemoryServiceManager.md start
```

#### Event Router Problems
```bash
# Check if port is in use
netstat -an | grep :8000

# Check process
ps aux | grep event_service

# Clean restart
pkill -f event_service
./.claude/agents/EventRouterServiceManager.md start
```

### Service Recovery
```bash
# Full system recovery
GADUGI_SERVICE_CHECK_AUTO_START=true ./.claude/hooks/service-check.sh

# Individual service recovery
./.claude/agents/Neo4jServiceManager.md restart
./.claude/agents/MemoryServiceManager.md restart
./.claude/agents/EventRouterServiceManager.md restart

# Coordinator-managed recovery
./.claude/agents/GadugiCoordinator.md start
```

## Development

### Adding New Service Managers
1. Create new service manager agent in `.claude/agents/`
2. Implement status check, start, stop, restart functions
3. Add to coordinator's service registry
4. Update service check hook if needed
5. Add tests and documentation

### Service Manager Template
```bash
#!/bin/bash
# New Service Manager Template

check_service_status() {
    # Implement service-specific status check
    echo "HEALTHY|UNHEALTHY|DOWN|ERROR"
}

start_service() {
    # Implement service start logic
    return 0  # success
}

stop_service() {
    # Implement service stop logic  
    return 0  # success
}

restart_service() {
    stop_service && start_service
}

# Command dispatch
case "${1:-status}" in
    "status") check_service_status ;;
    "start") start_service ;;
    "stop") stop_service ;;
    "restart") restart_service ;;
    *) echo "Usage: $0 {status|start|stop|restart}" ;;
esac
```

## Best Practices

### Service Management
1. **Always check prerequisites** before service operations
2. **Use timeouts** for all service checks and operations
3. **Implement graceful degradation** when services are unavailable
4. **Log all service operations** for debugging
5. **Provide clear status messages** for users

### Hook Integration
1. **Make hooks configurable** via environment variables
2. **Support quiet and verbose modes** for different contexts
3. **Handle hook failures gracefully** without blocking tasks
4. **Cache status information** to avoid redundant checks
5. **Provide easy disable mechanism** when not needed

### Error Handling
1. **Always return meaningful exit codes**
2. **Log errors with sufficient context**
3. **Provide recovery recommendations**
4. **Fail fast on critical errors**
5. **Degrade gracefully on non-critical errors**

This comprehensive service management system ensures Gadugi v0.3 services are always available and healthy, with intelligent fallback mechanisms and detailed monitoring capabilities.