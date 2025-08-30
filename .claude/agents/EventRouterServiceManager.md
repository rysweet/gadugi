---
name: EventRouterServiceManager
model: inherit
description: Manages the event router service for inter-agent communication, event distribution, and message routing
tools: Read, Write, Edit, Bash, Grep, TodoWrite
---

# Event Router Service Manager Agent


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
Manages the Gadugi v0.3 Event Router service lifecycle. Handles HTTP server operations, webhook endpoints, local Unix socket server, and GitHub polling functionality.

## Core Capabilities
- Monitor Event Router service health
- Start/stop/restart Event Router service
- Test webhook endpoints and Unix socket
- Monitor GitHub polling and webhook processing
- Handle service configuration and logging
- Provide detailed service diagnostics

## Service Configuration
- **Service Name**: `gadugi-event-service`
- **HTTP Port**: 8000 (default, configurable)
- **Unix Socket**: `/tmp/gadugi-events.sock` (configurable)
- **GitHub Webhook**: `/webhook/github`
- **Health Check**: `/health`
- **Module**: `gadugi.event_service.service`

## Service Architecture
```
Event Router Service
├── HTTP Server (Webhooks)
│   ├── GitHub webhook endpoint
│   ├── Health check endpoint
│   └── Admin endpoints
├── Unix Socket Server (Local Events)
│   ├── Local agent communication
│   └── Internal event submission
├── GitHub Polling (Fallback)
│   ├── API polling when webhooks fail
│   └── Event deduplication
└── Event Processing
    ├── Event filtering
    ├── Handler matching
    └── Agent invocation
```

## Implementation

### Service Status Check
```python
#!/usr/bin/env python3
"""
Event Router Service Manager - Status Check Implementation
"""
import asyncio
import json
import socket
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import psutil
import time

def check_event_router_status() -> Dict[str, Any]:
    """Check comprehensive Event Router service status."""
    status = {
        "service": "event-router",
        "overall_status": "UNKNOWN",
        "components": {
            "process": check_process_status(),
            "http_server": check_http_server(),
            "unix_socket": check_unix_socket(),
            "github_api": check_github_api_access()
        },
        "endpoints": {},
        "performance": {},
        "message": ""
    }

    # Determine overall status
    component_statuses = [comp["status"] for comp in status["components"].values()]

    if all(s == "HEALTHY" for s in component_statuses):
        status["overall_status"] = "HEALTHY"
        status["message"] = "Event Router fully operational"
    elif any(s == "HEALTHY" for s in component_statuses):
        status["overall_status"] = "DEGRADED"
        status["message"] = "Event Router partially operational"
    else:
        status["overall_status"] = "DOWN"
        status["message"] = "Event Router not responding"

    return status

def check_process_status() -> Dict[str, Any]:
    """Check if Event Router process is running."""
    try:
        # Look for the event service process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'gadugi.event_service' in cmdline or 'event_service.service' in cmdline:
                return {
                    "status": "HEALTHY",
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cmdline": cmdline,
                    "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                    "cpu_percent": proc.cpu_percent(),
                    "message": f"Process running (PID: {proc.info['pid']})"
                }

        return {
            "status": "DOWN",
            "message": "Event Router process not found"
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "message": f"Process check failed: {str(e)}"
        }

def check_http_server(port: int = 8000) -> Dict[str, Any]:
    """Check HTTP server status and endpoints."""
    try:
        # Test health endpoint
        health_url = f"http://localhost:{port}/health"
        response = requests.get(health_url, timeout=5)

        if response.status_code == 200:
            health_data = response.json()
            return {
                "status": "HEALTHY",
                "port": port,
                "health_endpoint": health_url,
                "health_data": health_data,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                "message": "HTTP server responding normally"
            }
        else:
            return {
                "status": "UNHEALTHY",
                "port": port,
                "http_status": response.status_code,
                "message": f"HTTP server returned status {response.status_code}"
            }

    except requests.exceptions.ConnectionError:
        return {
            "status": "DOWN",
            "port": port,
            "message": "HTTP server not responding (connection refused)"
        }
    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "port": port,
            "message": "HTTP server timeout"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "port": port,
            "error": str(e),
            "message": f"HTTP check failed: {str(e)}"
        }

def check_unix_socket(socket_path: str = "/tmp/gadugi-events.sock") -> Dict[str, Any]:
    """Check Unix socket server status."""
    try:
        socket_file = Path(socket_path)

        if not socket_file.exists():
            return {
                "status": "DOWN",
                "path": socket_path,
                "message": "Unix socket file does not exist"
            }

        # Test socket connection
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect(socket_path)

            # Send test event
            test_event = {
                "event_id": "test-connection",
                "event_type": "system.test",
                "timestamp": int(time.time()),
                "source": "service-manager",
                "payload": {"test": True}
            }

            sock.send(json.dumps(test_event).encode('utf-8'))
            response = sock.recv(1024)
            sock.close()

            if response:
                response_data = json.loads(response.decode('utf-8'))
                return {
                    "status": "HEALTHY",
                    "path": socket_path,
                    "test_response": response_data,
                    "message": "Unix socket responding normally"
                }
            else:
                return {
                    "status": "UNHEALTHY",
                    "path": socket_path,
                    "message": "Unix socket connected but no response"
                }

        except socket.timeout:
            return {
                "status": "TIMEOUT",
                "path": socket_path,
                "message": "Unix socket connection timeout"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "path": socket_path,
                "error": str(e),
                "message": f"Unix socket test failed: {str(e)}"
            }
        finally:
            try:
                sock.close()
            except:
                pass

    except Exception as e:
        return {
            "status": "ERROR",
            "path": socket_path,
            "error": str(e),
            "message": f"Unix socket check failed: {str(e)}"
        }

def check_github_api_access() -> Dict[str, Any]:
    """Check GitHub API access for polling."""
    try:
        # Test GitHub API access
        response = requests.get("https://api.github.com/rate_limit", timeout=10)

        if response.status_code == 200:
            rate_limit_data = response.json()
            return {
                "status": "HEALTHY",
                "api_accessible": True,
                "rate_limit": rate_limit_data.get("rate", {}),
                "message": "GitHub API accessible"
            }
        else:
            return {
                "status": "DEGRADED",
                "api_accessible": False,
                "http_status": response.status_code,
                "message": f"GitHub API returned status {response.status_code}"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "api_accessible": False,
            "error": str(e),
            "message": f"GitHub API check failed: {str(e)}"
        }

def get_event_router_metrics() -> Dict[str, Any]:
    """Get detailed Event Router performance metrics."""
    metrics = {
        "uptime": "unknown",
        "processed_events": "unknown",
        "active_handlers": "unknown",
        "recent_errors": []
    }

    try:
        # Try to get metrics from health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            metrics.update({
                "uptime": health_data.get("uptime", "unknown"),
                "handlers": health_data.get("handlers", "unknown"),
                "version": health_data.get("version", "unknown")
            })
    except:
        pass

    return metrics
```

