#!/usr/bin/env python3
"""Main CLI entry point for Gadugi v0.3."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure we can import from orchestrator
sys.path.insert(0, str(Path(__file__).parent))

from version import __version__, get_version_string


def main() -> int:
    """Main CLI entry point for Gadugi v0.3."""
    parser = argparse.ArgumentParser(
        description=f"{get_version_string()} - Multi-agent development framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gadugi-v3 run orchestrator --task "Build an API"
  gadugi-v3 run TaskDecomposer --task "Create user authentication"
  gadugi-v3 status
  gadugi-v3 serve
        """,
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=get_version_string(),
    )

    parser.add_argument(
        "--home",
        help="Override GADUGI_HOME directory",
        default=os.environ.get("GADUGI_HOME"),
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run an agent")
    run_parser.add_argument("agent", help="Name of the agent to run")
    run_parser.add_argument("--task", help="Task description", default="")
    run_parser.add_argument("--input", help="Input file for task")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start services")
    serve_parser.add_argument("--service", help="Specific service to start", default="all")
    serve_parser.add_argument("--port", type=int, help="Port override")

    # List command
    list_parser = subparsers.add_parser("list", help="List available agents")

    args = parser.parse_args()

    # Set GADUGI_HOME if provided
    if args.home:
        os.environ["GADUGI_HOME"] = args.home

    if args.command == "run":
        # Import here to benefit from GADUGI_HOME setting
        from orchestrator.run_agent import run_agent

        task = args.task
        if args.input:
            with open(args.input) as f:
                task = f.read()

        result = run_agent(args.agent, task)

        # Print output
        if result.get("stdout"):
            print(result["stdout"])
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr)

        return result.get("returncode", 0)

    if args.command == "status":
        from orchestrator.run_agent import AGENTS_DIR, GADUGI_BASE, SERVICES_DIR

        print(f"{get_version_string()} Status")
        print("==================")
        print(f"Base Directory: {GADUGI_BASE}")
        print(f"Agents Directory: {AGENTS_DIR}")
        print(f"Services Directory: {SERVICES_DIR}")

        # List available agents
        if AGENTS_DIR.exists():
            agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir()]
            print(f"\nAvailable Agents ({len(agents)}):")
            for agent in sorted(agents):
                print(f"  - {agent}")

        # List available services
        if SERVICES_DIR.exists():
            services = [d.name for d in SERVICES_DIR.iterdir() if d.is_dir()]
            print(f"\nAvailable Services ({len(services)}):")
            for service in sorted(services):
                print(f"  - {service}")

    elif args.command == "serve":
        print(f"Starting services: {args.service}")
        if args.service == "cli":
            from services.cli.gadugi_cli_service import main as cli_main
            return cli_main()
        if args.service == "event-router":
            from services.event_router.event_router_service import main as event_main
            return event_main()
        if args.service == "all":
            print("Starting all services...")
            # Could use subprocess to start each service
        else:
            print(f"Unknown service: {args.service}")
            return 1

    elif args.command == "list":
        from orchestrator.run_agent import AGENTS_DIR

        if AGENTS_DIR.exists():
            agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir()]
            print("Available Agents:")
            for agent in sorted(agents):
                agent_file = AGENTS_DIR / agent / "agent.md"
                if agent_file.exists():
                    # Try to extract description from agent.md
                    with open(agent_file) as f:
                        lines = f.readlines()
                        for line in lines[:10]:  # Check first 10 lines
                            if line.startswith("description:"):
                                desc = line.replace("description:", "").strip()
                                print(f"  {agent:<25} - {desc}")
                                break
                        else:
                            print(f"  {agent}")
                else:
                    print(f"  {agent}")

    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
