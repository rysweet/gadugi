#!/usr/bin/env python3
"""
Tests for the prompt-writer agent functionality.
"""

import json
import unittest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(src_path))

from prompt_writer_engine import (
    PromptWriterEngine,
    generate_prompt_for_task,
    _generate_filename,
)
from run_agent import run_agent


class TestPromptWriterEngine(unittest.TestCase):
    """Test the core prompt writer engine functionality."""

    def setUp(self):
        self.engine = PromptWriterEngine()

    def test_engine_initialization(self):
        """Test that the engine initializes with proper structure."""
        self.assertIsInstance(self.engine.template_structure, dict)
        self.assertIn("overview", self.engine.template_structure)
        self.assertIn("workflow_steps", self.engine.template_structure)
        self.assertIsInstance(self.engine.template_structure["workflow_steps"], list)

    def test_task_analysis(self):
        """Test task analysis functionality."""
        task = "Implement user authentication system"
        analysis = self.engine._analyze_task(task)

        self.assertIn("original_task", analysis)
        self.assertIn("title", analysis)
        self.assertIn("task_type", analysis)
        self.assertIn("complexity", analysis)
        self.assertEqual(analysis["original_task"], task)
        self.assertEqual(analysis["task_type"], "feature_implementation")

    def test_title_extraction(self):
        """Test title extraction from task descriptions."""
        test_cases = [
            ("implement user authentication", "User Authentication Implementation"),
            ("Add shopping cart feature", "Shopping Cart Feature Implementation"),
            ("fix login bug", "Login Bug Implementation"),
            ("Create API endpoint Implementation", "Api Endpoint Implementation"),
        ]

        for task, expected_title in test_cases:
            title = self.engine._extract_title(task)
            self.assertEqual(title, expected_title)

    def test_task_type_detection(self):
        """Test task type detection."""
        test_cases = [
            ("implement user auth", "feature_implementation"),
            ("fix login bug", "bug_fix"),
            ("enhance performance", "enhancement"),
            ("add unit tests", "feature_implementation"),
            ("update documentation", "enhancement"),
        ]

        for task, expected_type in test_cases:
            task_type = self.engine._determine_task_type(task)
            self.assertEqual(task_type, expected_type)

    def test_complexity_estimation(self):
        """Test complexity estimation."""
        test_cases = [
            ("fix simple button color", "low"),
            ("add user profile feature", "medium"),
            ("implement authentication system with database", "high"),
            ("create microservice architecture", "high"),
        ]

        for task, expected_complexity in test_cases:
            complexity = self.engine._estimate_complexity(task)
            self.assertEqual(complexity, expected_complexity)

    def test_component_identification(self):
        """Test component identification."""
        task = "build web API with database authentication"
        components = self.engine._identify_components(task)

        self.assertIn("web", components)
        self.assertIn("api", components)
        self.assertIn("database", components)
        self.assertIn("auth", components)

    def test_prompt_generation(self):
        """Test full prompt generation."""
        task = "Add user registration with email verification"
        prompt_data = self.engine.generate_prompt(task)

        # Check required sections exist
        required_sections = [
            "title",
            "overview",
            "problem_statement",
            "requirements",
            "implementation_plan",
            "success_criteria",
            "workflow_steps",
            "metadata",
        ]

        for section in required_sections:
            self.assertIn(section, prompt_data)

        # Check requirements structure
        self.assertIn("functional", prompt_data["requirements"])
        self.assertIn("technical", prompt_data["requirements"])
        self.assertIsInstance(prompt_data["requirements"]["functional"], list)
        self.assertIsInstance(prompt_data["requirements"]["technical"], list)

        # Check implementation plan structure
        self.assertIn("phase1", prompt_data["implementation_plan"])
        self.assertIn("phase2", prompt_data["implementation_plan"])

        # Check metadata
        self.assertIn("generated_at", prompt_data["metadata"])
        self.assertIn("task_type", prompt_data["metadata"])

    def test_markdown_formatting(self):
        """Test markdown formatting of prompts."""
        task = "Create simple todo list"
        prompt_data = self.engine.generate_prompt(task)
        markdown = self.engine.format_as_markdown(prompt_data)

        # Check markdown structure
        self.assertTrue(markdown.startswith("# "))
        self.assertIn("## Overview", markdown)
        self.assertIn("## Problem Statement", markdown)
        self.assertIn("## Requirements", markdown)
        self.assertIn("## Implementation Plan", markdown)
        self.assertIn("## Success Criteria", markdown)
        self.assertIn("## Workflow Steps", markdown)

        # Check for proper markdown formatting
        self.assertIn("### Functional Requirements", markdown)
        self.assertIn("### Technical Requirements", markdown)

        # Should contain numbered workflow steps
        self.assertIn("1. Create GitHub issue", markdown)


