# Gadugi Agent

The Gadugi Agent is the central management hub for the Gadugi v0.3 multi-agent platform, providing comprehensive system bootstrap, installation, configuration management, and health monitoring capabilities.

## Overview

The Gadugi Agent serves as the orchestration center for the entire Gadugi ecosystem, managing services, agents, configurations, and system health. It provides a unified interface for all system management operations from initial installation to ongoing maintenance.

## Core Capabilities

### System Bootstrap
- **Fresh Installation**: Complete system setup from scratch
- **Component Installation**: Individual service and agent installation
- **Dependency Management**: Automatic dependency resolution and installation
- **Environment Configuration**: Development, staging, and production environment setup

### System Management  
- **Service Lifecycle**: Start, stop, restart, and monitor all Gadugi services
- **Agent Lifecycle**: Manage agent instances, health monitoring, and load balancing
- **Configuration Management**: Centralized configuration for all system components
- **Resource Management**: Monitor and optimize system resource usage

### Health Monitoring
- **Real-time Monitoring**: Continuous monitoring of system health and performance
- **Alerting**: Threshold-based alerting for resource usage and service health
- **Performance Analytics**: Detailed performance metrics and optimization recommendations
- **Health Checks**: Comprehensive health assessments with actionable insights

### Backup and Recovery
- **Automated Backups**: Scheduled backups with configurable retention policies
- **Disaster Recovery**: Complete system recovery from backups
- **Data Protection**: Checksums and verification for backup integrity
- **Selective Restore**: Restore specific components or configurations

## Architecture

### Core Services Managed
1. **Event Router** (port 8080): Agent communication service with protobuf
2. **Neo4j Graph** (port 7687): Shared memory persistence service  
3. **MCP Service** (port 8082): Memory operations interface
4. **LLM Proxy** (port 8081): Provider abstraction service
5. **Gadugi CLI** (port 8083): User interaction service

### Available Agents
- **Orchestrator**: Parallel execution and task coordination
- **Architect**: System design and architecture planning
- **Task Decomposer**: Task analysis and decomposition
- **Workflow Manager**: Workflow management and phase coordination
- **Code Writer**: Code generation and implementation
- **Code Reviewer**: Code review and quality analysis
- **Memory Manager**: Memory management and state tracking
- **Team Coach**: Team coordination and performance optimization
- **Prompt Writer**: Prompt generation and template management
- **Worktree Manager**: Git management and worktree isolation

## Usage

### Basic System Operations

```python
from src.orchestrator.gadugi_engine import GadugiEngine

gadugi = GadugiEngine()

# Get system status
status_request = {
    "command": "status",
    "target": "system"
}
result = gadugi.execute_operation(status_request)

# Start all services
start_request = {
    "command": "start",
    "target": "all"
}
result = gadugi.execute_operation(start_request)
```

### Service Management

```python
# Start specific service
start_service = {
    "command": "start",
    "target": "service",
    "parameters": {"component": "event-router"}
}
result = gadugi.execute_operation(start_service)

# Check service status
service_status = {
    "command": "status",
    "target": "service"
}
result = gadugi.execute_operation(service_status)
```

### Agent Management

```python
# Install new agent
install_agent = {
    "command": "install",
    "target": "agent",
    "parameters": {"component": "code-writer"}
}
result = gadugi.execute_operation(install_agent)

# Start agent
start_agent = {
    "command": "start",
    "target": "agent",
    "parameters": {"component": "orchestrator"}
}
result = gadugi.execute_operation(start_agent)
```

### Health Monitoring

```python
# Perform health check
health_check = {
    "command": "health",
    "target": "system",
    "options": {"detailed": True}
}
result = gadugi.execute_operation(health_check)

# Get resource usage
resource_check = {
    "command": "status",
    "target": "system"
}
result = gadugi.execute_operation(resource_check)
```

### Backup Operations

