#!/usr/bin/env python3
"""
Service Launcher for Gadugi CLI

Launches individual Gadugi services as separate processes.
"""

import argparse
import asyncio
import importlib
import logging
import sys
import signal
from pathlib import Path


class ServiceLauncher:
    """Launches and manages individual Gadugi services."""

    def __init__(
        self, service_name: str, module_path: str, class_name: str, port: int = None
    ):
        self.service_name = service_name
        self.module_path = module_path
        self.class_name = class_name
        self.port = port
        self.service_instance = None
        self.running = False
        self._stop_event = None

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format=f"%(asctime)s - {service_name} - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(f"service_launcher_{service_name}")

    async def start(self):
        """Start the service."""
        try:
            self.logger.info(f"Starting {self.service_name} service")

            # Add the services directory to Python path
            services_dir = Path(__file__).parent.parent
            if str(services_dir) not in sys.path:
                sys.path.insert(0, str(services_dir))

            # Import the service module
            module = importlib.import_module(self.module_path)
            service_class = getattr(module, self.class_name)

            # Create service instance
            if self.port:
                self.service_instance = service_class(port=self.port)
            else:
                self.service_instance = service_class()

            # Set up signal handlers
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.stop())

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Start the service
            await self.service_instance.start()
            self.running = True

            self.logger.info(f"{self.service_name} service started successfully")

            # Keep the service running
            self._stop_event = asyncio.Event()
            await self._stop_event.wait()

        except Exception as e:
            self.logger.error(f"Failed to start {self.service_name} service: {e}")
            raise

    async def stop(self):
        """Stop the service."""
        if self.service_instance and self.running:
            self.logger.info(f"Stopping {self.service_name} service")
            self.running = False
            if self._stop_event:
                self._stop_event.set()

            try:
                await self.service_instance.stop()
                self.logger.info(f"{self.service_name} service stopped")
            except Exception as e:
                self.logger.error(f"Error stopping {self.service_name} service: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gadugi Service Launcher")
    parser.add_argument("--service", required=True, help="Service name")
    parser.add_argument("--module", required=True, help="Module path")
    parser.add_argument("--class", required=True, help="Class name")
    parser.add_argument("--port", type=int, help="Port number")

    args = parser.parse_args()

    launcher = ServiceLauncher(
        service_name=args.service,
        module_path=args.module,
        class_name=getattr(args, "class"),
        port=args.port,
    )

    try:
        await launcher.start()
    except KeyboardInterrupt:
        await launcher.stop()
    except Exception as e:
        print(f"Service launcher error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