### Service Management
```python
def start_event_router_service(config_path: Optional[str] = None):
    """Start the Event Router service."""
    print("Starting Event Router Service...")

    # Check if already running
    status = check_process_status()
    if status["status"] == "HEALTHY":
        print(f"Service already running (PID: {status.get('pid')})")
        return True

    try:
        # Build command
        cmd = ["python", "-m", "gadugi.event_service.service"]
        if config_path:
            cmd.extend(["--config", config_path])

        # Start process in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )

        print(f"Started Event Router service (PID: {process.pid})")

        # Wait for service to be ready
        print("Waiting for service to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            http_status = check_http_server()
            if http_status["status"] == "HEALTHY":
                print("✅ HTTP server ready")
                break
            print(f"HTTP server status: {http_status['status']} (attempt {i+1}/30)")
        else:
            print("⚠️ HTTP server not ready within timeout")

        # Check Unix socket
        for i in range(10):  # Wait up to 10 seconds for socket
            time.sleep(1)
            socket_status = check_unix_socket()
            if socket_status["status"] == "HEALTHY":
                print("✅ Unix socket ready")
                break
            print(f"Unix socket status: {socket_status['status']} (attempt {i+1}/10)")
        else:
            print("⚠️ Unix socket not ready within timeout")

        print("Event Router Service started successfully")
        return True

    except Exception as e:
        print(f"ERROR: Failed to start Event Router service: {e}")
        return False

def stop_event_router_service():
    """Stop the Event Router service."""
    print("Stopping Event Router Service...")

    try:
        # Find and terminate the process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'gadugi.event_service' in cmdline or 'event_service.service' in cmdline:
                print(f"Terminating process {proc.info['pid']}")
                proc.terminate()

                # Wait for graceful shutdown
                try:
                    proc.wait(timeout=10)
                    print("Process terminated gracefully")
                except psutil.TimeoutExpired:
                    print("Process did not terminate gracefully, killing...")
                    proc.kill()
                    proc.wait()

                # Clean up Unix socket
                socket_path = Path("/tmp/gadugi-events.sock")
                if socket_path.exists():
                    socket_path.unlink()
                    print("Unix socket cleaned up")

                print("Event Router Service stopped successfully")
                return True

        print("No Event Router process found to stop")
        return True

    except Exception as e:
        print(f"ERROR: Failed to stop Event Router service: {e}")
        return False

def restart_event_router_service(config_path: Optional[str] = None):
    """Restart the Event Router service."""
    print("Restarting Event Router Service...")

    if stop_event_router_service():
        time.sleep(2)  # Brief pause
        return start_event_router_service(config_path)
    else:
        return False
```