class TestPromptWriterIntegration(unittest.TestCase):
    """Test integration with orchestrator system."""

    def test_generate_prompt_for_task(self):
        """Test the main generation function."""
        task = "Add user authentication"
        result = generate_prompt_for_task(task, save_to_file=False)

        self.assertTrue(result["success"])
        self.assertIn("prompt_data", result)
        self.assertIn("markdown", result)
        self.assertIn("suggested_filename", result)

        # Check filename generation
        filename = result["suggested_filename"]
        self.assertTrue(filename.endswith(".md"))
        self.assertTrue(filename.startswith("implement-"))

    def test_filename_generation(self):
        """Test filename generation."""
        test_cases = [
            (
                "implement user authentication",
                "implement-implement-user-authentication.md",
            ),
            ("fix login bug", "fix-fix-login-bug.md"),
            (
                "enhance dashboard performance",
                "enhance-enhance-dashboard-performance.md",
            ),
        ]

        for task, expected_pattern in test_cases:
            filename = _generate_filename(task)
            self.assertTrue(filename.endswith(".md"))
            # Check that it starts with expected prefix
            expected_prefix = expected_pattern.split("-")[0]
            self.assertTrue(filename.startswith(expected_prefix))

    def test_run_agent_integration(self):
        """Test integration with run_agent system."""
        task = "Create simple API endpoint"
        result = run_agent("prompt-writer", task)

        self.assertTrue(result["success"])
        self.assertEqual(result["agent"], "prompt-writer")
        self.assertEqual(result["task"], task)
        self.assertEqual(result["returncode"], 0)

        # Check that stdout contains a proper markdown prompt
        stdout = result["stdout"]
        self.assertIn("# ", stdout)  # Should have title
        self.assertIn("## Overview", stdout)
        self.assertIn("## Requirements", stdout)
        self.assertIn("## Implementation Plan", stdout)

        # Check metadata is included
        self.assertIn("metadata", result)
        self.assertIn("suggested_filename", result["metadata"])


class TestPromptWriterErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_empty_task_description(self):
        """Test handling of empty task description."""
        result = generate_prompt_for_task("", save_to_file=False)
        self.assertTrue(result["success"])

        # Should generate generic prompt
        markdown = result["markdown"]
        self.assertIn("# ", markdown)

    def test_very_long_task_description(self):
        """Test handling of very long task descriptions."""
        long_task = "implement " + "very complex system " * 20
        result = generate_prompt_for_task(long_task, save_to_file=False)

        self.assertTrue(result["success"])
        # Filename should be truncated
        filename = result["suggested_filename"]
        self.assertTrue(len(filename) < 100)  # Reasonable limit

    def test_special_characters_in_task(self):
        """Test handling of special characters."""
        task = "implement user auth w/ OAuth2.0 & JWT tokens!"
        result = generate_prompt_for_task(task, save_to_file=False)

        self.assertTrue(result["success"])
        filename = result["suggested_filename"]
        # Should clean special characters from filename
        self.assertNotIn("!", filename)
        self.assertNotIn("&", filename)

    def test_run_agent_error_handling(self):
        """Test error handling in run_agent integration."""
        # This should still work with empty task
        result = run_agent("prompt-writer", "")
        self.assertTrue(result["success"])

        # Check error case by testing with invalid import (simulated)
        # This is harder to test without modifying the import system


class TestPromptWriterQuality(unittest.TestCase):
    """Test the quality and completeness of generated prompts."""

    def test_feature_implementation_quality(self):
        """Test quality of feature implementation prompts."""
        task = "Add user authentication with email and password"
        result = generate_prompt_for_task(task)
        prompt_data = result["prompt_data"]

        # Should have comprehensive requirements
        functional_reqs = prompt_data["requirements"]["functional"]
        self.assertGreater(len(functional_reqs), 2)

        technical_reqs = prompt_data["requirements"]["technical"]
        self.assertGreater(len(technical_reqs), 2)

        # Should have phased implementation plan
        plan = prompt_data["implementation_plan"]
        self.assertIn("phase1", plan)
        self.assertIn("phase2", plan)
        self.assertIn("phase3", plan)
        self.assertIn("phase4", plan)

        # Success criteria should be specific
        success_criteria = prompt_data["success_criteria"]
        self.assertGreater(len(success_criteria), 3)

    def test_bug_fix_quality(self):
        """Test quality of bug fix prompts."""
        task = "Fix login redirect issue after authentication"
        result = generate_prompt_for_task(task)
        prompt_data = result["prompt_data"]

        # Should be identified as bug fix
        self.assertEqual(prompt_data["metadata"]["task_type"], "bug_fix")

        # Should have appropriate requirements for bug fix
        functional_reqs = prompt_data["requirements"]["functional"]
        technical_reqs = prompt_data["requirements"]["technical"]

        # Bug fixes should mention testing and root cause
        all_reqs = functional_reqs + technical_reqs
        req_text = " ".join(all_reqs).lower()
        self.assertTrue(
            any(word in req_text for word in ["test", "root cause", "regression"])
        )

    def test_workflow_completeness(self):
        """Test that workflow steps are complete."""
        task = "Create user dashboard"
        result = generate_prompt_for_task(task)

        workflow_steps = result["prompt_data"]["workflow_steps"]

        # Should include key workflow elements
        workflow_text = " ".join(workflow_steps).lower()
        essential_elements = [
            "issue",
            "branch",
            "implement",
            "test",
            "documentation",
            "pull request",
            "review",
        ]

        for element in essential_elements:
            self.assertTrue(
                element in workflow_text,
                f"Workflow missing essential element: {element}",
            )


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
