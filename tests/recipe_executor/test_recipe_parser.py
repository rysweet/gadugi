"""Comprehensive tests for recipe_parser.py."""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Generator

from src.recipe_executor.recipe_parser import RecipeParser, RecipeParseError
from src.recipe_executor.recipe_model import (
    ComponentType,
    RequirementPriority,
)


class TestRecipeParser:
    """Test RecipeParser class."""

    @pytest.fixture
    def parser(self) -> RecipeParser:
        """Create a RecipeParser instance."""
        return RecipeParser()

    @pytest.fixture
    def sample_recipe_dir(self) -> Generator[Path, None, None]:
        """Create a temporary recipe directory with sample files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "test-recipe"
            recipe_path.mkdir()

            # Create requirements.md
            requirements_content = """# Test Recipe Requirements

## Core Purpose
This is a test recipe for validation.

## Functional Requirements
- MUST parse recipe files correctly
- MUST validate input data
- SHOULD handle errors gracefully
- COULD optimize performance

## Non-Functional Requirements
- MUST be fast
- MUST be reliable
- SHOULD be maintainable

## Success Criteria
1. All tests pass
2. No errors in production
3. Performance meets targets
"""
            (recipe_path / "requirements.md").write_text(requirements_content)

            # Create design.md
            design_content = """# Test Recipe Design

## Architecture Overview
This follows a simple layered architecture.

## Core Components

### 1. Recipe Parser (`recipe_parser.py`)
```python
class RecipeParser:
    def parse(self, path: Path) -> Recipe:
        pass
```

### 2. Recipe Validator (`recipe_validator.py`)
Validates parsed recipes.

