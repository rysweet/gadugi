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
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Any, Optional

try:
    import websockets  # type: ignore[import]
    from websockets.server import WebSocketServerProtocol  # type: ignore[import]
    websockets_available = True
except ImportError:
    websockets_available = False
    websockets = None  # type: ignore[assignment]
    WebSocketServerProtocol = None  # type: ignore[assignment]

try:
    from aiohttp import web  # type: ignore[import]
    import aiofiles  # type: ignore[import]
    aiohttp_available = True
except ImportError:
    aiohttp_available = False
    web = None  # type: ignore[assignment]
    aiofiles = None  # type: ignore[assignment]

try:
    import docker  # type: ignore[import]
    docker_available = True
except ImportError:
    docker_available = False
    docker = None  # type: ignore[assignment]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationMonitor:
    """Monitors and tracks orchestrator container execution"""

    def __init__(self, monitoring_dir: str) -> None:
        self.monitoring_dir = Path(monitoring_dir)
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        self.websocket_clients: Set[Any] = set()
        self.docker_client: Optional[Any] = None
        self.active_containers: Dict[str, Dict[str, Any]] = {}
        self.monitoring = False

        # Initialize Docker client
        if docker_available and docker is not None:
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
        if websockets_available and websockets is not None:
            asyncio.create_task(self.start_websocket_server())

    async def monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Update container status
                await self.update_container_status()

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
                filters={"name": "orchestrator-"},
                all=True
            )

            current_containers = {}

            for container in containers:
                container_info = {
                    'id': container.id,
                    'name': container.name,
                    'status': (container.status if container is not None else None),
                    'created': container.attrs['Created'],
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'labels': container.labels,
                    'ports': container.ports,
                    'mounts': [mount['Source'] + ':' + mount['Destination'] for mount in container.attrs.get('Mounts', [])],
                    'environment': container.attrs['Config'].get('Env', []),
                    'task_id': container.labels.get('task_id', 'unknown'),
                    'updated_at': datetime.now().isoformat()
                }

                # Get resource stats for running containers
                if (container.status if container is not None else None) == 'running':
                    try:
                        stats = container.stats(stream=False)
                        container_info['stats'] = {
                            'cpu_percent': self._calculate_cpu_percent(stats),
                            'memory_usage': stats.get('memory_stats', {}).get('usage', 0),
                            'memory_limit': stats.get('memory_stats', {}).get('limit', 0),
                            'network_rx': sum(net.get('rx_bytes', 0) for net in stats.get('networks', {}).values()),
                            'network_tx': sum(net.get('tx_bytes', 0) for net in stats.get('networks', {}).values())
                        }

                        # Get recent logs
                        logs = container.logs(tail=10).decode('utf-8').split('\n')
                        container_info['recent_logs'] = [log for log in logs if log.strip()]

                    except Exception as e:
                        logger.warning(f"Failed to get stats for {container.name}: {e}")
                        container_info['stats'] = {}
                        container_info['recent_logs'] = []
                else:
                    container_info['stats'] = {}
                    container_info['recent_logs'] = []

                current_containers[container.name] = container_info

            self.active_containers = current_containers

        except Exception as e:
            logger.error(f"Failed to update container status: {e}")

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})

            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})

            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(cpu_usage.get('percpu_usage', [])) * 100
                return round(cpu_percent, 2)

            return 0.0
        except Exception:
            return 0.0

    async def broadcast_status_update(self):
        """Broadcast status update to all WebSocket clients"""
        if not self.websocket_clients or not self.active_containers:
            return

        message = {
            'type': 'status_update',
            'timestamp': datetime.now().isoformat(),
            'containers': self.active_containers,
            'summary': {
                'total_containers': len(self.active_containers),
                'running_containers': len([c for c in self.active_containers.values() if c['status'] == 'running']),
                'failed_containers': len([c for c in self.active_containers.values() if c['status'] == 'exited'])
            }
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
        if not self.active_containers:
            return

        monitoring_file = self.monitoring_dir / f"orchestrator_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'containers': self.active_containers,
                'monitoring_metadata': {
                    'monitor_version': '1.0.0',
                    'docker_available': docker_available,
                    'websockets_available': websockets_available,
                    'connected_clients': len(self.websocket_clients)
                }
            }

            if aiofiles is not None:
                async with aiofiles.open(monitoring_file, 'w') as f:
                    await f.write(json.dumps(data, indent=2))
            else:
                with open(monitoring_file, 'w') as f:
                    json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")

    async def start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        if not websockets_available or websockets is None:
            logger.warning("WebSockets not available - install websockets package")
            return

        port = int(os.getenv('WEBSOCKET_PORT', 9001))

        async def handle_websocket(websocket, path):
            """Handle WebSocket connection"""
            logger.info(f"New WebSocket client connected: {websocket.remote_address}")
            self.websocket_clients.add(websocket)

            try:
                # Send initial status
                if self.active_containers:
                    initial_message = {
                        'type': 'initial_status',
                        'timestamp': datetime.now().isoformat(),
                        'containers': self.active_containers
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
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")

        try:
            if websockets_available and websockets is not None:
                await websockets.serve(handle_websocket, "0.0.0.0", port)
                logger.info(f"WebSocket server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")

    async def handle_client_message(self, websocket, data):
        """Handle messages from WebSocket clients"""
        message_type = data.get('type')

        if message_type == 'get_container_logs':
            container_name = data.get('container_name')
            await self.send_container_logs(websocket, container_name)
        elif message_type == 'get_detailed_stats':
            container_name = data.get('container_name')
            await self.send_detailed_stats(websocket, container_name)

    async def send_container_logs(self, websocket, container_name):
        """Send container logs to client"""
        if not self.docker_client or not container_name:
            return

        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=100).decode('utf-8')

            message = {
                'type': 'container_logs',
                'container_name': container_name,
                'logs': logs.split('\n'),
                'timestamp': datetime.now().isoformat()
            }

            await websocket.send(json.dumps(message))

        except Exception as e:
            error_message = {
                'type': 'error',
                'message': f"Failed to get logs for {container_name}: {e}"
            }
            await websocket.send(json.dumps(error_message))

    async def send_detailed_stats(self, websocket, container_name):
        """Send detailed container stats to client"""
        if not self.docker_client or not container_name:
            return

        try:
            container = self.docker_client.containers.get(container_name)

            if (container.status if container is not None else None) == 'running':
                stats = container.stats(stream=False)

                detailed_stats = {
                    'type': 'detailed_stats',
                    'container_name': container_name,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }

                await websocket.send(json.dumps(detailed_stats))

        except Exception as e:
            error_message = {
                'type': 'error',
                'message': f"Failed to get detailed stats for {container_name}: {e}"
            }
            await websocket.send(json.dumps(error_message))

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Stopping orchestrator monitoring...")


