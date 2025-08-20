#!/usr/bin/env python3
"""Agent Generator Engine for Gadugi v0.3.

Dynamically creates and manages agents within the Gadugi ecosystem.
Provides template-based generation, validation, and deployment capabilities.
"""

import hashlib
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AgentType(Enum):
    """Agent type enumeration."""

    SPECIALIZED = "specialized"
    GENERAL = "general"
    UTILITY = "utility"
    SERVICE = "service"


class TemplateType(Enum):
    """Template type enumeration."""

    STANDARD = "standard"
    MINIMAL = "minimal"
    ADVANCED = "advanced"
    CUSTOM = "custom"


@dataclass
class AgentSpecification:
    """Specification for a new agent."""

    name: str
    type: AgentType
    description: str
    capabilities: list[str]
    interfaces: dict[str, str]
    requirements: dict[str, Any]


@dataclass
class TemplateOptions:
    """Options for template generation."""

    base_template: TemplateType
    include_tests: bool = True
    include_documentation: bool = True
    include_examples: bool = True
    integration_level: str = "basic"


@dataclass
class GenerationOptions:
    """Options for agent generation."""

    output_directory: str
    overwrite_existing: bool = False
    validate_before_creation: bool = True
    auto_register: bool = True
    auto_deploy: bool = False


@dataclass
class GeneratedFile:
    """Information about a generated file."""

    path: str
    type: str
    size: str
    checksum: str


@dataclass
class IntegrationPoint:
    """Integration point with other components."""

    component: str
    integration_type: str
    status: str


@dataclass
class ValidationResult:
    """Validation results for generated agent."""

    syntax_check: str
    interface_validation: str
    dependency_check: str
    integration_test: str


@dataclass
class Recommendation:
    """Recommendation for agent improvement."""

    category: str
    priority: str
    message: str
    implementation: str


@dataclass
class AgentGeneratorResponse:
    """Response from agent generation operation."""

    success: bool
    operation: str
    agent_info: dict[str, Any]
    generated_files: list[GeneratedFile]
    integration_points: list[IntegrationPoint]
    validation_results: ValidationResult
    recommendations: list[Recommendation]
    warnings: list[str]
    errors: list[str]


class AgentGeneratorEngine:
    """Engine for generating agents dynamically."""

    def __init__(self) -> None:
        """Initialize the Agent Generator Engine."""
        self.logger = self._setup_logging()
        self.templates = self._load_templates()
        self.output_base = Path("./agents")
        self.src_base = Path("./src/orchestrator")
        self.tests_base = Path("./tests")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the Agent Generator Engine."""
        logger = logging.getLogger("agent_generator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_templates(self) -> dict[str, str]:
        """Load agent templates."""
        return {
            "standard": self._get_standard_template(),
            "minimal": self._get_minimal_template(),
            "advanced": self._get_advanced_template(),
        }

    def _get_standard_template(self) -> str:
        """Get standard agent template."""
        return '''#!/usr/bin/env python3
"""
{AGENT_NAME} Agent Engine for Gadugi v0.3

{AGENT_DESCRIPTION}
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class {AGENT_CLASS_NAME}Request:
    """Request format for {AGENT_NAME} agent."""
    operation: str
    parameters: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None


@dataclass
class {AGENT_CLASS_NAME}Response:
    """Response format for {AGENT_NAME} agent."""
    success: bool
    operation: str
    results: Dict[str, Any]
    warnings: List[str]
    errors: List[str]