```python
# Create backup
backup_request = {
    "command": "backup",
    "target": "system",
    "parameters": {
        "backup_type": "full",
        "compress": True,
        "include_data": True
    }
}
result = gadugi.execute_operation(backup_request)

# Restore from backup
restore_request = {
    "command": "restore",
    "target": "system",
    "parameters": {"backup_file": "gadugi_backup_full_20240115_103000.tar.gz"}
}
result = gadugi.execute_operation(restore_request)
```

## Command Line Interface

### System Management
```bash
# System status and control
gadugi status                    # Overall system status
gadugi start                     # Start all services and agents
gadugi stop                      # Stop all services and agents  
gadugi restart                   # Restart all components
gadugi health --detailed         # Comprehensive health check
```

### Service Management
```bash
# Service operations
gadugi service start event-router      # Start specific service
gadugi service stop neo4j-graph        # Stop specific service
gadugi service status                   # Status of all services
gadugi service logs llm-proxy --follow  # View service logs
```

### Agent Management
```bash
# Agent operations
gadugi agent start orchestrator        # Start specific agent
gadugi agent stop code-writer          # Stop specific agent
gadugi agent install task-decomposer   # Install new agent
gadugi agent status                     # Status of all agents
```

### Configuration Management
```bash
# Configuration operations
gadugi config show                     # Show current configuration
gadugi config edit                     # Edit configuration
gadugi config validate                 # Validate configuration
gadugi config template production      # Apply production template
```

### Backup and Maintenance
```bash
# Backup operations
gadugi backup create --type full       # Create full backup
gadugi backup list                     # List available backups
gadugi backup restore backup_file.tar.gz # Restore from backup

# Maintenance operations  
gadugi optimize --auto                 # Auto-optimize system
gadugi update check                    # Check for updates
gadugi logs --analyze --error          # Analyze error logs
```

## Configuration

### System Configuration
```yaml
gadugi:
  version: "0.3.0"
  environment: "production"
  log_level: "info"
  max_agents: 50
  max_memory: "8GB"
  data_directory: "/var/lib/gadugi"
  log_directory: "/var/log/gadugi"

services:
  event-router:
    enabled: true
    auto_start: true
    port: 8080
    health_check_interval: "30s"
    
  neo4j-graph:
    enabled: true
    auto_start: true
    port: 7687
    memory_limit: "2GB"
    backup_interval: "24h"

agents:
  orchestrator:
    enabled: true
    max_instances: 3
    memory_limit: "512MB"
    
  architect:
    enabled: true
    max_instances: 2
    memory_limit: "256MB"

monitoring:
  enabled: true
  interval: 30
  cpu_threshold: 80
  memory_threshold: 85
  disk_threshold: 90

backup:
  enabled: true
  interval: "24h"
  retention_days: 30
  compression: true
```

### Environment Templates

#### Development Environment
```yaml
gadugi:
  environment: "development"
  log_level: "debug"
  max_agents: 10
  max_memory: "4GB"

services:
  event-router:
    enabled: true
    auto_start: true
  neo4j-graph:
    enabled: false
    auto_start: false
  
monitoring:
  enabled: false

backup:
  enabled: false
```

#### Production Environment
```yaml
gadugi:
  environment: "production"
  log_level: "info"
  max_agents: 50
  max_memory: "16GB"

services:
  event-router:
    enabled: true
    auto_start: true
    health_check_interval: "15s"
  neo4j-graph:
    enabled: true
    auto_start: true
    backup_interval: "12h"

monitoring:
  enabled: true
  interval: 15
  cpu_threshold: 70
  memory_threshold: 80

backup:
  enabled: true
  interval: "6h"
  retention_days: 90
```

## API Reference

### OperationType Enum
- `INSTALL`: Install system components
- `CONFIGURE`: Configure system settings
- `START`: Start services/agents
- `STOP`: Stop services/agents
- `STATUS`: Get status information
- `UPDATE`: Update system components
- `BACKUP`: Create system backups
- `RESTORE`: Restore from backups
- `HEALTH`: Perform health checks
- `OPTIMIZE`: Optimize system performance

