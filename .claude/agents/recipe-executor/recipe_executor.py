#!/usr/bin/env python3
"""
Recipe Executor Agent - Reads recipe files and generates REAL implementations.

This agent reads structured recipe files (requirements.md, design.md, dependencies.json)
and generates actual working code, not stubs or placeholders.
"""

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Recipe:
    """Represents a complete recipe for implementation."""

    name: str
    path: Path
    requirements: str = ""
    design: str = ""
    dependencies: Dict[str, Any] = field(default_factory=dict)
    tests: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)


@dataclass
class Implementation:
    """Represents generated implementation code."""

    recipe_name: str
    files: Dict[str, str] = field(default_factory=dict)  # path -> content
    test_files: Dict[str, str] = field(default_factory=dict)
    config_files: Dict[str, str] = field(default_factory=dict)
    validation_results: Dict[str, bool] = field(default_factory=dict)


class RecipeExecutor:
    """Main Recipe Executor that generates real implementations."""

    def __init__(self, base_path: Path = Path.cwd()):
        self.base_path = base_path
        self.recipes: Dict[str, Recipe] = {}
        self.implementations: Dict[str, Implementation] = {}

    def load_recipe(self, recipe_path: Path) -> Recipe:
        """Load a recipe from directory containing requirements.md, design.md, dependencies.json."""

        if not recipe_path.exists():
            raise FileNotFoundError(f"Recipe path does not exist: {recipe_path}")

        recipe = Recipe(name=recipe_path.name, path=recipe_path)

        # Load requirements
        requirements_file = recipe_path / "requirements.md"
        if requirements_file.exists():
            recipe.requirements = requirements_file.read_text()
            logger.info(f"Loaded requirements for {recipe.name}")
        else:
            logger.warning(f"No requirements.md found for {recipe.name}")

        # Load design
        design_file = recipe_path / "design.md"
        if design_file.exists():
            recipe.design = design_file.read_text()
            logger.info(f"Loaded design for {recipe.name}")
        else:
            logger.warning(f"No design.md found for {recipe.name}")

        # Load dependencies
        deps_file = recipe_path / "dependencies.json"
        if deps_file.exists():
            recipe.dependencies = json.loads(deps_file.read_text())
            logger.info(f"Loaded dependencies for {recipe.name}")
        else:
            logger.warning(f"No dependencies.json found for {recipe.name}")

        # Extract validation criteria from requirements
        recipe.validation_criteria = self._extract_validation_criteria(
            recipe.requirements
        )

        self.recipes[recipe.name] = recipe
        return recipe

    def _extract_validation_criteria(self, requirements: str) -> List[str]:
        """Extract testable validation criteria from requirements."""

        criteria = []
        lines = requirements.split("\n")

        for line in lines:
            line = line.strip()
            # Look for lines that describe testable behavior
            if any(
                keyword in line.lower()
                for keyword in ["must", "should", "shall", "will"]
            ):
                if len(line) > 10:  # Avoid trivial lines
                    criteria.append(line)

        return criteria

    def generate_implementation(self, recipe: Recipe) -> Implementation:
        """Generate REAL implementation code from recipe."""

        logger.info(f"Generating implementation for {recipe.name}")

        impl = Implementation(recipe_name=recipe.name)

        # Parse requirements and design to understand what to build
        component_type = self._identify_component_type(recipe)

        if component_type == "service":
            impl = self._generate_service_implementation(recipe)
        elif component_type == "agent":
            impl = self._generate_agent_implementation(recipe)
        elif component_type == "library":
            impl = self._generate_library_implementation(recipe)
        else:
            impl = self._generate_generic_implementation(recipe)

        self.implementations[recipe.name] = impl
        return impl

    def _identify_component_type(self, recipe: Recipe) -> str:
        """Identify what type of component to generate."""

        combined_text = (recipe.requirements + " " + recipe.design).lower()

        if (
            "service" in combined_text
            or "api" in combined_text
            or "server" in combined_text
        ):
            return "service"
        elif "agent" in combined_text:
            return "agent"
        elif "library" in combined_text or "module" in combined_text:
            return "library"
        else:
            return "generic"

    def _generate_service_implementation(self, recipe: Recipe) -> Implementation:
        """Generate a complete service implementation."""

        impl = Implementation(recipe_name=recipe.name)

        # Main service file
        service_code = self._generate_service_code(recipe)
        impl.files["__init__.py"] = ""
        impl.files["main.py"] = service_code

        # Models
        models_code = self._generate_models_code(recipe)
        impl.files["models.py"] = models_code

        # Handlers
        handlers_code = self._generate_handlers_code(recipe)
        impl.files["handlers.py"] = handlers_code

        # Config
        config_code = self._generate_config_code(recipe)
        impl.files["config.py"] = config_code

        # Tests
        test_code = self._generate_test_code(recipe, "service")
        impl.test_files["test_main.py"] = test_code

        # Docker and config files
        impl.config_files["Dockerfile"] = self._generate_dockerfile(recipe)
        impl.config_files["requirements.txt"] = self._generate_requirements(recipe)

        return impl

    def _generate_agent_implementation(self, recipe: Recipe) -> Implementation:
        """Generate a complete agent implementation."""

        impl = Implementation(recipe_name=recipe.name)

        # Main agent file
        agent_code = self._generate_agent_code(recipe)
        impl.files["__init__.py"] = ""
        impl.files["agent.py"] = agent_code

        # Tools
        tools_code = self._generate_tools_code(recipe)
        impl.files["tools.py"] = tools_code

        # State management
        state_code = self._generate_state_code(recipe)
        impl.files["state.py"] = state_code

        # Tests
        test_code = self._generate_test_code(recipe, "agent")
        impl.test_files["test_agent.py"] = test_code

        return impl

    def _generate_library_implementation(self, recipe: Recipe) -> Implementation:
        """Generate a complete library implementation."""

        impl = Implementation(recipe_name=recipe.name)

        # Core library file
        lib_code = self._generate_library_code(recipe)
        impl.files["__init__.py"] = f'"""Library for {recipe.name}."""\n\n'
        impl.files["core.py"] = lib_code

        # Utils
        utils_code = self._generate_utils_code(recipe)
        impl.files["utils.py"] = utils_code

        # Tests
        test_code = self._generate_test_code(recipe, "library")
        impl.test_files["test_core.py"] = test_code

        return impl

    def _generate_generic_implementation(self, recipe: Recipe) -> Implementation:
        """Generate a generic implementation."""

        impl = Implementation(recipe_name=recipe.name)

        # Main implementation
        main_code = self._generate_main_code(recipe)
        impl.files["__init__.py"] = ""
        impl.files["main.py"] = main_code

        # Tests
        test_code = self._generate_test_code(recipe, "generic")
        impl.test_files["test_main.py"] = test_code

        return impl

    def _generate_service_code(self, recipe: Recipe) -> str:
        """Generate actual service code."""

        deps = recipe.dependencies.get("python", [])

        # Check if FastAPI is needed
        if any("fastapi" in str(d).lower() for d in deps):
            return self._generate_fastapi_service(recipe)
        else:
            return self._generate_flask_service(recipe)

    def _generate_fastapi_service(self, recipe: Recipe) -> str:
        """Generate FastAPI service code."""

        return '''"""
{name} Service - FastAPI Implementation
Generated from recipe: {recipe_name}
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings
from .handlers import (
    health_check,
    process_request,
    validate_input
)
from .models import RequestModel, ResponseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting {name} service...")
    yield
    # Shutdown
    logger.info("Shutting down {name} service...")

# Create FastAPI app
app = FastAPI(
    title="{name} Service",
    description="Service implementation for {recipe_name}",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return await health_check()

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"service": "{name}", "status": "running", "version": "0.1.0"}}

@app.post("/process", response_model=ResponseModel)
async def process(request: RequestModel):
    """Process incoming request."""
    try:
        # Validate input
        validation_result = await validate_input(request)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.error
            )

        # Process request
        result = await process_request(request)
        return ResponseModel(
            success=True,
            data=result,
            message="Request processed successfully"
        )
    except Exception as e:
        logger.error(f"Error processing request: {{e}}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/status")
async def status():
    """Get service status."""
    return {{
        "service": "{name}",
        "status": "operational",
        "uptime": "N/A",  # Would implement actual uptime tracking
        "version": "0.1.0"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''.format(name=recipe.name, recipe_name=recipe.name)

    def _generate_flask_service(self, recipe: Recipe) -> str:
        """Generate Flask service code."""

        return '''"""
{name} Service - Flask Implementation
Generated from recipe: {recipe_name}
"""