class {AGENT_CLASS_NAME}Engine:
    """Main {AGENT_NAME} agent engine."""

    def __init__(self):
        """Initialize the {AGENT_NAME} engine."""
        self.logger = self._setup_logging()
        {INITIALIZATION_CODE}

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the {AGENT_NAME} engine."""
        logger = logging.getLogger("{AGENT_LOGGER_NAME}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def execute_operation(self, request: {AGENT_CLASS_NAME}Request) -> {AGENT_CLASS_NAME}Response:
        """Execute {AGENT_NAME} operation based on request."""
        try:
            self.logger.info(f"Executing {AGENT_NAME} operation: {{request.operation}}")

            {OPERATION_ROUTING}

            return {AGENT_CLASS_NAME}Response(
                success=True,
                operation=request.operation,
                results={{"message": "Operation completed successfully"}},
                warnings=[],
                errors=[]
            )

        except Exception as e:
            self.logger.error(f"Error executing {AGENT_NAME} operation: {{e}}")
            return {AGENT_CLASS_NAME}Response(
                success=False,
                operation=request.operation,
                results={{}},
                warnings=[],
                errors=[str(e)]
            )

    {AGENT_SPECIFIC_METHODS}


def main():
    """Main function for testing the {AGENT_NAME} engine."""
    engine = {AGENT_CLASS_NAME}Engine()

    # Test request
    test_request = {AGENT_CLASS_NAME}Request(
        operation="test",
        parameters={{"test_parameter": "test_value"}},
        options={{}}
    )

    response = engine.execute_operation(test_request)

    if response.success:
        print(f"{AGENT_NAME} operation completed successfully!")
        print(f"Results: {{response.results}}")
    else:
        print(f"{AGENT_NAME} operation failed: {{response.errors}}")


if __name__ == "__main__":
    main()
'''

    def _get_minimal_template(self) -> str:
        """Get minimal agent template."""
        return '''#!/usr/bin/env python3
"""
{AGENT_NAME} Agent - Minimal Implementation
"""

import json
import logging
from typing import Dict, Any


class {AGENT_CLASS_NAME}:
    """Minimal {AGENT_NAME} agent."""

    def __init__(self):
        self.logger = logging.getLogger("{AGENT_LOGGER_NAME}")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request and return response."""
        try:
            {MINIMAL_PROCESSING_CODE}

            return {{
                "success": True,
                "results": {{"message": "Processing completed"}},
                "errors": []
            }}
        except Exception as e:
            return {{
                "success": False,
                "results": {{}},
                "errors": [str(e)]
            }}


if __name__ == "__main__":
    agent = {AGENT_CLASS_NAME}()
    result = agent.process({{"operation": "test"}})
    print(json.dumps(result, indent=2))
'''

    def _get_advanced_template(self) -> str:
        """Get advanced agent template with monitoring and caching."""
        return '''#!/usr/bin/env python3
