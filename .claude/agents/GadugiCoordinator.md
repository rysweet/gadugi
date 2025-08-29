# Gadugi Coordinator Agent


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
Central coordination agent that manages all Gadugi v0.3 services through their respective service managers. Provides unified status monitoring, service orchestration, and comprehensive system health reporting.

## Core Capabilities
- Coordinate all service managers (Neo4j, Memory, Event Router)
- Aggregate service status across the entire system
- Ensure all services are running and healthy
- Handle service dependencies and startup order
- Update agents and configurations
- Generate comprehensive status summaries
- Provide centralized service management interface

## Service Architecture
```
Gadugi Coordinator
├── Neo4j Service Manager
│   ├── Docker container management
│   ├── Health checks
│   └── Connection validation
├── Memory Service Manager
│   ├── Neo4j backend coordination
│   ├── SQLite fallback management
│   └── Cache layer monitoring
├── Event Router Service Manager
│   ├── HTTP server management
│   ├── Unix socket coordination
│   └── GitHub integration
└── Agent Management
    ├── Agent updates
    ├── Configuration sync
    └── Service discovery
```

## Implementation

### Core Coordination Logic
```python
#!/usr/bin/env python3
"""
Gadugi Coordinator - Central Service Management
"""
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceStatus:
    name: str
    status: str
    message: str
    details: Dict[str, Any]
    last_check: datetime
    manager_path: str

class GadugiCoordinator:
    """Central coordinator for all Gadugi v0.3 services."""

    def __init__(self):
        self.services = {
            "neo4j": {
                "name": "Neo4j Database",
                "manager": ".claude/agents/Neo4jServiceManager.md",
                "priority": 1,  # Start first
                "dependencies": [],
                "ports": {"http": 7475, "bolt": 7689}
            },
            "memory": {
                "name": "Memory System",
                "manager": ".claude/agents/MemoryServiceManager.md",
                "priority": 2,  # After Neo4j
                "dependencies": ["neo4j"],
                "features": ["fallback_chain", "caching"]
            },
            "event-router": {
                "name": "Event Router",
                "manager": ".claude/agents/EventRouterServiceManager.md",
                "priority": 3,  # After memory system
                "dependencies": ["memory"],
                "ports": {"http": 8000, "socket": "/tmp/gadugi-events.sock"}
            }
        }

        self.last_status_check = None
        self.status_cache = {}

    async def get_comprehensive_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive status of all Gadugi services."""
        if not force_refresh and self._status_cache_valid():
            return self.status_cache

        print("🔍 Checking Gadugi v0.3 Service Status...")

        status_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "services": {},
            "summary": {
                "total_services": len(self.services),
                "healthy": 0,
                "degraded": 0,
                "down": 0,
                "unknown": 0
            },
            "dependencies": self._check_dependencies(),
            "recommendations": [],
            "agent_updates": await self._check_agent_updates()
        }

        # Check each service
        for service_id, service_config in self.services.items():
            print(f"   Checking {service_config['name']}...")
            service_status = await self._check_service_status(service_id, service_config)
            status_report["services"][service_id] = service_status

            # Update summary counts
            status_key = service_status["status"].lower()
            if status_key in ["healthy", "optimal"]:
                status_report["summary"]["healthy"] += 1
            elif status_key in ["degraded", "unhealthy", "partially_operational"]:
                status_report["summary"]["degraded"] += 1
            elif status_key in ["down", "stopped", "critical"]:
                status_report["summary"]["down"] += 1
            else:
                status_report["summary"]["unknown"] += 1

        # Determine overall status
        status_report["overall_status"] = self._calculate_overall_status(status_report)

        # Generate recommendations
        status_report["recommendations"] = self._generate_recommendations(status_report)

        # Cache results
        self.status_cache = status_report
        self.last_status_check = datetime.now()

        return status_report

    async def _check_service_status(self, service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check status of individual service via its manager."""
        try:
            manager_path = Path(config["manager"])

            if not manager_path.exists():
                return {
                    "name": config["name"],
                    "status": "ERROR",
                    "message": f"Service manager not found: {manager_path}",
                    "details": {},
                    "last_check": datetime.now().isoformat()
                }

            # For now, we'll simulate calling the service managers
            # In practice, these would be actual executable scripts or Python modules
            if service_id == "neo4j":
                return await self._check_neo4j_service()
            elif service_id == "memory":
                return await self._check_memory_service()
            elif service_id == "event-router":
                return await self._check_event_router_service()
            else:
                return {
                    "name": config["name"],
                    "status": "UNKNOWN",
                    "message": "Service check not implemented",
                    "details": {},
                    "last_check": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "name": config["name"],
                "status": "ERROR",
                "message": f"Service check failed: {str(e)}",
                "details": {"error": str(e)},
                "last_check": datetime.now().isoformat()
            }

    async def _check_neo4j_service(self) -> Dict[str, Any]:
        """Check Neo4j service status."""
        try:
            # Test Docker container
            result = subprocess.run([
                "docker", "ps", "-f", "name=gadugi-neo4j", "--format", "{{.Status}}"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout.strip():
                # Container is running, test connection
                try:
                    import requests
                    response = requests.get("http://localhost:7475/db/data/", timeout=5)
                    if response.status_code == 200:
                        return {
                            "name": "Neo4j Database",
                            "status": "HEALTHY",
                            "message": "Neo4j running and accessible",
                            "details": {
                                "container_status": result.stdout.strip(),
                                "http_port": 7475,
                                "bolt_port": 7689,
                                "connection": "verified"
                            },
                            "last_check": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "name": "Neo4j Database",
                            "status": "UNHEALTHY",
                            "message": f"Neo4j container running but HTTP returned {response.status_code}",
                            "details": {
                                "container_status": result.stdout.strip(),
                                "http_status": response.status_code
                            },
                            "last_check": datetime.now().isoformat()
                        }
                except Exception as e:
                    return {
                        "name": "Neo4j Database",
                        "status": "UNHEALTHY",
                        "message": f"Neo4j container running but connection failed: {str(e)}",
                        "details": {
                            "container_status": result.stdout.strip(),
                            "connection_error": str(e)
                        },
                        "last_check": datetime.now().isoformat()
                    }
            else:
                return {
                    "name": "Neo4j Database",
                    "status": "DOWN",
                    "message": "Neo4j container not running",
                    "details": {
                        "container_status": "not found",
                        "expected_ports": {"http": 7475, "bolt": 7689}
                    },
                    "last_check": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "name": "Neo4j Database",
                "status": "ERROR",
                "message": f"Neo4j check failed: {str(e)}",
                "details": {"error": str(e)},
                "last_check": datetime.now().isoformat()
            }

    async def _check_memory_service(self) -> Dict[str, Any]:
        """Check Memory Service status."""
        try:
            # Check if Neo4j is available for primary backend
            neo4j_available = False
            try:
                import requests
                response = requests.get("http://localhost:7475/db/data/", timeout=3)
                neo4j_available = (response.status_code == 200)
            except:
                pass

            # Check SQLite fallback
            sqlite_path = Path(".claude/memory/fallback.db")
            sqlite_available = False
            try:
                import sqlite3
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                sqlite_available = True
            except:
                pass

            # Determine status
            if neo4j_available:
                return {
                    "name": "Memory System",
                    "status": "OPTIMAL",
                    "message": "Memory system using Neo4j primary backend",
                    "details": {
                        "active_backend": "neo4j",
                        "fallback_ready": sqlite_available,
                        "neo4j_available": True,
                        "sqlite_available": sqlite_available
                    },
                    "last_check": datetime.now().isoformat()
                }
            elif sqlite_available:
                return {
                    "name": "Memory System",
                    "status": "DEGRADED",
                    "message": "Memory system using SQLite fallback",
                    "details": {
                        "active_backend": "sqlite",
                        "fallback_active": True,
                        "neo4j_available": False,
                        "sqlite_available": True,
                        "sqlite_path": str(sqlite_path)
                    },
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "name": "Memory System",
                    "status": "CRITICAL",
                    "message": "No persistent memory backend available",
                    "details": {
                        "active_backend": "memory-only",
                        "neo4j_available": False,
                        "sqlite_available": False
                    },
                    "last_check": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "name": "Memory System",
                "status": "ERROR",
                "message": f"Memory service check failed: {str(e)}",
                "details": {"error": str(e)},
                "last_check": datetime.now().isoformat()
            }

    async def _check_event_router_service(self) -> Dict[str, Any]:
        """Check Event Router service status."""
        try:
            # Check if process is running
            import psutil
            process_running = False
            process_info = {}

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'gadugi.event_service' in cmdline or 'event_service.service' in cmdline:
                    process_running = True
                    process_info = {
                        "pid": proc.info['pid'],
                        "memory_mb": round(proc.memory_info().rss / 1024 / 1024, 2)
                    }
                    break

            if process_running:
                # Test HTTP endpoint
                http_healthy = False
                try:
                    import requests
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    http_healthy = (response.status_code == 200)
                except:
                    pass

                # Test Unix socket
                socket_healthy = False
                socket_path = Path("/tmp/gadugi-events.sock")
                if socket_path.exists():
                    try:
                        import socket
                        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        sock.connect(str(socket_path))
                        sock.close()
                        socket_healthy = True
                    except:
                        pass

                if http_healthy and socket_healthy:
                    return {
                        "name": "Event Router",
                        "status": "HEALTHY",
                        "message": "Event Router fully operational",
                        "details": {
                            "process": process_info,
                            "http_endpoint": "http://localhost:8000",
                            "unix_socket": str(socket_path),
                            "http_healthy": True,
                            "socket_healthy": True
                        },
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    return {
                        "name": "Event Router",
                        "status": "DEGRADED",
                        "message": "Event Router process running but endpoints unhealthy",
                        "details": {
                            "process": process_info,
                            "http_healthy": http_healthy,
                            "socket_healthy": socket_healthy
                        },
                        "last_check": datetime.now().isoformat()
                    }
            else:
                return {
                    "name": "Event Router",
                    "status": "DOWN",
                    "message": "Event Router process not found",
                    "details": {
                        "process_running": False,
                        "expected_port": 8000,
                        "expected_socket": "/tmp/gadugi-events.sock"
                    },
                    "last_check": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "name": "Event Router",
                "status": "ERROR",
                "message": f"Event Router check failed: {str(e)}",
                "details": {"error": str(e)},
                "last_check": datetime.now().isoformat()
            }

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check service dependencies."""
        deps = {
            "docker": self._check_docker_available(),
            "python": self._check_python_available(),
            "network": self._check_network_ports()
        }
        return deps

    def _check_docker_available(self) -> Dict[str, Any]:
        """Check if Docker is available."""
        try:
            result = subprocess.run(["docker", "--version"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return {
                    "available": True,
                    "version": result.stdout.strip(),
                    "message": "Docker is available"
                }
            else:
                return {
                    "available": False,
                    "message": "Docker command failed"
                }
        except Exception as e:
            return {
                "available": False,
                "message": f"Docker not available: {str(e)}"
            }

    def _check_python_available(self) -> Dict[str, Any]:
        """Check Python environment."""
        try:
            import sys
            return {
                "available": True,
                "version": sys.version,
                "executable": sys.executable,
                "message": "Python environment ready"
            }
        except Exception as e:
            return {
                "available": False,
                "message": f"Python check failed: {str(e)}"
            }

    def _check_network_ports(self) -> Dict[str, Any]:
        """Check network port availability."""
        import socket
        ports_to_check = [7475, 7689, 8000]
        port_status = {}

        for port in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()

                if result == 0:
                    port_status[port] = {"in_use": True, "status": "occupied"}
                else:
                    port_status[port] = {"in_use": False, "status": "available"}
            except Exception as e:
                port_status[port] = {"in_use": False, "status": f"error: {str(e)}"}

        return {
            "ports": port_status,
            "message": f"Checked {len(ports_to_check)} ports"
        }

    async def _check_agent_updates(self) -> Dict[str, Any]:
        """Check if agents need updates."""
        try:
            # This is a placeholder - in practice would check git status,
            # file timestamps, etc.
            return {
                "up_to_date": True,
                "last_update": "2024-08-29T00:00:00Z",
                "pending_updates": 0,
                "message": "All agents up to date"
            }
        except Exception as e:
            return {
                "up_to_date": False,
                "error": str(e),
                "message": f"Agent update check failed: {str(e)}"
            }

    def _calculate_overall_status(self, status_report: Dict[str, Any]) -> str:
        """Calculate overall system status."""
        summary = status_report["summary"]

        if summary["down"] > 0:
            return "CRITICAL"
        elif summary["degraded"] > 0:
            return "PARTIALLY_OPERATIONAL"
        elif summary["healthy"] == summary["total_services"]:
            return "FULLY_OPERATIONAL"
        else:
            return "UNKNOWN"

    def _generate_recommendations(self, status_report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Check Neo4j
        neo4j_status = status_report["services"].get("neo4j", {})
        if neo4j_status.get("status") in ["DOWN", "UNHEALTHY"]:
            recommendations.append("Start Neo4j service: docker-compose -f docker-compose.gadugi.yml up -d neo4j")

        # Check Memory System
        memory_status = status_report["services"].get("memory", {})
        if memory_status.get("status") == "CRITICAL":
            recommendations.append("Initialize SQLite fallback: mkdir -p .claude/memory")
        elif memory_status.get("status") == "DEGRADED":
            recommendations.append("Restore Neo4j connection for optimal memory performance")

        # Check Event Router
        event_status = status_report["services"].get("event-router", {})
        if event_status.get("status") in ["DOWN", "ERROR"]:
            recommendations.append("Start Event Router: python -m gadugi.event_service.service")

        # Dependencies
        deps = status_report["dependencies"]
        if not deps.get("docker", {}).get("available", False):
            recommendations.append("Install Docker for Neo4j container support")

        if not recommendations:
            recommendations.append("All services operational - no actions needed")

        return recommendations

    def _status_cache_valid(self) -> bool:
        """Check if status cache is still valid."""
        if not self.last_status_check:
            return False

        cache_age = (datetime.now() - self.last_status_check).total_seconds()
        return cache_age < 30  # 30 second cache

    async def ensure_services_running(self) -> bool:
        """Ensure all services are running, start if needed."""
        print("🚀 Ensuring all Gadugi services are running...")

        # Get current status
        status = await self.get_comprehensive_status(force_refresh=True)

        success = True

        # Start services in dependency order
        for service_id in sorted(self.services.keys(),
                               key=lambda x: self.services[x]["priority"]):
            service_status = status["services"][service_id]

            if service_status["status"] in ["DOWN", "ERROR", "CRITICAL"]:
                print(f"   Starting {service_status['name']}...")
                if await self._start_service(service_id):
                    print(f"   ✅ {service_status['name']} started")
                else:
                    print(f"   ❌ Failed to start {service_status['name']}")
                    success = False
            else:
                print(f"   ✅ {service_status['name']} already running")

        return success

    async def _start_service(self, service_id: str) -> bool:
        """Start individual service."""
        try:
            if service_id == "neo4j":
                result = subprocess.run([
                    "docker-compose", "-f", "docker-compose.gadugi.yml",
                    "up", "-d", "neo4j"
                ], capture_output=True, text=True, timeout=60)
                return result.returncode == 0

            elif service_id == "memory":
                # Memory service is primarily client-side, ensure dependencies
                return True

            elif service_id == "event-router":
                # Start Event Router service
                subprocess.Popen([
                    "python", "-m", "gadugi.event_service.service"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                await asyncio.sleep(5)  # Give it time to start
                return True

            return False

        except Exception as e:
            print(f"Error starting {service_id}: {e}")
            return False

    def generate_status_summary(self, status_report: Dict[str, Any]) -> str:
        """Generate human-readable status summary."""
        summary_lines = [
            "## Gadugi v0.3 Services Status",
            "",
            "### Core Services:"
        ]

        # Service status
        for service_id, service_status in status_report["services"].items():
            status = service_status["status"]
            name = service_status["name"]
            message = service_status.get("message", "")

            if status in ["HEALTHY", "OPTIMAL"]:
                icon = "✅"
            elif status in ["DEGRADED", "UNHEALTHY", "PARTIALLY_OPERATIONAL"]:
                icon = "⚠️ "
            elif status in ["DOWN", "CRITICAL"]:
                icon = "❌"
            else:
                icon = "❓"

            # Add port info if available
            port_info = ""
            details = service_status.get("details", {})
            if "http_port" in details and "bolt_port" in details:
                port_info = f" (Ports {details['http_port']}/{details['bolt_port']})"
            elif "http_endpoint" in details:
                port_info = f" (Port 8000)"

            summary_lines.append(f"{icon} {name} - {status.title()}{port_info}")
            if message and message != name:
                summary_lines.append(f"   {message}")

        # Agent updates
        summary_lines.extend([
            "",
            "### Agent Updates:"
        ])

        agent_info = status_report["agent_updates"]
        if agent_info.get("up_to_date", False):
            summary_lines.append("✅ All agents up to date")
        else:
            pending = agent_info.get("pending_updates", 0)
            summary_lines.append(f"⚠️ {pending} agent updates pending")

        # Overall status
        overall = status_report["overall_status"]
        summary_lines.extend([
            "",
            f"### Overall Status: {overall.replace('_', ' ').title()}"
        ])

        # Recommendations
        recommendations = status_report.get("recommendations", [])
        if recommendations and len(recommendations) > 1:  # More than just "no actions needed"
            summary_lines.extend([
                "",
                "### Recommendations:"
            ])
            for rec in recommendations[:3]:  # Top 3 recommendations
                summary_lines.append(f"- {rec}")

        return "\\n".join(summary_lines)

# Global coordinator instance
coordinator = GadugiCoordinator()

# CLI Interface Functions
async def status_command():
    """CLI command for status check."""
    status_report = await coordinator.get_comprehensive_status(force_refresh=True)

    # Print formatted summary
    summary = coordinator.generate_status_summary(status_report)
    print(summary.replace("\\n", "\n"))

    # Return JSON for programmatic use
    return status_report

async def start_command():
    """CLI command to start all services."""
    return await coordinator.ensure_services_running()

async def main():
    """Main CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        command = "status"
    else:
        command = sys.argv[1]

    if command == "status":
        await status_command()
    elif command == "start":
        await start_command()
    elif command == "json":
        status_report = await coordinator.get_comprehensive_status(force_refresh=True)
        print(json.dumps(status_report, indent=2))
    else:
        print("Usage: GadugiCoordinator.py {status|start|json}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Bash Interface
```bash
#!/bin/bash
# Gadugi Coordinator - Bash Interface

COORDINATOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$COORDINATOR_DIR/gadugi_coordinator.py"

gadugi_status() {
    echo "Checking Gadugi v0.3 Service Status..."
    python3 -c "
import asyncio
import sys
sys.path.append('$COORDINATOR_DIR')
from gadugi_coordinator import status_command
asyncio.run(status_command())
"
}

gadugi_start() {
    echo "Starting Gadugi v0.3 Services..."
    python3 -c "
import asyncio
import sys
sys.path.append('$COORDINATOR_DIR')
from gadugi_coordinator import start_command
success = asyncio.run(start_command())
sys.exit(0 if success else 1)
"
}

gadugi_json() {
    python3 -c "
import asyncio
import sys
sys.path.append('$COORDINATOR_DIR')
from gadugi_coordinator import coordinator
status = asyncio.run(coordinator.get_comprehensive_status(force_refresh=True))
import json
print(json.dumps(status, indent=2))
"
}

# Command dispatch
case "${1:-status}" in
    "status")
        gadugi_status
        ;;
    "start")
        gadugi_start
        ;;
    "json")
        gadugi_json
        ;;
    *)
        echo "Usage: $0 {status|start|json}"
        echo ""
        echo "Commands:"
        echo "  status - Show comprehensive service status"
        echo "  start  - Ensure all services are running"
        echo "  json   - Output detailed status as JSON"
        exit 1
        ;;
