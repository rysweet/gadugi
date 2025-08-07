#!/usr/bin/env python3
"""Tests for the code-writer agent functionality."""

import sys
import unittest
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(src_path))

from code_writer_engine import CodeWriterEngine, generate_code_for_task  # noqa: E402
from run_agent import run_agent  # noqa: E402


class TestCodeWriterEngine(unittest.TestCase):
    """Test the core code writer engine functionality."""

    def setUp(self) -> None:
        self.engine = CodeWriterEngine()

    def test_engine_initialization(self) -> None:
        """Test that the engine initializes with proper patterns."""
        assert isinstance(self.engine.language_patterns, dict)
        assert "python" in self.engine.language_patterns
        assert "javascript" in self.engine.language_patterns
        assert "typescript" in self.engine.language_patterns

    def test_language_detection(self) -> None:
        """Test programming language detection."""
        test_cases = [
            ("create python authentication", "python"),
            ("build flask api", "python"),
            ("implement javascript function", "javascript"),
            ("add react component", "javascript"),
            ("create typescript interface", "typescript"),
            ("generic programming task", "python"),  # Default
        ]

        for description, expected_lang in test_cases:
            detected = self.engine._detect_language(description.lower())
            assert detected == expected_lang, f"Failed for: {description}"

    def test_code_type_detection(self) -> None:
        """Test code type classification."""
        test_cases = [
            ("create user authentication", "authentication"),
            ("build rest api endpoint", "api_endpoint"),
            ("create data model", "data_model"),
            ("write unit tests", "test_class"),
            ("implement service class", "service_class"),
            ("create react component", "component"),
            ("generic task", "general_class"),
        ]

        for description, expected_type in test_cases:
            detected = self.engine._determine_code_type(description.lower())
            assert detected == expected_type, f"Failed for: {description}"

    def test_entity_extraction(self) -> None:
        """Test extraction of entities from task description."""
        task = "Create UserAuthentication class with login functionality"
        entities = self.engine._extract_entities(task)

        assert "UserAuthentication" in entities
        assert any("auth" in entity.lower() for entity in entities)

    def test_complexity_estimation(self) -> None:
        """Test complexity estimation."""
        test_cases = [
            ("create simple function", "low"),
            ("implement user service class", "medium"),
            ("build complex system architecture", "high"),
            ("add basic validation", "low"),
        ]

        for description, expected_complexity in test_cases:
            complexity = self.engine._estimate_code_complexity(description.lower())
            assert complexity == expected_complexity

    def test_filename_suggestion(self) -> None:
        """Test filename generation."""
        test_cases = [
            ("Create user authentication", "python", "user_authentication.py"),
            ("Build API endpoint", "javascript", "api_endpoint.js"),
            ("Implement data model", "typescript", "data_model.ts"),
        ]

        for task, language, _expected_pattern in test_cases:
            filename = self.engine._suggest_filename(task, language)
            assert filename.endswith(self.engine.language_patterns[language]["extensions"][0])
            assert " " not in filename  # No spaces in filename

    def test_dependency_suggestion(self) -> None:
        """Test dependency suggestion based on task description."""
        test_cases = [
            (
                "create authentication with password hashing",
                "python",
                ["hashlib", "secrets"],
            ),
            ("build rest api", "python", ["fastapi", "requests"]),
            ("create database model", "python", ["sqlalchemy", "sqlite3"]),
            ("add unit tests", "python", ["unittest", "pytest"]),
        ]

        for description, language, expected_deps in test_cases:
            deps = self.engine._suggest_dependencies(description, language)
            # Check that at least some expected dependencies are present
            assert any(dep in deps for dep in expected_deps)

    def test_task_analysis(self) -> None:
        """Test complete task analysis."""
        task = "Create Python user authentication with password hashing"
        context = {"language": "python"}

        analysis = self.engine._analyze_code_task(task, context)

        assert analysis["original_task"] == task
        assert analysis["language"] == "python"
        assert analysis["code_type"] == "authentication"
        assert "complexity" in analysis
        assert "suggested_filename" in analysis
        assert "dependencies" in analysis


class TestCodeGeneration(unittest.TestCase):
    """Test code generation functionality."""

    def setUp(self) -> None:
        self.engine = CodeWriterEngine()

    def test_python_auth_code_generation(self) -> None:
        """Test Python authentication code generation."""
        task = "Create user authentication system"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        assert result["success"]
        assert "files" in result
        assert len(result["files"]) > 0

        # Check first file
        file_info = result["files"][0]
        assert "filename" in file_info
        assert "content" in file_info
        assert file_info["language"] == "python"

        # Check that code contains authentication elements
        code = file_info["content"]
        assert "class" in code
        assert "def" in code
        assert "password" in code.lower()

    def test_python_api_code_generation(self) -> None:
        """Test Python API code generation."""
        task = "Create REST API endpoints for users"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        assert result["success"]
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for API elements
        assert "FastAPI" in code
        assert "@app.get" in code
        assert "@app.post" in code
        assert "BaseModel" in code

    def test_generic_python_code_generation(self) -> None:
        """Test generic Python code generation."""
        task = "Create data processing handler"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        assert result["success"]
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for generic class structure
        assert "class" in code
        assert "def __init__" in code
        assert "def process" in code
        assert "typing" in code

    def test_javascript_code_generation(self) -> None:
        """Test JavaScript code generation."""
        task = "Create task handler service"
        context = {"language": "javascript"}

        result = self.engine.generate_code(task, context)

        assert result["success"]
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for JavaScript elements
        assert "class" in code
        assert "constructor" in code
        assert "async" in code
        assert "module.exports" in code