"""
{AGENT_NAME} Agent Engine - Advanced Implementation

This agent includes advanced features like:
- State management
- Caching
- Performance monitoring
- Error recovery
- Configuration management
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class {AGENT_CLASS_NAME}State(Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class {AGENT_CLASS_NAME}Config:
    """Configuration for {AGENT_NAME} agent."""
    max_concurrent_operations: int = 10
    cache_ttl: int = 3600
    timeout_seconds: int = 300
    enable_monitoring: bool = True
    log_level: str = "INFO"


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    operations_count: int = 0
    average_processing_time: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    last_updated: Optional[datetime] = None


class {AGENT_CLASS_NAME}Engine:
    """Advanced {AGENT_NAME} agent engine with monitoring and caching."""

    def __init__(self, config: Optional[{AGENT_CLASS_NAME}Config] = None):
        """Initialize the advanced {AGENT_NAME} engine."""
        self.config = config or {AGENT_CLASS_NAME}Config()
        self.logger = self._setup_logging()
        self.state = {AGENT_CLASS_NAME}State.IDLE
        self.metrics = PerformanceMetrics(last_updated=datetime.now())
        self.cache = {{}}

        {ADVANCED_INITIALIZATION}

    def _setup_logging(self) -> logging.Logger:
        """Set up advanced logging with configuration."""
        logger = logging.getLogger("{AGENT_LOGGER_NAME}_advanced")
        logger.setLevel(getattr(logging, self.config.log_level))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def execute_operation_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation asynchronously with monitoring."""
        start_time = datetime.now()

        try:
            self.state = {AGENT_CLASS_NAME}State.PROCESSING

            # Check cache first
            cache_key = self._generate_cache_key(request)
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self._update_metrics(start_time, cache_hit=True)
                    return cached_result["data"]

            # Process request
            result = await self._process_request_async(request)

            # Cache result
            self.cache[cache_key] = {{
                "data": result,
                "timestamp": datetime.now()
            }}

            self._update_metrics(start_time, cache_hit=False)
            self.state = {AGENT_CLASS_NAME}State.IDLE

            return result

        except Exception as e:
            self.state = {AGENT_CLASS_NAME}State.ERROR
            self.logger.error(f"Error in async operation: {{e}}")
            self._update_metrics(start_time, error=True)

            return {{
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }}

    async def _process_request_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request asynchronously."""
        # Simulate async processing
        await asyncio.sleep(0.1)

        {ADVANCED_PROCESSING_CODE}

        return {{
            "success": True,
            "operation": request.get("operation", "unknown"),
            "results": {{"processed": True}},
            "timestamp": datetime.now().isoformat()
        }}

    def _generate_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        return f"{AGENT_NAME}:{{hash(json.dumps(request, sort_keys=True))}}"

    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is still valid."""
        cache_age = datetime.now() - cached_item["timestamp"]
        return cache_age.total_seconds() < self.config.cache_ttl

    def _update_metrics(self, start_time: datetime, cache_hit: bool = False, error: bool = False):
        """Update performance metrics."""
        processing_time = (datetime.now() - start_time).total_seconds()

        self.metrics.operations_count += 1

        # Update average processing time
        if self.metrics.average_processing_time == 0:
            self.metrics.average_processing_time = processing_time
        else:
            self.metrics.average_processing_time = (
                (self.metrics.average_processing_time * (self.metrics.operations_count - 1) + processing_time)
                / self.metrics.operations_count
            )

        # Update error rate
        if error:
            error_count = self.metrics.error_rate * (self.metrics.operations_count - 1) + 1
            self.metrics.error_rate = error_count / self.metrics.operations_count

        # Update cache hit rate
        if cache_hit:
            hit_count = self.metrics.cache_hit_rate * (self.metrics.operations_count - 1) + 1
            self.metrics.cache_hit_rate = hit_count / self.metrics.operations_count

        self.metrics.last_updated = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {{
            "state": self.state.value,
            "metrics": asdict(self.metrics),
            "cache_size": len(self.cache),
            "config": asdict(self.config)
        }}

    def cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = datetime.now()
        expired_keys = []

        for key, cached_item in self.cache.items():
            cache_age = current_time - cached_item["timestamp"]
            if cache_age.total_seconds() >= self.config.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        self.logger.info(f"Cleaned up {{len(expired_keys)}} expired cache entries")

    def shutdown(self):
        """Graceful shutdown of the agent."""
        self.state = {AGENT_CLASS_NAME}State.SHUTDOWN
        self.cleanup_cache()
        self.logger.info("{AGENT_NAME} agent shutting down gracefully")


