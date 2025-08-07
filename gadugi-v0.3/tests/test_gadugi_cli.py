#!/usr/bin/env python3
"""
Tests for Gadugi CLI Service
"""

import asyncio
import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "cli"))

from gadugi_cli_service import (
    GadugiCLI,
    ServiceManager,
    AgentManager,
    ServiceType,
    ServiceStatus,
    CommandResult,
    ServiceInfo,
    AgentInfo,
)


class TestGadugiCLI(unittest.IsolatedAsyncioTestCase):
    """Test cases for Gadugi CLI Service."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.cli = GadugiCLI()
        self.temp_dir = tempfile.mkdtemp()

    async def asyncTearDown(self):
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cli_initialization(self):
        """Test CLI initializes properly."""
        self.assertIsNotNone(self.cli)
        self.assertIsNotNone(self.cli.console)
        self.assertIsNotNone(self.cli.service_manager)
        self.assertIsNotNone(self.cli.agent_manager)
        self.assertIsNotNone(self.cli.logger)
        self.assertFalse(self.cli.verbose)

    def test_argument_parser_creation(self):
        """Test argument parser creation."""
        parser = self.cli.create_parser()

        self.assertIsNotNone(parser)

        # Test basic arguments
        args = parser.parse_args(["--verbose", "service", "list"])
        self.assertTrue(args.verbose)
        self.assertEqual(args.command, "service")
        self.assertEqual(args.service_action, "list")

    def test_service_command_parsing(self):
        """Test service command parsing."""
        parser = self.cli.create_parser()

        # Test service start
        args = parser.parse_args(["service", "start", "event-router"])
        self.assertEqual(args.command, "service")
        self.assertEqual(args.service_action, "start")
        self.assertEqual(args.service_name, "event-router")

        # Test service list
        args = parser.parse_args(["service", "list"])
        self.assertEqual(args.service_action, "list")

    def test_agent_command_parsing(self):
        """Test agent command parsing."""
        parser = self.cli.create_parser()

        # Test agent list
        args = parser.parse_args(["agent", "list", "--category", "workflow"])
        self.assertEqual(args.command, "agent")
        self.assertEqual(args.agent_action, "list")
        self.assertEqual(args.category, "workflow")

        # Test agent invoke
        args = parser.parse_args(["agent", "invoke", "orchestrator", "test prompt"])
        self.assertEqual(args.agent_action, "invoke")
        self.assertEqual(args.agent_name, "orchestrator")
        self.assertEqual(args.prompt, "test prompt")

    def test_workflow_command_parsing(self):
        """Test workflow command parsing."""
        parser = self.cli.create_parser()

        # Test workflow run
        args = parser.parse_args(["workflow", "run", "test.md", "--parallel"])
        self.assertEqual(args.command, "workflow")
        self.assertEqual(args.workflow_action, "run")
        self.assertEqual(args.prompt_file, "test.md")
        self.assertTrue(args.parallel)

    def test_system_command_parsing(self):
        """Test system command parsing."""
        parser = self.cli.create_parser()

        # Test system health
        args = parser.parse_args(["system", "health"])
        self.assertEqual(args.command, "system")
        self.assertEqual(args.system_action, "health")

        # Test system info
        args = parser.parse_args(["system", "info"])
        self.assertEqual(args.system_action, "info")

    @patch("gadugi_cli_service.GadugiCLI._print_command_result")
    async def test_handle_service_start_command(self, mock_print):
        """Test service start command handling."""
        # Mock service manager
        mock_result = CommandResult(success=True, message="Service started")
        self.cli.service_manager.start_service = AsyncMock(return_value=mock_result)

        # Create mock arguments
        args = Mock()
        args.service_action = "start"
        args.service_name = "event-router"

        result = await self.cli._handle_service_command(args)

        self.assertEqual(result, 0)
        self.cli.service_manager.start_service.assert_called_once_with("event-router")
        mock_print.assert_called_once_with(mock_result)

    @patch("gadugi_cli_service.GadugiCLI._print_services_list")
    async def test_handle_service_list_command(self, mock_print):
        """Test service list command handling."""
        # Mock service manager
        mock_services = [
            ServiceInfo(
                "event-router", ServiceType.EVENT_ROUTER, ServiceStatus.RUNNING
            ),
            ServiceInfo("mcp", ServiceType.MCP, ServiceStatus.STOPPED),
        ]
        self.cli.service_manager.list_services = AsyncMock(return_value=mock_services)

        # Create mock arguments
        args = Mock()
        args.service_action = "list"

        result = await self.cli._handle_service_command(args)

        self.assertEqual(result, 0)
        self.cli.service_manager.list_services.assert_called_once()
        mock_print.assert_called_once_with(mock_services)

    @patch("gadugi_cli_service.GadugiCLI._print_agents_list")
    async def test_handle_agent_list_command(self, mock_print):
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

        self.assertEqual(result, 0)
        self.cli.agent_manager.list_agents.assert_called_once_with(None)
        mock_print.assert_called_once_with(mock_agents)

    @patch("gadugi_cli_service.GadugiCLI._print_command_result")
    async def test_handle_agent_invoke_command(self, mock_print):
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

        self.assertEqual(result, 0)
        self.cli.agent_manager.invoke_agent.assert_called_once_with(
            "orchestrator", "test prompt"
        )
        mock_print.assert_called_once_with(mock_result)

    def test_command_result_dataclass(self):
        """Test CommandResult dataclass functionality."""
        result = CommandResult(
            success=True,
            message="Test successful",
            data={"key": "value"},
            execution_time=1.5,
            warnings=["Warning 1"],
            errors=[],
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Test successful")
        self.assertEqual(result.data["key"], "value")
        self.assertEqual(result.execution_time, 1.5)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.errors), 0)

    def test_service_info_dataclass(self):
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

        self.assertEqual(service.name, "test-service")
        self.assertEqual(service.type, ServiceType.EVENT_ROUTER)
        self.assertEqual(service.status, ServiceStatus.RUNNING)
        self.assertEqual(service.pid, 1234)
        self.assertEqual(service.port, 9090)
        self.assertEqual(service.description, "Test service")

    def test_agent_info_dataclass(self):
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

        self.assertEqual(agent.name, "test-agent")
        self.assertEqual(agent.category, "testing")
        self.assertEqual(len(agent.dependencies), 2)
        self.assertIsNotNone(agent.last_used)


class TestServiceManager(unittest.IsolatedAsyncioTestCase):
    """Test cases for ServiceManager."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.manager = ServiceManager()

    def test_service_manager_initialization(self):
        """Test ServiceManager initializes properly."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.logger)
        self.assertIsNotNone(self.manager.services)
        self.assertIsNotNone(self.manager.service_configs)

        # Check default service configurations
        self.assertIn("event-router", self.manager.service_configs)
        self.assertIn("neo4j-graph", self.manager.service_configs)
        self.assertIn("mcp", self.manager.service_configs)
        self.assertIn("llm-proxy", self.manager.service_configs)

    async def test_get_service_status_unknown(self):
        """Test getting status of unknown service."""
        status = await self.manager.get_service_status("unknown-service")

        self.assertEqual(status.name, "unknown-service")
        self.assertEqual(status.status, ServiceStatus.UNKNOWN)
        self.assertEqual(status.description, "Unknown service")

    async def test_get_service_status_known(self):
        """Test getting status of known but stopped service."""
        status = await self.manager.get_service_status("event-router")

        self.assertEqual(status.name, "event-router")
        self.assertEqual(status.status, ServiceStatus.STOPPED)
        self.assertIn("Event routing", status.description)

    async def test_list_services(self):
        """Test listing all services."""
        services = await self.manager.list_services()

        self.assertGreater(len(services), 0)
        service_names = [s.name for s in services]
        self.assertIn("event-router", service_names)
        self.assertIn("neo4j-graph", service_names)
        self.assertIn("mcp", service_names)
        self.assertIn("llm-proxy", service_names)

    @patch("subprocess.Popen")
    @patch("asyncio.sleep")
    async def test_start_service_success(self, mock_sleep, mock_popen):
        """Test successful service start."""
        # Mock successful process
        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        result = await self.manager.start_service("event-router")

        self.assertTrue(result.success)
        self.assertIn("started successfully", result.message)
        self.assertEqual(result.data["pid"], 1234)

    @patch("subprocess.Popen")
    @patch("asyncio.sleep")
    async def test_start_service_failure(self, mock_sleep, mock_popen):
        """Test service start failure."""
        # Mock failed process
        mock_process = Mock()
        mock_process.pid = 1234
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = (b"", b"Service failed to start")
        mock_popen.return_value = mock_process

        result = await self.manager.start_service("event-router")

        self.assertFalse(result.success)
        self.assertIn("Failed to start", result.message)
        self.assertIn("Service failed to start", result.errors[0])

    async def test_start_unknown_service(self):
        """Test starting unknown service."""
        result = await self.manager.start_service("unknown-service")

        self.assertFalse(result.success)
        self.assertIn("Unknown service", result.message)

    @patch("psutil.Process")
    async def test_stop_service_success(self, mock_process_class):
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

        self.assertTrue(result.success)
        self.assertIn("stopped successfully", result.message)
        self.assertNotIn("test-service", self.manager.services)

    async def test_stop_service_not_running(self):
        """Test stopping service that's not running."""
        result = await self.manager.stop_service("event-router")

        self.assertTrue(result.success)
        self.assertIn("not running", result.message)