### TargetType Enum
- `SYSTEM`: Target entire system
- `AGENT`: Target specific agent
- `SERVICE`: Target specific service
- `ALL`: Target all components

### Request Format
```json
{
  "command": "start",
  "target": "service",
  "parameters": {
    "component": "event-router",
    "force": false,
    "dry_run": false,
    "verbose": true
  },
  "options": {
    "environment": "production",
    "timeout": 300,
    "retry_count": 3
  }
}
```

### Response Format
```json
{
  "success": true,
  "operation": "start",
  "status": {
    "system_status": "healthy",
    "services_running": ["event-router", "llm-proxy"],
    "services_stopped": ["neo4j-graph"],
    "agents_active": 5,
    "memory_usage": "45%",
    "cpu_usage": "15%",
    "disk_usage": "60%",
    "uptime": "72:15:30"
  },
  "results": {
    "started_services": ["event-router"],
    "service_pids": {"event-router": 12345}
  },
  "recommendations": [
    {
      "priority": "medium",
      "category": "performance",
      "message": "Consider starting Neo4j service for full functionality",
      "action": "gadugi service start neo4j-graph"
    }
  ],
  "warnings": [],
  "errors": []
}
```

## System Status Monitoring

### Health Status Levels
- **HEALTHY**: All services running, resources within normal limits
- **DEGRADED**: Some services down or resources approaching limits  
- **CRITICAL**: Multiple services down or resources at critical levels
- **UNKNOWN**: Unable to determine system status

### Resource Thresholds
- **CPU Usage**: Warning at 70%, Critical at 90%
- **Memory Usage**: Warning at 80%, Critical at 95%
- **Disk Usage**: Warning at 85%, Critical at 95%
- **Service Response**: Warning at 1000ms, Critical at 5000ms

### Monitoring Metrics
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "overall_status": "healthy",
  "services": [
    {
      "name": "event-router",
      "status": "healthy",
      "uptime": "72h",
      "response_time": "15ms",
      "error_rate": "0.01%",
      "cpu_usage": "5%",
      "memory_usage": "256MB"
    }
  ],
  "agents": [
    {
      "name": "orchestrator", 
      "status": "healthy",
      "active_tasks": 5,
      "queue_length": 2,
      "last_heartbeat": "5s ago",
      "cpu_usage": "3%",
      "memory_usage": "128MB"
    }
  ],
  "resources": {
    "cpu_usage": "15%",
    "memory_usage": "45%",
    "disk_usage": "60%",
    "network_io": "125MB/s",
    "load_average": [0.5, 0.7, 0.8]
  }
}
```

## Backup and Recovery

### Backup Types
- **Full Backup**: Complete system state including all data
- **Incremental Backup**: Changes since last backup
- **Configuration Backup**: Configuration files only
- **Data Backup**: User and system data only

### Backup Operations
```python
# Create different backup types
full_backup = gadugi.execute_operation({
    "command": "backup",
    "target": "system", 
    "parameters": {"backup_type": "full", "compress": True}
})

config_backup = gadugi.execute_operation({
    "command": "backup",
    "target": "system",
    "parameters": {"backup_type": "config", "compress": False}
})

