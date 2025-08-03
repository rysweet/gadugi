#!/usr/bin/env python3
"""
Tests for TeamCoach hooks functionality.
"""

import unittest
import json
import subprocess
import os
from unittest.mock import patch, MagicMock
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTeamCoachStopHook(unittest.TestCase):
    """Test TeamCoach stop hook functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.hook_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".claude",
            "hooks",
            "teamcoach-stop.py",
        )
        self.assertTrue(os.path.exists(self.hook_script), "Hook script should exist")
        self.assertTrue(
            os.access(self.hook_script, os.X_OK), "Hook script should be executable"
        )

    @patch("subprocess.run")
    def test_hook_invokes_teamcoach_successfully(self, mock_run):
        """Test that the hook successfully invokes TeamCoach."""
        # Mock successful subprocess call
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Run the hook script
        result = subprocess.run(
            ["python", self.hook_script], input="{}", text=True, capture_output=True
        )

        # Check that the hook ran successfully
        self.assertEqual(result.returncode, 0)

        # Check that the output is valid JSON
        try:
            output = json.loads(result.stdout)
            self.assertEqual(output["action"], "continue")
            self.assertIn("message", output)
            self.assertIn("timestamp", output)
        except json.JSONDecodeError:
            self.fail("Hook output should be valid JSON")

    @patch("subprocess.run")
    def test_hook_handles_teamcoach_failure_gracefully(self, mock_run):
        """Test that the hook handles TeamCoach failures gracefully."""
        # Mock failed subprocess call
        mock_run.return_value = MagicMock(returncode=1, stderr="TeamCoach error")

        # Run the hook script
        result = subprocess.run(
            ["python", self.hook_script], input="{}", text=True, capture_output=True
        )

        # Hook should still succeed (not block the workflow)
        self.assertEqual(result.returncode, 0)

        # Check that the output indicates issues but continues
        try:
            output = json.loads(result.stdout)
            self.assertEqual(output["action"], "continue")
            self.assertIn("issues", output["message"])
        except json.JSONDecodeError:
            self.fail("Hook output should be valid JSON even on TeamCoach failure")

    @patch("subprocess.run")
    def test_hook_handles_timeout_gracefully(self, mock_run):
        """Test that the hook handles timeouts gracefully."""
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 300)

        # Run the hook script
        result = subprocess.run(
            ["python", self.hook_script], input="{}", text=True, capture_output=True
        )

        # Hook should still succeed (not block the workflow)
        self.assertEqual(result.returncode, 0)

        # Check that the output indicates timeout but continues
        try:
            output = json.loads(result.stdout)
            self.assertEqual(output["action"], "continue")
            self.assertIn("timed out", output["message"])
        except json.JSONDecodeError:
            self.fail("Hook output should be valid JSON even on timeout")

    def test_hook_script_has_correct_structure(self):
        """Test that the hook script has the correct structure."""
        with open(self.hook_script, "r") as f:
            content = f.read()

        # Check for required components
        self.assertIn("def invoke_teamcoach()", content)
        self.assertIn("def main()", content)
        self.assertIn('if __name__ == "__main__":', content)
        self.assertIn("claude", content)  # Should invoke Claude CLI
        self.assertIn("/agent:teamcoach", content)  # Should use TeamCoach agent
        self.assertIn("timeout=300", content)  # Should have 5-minute timeout

    def test_hook_script_generates_valid_prompt(self):
        """Test that the hook script generates a valid TeamCoach prompt."""
        with open(self.hook_script, "r") as f:
            content = f.read()

        # Check for required prompt elements
        self.assertIn("Task: Analyze completed session", content)
        self.assertIn("Context:", content)
        self.assertIn("Analysis Focus:", content)
        self.assertIn("Deliverables:", content)
        self.assertIn("performance metrics", content)
        self.assertIn("coaching recommendations", content)


class TestTeamCoachSubagentStopHook(unittest.TestCase):
    """Test TeamCoach subagent stop hook functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.hook_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".claude",
            "hooks",
            "teamcoach-subagent-stop.py",
        )
        self.assertTrue(
            os.path.exists(self.hook_script), "Subagent hook script should exist"
        )
        self.assertTrue(
            os.access(self.hook_script, os.X_OK),
            "Subagent hook script should be executable",
        )

    @patch("subprocess.run")
    def test_hook_processes_agent_data(self, mock_run):
        """Test that the hook processes agent data correctly."""
        # Mock successful subprocess call
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Create test input with agent data
        agent_data = {"agent_name": "test-agent", "result": "success", "duration": 120}

        # Run the hook script
        result = subprocess.run(
            ["python", self.hook_script],
            input=json.dumps(agent_data),
            text=True,
            capture_output=True,
        )

        # Check that the hook ran successfully
        self.assertEqual(result.returncode, 0)

        # Check that TeamCoach was called with agent-specific prompt
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("claude", args)
        self.assertIn("/agent:teamcoach", args)

        # Check prompt contains agent information
        prompt = args[2]  # Third argument should be the prompt
        self.assertIn("test-agent", prompt)
        self.assertIn("success", prompt)
        self.assertIn("120", prompt)

    @patch("subprocess.run")
    def test_hook_handles_malformed_input(self, mock_run):
        """Test that the hook handles malformed input gracefully."""
        # Mock successful subprocess call
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Run the hook script with malformed JSON
        result = subprocess.run(
            ["python", self.hook_script],
            input="invalid json",
            text=True,
            capture_output=True,
        )

        # Hook should still succeed (not block the workflow)
        self.assertEqual(result.returncode, 0)

        # Should have called TeamCoach with default/empty agent data
        mock_run.assert_called_once()

    def test_subagent_hook_has_shorter_timeout(self):
        """Test that the subagent hook has appropriate timeout."""
        with open(self.hook_script, "r") as f:
            content = f.read()

        # Should have 3-minute timeout (shorter than main hook)
        self.assertIn("timeout=180", content)


