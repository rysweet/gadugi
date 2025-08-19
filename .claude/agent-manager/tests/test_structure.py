import unittest

#!/usr/bin/env python3

"""
Simple structural tests for Agent Manager sub-agent.

These tests validate that the agent-manager file exists and has proper structure.
"""

from pathlib import Path

class TestAgentManagerStructure(unittest.TestCase):
    """Test the Agent Manager sub-agent file structure."""

    def setUp(self):
        """Set up test environment."""
        self.agent_manager_root = Path(__file__).parent.parent
        self.agent_file = self.agent_manager_root.parent / "agents" / "agent-manager.md"

    def test_agent_manager_file_exists(self):
        """Test that agent-manager.md exists in the correct location."""
        self.assertTrue(
            self.agent_file.exists(),
            f"Agent manager file not found at {self.agent_file}",
        )

    def test_agent_manager_has_frontmatter(self):
        """Test that agent-manager.md has proper YAML frontmatter."""
        with open(self.agent_file, "r") as f:
            content = f.read()

        # Check for YAML frontmatter
        self.assertTrue(
            content.startswith("---\n"), "Agent file should start with YAML frontmatter"
        )

        # Find end of frontmatter
        frontmatter_end = content.find("\n---\n", 4)
        self.assertGreater(
            frontmatter_end, 0, "YAML frontmatter should be properly closed"
        )

        # Check required fields in frontmatter
        frontmatter = content[4:frontmatter_end]
        required_fields = ["name:", "description:", "required_tools:"]

        for field in required_fields:
            self.assertIn(
                field, frontmatter, f"Frontmatter missing required field: {field}"
            )

    def test_agent_manager_directory_structure(self):
        """Test that agent-manager directory has expected structure."""
        expected_dirs = ["cache", "config", "templates", "tests", "docs"]

        for dir_name in expected_dirs:
            dir_path = self.agent_manager_root / dir_name
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Expected directory not found: {dir_name}",
            )

    def test_configuration_templates_exist(self):
        """Test that configuration template files exist."""
        templates_dir = self.agent_manager_root / "templates"
        expected_templates = ["config.yaml.template", "preferences.yaml.template"]

        for template in expected_templates:
            template_path = templates_dir / template
            self.assertTrue(
                template_path.exists(), f"Template file not found: {template}"
            )

if __name__ == "__main__":
    unittest.main()
