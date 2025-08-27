#!/usr/bin/env python3
"""
Test the agent-manager hook setup functionality with external scripts.

These tests validate that the agent-manager correctly sets up SessionStart hooks
in .claude/settings.json using the external setup-hooks.sh script.
"""

import json
import os
import shutil
import subprocess
# # import sys  # Not used  # Not currently used
import tempfile
import unittest
from pathlib import Path


class TestAgentManagerHookSetup(unittest.TestCase):
    """Test the Agent Manager hook setup functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create .claude directory
        self.claude_dir = Path(self.test_dir) / '.claude'
        self.claude_dir.mkdir()

        # Path to settings.json
        self.settings_file = self.claude_dir / 'settings.json'

        # Path to hooks directory
        self.hooks_dir = self.claude_dir / 'hooks'

        # Path to agent-manager script
        self.agent_manager_root = Path(__file__).parent.parent
        self.setup_script = self.agent_manager_root / 'scripts' / 'setup-hooks.sh'

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def run_setup_script(self):
        """Run the setup-hooks.sh script in the test directory."""
        result = subprocess.run(
            ['/bin/bash', str(self.setup_script)],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        )
        return result

    def test_hook_setup_creates_settings_file(self):
        """Test that setup script creates settings.json if it doesn't exist."""
        result = self.run_setup_script()

        # Check that settings.json was created
        self.assertTrue(self.settings_file.exists(),
                       f"settings.json not created. Stdout: {result.stdout}\nStderr: {result.stderr}")

        # Validate JSON structure
        with open(self.settings_file, 'r') as f:
            settings = json.load(f)

        self.assertIn('hooks', settings)
        self.assertIn('SessionStart', settings['hooks'])
        self.assertIsInstance(settings['hooks']['SessionStart'], list)

    def test_hook_setup_preserves_existing_settings(self):
        """Test that setup script preserves existing settings."""
        # Create existing settings with permissions
        existing_settings = {
            "permissions": {
                "allow": ["Bash(echo:*)", "Read(*)", "Write(*)"],
                "deny": ["Bash(rm:*)"]
            },
            "other_config": {
                "key": "value"
            }
        }

        with open(self.settings_file, 'w') as f:
            json.dump(existing_settings, f, indent=2)

        # Run setup
        self.run_setup_script()

        # Check that existing settings are preserved
        with open(self.settings_file, 'r') as f:
            updated_settings = json.load(f)

        self.assertIn('permissions', updated_settings)
        self.assertEqual(updated_settings['permissions'], existing_settings['permissions'])
        self.assertIn('other_config', updated_settings)
        self.assertEqual(updated_settings['other_config'], existing_settings['other_config'])
        self.assertIn('hooks', updated_settings)

    def test_hook_command_is_shell_compatible(self):
        """Test that the hook command is shell-compatible and doesn't use /agent: syntax."""
        self.run_setup_script()

        # Check the hook command
        with open(self.settings_file, 'r') as f:
            settings = json.load(f)

        # Find agent-manager hook by looking for check-agent-updates.sh
        agent_hooks = [h for h in settings['hooks']['SessionStart']
                      if 'check-agent-updates.sh' in str(h)]

        self.assertTrue(len(agent_hooks) > 0, "No agent-manager hook found")

        hook = agent_hooks[0]
        self.assertIn('hooks', hook)
        self.assertIsInstance(hook['hooks'], list)
        self.assertTrue(len(hook['hooks']) > 0)

        command = hook['hooks'][0]['command']

        # Verify it doesn't use /agent: syntax
        self.assertNotIn('/agent:', command,
                        "Hook command should not use /agent: syntax")

        # Verify it's a shell script execution
        self.assertIn('check-agent-updates.sh', command,
                     "Hook should run check-agent-updates.sh script")

        # Verify the script was created
        script_path = self.hooks_dir / 'check-agent-updates.sh'
        self.assertTrue(script_path.exists(),
                       f"Script not created at {script_path}")

    def test_hook_deduplication(self):
        """Test that multiple runs don't create duplicate hooks."""
        # Run the script multiple times
        for _ in range(3):
            self.run_setup_script()

        # Check that there's only one agent-manager hook
        with open(self.settings_file, 'r') as f:
            settings = json.load(f)

        agent_hooks = [h for h in settings['hooks']['SessionStart']
                      if 'check-agent-updates.sh' in str(h)]

        self.assertEqual(len(agent_hooks), 1,
                        f"Expected 1 agent-manager hook, found {len(agent_hooks)}")

    def test_backup_creation(self):
        """Test that setup creates backups of existing settings."""
        # Create existing settings
        with open(self.settings_file, 'w') as f:
            json.dump({"existing": "data"}, f)

        self.run_setup_script()

        # Check that a backup was created
        backups = list(self.claude_dir.glob('settings.json.backup.*'))
        self.assertTrue(len(backups) > 0, "No backup file created")

        # Verify backup contains original data
        with open(backups[0], 'r') as f:
            backup_data = json.load(f)

        self.assertEqual(backup_data, {"existing": "data"})

    def test_invalid_json_handling(self):
        """Test that setup handles invalid JSON gracefully."""
        # Create invalid JSON
        with open(self.settings_file, 'w') as f:
            f.write('{"invalid": json content}')

        _ = self.run_setup_script()  # Result not used

        # Should still create valid settings
        self.assertTrue(self.settings_file.exists())

        # The function should have recreated valid JSON
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)  # Should not raise

            self.assertIn('hooks', settings)
            valid_json = True
        except json.JSONDecodeError:
            valid_json = False

        self.assertTrue(valid_json, "Settings file should contain valid JSON after recovery")

        # Check that invalid backup was created
        invalid_backups = list(self.claude_dir.glob('settings.json.backup.*.invalid'))
        self.assertTrue(len(invalid_backups) > 0, "No invalid backup created")

    def test_script_creation(self):
        """Test that the check-agent-updates.sh script is created."""
        self.run_setup_script()

        # Check that script was created
        update_script = self.hooks_dir / 'check-agent-updates.sh'
        self.assertTrue(update_script.exists(),
                       f"Update script not created at {update_script}")

        # Check that script is executable
        self.assertTrue(os.access(update_script, os.X_OK),
                       "Update script is not executable")

        # Check script content
        content = update_script.read_text()
        self.assertIn('#!/bin/sh', content, "Script missing shebang")
        self.assertIn('Agent Manager', content,
                     "Script missing expected content")

    def test_gitignore_update(self):
        """Test that .gitignore is created/updated with agent-manager entries."""
        self.run_setup_script()

        # Check that .gitignore was created or updated
        gitignore_path = Path(self.test_dir) / '.gitignore'
        self.assertTrue(gitignore_path.exists(), ".gitignore not created")

        # Check content
        content = gitignore_path.read_text()
        expected_entries = [
            '.claude/agent-manager/cache/last-check-timestamp',
            '.claude/agent-manager/logs/',
            '.claude/cache/',
            '.claude/hooks/',
        ]

        for entry in expected_entries:
            self.assertIn(entry, content, f"Missing .gitignore entry: {entry}")


if __name__ == '__main__':
    unittest.main()
