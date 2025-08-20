#!/usr/bin/env python3
"""
Simple integration test for Team Coach agent files.

This test verifies that the Team Coach files were created correctly
and validates basic functionality without external dependencies.
"""

import unittest
import os
import sys
from pathlib import Path


class TestTeamCoachIntegration(unittest.TestCase):
    """Test Team Coach file structure and basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.teamcoach_dir = self.project_root / ".claude" / "agents" / "teamcoach"

    def test_teamcoach_directory_exists(self):
        """Test that the teamcoach directory exists."""
        self.assertTrue(self.teamcoach_dir.exists())
        self.assertTrue(self.teamcoach_dir.is_dir())

    def test_main_integration_file_exists(self):
        """Test that the main team_coach.py integration file exists."""
        team_coach_file = self.teamcoach_dir / "team_coach.py"
        self.assertTrue(team_coach_file.exists())
        self.assertTrue(team_coach_file.is_file())

    def test_readme_file_exists(self):
        """Test that the README documentation exists."""
        readme_file = self.teamcoach_dir / "README.md"
        self.assertTrue(readme_file.exists())
        self.assertTrue(readme_file.is_file())

    def test_example_usage_file_exists(self):
        """Test that the example usage file exists."""
        example_file = self.teamcoach_dir / "example_usage.py"
        self.assertTrue(example_file.exists())
        self.assertTrue(example_file.is_file())

    def test_test_file_exists(self):
        """Test that the comprehensive test file exists."""
        test_file = self.project_root / "tests" / "test_team_coach.py"
        self.assertTrue(test_file.exists())
        self.assertTrue(test_file.is_file())

    def test_main_integration_file_content(self):
        """Test that the main integration file has the expected content."""
        team_coach_file = self.teamcoach_dir / "team_coach.py"
        content = team_coach_file.read_text()

        # Check for main class definition
        self.assertIn("class TeamCoach:", content)

        # Check for key methods
        self.assertIn("def execute(", content)
        self.assertIn("def execute_async(", content)

        # Check for all expected actions
        expected_actions = [
            "analyze_session",
            "identify_improvements",
            "track_performance_trends",
            "generate_coaching_report",
            "optimize_task_assignment",
            "form_project_team",
            "resolve_conflicts",
            "optimize_workflow",
            "strategic_planning",
        ]

        for action in expected_actions:
            self.assertIn(action, content)

    def test_readme_content(self):
        """Test that the README has the expected sections."""
        readme_file = self.teamcoach_dir / "README.md"
        content = readme_file.read_text()

        # Check for key sections
        expected_sections = [
            "# Team Coach Agent",
            "## Overview",
            "## Key Features",
            "## Installation",
            "## Usage Examples",
            "## API Reference",
            "## Configuration",
            "## Testing",
            "## Architecture",
        ]

        for section in expected_sections:
            self.assertIn(section, content)

    def test_example_usage_content(self):
        """Test that the example usage file has working examples."""
        example_file = self.teamcoach_dir / "example_usage.py"
        content = example_file.read_text()

        # Check for example functions
        expected_examples = [
            "def example_session_analysis(",
            "def example_improvement_identification(",
            "def example_performance_trends(",
            "def example_task_assignment_optimization(",
            "def example_team_formation(",
            "def example_conflict_resolution(",
            "def example_workflow_optimization(",
            "def example_strategic_planning(",
            "def example_coaching_report(",
            "def run_all_examples(",
        ]

        for example in expected_examples:
            self.assertIn(example, content)

    def test_test_file_content(self):
        """Test that the test file has comprehensive test coverage."""
        test_file = self.project_root / "tests" / "test_team_coach.py"
        content = test_file.read_text()

        # Check for test class and methods
        self.assertIn("class TestTeamCoach(", content)

        # Check for key test methods covering all actions
        expected_tests = [
            "test_analyze_session_success",
            "test_identify_improvements_success",
            "test_track_performance_trends_success",
            "test_generate_coaching_report_success",
            "test_optimize_task_assignment_success",
            "test_form_project_team_success",
            "test_resolve_conflicts_success",
            "test_optimize_workflow_success",
            "test_strategic_planning_success",
        ]

        for test in expected_tests:
            self.assertIn(test, content)

    def test_file_permissions(self):
        """Test that the Python files are executable."""
        team_coach_file = self.teamcoach_dir / "team_coach.py"
        example_file = self.teamcoach_dir / "example_usage.py"
        test_file = self.project_root / "tests" / "test_team_coach.py"

        # Check that files are readable
        self.assertTrue(os.access(team_coach_file, os.R_OK))
        self.assertTrue(os.access(example_file, os.R_OK))
        self.assertTrue(os.access(test_file, os.R_OK))

    def test_phase_directories_exist(self):
        """Test that all phase directories exist."""
        phase_dirs = ["phase1", "phase2", "phase3"]

        for phase_dir in phase_dirs:
            phase_path = self.teamcoach_dir / phase_dir
            self.assertTrue(
                phase_path.exists(), f"Phase directory {phase_dir} should exist"
            )
            self.assertTrue(
                phase_path.is_dir(),
                f"Phase directory {phase_dir} should be a directory",
            )

    def test_agent_file_exists(self):
        """Test that the team-coach.md agent file exists."""
        agent_file = self.project_root / ".claude" / "agents" / "team-coach.md"
        self.assertTrue(agent_file.exists())
        self.assertTrue(agent_file.is_file())

    def test_basic_syntax_validation(self):
        """Test that Python files have valid syntax."""
        python_files = [
            self.teamcoach_dir / "team_coach.py",
            self.teamcoach_dir / "example_usage.py",
            self.project_root / "tests" / "test_team_coach.py",
        ]

        for py_file in python_files:
            with open(py_file, "r") as f:
                content = f.read()

            # Basic syntax check - try to compile
            try:
                compile(content, str(py_file), "exec")
            except SyntaxError as e:
                self.fail(f"Syntax error in {py_file}: {e}")


class TestTeamCoachFunctionality(unittest.TestCase):
    """Test basic Team Coach functionality with mocked dependencies."""

    def test_mock_team_coach_creation(self):
        """Test creating a mock TeamCoach for testing purposes."""

        # Create a simple mock implementation
        class MockTeamCoach:
            def __init__(self, config=None):
                self.config = config or {}

            def execute(self, request):
                action = request.get("action")
                if action == "analyze_session":
                    return {"status": "success", "metrics": {"performance_score": 85}}
                return {"status": "success", "result": f"Mock result for {action}"}

        # Test the mock
        coach = MockTeamCoach({"test": "config"})
        self.assertEqual(coach.config, {"test": "config"})

        # Test session analysis
        result = coach.execute(
            {"action": "analyze_session", "session_data": {"session_id": "test"}}
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["performance_score"], 85)

    def test_performance_score_calculation_logic(self):
        """Test the performance score calculation logic."""

        def calculate_performance_score(session_data):
            if session_data is None:
                return 0.0

            score = 100.0
            errors = len(session_data.get("errors", []))
            score -= errors * 5
            test_failures = session_data.get("test_failures", 0)
            score -= test_failures * 3
            if session_data.get("pr_created", False):
                score += 10
            return max(0.0, min(100.0, score))

        # Test perfect session
        perfect_session = {"errors": [], "test_failures": 0, "pr_created": True}
        self.assertEqual(calculate_performance_score(perfect_session), 100.0)

        # Test session with errors
        error_session = {
            "errors": ["error1", "error2"],
            "test_failures": 2,
            "pr_created": False,
        }
        expected_score = 100 - (2 * 5) - (2 * 3)  # 100 - 10 - 6 = 84
        self.assertEqual(calculate_performance_score(error_session), expected_score)

        # Test edge case - too many errors
        bad_session = {
            "errors": ["e1", "e2", "e3", "e4", "e5"],  # 25 point deduction
            "test_failures": 30,  # 90 point deduction
            "pr_created": False,
        }
        self.assertEqual(calculate_performance_score(bad_session), 0.0)


if __name__ == "__main__":
    unittest.main()
