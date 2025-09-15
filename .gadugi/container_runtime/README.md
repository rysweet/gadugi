# Container Execution Environment for Gadugi

A secure, containerized execution environment for the Gadugi multi-agent system that replaces direct shell execution with isolated container boundaries.

## Overview

The Container Execution Environment provides:

- **Security Isolation**: Execute code in completely isolated containers
- **Resource Management**: Configurable CPU, memory, disk, and network limits
- **Multiple Runtimes**: Support for Python, Node.js, Shell, and multi-language execution
- **Security Policies**: Comprehensive security policies with different levels of restriction
- **Audit Logging**: Complete audit trail of all execution activities
- **Enhanced Separation**: Integration with Gadugi's Enhanced Separation architecture

## Architecture

### Core Components

1. **ContainerManager**: Docker container lifecycle management
2. **SecurityPolicyEngine**: Security policy definition and enforcement
3. **ResourceManager**: Resource monitoring and limit enforcement
4. **AuditLogger**: Comprehensive audit logging
5. **ImageManager**: Secure container image building and management
6. **ExecutionEngine**: Main execution interface

### Security Features

- **Container Isolation**: Processes run in isolated containers with no host access
- **Resource Limits**: Strict CPU, memory, disk, and process limits
- **Security Hardening**: Read-only filesystems, dropped capabilities, non-root users
- **Network Isolation**: No network access by default, configurable exceptions
- **Audit Trail**: Complete logging of all execution activities
- **Policy Enforcement**: Configurable security policies for different contexts

## Installation

### Prerequisites

- Docker or containerd runtime
- Python 3.11+
- (Optional) Trivy for security scanning

### Setup

1. Install Docker:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io

# macOS with Homebrew
brew install docker

# Start Docker daemon
sudo systemctl start docker
```

2. Install Trivy (optional, for security scanning):
```bash
# Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# macOS with Homebrew
brew install trivy
```

3. Install Python dependencies:
```bash
pip install docker psutil
```

## Usage

### Basic Usage

```python
from container_runtime import ContainerExecutionEngine

# Initialize execution engine
engine = ContainerExecutionEngine()

# Execute Python code
response = engine.execute_python_code("""
print("Hello from containerized Python!")
import sys
print(f"Python version: {sys.version}")
""")

print(f"Exit code: {response.exit_code}")
print(f"Output: {response.stdout}")
```

### Security Policies

The system includes several built-in security policies:

- **minimal**: Basic isolation with relaxed restrictions
- **standard**: Default policy with balanced security and usability
- **hardened**: Enhanced security with strict restrictions
- **paranoid**: Maximum security with minimal capabilities

```python
# Use different security policies
response = engine.execute_python_code(
    code="print('Secure execution')",
    security_policy="hardened"
)
```

### Custom Security Policies

Define custom policies in YAML:

```yaml
policies:
  custom_policy:
    security_level: "hardened"
    network_policy: "none"
    resources:
      memory: "128m"
      cpu: "0.25"
      execution_time: 300
    security:
      read_only_root: true
      user_id: 65534
    allowed_images:
      - "python:3.11-slim"
    blocked_commands:
      - "sudo"
      - "wget"
```

### Agent-Manager Integration

Replace shell execution with containerized execution:

```python
from container_runtime.agent_integration import create_agent_executor

# Create agent executor
executor = create_agent_executor("standard")

# Execute shell script
result = executor.execute_script("/path/to/script.sh")

# Execute command
result = executor.execute_command(["python", "-c", "print('hello')"])

# Execute Python code with packages
result = executor.execute_python_code(
    code="import requests; print(requests.__version__)",
    packages=["requests"]
)
```

## Security Policies

### Built-in Policies

#### Minimal Policy
- **Use Case**: Development and testing
- **Memory**: 256MB
- **CPU**: 0.5 cores
- **Network**: None
- **Root Filesystem**: Read-write
- **User**: 1000:1000

#### Standard Policy (Default)
- **Use Case**: General purpose execution
- **Memory**: 512MB
- **CPU**: 1.0 core
- **Network**: None
- **Root Filesystem**: Read-only
- **User**: 1000:1000

#### Hardened Policy
- **Use Case**: Production environments
- **Memory**: 256MB
- **CPU**: 0.5 cores
- **Network**: None
- **Root Filesystem**: Read-only
- **User**: 65534:65534 (nobody)
- **Additional**: Seccomp profile, capability dropping

#### Paranoid Policy
- **Use Case**: Untrusted code execution
- **Memory**: 128MB
- **CPU**: 0.25 cores
- **Network**: None
- **Root Filesystem**: Read-only
- **User**: 65534:65534 (nobody)
- **Additional**: Maximum security restrictions

### Custom Policies

Located in `container_runtime/config/security_policies.yaml`:

- **development**: Relaxed policy for development work
- **testing**: Policy optimized for automated testing
- **production**: Maximum security for production
- **cicd**: Policy for CI/CD environments
- **sandbox**: Ultra-secure policy for untrusted code
- **demo**: Simplified policy for demonstrations

## Resource Management

### Resource Limits

All containers are subject to resource limits:

- **Memory**: Configurable memory limits (default: 512MB)
- **CPU**: CPU core limits (default: 1.0 core)
- **Disk**: Temporary disk space limits
- **Processes**: Maximum number of processes
- **Execution Time**: Maximum execution time (default: 30 minutes)

### Resource Monitoring

Real-time resource monitoring with alerts:

```python
# Get system status
status = engine.get_execution_statistics()
print(f"Active executions: {status['active_executions']}")
print(f"System CPU: {status['system_usage']['cpu_percent']}%")

