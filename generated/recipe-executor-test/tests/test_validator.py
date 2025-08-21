"""Tests for Validator."""

import pytest
from src.recipe_executor.validator import Validator


class TestValidator:
    """Test suite for Validator."""

    def test_initialization(self):
        """Test Validator initialization."""
        instance = Validator()
        assert instance.name == "Validator"
        assert instance.data == {}

    def test_methods(self):
        """Test Validator methods."""
        instance = Validator()
        # Test that methods work without raising exceptions
        assert instance.validate() is True
        assert instance.execute() is True

        # Test process method if it exists
        if hasattr(instance, "process"):
            result = instance.process({"test": "data"})
            assert result is not None
            assert "processed" in result
