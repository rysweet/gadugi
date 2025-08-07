#!/usr/bin/env python3
"""Tests for Gadugi CLI Service."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "cli"))

from gadugi_cli_service import (
    AgentInfo,
    AgentManager,
    CommandResult,
    GadugiCLI,
    ServiceInfo,
    ServiceManager,
    ServiceStatus,
    ServiceType,
)


class TestGadugiCLI(unittest.IsolatedAsyncioTestCase):
    """Test cases for Gadugi CLI Service."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.cli = GadugiCLI()
        self.temp_dir = tempfile.mkdtemp()

    async def asyncTearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cli_initialization(self) -> None:
        """Test CLI initializes properly."""
        assert self.cli is not None
        assert self.cli.console is not None
        assert self.cli.service_manager is not None
        assert self.cli.agent_manager is not None
        assert self.cli.logger is not None
        assert not self.cli.verbose

    def test_argument_parser_creation(self) -> None:
        """Test argument parser creation."""
        parser = self.cli.create_parser()

        assert parser is not None

        # Test basic arguments
        args = parser.parse_args(["--verbose", "service", "list"])
        assert args.verbose
        assert args.command == "service"
        assert args.service_action == "list"

    def test_service_command_parsing(self) -> None:
        """Test service command parsing."""
        parser = self.cli.create_parser()

        # Test service start
        args = parser.parse_args(["service", "start", "event-router"])
        assert args.command == "service"
        assert args.service_action == "start"
        assert args.service_name == "event-router"

        # Test service list
        args = parser.parse_args(["service", "list"])
        assert args.service_action == "list"

    def test_agent_command_parsing(self) -> None:
        """Test agent command parsing."""
        parser = self.cli.create_parser()

        # Test agent list
        args = parser.parse_args(["agent", "list", "--category", "workflow"])
        assert args.command == "agent"
        assert args.agent_action == "list"
        assert args.category == "workflow"

        # Test agent invoke
        args = parser.parse_args(["agent", "invoke", "orchestrator", "test prompt"])
        assert args.agent_action == "invoke"
        assert args.agent_name == "orchestrator"
        assert args.prompt == "test prompt"

    def test_workflow_command_parsing(self) -> None:
        """Test workflow command parsing."""
        parser = self.cli.create_parser()

        # Test workflow run
        args = parser.parse_args(["workflow", "run", "test.md", "--parallel"])
        assert args.command == "workflow"
        assert args.workflow_action == "run"
        assert args.prompt_file == "test.md"
        assert args.parallel

    def test_system_command_parsing(self) -> None:
        """Test system command parsing."""
        parser = self.cli.create_parser()

        # Test system health
        args = parser.parse_args(["system", "health"])
        assert args.command == "system"
        assert args.system_action == "health"

        # Test system info
        args = parser.parse_args(["system", "info"])
        assert args.system_action == "info"

    @patch("gadugi_cli_service.GadugiCLI._print_command_result")
    async def test_handle_service_start_command(self, mock_print) -> None:
        """Test service start command handling."""
        # Mock service manager
        mock_result = CommandResult(success=True, message="Service started")
        self.cli.service_manager.start_service = AsyncMock(return_value=mock_result)

        # Create mock arguments
        args = Mock()
        args.service_action = "start"
        args.service_name = "event-router"

        result = await self.cli._handle_service_command(args)

        assert result == 0
        self.cli.service_manager.start_service.assert_called_once_with("event-router")
        mock_print.assert_called_once_with(mock_result)

    @patch("gadugi_cli_service.GadugiCLI._print_services_list")
    async def test_handle_service_list_command(self, mock_print) -> None:
        """Test service list command handling."""
        # Mock service manager
        mock_services = [
            ServiceInfo(
                "event-router",
                ServiceType.EVENT_ROUTER,
                ServiceStatus.RUNNING,
            ),
            ServiceInfo("mcp", ServiceType.MCP, ServiceStatus.STOPPED),
        ]
        self.cli.service_manager.list_services = AsyncMock(return_value=mock_services)

        # Create mock arguments
        args = Mock()
        args.service_action = "list"

        result = await self.cli._handle_service_command(args)

        assert result == 0
        self.cli.service_manager.list_services.assert_called_once()
        mock_print.assert_called_once_with(mock_services)

    @patch("gadugi_cli_service.GadugiCLI._print_agents_list")
    async def test_handle_agent_list_command(self, mock_print) -> None:
        """Test agent list command handling."""
        # Mock agent manager
        mock_agents = [
            AgentInfo(
                "orchestrator",
                "/path/to/orchestrator.md",
                "Orchestration agent",
                "orchestration",
            ),
            AgentInfo(
                "workflow-manager",
                "/path/to/workflow.md",
                "Workflow management",
                "workflow",
            ),
        ]
        self.cli.agent_manager.list_agents = Mock(return_value=mock_agents)

        # Create mock arguments
        args = Mock()
        args.agent_action = "list"
        args.category = None

        result = await self.cli._handle_agent_command(args)

        assert result == 0
        self.cli.agent_manager.list_agents.assert_called_once_with(None)
        mock_print.assert_called_once_with(mock_agents)

    @patch("gadugi_cli_service.GadugiCLI._print_command_result")
    async def test_handle_agent_invoke_command(self, mock_print) -> None:
        """Test agent invoke command handling."""
        # Mock agent manager
        mock_result = CommandResult(success=True, message="Agent executed successfully")
        self.cli.agent_manager.invoke_agent = AsyncMock(return_value=mock_result)

        # Create mock arguments
        args = Mock()
        args.agent_action = "invoke"
        args.agent_name = "orchestrator"
        args.prompt = "test prompt"

        result = await self.cli._handle_agent_command(args)

        assert result == 0
        self.cli.agent_manager.invoke_agent.assert_called_once_with(
            "orchestrator",
            "test prompt",
        )
        mock_print.assert_called_once_with(mock_result)

    def test_command_result_dataclass(self) -> None:
        """Test CommandResult dataclass functionality."""
        result = CommandResult(
            success=True,
            message="Test successful",
            data={"key": "value"},
            execution_time=1.5,
            warnings=["Warning 1"],
            errors=[],
        )

        assert result.success
        assert result.message == "Test successful"
        assert result.data["key"] == "value"
        assert result.execution_time == 1.5
        assert len(result.warnings) == 1
        assert len(result.errors) == 0

    def test_service_info_dataclass(self) -> None:
        """Test ServiceInfo dataclass functionality."""
        service = ServiceInfo(
            name="test-service",
            type=ServiceType.EVENT_ROUTER,
            status=ServiceStatus.RUNNING,
            pid=1234,
            port=9090,
            uptime="2h 30m",
            memory_usage="50MB",
            cpu_usage=2.5,
            description="Test service",
        )

        assert service.name == "test-service"
        assert service.type == ServiceType.EVENT_ROUTER
        assert service.status == ServiceStatus.RUNNING
        assert service.pid == 1234
        assert service.port == 9090
        assert service.description == "Test service"

    def test_agent_info_dataclass(self) -> None:
        """Test AgentInfo dataclass functionality."""
        from datetime import datetime

        agent = AgentInfo(
            name="test-agent",
            path="/path/to/agent.md",
            description="Test agent description",
            category="testing",
            dependencies=["dep1", "dep2"],
            last_used=datetime.now(),
        )

        assert agent.name == "test-agent"
        assert agent.category == "testing"
        assert len(agent.dependencies) == 2
        assert agent.last_used is not None