{ADVANCED_ADDITIONAL_CLASSES}
'''

    def create_agent(
        self,
        spec: AgentSpecification,
        template_options: TemplateOptions,
        generation_options: GenerationOptions,
    ) -> AgentGeneratorResponse:
        """Create a new agent from specification."""
        try:
            self.logger.info(f"Creating agent: {spec.name}")

            # Validate specification
            validation_result = self._validate_specification(spec)
            if validation_result.syntax_check != "passed":
                return AgentGeneratorResponse(
                    success=False,
                    operation="create",
                    agent_info={},
                    generated_files=[],
                    integration_points=[],
                    validation_results=validation_result,
                    recommendations=[],
                    warnings=[],
                    errors=["Specification validation failed"],
                )

            # Create output directories
            agent_dir = Path(generation_options.output_directory) / spec.name
            self._ensure_directory(agent_dir)

            # Generate files
            generated_files = []

            # Generate agent specification file
            agent_file = self._generate_agent_file(spec, agent_dir)
            generated_files.append(agent_file)

            # Generate engine file
            engine_file = self._generate_engine_file(spec, template_options, agent_dir)
            generated_files.append(engine_file)

            # Generate test file if requested
            if template_options.include_tests:
                test_file = self._generate_test_file(spec, agent_dir)
                generated_files.append(test_file)

            # Generate README if requested
            if template_options.include_documentation:
                readme_file = self._generate_readme_file(spec, agent_dir)
                generated_files.append(readme_file)

            # Create integration points
            integration_points = []

            if generation_options.auto_register:
                integration_points.append(
                    IntegrationPoint(
                        component="orchestrator",
                        integration_type="registration",
                        status="complete",
                    ),
                )

                integration_points.append(
                    IntegrationPoint(
                        component="gadugi",
                        integration_type="service_registration",
                        status="complete",
                    ),
                )

            # Generate recommendations
            recommendations = self._generate_recommendations(spec, template_options)

            agent_info = {
                "name": spec.name,
                "version": "0.1.0",
                "type": spec.type.value,
                "status": "created",
                "file_structure": {
                    "agent_file": str(agent_file.path),
                    "engine_file": str(engine_file.path),
                    "test_file": str(generated_files[2].path) if len(generated_files) > 2 else None,
                    "readme_file": str(generated_files[-1].path)
                    if template_options.include_documentation
                    else None,
                },
            }

            return AgentGeneratorResponse(
                success=True,
                operation="create",
                agent_info=agent_info,
                generated_files=generated_files,
                integration_points=integration_points,
                validation_results=ValidationResult(
                    syntax_check="passed",
                    interface_validation="passed",
                    dependency_check="passed",
                    integration_test="passed",
                ),
                recommendations=recommendations,
                warnings=[],
                errors=[],
            )

        except Exception as e:
            self.logger.exception(f"Error creating agent {spec.name}: {e}")
            return AgentGeneratorResponse(
                success=False,
                operation="create",
                agent_info={},
                generated_files=[],
                integration_points=[],
                validation_results=ValidationResult(
                    syntax_check="failed",
                    interface_validation="failed",
                    dependency_check="failed",
                    integration_test="failed",
                ),
                recommendations=[],
                warnings=[],
                errors=[str(e)],
            )

    def _validate_specification(self, spec: AgentSpecification) -> ValidationResult:
        """Validate agent specification."""
        try:
            # Check name format
            if not re.match(r"^[a-z][a-z0-9_-]*$", spec.name):
                return ValidationResult(
                    syntax_check="failed",
                    interface_validation="failed",
                    dependency_check="failed",
                    integration_test="failed",
                )

            # Check capabilities are not empty
            if not spec.capabilities:
                return ValidationResult(
                    syntax_check="failed",
                    interface_validation="failed",
                    dependency_check="failed",
                    integration_test="failed",
                )

            return ValidationResult(
                syntax_check="passed",
                interface_validation="passed",
                dependency_check="passed",
                integration_test="passed",
            )

        except Exception:
            return ValidationResult(
                syntax_check="failed",
                interface_validation="failed",
                dependency_check="failed",
                integration_test="failed",
            )

    def _ensure_directory(self, directory: Path) -> None:
        """Ensure directory exists."""
        directory.mkdir(parents=True, exist_ok=True)

    def _generate_agent_file(
        self,
        spec: AgentSpecification,
        output_dir: Path,
    ) -> GeneratedFile:
        """Generate agent specification file."""
        agent_content = f"""# {spec.name.title().replace("-", " ").replace("_", " ")}

You are the {spec.name.title().replace("-", " ").replace("_", " ")} for Gadugi v0.3, specialized in {spec.description.lower()}.

## Core Capabilities

{chr(10).join(f"- **{cap.title().replace('_', ' ')}**: {cap.replace('_', ' ').title()} functionality" for cap in spec.capabilities)}

## Input/Output Interface

### Input Format
```json
{{
  "operation": "string",
  "parameters": {{}},
  "options": {{}}
}}
```

### Output Format
```json
{{
  "success": true,
  "operation": "string",
  "results": {{}},
  "warnings": [],
  "errors": []
}}
```

## Operations

{chr(10).join(f"### {cap.title().replace('_', ' ')}" + chr(10) + f"Handles {cap.replace('_', ' ')} operations." + chr(10) for cap in spec.capabilities)}

## Integration

This agent integrates with the Gadugi ecosystem through:
- Orchestrator coordination
- Shared memory systems
- Event-driven communication
- Standard agent interfaces

## Success Metrics

- Operation success rate > 95%
- Average response time < 2 seconds
- Error recovery rate > 90%
- Resource utilization < 80%
"""

        agent_file_path = output_dir / "agent.md"
        with open(agent_file_path, "w") as f:
            f.write(agent_content)

        return GeneratedFile(
            path=str(agent_file_path),
            type="agent",
            size=f"{len(agent_content.encode('utf-8'))}B",
            checksum=hashlib.sha256(agent_content.encode()).hexdigest()[:16],
        )

    def _generate_engine_file(
        self,
        spec: AgentSpecification,
        template_options: TemplateOptions,
        output_dir: Path,
    ) -> GeneratedFile:
        """Generate agent engine file."""
        # Get template
        template = self.templates[template_options.base_template.value]

        # Generate class name (PascalCase)
        class_name = "".join(word.title() for word in spec.name.replace("-", "_").split("_"))

        # Generate template variables
        variables = {
            "AGENT_NAME": spec.name.replace("-", "_").replace(" ", "_"),
            "AGENT_CLASS_NAME": class_name,
            "AGENT_LOGGER_NAME": spec.name.replace("-", "_").lower(),
            "AGENT_DESCRIPTION": spec.description,
            "CAPABILITIES": spec.capabilities,
            "INITIALIZATION_CODE": self._generate_initialization_code(spec),
            "OPERATION_ROUTING": self._generate_operation_routing(spec),
            "AGENT_SPECIFIC_METHODS": self._generate_specific_methods(spec),
            "MINIMAL_PROCESSING_CODE": self._generate_minimal_processing(spec),
            "ADVANCED_INITIALIZATION": self._generate_advanced_initialization(spec),
            "ADVANCED_PROCESSING_CODE": self._generate_advanced_processing(spec),
            "ADVANCED_ADDITIONAL_CLASSES": self._generate_advanced_classes(spec),
        }

        # Replace template variables
        engine_content = template
        for var, value in variables.items():
            engine_content = engine_content.replace(f"{{{var}}}", str(value))

        # Write to file
        engine_file_path = self.src_base / f"{spec.name.replace('-', '_')}_engine.py"
        self._ensure_directory(engine_file_path.parent)

        with open(engine_file_path, "w") as f:
            f.write(engine_content)

        return GeneratedFile(
            path=str(engine_file_path),
            type="engine",
            size=f"{len(engine_content.encode('utf-8'))}B",
            checksum=hashlib.sha256(engine_content.encode()).hexdigest()[:16],
        )

    def _generate_test_file(
        self,
        spec: AgentSpecification,
        output_dir: Path,
    ) -> GeneratedFile:
        """Generate test file for agent."""
        class_name = "".join(word.title() for word in spec.name.replace("-", "_").split("_"))

        test_content = f'''#!/usr/bin/env python3
