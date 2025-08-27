"""
Test suite for ADR Generator

Tests Architecture Decision Record generation, templates,
and file management functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from agents.system_design_reviewer.adr_generator import ADRGenerator, ADRData
from agents.system_design_reviewer.ast_parser import (
    ArchitecturalChange,
    ArchitecturalElement,
    ElementType,
    ChangeType,
    ImpactLevel,
)


@pytest.fixture
def sample_changes_requiring_adr():
    """Sample changes that require ADR generation"""
    return [
        ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="SecurityManager",
                location="security/manager.py:10",
                patterns=["singleton", "security"],
                is_public=True,
            ),
            impact_level=ImpactLevel.HIGH,
            design_implications=["Introduces centralized security management"],
            requires_adr=True,
        ),
        ArchitecturalChange(
            change_type=ChangeType.MODIFIED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="authenticate_user",
                location="auth/core.py:25",
                patterns=["security"],
            ),
            impact_level=ImpactLevel.HIGH,
            design_implications=["Changes authentication flow"],
            requires_adr=True,
        ),
    ]


@pytest.fixture
def sample_pr_info():
    """Sample PR information for ADR generation"""
    return {
        "number": "456",
        "title": "Implement centralized security architecture",
        "body": "This PR implements a new centralized security architecture\n\nCloses #789",
        "author": {"login": "security-engineer"},
    }


class TestADRGenerator:
    """Test the ADR Generator class"""

    def test_initialization_default(self):
        """Test ADR generator initialization with defaults"""
        generator = ADRGenerator("docs/adr")

        assert generator.adr_dir == Path("docs/adr")
        assert len(generator.decision_patterns) > 0
        assert "security_change" in generator.decision_patterns
        assert "new_pattern" in generator.decision_patterns

    def test_initialization_custom_dir(self):
        """Test initialization with custom ADR directory"""
        custom_dir = "custom/adr/path"
        generator = ADRGenerator(custom_dir)

        assert generator.adr_dir == Path(custom_dir)

    def test_get_next_adr_number_empty_dir(self):
        """Test getting next ADR number with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ADRGenerator(temp_dir)

            number = generator._get_next_adr_number()
            assert number == 1

    def test_get_next_adr_number_existing_adrs(self):
        """Test getting next ADR number with existing ADRs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ADRGenerator(temp_dir)

            # Create some existing ADR files
            Path(temp_dir, "ADR-001-first-decision.md").touch()
            Path(temp_dir, "ADR-003-third-decision.md").touch()
            Path(temp_dir, "ADR-005-fifth-decision.md").touch()
            Path(temp_dir, "other-file.md").touch()  # Non-ADR file

            number = generator._get_next_adr_number()
            assert number == 6  # Should be max + 1

    def test_classify_decision_type_security(self, sample_changes_requiring_adr):
        """Test classifying security-related changes"""
        generator = ADRGenerator("docs/adr")

        security_change = sample_changes_requiring_adr[0]  # SecurityManager
        decision_type = generator._classify_decision_type(security_change)

        assert decision_type == "security_change"

    def test_classify_decision_type_performance(self):
        """Test classifying performance-related changes"""
        generator = ADRGenerator("docs/adr")

        perf_change = ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="async_processor",
                location="perf/processor.py:10",
                is_async=True,
            ),
            impact_level=ImpactLevel.HIGH,
            requires_adr=True,
        )

        decision_type = generator._classify_decision_type(perf_change)
        assert decision_type == "performance_change"

    def test_classify_decision_type_integration(self):
        """Test classifying integration-related changes"""
        generator = ADRGenerator("docs/adr")

        integration_change = ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="GitHubIntegration",
                location="integrations/github.py:5",
            ),
            impact_level=ImpactLevel.HIGH,
            requires_adr=True,
        )

        decision_type = generator._classify_decision_type(integration_change)
        assert decision_type == "integration_change"

    def test_classify_decision_type_new_pattern(self):
        """Test classifying architectural pattern changes"""
        generator = ADRGenerator("docs/adr")

        pattern_change = ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="ObserverPattern",
                location="patterns/observer.py:5",
                patterns=["observer", "singleton"],
            ),
            impact_level=ImpactLevel.HIGH,
            requires_adr=True,
        )

        decision_type = generator._classify_decision_type(pattern_change)
        assert decision_type == "new_pattern"

    def test_group_changes_by_decision(self, sample_changes_requiring_adr):
        """Test grouping changes by decision type"""
        generator = ADRGenerator("docs/adr")

        groups = generator._group_changes_by_decision(sample_changes_requiring_adr)

        assert "security_change" in groups
        assert len(groups["security_change"]) == 2  # Both changes are security-related

        # Should not have empty groups
        for _group_name, changes in groups.items():
            assert len(changes) > 0

    def test_generate_title_single_change(self, sample_changes_requiring_adr):
        """Test generating title for single change"""
        generator = ADRGenerator("docs/adr")

        single_change = [sample_changes_requiring_adr[0]]
        title = generator._generate_title("security_change", single_change)

        assert "Security architecture modification" in title
        assert "SecurityManager" in title

    def test_generate_title_multiple_changes(self, sample_changes_requiring_adr):
        """Test generating title for multiple changes"""
        generator = ADRGenerator("docs/adr")

        title = generator._generate_title(
            "security_change", sample_changes_requiring_adr
        )

        assert "Security architecture modification" in title
        # Should handle multiple changes gracefully
        assert len(title) > 0

    def test_generate_context(self, sample_changes_requiring_adr, sample_pr_info):
        """Test generating context section"""
        generator = ADRGenerator("docs/adr")

        context = generator._generate_context(
            "security_change", sample_changes_requiring_adr, sample_pr_info
        )

        assert "PR #456" in context
        assert "Implement centralized security architecture" in context
        assert "SecurityManager" in context
        assert "authenticate_user" in context
        assert "high impact" in context.lower()

    def test_generate_decision(self, sample_changes_requiring_adr):
        """Test generating decision description"""
        generator = ADRGenerator("docs/adr")

        decision = generator._generate_decision(
            "security_change", sample_changes_requiring_adr
        )

        assert len(decision) > 0
        # Should contain template-based decision text
        assert "security" in decision.lower()

    def test_generate_rationale(self, sample_changes_requiring_adr):
        """Test generating rationale section"""
        generator = ADRGenerator("docs/adr")

        rationale = generator._generate_rationale(
            "security_change", sample_changes_requiring_adr
        )

        assert len(rationale) > 0
        assert "security" in rationale.lower()
        # Should include specific implications
        assert "centralized security management" in rationale.lower()

    def test_generate_consequences(self, sample_changes_requiring_adr):
        """Test generating consequences section"""
        generator = ADRGenerator("docs/adr")

        consequences = generator._generate_consequences(sample_changes_requiring_adr)

        assert len(consequences) > 0

        # Should have both positive and negative sections
        consequences_text = "\n".join(consequences)
        assert "**Positive:**" in consequences_text
        assert "**Negative:**" in consequences_text
        assert "architectural coherence" in consequences_text.lower()
        assert "complexity" in consequences_text.lower()

    def test_generate_alternatives(self, sample_changes_requiring_adr):
        """Test generating alternatives section"""
        generator = ADRGenerator("docs/adr")

        alternatives = generator._generate_alternatives(
            "security_change", sample_changes_requiring_adr
        )

        assert len(alternatives) > 0
        assert len(alternatives) >= 3  # Should have multiple alternatives

        # Check for reasonable alternatives
        alternatives_text = "\n".join(alternatives).lower()
        assert any(
            word in alternatives_text for word in ["minimal", "third-party", "delay"]
        )

    def test_generate_implementation_notes(self, sample_changes_requiring_adr):
        """Test generating implementation notes"""
        generator = ADRGenerator("docs/adr")

        notes = generator._generate_implementation_notes(sample_changes_requiring_adr)

        assert len(notes) > 0
        assert "**Affected Files:**" in notes
        assert "security/manager.py" in notes
        assert "auth/core.py" in notes
        assert "**Testing Requirements:**" in notes

    def test_generate_related_changes(
        self, sample_changes_requiring_adr, sample_pr_info
    ):
        """Test generating related changes references"""
        generator = ADRGenerator("docs/adr")

        related = generator._generate_related_changes(
            sample_changes_requiring_adr, sample_pr_info
        )

        assert len(related) > 0
        assert "PR #456" in related
        assert "Issue #789" in related  # From PR body "Closes #789"

    def test_create_adr_data(self, sample_changes_requiring_adr, sample_pr_info):
        """Test creating complete ADR data structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ADRGenerator(temp_dir)

            adr_data = generator._create_adr_data(
                "security_change", sample_changes_requiring_adr, sample_pr_info
            )

            assert adr_data.number == 1  # First ADR
            assert "security" in adr_data.title.lower()
            assert adr_data.status == "Proposed"
            assert adr_data.pr_number == "456"
            assert "PR #456" in adr_data.context
            assert len(adr_data.decision) > 0
            assert len(adr_data.rationale) > 0
            assert len(adr_data.consequences) > 0
            assert len(adr_data.alternatives) > 0
            assert len(adr_data.implementation_notes) > 0
            assert len(adr_data.related_changes) > 0

    def test_slugify(self):
        """Test title slugification for filenames"""
        generator = ADRGenerator("docs/adr")

        # Test various title formats
        assert generator._slugify("Simple Title") == "simple-title"
        assert (
            generator._slugify("Complex: Title with Special! Characters?")
            == "complex-title-with-special-characters"
        )
        assert generator._slugify("Multi---Hyphen--Title") == "multi-hyphen-title"
        assert (
            generator._slugify("  Leading and Trailing Spaces  ")
            == "leading-and-trailing-spaces"
        )

    def test_format_adr_content(self):
        """Test ADR content formatting"""
        generator = ADRGenerator("docs/adr")

        adr_data = ADRData(
            number=42,
            title="Test Decision",
            date=datetime(2024, 1, 15, 12, 0, 0),
            status="Proposed",
            context="Test context",
            decision="Test decision",
            rationale="Test rationale",
            consequences=["Positive: Good things", "Negative: Bad things"],
            alternatives=["Alternative 1", "Alternative 2"],
            implementation_notes="Test notes",
            related_changes=["PR #123", "Issue #456"],
            pr_number="123",
        )

        content = generator._format_adr_content(adr_data)

        assert "# ADR-042: Test Decision" in content
        assert "**Date**: 2024-01-15" in content
        assert "**Status**: Proposed" in content
        assert "**Context**: PR #123" in content
        assert "## Decision" in content
        assert "Test decision" in content
        assert "## Rationale" in content
        assert "Test rationale" in content
        assert "## Consequences" in content
        assert "Positive: Good things" in content
        assert "## Alternatives Considered" in content
        assert "- Alternative 1" in content
        assert "## Implementation Notes" in content
        assert "Test notes" in content
        assert "## Related Changes" in content
        assert "- PR #123" in content
        assert "SystemDesignReviewer agent" in content

    def test_write_adr(self):
        """Test writing ADR to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ADRGenerator(temp_dir)

            adr_data = ADRData(
                number=1,
                title="Test Security Decision",
                date=datetime.now(),
                status="Proposed",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                consequences=["Test consequences"],
                alternatives=["Test alternatives"],
                implementation_notes="Test notes",
                related_changes=["PR #123"],
                pr_number="123",
            )

            file_path = generator._write_adr(adr_data)

            assert file_path.endswith("ADR-001-test-security-decision.md")
            assert os.path.exists(file_path)

            # Check file content
            with open(file_path, "r") as f:
                content = f.read()

            assert "# ADR-001: Test Security Decision" in content
            assert "Test decision" in content

    def test_generate_adrs_no_changes_requiring_adr(self, sample_pr_info):
        """Test ADR generation with no changes requiring ADRs"""
        generator = ADRGenerator("docs/adr")

        # Changes that don't require ADRs
        low_impact_changes = [
            ArchitecturalChange(
                change_type=ChangeType.MODIFIED,
                element=ArchitecturalElement(
                    element_type=ElementType.FUNCTION,
                    name="helper_function",
                    location="utils.py:10",
                ),
                impact_level=ImpactLevel.LOW,
                requires_adr=False,
            )
        ]

        adrs = generator.generate_adrs(low_impact_changes, sample_pr_info)

        assert len(adrs) == 0

    def test_generate_adrs_success(self, sample_changes_requiring_adr, sample_pr_info):
        """Test successful ADR generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ADRGenerator(temp_dir)

            adrs = generator.generate_adrs(sample_changes_requiring_adr, sample_pr_info)

            assert len(adrs) > 0

            # Check that files were created
            for adr_path in adrs:
                assert os.path.exists(adr_path)
                assert adr_path.endswith(".md")

                # Check file content
                with open(adr_path, "r") as f:
                    content = f.read()

                assert "# ADR-" in content
                assert (
                    "Security architecture modification" in content
                    or "security" in content.lower()
                )


class TestADRData:
    """Test the ADRData data structure"""

    def test_adr_data_creation(self):
        """Test creating ADR data structure"""
        adr_data = ADRData(
            number=5,
            title="Test ADR",
            date=datetime(2024, 1, 1),
            status="Accepted",
            context="Test context",
            decision="Test decision",
            rationale="Test rationale",
            consequences=["Good", "Bad"],
            alternatives=["Alt1", "Alt2"],
            implementation_notes="Notes",
            related_changes=["PR #1"],
            pr_number="123",
        )

        assert adr_data.number == 5
        assert adr_data.title == "Test ADR"
        assert adr_data.status == "Accepted"
        assert adr_data.pr_number == "123"
        assert len(adr_data.consequences) == 2
        assert len(adr_data.alternatives) == 2
        assert len(adr_data.related_changes) == 1


if __name__ == "__main__":
    pytest.main([__file__])
