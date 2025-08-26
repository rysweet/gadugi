"""Tests for data models package."""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from src.data_models import (
    # Recipe Model
    Recipe,
    RecipeMetadata,
    Requirements,
    Requirement,
    RequirementPriority,
    Design,
    ComponentDesign,
    ComponentType,
    Components,
    # Requirements Model
    ExtendedRequirement,
    RequirementStatus,
    RequirementCategory,
    RequirementsMatrix,
    # Design Model
    ComponentArchitecture,
    SystemArchitecture,
    Interface,
    InterfaceType,
    MethodSignature,
    Dependency,
    # Execution Model
    ExecutionState,
    ExecutionPhase,
    ComponentStatus,
    GenerationResult,
    TestResult,
    ExecutionReport,
    # Validation Model
    ValidationResult,
    ValidationError,
    ValidationWarning,
    ValidationCategory,
    ValidationSeverity,
    ValidationReport,
)


class TestRecipeModel:
    """Test Recipe model and related classes."""

    def test_recipe_metadata_creation(self):
        """Test creating recipe metadata."""
        metadata = RecipeMetadata(
            name="test-recipe",
            version="1.0.0",
            description="Test recipe",
            author="Test Author"
        )
        assert metadata.name == "test-recipe"
        assert metadata.version == "1.0.0"
        assert str(metadata) == "test-recipe v1.0.0 by Test Author"

    def test_requirement_creation(self):
        """Test creating requirements."""
        req = Requirement(
            priority=RequirementPriority.MUST,
            description="Must implement feature X",
            category="functional"
        )
        assert req.priority == RequirementPriority.MUST
        assert req.id  # Auto-generated ID

    def test_recipe_creation_and_validation(self):
        """Test creating and validating a complete recipe."""
        metadata = RecipeMetadata(
            name="test-recipe",
            version="1.0.0",
            description="Test recipe",
            author="Test Author"
        )
        
        requirements = Requirements(
            functional=[
                Requirement(
                    priority=RequirementPriority.MUST,
                    description="Must implement feature X"
                )
            ]
        )
        
        design = Design(
            overview="Test design",
            components=[
                ComponentDesign(
                    name="test-component",
                    type=ComponentType.SERVICE,
                    path="/src/test"
                )
            ]
        )
        
        recipe = Recipe(
            metadata=metadata,
            requirements=requirements,
            design=design
        )
        
        assert recipe.is_valid()
        assert isinstance(recipe.id, UUID)
        summary = recipe.to_summary()
        assert "test-recipe" in summary


class TestRequirementsModel:
    """Test extended requirements model."""

    def test_extended_requirement_lifecycle(self):
        """Test requirement status transitions."""
        req = ExtendedRequirement(
            id="REQ-001",
            title="Test Requirement",
            description="Test description",
            priority=RequirementPriority.MUST,
            category=RequirementCategory.FUNCTIONAL
        )
        
        assert req.status == RequirementStatus.PENDING
        assert not req.is_complete()
        
        req.add_implementation("test-component")
        assert req.status == RequirementStatus.IN_PROGRESS
        
        req.mark_verified()
        assert req.status == RequirementStatus.VERIFIED
        assert req.is_complete()

    def test_requirements_matrix_coverage(self):
        """Test requirements matrix coverage calculation."""
        matrix = RequirementsMatrix()
        
        for i in range(5):
            req = ExtendedRequirement(
                id=f"REQ-{i:03d}",
                title=f"Requirement {i}",
                description=f"Description {i}",
                priority=RequirementPriority.MUST,
                category=RequirementCategory.FUNCTIONAL,
                status=RequirementStatus.VERIFIED if i < 3 else RequirementStatus.PENDING
            )
            matrix.add_requirement(req)
        
        stats = matrix.get_coverage_stats()
        assert stats["total_requirements"] == 5
        assert stats["verified"] == 3
        assert stats["verification_percentage"] == 60.0