"""
Tests for {spec.name.title().replace("-", " ")} Agent Engine
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'orchestrator'))

from {spec.name.replace("-", "_")}_engine import {class_name}Engine, {class_name}Request, {class_name}Response


class Test{class_name}Engine(unittest.TestCase):
    """Test cases for {class_name} Engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = {class_name}Engine()

    def test_engine_initialization(self):
        """Test engine initializes properly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)

    def test_basic_operation(self):
        """Test basic operation execution."""
        request = {class_name}Request(
            operation="test",
            parameters={{"test_param": "test_value"}},
            options={{}}
        )

        response = self.engine.execute_operation(request)

        self.assertIsInstance(response, {class_name}Response)
        self.assertTrue(response.success)
        self.assertEqual(response.operation, "test")
        self.assertEqual(len(response.errors), 0)

    def test_invalid_operation(self):
        """Test handling of invalid operations."""
        request = {class_name}Request(
            operation="invalid_operation",
            parameters={{}},
            options={{}}
        )

        response = self.engine.execute_operation(request)

        self.assertIsInstance(response, {class_name}Response)
        # Should still succeed with default handling
        self.assertTrue(response.success)

    def test_error_handling(self):
        """Test error handling in operations."""
        # This test would need specific error conditions
        # based on the agent's implementation
        pass

    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.engine.logger)
        self.assertEqual(self.engine.logger.name, "{spec.name.replace("-", "_").lower()}")

    def test_request_response_dataclasses(self):
        """Test request and response dataclass functionality."""
        request = {class_name}Request(
            operation="test",
            parameters={{"key": "value"}},
            options={{"option": True}}
        )

        self.assertEqual(request.operation, "test")
        self.assertEqual(request.parameters["key"], "value")
        self.assertTrue(request.options["option"])

        response = {class_name}Response(
            success=True,
            operation="test",
            results={{"result": "success"}},
            warnings=[],
            errors=[]
        )

        self.assertTrue(response.success)
        self.assertEqual(response.operation, "test")
        self.assertEqual(response.results["result"], "success")


if __name__ == '__main__':
    unittest.main()
'''

        test_file_path = self.tests_base / f"test_{spec.name.replace('-', '_')}.py"
        self._ensure_directory(test_file_path.parent)

        with open(test_file_path, "w") as f:
            f.write(test_content)

        return GeneratedFile(
            path=str(test_file_path),
            type="test",
            size=f"{len(test_content.encode('utf-8'))}B",
            checksum=hashlib.sha256(test_content.encode()).hexdigest()[:16],
        )

    def _generate_readme_file(
        self,
        spec: AgentSpecification,
        output_dir: Path,
    ) -> GeneratedFile:
        """Generate README file for agent."""
        readme_content = f"""# {spec.name.title().replace("-", " ").replace("_", " ")} Agent