# List backups
backups = gadugi.list_backups()
```

### Recovery Procedures
1. **System Recovery**: Complete system restoration from full backup
2. **Service Recovery**: Restore specific service configurations and data
3. **Configuration Recovery**: Restore system and service configurations only
4. **Data Recovery**: Restore user data and persistent storage

## Security Features

### Access Control
- Role-based access control for operations
- Service-level permissions and restrictions
- Agent capability-based security model
- Audit logging for all operations

### Data Protection
- Backup integrity verification with checksums
- Configuration file encryption at rest
- Secure inter-service communication
- Regular security health checks

### Audit Logging
```python
# System events are automatically logged
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "service_start",
  "component": "event-router",
  "user": "system",
  "action": "start_service",
  "result": "success",
  "details": {"pid": 12345, "port": 8080}
}
```

## Performance Optimization

### Automatic Optimization
- Memory garbage collection and cleanup
- Database optimization (VACUUM, ANALYZE)
- Log file rotation and cleanup
- Resource usage monitoring and alerting

### Manual Optimization
```python
# Run system optimization
optimize_request = {
    "command": "optimize", 
    "target": "system",
    "parameters": {"auto": True}
}
result = gadugi.execute_operation(optimize_request)
```

### Performance Metrics
- Service response times and throughput
- Resource utilization trends
- Agent task completion rates
- System bottleneck identification

## Troubleshooting

### Common Issues

#### Services Won't Start
1. Check configuration files for syntax errors
2. Verify port availability and conflicts
3. Check system resource availability
4. Review service logs for specific errors

#### High Resource Usage
1. Use `gadugi status system` to identify resource hogs
2. Run `gadugi optimize --auto` to clean up resources
3. Check for memory leaks in long-running agents
4. Consider scaling or load balancing

#### Agent Communication Issues
1. Verify event-router service is running
2. Check network connectivity between components
3. Review agent logs for connection errors
4. Validate agent configurations

### Diagnostic Commands
```bash
# System diagnostics
gadugi health --detailed              # Comprehensive health check
gadugi status system --verbose        # Detailed system information
gadugi logs --analyze --error         # Error log analysis

# Service diagnostics  
gadugi service logs event-router      # Service-specific logs
gadugi service status --detailed      # Detailed service status

# Agent diagnostics
gadugi agent status --detailed        # Detailed agent status
gadugi agent logs orchestrator        # Agent-specific logs
```

## Integration with Development Workflow

### Pre-Development Setup
```bash
# Setup development environment
gadugi install --environment development
gadugi config template development
gadugi start --services-only
```

### During Development
```bash
# Hot reload support
gadugi agent restart code-writer      # Restart agent with new code
gadugi service logs --follow          # Monitor service logs
gadugi status --watch                 # Real-time status monitoring
```

### Production Deployment
```bash
# Production setup
gadugi install --environment production
gadugi backup create --type full      # Create backup before deployment
gadugi start all                      # Start all components
gadugi health --detailed              # Verify deployment health
```

## Best Practices

### Installation
1. Always use environment-specific configurations
2. Verify all dependencies before installation
3. Create backup before major changes
4. Test in staging environment first

### Operations
1. Monitor system health continuously
2. Set up automated alerting for critical thresholds  
3. Regular backup schedule with rotation
4. Keep configurations in version control

### Maintenance
1. Regular system optimization and cleanup
2. Monitor and analyze performance trends
3. Update components on regular schedule
4. Review and rotate log files

### Security
1. Use role-based access control
2. Regular security health checks
3. Encrypt sensitive configurations
4. Maintain audit logs

## Error Handling

The Gadugi Agent includes comprehensive error handling:

- **Graceful Degradation**: Continues operation when non-critical services fail
- **Automatic Recovery**: Attempts to restart failed services and agents
- **Detailed Error Reporting**: Provides actionable error messages and recommendations
- **Rollback Support**: Can rollback failed operations to previous state
- **Circuit Breaker**: Prevents cascading failures through circuit breaker patterns

## Testing

### Unit Testing
```bash
# Run Gadugi engine tests
python -m pytest tests/test_gadugi_engine.py -v
```

### Integration Testing
```bash
# Test full system integration
python tests/test_gadugi_integration.py
```

### Health Check Testing
```bash
# Test health monitoring
gadugi health --test-mode
```

## Future Enhancements

- **Container Orchestration**: Docker and Kubernetes integration
- **Cloud Deployment**: AWS, GCP, Azure deployment templates
- **Advanced Analytics**: Machine learning-based performance optimization
- **High Availability**: Multi-node clustering and failover
- **GraphQL API**: Modern API interface for system management
- **Web Dashboard**: Real-time web-based monitoring and management interface