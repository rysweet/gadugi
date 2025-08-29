# Memory Health Check System

The Memory Health Check System provides comprehensive monitoring and automatic failover for Gadugi's memory backends. It ensures high availability and reliability of memory operations across different storage systems.

## Overview

The system monitors four types of memory backends:
- **Neo4j**: Graph database for complex memory relationships
- **SQLite**: Lightweight relational database for structured storage
- **Markdown**: File-based storage for human-readable persistence  
- **In-Memory**: Fast volatile storage (always available fallback)

## Features

### 🏥 Health Monitoring
- **Connection Testing**: Verifies backend connectivity and responsiveness
- **Query Validation**: Ensures backends can perform memory operations
- **Permission Checks**: Validates file system access for file-based backends
- **Performance Metrics**: Tracks response times and error rates

### ⚡ Automatic Failover
- **Priority-Based Selection**: Uses highest priority healthy backend
- **Graceful Degradation**: Falls back to simpler backends when needed
- **Retry Logic**: Attempts reconnection before permanent failover
- **Event Notifications**: Emits events for monitoring and debugging

### 📊 Status Reporting
- **Health Dashboard**: Comprehensive backend status information
- **Diagnostic Tools**: Built-in troubleshooting and testing utilities
- **Metrics Collection**: Performance and reliability statistics
- **API Endpoints**: Programmatic access to health information

### 🔧 Configuration
- **Flexible Intervals**: Configurable health check frequencies
- **Cache Management**: Intelligent result caching to reduce overhead
- **Logging Integration**: Detailed logging for debugging and monitoring
- **Environment Variables**: Easy deployment configuration

## Quick Start

### Basic Usage

```python
from .shared.memory_health_integration import memory_with_health_monitoring

# Use memory with automatic health monitoring
async with memory_with_health_monitoring(
    agent_id="my_agent",
    project_id="my_project",
    enable_health_monitoring=True,
    health_check_interval=30  # Check every 30 seconds
) as memory:
    
    # Memory operations automatically handle failover
    await memory.remember_short_term("Important information")
    memories = await memory.recall_memories(limit=10)
    
    # Check backend health status
    health_status = memory.get_memory_health_status()
    print(f"Current backend: {memory.get_current_backend()}")
```

### Advanced Configuration

```python
from .shared.memory_health import (
    create_memory_health_monitor,
    HealthMonitorConfig,
    BackendConfig,
    MemoryBackendType,
    FailoverStrategy
)

# Custom health monitoring configuration
config = HealthMonitorConfig(
    check_interval=15,                          # Check every 15 seconds
    cache_ttl=5,                               # Cache results for 5 seconds
    failover_strategy=FailoverStrategy.GRACEFUL,
    enable_auto_failover=True,
    enable_periodic_monitoring=True,
    log_backend_switches=True,
    emit_events=True
)

# Custom backend configurations
backends = [
    BackendConfig(
        backend_type=MemoryBackendType.NEO4J,
        priority=100,
        enabled=True,
        config={
            "uri": "bolt://localhost:7687",
            "user": "neo4j", 
            "password": "secure_password",
            "database": "gadugi"
        }
    ),
    BackendConfig(
        backend_type=MemoryBackendType.SQLITE,
        priority=80,
        enabled=True,
        config={
            "db_path": "/data/memory.db"
        }
    ),
    BackendConfig(
        backend_type=MemoryBackendType.IN_MEMORY,
        priority=40,
        enabled=True,
        config={}
    )
]

# Event handler for backend changes
def handle_backend_events(event_type: str, event_data: dict):
    if event_type == "backend_failover":
        print(f"FAILOVER: {event_data['from_backend']} -> {event_data['to_backend']}")

# Create monitor
monitor = create_memory_health_monitor(
    config=config,
    backends=backends,
    event_callback=handle_backend_events
)

# Use with context manager
async with monitor.health_monitoring_context():
    # Your application logic here
    pass
```

## Health Check Details

### Neo4j Health Check
- Tests database connection
- Validates authentication
- Executes test query: `RETURN 1 as test`
- Checks memory table accessibility
- Measures response time

```python
# Neo4j configuration
neo4j_config = {
    "uri": "bolt://localhost:7687",      # Connection URI
    "user": "neo4j",                     # Username
    "password": "gadugi123!",            # Password  
    "database": "neo4j"                  # Database name
}
```

### SQLite Health Check
- Verifies file access permissions
- Tests database connectivity
- Executes basic SQL query
- Checks memory table existence
- Measures file I/O performance

