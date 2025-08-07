#!/usr/bin/env python3
"""
Tests for the code-writer agent functionality.
"""

import json
import unittest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "orchestrator"
sys.path.insert(0, str(src_path))

from code_writer_engine import CodeWriterEngine, generate_code_for_task
from run_agent import run_agent


class TestCodeWriterEngine(unittest.TestCase):
    """Test the core code writer engine functionality."""

    def setUp(self):
        self.engine = CodeWriterEngine()

    def test_engine_initialization(self):
        """Test that the engine initializes with proper patterns."""
        self.assertIsInstance(self.engine.language_patterns, dict)
        self.assertIn("python", self.engine.language_patterns)
        self.assertIn("javascript", self.engine.language_patterns)
        self.assertIn("typescript", self.engine.language_patterns)

    def test_language_detection(self):
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
            self.assertEqual(detected, expected_lang, f"Failed for: {description}")

    def test_code_type_detection(self):
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
            self.assertEqual(detected, expected_type, f"Failed for: {description}")

    def test_entity_extraction(self):
        """Test extraction of entities from task description."""
        task = "Create UserAuthentication class with login functionality"
        entities = self.engine._extract_entities(task)

        self.assertIn("UserAuthentication", entities)
        self.assertTrue(any("auth" in entity.lower() for entity in entities))

    def test_complexity_estimation(self):
        """Test complexity estimation."""
        test_cases = [
            ("create simple function", "low"),
            ("implement user service class", "medium"),
            ("build complex system architecture", "high"),
            ("add basic validation", "low"),
        ]

        for description, expected_complexity in test_cases:
            complexity = self.engine._estimate_code_complexity(description.lower())
            self.assertEqual(complexity, expected_complexity)

    def test_filename_suggestion(self):
        """Test filename generation."""
        test_cases = [
            ("Create user authentication", "python", "user_authentication.py"),
            ("Build API endpoint", "javascript", "api_endpoint.js"),
            ("Implement data model", "typescript", "data_model.ts"),
        ]

        for task, language, expected_pattern in test_cases:
            filename = self.engine._suggest_filename(task, language)
            self.assertTrue(
                filename.endswith(
                    self.engine.language_patterns[language]["extensions"][0]
                )
            )
            self.assertNotIn(" ", filename)  # No spaces in filename

    def test_dependency_suggestion(self):
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
            self.assertTrue(any(dep in deps for dep in expected_deps))

    def test_task_analysis(self):
        """Test complete task analysis."""
        task = "Create Python user authentication with password hashing"
        context = {"language": "python"}

        analysis = self.engine._analyze_code_task(task, context)

        self.assertEqual(analysis["original_task"], task)
        self.assertEqual(analysis["language"], "python")
        self.assertEqual(analysis["code_type"], "authentication")
        self.assertIn("complexity", analysis)
        self.assertIn("suggested_filename", analysis)
        self.assertIn("dependencies", analysis)


class TestCodeGeneration(unittest.TestCase):
    """Test code generation functionality."""

    def setUp(self):
        self.engine = CodeWriterEngine()

    def test_python_auth_code_generation(self):
        """Test Python authentication code generation."""
        task = "Create user authentication system"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        self.assertTrue(result["success"])
        self.assertIn("files", result)
        self.assertGreater(len(result["files"]), 0)

        # Check first file
        file_info = result["files"][0]
        self.assertIn("filename", file_info)
        self.assertIn("content", file_info)
        self.assertEqual(file_info["language"], "python")

        # Check that code contains authentication elements
        code = file_info["content"]
        self.assertIn("class", code)
        self.assertIn("def", code)
        self.assertIn("password", code.lower())

    def test_python_api_code_generation(self):
        """Test Python API code generation."""
        task = "Create REST API endpoints for users"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        self.assertTrue(result["success"])
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for API elements
        self.assertIn("FastAPI", code)
        self.assertIn("@app.get", code)
        self.assertIn("@app.post", code)
        self.assertIn("BaseModel", code)

    def test_generic_python_code_generation(self):
        """Test generic Python code generation."""
        task = "Create data processing handler"
        context = {"language": "python"}

        result = self.engine.generate_code(task, context)

        self.assertTrue(result["success"])
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for generic class structure
        self.assertIn("class", code)
        self.assertIn("def __init__", code)
        self.assertIn("def process", code)
        self.assertIn("typing", code)

    def test_javascript_code_generation(self):
        """Test JavaScript code generation."""
        task = "Create task handler service"
        context = {"language": "javascript"}

        result = self.engine.generate_code(task, context)

        self.assertTrue(result["success"])
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for JavaScript elements
        self.assertIn("class", code)
        self.assertIn("constructor", code)
        self.assertIn("async", code)
        self.assertIn("module.exports", code)


