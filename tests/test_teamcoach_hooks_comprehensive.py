import unittest
import json
import subprocess
import tempfile
import os
import sys
import io
import importlib.util

#!/usr/bin/env python3

"""
Comprehensive tests for TeamCoach hooks functionality.
This test suite provides complete coverage of TeamCoach hook integration.
"""

from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTeamCoachStopHookUnit(unittest.TestCase):
    """Unit tests for TeamCoach stop hook functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.hook_script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".claude",
            "hooks",
            "teamcoach-stop.py",
        )

        # Load the hook module directly for unit testing
        spec = importlib.util.spec_from_file_location(
            "teamcoach_stop", self.hook_script_path
        )
        self.hook_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.hook_module)

    def test_hook_script_exists_and_executable(self):
        """Test that the hook script exists and is executable."""
        self.assertTrue(
            os.path.exists(self.hook_script_path), "Hook script should exist"
        )
        self.assertTrue(
            os.access(self.hook_script_path, os.X_OK),
            "Hook script should be executable",
        )

    def test_hook_has_correct_shebang(self):
        """Test that the hook has the correct shebang."""
        with open(self.hook_script_path, "r") as f:
            first_line = f.readline().strip()
        self.assertEqual(first_line, "#!/usr/bin/env python3")

    @patch("subprocess.run")
    def test_invoke_teamcoach_success(self, mock_run):
        """Test successful TeamCoach invocation."""
        # Mock successful subprocess
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Call the function
        result = self.hook_module.invoke_teamcoach()

        # Verify
        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "claude")
        self.assertEqual(args[1], "/agent:teamcoach")
        self.assertIn("Task: Analyze completed session", args[2])

    @patch("subprocess.run")
    def test_invoke_teamcoach_failure(self, mock_run):
        """Test TeamCoach invocation failure."""
        # Mock failed subprocess
        mock_run.return_value = MagicMock(returncode=1, stderr="Error message")

        # Call the function
        result = self.hook_module.invoke_teamcoach()

        # Verify
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_invoke_teamcoach_timeout(self, mock_run):
        """Test TeamCoach invocation timeout."""
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 300)

        # Call the function
        result = self.hook_module.invoke_teamcoach()

        # Verify
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_invoke_teamcoach_exception(self, mock_run):
        """Test TeamCoach invocation with exception."""
        # Mock exception
        mock_run.side_effect = Exception("Unexpected error")

        # Call the function
        result = self.hook_module.invoke_teamcoach()

        # Verify
        self.assertFalse(result)

    def test_teamcoach_prompt_structure(self):
        """Test that the TeamCoach prompt has correct structure."""
        # Get the prompt from the function
        with open(self.hook_script_path, "r") as f:
            content = f.read()

        # Verify prompt components
        self.assertIn("Task: Analyze completed session", content)
        self.assertIn("Context:", content)
        self.assertIn("Analysis Focus:", content)
        self.assertIn("Deliverables:", content)
        self.assertIn("Mode: Post-session analysis", content)

    @patch("sys.stdin", new_callable=io.StringIO)
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_main_function_success(self, mock_print, mock_run, mock_stdin):
        """Test main function with successful execution."""
        # Setup
        mock_stdin.write('{"test": "input"}')
        mock_stdin.seek(0)
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Execute
        with self.assertRaises(SystemExit) as cm:
            self.hook_module.main()

        # Verify
        self.assertEqual(cm.exception.code, 0)

        # Check printed output
        printed_output = None
        for call_args in mock_print.call_args_list:
            if call_args[0][0].startswith("{"):
                printed_output = json.loads(call_args[0][0])
                break

        self.assertIsNotNone(printed_output)
        self.assertEqual(printed_output["action"], "continue")
        self.assertIn("completed", printed_output["message"])
        self.assertIn("timestamp", printed_output)

    @patch("sys.stdin", new_callable=io.StringIO)
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_main_function_failure(self, mock_print, mock_run, mock_stdin):
        """Test main function with failed execution."""
        # Setup
        mock_stdin.write("{}")
        mock_stdin.seek(0)
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")

        # Execute
        with self.assertRaises(SystemExit) as cm:
            self.hook_module.main()

        # Verify
        self.assertEqual(cm.exception.code, 0)  # Should still exit 0

        # Check printed output
        printed_output = None
        for call_args in mock_print.call_args_list:
            if call_args[0][0].startswith("{"):
                printed_output = json.loads(call_args[0][0])
                break

        self.assertIsNotNone(printed_output)
        self.assertEqual(printed_output["action"], "continue")
        self.assertIn("issues", printed_output["message"])

class TestTeamCoachSubagentStopHookUnit(unittest.TestCase):
    """Unit tests for TeamCoach subagent stop hook functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.hook_script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".claude",
            "hooks",
            "teamcoach-subagent-stop.py",
        )

        # Load the hook module directly for unit testing
        spec = importlib.util.spec_from_file_location(
            "teamcoach_subagent_stop", self.hook_script_path
        )
        self.hook_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.hook_module)

    def test_hook_script_exists_and_executable(self):
        """Test that the subagent hook script exists and is executable."""
        self.assertTrue(
            os.path.exists(self.hook_script_path), "Subagent hook script should exist"
        )
        self.assertTrue(
            os.access(self.hook_script_path, os.X_OK),
            "Subagent hook script should be executable",
        )

    @patch("subprocess.run")
    def test_invoke_teamcoach_agent_analysis(self, mock_run):
        """Test TeamCoach agent analysis invocation."""
        # Mock successful subprocess
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Test data
        agent_data = {"agent_name": "test-agent", "result": "success", "duration": 120}

        # Call the function
        result = self.hook_module.invoke_teamcoach_agent_analysis(agent_data)

        # Verify
        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "claude")
        self.assertEqual(args[1], "/agent:teamcoach")

        # Check prompt contains agent data
        prompt = args[2]
        self.assertIn("test-agent", prompt)
        self.assertIn("success", prompt)
        self.assertIn("120", prompt)

    def test_subagent_hook_timeout_is_shorter(self):
        """Test that subagent hook has shorter timeout than main hook."""
        with open(self.hook_script_path, "r") as f:
            content = f.read()

        # Should have 3-minute timeout
        self.assertIn("timeout=180", content)

    @patch("sys.stdin", new_callable=io.StringIO)
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_main_with_malformed_json(self, mock_print, mock_run, mock_stdin):
        """Test main function with malformed JSON input."""
        # Setup
        mock_stdin.write("not valid json")
        mock_stdin.seek(0)
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Execute
        with self.assertRaises(SystemExit) as cm:
            self.hook_module.main()

        # Verify still exits successfully
        self.assertEqual(cm.exception.code, 0)

        # Should still call TeamCoach with empty data
        mock_run.assert_called_once()

