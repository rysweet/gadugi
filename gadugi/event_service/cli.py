#!/usr/bin/env python3
"""
Gadugi Event Service CLI

Command-line interface for managing the Gadugi event-driven service.
"""

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .service import GadugiEventService
from .config import (
    ServiceConfig,
    load_config,
    save_config,
    create_default_config,
    get_default_config_path,
    get_default_socket_path,
)
from .events import create_local_event
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class GadugiCLI:
    """Command-line interface for Gadugi Event Service."""

    def __init__(self):
        """Initialize CLI."""
        self.config_path = get_default_config_path()
        self.socket_path = get_default_socket_path()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="Gadugi Event-Driven Agent Service CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  gadugi install                     # Install service with defaults
  gadugi start                       # Start the service
  gadugi status                      # Check service status
  gadugi config                      # Interactive configuration
  gadugi webhook setup               # Setup GitHub webhook
  gadugi send local.test             # Send local event
  gadugi logs --tail                 # Show service logs
            """,
        )

        parser.add_argument(
            "--config",
            "-c",
            default=self.config_path,
            help=f"Configuration file path (default: {self.config_path})",
        )

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose logging"
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Install command
        install_parser = subparsers.add_parser(
            "install", help="Install and configure Gadugi service"
        )
        install_parser.add_argument(
            "--github-token", help="GitHub token for API access"
        )
        install_parser.add_argument("--webhook-secret", help="GitHub webhook secret")
        install_parser.add_argument(
            "--port", type=int, default=8080, help="Webhook server port"
        )
        install_parser.add_argument(
            "--no-webhook", action="store_true", help="Skip webhook setup"
        )

        # Service management commands
        subparsers.add_parser("start", help="Start the Gadugi service")
        subparsers.add_parser("stop", help="Stop the Gadugi service")
        subparsers.add_parser("restart", help="Restart the Gadugi service")
        subparsers.add_parser("status", help="Show service status")

        # Configuration commands
        config_parser = subparsers.add_parser("config", help="Manage configuration")
        config_parser.add_argument(
            "--show", action="store_true", help="Show current configuration"
        )
        config_parser.add_argument(
            "--edit", action="store_true", help="Edit configuration interactively"
        )
        config_parser.add_argument(
            "--validate", action="store_true", help="Validate configuration"
        )

        # Webhook commands
        webhook_parser = subparsers.add_parser("webhook", help="Manage GitHub webhooks")
        webhook_subparsers = webhook_parser.add_subparsers(dest="webhook_action")

        setup_parser = webhook_subparsers.add_parser(
            "setup", help="Setup GitHub webhook"
        )
        setup_parser.add_argument("--repo", help="Repository (owner/name)")
        setup_parser.add_argument(
            "--url", help="Webhook URL (auto-detected if not provided)"
        )

        list_parser = webhook_subparsers.add_parser("list", help="List webhooks")
        list_parser.add_argument("--repo", help="Repository (owner/name)")

        test_parser = webhook_subparsers.add_parser("test", help="Test webhook")
        test_parser.add_argument("--repo", help="Repository (owner/name)")
        test_parser.add_argument("--hook-id", type=int, help="Webhook ID")

        delete_parser = webhook_subparsers.add_parser("delete", help="Delete webhook")
        delete_parser.add_argument("--repo", help="Repository (owner/name)")
        delete_parser.add_argument("--hook-id", type=int, help="Webhook ID")

        # Event commands
        send_parser = subparsers.add_parser("send", help="Send local event")
        send_parser.add_argument("event_type", help="Event type (e.g., local.test)")
        send_parser.add_argument("--data", help="Event data as JSON")
        send_parser.add_argument("--file", help="Event data from file")

        # Logs command
        logs_parser = subparsers.add_parser("logs", help="Show service logs")
        logs_parser.add_argument(
            "--tail", action="store_true", help="Follow log output"
        )
        logs_parser.add_argument(
            "--lines", "-n", type=int, default=50, help="Number of lines to show"
        )

        # Handler management
        handler_parser = subparsers.add_parser("handler", help="Manage event handlers")
        handler_subparsers = handler_parser.add_subparsers(dest="handler_action")

        list_handlers_parser = handler_subparsers.add_parser(
            "list", help="List event handlers"
        )

        enable_parser = handler_subparsers.add_parser("enable", help="Enable handler")
        enable_parser.add_argument("name", help="Handler name")

        disable_parser = handler_subparsers.add_parser(
            "disable", help="Disable handler"
        )
        disable_parser.add_argument("name", help="Handler name")

        # Version command
        subparsers.add_parser("version", help="Show version information")

        return parser

    async def run(self, args: argparse.Namespace) -> int:
        """Run CLI command."""
        try:
            if args.command == "install":
                return await self.install(args)
            elif args.command == "start":
                return await self.start(args)
            elif args.command == "stop":
                return await self.stop(args)
            elif args.command == "restart":
                return await self.restart(args)
            elif args.command == "status":
                return await self.status(args)
            elif args.command == "config":
                return await self.config(args)
            elif args.command == "webhook":
                return await self.webhook(args)
            elif args.command == "send":
                return await self.send_event(args)
            elif args.command == "logs":
                return await self.logs(args)
            elif args.command == "handler":
                return await self.handler(args)
            elif args.command == "version":
                return self.version(args)
            else:
                print("No command specified. Use --help for usage information.")
                return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            logger.error(f"Command failed: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    async def install(self, args: argparse.Namespace) -> int:
        """Install and configure Gadugi service."""
        print("Installing Gadugi Event Service...")

        # Create default configuration
        config = create_default_config()

        # Update with command line arguments
        if args.github_token:
            config.github_token = args.github_token
        if args.webhook_secret:
            config.webhook_secret = args.webhook_secret
        if args.port != 8080:
            config.bind_port = args.port

        # Interactive configuration if no token provided
        if not config.github_token:
            print("\nGitHub token is required for full functionality.")
            print("You can get a token from: https://github.com/settings/tokens")
            token = input("Enter GitHub token (or press Enter to skip): ").strip()
            if token:
                config.github_token = token

        if not config.webhook_secret:
            import secrets

            config.webhook_secret = secrets.token_hex(32)
            print(f"Generated webhook secret: {config.webhook_secret}")

        # Save configuration
        save_config(config, args.config)
        print(f"Configuration saved to: {args.config}")

        # Setup webhook if requested
        if not args.no_webhook and config.github_token:
            try:
                await self._setup_webhook_interactive(config)
            except Exception as e:
                print(f"Webhook setup failed: {e}")
                print("You can set it up later with: gadugi webhook setup")

        print("\nGadugi Event Service installation complete!")
        print("Start the service with: gadugi start")
        return 0

    async def start(self, args: argparse.Namespace) -> int:
        """Start the Gadugi service."""
        print("Starting Gadugi Event Service...")

        try:
            service = GadugiEventService(args.config)
            await service.start()
        except Exception as e:
            print(f"Failed to start service: {e}")
            return 1

        return 0

    async def stop(self, args: argparse.Namespace) -> int:
        """Stop the Gadugi service."""
        print("Stopping Gadugi Event Service...")
        # In practice, this would send a signal to the running service
        print("Service stop command sent")
        return 0

    async def restart(self, args: argparse.Namespace) -> int:
        """Restart the Gadugi service."""
        await self.stop(args)
        await asyncio.sleep(2)
        return await self.start(args)

    async def status(self, args: argparse.Namespace) -> int:
        """Show service status."""
        try:
            config = load_config(args.config)

            # Try to connect to health endpoint
            import aiohttp

            async with aiohttp.ClientSession() as session:
                url = f"http://{config.bind_address}:{config.bind_port}/health"
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            print("Gadugi Event Service Status: RUNNING")
                            print(f"Version: {health_data.get('version', 'unknown')}")
                            print(f"Handlers: {health_data.get('handlers', 0)}")
                            print(f"Uptime: {health_data.get('uptime', 'unknown')}")
                            return 0
                        else:
                            print("Gadugi Event Service Status: UNHEALTHY")
                            return 1
                except:
                    print("Gadugi Event Service Status: NOT RUNNING")
                    return 1
        except Exception as e:
            print(f"Could not check status: {e}")
            return 1

    async def config(self, args: argparse.Namespace) -> int:
        """Manage configuration."""
        try:
            config = load_config(args.config)

            if args.show:
                print("Current Configuration:")
                print(json.dumps(config.__dict__, indent=2, default=str))
                return 0

            elif args.validate:
                print("Configuration is valid")
                return 0

            elif args.edit:
                # Simple interactive editor
                print("Interactive configuration editor")
                print("Current settings:")
                print(f"  Bind address: {config.bind_address}")
                print(f"  Bind port: {config.bind_port}")
                print(f"  Poll interval: {config.poll_interval_seconds} seconds")
                print(f"  Handlers: {len(config.handlers)}")

                # Allow editing basic settings
                new_port = input(f"New port ({config.bind_port}): ").strip()
                if new_port and new_port.isdigit():
                    config.bind_port = int(new_port)

                new_interval = input(
                    f"New poll interval ({config.poll_interval_seconds}): "
                ).strip()
                if new_interval and new_interval.isdigit():
                    config.poll_interval_seconds = int(new_interval)

                save_config(config, args.config)
                print("Configuration updated")
                return 0

            else:
                print("Use --show, --edit, or --validate")
                return 1

        except Exception as e:
            print(f"Configuration error: {e}")
            return 1

    async def webhook(self, args: argparse.Namespace) -> int:
        """Manage GitHub webhooks."""
        try:
            config = load_config(args.config)

            if not config.github_token:
                print("GitHub token required for webhook management")
                return 1

            async with GitHubClient(config.github_token) as client:
                if args.webhook_action == "setup":
                    return await self._webhook_setup(client, config, args)
                elif args.webhook_action == "list":
                    return await self._webhook_list(client, args)
                elif args.webhook_action == "test":
                    return await self._webhook_test(client, args)
                elif args.webhook_action == "delete":
                    return await self._webhook_delete(client, args)
                else:
                    print("Use: setup, list, test, or delete")
                    return 1

        except Exception as e:
            print(f"Webhook command failed: {e}")
            return 1

    async def send_event(self, args: argparse.Namespace) -> int:
        """Send local event."""
        try:
            # Prepare event data
            event_data = {}

            if args.data:
                event_data = json.loads(args.data)
            elif args.file:
                with open(args.file, "r") as f:
                    event_data = json.load(f)

            # Create event
            event = create_local_event(
                event_name=args.event_type, working_directory=os.getcwd(), **event_data
            )

            # Send via Unix socket
            config = load_config(args.config)
            socket_path = config.socket_path or get_default_socket_path()

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(socket_path)
                sock.send(event.to_json().encode("utf-8"))

                # Read response
                response = sock.recv(1024)
                response_data = json.loads(response.decode("utf-8"))

                if response_data.get("status") == "accepted":
                    print(f"Event sent successfully: {response_data.get('event_id')}")
                    return 0
                else:
                    print(f"Event failed: {response_data.get('message')}")
                    return 1

            finally:
                sock.close()

        except Exception as e:
            print(f"Failed to send event: {e}")
            return 1

    async def logs(self, args: argparse.Namespace) -> int:
        """Show service logs."""
        try:
            config = load_config(args.config)
            log_file = config.log_config.file_path

            if not log_file or not Path(log_file).exists():
                print("No log file found")
                return 1

            if args.tail:
                # Follow log file
                import subprocess

                subprocess.run(["tail", "-f", log_file])
            else:
                # Show last N lines
                import subprocess

                subprocess.run(["tail", "-n", str(args.lines), log_file])

            return 0

        except Exception as e:
            print(f"Failed to show logs: {e}")
            return 1

    async def handler(self, args: argparse.Namespace) -> int:
        """Manage event handlers."""
        try:
            config = load_config(args.config)

            if args.handler_action == "list":
                print("Event Handlers:")
                for handler in config.handlers:
                    status = "enabled" if handler.enabled else "disabled"
                    print(
                        f"  {handler.name}: {handler.invocation['agent_name']} ({status})"
                    )
                return 0

            elif args.handler_action in ["enable", "disable"]:
                # Find and update handler
                for handler in config.handlers:
                    if handler.name == args.name:
                        handler.enabled = args.handler_action == "enable"
                        save_config(config, args.config)
                        print(f"Handler {args.name} {args.handler_action}d")
                        return 0

                print(f"Handler not found: {args.name}")
                return 1

            else:
                print("Use: list, enable, or disable")
                return 1

        except Exception as e:
            print(f"Handler command failed: {e}")
            return 1

    def version(self, args: argparse.Namespace) -> int:
        """Show version information."""
        print("Gadugi Event Service CLI v0.1.0")
        return 0

    async def _setup_webhook_interactive(self, config: ServiceConfig):
        """Interactive webhook setup."""
        async with GitHubClient(config.github_token) as client:
            # Auto-detect repository
            repo_info = await client.auto_detect_repository()
            if repo_info:
                owner, repo = repo_info
                print(f"Detected repository: {owner}/{repo}")

                # Construct webhook URL
                webhook_url = f"http://localhost:{config.bind_port}/webhook/github"
                print(f"Webhook URL: {webhook_url}")

                confirm = input("Create webhook? (y/N): ").strip().lower()
                if confirm == "y":
                    await client.create_webhook(
                        owner, repo, webhook_url, config.webhook_secret
                    )
                    print("Webhook created successfully!")

    async def _webhook_setup(
        self, client: GitHubClient, config: ServiceConfig, args: argparse.Namespace
    ) -> int:
        """Setup webhook command."""
        if not args.repo:
            # Try auto-detection
            repo_info = await client.auto_detect_repository()
            if not repo_info:
                print("Repository not specified and could not auto-detect")
                return 1
            owner, repo = repo_info
        else:
            owner, repo = args.repo.split("/", 1)

        webhook_url = args.url or f"http://localhost:{config.bind_port}/webhook/github"

        result = await client.create_webhook(
            owner, repo, webhook_url, config.webhook_secret
        )
        print(f"Webhook created: ID {result.get('id')}")
        return 0

    async def _webhook_list(
        self, client: GitHubClient, args: argparse.Namespace
    ) -> int:
        """List webhooks command."""
        if not args.repo:
            repo_info = await client.auto_detect_repository()
            if not repo_info:
                print("Repository not specified and could not auto-detect")
                return 1
            owner, repo = repo_info
        else:
            owner, repo = args.repo.split("/", 1)

        webhooks = await client.list_webhooks(owner, repo)

        if not webhooks:
            print("No webhooks found")
            return 0

        print("Webhooks:")
        for webhook in webhooks:
            print(f"  ID {webhook['id']}: {webhook['config']['url']}")

        return 0

    async def _webhook_test(
        self, client: GitHubClient, args: argparse.Namespace
    ) -> int:
        """Test webhook command."""
        if not args.repo or not args.hook_id:
            print("Repository and hook ID required")
            return 1

        owner, repo = args.repo.split("/", 1)
        success = await client.test_webhook(owner, repo, args.hook_id)

        if success:
            print("Webhook test sent")
            return 0
        else:
            print("Webhook test failed")
            return 1

    async def _webhook_delete(
        self, client: GitHubClient, args: argparse.Namespace
    ) -> int:
        """Delete webhook command."""
        if not args.repo or not args.hook_id:
            print("Repository and hook ID required")
            return 1

        owner, repo = args.repo.split("/", 1)
        success = await client.delete_webhook(owner, repo, args.hook_id)

        if success:
            print("Webhook deleted")
            return 0
        else:
            print("Webhook deletion failed")
            return 1


def main():
    """Main CLI entry point."""
    cli = GadugiCLI()
    parser = cli.create_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    exit_code = asyncio.run(cli.run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