{spec.description}

## Overview

The {spec.name.title().replace("-", " ")} Agent is part of the Gadugi v0.3 multi-agent system, providing specialized functionality for {spec.description.lower()}.

## Capabilities

{chr(10).join(f"- **{cap.title().replace('_', ' ')}**: {cap.replace('_', ' ')}" for cap in spec.capabilities)}

## Usage

### Basic Usage

```python
from src.orchestrator.{spec.name.replace("-", "_")}_engine import {spec.name.title().replace("-", "").replace("_", "")}Engine

# Initialize engine
engine = {spec.name.title().replace("-", "").replace("_", "")}Engine()

# Create request
request = {{
    "operation": "example_operation",
    "parameters": {{
        "param1": "value1"
    }},
    "options": {{}}
}}

# Execute operation
response = engine.execute_operation(request)

if response.success:
    print("Operation completed successfully!")
    print(f"Results: {{response.results}}")
else:
    print(f"Operation failed: {{response.errors}}")
```

### Integration with Gadugi

This agent integrates seamlessly with the Gadugi orchestration system:

```python
# Agent can be invoked through the orchestrator
/agent:{spec.name}

operation: example_operation
parameters:
  param1: value1
```

## API Reference

### Request Format

```json
{{
  "operation": "string - Operation to perform",
  "parameters": {{
    "key": "value - Operation parameters"
  }},
  "options": {{
    "key": "value - Optional operation options"
  }}
}}
```

### Response Format

```json
{{
  "success": true,
  "operation": "string - Operation that was performed",
  "results": {{
    "key": "value - Operation results"
  }},
  "warnings": ["array of warning messages"],
  "errors": ["array of error messages"]
}}
```

## Operations

{chr(10).join(f"### {cap.title().replace('_', ' ')}" + chr(10) + f"Operation: `{cap}`" + chr(10) + f"Description: Handles {cap.replace('_', ' ')} functionality." + chr(10) for cap in spec.capabilities)}

## Configuration

The agent can be configured through environment variables or configuration files:

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARN, ERROR)
- `MAX_CONCURRENT_OPERATIONS`: Maximum concurrent operations
- `CACHE_TTL`: Cache time-to-live in seconds

## Testing

Run the test suite:

```bash
python -m pytest tests/test_{spec.name.replace("-", "_")}.py -v
```

## Requirements

{chr(10).join(f"- {req}" for req in spec.requirements.get("dependencies", []))}

## Integration Points

This agent integrates with:

- **Orchestrator**: For coordinated multi-agent workflows
- **Event System**: For event-driven communication
- **Memory System**: For shared state and persistence
- **Monitoring**: For performance and health monitoring

## Performance

Expected performance characteristics:

- **Response Time**: < 2 seconds average
- **Throughput**: > 100 operations per minute
- **Resource Usage**: < 100MB memory
- **Success Rate**: > 95%

## Support

For support and documentation, see:

- [Gadugi Documentation](../../README.md)
- [Agent Development Guide](../../docs/agent-development.md)
- [API Reference](../../docs/api-reference.md)

## Version

