#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard for Containerized Orchestrator

Provides web-based monitoring interface for parallel task execution
with real-time updates via WebSockets.

Features:
- Live container status tracking
- Real-time log streaming
- Resource usage monitoring
- Task progress visualization
- Performance analytics
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import websockets
    from websockets.asyncio.server import ServerConnection

    WEBSOCKETS_AVAILABLE = True
    # Define type for backward compatibility
    WebSocketServerProtocol = ServerConnection
except ImportError:
    try:
        # Fallback to legacy import for older versions
        import websockets
        from websockets.server import WebSocketServerProtocol

        WEBSOCKETS_AVAILABLE = True
    except ImportError:
        WEBSOCKETS_AVAILABLE = False
        WebSocketServerProtocol = None

try:
    from aiohttp import web, WSMsgType

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None
    WSMsgType = None

try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationMonitor:
    """Monitors and tracks orchestrator container execution"""

    def __init__(self, monitoring_dir: str = "./monitoring"):
        self.monitoring_dir = Path(monitoring_dir)
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        self.websocket_clients: Set[WebSocketServerProtocol] = set()
        self.docker_client = None
        self.active_containers: Dict[str, Dict] = {}
        self.active_processes: Dict[int, Dict] = {}
        self.active_worktrees: List[Dict] = []
        self.monitoring = False

        # Initialize Docker client
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker client not available: {e}")

    async def start_monitoring(self):
        """Start monitoring orchestrator containers"""
        self.monitoring = True
        logger.info("Starting orchestrator monitoring...")

        # Start monitoring loop
        asyncio.create_task(self.monitoring_loop())

        # Start WebSocket server if available
        if WEBSOCKETS_AVAILABLE:
            asyncio.create_task(self.start_websocket_server())

    async def monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Update container status
                await self.update_container_status()

                # Update process status
                await self.update_process_status()

                # Update worktree status
                await self.update_worktree_status()

                # Broadcast updates to WebSocket clients
                await self.broadcast_status_update()

                # Save monitoring data
                await self.save_monitoring_data()

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1)

    async def update_container_status(self):
        """Update status of all orchestrator containers"""
        if not self.docker_client:
            return

        try:
            # Find orchestrator containers
            containers = self.docker_client.containers.list(
                filters={"name": "orchestrator-"}, all=True
            )

            current_containers = {}

            for container in containers:
                container_info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "created": container.attrs["Created"],
                    "image": container.image.tags[0]
                    if container.image.tags
                    else "unknown",
                    "labels": container.labels,
                    "ports": container.ports,
                    "mounts": [
                        mount["Source"] + ":" + mount["Destination"]
                        for mount in container.attrs.get("Mounts", [])
                    ],
                    "environment": container.attrs["Config"].get("Env", []),
                    "task_id": container.labels.get("task_id", "unknown"),
                    "updated_at": datetime.now().isoformat(),
                }

                # Get resource stats for running containers
                if container.status == "running":
                    try:
                        stats = container.stats(stream=False)
                        container_info["stats"] = {
                            "cpu_percent": self._calculate_cpu_percent(stats),
                            "memory_usage": stats.get("memory_stats", {}).get(
                                "usage", 0
                            ),
                            "memory_limit": stats.get("memory_stats", {}).get(
                                "limit", 0
                            ),
                            "network_rx": sum(
                                net.get("rx_bytes", 0)
                                for net in stats.get("networks", {}).values()
                            ),
                            "network_tx": sum(
                                net.get("tx_bytes", 0)
                                for net in stats.get("networks", {}).values()
                            ),
                        }

                        # Get recent logs
                        logs = container.logs(tail=10).decode("utf-8").split("\n")
                        container_info["recent_logs"] = [
                            log for log in logs if log.strip()
                        ]

                    except Exception as e:
                        logger.warning(f"Failed to get stats for {container.name}: {e}")
                        container_info["stats"] = {}
                        container_info["recent_logs"] = []
                else:
                    container_info["stats"] = {}
                    container_info["recent_logs"] = []

                current_containers[container.name] = container_info

            self.active_containers = current_containers

        except Exception as e:
            logger.error(f"Failed to update container status: {e}")

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})

            cpu_usage = cpu_stats.get("cpu_usage", {})
            precpu_usage = precpu_stats.get("cpu_usage", {})

            cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get(
                "total_usage", 0
            )
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (
                    (cpu_delta / system_delta)
                    * len(cpu_usage.get("percpu_usage", []))
                    * 100
                )
                return round(cpu_percent, 2)

            return 0.0
        except Exception:
            return 0.0

    async def update_process_status(self):
        """Update status of Claude and orchestrator processes"""
        if not PSUTIL_AVAILABLE:
            return

        try:
            current_processes = {}

            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cmdline",
                    "create_time",
                    "cpu_percent",
                    "memory_info",
                    "status",
                ]
            ):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])

                    # Look for Claude, orchestrator, or Python processes related to our work
                    if any(
                        keyword in cmdline.lower()
                        for keyword in ["claude", "orchestrator", "gadugi", "workflow"]
                    ):
                        process_info = {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": cmdline,
                            "status": proc.info["status"],
                            "cpu_percent": proc.info["cpu_percent"] or 0.0,
                            "memory_mb": round(
                                proc.info["memory_info"].rss / 1024 / 1024, 1
                            )
                            if proc.info["memory_info"]
                            else 0,
                            "create_time": datetime.fromtimestamp(
                                proc.info["create_time"]
                            ).isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                        current_processes[proc.info["pid"]] = process_info

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            self.active_processes = current_processes

        except Exception as e:
            logger.error(f"Failed to update process status: {e}")

    async def update_worktree_status(self):
        """Update status of active worktrees"""
        try:
            worktrees = []

            # Check for .worktrees directory
            worktrees_dir = Path(".worktrees")
            if worktrees_dir.exists():
                for worktree_path in worktrees_dir.iterdir():
                    if worktree_path.is_dir():
                        try:
                            # Get basic info about the worktree
                            task_file = worktree_path / ".task" / "metadata.json"
                            git_status_cmd = ["git", "status", "--porcelain"]

                            worktree_info = {
                                "path": str(worktree_path),
                                "name": worktree_path.name,
                                "created": datetime.fromtimestamp(
                                    worktree_path.stat().st_ctime
                                ).isoformat(),
                                "modified": datetime.fromtimestamp(
                                    worktree_path.stat().st_mtime
                                ).isoformat(),
                                "updated_at": datetime.now().isoformat(),
                            }

                            # Try to get task metadata
                            if task_file.exists():
                                try:
                                    with open(task_file, "r") as f:
                                        task_data = json.load(f)
                                        worktree_info["task_id"] = task_data.get(
                                            "task_id", "unknown"
                                        )
                                        worktree_info["task_name"] = task_data.get(
                                            "task_name", "unknown"
                                        )
                                        worktree_info["phase"] = task_data.get(
                                            "current_phase", "unknown"
                                        )
                                except Exception:
                                    worktree_info["task_id"] = "unknown"

                            # Get git status
                            try:
                                result = subprocess.run(
                                    git_status_cmd,
                                    cwd=worktree_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=5,
                                )
                                if result.returncode == 0:
                                    changes = (
                                        result.stdout.strip().split("\n")
                                        if result.stdout.strip()
                                        else []
                                    )
                                    worktree_info["git_status"] = {
                                        "clean": len(changes) == 0,
                                        "changes_count": len(changes),
                                        "changes": changes[:5],  # First 5 changes only
                                    }
                            except Exception:
                                worktree_info["git_status"] = {
                                    "clean": None,
                                    "changes_count": 0,
                                    "changes": [],
                                }

                            worktrees.append(worktree_info)

                        except Exception as e:
                            logger.warning(
                                f"Failed to get info for worktree {worktree_path}: {e}"
                            )

            self.active_worktrees = worktrees

        except Exception as e:
            logger.error(f"Failed to update worktree status: {e}")

    async def broadcast_status_update(self):
        """Broadcast status update to all WebSocket clients"""
        if not self.websocket_clients:
            return

        message = {
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "containers": self.active_containers,
            "processes": self.active_processes,
            "worktrees": self.active_worktrees,
            "summary": {
                "total_containers": len(self.active_containers),
                "running_containers": len(
                    [
                        c
                        for c in self.active_containers.values()
                        if c["status"] == "running"
                    ]
                ),
                "failed_containers": len(
                    [
                        c
                        for c in self.active_containers.values()
                        if c["status"] == "exited"
                    ]
                ),
                "active_processes": len(self.active_processes),
                "active_worktrees": len(self.active_worktrees),
            },
        }

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(json.dumps(message))
            except Exception:
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

    async def save_monitoring_data(self):
        """Save current monitoring data to file"""
        if (
            not self.active_containers
            and not self.active_processes
            and not self.active_worktrees
        ):
            return

        monitoring_file = (
            self.monitoring_dir
            / f"orchestrator_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "containers": self.active_containers,
                "processes": self.active_processes,
                "worktrees": self.active_worktrees,
                "monitoring_metadata": {
                    "monitor_version": "1.1.0",
                    "docker_available": DOCKER_AVAILABLE,
                    "websockets_available": WEBSOCKETS_AVAILABLE,
                    "psutil_available": PSUTIL_AVAILABLE,
                    "aiofiles_available": AIOFILES_AVAILABLE,
                    "connected_clients": len(self.websocket_clients),
                },
            }

            if AIOFILES_AVAILABLE:
                async with aiofiles.open(monitoring_file, "w") as f:
                    await f.write(json.dumps(data, indent=2))
            else:
                with open(monitoring_file, "w") as f:
                    json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")

    async def start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSockets not available - install websockets package")
            return

        port = int(os.getenv("WEBSOCKET_PORT", 9001))

        async def handle_websocket(websocket, path):
            """Handle WebSocket connection"""
            logger.info(f"New WebSocket client connected: {websocket.remote_address}")
            self.websocket_clients.add(websocket)

            try:
                # Send initial status
                if self.active_containers:
                    initial_message = {
                        "type": "initial_status",
                        "timestamp": datetime.now().isoformat(),
                        "containers": self.active_containers,
                    }
                    await websocket.send(json.dumps(initial_message))

                # Keep connection alive
                async for message in websocket:
                    # Handle client messages if needed
                    try:
                        data = json.loads(message)
                        await self.handle_client_message(websocket, data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from client: {message}")

            except Exception as e:
                logger.warning(f"WebSocket client error: {e}")
            finally:
                self.websocket_clients.discard(websocket)
                logger.info(
                    f"WebSocket client disconnected: {websocket.remote_address}"
                )

        try:
            await websockets.serve(handle_websocket, "0.0.0.0", port)
            logger.info(f"WebSocket server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")

    async def handle_client_message(self, websocket, data):
        """Handle messages from WebSocket clients"""
        message_type = data.get("type")

        if message_type == "get_container_logs":
            container_name = data.get("container_name")
            await self.send_container_logs(websocket, container_name)
        elif message_type == "get_detailed_stats":
            container_name = data.get("container_name")
            await self.send_detailed_stats(websocket, container_name)

    async def send_container_logs(self, websocket, container_name):
        """Send container logs to client"""
        if not self.docker_client or not container_name:
            return

        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=100).decode("utf-8")

            message = {
                "type": "container_logs",
                "container_name": container_name,
                "logs": logs.split("\n"),
                "timestamp": datetime.now().isoformat(),
            }

            await websocket.send(json.dumps(message))

        except Exception as e:
            error_message = {
                "type": "error",
                "message": f"Failed to get logs for {container_name}: {e}",
            }
            await websocket.send(json.dumps(error_message))

    async def send_detailed_stats(self, websocket, container_name):
        """Send detailed container stats to client"""
        if not self.docker_client or not container_name:
            return

        try:
            container = self.docker_client.containers.get(container_name)

            if container.status == "running":
                stats = container.stats(stream=False)

                detailed_stats = {
                    "type": "detailed_stats",
                    "container_name": container_name,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat(),
                }

                await websocket.send(json.dumps(detailed_stats))

        except Exception as e:
            error_message = {
                "type": "error",
                "message": f"Failed to get detailed stats for {container_name}: {e}",
            }
            await websocket.send(json.dumps(error_message))

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Stopping orchestrator monitoring...")


async def create_web_app():
    """Create web application for monitoring dashboard"""
    if not AIOHTTP_AVAILABLE:
        logger.error("aiohttp not available - install with: pip install aiohttp")
        return None

    app = web.Application()

    # Serve static monitoring dashboard
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchestrator Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .containers { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .container-item { border-bottom: 1px solid #eee; padding: 15px 0; }
            .container-item:last-child { border-bottom: none; }
            .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .status.running { background: #27ae60; color: white; }
            .status.exited { background: #e74c3c; color: white; }
            .status.created { background: #3498db; color: white; }
            .logs { background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; font-family: monospace; max-height: 200px; overflow-y: auto; margin-top: 10px; }
            .timestamp { color: #7f8c8d; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Orchestrator Container Monitor</h1>
                <p>Real-time monitoring of parallel task execution</p>
                <div class="timestamp" id="lastUpdate">Last updated: Never</div>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Containers</h3>
                    <div id="totalContainers" style="font-size: 24px; font-weight: bold; color: #2c3e50;">0</div>
                </div>
                <div class="stat-card">
                    <h3>Running</h3>
                    <div id="runningContainers" style="font-size: 24px; font-weight: bold; color: #27ae60;">0</div>
                </div>
                <div class="stat-card">
                    <h3>Failed</h3>
                    <div id="failedContainers" style="font-size: 24px; font-weight: bold; color: #e74c3c;">0</div>
                </div>
                <div class="stat-card">
                    <h3>Active Processes</h3>
                    <div id="activeProcesses" style="font-size: 24px; font-weight: bold; color: #3498db;">0</div>
                </div>
                <div class="stat-card">
                    <h3>Active Worktrees</h3>
                    <div id="activeWorktrees" style="font-size: 24px; font-weight: bold; color: #9b59b6;">0</div>
                </div>
                <div class="stat-card">
                    <h3>WebSocket Status</h3>
                    <div id="wsStatus" style="font-size: 16px; font-weight: bold; color: #e74c3c;">Disconnected</div>
                </div>
            </div>

            <div class="containers">
                <h2>Active Containers</h2>
                <div id="containerList">
                    <p>No containers found. Waiting for updates...</p>
                </div>
            </div>

            <div class="containers">
                <h2>Active Processes</h2>
                <div id="processList">
                    <p>No processes found. Waiting for updates...</p>
                </div>
            </div>

            <div class="containers">
                <h2>Active Worktrees</h2>
                <div id="worktreeList">
                    <p>No worktrees found. Waiting for updates...</p>
                </div>
            </div>
        </div>

        <script>
            const wsPort = 9001;
            let ws = null;

            function connectWebSocket() {
                try {
                    ws = new WebSocket(`ws://localhost:${wsPort}`);

                    ws.onopen = function() {
                        document.getElementById('wsStatus').textContent = 'Connected';
                        document.getElementById('wsStatus').style.color = '#27ae60';
                    };

                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateDashboard(data);
                    };

                    ws.onclose = function() {
                        document.getElementById('wsStatus').textContent = 'Disconnected';
                        document.getElementById('wsStatus').style.color = '#e74c3c';
                        // Reconnect after 5 seconds
                        setTimeout(connectWebSocket, 5000);
                    };

                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                    };

                } catch (error) {
                    console.error('Failed to connect WebSocket:', error);
                    setTimeout(connectWebSocket, 5000);
                }
            }

            function updateDashboard(data) {
                document.getElementById('lastUpdate').textContent = `Last updated: ${new Date(data.timestamp).toLocaleString()}`;

                if (data.summary) {
                    document.getElementById('totalContainers').textContent = data.summary.total_containers || 0;
                    document.getElementById('runningContainers').textContent = data.summary.running_containers || 0;
                    document.getElementById('failedContainers').textContent = data.summary.failed_containers || 0;
                    document.getElementById('activeProcesses').textContent = data.summary.active_processes || 0;
                    document.getElementById('activeWorktrees').textContent = data.summary.active_worktrees || 0;
                }

                if (data.containers) {
                    updateContainerList(data.containers);
                }

                if (data.processes) {
                    updateProcessList(data.processes);
                }

                if (data.worktrees) {
                    updateWorktreeList(data.worktrees);
                }
            }

            function updateContainerList(containers) {
                const containerList = document.getElementById('containerList');

                if (Object.keys(containers).length === 0) {
                    containerList.innerHTML = '<p>No containers found.</p>';
                    return;
                }

                let html = '';
                for (const [name, container] of Object.entries(containers)) {
                    const stats = container.stats || {};
                    const memoryUsageMB = Math.round((stats.memory_usage || 0) / 1024 / 1024);
                    const memoryLimitMB = Math.round((stats.memory_limit || 0) / 1024 / 1024);

                    html += `
                        <div class="container-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${name}</strong>
                                    <span class="status ${container.status}">${container.status}</span>
                                </div>
                                <div class="timestamp">Task: ${container.task_id}</div>
                            </div>
                            ${container.status === 'running' ? `
                                <div style="margin-top: 10px;">
                                    <div>CPU: ${stats.cpu_percent || 0}%</div>
                                    <div>Memory: ${memoryUsageMB}MB / ${memoryLimitMB}MB</div>
                                </div>
                            ` : ''}
                            ${container.recent_logs && container.recent_logs.length > 0 ? `
                                <div class="logs">
                                    ${container.recent_logs.slice(-5).map(log => `<div>${log}</div>`).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                }

                containerList.innerHTML = html;
            }

            function updateProcessList(processes) {
                const processList = document.getElementById('processList');

                if (Object.keys(processes).length === 0) {
                    processList.innerHTML = '<p>No active processes found.</p>';
                    return;
                }

                let html = '';
                for (const [pid, process] of Object.entries(processes)) {
                    html += `
                        <div class="container-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>PID ${process.pid}</strong> - ${process.name}
                                    <span class="status ${process.status.toLowerCase()}">${process.status}</span>
                                </div>
                                <div class="timestamp">CPU: ${process.cpu_percent}% | RAM: ${process.memory_mb}MB</div>
                            </div>
                            <div style="margin-top: 5px; font-size: 12px; color: #666;">
                                ${process.cmdline.length > 100 ? process.cmdline.substring(0, 100) + '...' : process.cmdline}
                            </div>
                        </div>
                    `;
                }

                processList.innerHTML = html;
            }

            function updateWorktreeList(worktrees) {
                const worktreeList = document.getElementById('worktreeList');

                if (worktrees.length === 0) {
                    worktreeList.innerHTML = '<p>No active worktrees found.</p>';
                    return;
                }

                let html = '';
                for (const worktree of worktrees) {
                    const statusColor = worktree.git_status && worktree.git_status.clean ? '#27ae60' : '#f39c12';
                    const statusText = worktree.git_status && worktree.git_status.clean ? 'Clean' :
                                     `${worktree.git_status ? worktree.git_status.changes_count : 0} changes`;

                    html += `
                        <div class="container-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${worktree.name}</strong>
                                    <span class="status" style="background: ${statusColor};">${statusText}</span>
                                </div>
                                <div class="timestamp">${worktree.task_id || 'Unknown task'}</div>
                            </div>
                            <div style="margin-top: 5px;">
                                <div>Phase: ${worktree.phase || 'Unknown'}</div>
                                <div style="font-size: 12px; color: #666;">
                                    Created: ${new Date(worktree.created).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    `;
                }

                worktreeList.innerHTML = html;
            }

            // Initialize WebSocket connection
            connectWebSocket();
        </script>
    </body>
    </html>
    """

    async def dashboard_handler(request):
        return web.Response(text=dashboard_html, content_type="text/html")

    async def health_handler(request):
        return web.Response(text="OK", status=200)

    app.router.add_get("/", dashboard_handler)
    app.router.add_get("/health", health_handler)

    return app


async def main():
    """Main entry point for monitoring dashboard"""
    logger.info("Starting orchestrator monitoring dashboard...")

    # Create monitor
    monitor = OrchestrationMonitor()
    await monitor.start_monitoring()

    # Create and start web app
    if AIOHTTP_AVAILABLE:
        app = await create_web_app()
        if app:
            port = int(os.getenv("HTTP_PORT", 8080))
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()
            logger.info(f"Monitoring dashboard available at http://localhost:{port}")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring dashboard...")
        monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