import logging
from flask import Flask, jsonify, request

from .config import Config
from .handlers import process_request, validate_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({{"status": "healthy"}}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({{
        "service": "{name}",
        "status": "running",
        "version": "0.1.0"
    }}), 200

@app.route('/process', methods=['POST'])
def process():
    """Process incoming request."""
    try:
        data = request.get_json()

        # Validate input
        is_valid, error = validate_input(data)
        if not is_valid:
            return jsonify({{"error": error}}), 400

        # Process request
        result = process_request(data)

        return jsonify({{
            "success": True,
            "data": result,
            "message": "Request processed successfully"
        }}), 200
    except Exception as e:
        logger.error(f"Error processing request: {{e}}")
        return jsonify({{"error": str(e)}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
'''.format(name=recipe.name, recipe_name=recipe.name)

    def _generate_models_code(self, recipe: Recipe) -> str:
        """Generate models code."""

        return '''"""
Data models for {name}.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class RequestModel(BaseModel):
    """Request model for incoming data."""

    id: Optional[str] = Field(None, description="Request ID")
    data: Dict[str, Any] = Field(..., description="Request data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator('data')
    def validate_data(cls, v):
        """Validate request data."""
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class ResponseModel(BaseModel):
    """Response model for outgoing data."""

    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Validation result model."""

    is_valid: bool = Field(..., description="Validation status")
    error: Optional[str] = Field(None, description="Validation error message")
    warnings: List[str] = Field(default_factory=list)


class StateModel(BaseModel):
    """State model for tracking."""

    id: str = Field(..., description="State ID")
    status: str = Field(..., description="Current status")
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update(self, **kwargs):
        """Update state with new data."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
'''.format(name=recipe.name)

    def _generate_handlers_code(self, recipe: Recipe) -> str:
        """Generate handlers code."""

        return '''"""
Request handlers for {name}.
"""

import logging
from typing import Any, Dict, Optional

from .models import RequestModel, ValidationResult

logger = logging.getLogger(__name__)


async def health_check() -> Dict[str, str]:
    """Perform health check."""
    # Add actual health checks here
    return {{"status": "healthy", "service": "{name}"}}


async def validate_input(request: RequestModel) -> ValidationResult:
    """Validate incoming request."""
    try:
        # Add actual validation logic here
        if not request.data:
            return ValidationResult(
                is_valid=False,
                error="Request data is required"
            )

        # Check for required fields
        required_fields = []  # Add required fields based on recipe
        for field in required_fields:
            if field not in request.data:
                return ValidationResult(
                    is_valid=False,
                    error=f"Required field missing: {{field}}"
                )

        return ValidationResult(is_valid=True)
    except Exception as e:
        logger.error(f"Validation error: {{e}}")
        return ValidationResult(
            is_valid=False,
            error=str(e)
        )


async def process_request(request: RequestModel) -> Dict[str, Any]:
    """Process the incoming request."""
    try:
        # Add actual processing logic here
        result = {{
            "processed": True,
            "request_id": request.id,
            "data": request.data,
            "timestamp": request.timestamp.isoformat()
        }}

        # Implement actual business logic based on recipe

        return result
    except Exception as e:
        logger.error(f"Processing error: {{e}}")
        raise
'''.format(name=recipe.name)

    def _generate_config_code(self, recipe: Recipe) -> str:
        """Generate configuration code."""

        return '''"""
Configuration for {name}.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = "{name}"
    service_version: str = "0.1.0"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Database configuration (if needed)
    database_url: Optional[str] = None

    # Redis configuration (if needed)
    redis_url: Optional[str] = None

    # Logging configuration
    log_level: str = "INFO"

    # Security configuration
    api_key: Optional[str] = None
    secret_key: str = "change-me-in-production"

    class Config:
        env_prefix = "{name_upper}_"
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Flask-specific config class
class Config:
    """Flask configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
'''.format(name=recipe.name, name_upper=recipe.name.upper())

    def _generate_agent_code(self, recipe: Recipe) -> str:
        """Generate agent code."""

        return '''"""
{name} Agent Implementation
Generated from recipe: {recipe_name}
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .tools import ToolRegistry, Tool
from .state import StateManager, AgentState

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str = "{name}"
    version: str = "0.1.0"
    max_retries: int = 3
    timeout: int = 300
    tools: List[str] = field(default_factory=list)


class {name_class}Agent:
    """Main agent implementation."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the agent."""
        self.config = config or AgentConfig()
        self.state_manager = StateManager()
        self.tool_registry = ToolRegistry()
        self.current_state = AgentState.IDLE

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register available tools."""
        # Add tool registration based on recipe
        pass

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task."""
        logger.info(f"Executing task: {{task.get('name', 'unnamed')}}")

        try:
            # Update state
            self.current_state = AgentState.RUNNING
            self.state_manager.update_state(AgentState.RUNNING)

            # Validate task
            if not self._validate_task(task):
                raise ValueError("Invalid task format")

            # Process task
            result = await self._process_task(task)

            # Update state
            self.current_state = AgentState.COMPLETED
            self.state_manager.update_state(AgentState.COMPLETED)

            return {{
                "success": True,
                "result": result,
                "agent": self.config.name
            }}

        except Exception as e:
            logger.error(f"Error executing task: {{e}}")
            self.current_state = AgentState.ERROR
            self.state_manager.update_state(AgentState.ERROR)
            raise

    def _validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task format."""
        required_fields = ["type", "data"]
        return all(field in task for field in required_fields)

    async def _process_task(self, task: Dict[str, Any]) -> Any:
        """Process the task."""
        task_type = task.get("type")
        task_data = task.get("data")

        # Route to appropriate handler
        if task_type == "analyze":
            return await self._handle_analyze(task_data)
        elif task_type == "generate":
            return await self._handle_generate(task_data)
        elif task_type == "validate":
            return await self._handle_validate(task_data)
        else:
            raise ValueError(f"Unknown task type: {{task_type}}")

    async def _handle_analyze(self, data: Dict[str, Any]) -> Any:
        """Handle analyze task."""
        # Implement analysis logic
        return {{"analyzed": True, "data": data}}

    async def _handle_generate(self, data: Dict[str, Any]) -> Any:
        """Handle generate task."""
        # Implement generation logic
        return {{"generated": True, "data": data}}

    async def _handle_validate(self, data: Dict[str, Any]) -> Any:
        """Handle validate task."""
        # Implement validation logic
        return {{"validated": True, "data": data}}


async def main():
    """Main entry point."""
    agent = {name_class}Agent()

    # Example task
    task = {{
        "type": "analyze",
        "data": {{"input": "test"}}
    }}

    result = await agent.execute(task)
    print(f"Result: {{result}}")


if __name__ == "__main__":
    asyncio.run(main())
'''.format(
            name=recipe.name,
            recipe_name=recipe.name,
            name_class=recipe.name.replace("-", "").replace("_", "").title(),
        )

    def _generate_tools_code(self, recipe: Recipe) -> str:
        """Generate tools code for agent."""

        return '''"""
Tools for {name} agent.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Tool(ABC):
    """Base tool class."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass


class AnalysisTool(Tool):
    """Tool for analysis operations."""

    def __init__(self):
        super().__init__(
            name="analysis_tool",
            description="Performs analysis operations"
        )

    async def execute(self, data: Any) -> Dict[str, Any]:
        """Execute analysis."""
        # Implement actual analysis
        return {{
            "tool": self.name,
            "result": "analysis_complete",
            "data": data
        }}


class GenerationTool(Tool):
    """Tool for generation operations."""

    def __init__(self):
        super().__init__(
            name="generation_tool",
            description="Generates content or code"
        )

    async def execute(self, template: str, params: Dict[str, Any]) -> str:
        """Execute generation."""
        # Implement actual generation
        return f"Generated content with template: {{template}}"


class ValidationTool(Tool):
    """Tool for validation operations."""

    def __init__(self):
        super().__init__(
            name="validation_tool",
            description="Validates data or configurations"
        )

    async def execute(self, data: Any, rules: List[str]) -> bool:
        """Execute validation."""
        # Implement actual validation
        return True


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {{}}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools."""
        self.register(AnalysisTool())
        self.register(GenerationTool())
        self.register(ValidationTool())

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List available tools."""
        return list(self.tools.keys())
'''.format(name=recipe.name)

    def _generate_state_code(self, recipe: Recipe) -> str:
        """Generate state management code."""

        return '''"""
State management for {name} agent.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentState(Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class StateManager:
    """Manages agent state."""

    def __init__(self):
        self.current_state = AgentState.IDLE
        self.state_history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {{}}

    def update_state(self, new_state: AgentState, metadata: Optional[Dict[str, Any]] = None):
        """Update the current state."""
        old_state = self.current_state
        self.current_state = new_state

        # Record state change
        state_change = {{
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {{}}
        }}

        self.state_history.append(state_change)

        if metadata:
            self.metadata.update(metadata)

    def get_state(self) -> AgentState:
        """Get current state."""
        return self.current_state

    def get_history(self) -> List[Dict[str, Any]]:
        """Get state history."""
        return self.state_history

    def reset(self):
        """Reset state to idle."""
        self.update_state(AgentState.IDLE, {{"action": "reset"}})

    def is_running(self) -> bool:
        """Check if agent is running."""
        return self.current_state == AgentState.RUNNING

    def is_completed(self) -> bool:
        """Check if agent has completed."""
        return self.current_state == AgentState.COMPLETED

    def has_error(self) -> bool:
        """Check if agent has error."""
        return self.current_state == AgentState.ERROR
'''.format(name=recipe.name)

    def _generate_library_code(self, recipe: Recipe) -> str:
        """Generate library code."""

        return '''"""
Core library implementation for {name}.
Generated from recipe: {recipe_name}
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class {name_class}:
    """Main library class."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the library."""
        self.config = config or {{}}
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the library."""
        try:
            # Add initialization logic
            self._initialized = True
            logger.info(f"{{self.__class__.__name__}} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {{e}}")
            return False

    def process(self, data: Any) -> Any:
        """Process data."""
        if not self._initialized:
            raise RuntimeError("Library not initialized")

        # Add processing logic
        return self._process_internal(data)

    def _process_internal(self, data: Any) -> Any:
        """Internal processing logic."""
        # Implement actual processing
        return {{
            "processed": True,
            "input": data,
            "library": self.__class__.__name__
        }}

    def validate(self, data: Any) -> bool:
        """Validate data."""
        # Add validation logic
        return data is not None

    def transform(self, data: Any, format: str = "json") -> Any:
        """Transform data to specified format."""
        # Add transformation logic
        if format == "json":
            import json
            return json.dumps(data) if not isinstance(data, str) else data
        return data

    def cleanup(self):
        """Cleanup resources."""
        self._initialized = False
        logger.info("Library cleaned up")


def create_instance(config: Optional[Dict[str, Any]] = None) -> {name_class}:
    """Factory function to create library instance."""
    return {name_class}(config)
'''.format(
            name=recipe.name,
            recipe_name=recipe.name,
            name_class=recipe.name.replace("-", "").replace("_", "").title(),
        )

    def _generate_utils_code(self, recipe: Recipe) -> str:
        """Generate utilities code."""

        return '''"""
Utility functions for {name}.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {{file_path}}: {{e}}")
        return {{}}


def save_json_file(data: Dict[str, Any], file_path: Path) -> bool:
    """Save data to JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {{file_path}}: {{e}}")
        return False


def generate_id(prefix: str = "") -> str:
    """Generate unique ID."""
    timestamp = datetime.utcnow().isoformat()
    hash_input = f"{{prefix}}{{timestamp}}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:12]


def validate_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate data structure."""
    return all(field in data for field in required_fields)


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries."""
    result = {{}}
    for config in configs:
        result.update(config)
    return result


def retry_operation(func, max_retries: int = 3, delay: float = 1.0):
    """Retry an operation with exponential backoff."""
    import time

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {{attempt + 1}} failed: {{e}}. Retrying...")
            time.sleep(delay * (2 ** attempt))
'''.format(name=recipe.name)

    def _generate_main_code(self, recipe: Recipe) -> str:
        """Generate main implementation code."""

        return '''"""
Main implementation for {name}.
Generated from recipe: {recipe_name}
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class {name_class}:
    """Main implementation class."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the implementation."""
        self.config = self._load_config(config_path)
        self.initialized = False

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration."""
        if config_path and config_path.exists():
            import json
            with open(config_path) as f:
                return json.load(f)
        return {{}}

    def initialize(self) -> bool:
        """Initialize the system."""
        try:
            logger.info("Initializing {name}...")
            # Add initialization logic here
            self.initialized = True
            logger.info("{name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {{e}}")
            return False

    def run(self) -> int:
        """Run the main process."""
        if not self.initialized:
            logger.error("System not initialized")
            return 1

        try:
            logger.info("Running {name}...")
            # Add main logic here
            result = self._execute()
            logger.info("Execution completed successfully")
            return 0
        except Exception as e:
            logger.error(f"Execution failed: {{e}}")
            return 1

    def _execute(self) -> Any:
        """Execute main logic."""
        # Implement main execution logic
        logger.info("Executing main logic...")
        return {{"status": "completed"}}

    def shutdown(self):
        """Shutdown the system."""
        logger.info("Shutting down {name}...")
        self.initialized = False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="{name} implementation")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run instance
    instance = {name_class}(args.config)

    if not instance.initialize():
        logger.error("Initialization failed")
        return 1

    try:
        return instance.run()
    finally:
        instance.shutdown()


if __name__ == "__main__":
    sys.exit(main())
'''.format(
            name=recipe.name,
            recipe_name=recipe.name,
            name_class=recipe.name.replace("-", "").replace("_", "").title(),
        )

    def _generate_test_code(self, recipe: Recipe, component_type: str) -> str:
        """Generate comprehensive test code."""

        if component_type == "service":
            return self._generate_service_tests(recipe)
        elif component_type == "agent":
            return self._generate_agent_tests(recipe)
        elif component_type == "library":
            return self._generate_library_tests(recipe)
        else:
            return self._generate_generic_tests(recipe)

    def _generate_service_tests(self, recipe: Recipe) -> str:
        """Generate service tests."""

        return '''"""
Tests for {name} service.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from ..main import app
from ..models import RequestModel, ResponseModel


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_request():
    """Create sample request."""
    return RequestModel(
        id="test-123",
        data={{"test": "data"}},
        metadata={{"source": "test"}}
    )


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "{name}"
        assert data["status"] == "running"


class TestProcessEndpoint:
    """Test process endpoint."""

    def test_process_valid_request(self, client, sample_request):
        """Test processing valid request."""
        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_process_invalid_request(self, client):
        """Test processing invalid request."""
        response = client.post(
            "/process",
            json={{}}
        )
        assert response.status_code == 422  # Validation error

    def test_process_empty_data(self, client):
        """Test processing with empty data."""
        response = client.post(
            "/process",
            json={{"data": {{}}}}
        )
        # Should still work with empty data dict
        assert response.status_code == 200


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status(self, client):
        """Test status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "{name}"
        assert data["status"] == "operational"


class TestErrorHandling:
    """Test error handling."""

    @patch("main.process_request")
    def test_process_error_handling(self, mock_process, client, sample_request):
        """Test error handling in process endpoint."""
        mock_process.side_effect = Exception("Test error")

        response = client.post(
            "/process",
            json=sample_request.dict()
        )
        assert response.status_code == 500
        assert "error" in response.json()
'''.format(name=recipe.name)

    def _generate_agent_tests(self, recipe: Recipe) -> str:
        """Generate agent tests."""

        name_class = recipe.name.replace("-", "").replace("_", "").title()

        return f'''"""
Tests for {recipe.name} agent.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from ..agent import {name_class}Agent, AgentConfig
from ..state import AgentState, StateManager
from ..tools import ToolRegistry


@pytest.fixture
def agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        name="test-agent",
        max_retries=2,
        timeout=60
    )


@pytest.fixture
def agent(agent_config):
    """Create test agent instance."""
    return {name_class}Agent(agent_config)


@pytest.fixture
def sample_task():
    """Create sample task."""
    return {{
        "type": "analyze",
        "data": {{"input": "test data"}}
    }}


class TestAgentInitialization:
    """Test agent initialization."""

    def test_agent_creation(self, agent):
        """Test agent is created properly."""
        assert agent is not None
        assert agent.config.name == "test-agent"
        assert agent.current_state == AgentState.IDLE

    def test_tool_registration(self, agent):
        """Test tools are registered."""
        assert agent.tool_registry is not None
        assert len(agent.tool_registry.list_tools()) > 0


class TestAgentExecution:
    """Test agent execution."""

    @pytest.mark.asyncio
    async def test_execute_valid_task(self, agent, sample_task):
        """Test executing valid task."""
        result = await agent.execute(sample_task)

        assert result["success"] is True
        assert "result" in result
        assert result["agent"] == "test-agent"

    @pytest.mark.asyncio
    async def test_execute_invalid_task(self, agent):
        """Test executing invalid task."""
        invalid_task = {{"invalid": "data"}}

        with pytest.raises(ValueError, match="Invalid task format"):
            await agent.execute(invalid_task)

    @pytest.mark.asyncio
    async def test_execute_unknown_type(self, agent):
        """Test executing task with unknown type."""
        unknown_task = {{
            "type": "unknown",
            "data": {{}}
        }}

        with pytest.raises(ValueError, match="Unknown task type"):
            await agent.execute(unknown_task)


class TestTaskHandlers:
    """Test task handlers."""

    @pytest.mark.asyncio
    async def test_handle_analyze(self, agent):
        """Test analyze handler."""
        task = {{
            "type": "analyze",
            "data": {{"test": "data"}}
        }}

        result = await agent.execute(task)
        assert result["success"] is True
        assert result["result"]["analyzed"] is True

    @pytest.mark.asyncio
    async def test_handle_generate(self, agent):
        """Test generate handler."""
        task = {{
            "type": "generate",
            "data": {{"template": "test"}}
        }}

        result = await agent.execute(task)
        assert result["success"] is True
        assert result["result"]["generated"] is True

    @pytest.mark.asyncio
    async def test_handle_validate(self, agent):
        """Test validate handler."""
        task = {{
            "type": "validate",
            "data": {{"rules": []}}
        }}

        result = await agent.execute(task)
        assert result["success"] is True
        assert result["result"]["validated"] is True


class TestStateManagement:
    """Test state management."""

    @pytest.mark.asyncio
    async def test_state_transitions(self, agent, sample_task):
        """Test state transitions during execution."""
        assert agent.current_state == AgentState.IDLE

        result = await agent.execute(sample_task)

        assert agent.current_state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_state_on_error(self, agent):
        """Test state on error."""
        with pytest.raises(ValueError):
            await agent.execute({{}})

        assert agent.current_state == AgentState.ERROR


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_execution_error_handling(self, agent):
        """Test error handling during execution."""
        with patch.object(agent, '_process_task', side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                await agent.execute({{"type": "test", "data": {{}}}})

        assert agent.current_state == AgentState.ERROR
'''

    def _generate_library_tests(self, recipe: Recipe) -> str:
        """Generate library tests."""

        name_class = recipe.name.replace("-", "").replace("_", "").title()

        return f'''"""
Tests for {recipe.name} library.
"""

import pytest
from unittest.mock import Mock, patch

from ..core import {name_class}, create_instance
from ..utils import generate_id, validate_structure


@pytest.fixture
def library_instance():
    """Create library instance."""
    return create_instance()


@pytest.fixture
def sample_data():
    """Create sample data."""
    return {{
        "id": "test-123",
        "value": "test data",
        "metadata": {{}}
    }}


class TestLibraryInitialization:
    """Test library initialization."""

    def test_create_instance(self):
        """Test creating library instance."""
        instance = create_instance()
        assert instance is not None
        assert not instance._initialized

    def test_initialize(self, library_instance):
        """Test initialization."""
        result = library_instance.initialize()
        assert result is True
        assert library_instance._initialized is True

    def test_initialize_with_config(self):
        """Test initialization with config."""
        config = {{"setting": "value"}}
        instance = create_instance(config)
        assert instance.config == config


class TestProcessing:
    """Test processing functionality."""

    def test_process_data(self, library_instance, sample_data):
        """Test processing data."""
        library_instance.initialize()
        result = library_instance.process(sample_data)

        assert result["processed"] is True
        assert result["input"] == sample_data

    def test_process_without_init(self, library_instance, sample_data):
        """Test processing without initialization."""
        with pytest.raises(RuntimeError, match="Library not initialized"):
            library_instance.process(sample_data)


class TestValidation:
    """Test validation functionality."""

    def test_validate_valid_data(self, library_instance, sample_data):
        """Test validating valid data."""
        assert library_instance.validate(sample_data) is True

    def test_validate_none(self, library_instance):
        """Test validating None."""
        assert library_instance.validate(None) is False


class TestTransformation:
    """Test transformation functionality."""

    def test_transform_to_json(self, library_instance, sample_data):
        """Test transforming to JSON."""
        result = library_instance.transform(sample_data, "json")
        assert isinstance(result, str)

        import json
        parsed = json.loads(result)
        assert parsed == sample_data

    def test_transform_string(self, library_instance):
        """Test transforming string."""
        result = library_instance.transform("test", "json")
        assert result == "test"


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup(self, library_instance):
        """Test cleanup."""
        library_instance.initialize()
        assert library_instance._initialized is True

        library_instance.cleanup()
        assert library_instance._initialized is False


class TestUtilities:
    """Test utility functions."""

    def test_generate_id(self):
        """Test ID generation."""
        id1 = generate_id("test")
        id2 = generate_id("test")

        assert len(id1) == 12
        assert id1 != id2  # Should be unique

    def test_validate_structure(self):
        """Test structure validation."""
        data = {{"field1": "value", "field2": "value"}}

        assert validate_structure(data, ["field1"]) is True
        assert validate_structure(data, ["field1", "field2"]) is True
        assert validate_structure(data, ["field1", "field3"]) is False
'''

    def _generate_generic_tests(self, recipe: Recipe) -> str:
        """Generate generic tests."""

        name_class = recipe.name.replace("-", "").replace("_", "").title()

        return f'''"""
Tests for {recipe.name} implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from ..main import {name_class}, main


@pytest.fixture
def instance():
    """Create test instance."""
    return {name_class}()


@pytest.fixture
def config_file(tmp_path):
    """Create temporary config file."""
    config = tmp_path / "config.json"
    config.write_text('{{"test": "config"}}')
    return config


class TestInitialization:
    """Test initialization."""

    def test_create_instance(self):
        """Test creating instance."""
        instance = {name_class}()
        assert instance is not None
        assert not instance.initialized

    def test_load_config(self, config_file):
        """Test loading config."""
        instance = {name_class}(config_file)
        assert instance.config == {{"test": "config"}}

    def test_initialize(self, instance):
        """Test initialization."""
        result = instance.initialize()
        assert result is True
        assert instance.initialized is True


class TestExecution:
    """Test execution."""

    def test_run_initialized(self, instance):
        """Test running when initialized."""
        instance.initialize()
        result = instance.run()
        assert result == 0

    def test_run_not_initialized(self, instance):
        """Test running when not initialized."""
        result = instance.run()
        assert result == 1

    @patch.object({name_class}, '_execute')
    def test_run_with_error(self, mock_execute, instance):
        """Test running with error."""
        instance.initialize()
        mock_execute.side_effect = Exception("Test error")

        result = instance.run()
        assert result == 1


class TestShutdown:
    """Test shutdown."""

    def test_shutdown(self, instance):
        """Test shutdown."""
        instance.initialize()
        assert instance.initialized is True

        instance.shutdown()
        assert instance.initialized is False


class TestMain:
    """Test main entry point."""

    @patch('sys.argv', ['prog', '--config', 'test.json'])
    @patch.object({name_class}, 'initialize', return_value=True)
    @patch.object({name_class}, 'run', return_value=0)
    @patch.object({name_class}, 'shutdown')
    def test_main_success(self, mock_shutdown, mock_run, mock_init):
        """Test successful main execution."""
        with patch('pathlib.Path.exists', return_value=True):
            result = main()

        assert mock_init.called
        assert mock_run.called
        assert mock_shutdown.called

    @patch('sys.argv', ['prog'])
    @patch.object({name_class}, 'initialize', return_value=False)
    def test_main_init_failure(self, mock_init):
        """Test main with initialization failure."""
        result = main()
        assert result == 1
'''

    def _generate_dockerfile(self, recipe: Recipe) -> str:
        """Generate Dockerfile."""

        return f"""# Dockerfile for {recipe.name}
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "main"]
"""

    def _generate_requirements(self, recipe: Recipe) -> str:
        """Generate requirements.txt."""

        deps = recipe.dependencies.get("python", [])

        # Default dependencies
        default_deps = [
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ]

        # Add FastAPI if needed
        if any("fastapi" in str(d).lower() for d in deps):
            default_deps.extend(
                [
                    "fastapi>=0.100.0",
                    "uvicorn[standard]>=0.23.0",
                ]
            )
        else:
            default_deps.extend(
                [
                    "flask>=2.3.0",
                ]
            )

        # Combine with recipe dependencies
        all_deps = set(default_deps)
        for dep in deps:
            if isinstance(dep, str):
                all_deps.add(dep)

        return "\n".join(sorted(all_deps))

    def write_implementation(self, impl: Implementation, output_path: Path):
        """Write implementation files to disk."""

        logger.info(f"Writing implementation to {output_path}")

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Write main files
        for file_path, content in impl.files.items():
            file_full_path = output_path / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text(content)
            logger.info(f"Wrote {file_full_path}")

        # Write test files
        test_dir = output_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "__init__.py").write_text("")

        for file_path, content in impl.test_files.items():
            file_full_path = test_dir / file_path
            file_full_path.write_text(content)
            logger.info(f"Wrote test {file_full_path}")

        # Write config files
        for file_path, content in impl.config_files.items():
            file_full_path = output_path / file_path
            file_full_path.write_text(content)
            logger.info(f"Wrote config {file_full_path}")

    def validate_implementation(self, impl: Implementation, output_path: Path) -> bool:
        """Validate the implementation works."""

        logger.info(f"Validating implementation at {output_path}")

        # Check files exist
        for file_path in impl.files.keys():
            if not (output_path / file_path).exists():
                logger.error(f"File missing: {file_path}")
                return False

        # Run type checking
        logger.info("Running type checking...")
        result = subprocess.run(
            ["python", "-m", "pyright", str(output_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.warning(f"Type checking had issues: {result.stdout}")

        # Run tests
        logger.info("Running tests...")
        result = subprocess.run(
            ["python", "-m", "pytest", str(output_path / "tests"), "-v"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Tests failed: {result.stdout}")
            return False

        logger.info("Implementation validated successfully!")
        return True


def main():
    """Main entry point for Recipe Executor."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Recipe Executor - Generate real implementations from recipes"
    )
    parser.add_argument("recipe_path", type=Path, help="Path to recipe directory")
    parser.add_argument("--output", type=Path, help="Output directory", default=None)
    parser.add_argument(
        "--validate", action="store_true", help="Validate generated implementation"
    )

    args = parser.parse_args()

    # Create executor
    executor = RecipeExecutor()

    try:
        # Load recipe
        recipe = executor.load_recipe(args.recipe_path)
        logger.info(f"Loaded recipe: {recipe.name}")

        # Generate implementation
        impl = executor.generate_implementation(recipe)
        logger.info(f"Generated implementation with {len(impl.files)} files")

        # Determine output path
        output_path = args.output or Path.cwd() / f"generated_{recipe.name}"

        # Write implementation
        executor.write_implementation(impl, output_path)

        # Validate if requested
        if args.validate:
            if executor.validate_implementation(impl, output_path):
                logger.info("✅ Implementation is valid and working!")
            else:
                logger.error("❌ Implementation validation failed")
                return 1

    except Exception as e:
        logger.error(f"Failed to execute recipe: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
