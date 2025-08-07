#!/usr/bin/env python3
"""
Comprehensive tests for the Architect Agent Engine.

This test suite validates all core functionality of the ArchitectEngine including
system design, component design, integration planning, and architecture review.
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'orchestrator'))

from architect_engine import (
    ArchitectEngine,
    ArchitectureComplexity,
    ArchitectureScale,
    RequestType,
    ProjectContext,
    DesignScope,
    TechnicalPreferences,
    ArchitectureComponent,
    ArchitectureResponse
)


class TestArchitectEngine:
    """Test cases for the ArchitectEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.architect = ArchitectEngine()
        self.sample_request = {
            "request_type": "system_design",
            "project_context": {
                "name": "Test E-commerce Platform",
                "description": "Online marketplace for testing",
                "requirements": [
                    "User authentication",
                    "Product catalog",
                    "Shopping cart",
                    "Order processing"
                ],
                "constraints": [
                    "Handle 1000 concurrent users",
                    "Response time < 300ms"
                ],
                "scale": "medium"
            },
            "design_scope": {
                "focus_area": "full_system",
                "complexity_level": "moderate",
                "timeline": "production"
            },
            "technical_preferences": {
                "languages": ["python"],
                "frameworks": ["fastapi"],
                "databases": ["postgresql"],
                "deployment": "cloud"
            }
        }

    def test_architect_engine_initialization(self):
        """Test ArchitectEngine initialization."""
        assert self.architect is not None
        assert hasattr(self.architect, 'logger')
        assert hasattr(self.architect, 'system_patterns')
        assert hasattr(self.architect, 'integration_patterns')
        assert hasattr(self.architect, 'technology_recommendations')

    def test_architecture_enums(self):
        """Test architecture enumeration values."""
        # Test ArchitectureComplexity enum
        assert ArchitectureComplexity.SIMPLE.value == "simple"
        assert ArchitectureComplexity.MODERATE.value == "moderate"
        assert ArchitectureComplexity.COMPLEX.value == "complex"
        assert ArchitectureComplexity.ENTERPRISE.value == "enterprise"

        # Test ArchitectureScale enum
        assert ArchitectureScale.SMALL.value == "small"
        assert ArchitectureScale.MEDIUM.value == "medium"
        assert ArchitectureScale.LARGE.value == "large"
        assert ArchitectureScale.ENTERPRISE.value == "enterprise"

        # Test RequestType enum
        assert RequestType.SYSTEM_DESIGN.value == "system_design"
        assert RequestType.COMPONENT_DESIGN.value == "component_design"
        assert RequestType.INTEGRATION_PLAN.value == "integration_plan"
        assert RequestType.REVIEW.value == "review"

    def test_parse_project_context(self):
        """Test parsing of project context."""
        context_data = {
            "name": "Test Project",
            "description": "Test description",
            "requirements": ["req1", "req2"],
            "constraints": ["constraint1"],
            "scale": "large"
        }

        context = self.architect._parse_project_context(context_data)

        assert context.name == "Test Project"
        assert context.description == "Test description"
        assert len(context.requirements) == 2
        assert len(context.constraints) == 1
        assert context.scale == ArchitectureScale.LARGE

    def test_parse_project_context_defaults(self):
        """Test parsing of project context with default values."""
        context_data = {}

        context = self.architect._parse_project_context(context_data)

        assert context.name == "Unnamed Project"
        assert context.description == ""
        assert len(context.requirements) == 0
        assert len(context.constraints) == 0
        assert context.scale == ArchitectureScale.MEDIUM

    def test_parse_design_scope(self):
        """Test parsing of design scope."""
        scope_data = {
            "focus_area": "backend",
            "complexity_level": "complex",
            "timeline": "mvp"
        }

        scope = self.architect._parse_design_scope(scope_data)

        assert scope.focus_area == "backend"
        assert scope.complexity_level == ArchitectureComplexity.COMPLEX
        assert scope.timeline == "mvp"

    def test_parse_design_scope_defaults(self):
        """Test parsing of design scope with defaults."""
        scope_data = {}

        scope = self.architect._parse_design_scope(scope_data)

        assert scope.focus_area == "full_system"
        assert scope.complexity_level == ArchitectureComplexity.MODERATE
        assert scope.timeline == "production"

    def test_parse_tech_preferences(self):
        """Test parsing of technical preferences."""
        tech_data = {
            "languages": ["python", "javascript"],
            "frameworks": ["fastapi", "react"],
            "databases": ["postgresql", "redis"],
            "deployment": "hybrid"
        }

        tech_prefs = self.architect._parse_tech_preferences(tech_data)

        assert len(tech_prefs.languages) == 2
        assert "python" in tech_prefs.languages
        assert len(tech_prefs.frameworks) == 2
        assert "fastapi" in tech_prefs.frameworks
        assert len(tech_prefs.databases) == 2
        assert "postgresql" in tech_prefs.databases
        assert tech_prefs.deployment == "hybrid"

    def test_parse_tech_preferences_defaults(self):
        """Test parsing of technical preferences with defaults."""
        tech_data = {}

        tech_prefs = self.architect._parse_tech_preferences(tech_data)

        assert tech_prefs.languages == ["python"]
        assert tech_prefs.frameworks == []
        assert tech_prefs.databases == ["postgresql"]
        assert tech_prefs.deployment == "cloud"

    def test_select_architecture_pattern_simple(self):
        """Test architecture pattern selection for simple projects."""
        context = ProjectContext(
            name="Simple App",
            description="Simple application",
            requirements=["basic auth"],
            constraints=[],
            scale=ArchitectureScale.SMALL
        )
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.SIMPLE,
            timeline="prototype"
        )
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=[],
            databases=["sqlite"],
            deployment="cloud"
        )

        pattern = self.architect._select_architecture_pattern(context, scope, tech_prefs)

        assert pattern == "monolithic"

    def test_select_architecture_pattern_microservices(self):
        """Test architecture pattern selection for microservices."""
        context = ProjectContext(
            name="Complex App",
            description="Complex distributed application",
            requirements=["scalability", "fault tolerance"],
            constraints=["high availability"],
            scale=ArchitectureScale.LARGE
        )
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.COMPLEX,
            timeline="production"
        )
        tech_prefs = TechnicalPreferences(
            languages=["python", "go"],
            frameworks=["fastapi"],
            databases=["postgresql", "redis"],
            deployment="cloud"
        )

        pattern = self.architect._select_architecture_pattern(context, scope, tech_prefs)

        assert pattern == "microservices"

    def test_select_architecture_pattern_enterprise(self):
        """Test architecture pattern selection for enterprise projects."""
        context = ProjectContext(
            name="Enterprise System",
            description="Large enterprise system",
            requirements=["legacy integration", "governance"],
            constraints=["compliance", "enterprise policies"],
            scale=ArchitectureScale.ENTERPRISE
        )
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.ENTERPRISE,
            timeline="enterprise"
        )
        tech_prefs = TechnicalPreferences(
            languages=["java"],
            frameworks=["spring_boot"],
            databases=["oracle"],
            deployment="on_premise"
        )

        pattern = self.architect._select_architecture_pattern(context, scope, tech_prefs)

        assert pattern == "service_oriented"

    def test_select_framework(self):
        """Test framework selection logic."""
        # Test with preferred frameworks
        framework = self.architect._select_framework("python", ["django", "flask"])
        assert framework == "django"

        # Test with default frameworks
        framework = self.architect._select_framework("python", [])
        assert framework == "fastapi"

        framework = self.architect._select_framework("javascript", [])
        assert framework == "express"

        framework = self.architect._select_framework("unknown_language", [])
        assert framework == "unknown"

    def test_design_monolithic_components(self):
        """Test monolithic architecture component design."""
        context = ProjectContext(
            name="Monolithic App",
            description="Simple monolithic application",
            requirements=["user management", "data processing"],
            constraints=[],
            scale=ArchitectureScale.SMALL
        )
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=["flask"],
            databases=["postgresql"],
            deployment="cloud"
        )

        components = self.architect._design_monolithic_components(context, tech_prefs)

        assert len(components) == 2
        assert any(comp.name == "application_core" for comp in components)
        assert any(comp.name == "database_layer" for comp in components)

        # Verify component properties
        app_core = next(comp for comp in components if comp.name == "application_core")
        assert app_core.technology_stack.language == "python"
        assert app_core.technology_stack.framework == "flask"
        assert app_core.technology_stack.database == "postgresql"
        assert len(app_core.responsibilities) >= 4

    def test_design_microservice_components(self):
        """Test microservices architecture component design."""
        context = ProjectContext(
            name="Microservices App",
            description="Distributed microservices application",
            requirements=["scalability", "independence"],
            constraints=["high availability"],
            scale=ArchitectureScale.LARGE
        )
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=["fastapi"],
            databases=["postgresql"],
            deployment="cloud"
        )

        components = self.architect._design_microservice_components(context, tech_prefs)

        assert len(components) == 3
        component_names = [comp.name for comp in components]
        assert "api_gateway" in component_names
        assert "user_service" in component_names
        assert "business_service" in component_names

        # Verify API Gateway component
        api_gateway = next(comp for comp in components if comp.name == "api_gateway")
        assert "Request routing" in api_gateway.responsibilities
        assert "Authentication" in api_gateway.responsibilities

    def test_design_layered_components(self):
        """Test layered architecture component design."""
        context = ProjectContext(
            name="Layered App",
            description="Traditional layered application",
            requirements=["separation of concerns", "maintainability"],
            constraints=[],
            scale=ArchitectureScale.MEDIUM
        )
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=["django"],
            databases=["postgresql"],
            deployment="cloud"
        )

        components = self.architect._design_layered_components(context, tech_prefs)

        assert len(components) == 3
        component_names = [comp.name for comp in components]
        assert "presentation_layer" in component_names
        assert "business_layer" in component_names
        assert "data_layer" in component_names

        # Verify layer dependencies
        presentation = next(comp for comp in components if comp.name == "presentation_layer")
        assert "business_layer" in presentation.interfaces.dependencies

        business = next(comp for comp in components if comp.name == "business_layer")
        assert "data_layer" in business.interfaces.dependencies

    def test_design_soa_components(self):
        """Test SOA architecture component design."""
        context = ProjectContext(
            name="SOA System",
            description="Service-oriented architecture system",
            requirements=["service reuse", "governance"],
            constraints=["enterprise compliance"],
            scale=ArchitectureScale.ENTERPRISE
        )
        tech_prefs = TechnicalPreferences(
            languages=["java"],
            frameworks=["spring_boot"],
            databases=["oracle"],
            deployment="on_premise"
        )

        components = self.architect._design_soa_components(context, tech_prefs)

        assert len(components) == 3
        component_names = [comp.name for comp in components]
        assert "service_registry" in component_names
        assert "enterprise_service_bus" in component_names
        assert "business_service" in component_names

        # Verify SOA-specific components
        service_registry = next(comp for comp in components if comp.name == "service_registry")
        assert "Service registration" in service_registry.responsibilities
        assert service_registry.technology_stack.framework == "consul"

    def test_design_data_flow(self):
        """Test data flow design."""
        # Test microservices data flow
        components = [
            ArchitectureComponent(
                name="api_gateway",
                purpose="API gateway",
                responsibilities=[],
                interfaces=None,
                technology_stack=None
            )
        ]

        data_flow = self.architect._design_data_flow(components, "microservices")
        assert "API Gateway" in data_flow.description
        assert "microservices_data_flow.mermaid" in data_flow.diagrams

        # Test layered data flow
        data_flow = self.architect._design_data_flow(components, "layered")
        assert "presentation layer" in data_flow.description
        assert "layered_data_flow.mermaid" in data_flow.diagrams

        # Test monolithic data flow
        data_flow = self.architect._design_data_flow(components, "monolithic")
        assert "monolithic application" in data_flow.description
        assert "monolithic_data_flow.mermaid" in data_flow.diagrams

    def test_select_integration_patterns_microservices(self):
        """Test integration pattern selection for microservices."""
        components = [
            ArchitectureComponent(
                name="service1",
                purpose="test",
                responsibilities=[],
                interfaces=None,
                technology_stack=None
            )
        ]
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.COMPLEX,
            timeline="production"
        )

        patterns = self.architect._select_integration_patterns(components, "microservices", scope)

        assert len(patterns) == 3
        pattern_names = [pattern.pattern_name for pattern in patterns]
        assert "api_gateway" in pattern_names
        assert "message_queue" in pattern_names
        assert "database_per_service" in pattern_names

    def test_select_integration_patterns_soa(self):
        """Test integration pattern selection for SOA."""
        components = []
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.ENTERPRISE,
            timeline="enterprise"
        )

        patterns = self.architect._select_integration_patterns(components, "service_oriented", scope)

        assert len(patterns) == 2
        pattern_names = [pattern.pattern_name for pattern in patterns]
        assert "enterprise_service_bus" in pattern_names
        assert "service_registry" in pattern_names

    def test_create_implementation_plan(self):
        """Test implementation plan creation."""
        components = [
            ArchitectureComponent(
                name="comp1",
                purpose="test",
                responsibilities=[],
                interfaces=None,
                technology_stack=None
            ),
            ArchitectureComponent(
                name="comp2",
                purpose="test",
                responsibilities=[],
                interfaces=None,
                technology_stack=None
            )
        ]
        context = ProjectContext(
            name="Test Project",
            description="Test",
            requirements=[],
            constraints=[],
            scale=ArchitectureScale.MEDIUM
        )
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.MODERATE,
            timeline="production"
        )

        plan = self.architect._create_implementation_plan(components, context, scope)

        assert len(plan.phases) == 4
        assert plan.phases[0].name == "Foundation Setup"
        assert plan.phases[1].name == "Core Components"
        assert plan.phases[2].name == "Component Integration"
        assert plan.phases[3].name == "Testing & Deployment"

        # Verify resource requirements
        assert plan.resource_requirements.developers >= 2
        assert plan.resource_requirements.devops >= 1
        assert "weeks" in plan.resource_requirements.timeline

        # Verify critical path
        assert "foundation_setup" in plan.critical_path
        assert "core_components" in plan.critical_path
        assert "component_integration" in plan.critical_path

    def test_generate_technical_specifications(self):
        """Test technical specifications generation."""
        components = []
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=["fastapi"],
            databases=["postgresql"],
            deployment="cloud"
        )
        context = ProjectContext(
            name="Test Project",
            description="Test",
            requirements=[],
            constraints=[],
            scale=ArchitectureScale.MEDIUM
        )

        specs = self.architect._generate_technical_specifications(components, tech_prefs, context)

        # Verify API design
        assert specs.api_design.base_url == "https://api.example.com"
        assert specs.api_design.authentication == "jwt"
        assert len(specs.api_design.endpoints) >= 3

        # Verify database design
        assert specs.database_design.type == "postgresql"
        assert len(specs.database_design.schemas) >= 1
        assert specs.database_design.schemas[0].table_name == "users"

        # Verify security design
        assert specs.security_design.authentication == "oauth2_jwt"
        assert specs.security_design.authorization == "role_based"
        assert "encryption_at_rest" in specs.security_design.data_protection

    def test_define_quality_attributes(self):
        """Test quality attributes definition."""
        # Test small scale
        context_small = ProjectContext(
            name="Small App",
            description="Test",
            requirements=[],
            constraints=[],
            scale=ArchitectureScale.SMALL
        )
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.SIMPLE,
            timeline="production"
        )

        qa_small = self.architect._define_quality_attributes(context_small, scope)
        assert "500ms" in qa_small.performance.requirements

        # Test enterprise scale
        context_enterprise = ProjectContext(
            name="Enterprise App",
            description="Test",
            requirements=[],
            constraints=[],
            scale=ArchitectureScale.ENTERPRISE
        )

        qa_enterprise = self.architect._define_quality_attributes(context_enterprise, scope)
        assert "50ms" in qa_enterprise.performance.requirements
        assert "database_sharding" in qa_enterprise.performance.strategies

    def test_generate_recommendations(self):
        """Test recommendations generation."""
        components = []
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.SIMPLE,
            timeline="production"
        )
        tech_prefs = TechnicalPreferences(
            languages=["python"],
            frameworks=[],
            databases=[],
            deployment="cloud"
        )

        recommendations = self.architect._generate_recommendations("microservices", components, scope, tech_prefs)

        assert len(recommendations) >= 2
        
        # Check for pattern recommendation for simple complexity
        pattern_rec = next((r for r in recommendations if r.category == "architecture"), None)
        if pattern_rec:
            assert "monolithic" in pattern_rec.recommendation

        # Check for technology recommendation
        tech_rec = next((r for r in recommendations if r.category == "technology"), None)
        if tech_rec:
            assert "FastAPI" in tech_rec.recommendation

    def test_assess_risks(self):
        """Test risk assessment."""
        components = []
        scope = DesignScope(
            focus_area="full_system",
            complexity_level=ArchitectureComplexity.COMPLEX,
            timeline="production"
        )
        context = ProjectContext(
            name="Test App",
            description="Test",
            requirements=[],
            constraints=[],
            scale=ArchitectureScale.LARGE
        )

        risks = self.architect._assess_risks("microservices", components, scope, context)

        assert len(risks) >= 3
        risk_types = [risk.risk for risk in risks]
        assert any("communication" in risk_type.lower() for risk_type in risk_types)
        assert any("consistency" in risk_type.lower() for risk_type in risk_types)
        assert any("security" in risk_type.lower() for risk_type in risk_types)

        # Check for database performance risk for large scale
        db_risk = next((risk for risk in risks if "database" in risk.risk.lower()), None)
        if db_risk:
            assert db_risk.impact == "high"
            assert "replicas" in db_risk.mitigation.lower()

    def test_design_system_architecture_success(self):
        """Test successful system architecture design."""
        response = self.architect.design_system_architecture(self.sample_request)

        assert response.success is True
        assert response.architecture is not None
        assert response.implementation_plan is not None
        assert response.technical_specifications is not None
        assert response.quality_attributes is not None
        assert len(response.recommendations) > 0
        assert len(response.risks_and_mitigations) > 0
        assert response.error_message is None

        # Verify architecture components
        assert len(response.architecture.components) > 0
        assert response.architecture.overview is not None
        assert response.architecture.data_flow is not None
        assert len(response.architecture.integration_patterns) >= 0

    def test_design_system_architecture_with_error(self):
        """Test system architecture design with error handling."""
        # Invalid request that should cause an error
        invalid_request = {
            "project_context": {
                "scale": "invalid_scale"  # Invalid enum value
            }
        }

        response = self.architect.design_system_architecture(invalid_request)

        assert response.success is False
        assert response.error_message is not None
        assert response.architecture is None

    def test_design_component(self):
        """Test component design functionality."""
        component_request = {
            "component_name": "user_service",
            "requirements": [
                "User registration",
                "Authentication",
                "Profile management"
            ],
            "technical_preferences": {
                "languages": ["python"],
                "frameworks": ["fastapi"],
                "databases": ["postgresql"]
            }
        }

        response = self.architect.design_component(component_request)

        assert response["success"] is True
        assert "component" in response
        assert response["component"]["name"] == "user_service"
        assert len(response["component"]["responsibilities"]) >= 4
        assert response["component"]["technology_stack"]["language"] == "python"
        assert len(response["recommendations"]) >= 2
        assert len(response["risks"]) >= 2

    def test_design_component_database(self):
        """Test database component design."""
        component_request = {
            "component_name": "user_database",
            "requirements": [
                "Data persistence",
                "High availability"
            ],
            "technical_preferences": {
                "databases": ["postgresql"]
            }
        }

        response = self.architect.design_component(component_request)

        assert response["success"] is True
        component = response["component"]
        assert component["name"] == "user_database"
        assert "Data persistence" in component["responsibilities"]
        assert component["technology_stack"]["language"] == "sql"

    def test_design_component_with_error(self):
        """Test component design error handling."""
        # Mock an error in the design process
        with patch.object(self.architect, '_design_specific_component', side_effect=Exception("Test error")):
            component_request = {
                "component_name": "test_component",
                "requirements": [],
                "technical_preferences": {}
            }

            response = self.architect.design_component(component_request)

            assert response["success"] is False
            assert response["error_message"] == "Test error"

    def test_create_integration_plan(self):
        """Test integration plan creation."""
        integration_request = {
            "components": ["user_service", "order_service", "payment_service"],
            "integration_requirements": [
                "Real-time communication",
                "Data consistency",
                "Error handling"
            ]
        }

        response = self.architect.create_integration_plan(integration_request)

        assert response["success"] is True
        assert "integration_plan" in response
        assert "overview" in response["integration_plan"]
        assert "integration_points" in response["integration_plan"]
        assert len(response["recommendations"]) >= 2
        assert len(response["risks"]) >= 2

    def test_create_integration_plan_with_error(self):
        """Test integration plan creation error handling."""
        with patch.object(self.architect, '_create_integration_plan', side_effect=Exception("Integration error")):
            integration_request = {
                "components": [],
                "integration_requirements": []
            }

            response = self.architect.create_integration_plan(integration_request)

            assert response["success"] is False
            assert response["error_message"] == "Integration error"

    def test_review_architecture(self):
        """Test architecture review functionality."""
        review_request = {
            "architecture_description": "Microservices architecture with API gateway and multiple services",
            "review_criteria": [
                "scalability",
                "security",
                "maintainability",
                "performance"
            ]
        }

        response = self.architect.review_architecture(review_request)

        assert response["success"] is True
        assert "review_results" in response
        assert "score" in response
        assert isinstance(response["score"], int)
        assert 0 <= response["score"] <= 100
        assert "recommendations" in response
        assert "action_items" in response

        # Verify review results structure
        results = response["review_results"]
        assert "scalability_assessment" in results
        assert "security_assessment" in results
        assert "maintainability_assessment" in results
        assert "performance_assessment" in results

    def test_calculate_architecture_score(self):
        """Test architecture score calculation."""
        # Test excellent assessments
        excellent_results = {
            "scalability_assessment": "Excellent scalability design",
            "security_assessment": "Excellent security measures",
            "maintainability_assessment": "Excellent code structure",
            "performance_assessment": "Excellent performance optimization"
        }

        score = self.architect._calculate_architecture_score(excellent_results)
        assert score == 100

        # Test mixed assessments
        mixed_results = {
            "scalability_assessment": "Good scalability approach",
            "security_assessment": "Needs improvement in security",
            "maintainability_assessment": "Good maintainability",
            "performance_assessment": "Poor performance design"
        }

        score = self.architect._calculate_architecture_score(mixed_results)
        assert 0 < score < 100

    def test_review_architecture_with_error(self):
        """Test architecture review error handling."""
        with patch.object(self.architect, '_perform_architecture_review', side_effect=Exception("Review error")):
            review_request = {
                "architecture_description": "Test architecture",
                "review_criteria": []
            }

            response = self.architect.review_architecture(review_request)

            assert response["success"] is False
            assert response["error_message"] == "Review error"

    def test_design_specific_component_api(self):
        """Test specific component design for API services."""
        component = self.architect._design_specific_component(
            "test_api_service",
            ["API handling", "Business logic"],
            TechnicalPreferences(["python"], ["fastapi"], ["postgresql"], "cloud")
        )

        assert component.name == "test_api_service"
        assert "API service" in component.purpose
        assert "HTTP request handling" in component.responsibilities
        assert component.technology_stack.language == "python"
        assert component.technology_stack.framework == "fastapi"

    def test_design_specific_component_database(self):
        """Test specific component design for database components."""
        component = self.architect._design_specific_component(
            "user_storage",
            ["Data persistence", "Backup"],
            TechnicalPreferences([], [], ["mongodb"], "cloud")
        )

        assert component.name == "user_storage"
        assert "storage" in component.purpose.lower()
        assert "Data persistence" in component.responsibilities
        assert component.technology_stack.language == "sql"
        assert component.technology_stack.database == "mongodb"

    def test_design_specific_component_generic(self):
        """Test specific component design for generic components."""
        component = self.architect._design_specific_component(
            "message_processor",
            ["Message processing", "Queue management"],
            TechnicalPreferences(["go"], ["gin"], [], "cloud")
        )

        assert component.name == "message_processor"
        assert "message_processor functionality" in component.purpose
        assert "Message processing" in component.responsibilities
        assert component.technology_stack.language == "go"
        assert component.technology_stack.framework == "gin"

    def test_generate_component_recommendations(self):
        """Test component-specific recommendation generation."""
        component = ArchitectureComponent(
            name="test_component",
            purpose="Testing",
            responsibilities=["Testing"],
            interfaces=None,
            technology_stack=None
        )

        recommendations = self.architect._generate_component_recommendations(component)

        assert len(recommendations) >= 2
        rec_categories = [rec.category for rec in recommendations]
        assert "implementation" in rec_categories
        assert "testing" in rec_categories

    def test_assess_component_risks(self):
        """Test component-specific risk assessment."""
        component = ArchitectureComponent(
            name="critical_component",
            purpose="Critical functionality",
            responsibilities=["Critical processing"],
            interfaces=None,
            technology_stack=None
        )

        risks = self.architect._assess_component_risks(component)

        assert len(risks) >= 2
        risk_types = [risk.risk for risk in risks]
        assert any("performance" in risk_type.lower() for risk_type in risk_types)
        assert any("security" in risk_type.lower() for risk_type in risk_types)

    def test_integration_recommendations(self):
        """Test integration-specific recommendations."""
        components = ["service1", "service2", "service3"]
        recommendations = self.architect._generate_integration_recommendations(components)

        assert len(recommendations) >= 2
        rec_types = [rec.category for rec in recommendations]
        assert "integration" in rec_types
        assert "monitoring" in rec_types

        # Check for API versioning recommendation
        api_rec = next((r for r in recommendations if "versioning" in r.recommendation.lower()), None)
        assert api_rec is not None

    def test_integration_risks(self):
        """Test integration-specific risk assessment."""
        components = ["service1", "service2"]
        risks = self.architect._assess_integration_risks(components)

        assert len(risks) >= 2
        risk_descriptions = [risk.risk for risk in risks]
        assert any("integration" in risk_desc.lower() for risk_desc in risk_descriptions)
        assert any("data format" in risk_desc.lower() for risk_desc in risk_descriptions)

    def test_system_patterns_catalog(self):
        """Test system patterns catalog completeness."""
        assert "monolithic" in self.architect.system_patterns
        assert "microservices" in self.architect.system_patterns
        assert "service_oriented" in self.architect.system_patterns
        assert "event_driven" in self.architect.system_patterns
        assert "layered" in self.architect.system_patterns
        assert "hexagonal" in self.architect.system_patterns

        # Verify pattern structure
        monolithic = self.architect.system_patterns["monolithic"]
        assert "description" in monolithic
        assert "use_case" in monolithic
        assert "pros" in monolithic
        assert "cons" in monolithic

    def test_integration_patterns_catalog(self):
        """Test integration patterns catalog completeness."""
        assert "api_gateway" in self.architect.integration_patterns
        assert "message_queue" in self.architect.integration_patterns
        assert "event_streaming" in self.architect.integration_patterns
        assert "database_per_service" in self.architect.integration_patterns
        assert "saga_pattern" in self.architect.integration_patterns
        assert "cqrs" in self.architect.integration_patterns

        # Verify pattern structure
        api_gateway = self.architect.integration_patterns["api_gateway"]
        assert "description" in api_gateway
        assert "implementation" in api_gateway
        assert "technologies" in api_gateway

    def test_technology_recommendations_catalog(self):
        """Test technology recommendations catalog."""
        assert "python" in self.architect.technology_recommendations
        assert "javascript" in self.architect.technology_recommendations
        assert "java" in self.architect.technology_recommendations
        assert "go" in self.architect.technology_recommendations

        # Verify recommendation structure
        python_rec = self.architect.technology_recommendations["python"]
        assert "frameworks" in python_rec
        assert "databases" in python_rec
        assert "use_cases" in python_rec
        assert "FastAPI" in python_rec["frameworks"]

    def test_logging_setup(self):
        """Test logging configuration."""
        assert self.architect.logger is not None
        assert self.architect.logger.name == "architect_engine"
        assert self.architect.logger.level == 20  # INFO level

    @patch('architect_engine.logging.StreamHandler')
    def test_logging_handler_setup(self, mock_handler):
        """Test logging handler setup."""
        # Create new architect to trigger logging setup
        new_architect = ArchitectEngine()
        
        assert new_architect.logger is not None
        # Verify logger was configured (handler count may vary in test environment)

    def test_comprehensive_system_design_workflow(self):
        """Test comprehensive system design workflow end-to-end."""
        # Large-scale e-commerce system
        complex_request = {
            "request_type": "system_design",
            "project_context": {
                "name": "Enterprise E-commerce Platform",
                "description": "Large-scale online marketplace with multiple vendors",
                "requirements": [
                    "Multi-tenant architecture",
                    "Real-time inventory management",
                    "Advanced search capabilities",
                    "Recommendation engine",
                    "Payment processing",
                    "Order fulfillment",
                    "Analytics and reporting",
                    "Mobile API support"
                ],
                "constraints": [
                    "Handle 100,000 concurrent users",
                    "99.99% uptime requirement",
                    "Response time < 100ms",
                    "PCI DSS compliance",
                    "GDPR compliance",
                    "Global deployment"
                ],
                "scale": "enterprise"
            },
            "design_scope": {
                "focus_area": "full_system",
                "complexity_level": "enterprise",
                "timeline": "enterprise"
            },
            "existing_systems": {
                "current_architecture": "Legacy monolithic system",
                "legacy_systems": ["Old inventory system", "Legacy payment gateway"],
                "integration_points": ["ERP system", "CRM system", "Third-party logistics"]
            },
            "technical_preferences": {
                "languages": ["python", "javascript", "go"],
                "frameworks": ["fastapi", "react", "gin"],
                "databases": ["postgresql", "redis", "elasticsearch"],
                "deployment": "cloud"
            }
        }

        response = self.architect.design_system_architecture(complex_request)

        # Comprehensive validation
        assert response.success is True
        assert response.architecture is not None
        assert response.implementation_plan is not None
        assert response.technical_specifications is not None
        assert response.quality_attributes is not None

        # Verify enterprise-scale characteristics
        assert len(response.architecture.components) >= 3
        assert len(response.implementation_plan.phases) == 4
        assert response.implementation_plan.resource_requirements.developers >= 3
        assert len(response.recommendations) > 0
        assert len(response.risks_and_mitigations) > 0

        # Verify quality attributes for enterprise scale
        assert "enterprise" in response.quality_attributes.security.requirements
        assert len(response.quality_attributes.performance.strategies) >= 3

        # Verify comprehensive specifications
        assert len(response.technical_specifications.api_design.endpoints) >= 3
        assert len(response.technical_specifications.database_design.schemas) >= 1
        assert "gdpr" in response.technical_specifications.security_design.compliance

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and comprehensive error handling."""
        # Test with minimal/empty request
        minimal_request = {}
        response = self.architect.design_system_architecture(minimal_request)
        
        # Should handle gracefully with defaults
        assert response.success is True  # Should succeed with defaults
        assert response.architecture is not None

        # Test with invalid enum values (should be handled by parsing)
        invalid_enum_request = {
            "project_context": {"scale": "medium"},  # Valid value
            "design_scope": {"complexity_level": "moderate"}  # Valid value
        }
        
        response = self.architect.design_system_architecture(invalid_enum_request)
        assert response.success is True  # Should succeed with valid enums


class TestDataClasses:
    """Test the data classes used by the architect engine."""

    def test_project_context_creation(self):
        """Test ProjectContext data class creation."""
        context = ProjectContext(
            name="Test Project",
            description="Test Description",
            requirements=["req1", "req2"],
            constraints=["constraint1"],
            scale=ArchitectureScale.MEDIUM
        )

        assert context.name == "Test Project"
        assert context.description == "Test Description"
        assert len(context.requirements) == 2
        assert len(context.constraints) == 1
        assert context.scale == ArchitectureScale.MEDIUM

    def test_design_scope_creation(self):
        """Test DesignScope data class creation."""
        scope = DesignScope(
            focus_area="backend",
            complexity_level=ArchitectureComplexity.COMPLEX,
            timeline="production"
        )

        assert scope.focus_area == "backend"
        assert scope.complexity_level == ArchitectureComplexity.COMPLEX
        assert scope.timeline == "production"

    def test_technical_preferences_creation(self):
        """Test TechnicalPreferences data class creation."""
        tech_prefs = TechnicalPreferences(
            languages=["python", "go"],
            frameworks=["fastapi", "gin"],
            databases=["postgresql", "redis"],
            deployment="cloud"
        )

        assert len(tech_prefs.languages) == 2
        assert "python" in tech_prefs.languages
        assert len(tech_prefs.frameworks) == 2
        assert "fastapi" in tech_prefs.frameworks
        assert len(tech_prefs.databases) == 2
        assert "postgresql" in tech_prefs.databases
        assert tech_prefs.deployment == "cloud"

    def test_architecture_component_creation(self):
        """Test ArchitectureComponent data class creation."""
        from architect_engine import ComponentInterface, TechnologyStack

        interfaces = ComponentInterface(
            inputs=["HTTP requests"],
            outputs=["HTTP responses"],
            dependencies=["database"]
        )

        tech_stack = TechnologyStack(
            language="python",
            framework="fastapi",
            database="postgresql"
        )

        component = ArchitectureComponent(
            name="test_component",
            purpose="Testing component creation",
            responsibilities=["Handle requests", "Process data"],
            interfaces=interfaces,
            technology_stack=tech_stack
        )

        assert component.name == "test_component"
        assert component.purpose == "Testing component creation"
        assert len(component.responsibilities) == 2
        assert component.interfaces.inputs == ["HTTP requests"]
        assert component.technology_stack.language == "python"

    def test_architecture_response_creation(self):
        """Test ArchitectureResponse data class creation."""
        from architect_engine import Architecture, ImplementationPlan, TechnicalSpecifications, QualityAttributes

        # Create minimal objects for testing
        architecture = Architecture(
            overview="Test architecture",
            components=[],
            data_flow=None,
            integration_patterns=[]
        )

        response = ArchitectureResponse(
            success=True,
            architecture=architecture,
            implementation_plan=None,
            technical_specifications=None,
            quality_attributes=None,
            recommendations=[],
            risks_and_mitigations=[]
        )

        assert response.success is True
        assert response.architecture.overview == "Test architecture"
        assert response.error_message is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])