class TestServiceManager(unittest.IsolatedAsyncioTestCase):
    """Test cases for ServiceManager."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.manager = ServiceManager()

    def test_service_manager_initialization(self) -> None:
        """Test ServiceManager initializes properly."""
        assert self.manager is not None
        assert self.manager.logger is not None
        assert self.manager.services is not None
        assert self.manager.service_configs is not None

        # Check default service configurations
        assert "event-router" in self.manager.service_configs
        assert "neo4j-graph" in self.manager.service_configs
        assert "mcp" in self.manager.service_configs
        assert "llm-proxy" in self.manager.service_configs

    async def test_get_service_status_unknown(self) -> None:
        """Test getting status of unknown service."""
        status = await self.manager.get_service_status("unknown-service")

        assert status.name == "unknown-service"
        assert status.status == ServiceStatus.UNKNOWN
        assert status.description == "Unknown service"

    async def test_get_service_status_known(self) -> None:
        """Test getting status of known but stopped service."""
        status = await self.manager.get_service_status("event-router")

        assert status.name == "event-router"
        assert status.status == ServiceStatus.STOPPED
        assert "Event routing" in status.description

    async def test_list_services(self) -> None:
        """Test listing all services."""
        services = await self.manager.list_services()

        assert len(services) > 0
        service_names = [s.name for s in services]
        assert "event-router" in service_names
        assert "neo4j-graph" in service_names
        assert "mcp" in service_names
        assert "llm-proxy" in service_names

    @patch("subprocess.Popen")
    @patch("asyncio.sleep")
    async def test_start_service_success(self, mock_sleep, mock_popen) -> None:
        """Test successful service start."""
        # Mock successful process
        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        result = await self.manager.start_service("event-router")

        assert result.success
        assert "started successfully" in result.message
        assert result.data["pid"] == 1234

    @patch("subprocess.Popen")
    @patch("asyncio.sleep")
    async def test_start_service_failure(self, mock_sleep, mock_popen) -> None:
        """Test service start failure."""
        # Mock failed process
        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = (b"", b"Service failed to start")
        mock_popen.return_value = mock_process

        result = await self.manager.start_service("event-router")

        assert not result.success
        assert "Failed to start" in result.message
        assert "Service failed to start" in result.errors[0]

    async def test_start_unknown_service(self) -> None:
        """Test starting unknown service."""
        result = await self.manager.start_service("unknown-service")

        assert not result.success
        assert "Unknown service" in result.message

    @patch("psutil.Process")
    async def test_stop_service_success(self, mock_process_class) -> None:
        """Test successful service stop."""
        # Set up mock process
        mock_process = Mock()
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = None
        mock_process_class.return_value = mock_process

        # Add service to registry
        self.manager.services["test-service"] = ServiceInfo(
            name="test-service",
            type=ServiceType.EVENT_ROUTER,
            status=ServiceStatus.RUNNING,
            pid=1234,
        )

        result = await self.manager.stop_service("test-service")

        assert result.success
        assert "stopped successfully" in result.message
        assert "test-service" not in self.manager.services

    async def test_stop_service_not_running(self) -> None:
        """Test stopping service that's not running."""
        result = await self.manager.stop_service("event-router")

        assert result.success
        assert "not running" in result.message