```python
# SQLite configuration
sqlite_config = {
    "db_path": ".claude/data/memory.db"  # Database file path
}
```

### Markdown Health Check
- Tests directory permissions
- Creates and reads test file
- Validates file system access
- Counts existing memory files
- Ensures read/write capabilities

```python
# Markdown configuration
markdown_config = {
    "base_dir": ".claude/memory/markdown"  # Base directory
}
```

### In-Memory Health Check
- Always returns healthy status
- Provides instant availability
- Used as final fallback option
- No external dependencies

## Failover Strategies

### Immediate Failover
```python
config = HealthMonitorConfig(
    failover_strategy=FailoverStrategy.IMMEDIATE
)
```
- Switches to backup backend on first failure
- Fastest failover time
- May be aggressive for temporary issues

### Retry Then Switch
```python 
config = HealthMonitorConfig(
    failover_strategy=FailoverStrategy.RETRY_THEN_SWITCH
)
```
- Retries failed backend several times
- Switches only after repeated failures
- Balances reliability with stability

### Graceful Failover
```python
config = HealthMonitorConfig(
    failover_strategy=FailoverStrategy.GRACEFUL  
)
```
- Waits for ongoing operations to complete
- Smoothest transition experience
- Slower but most reliable

## Status and Monitoring

### Health Status API

```python
# Get comprehensive status
status = monitor.get_status()

{
    "current_backend": "neo4j",
    "failover_count": 0,
    "last_failover": null,
    "monitoring_enabled": true,
    "auto_failover_enabled": true,
    "backends": {
        "neo4j": {
            "status": "healthy",
            "response_time_ms": 12.5,
            "last_checked": "2024-01-15T10:30:00Z",
            "error": null,
            "details": {
                "uri": "bolt://localhost:7687",
                "database": "neo4j",
                "memory_count": 1543
            }
        },
        "sqlite": {
            "status": "healthy", 
            "response_time_ms": 2.1,
            "last_checked": "2024-01-15T10:30:00Z",
            "error": null,
            "details": {
                "db_path": ".claude/data/memory.db",
                "file_size_bytes": 2048576,
                "memory_count": 1543
            }
        }
    },
    "timestamp": "2024-01-15T10:30:15Z"
}
```

### Force Health Check

```python
# Trigger immediate health check
health_results = await monitor.check_all_backends_health()

for backend_type, result in health_results.items():
    print(f"{backend_type.value}: {result.status.value} ({result.response_time_ms:.1f}ms)")
```

### Manual Failover

```python
# Manually trigger failover
success = await monitor.handle_backend_failure(MemoryBackendType.NEO4J)
if success:
    print(f"Failover successful, new backend: {monitor.current_backend_type.value}")
```

## Error Handling and Recovery

### Automatic Retry with Failover

```python
async with memory_with_health_monitoring("agent_id") as memory:
    try:
        # This automatically retries with failover if backend fails
        memory_id = await memory.remember_short_term(
            "Important data",
            retry_on_failure=True  # Enable automatic retry
        )
    except Exception as e:
        # All backends failed
        logger.error(f"Memory operation failed completely: {e}")
```

### Emergency Recovery

```python
# Health-aware agent with emergency handling
agent = HealthAwareMemoryAgent("emergency_agent")
await agent.initialize()

# Handle memory system emergency
if await agent.handle_memory_emergency():
    print("Emergency recovery successful")
else:
    print("Emergency recovery failed")
```

### Diagnostics

```python
async with memory_with_health_monitoring("diagnostic_agent") as memory:
    # Run comprehensive diagnostics
    diagnostics = await memory.run_memory_diagnostics()
    
    print(f"Health monitoring: {diagnostics['health_monitoring_enabled']}")
    print(f"Backend health: {diagnostics['backend_health']}")
    print(f"Connection test: {diagnostics['connection_test']}")
    print(f"Memory operations: {diagnostics['memory_operations_test']}")
```

## Environment Variables

Configure the system using environment variables:

```bash
# Neo4j Configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="gadugi123!"
export NEO4J_DATABASE="neo4j"

# SQLite Configuration  
export SQLITE_DB_PATH=".claude/data/memory.db"

# Markdown Configuration
export MARKDOWN_DIR=".claude/memory/markdown"

# Health Check Configuration
export MEMORY_HEALTH_CHECK_INTERVAL="30"
export MEMORY_HEALTH_CACHE_TTL="10"
export MEMORY_ENABLE_AUTO_FAILOVER="true"
export MEMORY_ENABLE_MONITORING="true"
```

