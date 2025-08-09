"""
Comprehensive tests for Recipe Executor Agent.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from recipe_executor import RecipeExecutor, Recipe, Implementation


@pytest.fixture
def temp_recipe_dir(tmp_path):
    """Create a temporary recipe directory with files."""
    recipe_dir = tmp_path / "test-recipe"
    recipe_dir.mkdir()
    
    # Create requirements.md
    requirements = recipe_dir / "requirements.md"
    requirements.write_text("""# Test Service Requirements

## Functional Requirements
- The service MUST provide a REST API
- The service SHALL handle JSON requests
- The service MUST include health checks
- The service SHOULD support async operations

## Non-Functional Requirements
- Response time must be under 100ms
- Service should handle 1000 req/s
""")
    
    # Create design.md
    design = recipe_dir / "design.md"
    design.write_text("""# Test Service Design

## Architecture
- FastAPI-based service
- Async request handling
- PostgreSQL for persistence
- Redis for caching

## Components
1. API Layer - FastAPI routes
2. Business Logic - Core processing
3. Data Layer - Database models
""")
    
    # Create dependencies.json
    deps = recipe_dir / "dependencies.json"
    deps.write_text(json.dumps({
        "python": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "sqlalchemy>=2.0.0",
            "redis>=4.5.0"
        ],
        "system": ["postgresql", "redis"]
    }))
    
    return recipe_dir


@pytest.fixture
def executor():
    """Create Recipe Executor instance."""
    return RecipeExecutor()


class TestRecipeLoading:
    """Test recipe loading functionality."""
    
    def test_load_complete_recipe(self, executor, temp_recipe_dir):
        """Test loading a complete recipe."""
        recipe = executor.load_recipe(temp_recipe_dir)
        
        assert recipe.name == "test-recipe"
        assert recipe.path == temp_recipe_dir
        assert "REST API" in recipe.requirements
        assert "FastAPI" in recipe.design
        assert "fastapi" in str(recipe.dependencies)
        
    def test_load_recipe_missing_files(self, executor, tmp_path):
        """Test loading recipe with missing files."""
        recipe_dir = tmp_path / "incomplete-recipe"
        recipe_dir.mkdir()
        
        # Only create requirements.md
        (recipe_dir / "requirements.md").write_text("# Requirements\n- Must work")
        
        recipe = executor.load_recipe(recipe_dir)
        
        assert recipe.name == "incomplete-recipe"
        assert recipe.requirements != ""
        assert recipe.design == ""  # Missing
        assert recipe.dependencies == {}  # Missing
        
    def test_load_nonexistent_recipe(self, executor, tmp_path):
        """Test loading non-existent recipe."""
        with pytest.raises(FileNotFoundError):
            executor.load_recipe(tmp_path / "nonexistent")
            
    def test_extract_validation_criteria(self, executor, temp_recipe_dir):
        """Test extracting validation criteria from requirements."""
        recipe = executor.load_recipe(temp_recipe_dir)
        
        assert len(recipe.validation_criteria) > 0
        
        # Check that MUST/SHALL/SHOULD requirements are captured
        criteria_text = " ".join(recipe.validation_criteria).lower()
        assert "must" in criteria_text or "shall" in criteria_text or "should" in criteria_text


class TestComponentTypeIdentification:
    """Test component type identification."""
    
    def test_identify_service_component(self, executor):
        """Test identifying service component."""
        recipe = Recipe(
            name="test-service",
            path=Path("."),
            requirements="Build a REST API service",
            design="FastAPI-based microservice"
        )
        
        component_type = executor._identify_component_type(recipe)
        assert component_type == "service"
        
    def test_identify_agent_component(self, executor):
        """Test identifying agent component."""
        recipe = Recipe(
            name="test-agent",
            path=Path("."),
            requirements="Build an autonomous agent",
            design="Agent with tool execution"
        )
        
        component_type = executor._identify_component_type(recipe)
        assert component_type == "agent"
        
    def test_identify_library_component(self, executor):
        """Test identifying library component."""
        recipe = Recipe(
            name="test-lib",
            path=Path("."),
            requirements="Build a utility library",
            design="Reusable module for data processing"
        )
        
        component_type = executor._identify_component_type(recipe)
        assert component_type == "library"
        
    def test_identify_generic_component(self, executor):
        """Test identifying generic component."""
        recipe = Recipe(
            name="test-generic",
            path=Path("."),
            requirements="Build something",
            design="Some implementation"
        )
        
        component_type = executor._identify_component_type(recipe)
        assert component_type == "generic"


class TestImplementationGeneration:
    """Test implementation generation."""
    
    def test_generate_service_implementation(self, executor, temp_recipe_dir):
        """Test generating service implementation."""
        recipe = executor.load_recipe(temp_recipe_dir)
        impl = executor.generate_implementation(recipe)
        
        assert impl.recipe_name == "test-recipe"
        assert "main.py" in impl.files
        assert "models.py" in impl.files
        assert "handlers.py" in impl.files
        assert "config.py" in impl.files
        assert "test_main.py" in impl.test_files
        assert "Dockerfile" in impl.config_files
        assert "requirements.txt" in impl.config_files
        
    def test_generate_agent_implementation(self, executor):
        """Test generating agent implementation."""
        recipe = Recipe(
            name="test-agent",
            path=Path("."),
            requirements="Build an agent",
            design="Agent implementation"
        )
        
        impl = executor._generate_agent_implementation(recipe)
        
        assert "agent.py" in impl.files
        assert "tools.py" in impl.files
        assert "state.py" in impl.files
        assert "test_agent.py" in impl.test_files
        
    def test_generate_library_implementation(self, executor):
        """Test generating library implementation."""
        recipe = Recipe(
            name="test-library",
            path=Path("."),
            requirements="Build a library",
            design="Library implementation"
        )
        
        impl = executor._generate_library_implementation(recipe)
        
        assert "__init__.py" in impl.files
        assert "core.py" in impl.files
        assert "utils.py" in impl.files
        assert "test_core.py" in impl.test_files
        
    def test_fastapi_service_generation(self, executor, temp_recipe_dir):
        """Test FastAPI service code generation."""
        recipe = executor.load_recipe(temp_recipe_dir)
        service_code = executor._generate_service_code(recipe)
        
        assert "FastAPI" in service_code
        assert "async def" in service_code
        assert "/health" in service_code
        assert "/process" in service_code
        
    def test_flask_service_generation(self, executor):
        """Test Flask service code generation."""
        recipe = Recipe(
            name="flask-service",
            path=Path("."),
            requirements="Simple service",
            design="Web service",
            dependencies={"python": ["flask"]}
        )
        
        service_code = executor._generate_service_code(recipe)
        
        assert "Flask" in service_code
        assert "@app.route" in service_code
        assert "/health" in service_code


class TestFileWriting:
    """Test writing implementation to disk."""
    
    def test_write_implementation(self, executor, tmp_path):
        """Test writing implementation files."""
        impl = Implementation(
            recipe_name="test-impl",
            files={
                "__init__.py": "# Init file",
                "main.py": "# Main file",
                "subdir/module.py": "# Module in subdir"
            },
            test_files={
                "test_main.py": "# Test file"
            },
            config_files={
                "config.json": '{"key": "value"}'
            }
        )
        
        output_path = tmp_path / "output"
        executor.write_implementation(impl, output_path)
        
        # Check files were written
        assert (output_path / "__init__.py").exists()
        assert (output_path / "main.py").exists()
        assert (output_path / "subdir" / "module.py").exists()
        assert (output_path / "tests" / "test_main.py").exists()
        assert (output_path / "tests" / "__init__.py").exists()
        assert (output_path / "config.json").exists()
        
        # Check content
        assert (output_path / "main.py").read_text() == "# Main file"


class TestValidation:
    """Test implementation validation."""
    
    @patch('subprocess.run')
    def test_validate_implementation_success(self, mock_run, executor, tmp_path):
        """Test successful validation."""
        # Setup mock responses
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
        
        impl = Implementation(
            recipe_name="test",
            files={"main.py": "print('hello')"}
        )
        
        # Write files
        output_path = tmp_path / "test"
        executor.write_implementation(impl, output_path)
        
        # Validate
        result = executor.validate_implementation(impl, output_path)
        
        assert result is True
        assert mock_run.called
        
    @patch('subprocess.run')
    def test_validate_implementation_test_failure(self, mock_run, executor, tmp_path):
        """Test validation with test failures."""
        # First call for pyright succeeds, second for pytest fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="Test failed", stderr="")
        ]
        
        impl = Implementation(
            recipe_name="test",
            files={"main.py": "print('hello')"}
        )
        
        output_path = tmp_path / "test"
        executor.write_implementation(impl, output_path)
        
        result = executor.validate_implementation(impl, output_path)
        
        assert result is False
        
    def test_validate_missing_files(self, executor, tmp_path):
        """Test validation with missing files."""
        impl = Implementation(
            recipe_name="test",
            files={"main.py": "content", "missing.py": "content"}
        )
        
        output_path = tmp_path / "test"
        output_path.mkdir()
        (output_path / "main.py").write_text("content")
        # missing.py is not created
        
        result = executor.validate_implementation(impl, output_path)
        
        assert result is False


class TestEndToEnd:
    """Test end-to-end workflow."""
    
    def test_complete_workflow(self, executor, temp_recipe_dir, tmp_path):
        """Test complete recipe execution workflow."""
        # Load recipe
        recipe = executor.load_recipe(temp_recipe_dir)
        
        # Generate implementation
        impl = executor.generate_implementation(recipe)
        
        # Write to disk
        output_path = tmp_path / "generated"
        executor.write_implementation(impl, output_path)
        
        # Verify structure
        assert (output_path / "main.py").exists()
        assert (output_path / "models.py").exists()
        assert (output_path / "tests" / "test_main.py").exists()
        
        # Check content makes sense
        main_content = (output_path / "main.py").read_text()
        assert "test-recipe" in main_content
        assert "FastAPI" in main_content  # Should use FastAPI based on deps
        
    def test_stored_implementations(self, executor, temp_recipe_dir):
        """Test that implementations are stored in executor."""
        recipe = executor.load_recipe(temp_recipe_dir)
        impl = executor.generate_implementation(recipe)
        
        assert recipe.name in executor.recipes
        assert recipe.name in executor.implementations
        assert executor.implementations[recipe.name] == impl


class TestCodeGeneration:
    """Test specific code generation functions."""
    
    def test_generate_models_code(self, executor):
        """Test models code generation."""
        recipe = Recipe(name="test", path=Path("."))
        code = executor._generate_models_code(recipe)
        
        assert "RequestModel" in code
        assert "ResponseModel" in code
        assert "ValidationResult" in code
        assert "pydantic" in code.lower()
        
    def test_generate_handlers_code(self, executor):
        """Test handlers code generation."""
        recipe = Recipe(name="test", path=Path("."))
        code = executor._generate_handlers_code(recipe)
        
        assert "health_check" in code
        assert "validate_input" in code
        assert "process_request" in code
        assert "async def" in code
        
    def test_generate_config_code(self, executor):
        """Test config code generation."""
        recipe = Recipe(name="test", path=Path("."))
        code = executor._generate_config_code(recipe)
        
        assert "Settings" in code
        assert "BaseSettings" in code
        assert "get_settings" in code
        
    def test_generate_dockerfile(self, executor):
        """Test Dockerfile generation."""
        recipe = Recipe(name="test-service", path=Path("."))
        dockerfile = executor._generate_dockerfile(recipe)
        
        assert "FROM python:" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "requirements.txt" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        
    def test_generate_requirements(self, executor):
        """Test requirements.txt generation."""
        recipe = Recipe(
            name="test",
            path=Path("."),
            dependencies={"python": ["custom-package>=1.0.0"]}
        )
        
        requirements = executor._generate_requirements(recipe)
        
        assert "pydantic" in requirements
        assert "pytest" in requirements
        assert "custom-package>=1.0.0" in requirements