#!/usr/bin/env python3
"""Tests for Agent Generator Engine."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from agent_generator_engine import (
    AgentGeneratorEngine,
    AgentGeneratorResponse,
    AgentSpecification,
    AgentType,
    GeneratedFile,
    GenerationOptions,
    TemplateOptions,
    TemplateType,
)


class TestAgentGeneratorEngine(unittest.TestCase):
    """Test cases for Agent Generator Engine."""

    def setUp(self) -> None:
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

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_engine_initialization(self) -> None:
        """Test engine initializes properly."""
        assert self.engine is not None
        assert self.engine.logger is not None
        assert self.engine.templates is not None
        assert "standard" in self.engine.templates
        assert "minimal" in self.engine.templates
        assert "advanced" in self.engine.templates

    def test_template_loading(self) -> None:
        """Test that templates are loaded correctly."""
        templates = self.engine.templates

        # Check all required templates exist
        required_templates = ["standard", "minimal", "advanced"]
        for template_name in required_templates:
            assert template_name in templates
            assert isinstance(templates[template_name], str)
            assert len(templates[template_name]) > 100

    def test_agent_specification_validation_valid(self) -> None:
        """Test validation of valid agent specification."""
        result = self.engine._validate_specification(self.test_spec)

        assert result.syntax_check == "passed"
        assert result.interface_validation == "passed"
        assert result.dependency_check == "passed"
        assert result.integration_test == "passed"

    def test_agent_specification_validation_invalid_name(self) -> None:
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
        assert result.syntax_check == "failed"

    def test_agent_specification_validation_no_capabilities(self) -> None:
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
        assert result.syntax_check == "failed"

    def test_directory_creation(self) -> None:
        """Test directory creation utility."""
        test_dir = Path(self.temp_dir) / "new_directory"
        assert not test_dir.exists()

        self.engine._ensure_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_agent_file_generation(self) -> None:
        """Test generation of agent specification file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check file was generated
        assert isinstance(generated_file, GeneratedFile)
        assert generated_file.type == "agent"
        assert os.path.exists(generated_file.path)

        # Check file content
        with open(generated_file.path) as f:
            content = f.read()

        assert "test-agent" in content.lower()
        assert "data_processing" in content
        assert "validation" in content
        assert "reporting" in content

    def test_engine_file_generation_standard_template(self) -> None:
        """Test generation of engine file with standard template."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec,
            self.test_template_options,
            output_dir,
        )

        # Check file was generated
        assert isinstance(generated_file, GeneratedFile)
        assert generated_file.type == "engine"
        assert os.path.exists(generated_file.path)

        # Check file content
        with open(generated_file.path) as f:
            content = f.read()

        assert "class TestAgentEngine:" in content
        assert "def execute_operation" in content
        assert "_handle_data_processing" in content
        assert "_handle_validation" in content
        assert "_handle_reporting" in content

    def test_engine_file_generation_minimal_template(self) -> None:
        """Test generation of engine file with minimal template."""
        minimal_options = TemplateOptions(
            base_template=TemplateType.MINIMAL,
            include_tests=False,
            include_documentation=False,
        )

        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec,
            minimal_options,
            output_dir,
        )

        # Check file was generated
        assert os.path.exists(generated_file.path)

        # Check file content is minimal
        with open(generated_file.path) as f:
            content = f.read()

        assert "class TestAgent:" in content
        assert "def process" in content
        assert "async def" not in content  # No async in minimal

    def test_engine_file_generation_advanced_template(self) -> None:
        """Test generation of engine file with advanced template."""
        advanced_options = TemplateOptions(
            base_template=TemplateType.ADVANCED,
            include_tests=True,
            include_documentation=True,
        )

        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec,
            advanced_options,
            output_dir,
        )

        # Check file was generated
        assert os.path.exists(generated_file.path)

        # Check file content has advanced features
        with open(generated_file.path) as f:
            content = f.read()

        assert "async def execute_operation_async" in content
        assert "PerformanceMetrics" in content
        assert "cache" in content
        assert "TestAgentManager" in content

    def test_test_file_generation(self) -> None:
        """Test generation of test file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_test_file(self.test_spec, output_dir)

        # Check file was generated
        assert isinstance(generated_file, GeneratedFile)
        assert generated_file.type == "test"
        assert os.path.exists(generated_file.path)

        # Check file content
        with open(generated_file.path) as f:
            content = f.read()

        assert "class TestTestAgentEngine(unittest.TestCase):" in content
        assert "def test_engine_initialization" in content
        assert "def test_basic_operation" in content
        assert "from test_agent_engine import" in content

    def test_readme_file_generation(self) -> None:
        """Test generation of README file."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_readme_file(self.test_spec, output_dir)

        # Check file was generated
        assert isinstance(generated_file, GeneratedFile)
        assert generated_file.type == "documentation"
        assert os.path.exists(generated_file.path)

        # Check file content
        with open(generated_file.path) as f:
            content = f.read()

        assert "# Test Agent" in content
        assert "## Overview" in content
        assert "## Capabilities" in content
        assert "data_processing" in content
        assert "validation" in content
        assert "reporting" in content

    def test_initialization_code_generation(self) -> None:
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

        assert "self.cache = {}" in init_code
        assert "self.metrics = {}" in init_code
        assert "self.state = {}" in init_code

    def test_operation_routing_generation(self) -> None:
        """Test generation of operation routing logic."""
        routing_code = self.engine._generate_operation_routing(self.test_spec)

        assert 'if request.operation == "data_processing":' in routing_code
        assert 'if request.operation == "validation":' in routing_code
        assert 'if request.operation == "reporting":' in routing_code
        assert "return self._handle_data_processing(request)" in routing_code
        assert "return self._handle_validation(request)" in routing_code
        assert "return self._handle_reporting(request)" in routing_code

    def test_specific_methods_generation(self) -> None:
        """Test generation of agent-specific methods."""
        methods_code = self.engine._generate_specific_methods(self.test_spec)

        assert "def _handle_data_processing(self, request:" in methods_code
        assert "def _handle_validation(self, request:" in methods_code
        assert "def _handle_reporting(self, request:" in methods_code
        assert "Handle data processing operation" in methods_code
        assert "Handle validation operation" in methods_code
        assert "Handle reporting operation" in methods_code

    def test_recommendations_generation(self) -> None:
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
            complex_spec,
            self.test_template_options,
        )

        # Should recommend splitting due to many capabilities
        arch_recommendations = [r for r in recommendations if r.category == "architecture"]
        assert len(arch_recommendations) > 0

        # Test with minimal template
        minimal_options = TemplateOptions(
            base_template=TemplateType.MINIMAL,
            include_tests=False,
        )

        recommendations = self.engine._generate_recommendations(
            self.test_spec,
            minimal_options,
        )

        # Should recommend upgrading template and adding tests
        feature_recommendations = [r for r in recommendations if r.category == "features"]
        quality_recommendations = [r for r in recommendations if r.category == "quality"]

        assert len(feature_recommendations) > 0
        assert len(quality_recommendations) > 0

    def test_create_agent_success(self) -> None:
        """Test successful agent creation."""
        response = self.engine.create_agent(
            self.test_spec,
            self.test_template_options,
            self.test_generation_options,
        )

        assert isinstance(response, AgentGeneratorResponse)
        assert response.success
        assert response.operation == "create"

        # Check agent info
        assert "name" in response.agent_info
        assert "version" in response.agent_info
        assert "type" in response.agent_info
        assert "status" in response.agent_info

        # Check generated files
        assert len(response.generated_files) > 0

        # Verify files were actually created
        for file_info in response.generated_files:
            assert os.path.exists(file_info.path)

        # Check integration points
        assert len(response.integration_points) > 0

        # Check validation results
        assert response.validation_results.syntax_check == "passed"
        assert response.validation_results.interface_validation == "passed"

    def test_create_agent_validation_failure(self) -> None:
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
            invalid_spec,
            self.test_template_options,
            self.test_generation_options,
        )

        assert not response.success
        assert "Specification validation failed" in response.errors
        assert response.validation_results.syntax_check == "failed"

    @patch("builtins.open", side_effect=PermissionError("Access denied"))
    def test_create_agent_file_error(self, mock_open) -> None:
        """Test agent creation with file system error."""
        response = self.engine.create_agent(
            self.test_spec,
            self.test_template_options,
            self.test_generation_options,
        )

        assert not response.success
        assert len(response.errors) > 0

    def test_process_request_create_operation(self) -> None:
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

        assert isinstance(response, dict)
        assert response["success"]
        assert response["operation"] == "create"
        assert "agent_info" in response
        assert "generated_files" in response

    def test_process_request_unsupported_operation(self) -> None:
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation", "agent_specification": {}}

        response = self.engine.process_request(request)

        assert not response["success"]
        assert "Unsupported operation" in response["errors"][0]

    def test_process_request_malformed_data(self) -> None:
        """Test processing request with malformed data."""
        request = {
            "operation": "create",
            # Missing required fields
        }

        response = self.engine.process_request(request)

        assert not response["success"]
        assert len(response["errors"]) > 0

    def test_template_variable_replacement(self) -> None:
        """Test that template variables are properly replaced."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_engine_file(
            self.test_spec,
            self.test_template_options,
            output_dir,
        )

        with open(generated_file.path) as f:
            content = f.read()

        # Check that template variables were replaced
        assert "{AGENT_NAME}" not in content
        assert "{AGENT_CLASS_NAME}" not in content
        assert "{AGENT_LOGGER_NAME}" not in content
        assert "{AGENT_DESCRIPTION}" not in content

        # Check that actual values are present
        assert "test_agent" in content
        assert "TestAgentEngine" in content

    def test_file_size_calculation(self) -> None:
        """Test that file size is calculated correctly."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check that size is reported
        assert generated_file.size is not None
        assert generated_file.size.endswith("B")

        # Verify size is approximately correct
        actual_size = os.path.getsize(generated_file.path)
        reported_size = int(generated_file.size[:-1])  # Remove 'B'
        assert actual_size == reported_size

    def test_checksum_generation(self) -> None:
        """Test that file checksums are generated correctly."""
        output_dir = Path(self.test_output_dir) / "test-agent"
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_file = self.engine._generate_agent_file(self.test_spec, output_dir)

        # Check that checksum is generated
        assert generated_file.checksum is not None
        assert len(generated_file.checksum) == 16  # Truncated SHA256

        # Verify checksum is correct
        with open(generated_file.path) as f:
            content = f.read()

        import hashlib

        expected_checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        assert generated_file.checksum == expected_checksum

    def test_integration_points_generation(self) -> None:
        """Test generation of integration points."""
        response = self.engine.create_agent(
            self.test_spec,
            self.test_template_options,
            self.test_generation_options,
        )

        assert response.success
        assert len(response.integration_points) > 0

        # Check for orchestrator integration
        orchestrator_integration = [
            ip for ip in response.integration_points if ip.component == "orchestrator"
        ]
        assert len(orchestrator_integration) > 0

        # Check for gadugi integration
        gadugi_integration = [ip for ip in response.integration_points if ip.component == "gadugi"]
        assert len(gadugi_integration) > 0

    def test_agent_type_enum(self) -> None:
        """Test AgentType enum functionality."""
        assert AgentType.SPECIALIZED.value == "specialized"
        assert AgentType.GENERAL.value == "general"
        assert AgentType.UTILITY.value == "utility"
        assert AgentType.SERVICE.value == "service"

    def test_template_type_enum(self) -> None:
        """Test TemplateType enum functionality."""
        assert TemplateType.STANDARD.value == "standard"
        assert TemplateType.MINIMAL.value == "minimal"
        assert TemplateType.ADVANCED.value == "advanced"
        assert TemplateType.CUSTOM.value == "custom"

    def test_dataclass_serialization(self) -> None:
        """Test that dataclasses can be serialized to dictionaries."""
        response = self.engine.create_agent(
            self.test_spec,
            self.test_template_options,
            self.test_generation_options,
        )

        # Test that response can be converted to dict (via asdict)
        from dataclasses import asdict

        response_dict = asdict(response)

        assert isinstance(response_dict, dict)
        assert "success" in response_dict
        assert "operation" in response_dict
        assert "agent_info" in response_dict

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.engine.logger is not None
        assert self.engine.logger.name == "agent_generator"

        # Test logging level
        import logging

        assert self.engine.logger.level == logging.INFO

    def test_full_agent_generation_integration(self) -> None:
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
            full_spec,
            full_template_options,
            full_generation_options,
        )

        # Verify successful generation
        assert response.success
        assert len(response.errors) == 0
        assert len(response.generated_files) > 3  # At least 4 files

        # Verify all file types were generated
        file_types = {f.type for f in response.generated_files}
        assert "agent" in file_types
        assert "engine" in file_types
        assert "test" in file_types
        assert "documentation" in file_types

        # Verify files contain expected content
        engine_file = next(f for f in response.generated_files if f.type == "engine")
        with open(engine_file.path) as f:
            engine_content = f.read()

        # Check advanced template features
        assert "async def execute_operation_async" in engine_content
        assert "PerformanceMetrics" in engine_content
        assert "cache" in engine_content
        assert "IntegrationTestAgentManager" in engine_content

        # Check all capabilities have handlers
        for capability in full_spec.capabilities:
            assert f"_handle_{capability}" in engine_content

        # Verify test file
        test_file = next(f for f in response.generated_files if f.type == "test")
        with open(test_file.path) as f:
            test_content = f.read()

        assert "TestIntegrationTestAgentEngine" in test_content
        assert "def test_engine_initialization" in test_content

        # Verify README file
        readme_file = next(f for f in response.generated_files if f.type == "documentation")
        with open(readme_file.path) as f:
            readme_content = f.read()

        assert "# Integration Test Agent" in readme_content
        assert "data_processing" in readme_content
        assert "file_operations" in readme_content
        assert "networking" in readme_content
        assert "monitoring" in readme_content


if __name__ == "__main__":
    unittest.main()
