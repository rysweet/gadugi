#!/usr/bin/env python3
"""Event Router Management CLI.

This CLI provides commands to manage the Event Router service, including:
- Starting/stopping the router
- Checking status and health
- Managing configurations
- Monitoring events
"""

import asyncio
import json
import subprocess
import sys
import os
import signal
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from client.client import EventRouterClient
from core.models import EventPriority, EventType


class EventRouterManager:
    """Event Router management utility."""
    
    def __init__(self):
        """Initialize manager."""
        self.config_file = Path("router_config.json")
        self.pid_file = Path("event_router.pid")
        self.log_file = Path("event_router.log")
        self.default_config = {
            "host": "localhost",
            "port": 9090,
            "max_queue_size": 10000,
            "max_clients": 1000,
            "use_multi_queue": False,
            "log_level": "INFO"
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")
    
    def start(self, daemon: bool = False):
        """Start the Event Router server."""
        if self.is_running():
            print("Event Router is already running")
            return False
        
        config = self.load_config()
        
        # Create start script
        start_script = f"""#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

sys.path.append('{os.path.join(os.path.dirname(__file__), 'src')}')

from core.router import EventRouter

logging.basicConfig(
    level=logging.{config.get('log_level', 'INFO')},
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('{self.log_file}'),
        logging.StreamHandler()
    ]
)

async def main():
    router = EventRouter(
        host="{config['host']}",
        port={config['port']},
        max_queue_size={config['max_queue_size']},
        max_clients={config['max_clients']},
        use_multi_queue={config['use_multi_queue']}
    )
    print(f"Event Router starting on ws://{config['host']}:{config['port']}")
    await router.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nEvent Router stopped")
"""
        
        # Write start script
        script_file = Path("_start_router.py")
        with open(script_file, 'w') as f:
            f.write(start_script)
        
        # Start process
        if daemon:
            # Start as daemon
            process = subprocess.Popen(
                [sys.executable, str(script_file)],
                stdout=open(self.log_file, 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            print(f"Event Router started as daemon (PID: {process.pid})")
            print(f"Logs: {self.log_file}")
            print(f"WebSocket URL: ws://{config['host']}:{config['port']}")
        else:
            # Start in foreground
            print(f"Starting Event Router on ws://{config['host']}:{config['port']}")
            print("Press Ctrl+C to stop")
            subprocess.run([sys.executable, str(script_file)])
        
        return True
    
    def stop(self):
        """Stop the Event Router server."""
        if not self.is_running():
            print("Event Router is not running")
            return False
        
        if self.pid_file.exists():
            with open(self.pid_file) as f:
                pid = int(f.read().strip())
            
            try:
                # Send SIGTERM
                os.kill(pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    time.sleep(0.5)
                    try:
                        os.kill(pid, 0)  # Check if process exists
                    except ProcessLookupError:
                        break
                else:
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)
                
                print(f"Event Router stopped (PID: {pid})")
                self.pid_file.unlink()
                return True
                
            except ProcessLookupError:
                print("Event Router process not found")
                self.pid_file.unlink()
                return False
            except Exception as e:
                print(f"Error stopping Event Router: {e}")
                return False
        
        return False
    
    def restart(self):
        """Restart the Event Router server."""
        print("Restarting Event Router...")
        self.stop()
        time.sleep(2)
        self.start(daemon=True)
    
    def is_running(self) -> bool:
        """Check if Event Router is running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, ValueError):
            # Clean up stale PID file
            self.pid_file.unlink()
            return False
    
    async def status(self):
        """Get Event Router status."""
        if not self.is_running():
            print("Event Router Status: STOPPED")
            return
        
        config = self.load_config()
        print(f"Event Router Status: RUNNING")
        
        if self.pid_file.exists():
            with open(self.pid_file) as f:
                pid = f.read().strip()
            print(f"PID: {pid}")
        
        print(f"WebSocket URL: ws://{config['host']}:{config['port']}")
        
        # Try to connect and get health
        try:
            client = EventRouterClient(url=f"ws://{config['host']}:{config['port']}")
            if await client.connect():
                health = await client.get_health()
                if health:
                    print(f"\nHealth Status:")
                    print(f"  Status: {health.get('status', 'unknown')}")
                    print(f"  Uptime: {health.get('uptime', 0):.1f} seconds")
                    print(f"  Events Processed: {health.get('events_processed', 0)}")
                    print(f"  Events Failed: {health.get('events_failed', 0)}")
                    print(f"  Events in Queue: {health.get('events_in_queue', 0)}")
                    print(f"  Active Subscriptions: {health.get('active_subscriptions', 0)}")
                    print(f"  Connected Clients: {health.get('connected_clients', 0)}")
                    
                    if health.get('errors'):
                        print(f"  Errors: {', '.join(health['errors'])}")
                
                await client.disconnect()
        except Exception as e:
            print(f"Could not connect to Event Router: {e}")
    
    def configure(self):
        """Interactive configuration."""
        config = self.load_config()
        
        print("\nEvent Router Configuration")
        print("-" * 40)
        
        # Host
        host = input(f"Host [{config['host']}]: ").strip()
        if host:
            config['host'] = host
        
        # Port
        port = input(f"Port [{config['port']}]: ").strip()
        if port:
            try:
                config['port'] = int(port)
            except ValueError:
                print("Invalid port number")
                return
        
        # Max queue size
        max_queue = input(f"Max Queue Size [{config['max_queue_size']}]: ").strip()
        if max_queue:
            try:
                config['max_queue_size'] = int(max_queue)
            except ValueError:
                print("Invalid queue size")
                return
        
        # Max clients
        max_clients = input(f"Max Clients [{config['max_clients']}]: ").strip()
        if max_clients:
            try:
                config['max_clients'] = int(max_clients)
            except ValueError:
                print("Invalid client limit")
                return
        
        # Multi-queue
        use_multi = input(f"Use Multi-Queue (y/n) [{'y' if config['use_multi_queue'] else 'n'}]: ").strip().lower()
        if use_multi:
            config['use_multi_queue'] = use_multi == 'y'
        
        # Log level
        log_level = input(f"Log Level (DEBUG/INFO/WARNING/ERROR) [{config.get('log_level', 'INFO')}]: ").strip().upper()
        if log_level and log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            config['log_level'] = log_level
        
        self.save_config(config)
        
        # Offer to restart if running
        if self.is_running():
            restart = input("\nEvent Router is running. Restart now? (y/n): ").strip().lower()
            if restart == 'y':
                self.restart()
    
    async def monitor(self):
        """Monitor events in real-time."""
        config = self.load_config()
        
        print(f"Connecting to Event Router at ws://{config['host']}:{config['port']}")
        print("Monitoring all events (Press Ctrl+C to stop)")
        print("-" * 60)
        
        client = EventRouterClient(url=f"ws://{config['host']}:{config['port']}")
        
        try:
            if not await client.connect():
                print("Failed to connect to Event Router")
                return
            
            # Subscribe to all events
            @client.on("*")
            async def log_event(event):
                timestamp = event.metadata.created_at.strftime("%H:%M:%S") if event.metadata and event.metadata.created_at else "??:??:??"
                priority = event.priority.name if hasattr(event.priority, 'name') else str(event.priority)
                print(f"[{timestamp}] [{priority:8}] {event.topic:30} | {event.source:20} | {json.dumps(event.payload)[:100]}")
            
            await client.subscribe(topics=["*"], callback=log_event)
            
            # Keep monitoring
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        finally:
            await client.disconnect()
    
    def logs(self, lines: int = 50, follow: bool = False):
        """View Event Router logs."""
        if not self.log_file.exists():
            print("No log file found")
            return
        
        if follow:
            # Follow logs
            print(f"Following {self.log_file} (Press Ctrl+C to stop)")
            try:
                subprocess.run(["tail", "-f", str(self.log_file)])
            except KeyboardInterrupt:
                print("\nStopped following logs")
        else:
            # Show last N lines
            subprocess.run(["tail", f"-n{lines}", str(self.log_file)])


async def async_main():
    """Async main for commands that need it."""
    parser = argparse.ArgumentParser(description="Event Router Management CLI")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "configure", 
        "monitor", "logs", "help"
    ], help="Command to execute")
    parser.add_argument("--daemon", "-d", action="store_true", 
                       help="Start as daemon (background process)")
    parser.add_argument("--lines", "-n", type=int, default=50,
                       help="Number of log lines to show")
    parser.add_argument("--follow", "-f", action="store_true",
                       help="Follow log output")
    
    args = parser.parse_args()
    manager = EventRouterManager()
    
    if args.command == "start":
        manager.start(daemon=args.daemon)
    elif args.command == "stop":
        manager.stop()
    elif args.command == "restart":
        manager.restart()
    elif args.command == "status":
        await manager.status()
    elif args.command == "configure":
        manager.configure()
    elif args.command == "monitor":
        await manager.monitor()
    elif args.command == "logs":
        manager.logs(lines=args.lines, follow=args.follow)
    elif args.command == "help":
        parser.print_help()
        print("\nExamples:")
        print("  python manage_router.py start --daemon    # Start in background")
        print("  python manage_router.py status            # Check status and health")
        print("  python manage_router.py monitor           # Monitor events in real-time")
        print("  python manage_router.py logs -f           # Follow logs")
        print("  python manage_router.py configure         # Interactive configuration")


def main():
    """Main entry point."""
    # Commands that need async
    async_commands = ["status", "monitor"]
    
    if len(sys.argv) > 1 and sys.argv[1] in async_commands:
        asyncio.run(async_main())
    else:
        # Parse args for sync commands
        parser = argparse.ArgumentParser(description="Event Router Management CLI")
        parser.add_argument("command", choices=[
            "start", "stop", "restart", "status", "configure", 
            "monitor", "logs", "help"
        ], help="Command to execute")
        parser.add_argument("--daemon", "-d", action="store_true", 
                           help="Start as daemon (background process)")
        parser.add_argument("--lines", "-n", type=int, default=50,
                           help="Number of log lines to show")
        parser.add_argument("--follow", "-f", action="store_true",
                           help="Follow log output")
        
        args = parser.parse_args()
        manager = EventRouterManager()
        
        if args.command == "start":
            manager.start(daemon=args.daemon)
        elif args.command == "stop":
            manager.stop()
        elif args.command == "restart":
            manager.restart()
        elif args.command == "configure":
            manager.configure()
        elif args.command == "logs":
            manager.logs(lines=args.lines, follow=args.follow)
        elif args.command == "help":
            parser.print_help()
            print("\nExamples:")
            print("  python manage_router.py start --daemon    # Start in background")
            print("  python manage_router.py status            # Check status and health")
            print("  python manage_router.py monitor           # Monitor events in real-time")
            print("  python manage_router.py logs -f           # Follow logs")
            print("  python manage_router.py configure         # Interactive configuration")
        else:
            # Async commands
            asyncio.run(async_main())


if __name__ == "__main__":
    main()