### Event Testing
```python
def test_event_submission():
    """Test event submission through various channels."""
    print("=== Event Router Test Suite ===")

    results = {
        "webhook_endpoint": test_webhook_endpoint(),
        "unix_socket": test_unix_socket_submission(),
        "health_endpoint": test_health_endpoint()
    }

    # Summary
    print("\nTest Results:")
    for test_name, result in results.items():
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {test_name}: {result['message']}")

    return results

def test_webhook_endpoint():
    """Test GitHub webhook endpoint."""
    try:
        test_payload = {
            "action": "opened",
            "issue": {
                "number": 1,
                "title": "Test Issue",
                "body": "Test issue for service validation"
            },
            "repository": {
                "full_name": "test/repo"
            },
            "sender": {
                "login": "test-user"
            }
        }

        response = requests.post(
            "http://localhost:8000/webhook/github",
            json=test_payload,
            headers={
                "X-GitHub-Event": "issues",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Webhook endpoint responding",
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "message": f"Webhook returned status {response.status_code}",
                "status_code": response.status_code
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Webhook test failed: {str(e)}",
            "error": str(e)
        }

def test_unix_socket_submission():
    """Test Unix socket event submission."""
    try:
        socket_path = "/tmp/gadugi-events.sock"

        if not Path(socket_path).exists():
            return {
                "success": False,
                "message": "Unix socket does not exist"
            }

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(10)

        try:
            sock.connect(socket_path)

            test_event = {
                "event_id": "test-" + str(int(time.time())),
                "event_type": "system.test",
                "timestamp": int(time.time()),
                "source": "service-manager-test",
                "payload": {
                    "test_data": "Event Router service test",
                    "timestamp": time.time()
                }
            }

            sock.send(json.dumps(test_event).encode('utf-8'))
            response = sock.recv(1024)

            if response:
                response_data = json.loads(response.decode('utf-8'))
                return {
                    "success": True,
                    "message": "Unix socket responding",
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "message": "Unix socket connected but no response"
                }

        finally:
            sock.close()

    except Exception as e:
        return {
            "success": False,
            "message": f"Unix socket test failed: {str(e)}",
            "error": str(e)
        }

def test_health_endpoint():
    """Test health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            health_data = response.json()
            return {
                "success": True,
                "message": "Health endpoint responding",
                "health_data": health_data
            }
        else:
            return {
                "success": False,
                "message": f"Health endpoint returned status {response.status_code}",
                "status_code": response.status_code
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Health endpoint test failed: {str(e)}",
            "error": str(e)
        }
```