class TestTeamCoachHookIntegration(unittest.TestCase):
    """Integration tests for TeamCoach hooks."""

    def test_settings_json_configuration(self):
        """Test that settings.json has safe hooks only (no TeamCoach hooks)."""
        settings_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "settings.json"
        )

        with open(settings_path, "r") as f:
            settings = json.load(f)

        # If hooks exist, verify they don't contain dangerous TeamCoach hooks
        if "hooks" in settings:
            # Check all hook configurations
            for hook_type in settings["hooks"]:
                if isinstance(settings["hooks"][hook_type], list):
                    for hook_config in settings["hooks"][hook_type]:
                        if "hooks" in hook_config:
                            for hook in hook_config["hooks"]:
                                command = hook.get("command", "")
                                # Ensure no TeamCoach hooks that spawn Claude sessions
                                self.assertNotIn(
                                    "teamcoach",
                                    command.lower(),
                                    "TeamCoach hooks should not be present (Issue #89)",
                                )
                                self.assertNotIn(
                                    "claude /agent",
                                    command.lower(),
                                    "Hooks should not spawn new Claude sessions",
                                )

        # Verify permissions are still present (these should remain)
        self.assertIn("permissions", settings, "Permissions should still be configured")

    def test_hook_end_to_end_execution(self):
        """Test end-to-end hook execution (without actually calling TeamCoach)."""
        # Create a temporary directory for our mock
        temp_dir = tempfile.mkdtemp()

        # Create a mock claude script
        mock_claude = os.path.join(temp_dir, "claude")
        with open(mock_claude, "w") as f:
            f.write("""#!/usr/bin/env python3
# Simulate successful claude execution
sys.exit(0)
""")
        os.chmod(mock_claude, 0o755)

        try:
            # Patch PATH to use our mock claude
            env = os.environ.copy()
            env["PATH"] = temp_dir + ":" + env["PATH"]

            # Run the stop hook
            hook_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                ".claude",
                "hooks",
                "teamcoach-stop.py",
            )

            result = subprocess.run(
                ["python", hook_path],
                input="{}",
                text=True,
                capture_output=True,
                env=env,
            )

            # Verify execution
            self.assertEqual(result.returncode, 0)

            # Verify output - extract JSON from potentially mixed output
            lines = result.stdout.strip().split("\n")
            json_output = None
            for line in lines:
                if line.startswith("{"):
                    try:
                        json_output = json.loads(line)
                        break
                    except Exception:
                        continue

            self.assertIsNotNone(json_output, "Should have JSON output")
            self.assertEqual(json_output["action"], "continue")
            self.assertIn("timestamp", json_output)

        finally:
            # Cleanup
            os.unlink(mock_claude)
            os.rmdir(temp_dir)

    def test_both_hooks_are_non_blocking(self):
        """Test that both hooks are designed to be non-blocking."""
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        for hook_file in ["teamcoach-stop.py", "teamcoach-subagent-stop.py"]:
            hook_path = os.path.join(hooks_dir, hook_file)
            with open(hook_path, "r") as f:
                content = f.read()

            # Check for non-blocking patterns
            self.assertIn('"action": "continue"', content)
            self.assertIn("sys.exit(0)", content)
            self.assertNotIn("sys.exit(1)", content)

            # Check for error handling
            self.assertIn("try:", content)
            self.assertIn("except", content)

    def test_hooks_use_appropriate_timeouts(self):
        """Test that hooks use appropriate timeout values."""
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        # Check stop hook (should be 5 minutes)
        with open(os.path.join(hooks_dir, "teamcoach-stop.py"), "r") as f:
            stop_content = f.read()
        self.assertIn("timeout=300", stop_content)

        # Check subagent hook (should be 3 minutes)
        with open(os.path.join(hooks_dir, "teamcoach-subagent-stop.py"), "r") as f:
            subagent_content = f.read()
        self.assertIn("timeout=180", subagent_content)