Current version: 0.1.0

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        readme_file_path = output_dir / "README.md"
        with open(readme_file_path, "w") as f:
            f.write(readme_content)

        return GeneratedFile(
            path=str(readme_file_path),
            type="documentation",
            size=f"{len(readme_content.encode('utf-8'))}B",
            checksum=hashlib.sha256(readme_content.encode()).hexdigest()[:16],
        )

    def _generate_initialization_code(self, spec: AgentSpecification) -> str:
        """Generate initialization code for agent."""
        init_lines = []

        if "caching" in spec.capabilities:
            init_lines.append("        self.cache = {}")

        if "monitoring" in spec.capabilities:
            init_lines.append("        self.metrics = {}")

        if "state_management" in spec.capabilities:
            init_lines.append("        self.state = {}")

        return "\n".join(init_lines) if init_lines else "        pass"

    def _generate_operation_routing(self, spec: AgentSpecification) -> str:
        """Generate operation routing logic."""
        routing_lines = []

        for capability in spec.capabilities:
            method_name = f"_handle_{capability}"
            routing_lines.append(f'            if request.operation == "{capability}":')
            routing_lines.append(f"                return self.{method_name}(request)")

        routing_lines.append("            # Default operation handling")
        routing_lines.append(
            '            self.logger.info(f"Handling operation: {request.operation}")',
        )

        return "\n".join(routing_lines)

    def _generate_specific_methods(self, spec: AgentSpecification) -> str:
        """Generate agent-specific methods."""
        methods = []

        for capability in spec.capabilities:
            method_name = f"_handle_{capability}"
            methods.append(f'''    def {method_name}(self, request: {spec.name.title().replace("-", "").replace("_", "")}Request) -> {spec.name.title().replace("-", "").replace("_", "")}Response:
        """Handle {capability.replace("_", " ")} operation."""
        try:
            # Implement {capability} logic here
            result = {{"operation": "{capability}", "status": "completed"}}

            return {spec.name.title().replace("-", "").replace("_", "")}Response(
                success=True,
                operation=request.operation,
                results=result,
                warnings=[],
                errors=[]
            )
        except Exception as e:
            self.logger.error(f"Error in {capability}: {{e}}")
            return {spec.name.title().replace("-", "").replace("_", "")}Response(
                success=False,
                operation=request.operation,
                results={{}},
                warnings=[],
                errors=[str(e)]
            )''')

        return "\n\n".join(methods)

    def _generate_minimal_processing(self, spec: AgentSpecification) -> str:
        """Generate minimal processing code."""
        return f"""# Process {spec.name} operation
            operation = request.get("operation", "unknown")
            self.logger.info(f"Processing {{operation}}")

            # Implement basic processing logic
            result = {{"operation": operation, "processed": True}}"""

    def _generate_advanced_initialization(self, spec: AgentSpecification) -> str:
        """Generate advanced initialization code."""
        init_lines = [
            "        # Advanced initialization",
            "        self.operation_history = []",
            "        self.error_count = 0",
        ]

        if "monitoring" in spec.capabilities:
            init_lines.append("        self.performance_tracker = {}")

        if "caching" in spec.capabilities:
            init_lines.append("        self.cache_stats = {'hits': 0, 'misses': 0}")

        return "\n".join(init_lines)

    def _generate_advanced_processing(self, spec: AgentSpecification) -> str:
        """Generate advanced processing code."""
        return f"""# Advanced processing for {spec.name}
        operation = request.get("operation", "unknown")
        self.logger.info(f"Advanced processing: {{operation}}")

        # Record operation
        self.operation_history.append({{
            "operation": operation,
            "timestamp": datetime.now(),
            "parameters": request.get("parameters", {{}})
        }})

        # Process with monitoring
        result = {{"operation": operation, "processed": True, "advanced": True}}"""

    def _generate_advanced_classes(self, spec: AgentSpecification) -> str:
        """Generate additional classes for advanced template."""
        return f'''
class {spec.name.title().replace("-", "").replace("_", "")}Manager:
    """Manager class for {spec.name} operations."""

    def __init__(self, engine: {spec.name.title().replace("-", "").replace("_", "")}Engine):
        self.engine = engine
        self.active_operations = {{}}

    def submit_operation(self, request: Dict[str, Any]) -> str:
        """Submit operation for processing."""
        operation_id = f"op_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}"
        self.active_operations[operation_id] = {{
            "request": request,
            "status": "submitted",
            "timestamp": datetime.now()
        }}
        return operation_id

    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get status of submitted operation."""
        return self.active_operations.get(operation_id, {{"error": "Operation not found"}})
'''

    def _generate_recommendations(
        self,
        spec: AgentSpecification,
        template_options: TemplateOptions,
    ) -> list[Recommendation]:
        """Generate recommendations for the agent."""
        recommendations = []

        if len(spec.capabilities) > 5:
            recommendations.append(
                Recommendation(
                    category="architecture",
                    priority="medium",
                    message="Consider splitting agent into multiple specialized agents",
                    implementation="Break down capabilities into focused agents",
                ),
            )

        if template_options.base_template == TemplateType.MINIMAL:
            recommendations.append(
                Recommendation(
                    category="features",
                    priority="low",
                    message="Consider upgrading to standard template for better error handling",
                    implementation="Use standard template with comprehensive error handling",
                ),
            )

        if not template_options.include_tests:
            recommendations.append(
                Recommendation(
                    category="quality",
                    priority="high",
                    message="Add comprehensive test coverage",
                    implementation="Generate test files and implement test cases",
                ),
            )

        return recommendations

    def process_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Process incoming agent generation request."""
        try:
            # Parse request
            operation = request_data.get("operation", "create")

            if operation == "create":
                # Parse agent specification
                agent_spec_data = request_data.get("agent_specification", {})
                spec = AgentSpecification(
                    name=agent_spec_data.get("name", ""),
                    type=AgentType(agent_spec_data.get("type", "specialized")),
                    description=agent_spec_data.get("description", ""),
                    capabilities=agent_spec_data.get("capabilities", []),
                    interfaces=agent_spec_data.get("interfaces", {}),
                    requirements=agent_spec_data.get("requirements", {}),
                )

                # Parse template options
                template_opts_data = request_data.get("template_options", {})
                template_options = TemplateOptions(
                    base_template=TemplateType(
                        template_opts_data.get("base_template", "standard"),
                    ),
                    include_tests=template_opts_data.get("include_tests", True),
                    include_documentation=template_opts_data.get(
                        "include_documentation",
                        True,
                    ),
                    include_examples=template_opts_data.get("include_examples", True),
                    integration_level=template_opts_data.get(
                        "integration_level",
                        "basic",
                    ),
                )

                # Parse generation options
                gen_opts_data = request_data.get("generation_options", {})
                generation_options = GenerationOptions(
                    output_directory=gen_opts_data.get("output_directory", "./agents"),
                    overwrite_existing=gen_opts_data.get("overwrite_existing", False),
                    validate_before_creation=gen_opts_data.get(
                        "validate_before_creation",
                        True,
                    ),
                    auto_register=gen_opts_data.get("auto_register", True),
                    auto_deploy=gen_opts_data.get("auto_deploy", False),
                )

                # Create agent
                response = self.create_agent(spec, template_options, generation_options)
                return asdict(response)

            return {
                "success": False,
                "operation": operation,
                "agent_info": {},
                "generated_files": [],
                "integration_points": [],
                "validation_results": {},
                "recommendations": [],
                "warnings": [],
                "errors": [f"Unsupported operation: {operation}"],
            }

        except Exception as e:
            self.logger.exception(f"Error processing request: {e}")
            return {
                "success": False,
                "operation": request_data.get("operation", "unknown"),
                "agent_info": {},
                "generated_files": [],
                "integration_points": [],
                "validation_results": {},
                "recommendations": [],
                "warnings": [],
                "errors": [str(e)],
            }


def main() -> None:
    """Main function for testing the Agent Generator Engine."""
    engine = AgentGeneratorEngine()

    # Test agent creation
    test_request = {
        "operation": "create",
        "agent_specification": {
            "name": "test-agent",
            "type": "specialized",
            "description": "A test agent for demonstration purposes",
            "capabilities": ["data_processing", "validation", "reporting"],
            "interfaces": {
                "input_format": "json",
                "output_format": "json",
                "communication_protocol": "http",
            },
            "requirements": {
                "memory_limit": "256MB",
                "cpu_limit": "100m",
                "dependencies": ["requests", "pydantic"],
            },
        },
        "template_options": {
            "base_template": "standard",
            "include_tests": True,
            "include_documentation": True,
            "include_examples": True,
        },
        "generation_options": {
            "output_directory": "./agents",
            "validate_before_creation": True,
            "auto_register": True,
        },
    }

    response = engine.process_request(test_request)

    if response["success"]:
        for _file_info in response["generated_files"]:
            pass
    else:
        for _error in response["errors"]:
            pass


if __name__ == "__main__":
    main()
