#!/usr/bin/env python3
"""
Gadugi CLI Service for Gadugi v0.3

Unified command-line interface for all Gadugi operations.
Provides comprehensive CLI commands, service management, and user interaction.
"""

import asyncio
import argparse
import json
import logging
import os
import subprocess
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util
import signal
import psutil

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

try:
    import rich
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Mock rich components
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def input(self, prompt): return input(prompt)
    
    class Table: pass
    class Panel: pass
    class Progress: pass
    class SpinnerColumn: pass
    class TextColumn: pass
    class Prompt:
        @staticmethod
        def ask(prompt, default=None): return input(f"{prompt} [{default}]: ") or default
    class Confirm:
        @staticmethod
        def ask(prompt): return input(f"{prompt} (y/n): ").lower().startswith('y')
    class Syntax: pass
    class Tree: pass


class ServiceType(Enum):
    """Service type enumeration."""
    EVENT_ROUTER = "event-router"
    NEO4J_GRAPH = "neo4j-graph"
    MCP = "mcp"
    LLM_PROXY = "llm-proxy"
    ORCHESTRATOR = "orchestrator"
    WORKFLOW_MANAGER = "workflow-manager"
    ALL = "all"


class CommandCategory(Enum):
    """Command category enumeration."""
    SERVICE = "service"
    AGENT = "agent"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    GRAPH = "graph"
    LLM = "llm"
    DEVELOPMENT = "development"
    SYSTEM = "system"