class TestCodeWriterIntegration(unittest.TestCase):
    """Test integration with orchestrator system."""

    def test_generate_code_for_task(self) -> None:
        """Test the main generation function."""
        task = "Create user authentication class"
        result = generate_code_for_task(task)

        assert result["success"]
        assert "files" in result
        assert "dependencies" in result
        assert "integration_notes" in result
        assert "metadata" in result

        # Check metadata structure
        metadata = result["metadata"]
        assert "generated_at" in metadata
        assert "language" in metadata
        assert "code_type" in metadata

    def test_run_agent_integration(self) -> None:
        """Test integration with run_agent system."""
        task = "Create simple API endpoint"
        result = run_agent("code-writer", task)

        assert result["success"]
        assert result["agent"] == "code-writer"
        assert result["task"] == task
        assert result["returncode"] == 0

        # Check that stdout contains code generation summary
        stdout = result["stdout"]
        assert "Code Generation Results" in stdout
        assert "Task:" in stdout
        assert "Files Generated:" in stdout

        # Check metadata
        assert "metadata" in result
        assert "code_result" in result["metadata"]

    def test_error_handling(self) -> None:
        """Test error handling in code generation."""
        # Test with empty task
        result = generate_code_for_task("")
        assert result["success"]  # Should handle empty gracefully

        # Test with valid task but expect no errors
        result = generate_code_for_task("Create test class")
        assert result["success"]

    def test_different_task_types(self) -> None:
        """Test code generation for different task types."""
        test_tasks = [
            "Create user authentication system",
            "Build REST API endpoints",
            "Implement data models",
            "Add unit tests",
            "Create service class",
        ]

        for task in test_tasks:
            result = generate_code_for_task(task)
            assert result["success"], f"Failed for task: {task}"
            assert len(result["files"]) > 0, f"No files generated for: {task}"


class TestCodeQuality(unittest.TestCase):
    """Test the quality of generated code."""

    def test_python_code_structure(self) -> None:
        """Test that generated Python code has proper structure."""
        task = "Create user management class"
        result = generate_code_for_task(task)

        assert result["success"]
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for proper Python structure
        assert '"""' in code  # Docstrings
        assert "def __init__" in code  # Constructor
        assert "from typing" in code  # Type hints
        assert 'if __name__ == "__main__":' in code  # Main block

        # Check for error handling
        assert "try:" in code
        assert "except" in code

    def test_code_documentation(self) -> None:
        """Test that generated code includes proper documentation."""
        task = "Create authentication handler"
        result = generate_code_for_task(task)

        file_info = result["files"][0]
        code = file_info["content"]

        # Check for documentation elements
        assert '"""' in code  # Module docstring
        assert "Args:" in code  # Function documentation
        assert "Returns:" in code  # Return documentation

        # Check for comments
        lines = code.split("\n")
        comment_lines = [line for line in lines if line.strip().startswith("#")]
        assert len(comment_lines) > 0, "No comment lines found"

    def test_imports_and_dependencies(self) -> None:
        """Test that generated code has proper imports."""
        task = "Create authentication with secure password hashing"
        result = generate_code_for_task(task)

        # Check dependencies are suggested
        assert "hashlib" in result["dependencies"]

        # Check code has proper imports
        file_info = result["files"][0]
        code = file_info["content"]
        assert "import" in code
        assert "from" in code

    def test_usage_examples(self) -> None:
        """Test that generated code includes usage examples."""
        task = "Create data processor"
        result = generate_code_for_task(task)

        assert result["usage_examples"]

        # Check that code includes example usage
        file_info = result["files"][0]
        code = file_info["content"]
        assert "main()" in code
        assert "Example" in (code.split("def main()")[1] if "def main()" in code else code)


class TestMultiLanguageSupport(unittest.TestCase):
    """Test support for multiple programming languages."""

    def test_python_generation(self) -> None:
        """Test Python code generation."""
        task = "Create authentication system"
        context = {"language": "python"}

        result = generate_code_for_task(task, context)

        assert result["success"]
        assert result["metadata"]["language"] == "python"

        file_info = result["files"][0]
        assert file_info["filename"].endswith(".py")
        assert "def" in file_info["content"]

    def test_javascript_generation(self) -> None:
        """Test JavaScript code generation."""
        task = "Create task handler"
        context = {"language": "javascript"}

        result = generate_code_for_task(task, context)

        assert result["success"]
        assert result["metadata"]["language"] == "javascript"

        file_info = result["files"][0]
        assert file_info["filename"].endswith(".js")
        assert "class" in file_info["content"]
        assert "constructor" in file_info["content"]

    def test_typescript_generation(self) -> None:
        """Test TypeScript code generation."""
        task = "Create service handler"
        context = {"language": "typescript"}

        result = generate_code_for_task(task, context)

        assert result["success"]
        # Should fall back to JavaScript generation currently
        file_info = result["files"][0]
        assert "class" in file_info["content"]


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