class TestTeamCoachHookConfiguration(unittest.TestCase):
    """Test TeamCoach hook configuration in settings.json."""

    def setUp(self):
        """Set up test fixtures."""
        self.settings_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "settings.json"
        )
        self.assertTrue(
            os.path.exists(self.settings_file), "Settings file should exist"
        )

    def test_settings_file_has_valid_json(self):
        """Test that settings.json is valid JSON."""
        with open(self.settings_file, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"Settings file should be valid JSON: {e}")

    def test_hooks_configuration_exists(self):
        """Test that hooks configuration exists."""
        with open(self.settings_file, "r") as f:
            settings = json.load(f)

        self.assertIn("hooks", settings, "Settings should contain hooks configuration")
        hooks = settings["hooks"]

        # Check for Stop hook
        self.assertIn("Stop", hooks, "Should have Stop hook configured")
        stop_hooks = hooks["Stop"]
        self.assertIsInstance(stop_hooks, list, "Stop hooks should be a list")
        self.assertTrue(len(stop_hooks) > 0, "Should have at least one Stop hook")

        # Check for SubagentStop hook
        self.assertIn("SubagentStop", hooks, "Should have SubagentStop hook configured")
        subagent_hooks = hooks["SubagentStop"]
        self.assertIsInstance(
            subagent_hooks, list, "SubagentStop hooks should be a list"
        )
        self.assertTrue(
            len(subagent_hooks) > 0, "Should have at least one SubagentStop hook"
        )

    def test_hook_configurations_have_required_fields(self):
        """Test that hook configurations have required fields."""
        with open(self.settings_file, "r") as f:
            settings = json.load(f)

        hooks = settings["hooks"]

        # Test Stop hook configuration
        stop_hook = hooks["Stop"][0]["hooks"][0]
        self.assertEqual(stop_hook["type"], "command")
        self.assertIn("teamcoach-stop.py", stop_hook["command"])
        self.assertEqual(stop_hook["timeout"], 300)  # 5 minutes

        # Test SubagentStop hook configuration
        subagent_hook = hooks["SubagentStop"][0]["hooks"][0]
        self.assertEqual(subagent_hook["type"], "command")
        self.assertIn("teamcoach-subagent-stop.py", subagent_hook["command"])
        self.assertEqual(subagent_hook["timeout"], 180)  # 3 minutes

    def test_hook_commands_use_project_relative_paths(self):
        """Test that hook commands use project-relative paths."""
        with open(self.settings_file, "r") as f:
            settings = json.load(f)

        hooks = settings["hooks"]

        # Check Stop hook path
        stop_command = hooks["Stop"][0]["hooks"][0]["command"]
        self.assertIn("$CLAUDE_PROJECT_DIR", stop_command)

        # Check SubagentStop hook path
        subagent_command = hooks["SubagentStop"][0]["hooks"][0]["command"]
        self.assertIn("$CLAUDE_PROJECT_DIR", subagent_command)


class TestTeamCoachHookIntegration(unittest.TestCase):
    """Test TeamCoach hook integration with the overall system."""

    def test_hook_files_are_executable(self):
        """Test that hook files have correct permissions."""
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        stop_hook = os.path.join(base_dir, "teamcoach-stop.py")
        subagent_hook = os.path.join(base_dir, "teamcoach-subagent-stop.py")

        self.assertTrue(os.access(stop_hook, os.X_OK), "Stop hook should be executable")
        self.assertTrue(
            os.access(subagent_hook, os.X_OK), "Subagent hook should be executable"
        )

    def test_hook_files_have_shebang(self):
        """Test that hook files have proper shebang."""
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        for hook_file in ["teamcoach-stop.py", "teamcoach-subagent-stop.py"]:
            hook_path = os.path.join(base_dir, hook_file)
            with open(hook_path, "r") as f:
                first_line = f.readline().strip()
                self.assertTrue(
                    first_line.startswith("#!"), f"{hook_file} should have shebang"
                )
                self.assertIn("python", first_line, f"{hook_file} should use Python")

    def test_hooks_handle_errors_gracefully(self):
        """Test that hooks are designed to handle errors gracefully."""
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        for hook_file in ["teamcoach-stop.py", "teamcoach-subagent-stop.py"]:
            hook_path = os.path.join(base_dir, hook_file)
            with open(hook_path, "r") as f:
                content = f.read()

                # Should have try-except blocks
                self.assertIn("try:", content)
                self.assertIn("except", content)

                # Should always exit with success to avoid blocking
                self.assertIn("sys.exit(0)", content)

                # Should return 'continue' action
                self.assertIn('"action": "continue"', content)


if __name__ == "__main__":
    unittest.main()
