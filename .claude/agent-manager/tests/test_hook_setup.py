#!/usr/bin/env python3
"""
Test the agent-manager hook setup functionality.

These tests validate that the agent-manager correctly sets up SessionStart hooks
in .claude/settings.json and creates the check-agent-updates.sh script.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
import shutil
import subprocess
import sys


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
        
        # Path to agent-manager script (we'll need to extract it from the .md file)
        self.agent_manager_root = Path(__file__).parent.parent
        self.agent_file = self.agent_manager_root.parent / 'agents' / 'agent-manager.md'
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def extract_function_from_agent(self, function_name):
        """Extract a bash function from the agent-manager.md file."""
        with open(self.agent_file, 'r') as f:
            content = f.read()
        
        # Find the function
        start_marker = f"{function_name}() {{"
        start = content.find(start_marker)
        if start == -1:
            return None
        
        # Extract until the closing brace at the start of a line
        brace_count = 1
        i = start + len(start_marker)
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1
        
        return content[start:i]
    
    def test_hook_setup_creates_settings_file(self):
        """Test that setup_startup_hooks creates settings.json if it doesn't exist."""
        # Extract and run the setup function
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        self.assertIsNotNone(setup_func, "Could not find setup_startup_hooks function")
        
        # Create a test script that includes the function
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function
setup_startup_hooks
"""
        
        # Write and execute the test script
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        result = subprocess.run(['/bin/bash', str(script_path)], 
                              capture_output=True, text=True)
        
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
        """Test that setup_startup_hooks preserves existing settings."""
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
        
        # Extract and run the setup function
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        subprocess.run(['/bin/bash', str(script_path)], capture_output=True)
        
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
        # Run setup
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        subprocess.run(['/bin/bash', str(script_path)], capture_output=True)
        
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
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function multiple times
setup_startup_hooks
setup_startup_hooks
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        subprocess.run(['/bin/bash', str(script_path)], capture_output=True)
        
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
        
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        subprocess.run(['/bin/bash', str(script_path)], capture_output=True)
        
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
        
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
cd {self.test_dir}

{setup_func}

# Run the function (remove set -e to allow handling of errors)
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        result = subprocess.run(['/bin/bash', str(script_path)], 
                              capture_output=True, text=True)
        
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
        setup_func = self.extract_function_from_agent('setup_startup_hooks')
        test_script = f"""#!/bin/bash
set -e
cd {self.test_dir}

{setup_func}

# Run the function
setup_startup_hooks
"""
        
        script_path = Path(self.test_dir) / 'test_setup.sh'
        script_path.write_text(test_script)
        script_path.chmod(0o755)
        
        subprocess.run(['/bin/bash', str(script_path)], capture_output=True)
        
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


if __name__ == '__main__':
    unittest.main()