class TestAgentManager(unittest.TestCase):
    """Test cases for AgentManager."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = AgentManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_agent_manager_initialization(self) -> None:
        """Test AgentManager initializes properly."""
        assert self.manager is not None
        assert self.manager.logger is not None
        assert isinstance(self.manager.agents, dict)

    def test_parse_agent_file_success(self) -> None:
        """Test parsing a valid agent file."""
        # Create a test agent file
        agent_content = """# Test Agent

This is a test agent for testing purposes.

## Capabilities
- Testing functionality
- Validation

## Usage
Use this agent for testing.
"""
        agent_file = Path(self.temp_dir) / "test-agent.md"
        agent_file.write_text(agent_content)

        agent_info = self.manager._parse_agent_file(agent_file)

        assert agent_info is not None
        assert agent_info.name == "test-agent"
        assert "test agent" in agent_info.description.lower()
        assert agent_info.category == "general"
        assert agent_info.path == str(agent_file)

    def test_parse_agent_file_with_category(self) -> None:
        """Test parsing agent file with category detection."""
        # Create workflow agent file
        agent_content = "# Workflow Agent\n\nManages workflows."
        agent_file = Path(self.temp_dir) / "workflow" / "workflow-agent.md"
        agent_file.parent.mkdir(exist_ok=True)
        agent_file.write_text(agent_content)

        agent_info = self.manager._parse_agent_file(agent_file)

        assert agent_info is not None
        assert agent_info.category == "workflow"

    def test_scan_agent_directory(self) -> None:
        """Test scanning directory for agent files."""
        # Create test agent files
        test_agents = [
            ("agent1.md", "# Agent 1\nFirst test agent"),
            ("agent2.md", "# Agent 2\nSecond test agent"),
            ("not-agent.txt", "This is not an agent file"),
        ]

        agent_dir = Path(self.temp_dir) / "agents"
        agent_dir.mkdir()

        for filename, content in test_agents:
            (agent_dir / filename).write_text(content)

        # Clear existing agents and scan
        original_agents = self.manager.agents.copy()
        self.manager.agents.clear()
        self.manager._scan_agent_directory(agent_dir)

        # Should only find .md files
        assert len(self.manager.agents) == 2
        assert "agent1" in self.manager.agents
        assert "agent2" in self.manager.agents
        assert "not-agent" not in self.manager.agents

        # Restore original agents
        self.manager.agents.update(original_agents)

    def test_list_agents_no_filter(self) -> None:
        """Test listing all agents."""
        agents = self.manager.list_agents()
        assert isinstance(agents, list)

        # Should be sorted by name
        if len(agents) > 1:
            for i in range(len(agents) - 1):
                assert agents[i].name <= agents[i + 1].name

    def test_list_agents_with_category_filter(self) -> None:
        """Test listing agents with category filter."""
        # Add test agents with different categories
        self.manager.agents["test1"] = AgentInfo(
            name="test1",
            path="/test1.md",
            description="Test agent 1",
            category="workflow",
        )
        self.manager.agents["test2"] = AgentInfo(
            name="test2",
            path="/test2.md",
            description="Test agent 2",
            category="memory",
        )

        workflow_agents = self.manager.list_agents(category="workflow")
        memory_agents = self.manager.list_agents(category="memory")

        # Check filtering works
        workflow_names = [a.name for a in workflow_agents]
        memory_names = [a.name for a in memory_agents]

        assert "test1" in workflow_names
        assert "test1" not in memory_names
        assert "test2" in memory_names
        assert "test2" not in workflow_names

    def test_get_agent_categories(self) -> None:
        """Test getting agent categories."""
        # Add test agents with different categories
        self.manager.agents["test1"] = AgentInfo(
            name="test1",
            path="/test1.md",
            description="Test agent 1",
            category="workflow",
        )
        self.manager.agents["test2"] = AgentInfo(
            name="test2",
            path="/test2.md",
            description="Test agent 2",
            category="memory",
        )
        self.manager.agents["test3"] = AgentInfo(
            name="test3",
            path="/test3.md",
            description="Test agent 3",
            category="workflow",  # Duplicate category
        )

        categories = self.manager.get_agent_categories()

        assert "workflow" in categories
        assert "memory" in categories
        # Should be deduplicated and sorted
        assert len(set(categories)) == len(categories)
        assert categories == sorted(categories)


class TestCLIFormatting(unittest.TestCase):
    """Test cases for CLI output formatting."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.cli = GadugiCLI()
        self.cli.output_format = "plain"  # Use plain format for testing

    def test_print_command_result_success(self) -> None:
        """Test printing successful command result."""
        result = CommandResult(
            success=True,
            message="Operation completed successfully",
            execution_time=1.5,
        )

        # Should not raise any exceptions
        try:
            self.cli._print_command_result(result)
        except Exception as e:
            self.fail(f"_print_command_result raised an exception: {e}")

    def test_print_command_result_failure(self) -> None:
        """Test printing failed command result."""
        result = CommandResult(
            success=False,
            message="Operation failed",
            execution_time=0.5,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )

        # Should not raise any exceptions
        try:
            self.cli._print_command_result(result)
        except Exception as e:
            self.fail(f"_print_command_result raised an exception: {e}")

    def test_print_service_info(self) -> None:
        """Test printing service information."""
        service = ServiceInfo(
            name="test-service",
            type=ServiceType.EVENT_ROUTER,
            status=ServiceStatus.RUNNING,
            pid=1234,
            port=9090,
            uptime="2h 30m",
            memory_usage="50MB",
            cpu_usage=2.5,
            description="Test service description",
        )

        # Should not raise any exceptions
        try:
            self.cli._print_service_info(service)
        except Exception as e:
            self.fail(f"_print_service_info raised an exception: {e}")

    def test_print_services_list(self) -> None:
        """Test printing services list."""
        services = [
            ServiceInfo("service1", ServiceType.EVENT_ROUTER, ServiceStatus.RUNNING),
            ServiceInfo("service2", ServiceType.MCP, ServiceStatus.STOPPED),
            ServiceInfo("service3", ServiceType.LLM_PROXY, ServiceStatus.ERROR),
        ]

        # Should not raise any exceptions
        try:
            self.cli._print_services_list(services)
        except Exception as e:
            self.fail(f"_print_services_list raised an exception: {e}")

    def test_print_agents_list(self) -> None:
        """Test printing agents list."""
        from datetime import datetime

        agents = [
            AgentInfo("agent1", "/path1.md", "First agent", "workflow"),
            AgentInfo(
                "agent2",
                "/path2.md",
                "Second agent",
                "memory",
                last_used=datetime.now(),
            ),
            AgentInfo("agent3", "/path3.md", "Third agent", "development"),
        ]

        # Should not raise any exceptions
        try:
            self.cli._print_agents_list(agents)
        except Exception as e:
            self.fail(f"_print_agents_list raised an exception: {e}")


class TestCLIIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration test cases for CLI."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.cli = GadugiCLI()

    @patch("sys.argv", ["gadugi", "service", "list"])
    async def test_run_with_service_list_command(self) -> None:
        """Test running CLI with service list command."""
        # Mock service manager
        mock_services = [
            ServiceInfo(
                "event-router",
                ServiceType.EVENT_ROUTER,
                ServiceStatus.STOPPED,
            ),
            ServiceInfo("mcp", ServiceType.MCP, ServiceStatus.STOPPED),
        ]
        self.cli.service_manager.list_services = AsyncMock(return_value=mock_services)

        result = await self.cli.run(["service", "list"])

        assert result == 0
        self.cli.service_manager.list_services.assert_called_once()

    @patch("sys.argv", ["gadugi", "agent", "list"])
    async def test_run_with_agent_list_command(self) -> None:
        """Test running CLI with agent list command."""
        result = await self.cli.run(["agent", "list"])

        assert result == 0

    async def test_run_with_no_arguments(self) -> None:
        """Test running CLI with no arguments shows help."""
        with patch("argparse.ArgumentParser.print_help") as mock_help:
            result = await self.cli.run([])

            assert result == 0
            mock_help.assert_called_once()

    async def test_run_with_invalid_command(self) -> None:
        """Test running CLI with invalid command."""
        with patch("argparse.ArgumentParser.print_help") as mock_help:
            result = await self.cli.run(["invalid-command"])

            assert result == 0
            mock_help.assert_called_once()


if __name__ == "__main__":
    unittest.main()