## Integration Examples

### With Existing Memory System

```python
from .shared.memory_health_integration import HealthAwareMemoryInterface

class MyAgent:
    def __init__(self):
        # Replace standard interface with health-aware version
        self.memory = HealthAwareMemoryInterface(
            agent_id="my_agent",
            enable_health_monitoring=True,
            health_check_interval=30,
            auto_failover=True
        )
    
    async def work(self):
        async with self.memory:
            # All memory operations now have health monitoring
            await self.memory.remember_short_term("Working...")
            memories = await self.memory.recall_memories()
```

### With Event System

```python
def memory_event_handler(event_type: str, event_data: dict):
    if event_type == "backend_failover":
        # Notify monitoring system
        send_alert(f"Memory failover: {event_data}")
    elif event_type == "backend_recovery": 
        # Log recovery
        log_info(f"Backend recovered: {event_data}")

monitor = create_memory_health_monitor(
    event_callback=memory_event_handler
)
```

### With Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_health")

monitor = create_memory_health_monitor(logger=logger)

# Log levels:
# INFO: Normal operations, failovers
# WARNING: Backend health issues
# ERROR: Complete system failures  
# DEBUG: Detailed health check results
```

## Best Practices

### 1. Backend Priority Configuration
- Set Neo4j as highest priority for complex relationships
- Use SQLite for structured data with good performance
- Configure Markdown for human-readable persistence
- Keep In-Memory as lowest priority fallback

### 2. Health Check Intervals
- Use 30-60 seconds for production systems
- Use 10-15 seconds for critical applications
- Use 5-10 seconds for development/testing
- Consider backend load and response times

### 3. Failover Strategy Selection
- Use IMMEDIATE for critical systems requiring high availability
- Use RETRY_THEN_SWITCH for balanced reliability and stability
- Use GRACEFUL for systems where consistency is most important

### 4. Event Handling
- Always implement event handlers for production systems
- Log all failover events for debugging
- Consider integrating with monitoring systems
- Set up alerts for repeated failovers

### 5. Error Handling
- Always enable retry_on_failure for critical operations
- Implement graceful degradation in your application
- Have fallback logic for complete memory system failure
- Monitor and alert on error rates

### 6. Testing and Validation
- Test failover scenarios in development
- Validate backend configurations before deployment
- Use diagnostics tools to verify system health
- Implement health checks in CI/CD pipelines

## Troubleshooting

### Common Issues

#### Backend Not Available
```python
# Check backend status
status = monitor.get_status()
for backend, info in status['backends'].items():
    if info['status'] != 'healthy':
        print(f"Issue with {backend}: {info['error']}")
```

#### Frequent Failovers
```python
# Check failover frequency
if status['failover_count'] > expected_limit:
    # Investigate backend stability
    # Check network connectivity
    # Review resource usage
    # Adjust health check intervals
```

#### Slow Response Times
```python
# Monitor response times
for backend, info in status['backends'].items():
    if info['response_time_ms'] > 1000:  # Slow threshold
        print(f"{backend} is responding slowly: {info['response_time_ms']}ms")
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger("memory_health").setLevel(logging.DEBUG)

# Get detailed diagnostics
diagnostics = await memory.run_memory_diagnostics()
print(json.dumps(diagnostics, indent=2))
```

## Performance Considerations

### Health Check Overhead
- Health checks consume minimal resources (~1-5ms per check)
- Caching reduces redundant checks
- Concurrent checks minimize impact
- Configurable intervals balance monitoring and performance

### Failover Impact
- Failover typically completes in <100ms
- In-memory backend provides instant availability
- Connection pooling reduces setup time
- Graceful failover minimizes operation interruption

### Memory Usage
- Health monitor uses ~1-5MB RAM
- Backend connections cached efficiently
- Minimal persistent storage requirements
- Scales well with agent count

## Security Considerations

### Connection Security
- Use encrypted connections (TLS/SSL) for Neo4j
- Secure file permissions for SQLite databases
- Protect Markdown directories appropriately
- Store credentials in environment variables

### Access Control
- Implement proper authentication for backends
- Use minimal required permissions
- Audit access patterns and failures
- Monitor for unauthorized access attempts

### Data Protection
- Encrypt sensitive data before storage
- Use secure credential management
- Implement data retention policies
- Follow organizational security guidelines

---

For additional help or questions about the Memory Health Check System, please refer to the source code documentation or contact the Gadugi development team.