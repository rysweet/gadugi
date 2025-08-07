"""
Main Gadugi Event Service Implementation

Provides the core event-driven service that handles:
- GitHub webhook events
- Local event submission via Unix socket
- Periodic GitHub API polling (fallback)
- Event filtering and agent invocation
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import hmac
import hashlib
import signal
import sys

from aiohttp import web

from .config import load_config
from .events import Event, GitHubEvent
from .handlers import EventHandler
from .github_client import GitHubClient
from .agent_invoker import AgentInvoker

logger = logging.getLogger(__name__)


class GadugiEventService:
    """
    Main event service that coordinates all event handling for Gadugi.

    Features:
    - HTTP server for GitHub webhooks
    - Unix socket server for local events
    - GitHub API polling fallback
    - Event filtering and routing
    - Agent invocation management
    - Service lifecycle management
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Gadugi event service."""
        self.config = load_config(config_path)
        self.handlers: List[EventHandler] = []
        self.github_client = GitHubClient(self.config.github_token)
        self.agent_invoker = AgentInvoker()

        # Service state
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._tasks: Set[asyncio.Task] = set()

        # Polling state
        self._last_poll_time = datetime.now()
        self._processed_events: Set[str] = set()

        # Setup logging
        self._setup_logging()

        # Load event handlers
        self._load_event_handlers()

        logger.info(
            f"Gadugi Event Service initialized with {len(self.handlers)} handlers"
        )

    def _setup_logging(self):
        """Configure logging based on service configuration."""
        log_config = self.config.log_config

        # Configure main logger
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Setup file logging if configured
        if log_config.output == "file" and log_config.file_path:
            file_handler = logging.FileHandler(log_config.file_path)
            file_handler.setLevel(log_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Setup audit logging if enabled
        if log_config.enable_audit and log_config.audit_file_path:
            self.audit_logger = logging.getLogger("gadugi.audit")
            audit_handler = logging.FileHandler(log_config.audit_file_path)
            audit_formatter = logging.Formatter("%(asctime)s - AUDIT - %(message)s")
            audit_handler.setFormatter(audit_formatter)
            self.audit_logger.addHandler(audit_handler)
            self.audit_logger.setLevel(logging.INFO)

    def _load_event_handlers(self):
        """Load event handlers from configuration."""
        self.handlers = [EventHandler.from_config(h) for h in self.config.handlers]

        # Sort handlers by priority (higher priority first)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)

        logger.info(f"Loaded {len(self.handlers)} event handlers")

    async def start(self):
        """Start the Gadugi event service."""
        if self.running:
            logger.warning("Service is already running")
            return

        logger.info("Starting Gadugi Event Service")
        self.running = True
        # Record service start time for health checks and metrics
        self._start_time = datetime.now()

        try:
            # Start HTTP server for webhooks
            webhook_task = asyncio.create_task(self._start_webhook_server())
            self._tasks.add(webhook_task)

            # Start Unix socket server for local events
            socket_task = asyncio.create_task(self._start_socket_server())
            self._tasks.add(socket_task)

            # Start GitHub polling (fallback)
            if self.config.poll_interval_seconds > 0:
                poll_task = asyncio.create_task(self._start_github_polling())
                self._tasks.add(poll_task)

            # Setup signal handlers
            self._setup_signal_handlers()

            logger.info("Gadugi Event Service started successfully")

            # Wait for shutdown
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Error starting service: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the Gadugi event service."""
        if not self.running:
            return

        logger.info("Stopping Gadugi Event Service")
        self.running = False

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close GitHub client
        await self.github_client.close()

        logger.info("Gadugi Event Service stopped")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _start_webhook_server(self):
        """Start HTTP server for GitHub webhooks."""
        app = web.Application()
        app.router.add_post("/webhook/github", self._handle_github_webhook)
        app.router.add_get("/health", self._handle_health_check)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, self.config.bind_address, self.config.bind_port)
        await site.start()

        logger.info(
            f"Webhook server listening on {self.config.bind_address}:{self.config.bind_port}"
        )

        try:
            # Use an event to wait for shutdown instead of polling with sleep
            shutdown_event = self._shutdown_event
            await shutdown_event.wait()
        finally:
            await runner.cleanup()

    async def _start_socket_server(self):
        """Start Unix socket server for local events."""
        if not self.config.socket_path:
            logger.info("Unix socket disabled (no socket_path configured)")
            return

        # Remove existing socket file
        socket_path = Path(self.config.socket_path)
        if socket_path.exists():
            socket_path.unlink()

        # Create socket directory if needed
        socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Start Unix socket server
        server = await asyncio.start_unix_server(
            self._handle_socket_connection, path=str(socket_path)
        )

        logger.info(f"Unix socket server listening on {socket_path}")

        try:
            shutdown_event = self._shutdown_event
            await shutdown_event.wait()
        finally:
            server.close()
            await server.wait_closed()
            if socket_path.exists():
                socket_path.unlink()

    async def _start_github_polling(self):
        """Start GitHub API polling for events (fallback mode)."""
        logger.info(
            f"Starting GitHub polling every {self.config.poll_interval_seconds} seconds"
        )

        while self.running:
            try:
                await self._poll_github_events()
                # Wait for either shutdown or poll interval
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.config.poll_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass
            except Exception as e:
                logger.error(f"Error during GitHub polling: {e}")
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=min(self.config.poll_interval_seconds, 60),
                    )
                except asyncio.TimeoutError:
                    pass

    async def _handle_github_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming GitHub webhook."""
        try:
            # Read raw body once for signature verification and JSON parsing
            raw_body = await request.read()

            # Verify webhook signature (if configured)
            signature_header = request.headers.get("X-Hub-Signature-256", "")
            if not self._verify_webhook_signature(raw_body, signature_header):
                logger.warning("Invalid webhook signature")
                return web.Response(status=401, text="Unauthorized")

            # Parse webhook JSON payload
            webhook_data = json.loads(raw_body.decode("utf-8") or "{}")
            event_type = request.headers.get("X-GitHub-Event", "unknown")

            # Create event object
            event = self._create_github_event(event_type, webhook_data)

            # Log webhook receipt
            if hasattr(self, "audit_logger"):
                self.audit_logger.info(
                    f"Received GitHub webhook: {event_type} from {event.payload.github_event.repository}"
                )

            # Process event
            await self._process_event(event)

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Error handling GitHub webhook: {e}")
            return web.Response(status=500, text="Internal Server Error")

    async def _handle_health_check(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        health_data = {
            "status": "healthy" if self.running else "unhealthy",
            "service": "gadugi-event-service",
            "version": "0.1.0",
            "handlers": len(self.handlers),
            "uptime": str(datetime.now() - self._start_time)
            if hasattr(self, "_start_time")
            else "unknown",
        }
        return web.json_response(health_data)

    async def _handle_socket_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle Unix socket connection for local events."""
        try:
            # Read event data
            data = await reader.read(1024 * 1024)  # 1MB limit
            if not data:
                return

            # Parse event
            event_data = json.loads(data.decode("utf-8"))
            event = Event.from_dict(event_data)

            # Log local event
            if hasattr(self, "audit_logger"):
                self.audit_logger.info(f"Received local event: {event.event_type}")

            # Process event
            await self._process_event(event)

            # Send response
            response = {"status": "accepted", "event_id": event.event_id}
            writer.write(json.dumps(response).encode("utf-8"))
            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling socket connection: {e}")
            error_response = {"status": "error", "message": str(e)}
            writer.write(json.dumps(error_response).encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def _verify_webhook_signature(self, body: bytes, signature_header: str) -> bool:
        """Verify GitHub webhook signature.

        Parameters
        ----------
        body : bytes
            Raw request body.
        signature_header : str
            Value of the `X-Hub-Signature-256` header.
        """
        if not self.config.webhook_secret:
            # Signature verification disabled
            return True

        if not signature_header.startswith("sha256="):
            return False

        expected = (
            "sha256="
            + hmac.new(
                self.config.webhook_secret.encode("utf-8"), body, hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature_header, expected)

    def _create_github_event(
        self, event_type: str, webhook_data: Dict[str, Any]
    ) -> Event:
        """Create Event object from GitHub webhook data."""
        # Extract common fields
        repository = webhook_data.get("repository", {}).get("full_name", "unknown")
        action = webhook_data.get("action", "unknown")
        sender = webhook_data.get("sender", {}).get("login", "unknown")

        # Extract issue/PR specific fields
        number = None
        title = None
        body = None
        state = None
        labels = []
        assignees = []
        milestone = None

        if "issue" in webhook_data:
            issue = webhook_data["issue"]
            number = issue.get("number")
            title = issue.get("title", "")
            body = issue.get("body", "")
            state = issue.get("state", "")
            labels = [label["name"] for label in issue.get("labels", [])]
            assignees = [assignee["login"] for assignee in issue.get("assignees", [])]
            milestone = (
                issue.get("milestone", {}).get("title")
                if issue.get("milestone")
                else None
            )

        elif "pull_request" in webhook_data:
            pr = webhook_data["pull_request"]
            number = pr.get("number")
            title = pr.get("title", "")
            body = pr.get("body", "")
            state = pr.get("state", "")
            labels = [label["name"] for label in pr.get("labels", [])]
            assignees = [assignee["login"] for assignee in pr.get("assignees", [])]
            milestone = (
                pr.get("milestone", {}).get("title") if pr.get("milestone") else None
            )

        # Extract ref for push events
        ref = webhook_data.get("ref", "")

        # Create GitHub event
        github_event = GitHubEvent(
            webhook_event=event_type,
            repository=repository,
            number=number,
            action=action,
            actor=sender,
            ref=ref,
            labels=labels,
            title=title or "",
            body=body or "",
            state=state or "",
            milestone=milestone or "",
            assignees=assignees,
        )

        # Create main event
        event = Event(
            event_id=f"github-{int(time.time())}-{hash(str(webhook_data)) & 0x7FFFFFFF}",
            event_type=f"github.{event_type}.{action}",
            timestamp=int(time.time()),
            source="github",
            metadata={
                "delivery_id": str(webhook_data.get("delivery_id", "")),
                "hook_id": str(webhook_data.get("hook_id", "")),
            },
            payload={"github_event": github_event},
        )

        return event

    async def _poll_github_events(self):
        """Poll GitHub API for new events (fallback mode)."""
        try:
            # Get events since last poll
            events = await self.github_client.get_events_since(self._last_poll_time)

            for event_data in events:
                # Skip if we've already processed this event
                event_id = f"github-poll-{event_data.get('id', '')}"
                if event_id in self._processed_events:
                    continue

                # Create event object
                event = self._create_github_event_from_api(event_data)

                # Process event
                await self._process_event(event)

                # Mark as processed
                self._processed_events.add(event_id)

            # Update last poll time
            self._last_poll_time = datetime.now()

            # Clean up old processed events (keep last 1000)
            if len(self._processed_events) > 1000:
                old_events = list(self._processed_events)[:500]
                for old_event in old_events:
                    self._processed_events.discard(old_event)

        except Exception as e:
            logger.error(f"Error polling GitHub events: {e}")

    def _create_github_event_from_api(self, event_data: Dict[str, Any]) -> Event:
        """Create Event object from GitHub API event data."""
        # This is simplified - in practice would need more comprehensive mapping
        event_type = event_data.get("type", "unknown")
        payload_data = event_data.get("payload", {})

        github_event = GitHubEvent(
            webhook_event=event_type,
            repository=event_data.get("repo", {}).get("name", "unknown"),
            action=payload_data.get("action", "unknown"),
            actor=event_data.get("actor", {}).get("login", "unknown"),
            ref=payload_data.get("ref", ""),
            labels=[],
            title="",
            body="",
            state="",
            milestone="",
            assignees=[],
        )

        event = Event(
            event_id=f"github-poll-{event_data.get('id', '')}",
            event_type=f"github.{event_type.lower()}",
            timestamp=int(time.time()),
            source="github-poll",
            metadata={},
            payload={"github_event": github_event},
        )

        return event

    async def _process_event(self, event: Event):
        """Process an event through all matching handlers."""
        logger.debug(f"Processing event: {event.event_type}")

        matching_handlers = []

        # Find matching handlers
        for handler in self.handlers:
            if not handler.enabled:
                continue

            if handler.filter.matches(event):
                matching_handlers.append(handler)

        if not matching_handlers:
            logger.debug(f"No handlers found for event: {event.event_type}")
            return

        logger.info(
            f"Processing event {event.event_type} with {len(matching_handlers)} handlers"
        )

        # Execute handlers
        for handler in matching_handlers:
            try:
                if handler.async_execution:
                    # Execute asynchronously (fire and forget)
                    asyncio.create_task(self._execute_handler(handler, event))
                else:
                    # Execute synchronously
                    await self._execute_handler(handler, event)
            except Exception as e:
                logger.error(f"Error executing handler {handler.name}: {e}")

    async def _execute_handler(self, handler: EventHandler, event: Event):
        """Execute a single event handler."""
        try:
            logger.info(
                f"Executing handler: {handler.name} for event: {event.event_type}"
            )

            if hasattr(self, "audit_logger"):
                self.audit_logger.info(
                    f"Executing handler: {handler.name} -> {handler.invocation.agent_name}"
                )

            # Execute with timeout
            await asyncio.wait_for(
                self.agent_invoker.invoke_agent(handler.invocation, event),
                timeout=handler.timeout_seconds,
            )

            logger.info(f"Handler {handler.name} completed successfully")

        except asyncio.TimeoutError:
            logger.error(
                f"Handler {handler.name} timed out after {handler.timeout_seconds} seconds"
            )
        except Exception as e:
            logger.error(f"Handler {handler.name} failed: {e}")


def main():
    """Main entry point for the Gadugi event service."""
    import argparse

    parser = argparse.ArgumentParser(description="Gadugi Event-Driven Agent Service")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Create and run service
    try:
        service = GadugiEventService(args.config)
        service._start_time = datetime.now()
        asyncio.run(service.start())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
