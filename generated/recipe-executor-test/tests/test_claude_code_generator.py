"""Tests for Claude Code Generator."""

import pytest
from src.recipe_executor.claude_code_generator import ClaudeCodeGenerator


class TestClaudeCodeGenerator:
    """Test suite for ClaudeCodeGenerator."""

    def test_initialization(self):
        """Test ClaudeCodeGenerator initialization."""
        instance = ClaudeCodeGenerator()
        assert instance.name == "Claude Code Generator"
        assert instance.data == {}

    def test_methods(self):
        """Test ClaudeCodeGenerator methods."""
        instance = ClaudeCodeGenerator()
        # Test that methods work without raising exceptions
        assert instance.validate() is True
        assert instance.execute() is True

        # Test process method if it exists
        if hasattr(instance, "process"):
            result = instance.process({"test": "data"})
            assert result is not None
            assert "processed" in result
