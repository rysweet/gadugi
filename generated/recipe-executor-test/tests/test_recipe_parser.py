"""Tests for Recipe Parser."""

import pytest
from src.recipe_executor.recipe_parser import RecipeParser


class TestRecipeParser:
    """Test suite for RecipeParser."""

    def test_initialization(self):
        """Test RecipeParser initialization."""
        instance = RecipeParser()
        assert instance.name == "Recipe Parser"
        assert instance.data == {}

    def test_methods(self):
        """Test RecipeParser methods."""
        instance = RecipeParser()
        # Test that methods work without raising exceptions
        assert instance.validate() is True
        assert instance.execute() is True

        # Test process method if it exists
        if hasattr(instance, "process"):
            result = instance.process({"test": "data"})
            assert result is not None
            assert "processed" in result
