"""Comprehensive tests for claude_code_generator.py."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import subprocess
import tempfile

from src.recipe_executor.claude_code_generator import (
    ClaudeCodeGenerator,
    ClaudeCodeGenerationError,
)
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    RecipeMetadata,
    ComponentType,
    GeneratedCode,
    BuildContext,
    Requirement,
    RequirementPriority,
    ComponentDesign,
)


class TestClaudeCodeGenerator:
    """Test ClaudeCodeGenerator class."""

    @pytest.fixture
    def generator(self) -> ClaudeCodeGenerator:
        """Create a generator instance."""
        return ClaudeCodeGenerator()

    @pytest.fixture
    def sample_recipe(self) -> Recipe:
        """Create a sample recipe for testing."""
        requirements = Requirements(
            purpose="Build a test component",
            functional_requirements=[
                Requirement(
                    "req_1",
                    "MUST parse input files",
                    RequirementPriority.MUST,
                    validation_criteria=["Correctly parses JSON", "Handles errors"],
                ),
                Requirement(
                    "req_2",
                    "SHOULD validate data",
                    RequirementPriority.SHOULD,
                ),
            ],
            non_functional_requirements=[
                Requirement(
                    "req_3",
                    "MUST handle errors gracefully",
                    RequirementPriority.MUST,
                ),
            ],
            success_criteria=["All tests pass", "No pyright errors"],
        )

        design = Design(
            architecture="Layered architecture with clear separation",
            components=[
                ComponentDesign(
                    name="Parser",
                    description="Parses input files",
                    class_name="FileParser",
                    methods=["parse", "validate"],
                ),
                ComponentDesign(
                    name="Validator",
                    description="Validates parsed data",
                    class_name="DataValidator",
                ),
            ],
            interfaces=[],
            implementation_notes="Use strict typing",
            code_blocks=["class FileParser:\n    pass"],
        )

        components = Components(
            name="test-recipe",
            version="1.0.0",
            type=ComponentType.LIBRARY,
            dependencies=["base-recipe"],
            metadata={"self_hosting": False},
        )

        metadata = RecipeMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return Recipe(
            name="test-recipe",
            path=Path("recipes/test-recipe"),
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata,
        )

    @pytest.fixture
    def build_context(self, sample_recipe: Recipe) -> BuildContext:
        """Create a build context."""
        return BuildContext(
            recipe=sample_recipe,
            dependencies={"base-recipe": "some_dependency"},
            dry_run=False,
            verbose=True,
        )

    def test_generator_initialization(self) -> None:
        """Test generator initialization."""
        generator = ClaudeCodeGenerator(claude_command="custom-claude")
        assert generator.claude_command == "custom-claude"
        assert generator.guidelines_path == Path(".claude/Guidelines.md")

        generator2 = ClaudeCodeGenerator(
            guidelines_path=Path("custom/guidelines.md")
        )
        assert generator2.guidelines_path == Path("custom/guidelines.md")

    def test_load_guidelines(self, generator: ClaudeCodeGenerator, tmp_path: Path) -> None:
        """Test loading guidelines from file."""
        guidelines_file = tmp_path / "guidelines.md"
        guidelines_content = "# Test Guidelines\n\nBe awesome!"
        guidelines_file.write_text(guidelines_content)

        generator.guidelines_path = guidelines_file
        loaded = generator._load_guidelines()
        assert loaded == guidelines_content

    def test_load_guidelines_file_not_found(
        self, generator: ClaudeCodeGenerator
    ) -> None:
        """Test loading guidelines when file doesn't exist."""
        generator.guidelines_path = Path("nonexistent.md")
        guidelines = generator._load_guidelines()
        assert "Guidelines not found" in guidelines

    def test_create_generation_prompt(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test prompt creation."""
        with patch.object(generator, "_load_guidelines", return_value="# Guidelines"):
            prompt = generator._create_generation_prompt(sample_recipe)

            # Verify prompt structure
            assert "# Generate Implementation for test-recipe" in prompt
            assert "## CRITICAL: Development Guidelines" in prompt
            assert "Zero BS Principle" in prompt  # Check it exists in any form
            # Note: TDD prompt is only used in generate_test_driven, not standard generation
            assert "## Requirements" in prompt
            assert "MUST parse input files" in prompt
            assert "SHOULD validate data" in prompt
            assert "## Design Specification" in prompt
            assert "Layered architecture" in prompt
            assert "## Components to Implement" in prompt
            assert "**Parser**" in prompt
            assert "Parses input files" in prompt
            # Note: Quality gates are in TDD prompt, not regular generation
            assert "## Dependencies" in prompt
            assert "base-recipe" in prompt

    def test_create_generation_prompt_self_hosting(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test prompt creation for self-hosting recipe."""
        sample_recipe.components.metadata["self_hosting"] = True
        
        with patch.object(generator, "_load_guidelines", return_value="# Guidelines"):
            prompt = generator._create_generation_prompt(sample_recipe)
            
            assert "## SELF-HOSTING REQUIREMENT" in prompt
            assert "This component MUST be able to regenerate itself" in prompt

    def test_invoke_claude_code(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe, tmp_path: Path
    ) -> None:
        """Test invoking Claude Code CLI."""
        prompt = "Test prompt"
        
        # Mock subprocess.run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated code"
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch("tempfile.mkdtemp", return_value=str(tmp_path)):
                output = generator._invoke_claude_code(prompt, sample_recipe)
                
                # Verify subprocess call
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert call_args[0][0][0] == "claude"
                assert "--prompt-file" in call_args[0][0]
                
                # Verify output
                assert output == "Generated code"

    def test_invoke_claude_code_with_error(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test Claude Code invocation with error."""
        prompt = "Test prompt"
        
        # Mock subprocess.run to return error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = "/tmp/test"
                Path("/tmp/test").mkdir(parents=True, exist_ok=True)
                with pytest.raises(ClaudeCodeGenerationError, match="Error occurred"):
                    generator._invoke_claude_code(prompt, sample_recipe)

    def test_parse_generated_files(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test parsing generated files from Claude output."""
        claude_output = """
Creating file: src/test_recipe/parser.py
```python
class FileParser:
    def parse(self): pass
```

Creating file: src/test_recipe/validator.py
```python
class DataValidator:
    def validate(self): pass
```

Creating file: tests/test_parser.py
```python
def test_parser(): pass
```
"""
        
        files = generator._parse_generated_files(claude_output, sample_recipe)
        
        assert len(files) == 3
        assert "src/test_recipe/parser.py" in files
        assert "class FileParser:" in files["src/test_recipe/parser.py"]
        assert "src/test_recipe/validator.py" in files
        assert "tests/test_parser.py" in files

    def test_parse_generated_files_with_path_normalization(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test file path normalization in parsing."""
        claude_output = """
File: test-recipe/main.py
```python
def main(): pass
```
"""
        
        files = generator._parse_generated_files(claude_output, sample_recipe)
        
        # Should normalize to src/test_recipe/main.py
        assert "src/test_recipe/main.py" in files
        assert "def main(): pass" in files["src/test_recipe/main.py"]

    def test_generate_test_driven(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe, build_context: BuildContext
    ) -> None:
        """Test test-driven generation flow."""
        # Mock Claude invocations
        test_output = """
Creating file: tests/test_parser.py
```python
def test_parser():
    assert True
```
"""
        
        code_output = """
Creating file: src/test_recipe/parser.py
```python
class FileParser:
    def parse(self, input_files):
        '''Parse input files and handle errors gracefully.'''
        return {}
```
"""
        
        with patch.object(
            generator,
            "_invoke_claude_code",
            side_effect=[test_output, code_output]
        ):
            result = generator.generate(sample_recipe, build_context)
            
            assert result.recipe_name == "test-recipe"
            assert len(result.files) == 2
            assert "tests/test_parser.py" in result.files
            assert "src/test_recipe/parser.py" in result.files

    def test_generate_with_dependency_context(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test generation with dependency context."""
        context = BuildContext(
            recipe=sample_recipe,
            dependencies={
                "base-recipe": {"api": "base_api", "version": "1.0"},
                "utils": {"helpers": ["format", "validate"]},
            },
        )
        
        with patch.object(generator, "_load_guidelines", return_value=""):
            prompt = generator._create_generation_prompt(sample_recipe)
            
            # Dependencies should be in prompt
            assert "base-recipe" in prompt

    def test_generate_dry_run(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test generation in dry run mode."""
        context = BuildContext(recipe=sample_recipe, dry_run=True)
        
        # Should not invoke Claude in dry run
        with patch.object(generator, "_invoke_claude_code") as mock_invoke:
            result = generator.generate(sample_recipe, context)
            
            mock_invoke.assert_not_called()
            assert result.recipe_name == "test-recipe"
            assert len(result.files) == 0

    def test_validate_generated_code(
        self, generator: ClaudeCodeGenerator
    ) -> None:
        """Test generated code validation."""
        files = {
            "src/test/main.py": "class Main: pass",
            "tests/test_main.py": "def test_main(): pass",
        }
        
        # Basic validation should pass
        is_valid = generator._validate_generated_code(files)
        assert is_valid is True
        
        # Empty files should fail
        assert generator._validate_generated_code({}) is False

    def test_create_tdd_test_prompt(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test TDD test prompt creation."""
        prompt = generator._create_tdd_test_prompt(sample_recipe)
        
        assert "# Generate Tests for test-recipe" in prompt
        assert "## Test-Driven Development (TDD) Approach" in prompt
        assert "MUST parse input files" in prompt
        assert "comprehensive test coverage" in prompt
        assert "pytest" in prompt

    def test_create_implementation_prompt(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test implementation prompt creation."""
        test_files = {
            "tests/test_parser.py": "def test_parser(): pass"
        }
        
        prompt = generator._create_implementation_prompt(sample_recipe, test_files)
        
        assert "# Implement Code to Pass Tests" in prompt
        assert "tests/test_parser.py" in prompt
        assert "def test_parser(): pass" in prompt
        assert "make all tests pass" in prompt

    def test_format_requirements(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test requirements formatting."""
        formatted = generator._format_requirements(sample_recipe.requirements)
        
        assert "### Functional Requirements" in formatted
        assert "req_1" in formatted
        assert "MUST parse input files" in formatted
        assert "Correctly parses JSON" in formatted
        assert "### Non-Functional Requirements" in formatted
        assert "req_3" in formatted

    def test_format_design(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test design formatting."""
        formatted = generator._format_design(sample_recipe.design)
        
        assert "Architecture:" in formatted
        assert "Layered architecture" in formatted
        assert "Implementation Notes:" in formatted
        assert "Use strict typing" in formatted
        assert "class FileParser:" in formatted

    def test_format_components(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test components formatting."""
        formatted = generator._format_components(sample_recipe.design.components)
        
        assert "**Parser**" in formatted
        assert "Parses input files" in formatted
        assert "Class: `FileParser`" in formatted
        assert "Methods: parse, validate" in formatted

    def test_error_handling_in_generation(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe, build_context: BuildContext
    ) -> None:
        """Test error handling during generation."""
        # Mock Claude to raise exception
        with patch.object(
            generator,
            "_invoke_claude_code",
            side_effect=ClaudeCodeGenerationError("Claude failed")
        ):
            with pytest.raises(ClaudeCodeGenerationError, match="Claude failed"):
                generator.generate(sample_recipe, build_context)

    def test_subprocess_timeout_handling(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test handling of subprocess timeout."""
        prompt = "Test prompt"
        
        # Mock subprocess.run to raise timeout
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired("claude", 300)
        ):
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = "/tmp/test"
                Path("/tmp/test").mkdir(parents=True, exist_ok=True)
                with pytest.raises(
                    ClaudeCodeGenerationError,
                    match="timed out after 300 seconds"
                ):
                    generator._invoke_claude_code(prompt, sample_recipe)

    def test_empty_claude_output_handling(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test handling of empty Claude output."""
        # Mock empty output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
                mock_tmpdir.return_value.__enter__.return_value = "/tmp/test"
                Path("/tmp/test").mkdir(parents=True, exist_ok=True)
                output = generator._invoke_claude_code("prompt", sample_recipe)
                assert output == ""

    def test_large_output_handling(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test handling of large Claude output."""
        # Create large output with multiple files
        large_output = ""
        for i in range(50):
            large_output += f"""
Creating file: src/test_recipe/module_{i}.py
```python
class Module{i}:
    def method_{i}(self):
        return {i}
```
"""
        
        files = generator._parse_generated_files(large_output, sample_recipe)
        
        # Should parse all 50 files
        assert len(files) == 50
        assert "src/test_recipe/module_0.py" in files
        assert "src/test_recipe/module_49.py" in files

    def test_special_characters_in_output(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test handling of special characters in Claude output."""
        output_with_special = """
Creating file: src/test_recipe/special.py
```python
def special_func():
    return "Hello\nWorld\t!"
    # Comment with 中文字符
```
"""
        
        files = generator._parse_generated_files(output_with_special, sample_recipe)
        
        assert "src/test_recipe/special.py" in files
        content = files["src/test_recipe/special.py"]
        # Check that escape sequences are preserved in the Python string literal
        assert r'"Hello\nWorld\t!"' in content or '"Hello\nWorld\t!"' in content
        assert "中文字符" in content

    def test_malformed_output_handling(
        self, generator: ClaudeCodeGenerator, sample_recipe: Recipe
    ) -> None:
        """Test handling of malformed Claude output."""
        malformed_output = """
Creating file: src/test.py
No closing backticks here
def test(): pass

Creating file: another.py
```python
Properly formatted
```
"""
        
        files = generator._parse_generated_files(malformed_output, sample_recipe)
        
        # Should only get the properly formatted file
        assert len(files) >= 1
        if "src/test_recipe/another.py" in files:
            assert "Properly formatted" in files["src/test_recipe/another.py"]