## Bash Interface
```bash
#!/bin/bash
# Event Router Service Manager - Bash Interface

SERVICE_MANAGER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SERVICE_MANAGER_DIR/event_router_service_manager.py"

check_event_router_status() {
    echo "=== Event Router Service Status ==="
    python3 -c "
import sys
sys.path.append('$SERVICE_MANAGER_DIR')
from event_router_service_manager import check_event_router_status, get_event_router_metrics
import json

status = check_event_router_status()
print(f\"Overall Status: {status['overall_status']}\")
print(f\"Message: {status['message']}\")
print()

for comp_name, comp_info in status['components'].items():
    print(f\"{comp_name.upper().replace('_', ' ')}:\")
    print(f\"  Status: {comp_info['status']}\")
    print(f\"  Message: {comp_info['message']}\")
    if 'port' in comp_info:
        print(f\"  Port: {comp_info['port']}\")
    if 'pid' in comp_info:
        print(f\"  PID: {comp_info['pid']}\")
        print(f\"  Memory: {comp_info.get('memory_mb', 0)} MB\")
    print()

# Show metrics
metrics = get_event_router_metrics()
print(\"METRICS:\")
for key, value in metrics.items():
    print(f\"  {key}: {value}\")
"
}

start_event_router() {
    echo "Starting Event Router Service..."
    python3 -c "
import sys
sys.path.append('$SERVICE_MANAGER_DIR')
from event_router_service_manager import start_event_router_service
start_event_router_service()
"
}

stop_event_router() {
    echo "Stopping Event Router Service..."
    python3 -c "
import sys
sys.path.append('$SERVICE_MANAGER_DIR')
from event_router_service_manager import stop_event_router_service
stop_event_router_service()
"
}

restart_event_router() {
    echo "Restarting Event Router Service..."
    python3 -c "
import sys
sys.path.append('$SERVICE_MANAGER_DIR')
from event_router_service_manager import restart_event_router_service
restart_event_router_service()
"
}

test_event_router() {
    echo "Testing Event Router Service..."
    python3 -c "
import sys
sys.path.append('$SERVICE_MANAGER_DIR')
from event_router_service_manager import test_event_submission
test_event_submission()
"
}

# Command dispatch
case "${1:-status}" in
    "status")
        check_event_router_status
        ;;
    "start")
        start_event_router
        ;;
    "stop")
        stop_event_router
        ;;
    "restart")
        restart_event_router
        ;;
    "test")
        test_event_router
        ;;
    *)
        echo "Usage: $0 {status|start|stop|restart|test}"
        exit 1
        ;;
esac
```

## Environment Variables

### Service Configuration
- `GADUGI_EVENT_PORT` - HTTP server port (default: 8000)
- `GADUGI_EVENT_BIND` - Bind address (default: 127.0.0.1)
- `GADUGI_EVENT_SOCKET` - Unix socket path
- `GADUGI_EVENT_CONFIG` - Configuration file path

### GitHub Integration
- `GITHUB_TOKEN` - GitHub API token
- `GADUGI_WEBHOOK_SECRET` - Webhook signature secret
- `GADUGI_POLL_INTERVAL` - GitHub polling interval (seconds)

### Monitoring
- `GADUGI_EVENT_LOG_LEVEL` - Log level (DEBUG/INFO/WARNING/ERROR)
- `GADUGI_EVENT_LOG_FILE` - Log file path
- `GADUGI_EVENT_METRICS` - Enable metrics collection

## Integration with Gadugi Coordinator

### JSON Status Output
```json
{
  "service": "event-router",
  "overall_status": "HEALTHY|DEGRADED|DOWN",
  "components": {
    "process": {
      "status": "HEALTHY",
      "pid": 12345,
      "memory_mb": 45.2,
      "cpu_percent": 2.1
    },
    "http_server": {
      "status": "HEALTHY",
      "port": 8000,
      "response_time_ms": 15.3
    },
    "unix_socket": {
      "status": "HEALTHY",
      "path": "/tmp/gadugi-events.sock"
    },
    "github_api": {
      "status": "HEALTHY",
      "api_accessible": true
    }
  },
  "endpoints": {
    "webhook": "http://localhost:8000/webhook/github",
    "health": "http://localhost:8000/health",
    "socket": "/tmp/gadugi-events.sock"
  },
  "metrics": {
    "uptime": "2h 15m 30s",
    "handlers": 5,
    "version": "0.3.0"
  },
  "message": "Event Router fully operational"
}
```

## Recovery Strategies

### Automatic Recovery
1. **Process Crash**: Automatic restart with exponential backoff
2. **Port Conflict**: Try alternative ports
3. **Socket Issues**: Clean up and recreate socket
4. **GitHub API Issues**: Fall back to local events only

### Manual Recovery
```bash
# Full service restart
./EventRouterServiceManager.md restart

# Clean restart (remove socket, logs)
rm -f /tmp/gadugi-events.sock
./EventRouterServiceManager.md restart

# Test all components
./EventRouterServiceManager.md test
```

This Event Router service manager provides comprehensive monitoring and management of the Gadugi event-driven architecture with full diagnostic capabilities.