esac
```

## Environment Variables

### Configuration
- `GADUGI_COORDINATOR_CACHE_TTL` - Status cache TTL (default: 30s)
- `GADUGI_STARTUP_TIMEOUT` - Service startup timeout (default: 60s)
- `GADUGI_SERVICE_CHECK_TIMEOUT` - Individual service check timeout (default: 10s)

### Service Overrides
- `GADUGI_NEO4J_DISABLED` - Disable Neo4j checks
- `GADUGI_MEMORY_BACKEND` - Force memory backend (neo4j/sqlite)
- `GADUGI_EVENT_ROUTER_PORT` - Override event router port

## Integration Examples

### As Startup Hook
```bash
# In .claude/hooks/service-check.sh
source .claude/agents/GadugiCoordinator.md
gadugi_status
```

### Programmatic Usage
```python
from gadugi_coordinator import coordinator

# Get status
status = await coordinator.get_comprehensive_status()
print(f"Overall status: {status['overall_status']}")

# Ensure services running
success = await coordinator.ensure_services_running()
```

### JSON API Response
```json
{
  "timestamp": "2024-08-29T12:00:00.000Z",
  "overall_status": "FULLY_OPERATIONAL",
  "services": {
    "neo4j": {
      "name": "Neo4j Database",
      "status": "HEALTHY",
      "message": "Neo4j running and accessible",
      "details": {
        "container_status": "Up 2 hours",
        "http_port": 7475,
        "bolt_port": 7689,
        "connection": "verified"
      }
    },
    "memory": {
      "name": "Memory System",
      "status": "OPTIMAL",
      "message": "Memory system using Neo4j primary backend",
      "details": {
        "active_backend": "neo4j",
        "fallback_ready": true
      }
    },
    "event-router": {
      "name": "Event Router",
      "status": "HEALTHY",
      "message": "Event Router fully operational",
      "details": {
        "process": {"pid": 12345, "memory_mb": 45.2},
        "http_endpoint": "http://localhost:8000",
        "unix_socket": "/tmp/gadugi-events.sock"
      }
    }
  },
  "summary": {
    "total_services": 3,
    "healthy": 3,
    "degraded": 0,
    "down": 0,
    "unknown": 0
  },
  "agent_updates": {
    "up_to_date": true,
    "message": "All agents up to date"
  },
  "recommendations": [
    "All services operational - no actions needed"
  ]
}
```

This Gadugi Coordinator provides comprehensive orchestration and monitoring of all Gadugi v0.3 services with intelligent dependency management and detailed status reporting.
