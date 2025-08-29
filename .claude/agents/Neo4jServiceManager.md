# Neo4j Service Manager Agent


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
Manages Neo4j database container lifecycle for Gadugi v0.3. Handles Docker Compose operations, health checks, and provides detailed status reporting.

## Core Capabilities
- Check Neo4j container status
- Start/stop/restart Neo4j container
- Health check validation
- Connection testing
- Error handling and recovery
- Support for both Docker Compose and direct Docker commands

## Service Configuration
- **Container Name**: `gadugi-neo4j`
- **HTTP Port**: 7475 (external) → 7474 (internal)
- **Bolt Port**: 7689 (external) → 7687 (internal)
- **Docker Compose File**: `docker-compose.gadugi.yml`
- **Network**: `gadugi-network`

## Command Interface

### Status Check
```bash
# Check if container is running
docker ps -f name=gadugi-neo4j --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check container health
docker inspect gadugi-neo4j --format='{{.State.Health.Status}}'

# Test connection
curl -f http://localhost:7475/db/data/ >/dev/null 2>&1
```

### Service Management
```bash
# Start service
docker-compose -f docker-compose.gadugi.yml up -d neo4j

# Stop service
docker-compose -f docker-compose.gadugi.yml stop neo4j

# Restart service
docker-compose -f docker-compose.gadugi.yml restart neo4j

# Remove and recreate
docker-compose -f docker-compose.gadugi.yml down neo4j
docker-compose -f docker-compose.gadugi.yml up -d neo4j
```

## Implementation

### Status Detection
```bash
#!/bin/bash
check_neo4j_status() {
    # Check if container exists and is running
    if ! docker ps -f name=gadugi-neo4j --format "{{.Names}}" | grep -q "gadugi-neo4j"; then
        echo "STOPPED"
        return
    fi

    # Check health status
    health_status=$(docker inspect gadugi-neo4j --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")

    case "$health_status" in
        "healthy")
            # Double-check with connection test
            if curl -f http://localhost:7475/db/data/ >/dev/null 2>&1; then
                echo "HEALTHY"
            else
                echo "UNHEALTHY"
            fi
            ;;
        "unhealthy")
            echo "UNHEALTHY"
            ;;
        "starting")
            echo "STARTING"
            ;;
        *)
            echo "UNKNOWN"
            ;;
    esac
}
```

### Service Operations
```bash
#!/bin/bash
start_neo4j_service() {
    echo "Starting Neo4j service..."

    # Ensure Docker Compose file exists
    if [ ! -f "docker-compose.gadugi.yml" ]; then
        echo "ERROR: docker-compose.gadugi.yml not found"
        return 1
    fi

    # Start with Docker Compose
    if docker-compose -f docker-compose.gadugi.yml up -d neo4j; then
        echo "Neo4j service started successfully"

        # Wait for health check
        echo "Waiting for Neo4j to become healthy..."
        for i in {1..30}; do
            status=$(check_neo4j_status)
            if [ "$status" = "HEALTHY" ]; then
                echo "Neo4j is now healthy"
                return 0
            fi
            echo "Status: $status (attempt $i/30)"
            sleep 2
        done

        echo "WARNING: Neo4j started but health check timeout"
        return 2
    else
        echo "ERROR: Failed to start Neo4j service"
        return 1
    fi
}

stop_neo4j_service() {
    echo "Stopping Neo4j service..."

    if docker-compose -f docker-compose.gadugi.yml stop neo4j; then
        echo "Neo4j service stopped successfully"
        return 0
    else
        echo "ERROR: Failed to stop Neo4j service"
        return 1
    fi
}

restart_neo4j_service() {
    echo "Restarting Neo4j service..."

    if docker-compose -f docker-compose.gadugi.yml restart neo4j; then
        echo "Neo4j service restarted successfully"

        # Wait for health check
        echo "Waiting for Neo4j to become healthy..."
        for i in {1..30}; do
            status=$(check_neo4j_status)
            if [ "$status" = "HEALTHY" ]; then
                echo "Neo4j is now healthy"
                return 0
            fi
            echo "Status: $status (attempt $i/30)"
            sleep 2
        done

        echo "WARNING: Neo4j restarted but health check timeout"
        return 2
    else
        echo "ERROR: Failed to restart Neo4j service"
        return 1
    fi
}
```

