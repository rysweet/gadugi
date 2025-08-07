#!/usr/bin/env python3
"""
Tests for Agent Generator Engine
"""

import unittest
import json
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from agent_generator_engine import (
    AgentGeneratorEngine,
    AgentSpecification,
    TemplateOptions,
    GenerationOptions,
    AgentType,
    TemplateType,
    AgentGeneratorResponse,
    GeneratedFile,
    IntegrationPoint,
    ValidationResult,
    Recommendation,
)


class TestAgentGeneratorEngine(unittest.TestCase):
    """Test cases for Agent Generator Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = AgentGeneratorEngine()

        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = os.path.join(self.temp_dir, "test_agents")
        os.makedirs(self.test_output_dir, exist_ok=True)

        # Sample agent specification
        self.test_spec = AgentSpecification(
            name="test-agent",
            type=AgentType.SPECIALIZED,
            description="A test agent for unit testing",
            capabilities=["data_processing", "validation", "reporting"],
            interfaces={"input_format": "json", "output_format": "json"},
            requirements={"memory_limit": "256MB", "dependencies": ["requests"]},
        )

        # Sample template options
        self.test_template_options = TemplateOptions(
            base_template=TemplateType.STANDARD,
            include_tests=True,
            include_documentation=True,
        )

        # Sample generation options
        self.test_generation_options = GenerationOptions(
            output_directory=self.test_output_dir,
            overwrite_existing=True,
            validate_before_creation=True,
            auto_register=True,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_engine_initialization(self):
        """Test engine initializes properly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)
        self.assertIsNotNone(self.engine.templates)
        self.assertIn("standard", self.engine.templates)
        self.assertIn("minimal", self.engine.templates)
        self.assertIn("advanced", self.engine.templates)

    def test_template_loading(self):
        """Test that templates are loaded correctly."""
        templates = self.engine.templates

        # Check all required templates exist
        required_templates = ["standard", "minimal", "advanced"]
        for template_name in required_templates:
            self.assertIn(template_name, templates)
            self.assertIsInstance(templates[template_name], str)
            self.assertGreater(len(templates[template_name]), 100)

    def test_agent_specification_validation_valid(self):
        """Test validation of valid agent specification."""
        result = self.engine._validate_specification(self.test_spec)

        self.assertEqual(result.syntax_check, "passed")
        self.assertEqual(result.interface_validation, "passed")
        self.assertEqual(result.dependency_check, "passed")
        self.assertEqual(result.integration_test, "passed")

    def test_agent_specification_validation_invalid_name(self):
        """Test validation rejects invalid agent names."""
        invalid_spec = AgentSpecification(
            name="Invalid Agent Name!",  # Invalid characters
            type=AgentType.SPECIALIZED,
            description="Test description",
            capabilities=["test"],
            interfaces={},
            requirements={},
        )

        result = self.engine._validate_specification(invalid_spec)
        self.assertEqual(result.syntax_check, "failed")

    def test_agent_specification_validation_no_capabilities(self):
        """Test validation rejects specs with no capabilities."""
        invalid_spec = AgentSpecification(
            name="test-agent",
            type=AgentType.SPECIALIZED,
            description="Test description",
            capabilities=[],  # Empty capabilities
            interfaces={},
            requirements={},
        )

        result = self.engine._validate_specification(invalid_spec)
        self.assertEqual(result.syntax_check, "failed")

    def test_directory_creation(self):
        """Test directory creation utility."""
        test_dir = Path(self.temp_dir) / "new_directory"
        self.assertFalse(test_dir.exists())

        self.engine._ensure_directory(test_dir)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())

    def test_agent_file_generation(self):
        """Test generation of agent specification file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check file was generated
        self.assertIsInstance(generated_file, GeneratedFile)
        self.assertEqual(generated_file.type, "agent")
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("test-agent", content.lower())
        self.assertIn("data_processing", content)
        self.assertIn("validation", content)
        self.assertIn("reporting", content)

    def test_engine_file_generation_standard_template(self):
        """Test generation of engine file with standard template."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec, self.test_template_options, output_dir
        )

        # Check file was generated
        self.assertIsInstance(generated_file, GeneratedFile)
        self.assertEqual(generated_file.type, "engine")
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("class TestAgentEngine:", content)
        self.assertIn("def execute_operation", content)
        self.assertIn("_handle_data_processing", content)
        self.assertIn("_handle_validation", content)
        self.assertIn("_handle_reporting", content)

    def test_engine_file_generation_minimal_template(self):
        """Test generation of engine file with minimal template."""
        minimal_options = TemplateOptions(
            base_template=TemplateType.MINIMAL,
            include_tests=False,
            include_documentation=False,
        )

        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec, minimal_options, output_dir
        )

        # Check file was generated
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content is minimal
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("class TestAgent:", content)
        self.assertIn("def process", content)
        self.assertNotIn("async def", content)  # No async in minimal

    def test_engine_file_generation_advanced_template(self):
        """Test generation of engine file with advanced template."""
        advanced_options = TemplateOptions(
            base_template=TemplateType.ADVANCED,
            include_tests=True,
            include_documentation=True,
        )

        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec, advanced_options, output_dir
        )

        # Check file was generated
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content has advanced features
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("async def execute_operation_async", content)
        self.assertIn("PerformanceMetrics", content)
        self.assertIn("cache", content)
        self.assertIn("TestAgentManager", content)

    def test_test_file_generation(self):
        """Test generation of test file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_test_file(self.test_spec, output_dir)

        # Check file was generated
        self.assertIsInstance(generated_file, GeneratedFile)
        self.assertEqual(generated_file.type, "test")
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("class TestTestAgentEngine(unittest.TestCase):", content)
        self.assertIn("def test_engine_initialization", content)
        self.assertIn("def test_basic_operation", content)
        self.assertIn("from test_agent_engine import", content)

    def test_readme_file_generation(self):
        """Test generation of README file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_readme_file(self.test_spec, output_dir)

        # Check file was generated
        self.assertIsInstance(generated_file, GeneratedFile)
        self.assertEqual(generated_file.type, "documentation")
        self.assertTrue(os.path.exists(generated_file.path))

        # Check file content
        with open(generated_file.path, "r") as f:
            content = f.read()

        self.assertIn("# Test Agent", content)
        self.assertIn("## Overview", content)
        self.assertIn("## Capabilities", content)
        self.assertIn("data_processing", content)
        self.assertIn("validation", content)
        self.assertIn("reporting", content)

    def test_initialization_code_generation(self):
        """Test generation of initialization code."""
        spec_with_features = AgentSpecification(
            name="feature-agent",
            type=AgentType.SPECIALIZED,
            description="Agent with special features",
            capabilities=["caching", "monitoring", "state_management"],
            interfaces={},
            requirements={},
        )

        init_code = self.engine._generate_initialization_code(spec_with_features)

        self.assertIn("self.cache = {}", init_code)
        self.assertIn("self.metrics = {}", init_code)
        self.assertIn("self.state = {}", init_code)

    def test_operation_routing_generation(self):
        """Test generation of operation routing logic."""
        routing_code = self.engine._generate_operation_routing(self.test_spec)

        self.assertIn('if request.operation == "data_processing":', routing_code)
        self.assertIn('if request.operation == "validation":', routing_code)
        self.assertIn('if request.operation == "reporting":', routing_code)
        self.assertIn("return self._handle_data_processing(request)", routing_code)
        self.assertIn("return self._handle_validation(request)", routing_code)
        self.assertIn("return self._handle_reporting(request)", routing_code)

    def test_specific_methods_generation(self):
        """Test generation of agent-specific methods."""
        methods_code = self.engine._generate_specific_methods(self.test_spec)

        self.assertIn("def _handle_data_processing(self, request:", methods_code)
        self.assertIn("def _handle_validation(self, request:", methods_code)
        self.assertIn("def _handle_reporting(self, request:", methods_code)
        self.assertIn("Handle data processing operation", methods_code)
        self.assertIn("Handle validation operation", methods_code)
        self.assertIn("Handle reporting operation", methods_code)

    def test_recommendations_generation(self):
        """Test generation of recommendations."""
        # Test with many capabilities
        complex_spec = AgentSpecification(
            name="complex-agent",
            type=AgentType.SPECIALIZED,
            description="Complex agent",
            capabilities=["cap1", "cap2", "cap3", "cap4", "cap5", "cap6"],
            interfaces={},
            requirements={},
        )

        recommendations = self.engine._generate_recommendations(
            complex_spec, self.test_template_options
        )

        # Should recommend splitting due to many capabilities
        arch_recommendations = [
            r for r in recommendations if r.category == "architecture"
        ]
        self.assertGreater(len(arch_recommendations), 0)

        # Test with minimal template
        minimal_options = TemplateOptions(
            base_template=TemplateType.MINIMAL, include_tests=False
        )

        recommendations = self.engine._generate_recommendations(
            self.test_spec, minimal_options
        )

        # Should recommend upgrading template and adding tests
        feature_recommendations = [
            r for r in recommendations if r.category == "features"
        ]
        quality_recommendations = [
            r for r in recommendations if r.category == "quality"
        ]

        self.assertGreater(len(feature_recommendations), 0)
        self.assertGreater(len(quality_recommendations), 0)

    def test_create_agent_success(self):
        """Test successful agent creation."""
        response = self.engine.create_agent(
            self.test_spec, self.test_template_options, self.test_generation_options
        )

        self.assertIsInstance(response, AgentGeneratorResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.operation, "create")

        # Check agent info
        self.assertIn("name", response.agent_info)
        self.assertIn("version", response.agent_info)
        self.assertIn("type", response.agent_info)
        self.assertIn("status", response.agent_info)

        # Check generated files
        self.assertGreater(len(response.generated_files), 0)

        # Verify files were actually created
        for file_info in response.generated_files:
            self.assertTrue(os.path.exists(file_info.path))

        # Check integration points
        self.assertGreater(len(response.integration_points), 0)

        # Check validation results
        self.assertEqual(response.validation_results.syntax_check, "passed")
        self.assertEqual(response.validation_results.interface_validation, "passed")

    def test_create_agent_validation_failure(self):
        """Test agent creation with validation failure."""
        invalid_spec = AgentSpecification(
            name="Invalid Name!",
            type=AgentType.SPECIALIZED,
            description="Invalid agent",
            capabilities=[],
            interfaces={},
            requirements={},
        )

        response = self.engine.create_agent(
            invalid_spec, self.test_template_options, self.test_generation_options
        )

        self.assertFalse(response.success)
        self.assertIn("Specification validation failed", response.errors)
        self.assertEqual(response.validation_results.syntax_check, "failed")

    @patch("builtins.open", side_effect=PermissionError("Access denied"))
    def test_create_agent_file_error(self, mock_open):
        """Test agent creation with file system error."""
        response = self.engine.create_agent(
            self.test_spec, self.test_template_options, self.test_generation_options
        )

        self.assertFalse(response.success)
        self.assertGreater(len(response.errors), 0)

    def test_process_request_create_operation(self):
        """Test processing create operation request."""
        request = {
            "operation": "create",
            "agent_specification": {
                "name": "api-client",
                "type": "specialized",
                "description": "REST API client agent",
                "capabilities": ["http_requests", "response_parsing", "error_handling"],
                "interfaces": {"input_format": "json", "output_format": "json"},
                "requirements": {"dependencies": ["requests", "httpx"]},
            },
            "template_options": {
                "base_template": "standard",
                "include_tests": True,
                "include_documentation": True,
            },
            "generation_options": {
                "output_directory": self.test_output_dir,
                "validate_before_creation": True,
                "auto_register": True,
            },
        }

        response = self.engine.process_request(request)

        self.assertIsInstance(response, dict)
        self.assertTrue(response["success"])
        self.assertEqual(response["operation"], "create")
        self.assertIn("agent_info", response)
        self.assertIn("generated_files", response)

    def test_process_request_unsupported_operation(self):
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation", "agent_specification": {}}

        response = self.engine.process_request(request)

        self.assertFalse(response["success"])
        self.assertIn("Unsupported operation", response["errors"][0])

    def test_process_request_malformed_data(self):
        """Test processing request with malformed data."""
        request = {
            "operation": "create",
            # Missing required fields
        }

        response = self.engine.process_request(request)

        self.assertFalse(response["success"])
        self.assertGreater(len(response["errors"]), 0)

    def test_template_variable_replacement(self):
        """Test that template variables are properly replaced."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec, self.test_template_options, output_dir
        )

        with open(generated_file.path, "r") as f:
            content = f.read()

        # Check that template variables were replaced
        self.assertNotIn("{AGENT_NAME}", content)
        self.assertNotIn("{AGENT_CLASS_NAME}", content)
        self.assertNotIn("{AGENT_LOGGER_NAME}", content)
        self.assertNotIn("{AGENT_DESCRIPTION}", content)

        # Check that actual values are present
        self.assertIn("test_agent", content)
        self.assertIn("TestAgentEngine", content)

    def test_file_size_calculation(self):
        """Test that file size is calculated correctly."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check that size is reported
        self.assertIsNotNone(generated_file.size)
        self.assertTrue(generated_file.size.endswith("B"))

        # Verify size is approximately correct
        actual_size = os.path.getsize(generated_file.path)
        reported_size = int(generated_file.size[:-1])  # Remove 'B'
        self.assertEqual(actual_size, reported_size)

    def test_checksum_generation(self):
        """Test that file checksums are generated correctly."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check that checksum is generated
        self.assertIsNotNone(generated_file.checksum)
        self.assertEqual(len(generated_file.checksum), 16)  # Truncated SHA256

        # Verify checksum is correct
        with open(generated_file.path, "r") as f:
            content = f.read()

        import hashlib

        expected_checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        self.assertEqual(generated_file.checksum, expected_checksum)

    def test_integration_points_generation(self):
        """Test generation of integration points."""
        response = self.engine.create_agent(
            self.test_spec, self.test_template_options, self.test_generation_options
        )

        self.assertTrue(response.success)
        self.assertGreater(len(response.integration_points), 0)

        # Check for orchestrator integration
        orchestrator_integration = [
            ip for ip in response.integration_points if ip.component == "orchestrator"
        ]
        self.assertGreater(len(orchestrator_integration), 0)

        # Check for gadugi integration
        gadugi_integration = [
            ip for ip in response.integration_points if ip.component == "gadugi"
        ]
        self.assertGreater(len(gadugi_integration), 0)

    def test_agent_type_enum(self):
        """Test AgentType enum functionality."""
        self.assertEqual(AgentType.SPECIALIZED.value, "specialized")
        self.assertEqual(AgentType.GENERAL.value, "general")
        self.assertEqual(AgentType.UTILITY.value, "utility")
        self.assertEqual(AgentType.SERVICE.value, "service")

    def test_template_type_enum(self):
        """Test TemplateType enum functionality."""
        self.assertEqual(TemplateType.STANDARD.value, "standard")
        self.assertEqual(TemplateType.MINIMAL.value, "minimal")
        self.assertEqual(TemplateType.ADVANCED.value, "advanced")
        self.assertEqual(TemplateType.CUSTOM.value, "custom")

    def test_dataclass_serialization(self):
        """Test that dataclasses can be serialized to dictionaries."""
        response = self.engine.create_agent(
            self.test_spec, self.test_template_options, self.test_generation_options
        )

        # Test that response can be converted to dict (via asdict)
        from dataclasses import asdict

        response_dict = asdict(response)

        self.assertIsInstance(response_dict, dict)
        self.assertIn("success", response_dict)
        self.assertIn("operation", response_dict)
        self.assertIn("agent_info", response_dict)

    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.engine.logger)
        self.assertEqual(self.engine.logger.name, "agent_generator")

        # Test logging level
        import logging

        self.assertEqual(self.engine.logger.level, logging.INFO)

    def test_full_agent_generation_integration(self):
        """Test complete agent generation workflow."""
        # Generate a complete agent with all features
        full_spec = AgentSpecification(
            name="integration-test-agent",
            type=AgentType.SPECIALIZED,
            description="Full integration test agent with all features",
            capabilities=[
                "data_processing",
                "file_operations",
                "networking",
                "monitoring",
            ],
            interfaces={
                "input_format": "json",
                "output_format": "json",
                "communication_protocol": "http",
            },
            requirements={
                "memory_limit": "512MB",
                "cpu_limit": "200m",
                "dependencies": ["requests", "pydantic", "asyncio"],
            },
        )

        full_template_options = TemplateOptions(
            base_template=TemplateType.ADVANCED,
            include_tests=True,
            include_documentation=True,
            include_examples=True,
            integration_level="full",
        )

        full_generation_options = GenerationOptions(
            output_directory=self.test_output_dir,
            overwrite_existing=True,
            validate_before_creation=True,
            auto_register=True,
            auto_deploy=False,
        )

        response = self.engine.create_agent(
            full_spec, full_template_options, full_generation_options
        )

        # Verify successful generation
        self.assertTrue(response.success)
        self.assertEqual(len(response.errors), 0)
        self.assertGreater(len(response.generated_files), 3)  # At least 4 files

        # Verify all file types were generated
        file_types = {f.type for f in response.generated_files}
        self.assertIn("agent", file_types)
        self.assertIn("engine", file_types)
        self.assertIn("test", file_types)
        self.assertIn("documentation", file_types)

        # Verify files contain expected content
        engine_file = next(f for f in response.generated_files if f.type == "engine")
        with open(engine_file.path, "r") as f:
            engine_content = f.read()

        # Check advanced template features
        self.assertIn("async def execute_operation_async", engine_content)
        self.assertIn("PerformanceMetrics", engine_content)
        self.assertIn("cache", engine_content)
        self.assertIn("IntegrationTestAgentManager", engine_content)

        # Check all capabilities have handlers
        for capability in full_spec.capabilities:
            self.assertIn(f"_handle_{capability}", engine_content)

        # Verify test file
        test_file = next(f for f in response.generated_files if f.type == "test")
        with open(test_file.path, "r") as f:
            test_content = f.read()

        self.assertIn("TestIntegrationTestAgentEngine", test_content)
        self.assertIn("def test_engine_initialization", test_content)

        # Verify README file
        readme_file = next(
            f for f in response.generated_files if f.type == "documentation"
        )
        with open(readme_file.path, "r") as f:
            readme_content = f.read()

        self.assertIn("# Integration Test Agent", readme_content)
        self.assertIn("data_processing", readme_content)
        self.assertIn("file_operations", readme_content)
        self.assertIn("networking", readme_content)
        self.assertIn("monitoring", readme_content)


if __name__ == "__main__":
    unittest.main()