## Implementation
Implementation details here.
"""
            (recipe_path / "design.md").write_text(design_content)

            # Create components.json
            components_data = {
                "name": "test-recipe",
                "version": "1.0.0",
                "type": "library",
                "dependencies": ["base-recipe"],
                "description": "Test recipe",
                "metadata": {"test": True},
            }
            (recipe_path / "components.json").write_text(json.dumps(components_data))

            yield recipe_path

    def test_parse_recipe_success(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test successfully parsing a complete recipe."""
        recipe = parser.parse_recipe(sample_recipe_dir)

        assert recipe.name == "test-recipe"
        assert recipe.path == sample_recipe_dir
        assert recipe.components.version == "1.0.0"
        assert recipe.components.type == ComponentType.LIBRARY
        assert "base-recipe" in recipe.components.dependencies

    def test_parse_recipe_missing_path(self, parser: RecipeParser) -> None:
        """Test parsing with non-existent path."""
        with pytest.raises(RecipeParseError, match="Recipe path does not exist"):
            parser.parse_recipe(Path("/nonexistent/path"))

    def test_parse_recipe_missing_files(self, parser: RecipeParser) -> None:
        """Test parsing with missing required files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "incomplete"
            recipe_path.mkdir()

            # Only create requirements.md
            (recipe_path / "requirements.md").write_text("# Requirements")

            with pytest.raises(RecipeParseError, match="Required recipe file missing"):
                parser.parse_recipe(recipe_path)

    def test_parse_requirements(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test parsing requirements.md."""
        requirements = parser._parse_requirements(sample_recipe_dir / "requirements.md")

        assert requirements.purpose == "This is a test recipe for validation."
        assert len(requirements.functional_requirements) == 4
        assert len(requirements.non_functional_requirements) == 3
        assert len(requirements.success_criteria) == 3

        # Check MUST requirements
        must_reqs = [
            r
            for r in requirements.functional_requirements
            if r.priority == RequirementPriority.MUST
        ]
        assert len(must_reqs) == 2

    def test_parse_design(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test parsing design.md."""
        design = parser._parse_design(sample_recipe_dir / "design.md")

        assert "simple layered architecture" in design.architecture.lower()
        assert len(design.components) == 2
        assert design.components[0].name == "Recipe Parser"
        assert design.components[0].class_name == "RecipeParser"
        assert len(design.code_blocks) == 1

    def test_parse_components(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test parsing components.json."""
        components = parser._parse_components(sample_recipe_dir / "components.json")

        assert components.name == "test-recipe"
        assert components.version == "1.0.0"
        assert components.type == ComponentType.LIBRARY
        assert components.dependencies == ["base-recipe"]
        assert components.metadata["test"] is True

    def test_parse_components_invalid_json(self, parser: RecipeParser) -> None:
        """Test parsing invalid JSON in components.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            components_path = Path(tmpdir) / "components.json"
            components_path.write_text("{ invalid json")

            with pytest.raises(RecipeParseError, match="Invalid JSON"):
                parser._parse_components(components_path)

    def test_extract_purpose(self, parser: RecipeParser) -> None:
        """Test extracting purpose from requirements."""
        # Test with Core Purpose section
        content = """## Core Purpose
This is the purpose.

## Other Section
Other content."""
        purpose = parser._extract_purpose(content)
        assert purpose == "This is the purpose."

        # Test with Purpose section
        content = """# Purpose
Another purpose statement."""
        purpose = parser._extract_purpose(content)
        assert purpose == "Another purpose statement."

        # Test fallback to first paragraph
        content = """This is the first line.
More content here."""
        purpose = parser._extract_purpose(content)
        assert purpose == "This is the first line."

    def test_extract_requirements(self, parser: RecipeParser) -> None:
        """Test extracting requirements from a section."""
        content = """## Functional Requirements
- MUST implement feature A
- MUST implement feature B
- SHOULD add feature C
- COULD optimize feature D

## Non-Functional Requirements
- MUST be secure"""

        functional = parser._extract_requirements(content, "Functional Requirements")
        assert len(functional) == 4

        must_reqs = [r for r in functional if r.priority == RequirementPriority.MUST]
        assert len(must_reqs) == 2

        should_reqs = [r for r in functional if r.priority == RequirementPriority.SHOULD]
        assert len(should_reqs) == 1

    def test_extract_success_criteria(self, parser: RecipeParser) -> None:
        """Test extracting success criteria."""
        content = """## Success Criteria
1. All tests pass
2. Performance targets met
- Documentation complete
* No critical bugs

## Other Section"""

        criteria = parser._extract_success_criteria(content)
        assert len(criteria) == 4
        assert "All tests pass" in criteria
        assert "Documentation complete" in criteria

    def test_validate_recipe(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test recipe validation."""
        recipe = parser.parse_recipe(sample_recipe_dir)
        issues = parser.validate_recipe(recipe)

        # Should have no issues for valid recipe
        assert len(issues) == 0

    def test_validate_recipe_with_issues(self, parser: RecipeParser) -> None:
        """Test validation with problematic recipe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recipe_path = Path(tmpdir) / "bad-recipe"
            recipe_path.mkdir()

            # Create minimal files
            (recipe_path / "requirements.md").write_text("# Empty")
            (recipe_path / "design.md").write_text("# Empty")
            components = {
                "name": "bad-recipe",
                "version": "1.0.0",
                "type": "library",
                "dependencies": ["bad-recipe"],  # Self-dependency
            }
            (recipe_path / "components.json").write_text(json.dumps(components))

            recipe = parser.parse_recipe(recipe_path)
            issues = parser.validate_recipe(recipe)

            assert len(issues) > 0
            assert any("depends on itself" in issue for issue in issues)
            assert any("No requirements defined" in issue for issue in issues)

    def test_calculate_recipe_checksum(self, parser: RecipeParser, sample_recipe_dir: Path) -> None:
        """Test checksum calculation."""
        checksum1 = parser._calculate_recipe_checksum(sample_recipe_dir)
        assert checksum1 is not None
        assert len(checksum1) == 64  # SHA256 hex length

        # Checksum should be consistent
        checksum2 = parser._calculate_recipe_checksum(sample_recipe_dir)
        assert checksum1 == checksum2

        # Modify a file and check checksum changes
        (sample_recipe_dir / "requirements.md").write_text("# Modified")
        checksum3 = parser._calculate_recipe_checksum(sample_recipe_dir)
        assert checksum3 != checksum1

    def test_extract_component_designs(self, parser: RecipeParser) -> None:
        """Test extracting component designs from markdown."""
        content = """## Components

### 1. Parser Component (`parser.py`)
This component parses files.

```python
class Parser:
    def parse(self): pass
```

### 2. Generator (`generator.py`)
Generates output.
"""
        components = parser._extract_component_designs(content)
        assert len(components) == 2
        assert components[0].name == "Parser Component"
        assert components[0].class_name == "Parser"
        assert components[1].name == "Generator"

    def test_requirement_pattern_matching(self, parser: RecipeParser) -> None:
        """Test requirement pattern matching."""
        # Test MUST pattern
        assert parser.requirement_pattern.search("- MUST do something")
        assert parser.requirement_pattern.search("* MUST handle errors")

        # Test SHOULD pattern
        assert parser.should_pattern.search("- SHOULD optimize")

        # Test COULD pattern
        assert parser.could_pattern.search("- COULD add feature")

    def test_code_block_extraction(self, parser: RecipeParser) -> None:
        """Test extracting code blocks from markdown."""
        content = """Some text

```python
def hello():
    print("world")
```

More text

```py
class Test:
    pass
```

Even more text

```
plain code block
```
"""
        blocks = parser.code_block_pattern.findall(content)
        # The regex also matches empty language specifier
        python_blocks = [b for b in blocks if "def hello():" in b or "class Test:" in b]
        assert len(python_blocks) == 2  # Only python blocks
        assert "def hello():" in blocks[0]
        assert "class Test:" in blocks[1]