class TestTeamCoachHookPermissions(unittest.TestCase):
    """Test file permissions and security aspects."""

    def test_hook_files_have_correct_permissions(self):
        """Test that hook files have secure permissions."""
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        for hook_file in ["teamcoach-stop.py", "teamcoach-subagent-stop.py"]:
            hook_path = os.path.join(hooks_dir, hook_file)
            stat_info = os.stat(hook_path)
            mode = stat_info.st_mode

            # Check file is executable by owner
            self.assertTrue(mode & 0o100, f"{hook_file} should be executable by owner")

            # Check file is readable by owner
            self.assertTrue(mode & 0o400, f"{hook_file} should be readable by owner")

            # Check file is not world-writable
            self.assertFalse(mode & 0o002, f"{hook_file} should not be world-writable")

    def test_settings_json_uses_environment_variables(self):
        """Test that if hooks exist, they are safe and properly configured."""
        settings_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "settings.json"
        )

        with open(settings_path, "r") as f:
            settings = json.load(f)

        # If hooks exist, verify they are safe (no TeamCoach or environment variable issues)
        if "hooks" in settings:
            for hook_type in settings["hooks"]:
                if isinstance(settings["hooks"][hook_type], list):
                    for hook_config in settings["hooks"][hook_type]:
                        if "hooks" in hook_config:
                            for hook in hook_config["hooks"]:
                                command = hook.get("command", "")
                                # XPIA hooks are allowed, TeamCoach hooks are not
                                if "xpia" in command.lower():
                                    # XPIA hooks should use relative paths
                                    self.assertIn(
                                        ".claude/hooks/",
                                        command,
                                        "XPIA hooks should use relative paths",
                                    )
                                else:
                                    # No TeamCoach hooks allowed
                                    self.assertNotIn(
                                        "teamcoach",
                                        command.lower(),
                                        "TeamCoach hooks not allowed (Issue #89)",
                                    )

        # Verify that new workflow reflection system components exist as replacement
        base_dir = os.path.dirname(os.path.dirname(__file__))
        reflection_agent = os.path.join(
            base_dir, ".claude", "agents", "workflow-phase-reflection.md"
        )
        self.assertTrue(
            os.path.exists(reflection_agent),
            "Workflow reflection agent should exist as hook replacement",
        )

class TestTeamCoachHookErrorHandling(unittest.TestCase):
    """Test error handling in TeamCoach hooks."""

    def test_hooks_handle_all_exceptions(self):
        """Test that hooks have comprehensive exception handling."""
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        for hook_file in ["teamcoach-stop.py", "teamcoach-subagent-stop.py"]:
            hook_path = os.path.join(hooks_dir, hook_file)
            with open(hook_path, "r") as f:
                content = f.read()

            # Check for general exception handling in main
            self.assertIn("except Exception as e:", content)

            # Check for specific exception types
            self.assertIn("TimeoutExpired", content)

            # Check that errors still result in exit(0)
            self.assertIn("sys.exit(0)", content)

    def test_hooks_provide_meaningful_error_messages(self):
        """Test that hooks provide meaningful error messages."""
        hooks_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".claude", "hooks"
        )

        # Test stop hook error messages
        with open(os.path.join(hooks_dir, "teamcoach-stop.py"), "r") as f:
            stop_content = f.read()

        # Check for descriptive error messages in stop hook
        self.assertIn("TeamCoach analysis failed", stop_content)
        self.assertIn("TeamCoach analysis timed out", stop_content)
        self.assertIn("Error invoking TeamCoach", stop_content)
        self.assertIn("hook error", stop_content)

        # Test subagent hook error messages
        with open(os.path.join(hooks_dir, "teamcoach-subagent-stop.py"), "r") as f:
            subagent_content = f.read()

        # Check for descriptive error messages in subagent hook
        self.assertIn("TeamCoach agent analysis failed", subagent_content)
        self.assertIn("TeamCoach agent analysis timed out", subagent_content)
        self.assertIn("Error in TeamCoach agent analysis", subagent_content)
        self.assertIn("hook error", subagent_content)

if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