class TestCodeWriterIntegration(unittest.TestCase):
    """Test integration with orchestrator system."""

    def test_generate_code_for_task(self):
        """Test the main generation function."""
        task = "Create user authentication class"
        result = generate_code_for_task(task)

        self.assertTrue(result["success"])
        self.assertIn("files", result)
        self.assertIn("dependencies", result)
        self.assertIn("integration_notes", result)
        self.assertIn("metadata", result)

        # Check metadata structure
        metadata = result["metadata"]
        self.assertIn("generated_at", metadata)
        self.assertIn("language", metadata)
        self.assertIn("code_type", metadata)

    def test_run_agent_integration(self):
        """Test integration with run_agent system."""
        task = "Create simple API endpoint"
        result = run_agent("code-writer", task)

        self.assertTrue(result["success"])
        self.assertEqual(result["agent"], "code-writer")
        self.assertEqual(result["task"], task)
        self.assertEqual(result["returncode"], 0)

        # Check that stdout contains code generation summary
        stdout = result["stdout"]
        self.assertIn("Code Generation Results", stdout)
        self.assertIn("Task:", stdout)
        self.assertIn("Files Generated:", stdout)

        # Check metadata
        self.assertIn("metadata", result)
        self.assertIn("code_result", result["metadata"])

    def test_error_handling(self):
        """Test error handling in code generation."""
        # Test with empty task
        result = generate_code_for_task("")
        self.assertTrue(result["success"])  # Should handle empty gracefully

        # Test with valid task but expect no errors
        result = generate_code_for_task("Create test class")
        self.assertTrue(result["success"])

    def test_different_task_types(self):
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
            self.assertTrue(result["success"], f"Failed for task: {task}")
            self.assertGreater(
                len(result["files"]), 0, f"No files generated for: {task}"
            )


class TestCodeQuality(unittest.TestCase):
    """Test the quality of generated code."""

    def test_python_code_structure(self):
        """Test that generated Python code has proper structure."""
        task = "Create user management class"
        result = generate_code_for_task(task)

        self.assertTrue(result["success"])
        file_info = result["files"][0]
        code = file_info["content"]

        # Check for proper Python structure
        self.assertIn('"""', code)  # Docstrings
        self.assertIn("def __init__", code)  # Constructor
        self.assertIn("from typing", code)  # Type hints
        self.assertIn('if __name__ == "__main__":', code)  # Main block

        # Check for error handling
        self.assertIn("try:", code)
        self.assertIn("except", code)

    def test_code_documentation(self):
        """Test that generated code includes proper documentation."""
        task = "Create authentication handler"
        result = generate_code_for_task(task)

        file_info = result["files"][0]
        code = file_info["content"]

        # Check for documentation elements
        self.assertIn('"""', code)  # Module docstring
        self.assertIn("Args:", code)  # Function documentation
        self.assertIn("Returns:", code)  # Return documentation

        # Check for comments
        lines = code.split("\n")
        comment_lines = [line for line in lines if line.strip().startswith("#")]
        self.assertGreater(len(comment_lines), 0, "No comment lines found")

    def test_imports_and_dependencies(self):
        """Test that generated code has proper imports."""
        task = "Create authentication with secure password hashing"
        result = generate_code_for_task(task)

        # Check dependencies are suggested
        self.assertIn("hashlib", result["dependencies"])

        # Check code has proper imports
        file_info = result["files"][0]
        code = file_info["content"]
        self.assertIn("import", code)
        self.assertIn("from", code)

    def test_usage_examples(self):
        """Test that generated code includes usage examples."""
        task = "Create data processor"
        result = generate_code_for_task(task)

        self.assertTrue(result["usage_examples"])

        # Check that code includes example usage
        file_info = result["files"][0]
        code = file_info["content"]
        self.assertIn("main()", code)
        self.assertIn(
            "Example", code.split("def main()")[1] if "def main()" in code else code
        )


class TestMultiLanguageSupport(unittest.TestCase):
    """Test support for multiple programming languages."""

    def test_python_generation(self):
        """Test Python code generation."""
        task = "Create authentication system"
        context = {"language": "python"}

        result = generate_code_for_task(task, context)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["language"], "python")

        file_info = result["files"][0]
        self.assertTrue(file_info["filename"].endswith(".py"))
        self.assertIn("def", file_info["content"])

    def test_javascript_generation(self):
        """Test JavaScript code generation."""
        task = "Create task handler"
        context = {"language": "javascript"}

        result = generate_code_for_task(task, context)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["language"], "javascript")

        file_info = result["files"][0]
        self.assertTrue(file_info["filename"].endswith(".js"))
        self.assertIn("class", file_info["content"])
        self.assertIn("constructor", file_info["content"])

    def test_typescript_generation(self):
        """Test TypeScript code generation."""
        task = "Create service handler"
        context = {"language": "typescript"}

        result = generate_code_for_task(task, context)

        self.assertTrue(result["success"])
        # Should fall back to JavaScript generation currently
        file_info = result["files"][0]
        self.assertIn("class", file_info["content"])


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