async def create_web_app():
    """Create web application for monitoring dashboard"""
    if not aiohttp_available or web is None:
        logger.error("aiohttp not available - install with: pip install aiohttp")
        return None

    app = web.Application()

    # Serve static monitoring dashboard
    dashboard_html = '''
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
                    document.getElementById('totalContainers').textContent = data.summary.total_containers;
                    document.getElementById('runningContainers').textContent = data.summary.running_containers;
                    document.getElementById('failedContainers').textContent = data.summary.failed_containers;
                }

                if (data.containers) {
                    updateContainerList(data.containers);
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
                                    <span class="status ${(container.status if container is not None else None)}">${(container.status if container is not None else None)}</span>
                                </div>
                                <div class="timestamp">Task: ${(container.task_id if container is not None else None)}</div>
                            </div>
                            ${(container.status if container is not None else None) === 'running' ? `
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

            // Initialize WebSocket connection
            connectWebSocket();
        </script>
    </body>
    </html>
    '''

    async def dashboard_handler(request):
        if web is not None:
            return web.Response(text=dashboard_html, content_type='text/html')
        return None

    async def health_handler(request):
        if web is not None:
            return web.Response(text='OK', status=200)
        return None

    app.router.add_get('/', dashboard_handler)
    app.router.add_get('/health', health_handler)

    return app


async def main():
    """Main entry point for monitoring dashboard"""
    logger.info("Starting orchestrator monitoring dashboard...")

    # Create monitor
    monitor = OrchestrationMonitor(monitoring_dir="./monitoring")
    await monitor.start_monitoring()

    # Create and start web app
    if aiohttp_available and web is not None:
        app = await create_web_app()
        if app:
            port = int(os.getenv('HTTP_PORT', 8080))
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', port)
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