class TestDesignModel:
    """Test design model classes."""

    def test_method_signature(self):
        """Test method signature generation."""
        method = MethodSignature(
            name="process_data",
            parameters=[
                {"name": "data", "type": "str"},
                {"name": "options", "type": "Dict[str, Any]"}
            ],
            return_type="bool",
            async_method=True
        )
        
        signature = method.get_signature()
        assert "async def process_data" in signature
        assert "data: str" in signature
        assert "-> bool" in signature

    def test_component_architecture(self):
        """Test component architecture with dependencies."""
        component = ComponentArchitecture(
            name="test-service",
            type=ComponentType.SERVICE,
            description="Test service",
            dependencies=[
                Dependency(name="database", type="internal"),
                Dependency(name="redis", type="external", optional=True)
            ]
        )
        
        external_deps = component.get_external_dependencies()
        assert len(external_deps) == 1
        assert external_deps[0].name == "redis"
        
        diagram = component.to_component_diagram()
        assert "@startuml" in diagram
        assert "test-service" in diagram


class TestExecutionModel:
    """Test execution tracking models."""

    def test_execution_state_phases(self):
        """Test execution state phase transitions."""
        state = ExecutionState(
            id="exec-001",
            recipe_name="test-recipe"
        )
        
        assert state.current_phase == ExecutionPhase.INITIALIZING
        assert state.get_progress() < 100.0
        
        state.update_phase(ExecutionPhase.PARSING)
        state.update_phase(ExecutionPhase.VALIDATING)
        state.update_phase(ExecutionPhase.COMPLETED)
        
        assert state.current_phase == ExecutionPhase.COMPLETED
        assert state.get_progress() == 100.0
        assert state.is_complete()

    def test_generation_result(self):
        """Test generation result tracking."""
        result = GenerationResult(
            component_name="test-component",
            success=True,
            generation_time=timedelta(seconds=30),
            implementation_count=10,
            stub_count=2
        )
        
        result.add_file("/src/test.py")
        assert len(result.files_generated) == 1
        
        completion_rate = result.get_completion_rate()
        assert completion_rate > 80.0  # 10 implementations, 2 stubs

    def test_test_result(self):
        """Test result tracking."""
        result = TestResult(
            component_name="test-component",
            test_suite="unit-tests",
            total_tests=10,
            passed=8,
            failed=2,
            execution_time=timedelta(seconds=5)
        )
        
        assert result.success_rate() == 80.0
        assert not result.is_passing()
        
        result.add_failure("test_feature_x", "AssertionError: Expected True")
        assert len(result.failure_details) == 1


class TestValidationModel:
    """Test validation models."""

    def test_validation_result(self):
        """Test validation result with mixed issues."""
        result = ValidationResult(
            validator_name="test-validator",
            target="test-recipe"
        )
        
        result.add_error("Missing required field", ValidationCategory.COMPLETENESS)
        result.add_warning("Consider using newer API", ValidationCategory.STYLE)
        result.add_info("Found 10 components", ValidationCategory.STRUCTURE)
        
        assert not result.is_valid()
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        
        summary = result.to_summary()
        assert summary["total_issues"] == 3
        assert not summary["valid"]

    def test_validation_report_aggregation(self):
        """Test aggregating multiple validation results."""
        report = ValidationReport(id="report-001")
        
        results = []
        for i in range(3):
            result = ValidationResult(
                validator_name=f"validator-{i}",
                target=f"target-{i}"
            )
            if i == 0:
                result.add_error("Test error", ValidationCategory.SYNTAX)
            results.append(result)
        
        report.aggregate_results(results)
        assert not report.overall_valid
        assert report.summary_stats["total_validators"] == 3
        assert report.summary_stats["passed_validators"] == 2
        
        markdown = report.to_markdown()
        assert "## Summary" in markdown
        assert "✗ INVALID" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])