class TestAgentManager(unittest.TestCase):
    """Test cases for AgentManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AgentManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_agent_manager_initialization(self):
        """Test AgentManager initializes properly."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.logger)
        self.assertIsInstance(self.manager.agents, dict)

    def test_parse_agent_file_success(self):
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

        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info.name, "test-agent")
        self.assertIn("test agent", agent_info.description.lower())
        self.assertEqual(agent_info.category, "general")
        self.assertEqual(agent_info.path, str(agent_file))

    def test_parse_agent_file_with_category(self):
        """Test parsing agent file with category detection."""
        # Create workflow agent file
        agent_content = "# Workflow Agent\n\nManages workflows."
        agent_file = Path(self.temp_dir) / "workflow" / "workflow-agent.md"
        agent_file.parent.mkdir(exist_ok=True)
        agent_file.write_text(agent_content)

        agent_info = self.manager._parse_agent_file(agent_file)

        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info.category, "workflow")

    def test_scan_agent_directory(self):
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
        self.assertEqual(len(self.manager.agents), 2)
        self.assertIn("agent1", self.manager.agents)
        self.assertIn("agent2", self.manager.agents)
        self.assertNotIn("not-agent", self.manager.agents)

        # Restore original agents
        self.manager.agents.update(original_agents)

    def test_list_agents_no_filter(self):
        """Test listing all agents."""
        agents = self.manager.list_agents()
        self.assertIsInstance(agents, list)

        # Should be sorted by name
        if len(agents) > 1:
            for i in range(len(agents) - 1):
                self.assertLessEqual(agents[i].name, agents[i + 1].name)

    def test_list_agents_with_category_filter(self):
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

        self.assertIn("test1", workflow_names)
        self.assertNotIn("test1", memory_names)
        self.assertIn("test2", memory_names)
        self.assertNotIn("test2", workflow_names)

    def test_get_agent_categories(self):
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

        self.assertIn("workflow", categories)
        self.assertIn("memory", categories)
        # Should be deduplicated and sorted
        self.assertEqual(len(set(categories)), len(categories))
        self.assertEqual(categories, sorted(categories))