class ServiceStatus(Enum):
    """Service status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CommandResult:
    """Result of a CLI command execution."""
    success: bool
    message: str
    data: Any = None
    execution_time: float = 0.0
    warnings: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


@dataclass
class ServiceInfo:
    """Information about a service."""
    name: str
    type: ServiceType
    status: ServiceStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    uptime: Optional[str] = None
    memory_usage: Optional[str] = None
    cpu_usage: Optional[float] = None
    description: str = ""


@dataclass
class AgentInfo:
    """Information about an agent."""
    name: str
    path: str
    description: str
    category: str
    dependencies: List[str] = None
    last_used: Optional[datetime] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceManager:
    """Manages Gadugi services."""
    
    def __init__(self):
        self.logger = logging.getLogger("service_manager")
        self.services: Dict[str, ServiceInfo] = {}
        self.service_configs = {
            "event-router": {
                "module": "services.event-router.event_router_service",
                "class": "EventRouterService",
                "port": 9090,
                "description": "Event routing and coordination service"
            },
            "neo4j-graph": {
                "module": "services.neo4j-graph.neo4j_graph_service",
                "class": "GraphDatabaseService", 
                "port": 7687,
                "description": "Graph database service for relationships and knowledge"
            },
            "mcp": {
                "module": "services.mcp.mcp_service",
                "class": "MCPService",
                "port": None,
                "description": "Memory and context persistence service"
            },
            "llm-proxy": {
                "module": "services.llm-proxy.llm_proxy_service",
                "class": "LLMProxyService",
                "port": 8080,
                "description": "LLM provider abstraction and proxy service"
            }
        }
    
    async def start_service(self, service_name: str) -> CommandResult:
        """Start a Gadugi service."""
        start_time = time.time()
        
        try:
            if service_name not in self.service_configs:
                return CommandResult(
                    success=False,
                    message=f"Unknown service: {service_name}",
                    execution_time=time.time() - start_time
                )
            
            # Check if service is already running
            status = await self.get_service_status(service_name)
            if status.status == ServiceStatus.RUNNING:
                return CommandResult(
                    success=True,
                    message=f"Service {service_name} is already running",
                    execution_time=time.time() - start_time,
                    warnings=[f"Service was already running with PID {status.pid}"]
                )
            
            config = self.service_configs[service_name]
            
            # Start service as subprocess
            service_script = Path(__file__).parent / "service_launcher.py"
            cmd = [
                sys.executable, str(service_script),
                "--service", service_name,
                "--module", config["module"],
                "--class", config["class"]
            ]
            
            if config["port"]:
                cmd.extend(["--port", str(config["port"])])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait a moment to check if service started successfully
            await asyncio.sleep(2)
            
            if process.poll() is None:  # Process is still running
                self.services[service_name] = ServiceInfo(
                    name=service_name,
                    type=ServiceType(service_name),
                    status=ServiceStatus.RUNNING,
                    pid=process.pid,
                    port=config["port"],
                    description=config["description"]
                )
                
                return CommandResult(
                    success=True,
                    message=f"Service {service_name} started successfully",
                    data={"pid": process.pid, "port": config["port"]},
                    execution_time=time.time() - start_time
                )
            else:
                stdout, stderr = process.communicate()
                return CommandResult(
                    success=False,
                    message=f"Failed to start service {service_name}",
                    execution_time=time.time() - start_time,
                    errors=[stderr.decode() if stderr else "Unknown error"]
                )
                
        except Exception as e:
            self.logger.error(f"Error starting service {service_name}: {e}")
            return CommandResult(
                success=False,
                message=f"Error starting service {service_name}: {str(e)}",
                execution_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def stop_service(self, service_name: str) -> CommandResult:
        """Stop a Gadugi service."""
        start_time = time.time()
        
        try:
            status = await self.get_service_status(service_name)
            
            if status.status != ServiceStatus.RUNNING:
                return CommandResult(
                    success=True,
                    message=f"Service {service_name} is not running",
                    execution_time=time.time() - start_time
                )
            
            if status.pid:
                try:
                    # Try graceful shutdown first
                    process = psutil.Process(status.pid)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        process.kill()
                        process.wait(timeout=5)
                    
                    # Remove from services registry
                    if service_name in self.services:
                        del self.services[service_name]
                    
                    return CommandResult(
                        success=True,
                        message=f"Service {service_name} stopped successfully",
                        execution_time=time.time() - start_time
                    )
                    
                except psutil.NoSuchProcess:
                    # Process already dead
                    if service_name in self.services:
                        del self.services[service_name]
                    
                    return CommandResult(
                        success=True,
                        message=f"Service {service_name} was not running",
                        execution_time=time.time() - start_time
                    )
                    
            else:
                return CommandResult(
                    success=False,
                    message=f"No PID found for service {service_name}",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self.logger.error(f"Error stopping service {service_name}: {e}")
            return CommandResult(
                success=False,
                message=f"Error stopping service {service_name}: {str(e)}",
                execution_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def restart_service(self, service_name: str) -> CommandResult:
        """Restart a Gadugi service."""
        start_time = time.time()
        
        # Stop service first
        stop_result = await self.stop_service(service_name)
        if not stop_result.success and "not running" not in stop_result.message:
            return stop_result
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Start service
        start_result = await self.start_service(service_name)
        
        return CommandResult(
            success=start_result.success,
            message=f"Service {service_name} restarted: {start_result.message}",
            data=start_result.data,
            execution_time=time.time() - start_time,
            warnings=stop_result.warnings + start_result.warnings,
            errors=stop_result.errors + start_result.errors
        )
    
    async def get_service_status(self, service_name: str) -> ServiceInfo:
        """Get status of a specific service."""
        if service_name in self.services:
            service_info = self.services[service_name]
            
            # Update status by checking if process is still running
            if service_info.pid:
                try:
                    process = psutil.Process(service_info.pid)
                    if process.is_running():
                        service_info.status = ServiceStatus.RUNNING
                        service_info.memory_usage = f"{process.memory_info().rss / 1024 / 1024:.1f}MB"
                        service_info.cpu_usage = process.cpu_percent()
                        
                        # Calculate uptime
                        create_time = datetime.fromtimestamp(process.create_time())
                        uptime = datetime.now() - create_time
                        service_info.uptime = str(uptime).split('.')[0]  # Remove microseconds
                    else:
                        service_info.status = ServiceStatus.STOPPED
                        service_info.pid = None
                        
                except psutil.NoSuchProcess:
                    service_info.status = ServiceStatus.STOPPED
                    service_info.pid = None
            
            return service_info
        
        # Service not in registry, try to find it by name
        config = self.service_configs.get(service_name)
        if config:
            return ServiceInfo(
                name=service_name,
                type=ServiceType(service_name) if service_name != "all" else ServiceType.ALL,
                status=ServiceStatus.STOPPED,
                description=config["description"]
            )
        
        return ServiceInfo(
            name=service_name,
            type=ServiceType.ALL,
            status=ServiceStatus.UNKNOWN,
            description="Unknown service"
        )
    
    async def list_services(self) -> List[ServiceInfo]:
        """List all available services."""
        services = []
        
        for service_name in self.service_configs.keys():
            service_info = await self.get_service_status(service_name)
            services.append(service_info)
        
        return services


class AgentManager:
    """Manages Gadugi agents."""
    
    def __init__(self):
        self.logger = logging.getLogger("agent_manager")
        self.agents: Dict[str, AgentInfo] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Discover available agents."""
        # Look for agents in standard locations
        agent_paths = [
            Path(__file__).parent.parent.parent / "agents",
            Path(__file__).parent.parent.parent / ".claude" / "agents"
        ]
        
        for agent_dir in agent_paths:
            if agent_dir.exists():
                self._scan_agent_directory(agent_dir)
    
    def _scan_agent_directory(self, directory: Path):
        """Scan directory for agent files."""
        for agent_file in directory.glob("**/*.md"):
            try:
                agent_info = self._parse_agent_file(agent_file)
                if agent_info:
                    self.agents[agent_info.name] = agent_info
            except Exception as e:
                self.logger.warning(f"Error parsing agent file {agent_file}: {e}")
    
    def _parse_agent_file(self, agent_file: Path) -> Optional[AgentInfo]:
        """Parse an agent file to extract information."""
        try:
            content = agent_file.read_text()
            
            # Extract basic info from file
            name = agent_file.stem
            description = "No description available"
            category = "general"
            dependencies = []
            
            # Try to extract description from first few lines
            lines = content.split('\n')[:10]
            for line in lines:
                if line.strip().startswith('#') and len(line.strip()) > 2:
                    description = line.strip()[1:].strip()
                    break
            
            # Try to determine category from path
            if "workflow" in str(agent_file).lower():
                category = "workflow"
            elif "memory" in str(agent_file).lower():
                category = "memory"
            elif "code" in str(agent_file).lower():
                category = "development"
            elif "test" in str(agent_file).lower():
                category = "testing"
            elif "orchestrator" in str(agent_file).lower():
                category = "orchestration"
            
            return AgentInfo(
                name=name,
                path=str(agent_file),
                description=description,
                category=category,
                dependencies=dependencies
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing agent file {agent_file}: {e}")
            return None
    
    def list_agents(self, category: Optional[str] = None) -> List[AgentInfo]:
        """List available agents."""
        agents = list(self.agents.values())
        
        if category:
            agents = [agent for agent in agents if agent.category == category]
        
        return sorted(agents, key=lambda x: x.name)
    
    def get_agent_categories(self) -> List[str]:
        """Get list of agent categories."""
        categories = set(agent.category for agent in self.agents.values())
        return sorted(list(categories))
    
    async def invoke_agent(self, agent_name: str, prompt: str, **kwargs) -> CommandResult:
        """Invoke an agent."""
        start_time = time.time()
        
        try:
            if agent_name not in self.agents:
                return CommandResult(
                    success=False,
                    message=f"Agent not found: {agent_name}",
                    execution_time=time.time() - start_time
                )
            
            agent_info = self.agents[agent_name]
            
            # Use Claude CLI to invoke agent
            cmd = ["claude", f"/agent:{agent_name}", prompt]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Update last used time
                agent_info.last_used = datetime.now()
                
                return CommandResult(
                    success=True,
                    message=f"Agent {agent_name} executed successfully",
                    data=stdout.decode(),
                    execution_time=time.time() - start_time
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Agent {agent_name} execution failed",
                    execution_time=time.time() - start_time,
                    errors=[stderr.decode() if stderr else "Unknown error"]
                )
                
        except Exception as e:
            self.logger.error(f"Error invoking agent {agent_name}: {e}")
            return CommandResult(
                success=False,
                message=f"Error invoking agent {agent_name}: {str(e)}",
                execution_time=time.time() - start_time,
                errors=[str(e)]
            )


class GadugiCLI:
    """Main Gadugi CLI interface."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else Console()
        self.service_manager = ServiceManager()
        self.agent_manager = AgentManager()
        self.logger = self._setup_logging()
        
        # CLI state
        self.verbose = False
        self.output_format = "rich" if RICH_AVAILABLE else "plain"
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the CLI."""
        logger = logging.getLogger("gadugi_cli")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            description="Gadugi v0.3 - Multi-Agent Development Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  gadugi service start event-router    Start the event router service
  gadugi service list                  List all services and their status
  gadugi agent list                    List all available agents
  gadugi agent invoke orchestrator     Invoke the orchestrator agent
  gadugi workflow run feature.md       Run a workflow from a prompt file
  gadugi system health                 Check system health
  gadugi dev setup                     Set up development environment
            """
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        parser.add_argument(
            "--format",
            choices=["rich", "plain", "json"],
            default="rich" if RICH_AVAILABLE else "plain",
            help="Output format"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Service management
        service_parser = subparsers.add_parser("service", help="Service management")
        service_subparsers = service_parser.add_subparsers(dest="service_action")
        
        # service start
        start_parser = service_subparsers.add_parser("start", help="Start a service")
        start_parser.add_argument("service_name", help="Name of the service to start")
        
        # service stop
        stop_parser = service_subparsers.add_parser("stop", help="Stop a service")
        stop_parser.add_argument("service_name", help="Name of the service to stop")
        
        # service restart
        restart_parser = service_subparsers.add_parser("restart", help="Restart a service")
        restart_parser.add_argument("service_name", help="Name of the service to restart")
        
        # service status
        status_parser = service_subparsers.add_parser("status", help="Get service status")
        status_parser.add_argument("service_name", nargs="?", help="Name of the service")
        
        # service list
        service_subparsers.add_parser("list", help="List all services")
        
        # Agent management
        agent_parser = subparsers.add_parser("agent", help="Agent management")
        agent_subparsers = agent_parser.add_subparsers(dest="agent_action")
        
        # agent list
        list_parser = agent_subparsers.add_parser("list", help="List available agents")
        list_parser.add_argument("--category", help="Filter by category")
        
        # agent invoke
        invoke_parser = agent_subparsers.add_parser("invoke", help="Invoke an agent")
        invoke_parser.add_argument("agent_name", help="Name of the agent to invoke")
        invoke_parser.add_argument("prompt", help="Prompt or input for the agent")
        
        # agent info
        info_parser = agent_subparsers.add_parser("info", help="Get agent information")
        info_parser.add_argument("agent_name", help="Name of the agent")
        
        # Workflow management
        workflow_parser = subparsers.add_parser("workflow", help="Workflow management")
        workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_action")
        
        # workflow run
        run_parser = workflow_subparsers.add_parser("run", help="Run a workflow")
        run_parser.add_argument("prompt_file", help="Path to prompt file")
        run_parser.add_argument("--parallel", action="store_true", help="Enable parallel execution")
        
        # workflow status
        workflow_subparsers.add_parser("status", help="Get workflow status")
        
        # System management
        system_parser = subparsers.add_parser("system", help="System management")
        system_subparsers = system_parser.add_subparsers(dest="system_action")
        
        # system health
        system_subparsers.add_parser("health", help="Check system health")
        
        # system info
        system_subparsers.add_parser("info", help="Get system information")
        
        # Development tools
        dev_parser = subparsers.add_parser("dev", help="Development tools")
        dev_subparsers = dev_parser.add_subparsers(dest="dev_action")
        
        # dev setup
        system_subparsers.add_parser("setup", help="Set up development environment")
        
        # dev test
        test_parser = dev_subparsers.add_parser("test", help="Run tests")
        test_parser.add_argument("--module", help="Specific module to test")
        
        # dev build
        dev_subparsers.add_parser("build", help="Build the project")
        
        return parser
    
    async def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        self.verbose = parsed_args.verbose
        self.output_format = parsed_args.format
        
        try:
            if parsed_args.command == "service":
                return await self._handle_service_command(parsed_args)
            elif parsed_args.command == "agent":
                return await self._handle_agent_command(parsed_args)
            elif parsed_args.command == "workflow":
                return await self._handle_workflow_command(parsed_args)
            elif parsed_args.command == "system":
                return await self._handle_system_command(parsed_args)
            elif parsed_args.command == "dev":
                return await self._handle_dev_command(parsed_args)
            else:
                parser.print_help()
                return 0
                
        except KeyboardInterrupt:
            self.console.print("\n[red]Interrupted by user[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            if self.verbose:
                import traceback
                self.console.print(f"[red]{traceback.format_exc()}[/red]")
            return 1
    
    async def _handle_service_command(self, args) -> int:
        """Handle service management commands."""
        if args.service_action == "start":
            result = await self.service_manager.start_service(args.service_name)
            self._print_command_result(result)
            return 0 if result.success else 1
            
        elif args.service_action == "stop":
            result = await self.service_manager.stop_service(args.service_name)
            self._print_command_result(result)
            return 0 if result.success else 1
            
        elif args.service_action == "restart":
            result = await self.service_manager.restart_service(args.service_name)
            self._print_command_result(result)
            return 0 if result.success else 1
            
        elif args.service_action == "status":
            if args.service_name:
                service_info = await self.service_manager.get_service_status(args.service_name)
                self._print_service_info(service_info)
            else:
                services = await self.service_manager.list_services()
                self._print_services_list(services)
            return 0
            
        elif args.service_action == "list":
            services = await self.service_manager.list_services()
            self._print_services_list(services)
            return 0
        
        return 0
    
    async def _handle_agent_command(self, args) -> int:
        """Handle agent management commands."""
        if args.agent_action == "list":
            agents = self.agent_manager.list_agents(args.category)
            self._print_agents_list(agents)
            return 0
            
        elif args.agent_action == "invoke":
            result = await self.agent_manager.invoke_agent(args.agent_name, args.prompt)
            self._print_command_result(result)
            return 0 if result.success else 1
            
        elif args.agent_action == "info":
            agents = self.agent_manager.list_agents()
            agent = next((a for a in agents if a.name == args.agent_name), None)
            if agent:
                self._print_agent_info(agent)
                return 0
            else:
                self.console.print(f"[red]Agent not found: {args.agent_name}[/red]")
                return 1
        
        return 0
    
    async def _handle_workflow_command(self, args) -> int:
        """Handle workflow management commands."""
        if args.workflow_action == "run":
            # Use orchestrator agent for workflow execution
            if args.parallel:
                prompt = f"Execute workflow from {args.prompt_file} in parallel"
                result = await self.agent_manager.invoke_agent("orchestrator-agent", prompt)
            else:
                prompt = f"Execute workflow from {args.prompt_file}"
                result = await self.agent_manager.invoke_agent("workflow-manager", prompt)
            
            self._print_command_result(result)
            return 0 if result.success else 1
            
        elif args.workflow_action == "status":
            self.console.print("[yellow]Workflow status tracking not yet implemented[/yellow]")
            return 0
        
        return 0
    
    async def _handle_system_command(self, args) -> int:
        """Handle system management commands."""
        if args.system_action == "health":
            await self._check_system_health()
            return 0
            
        elif args.system_action == "info":
            await self._show_system_info()
            return 0
        
        return 0
    
    async def _handle_dev_command(self, args) -> int:
        """Handle development tools commands."""
        if args.dev_action == "setup":
            await self._setup_development_environment()
            return 0
            
        elif args.dev_action == "test":
            await self._run_tests(args.module)
            return 0
            
        elif args.dev_action == "build":
            await self._build_project()
            return 0
        
        return 0
    
    def _print_command_result(self, result: CommandResult):
        """Print command result."""
        if self.output_format == "json":
            self.console.print(json.dumps(asdict(result), indent=2, default=str))
        elif self.output_format == "rich" and RICH_AVAILABLE:
            if result.success:
                self.console.print(f"[green]✓[/green] {result.message}")
            else:
                self.console.print(f"[red]✗[/red] {result.message}")
            
            if result.data and self.verbose:
                self.console.print(f"Data: {result.data}")
            
            if result.warnings:
                for warning in result.warnings:
                    self.console.print(f"[yellow]⚠[/yellow] {warning}")
            
            if result.errors:
                for error in result.errors:
                    self.console.print(f"[red]✗[/red] {error}")
            
            if self.verbose:
                self.console.print(f"Execution time: {result.execution_time:.2f}s")
        else:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.message}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"⚠ {warning}")
            
            if result.errors:
                for error in result.errors:
                    print(f"✗ {error}")
    
    def _print_service_info(self, service: ServiceInfo):
        """Print service information."""
        if self.output_format == "json":
            self.console.print(json.dumps(asdict(service), indent=2, default=str))
        elif self.output_format == "rich" and RICH_AVAILABLE:
            status_color = {
                ServiceStatus.RUNNING: "green",
                ServiceStatus.STOPPED: "red", 
                ServiceStatus.ERROR: "red",
                ServiceStatus.UNKNOWN: "yellow"
            }.get(service.status, "white")
            
            panel_content = [
                f"Status: [{status_color}]{service.status.value}[/{status_color}]",
                f"Type: {service.type.value}",
                f"Description: {service.description}"
            ]
            
            if service.pid:
                panel_content.append(f"PID: {service.pid}")
            if service.port:
                panel_content.append(f"Port: {service.port}")
            if service.uptime:
                panel_content.append(f"Uptime: {service.uptime}")
            if service.memory_usage:
                panel_content.append(f"Memory: {service.memory_usage}")
            if service.cpu_usage is not None:
                panel_content.append(f"CPU: {service.cpu_usage:.1f}%")
            
            panel = Panel(
                "\n".join(panel_content),
                title=f"Service: {service.name}",
                border_style=status_color
            )
            self.console.print(panel)
        else:
            print(f"Service: {service.name}")
            print(f"  Status: {service.status.value}")
            print(f"  Type: {service.type.value}")
            print(f"  Description: {service.description}")
            if service.pid:
                print(f"  PID: {service.pid}")
            if service.port:
                print(f"  Port: {service.port}")
    
    def _print_services_list(self, services: List[ServiceInfo]):
        """Print list of services."""
        if self.output_format == "json":
            self.console.print(json.dumps([asdict(s) for s in services], indent=2, default=str))
        elif self.output_format == "rich" and RICH_AVAILABLE:
            table = Table(title="Gadugi Services")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Status")
            table.add_column("PID")
            table.add_column("Port")
            table.add_column("Uptime")
            table.add_column("Memory")
            table.add_column("Description", style="dim")
            
            for service in services:
                status_color = {
                    ServiceStatus.RUNNING: "green",
                    ServiceStatus.STOPPED: "red",
                    ServiceStatus.ERROR: "red", 
                    ServiceStatus.UNKNOWN: "yellow"
                }.get(service.status, "white")
                
                table.add_row(
                    service.name,
                    f"[{status_color}]{service.status.value}[/{status_color}]",
                    str(service.pid) if service.pid else "-",
                    str(service.port) if service.port else "-",
                    service.uptime or "-",
                    service.memory_usage or "-",
                    service.description
                )
            
            self.console.print(table)
        else:
            print("Gadugi Services:")
            print("-" * 80)
            for service in services:
                print(f"{service.name:<20} {service.status.value:<10} {str(service.pid or '-'):<8} {str(service.port or '-'):<8} {service.description}")
    
    def _print_agents_list(self, agents: List[AgentInfo]):
        """Print list of agents."""
        if self.output_format == "json":
            self.console.print(json.dumps([asdict(a) for a in agents], indent=2, default=str))
        elif self.output_format == "rich" and RICH_AVAILABLE:
            table = Table(title="Gadugi Agents")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Category", style="magenta")
            table.add_column("Last Used")
            table.add_column("Description", style="dim")
            
            for agent in agents:
                last_used = agent.last_used.strftime("%Y-%m-%d %H:%M") if agent.last_used else "Never"
                table.add_row(
                    agent.name,
                    agent.category,
                    last_used,
                    agent.description[:60] + "..." if len(agent.description) > 60 else agent.description
                )
            
            self.console.print(table)
        else:
            print("Gadugi Agents:")
            print("-" * 80)
            for agent in agents:
                last_used = agent.last_used.strftime("%Y-%m-%d %H:%M") if agent.last_used else "Never"
                print(f"{agent.name:<25} {agent.category:<15} {last_used:<16} {agent.description}")
    
    def _print_agent_info(self, agent: AgentInfo):
        """Print agent information."""
        if self.output_format == "json":
            self.console.print(json.dumps(asdict(agent), indent=2, default=str))
        elif self.output_format == "rich" and RICH_AVAILABLE:
            panel_content = [
                f"Category: {agent.category}",
                f"Path: {agent.path}",
                f"Description: {agent.description}"
            ]
            
            if agent.dependencies:
                panel_content.append(f"Dependencies: {', '.join(agent.dependencies)}")
            
            if agent.last_used:
                panel_content.append(f"Last Used: {agent.last_used.strftime('%Y-%m-%d %H:%M:%S')}")
            
            panel = Panel(
                "\n".join(panel_content),
                title=f"Agent: {agent.name}",
                border_style="blue"
            )
            self.console.print(panel)
        else:
            print(f"Agent: {agent.name}")
            print(f"  Category: {agent.category}")
            print(f"  Path: {agent.path}")
            print(f"  Description: {agent.description}")
            if agent.dependencies:
                print(f"  Dependencies: {', '.join(agent.dependencies)}")
    
    async def _check_system_health(self):
        """Check system health."""
        if RICH_AVAILABLE:
            self.console.print("[bold]System Health Check[/bold]")
            self.console.print()
        else:
            print("System Health Check")
            print("-" * 20)
        
        # Check services
        services = await self.service_manager.list_services()
        running_services = [s for s in services if s.status == ServiceStatus.RUNNING]
        
        if RICH_AVAILABLE:
            self.console.print(f"Services: {len(running_services)}/{len(services)} running")
        else:
            print(f"Services: {len(running_services)}/{len(services)} running")
        
        # Check agents
        agents = self.agent_manager.list_agents()
        if RICH_AVAILABLE:
            self.console.print(f"Agents: {len(agents)} available")
        else:
            print(f"Agents: {len(agents)} available")
        
        # Check system resources
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            if RICH_AVAILABLE:
                self.console.print(f"CPU Usage: {cpu_percent:.1f}%")
                self.console.print(f"Memory Usage: {memory.percent:.1f}%")
                self.console.print(f"Disk Usage: {disk.percent:.1f}%")
            else:
                print(f"CPU Usage: {cpu_percent:.1f}%")
                print(f"Memory Usage: {memory.percent:.1f}%")
                print(f"Disk Usage: {disk.percent:.1f}%")
        except ImportError:
            if RICH_AVAILABLE:
                self.console.print("[yellow]System resource monitoring unavailable (psutil not installed)[/yellow]")
            else:
                print("System resource monitoring unavailable (psutil not installed)")
    
    async def _show_system_info(self):
        """Show system information."""
        if RICH_AVAILABLE:
            self.console.print("[bold]System Information[/bold]")
            self.console.print()
        else:
            print("System Information")
            print("-" * 18)
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Platform info
        import platform
        system_info = {
            "Python Version": python_version,
            "Platform": platform.system(),
            "Architecture": platform.machine(),
            "Hostname": platform.node()
        }
        
        # Gadugi info
        gadugi_info = {
            "Version": "0.3",
            "CLI Available": "Yes",
            "Rich Support": "Yes" if RICH_AVAILABLE else "No",
            "Click Support": "Yes" if CLICK_AVAILABLE else "No"
        }
        
        if RICH_AVAILABLE:
            # System info panel
            sys_panel = Panel(
                "\n".join([f"{k}: {v}" for k, v in system_info.items()]),
                title="System",
                border_style="blue"
            )
            self.console.print(sys_panel)
            
            # Gadugi info panel
            gadugi_panel = Panel(
                "\n".join([f"{k}: {v}" for k, v in gadugi_info.items()]),
                title="Gadugi",
                border_style="green"
            )
            self.console.print(gadugi_panel)
        else:
            print("System:")
            for k, v in system_info.items():
                print(f"  {k}: {v}")
            print("\nGadugi:")
            for k, v in gadugi_info.items():
                print(f"  {k}: {v}")
    
    async def _setup_development_environment(self):
        """Set up development environment."""
        if RICH_AVAILABLE:
            self.console.print("[bold]Setting up Gadugi development environment...[/bold]")
        else:
            print("Setting up Gadugi development environment...")
        
        # Check for required tools
        required_tools = ["git", "python", "pip"]
        missing_tools = []
        
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            if RICH_AVAILABLE:
                self.console.print(f"[red]Missing required tools: {', '.join(missing_tools)}[/red]")
            else:
                print(f"Missing required tools: {', '.join(missing_tools)}")
            return
        
        # Install development dependencies
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], check=True)
            if RICH_AVAILABLE:
                self.console.print("[green]Development dependencies installed[/green]")
            else:
                print("Development dependencies installed")
        except subprocess.CalledProcessError:
            if RICH_AVAILABLE:
                self.console.print("[yellow]Could not install development dependencies (requirements-dev.txt not found)[/yellow]")
            else:
                print("Could not install development dependencies (requirements-dev.txt not found)")
        
        if RICH_AVAILABLE:
            self.console.print("[green]Development environment setup complete![/green]")
        else:
            print("Development environment setup complete!")
    
    async def _run_tests(self, module: Optional[str] = None):
        """Run tests."""
        if RICH_AVAILABLE:
            self.console.print("[bold]Running tests...[/bold]")
        else:
            print("Running tests...")
        
        cmd = [sys.executable, "-m", "pytest"]
        if module:
            cmd.append(f"tests/test_{module}.py")
        else:
            cmd.append("tests/")
        
        cmd.extend(["-v", "--tb=short"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if RICH_AVAILABLE:
                if result.returncode == 0:
                    self.console.print("[green]All tests passed![/green]")
                else:
                    self.console.print("[red]Some tests failed[/red]")
                
                if result.stdout:
                    self.console.print(result.stdout)
                if result.stderr:
                    self.console.print(f"[red]{result.stderr}[/red]")
            else:
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                
        except FileNotFoundError:
            if RICH_AVAILABLE:
                self.console.print("[red]pytest not found. Install with: pip install pytest[/red]")
            else:
                print("pytest not found. Install with: pip install pytest")
    
    async def _build_project(self):
        """Build the project."""
        if RICH_AVAILABLE:
            self.console.print("[bold]Building project...[/bold]")
        else:
            print("Building project...")
        
        # Run basic checks
        try:
            # Python syntax check
            subprocess.run([sys.executable, "-m", "py_compile"] + 
                         [str(f) for f in Path(".").rglob("*.py")], check=True)
            
            if RICH_AVAILABLE:
                self.console.print("[green]Python syntax check passed[/green]")
            else:
                print("Python syntax check passed")
        except subprocess.CalledProcessError:
            if RICH_AVAILABLE:
                self.console.print("[red]Python syntax check failed[/red]")
            else:
                print("Python syntax check failed")
        
        if RICH_AVAILABLE:
            self.console.print("[green]Build complete![/green]")
        else:
            print("Build complete!")


async def main():
    """Main CLI entry point."""
    cli = GadugiCLI()
    return await cli.run()


def cli_entry():
    """Entry point for the CLI script."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(cli_entry())