### Detailed Status Reporting
```bash
#!/bin/bash
get_neo4j_detailed_status() {
    echo "=== Neo4j Service Status ==="

    # Basic container info
    if docker ps -f name=gadugi-neo4j --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "gadugi-neo4j"; then
        echo "Container Status:"
        docker ps -f name=gadugi-neo4j --format "  Name: {{.Names}}\n  Status: {{.Status}}\n  Ports: {{.Ports}}"

        # Health check details
        echo ""
        echo "Health Check:"
        health_status=$(docker inspect gadugi-neo4j --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
        echo "  Health Status: $health_status"

        if [ "$health_status" != "none" ]; then
            # Get health check logs
            echo "  Recent Health Checks:"
            docker inspect gadugi-neo4j --format='{{range .State.Health.Log}}  {{.Start}}: {{.Output}}{{end}}' | tail -3
        fi

        # Connection test
        echo ""
        echo "Connectivity:"
        if curl -f http://localhost:7475/db/data/ >/dev/null 2>&1; then
            echo "  HTTP (7475): ✅ Connected"
        else
            echo "  HTTP (7475): ❌ Failed"
        fi

        # Bolt connection test (basic telnet check)
        if timeout 3 bash -c "</dev/tcp/localhost/7689" 2>/dev/null; then
            echo "  Bolt (7689): ✅ Port Open"
        else
            echo "  Bolt (7689): ❌ Port Closed"
        fi

        # Resource usage
        echo ""
        echo "Resource Usage:"
        docker stats gadugi-neo4j --no-stream --format "  CPU: {{.CPUPerc}}\n  Memory: {{.MemUsage}}\n  Memory %: {{.MemPerc}}"

        # Logs (last few lines)
        echo ""
        echo "Recent Logs:"
        docker logs gadugi-neo4j --tail 3 2>&1 | sed 's/^/  /'

    else
        echo "Container Status: ❌ Not Running"

        # Check if container exists but is stopped
        if docker ps -a -f name=gadugi-neo4j --format "{{.Names}}" | grep -q "gadugi-neo4j"; then
            echo "Container exists but is stopped:"
            docker ps -a -f name=gadugi-neo4j --format "  Name: {{.Names}}\n  Status: {{.Status}}\n  Image: {{.Image}}"
        else
            echo "Container does not exist"
        fi
    fi

    # Check Docker Compose file
    echo ""
    echo "Configuration:"
    if [ -f "docker-compose.gadugi.yml" ]; then
        echo "  Docker Compose: ✅ Found"
    else
        echo "  Docker Compose: ❌ Missing"
    fi

    # Check network
    if docker network ls | grep -q "gadugi-network"; then
        echo "  Network: ✅ gadugi-network exists"
    else
        echo "  Network: ❌ gadugi-network missing"
    fi
}
```

## Error Recovery Strategies

### Common Issues and Solutions
1. **Container Not Starting**
   - Check Docker daemon
   - Verify docker-compose.gadugi.yml exists
   - Check for port conflicts
   - Ensure sufficient resources

2. **Health Check Failing**
   - Wait longer for startup
   - Check logs for errors
   - Verify network connectivity
   - Restart container

3. **Connection Issues**
   - Verify port mappings
   - Check firewall settings
   - Test internal vs external ports
   - Validate Neo4j authentication

### Automated Recovery
```bash
#!/bin/bash
recover_neo4j_service() {
    echo "Attempting Neo4j service recovery..."

    status=$(check_neo4j_status)
    echo "Current status: $status"

    case "$status" in
        "STOPPED")
            echo "Service is stopped, attempting to start..."
            start_neo4j_service
            ;;
        "UNHEALTHY")
            echo "Service is unhealthy, attempting restart..."
            restart_neo4j_service
            ;;
        "STARTING")
            echo "Service is starting, waiting..."
            sleep 10
            check_neo4j_status
            ;;
        "UNKNOWN")
            echo "Unknown status, attempting full restart..."
            stop_neo4j_service
            sleep 5
            start_neo4j_service
            ;;
        "HEALTHY")
            echo "Service is healthy, no action needed"
            ;;
    esac
}
```

## Environment Variables

### Configuration
- `NEO4J_AUTH` - Authentication (default: read from environment, never hardcode)
- `NEO4J_PAGECACHE_SIZE` - Page cache size (default: 1G)
- `NEO4J_HEAP_INITIAL_SIZE` - Initial heap (default: 1G)
- `NEO4J_HEAP_MAX_SIZE` - Max heap (default: 2G)

### Service Manager
- `GADUGI_NEO4J_TIMEOUT` - Health check timeout (default: 60s)
- `GADUGI_NEO4J_RETRIES` - Startup retries (default: 3)
- `GADUGI_COMPOSE_FILE` - Docker compose file path

## Agent Integration

This service manager is designed to be called by the Gadugi Coordinator agent and provide structured status information for centralized service monitoring.

### Return Codes
- `0` - Success/Healthy
- `1` - Error/Failed
- `2` - Warning/Timeout
- `3` - Not Applicable

### JSON Output Format
```json
{
  "service": "neo4j",
  "status": "HEALTHY|UNHEALTHY|STARTING|STOPPED|UNKNOWN",
  "ports": {
    "http": 7475,
    "bolt": 7689
  },
  "container": {
    "name": "gadugi-neo4j",
    "running": true,
    "health": "healthy"
  },
  "connectivity": {
    "http": true,
    "bolt": true
  },
  "message": "Service is running and healthy"
}
```