# Get security alerts
alerts = engine.get_security_alerts()
for alert in alerts:
    print(f"ALERT: {alert.message}")
```

## Audit Logging

Comprehensive audit logging tracks all execution activities:

### Audit Events

- Container creation and execution
- Security policy application
- Resource limit violations
- Security violations
- Access denied events

### Audit Search

```python
from datetime import datetime, timedelta
from container_runtime.audit_logger import AuditEventType

# Search recent security violations
recent_violations = engine.audit_logger.search_events(
    event_type=AuditEventType.SECURITY_VIOLATION,
    start_time=datetime.now() - timedelta(hours=24)
)
```

## Image Management

### Runtime Images

The system automatically creates hardened runtime images:

- **Python**: Based on python:3.11-slim with security hardening
- **Node.js**: Based on node:18-alpine with security hardening
- **Shell**: Based on alpine:latest with minimal tools
- **Multi**: Ubuntu-based image with multiple runtimes

### Security Scanning

Automatic vulnerability scanning with Trivy:

```python
# Get security summary
security_summary = engine.image_manager.get_security_summary()
print(f"Images scanned: {security_summary['scanned_images']}")
print(f"Average security score: {security_summary['average_security_score']}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/container_runtime/

# Run specific test categories
pytest tests/container_runtime/test_container_manager.py
pytest tests/container_runtime/test_security_policy.py

# Run with coverage
pytest --cov=container_runtime tests/container_runtime/
```

## Performance

### Benchmarks

Typical performance characteristics:

- **Container Startup**: <5 seconds for cached images
- **Memory Overhead**: <2MB for monitoring and management
- **CPU Overhead**: <5% for resource monitoring
- **Throughput**: 10+ concurrent containers on standard hardware

### Optimization

Performance optimizations:

- Container image caching and reuse
- Efficient resource monitoring
- Lazy initialization of components
- Cleanup of unused resources

## Monitoring

### System Monitoring

Monitor system resources and container health:

```python
# Get resource usage summary
usage = engine.resource_manager.get_usage_summary()
print(f"Total containers: {usage['total_containers']}")
print(f"Total CPU usage: {usage['total_cpu_percent']}%")
print(f"Total memory: {usage['total_memory_mb']} MB")
```

### Alerting

Resource alerts for critical situations:

- CPU usage > 95%
- Memory usage > 95%
- Disk usage > 95%
- Container failures
- Security violations

## Troubleshooting

### Common Issues

#### Docker Connection Failed
```
Error: Failed to connect to Docker daemon
```
**Solution**: Ensure Docker daemon is running and accessible

#### Image Build Failed
```
Error: Failed to build image
```
**Solution**: Check Docker image availability and network connectivity

#### Resource Limit Exceeded
```
Error: Container killed due to memory limit
```
**Solution**: Increase memory limit in security policy

#### Permission Denied
```
Error: Permission denied accessing Docker socket
```
**Solution**: Add user to docker group or run with appropriate permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
engine = ContainerExecutionEngine()
```

### Log Files

Log locations:

- **Audit Logs**: `logs/audit/audit_YYYYMMDD_HHMMSS.jsonl`
- **System Logs**: Standard Python logging
- **Container Logs**: Captured in execution results

## Security Considerations

### Container Escape Prevention

- Read-only root filesystems
- Dropped Linux capabilities
- Non-root user execution
- Resource limits
- Seccomp and AppArmor profiles

### Network Security

- No network access by default
- Configurable network policies
- DNS restrictions
- Firewall rules

### Data Protection

- Temporary filesystem usage
- Automatic cleanup
- Input/output isolation
- Secret management

### Compliance

- Complete audit trail
- Policy enforcement
- Access controls
- Security scanning

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the GitHub repository
- Review the troubleshooting guide
- Check the audit logs for detailed error information
- Enable debug logging for detailed diagnostics
