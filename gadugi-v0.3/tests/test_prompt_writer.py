#!/usr/bin/env python3
"""Tests for the prompt-writer agent functionality."""

import sys
import unittest
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(src_path))

from prompt_writer_engine import (  # noqa: E402
    PromptWriterEngine,
    _generate_filename,
    generate_prompt_for_task,
)
from run_agent import run_agent  # noqa: E402


class TestPromptWriterEngine(unittest.TestCase):
    """Test the core prompt writer engine functionality."""

    def setUp(self) -> None:
        self.engine = PromptWriterEngine()

    def test_engine_initialization(self) -> None:
        """Test that the engine initializes with proper structure."""
        assert isinstance(self.engine.template_structure, dict)
        assert "overview" in self.engine.template_structure
        assert "workflow_steps" in self.engine.template_structure
        assert isinstance(self.engine.template_structure["workflow_steps"], list)

    def test_task_analysis(self) -> None:
        """Test task analysis functionality."""
        task = "Implement user authentication system"
        analysis = self.engine._analyze_task(task)

        assert "original_task" in analysis
        assert "title" in analysis
        assert "task_type" in analysis
        assert "complexity" in analysis
        assert analysis["original_task"] == task
        assert analysis["task_type"] == "feature_implementation"

    def test_title_extraction(self) -> None:
        """Test title extraction from task descriptions."""
        test_cases = [
            ("implement user authentication", "User Authentication Implementation"),
            ("Add shopping cart feature", "Shopping Cart Feature Implementation"),
            ("fix login bug", "Login Bug Implementation"),
            ("Create API endpoint Implementation", "Api Endpoint Implementation"),
        ]

        for task, expected_title in test_cases:
            title = self.engine._extract_title(task)
            assert title == expected_title

    def test_task_type_detection(self) -> None:
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
            assert task_type == expected_type

    def test_complexity_estimation(self) -> None:
        """Test complexity estimation."""
        test_cases = [
            ("fix simple button color", "low"),
            ("add user profile feature", "medium"),
            ("implement authentication system with database", "high"),
            ("create microservice architecture", "high"),
        ]

        for task, expected_complexity in test_cases:
            complexity = self.engine._estimate_complexity(task)
            assert complexity == expected_complexity

    def test_component_identification(self) -> None:
        """Test component identification."""
        task = "build web API with database authentication"
        components = self.engine._identify_components(task)

        assert "web" in components
        assert "api" in components
        assert "database" in components
        assert "auth" in components

    def test_prompt_generation(self) -> None:
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
            assert section in prompt_data

        # Check requirements structure
        assert "functional" in prompt_data["requirements"]
        assert "technical" in prompt_data["requirements"]
        assert isinstance(prompt_data["requirements"]["functional"], list)
        assert isinstance(prompt_data["requirements"]["technical"], list)

        # Check implementation plan structure
        assert "phase1" in prompt_data["implementation_plan"]
        assert "phase2" in prompt_data["implementation_plan"]

        # Check metadata
        assert "generated_at" in prompt_data["metadata"]
        assert "task_type" in prompt_data["metadata"]

    def test_markdown_formatting(self) -> None:
        """Test markdown formatting of prompts."""
        task = "Create simple todo list"
        prompt_data = self.engine.generate_prompt(task)
        markdown = self.engine.format_as_markdown(prompt_data)

        # Check markdown structure
        assert markdown.startswith("# ")
        assert "## Overview" in markdown
        assert "## Problem Statement" in markdown
        assert "## Requirements" in markdown
        assert "## Implementation Plan" in markdown
        assert "## Success Criteria" in markdown
        assert "## Workflow Steps" in markdown

        # Check for proper markdown formatting
        assert "### Functional Requirements" in markdown
        assert "### Technical Requirements" in markdown

        # Should contain numbered workflow steps
        assert "1. Create GitHub issue" in markdown