class TestCLIFormatting(unittest.TestCase):
    """Test cases for CLI output formatting."""

    def setUp(self):
        """Set up test fixtures."""
        self.cli = GadugiCLI()
        self.cli.output_format = "plain"  # Use plain format for testing

    def test_print_command_result_success(self):
        """Test printing successful command result."""
        result = CommandResult(
            success=True, message="Operation completed successfully", execution_time=1.5
        )

        # Should not raise any exceptions
        try:
            self.cli._print_command_result(result)
        except Exception as e:
            self.fail(f"_print_command_result raised an exception: {e}")

    def test_print_command_result_failure(self):
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

    def test_print_service_info(self):
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

    def test_print_services_list(self):
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

    def test_print_agents_list(self):
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

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.cli = GadugiCLI()

    @patch("sys.argv", ["gadugi", "service", "list"])
    async def test_run_with_service_list_command(self):
        """Test running CLI with service list command."""
        # Mock service manager
        mock_services = [
            ServiceInfo(
                "event-router", ServiceType.EVENT_ROUTER, ServiceStatus.STOPPED
            ),
            ServiceInfo("mcp", ServiceType.MCP, ServiceStatus.STOPPED),
        ]
        self.cli.service_manager.list_services = AsyncMock(return_value=mock_services)

        result = await self.cli.run(["service", "list"])

        self.assertEqual(result, 0)
        self.cli.service_manager.list_services.assert_called_once()

    @patch("sys.argv", ["gadugi", "agent", "list"])
    async def test_run_with_agent_list_command(self):
        """Test running CLI with agent list command."""
        result = await self.cli.run(["agent", "list"])

        self.assertEqual(result, 0)

    async def test_run_with_no_arguments(self):
        """Test running CLI with no arguments shows help."""
        with patch("argparse.ArgumentParser.print_help") as mock_help:
            result = await self.cli.run([])

            self.assertEqual(result, 0)
            mock_help.assert_called_once()

    async def test_run_with_invalid_command(self):
        """Test running CLI with invalid command."""
        with patch("argparse.ArgumentParser.print_help") as mock_help:
            result = await self.cli.run(["invalid-command"])

            self.assertEqual(result, 0)
            mock_help.assert_called_once()


if __name__ == "__main__":
    unittest.main()