class TestPromptWriterIntegration(unittest.TestCase):
    """Test integration with orchestrator system."""

    def test_generate_prompt_for_task(self) -> None:
        """Test the main generation function."""
        task = "Add user authentication"
        result = generate_prompt_for_task(task, save_to_file=False)

        assert result["success"]
        assert "prompt_data" in result
        assert "markdown" in result
        assert "suggested_filename" in result

        # Check filename generation
        filename = result["suggested_filename"]
        assert filename.endswith(".md")
        assert filename.startswith("implement-")

    def test_filename_generation(self) -> None:
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
            assert filename.endswith(".md")
            # Check that it starts with expected prefix
            expected_prefix = expected_pattern.split("-")[0]
            assert filename.startswith(expected_prefix)

    def test_run_agent_integration(self) -> None:
        """Test integration with run_agent system."""
        task = "Create simple API endpoint"
        result = run_agent("prompt-writer", task)

        assert result["success"]
        assert result["agent"] == "prompt-writer"
        assert result["task"] == task
        assert result["returncode"] == 0

        # Check that stdout contains a proper markdown prompt
        stdout = result["stdout"]
        assert "# " in stdout  # Should have title
        assert "## Overview" in stdout
        assert "## Requirements" in stdout
        assert "## Implementation Plan" in stdout

        # Check metadata is included
        assert "metadata" in result
        assert "suggested_filename" in result["metadata"]


class TestPromptWriterErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_empty_task_description(self) -> None:
        """Test handling of empty task description."""
        result = generate_prompt_for_task("", save_to_file=False)
        assert result["success"]

        # Should generate generic prompt
        markdown = result["markdown"]
        assert "# " in markdown

    def test_very_long_task_description(self) -> None:
        """Test handling of very long task descriptions."""
        long_task = "implement " + "very complex system " * 20
        result = generate_prompt_for_task(long_task, save_to_file=False)

        assert result["success"]
        # Filename should be truncated
        filename = result["suggested_filename"]
        assert len(filename) < 100  # Reasonable limit

    def test_special_characters_in_task(self) -> None:
        """Test handling of special characters."""
        task = "implement user auth w/ OAuth2.0 & JWT tokens!"
        result = generate_prompt_for_task(task, save_to_file=False)

        assert result["success"]
        filename = result["suggested_filename"]
        # Should clean special characters from filename
        assert "!" not in filename
        assert "&" not in filename

    def test_run_agent_error_handling(self) -> None:
        """Test error handling in run_agent integration."""
        # This should still work with empty task
        result = run_agent("prompt-writer", "")
        assert result["success"]

        # Check error case by testing with invalid import (simulated)
        # This is harder to test without modifying the import system


class TestPromptWriterQuality(unittest.TestCase):
    """Test the quality and completeness of generated prompts."""

    def test_feature_implementation_quality(self) -> None:
        """Test quality of feature implementation prompts."""
        task = "Add user authentication with email and password"
        result = generate_prompt_for_task(task)
        prompt_data = result["prompt_data"]

        # Should have comprehensive requirements
        functional_reqs = prompt_data["requirements"]["functional"]
        assert len(functional_reqs) > 2

        technical_reqs = prompt_data["requirements"]["technical"]
        assert len(technical_reqs) > 2

        # Should have phased implementation plan
        plan = prompt_data["implementation_plan"]
        assert "phase1" in plan
        assert "phase2" in plan
        assert "phase3" in plan
        assert "phase4" in plan

        # Success criteria should be specific
        success_criteria = prompt_data["success_criteria"]
        assert len(success_criteria) > 3

    def test_bug_fix_quality(self) -> None:
        """Test quality of bug fix prompts."""
        task = "Fix login redirect issue after authentication"
        result = generate_prompt_for_task(task)
        prompt_data = result["prompt_data"]

        # Should be identified as bug fix
        assert prompt_data["metadata"]["task_type"] == "bug_fix"

        # Should have appropriate requirements for bug fix
        functional_reqs = prompt_data["requirements"]["functional"]
        technical_reqs = prompt_data["requirements"]["technical"]

        # Bug fixes should mention testing and root cause
        all_reqs = functional_reqs + technical_reqs
        req_text = " ".join(all_reqs).lower()
        assert any(word in req_text for word in ["test", "root cause", "regression"])

    def test_workflow_completeness(self) -> None:
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
            assert element in workflow_text, f"Workflow missing essential element: {element}"


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
