#!/usr/bin/env python3
"""Tests for README Agent Engine."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from readme_agent_engine import (
    AudienceType,
    Badge,
    ContentDiscoverer,
    ContentRequirements,
    DocumentationResult,
    DocumentationStyle,
    GenerationOptions,
    ImprovementSuggestion,
    ProjectMetadata,
    ProjectType,
    QualityAssessor,
    QualityMetrics,
    ReadmeAgentEngine,
    SectionInfo,
)


class TestReadmeAgentEngine(unittest.TestCase):
    """Test cases for README Agent Engine."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = ReadmeAgentEngine()

        # Create temporary directory for test projects
        self.temp_dir = tempfile.mkdtemp()

        # Sample metadata
        self.test_metadata = ProjectMetadata(
            name="test-project",
            version="1.0.0",
            description="A test project for README generation",
            author="Test Author",
            license="MIT",
            repository_url="https://github.com/test/test-project",
            homepage="https://test-project.example.com",
            languages=["Python"],
            frameworks=["Flask"],
            dependencies={
                "runtime": ["flask>=2.0.0"],
                "development": ["pytest>=6.0.0"],
            },
            entry_points=[{"type": "cli", "command": "test-project"}],
        )

        # Sample content requirements
        self.test_content_requirements = ContentRequirements(
            sections=["overview", "installation", "usage", "api_reference"],
            style=DocumentationStyle.COMPREHENSIVE,
            audience=AudienceType.DEVELOPERS,
        )

        # Sample generation options
        self.test_generation_options = GenerationOptions(
            include_badges=True,
            include_toc=True,
            include_examples=True,
            auto_discover=False,  # Use provided metadata
            template_name="standard",
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_engine_initialization(self) -> None:
        """Test engine initializes properly."""
        assert self.engine is not None
        assert self.engine.logger is not None
        assert self.engine.templates is not None
        assert self.engine.badge_providers is not None
        assert isinstance(self.engine.quality_assessor, QualityAssessor)
        assert isinstance(self.engine.content_discoverer, ContentDiscoverer)

    def test_templates_loading(self) -> None:
        """Test that templates are loaded correctly."""
        templates = self.engine.templates

        required_templates = [
            "standard",
            "library",
            "application",
            "framework",
            "minimal",
        ]
        for template_name in required_templates:
            assert template_name in templates
            assert isinstance(templates[template_name], str)
            assert len(templates[template_name]) > 100

    def test_badge_providers_setup(self) -> None:
        """Test badge providers are set up correctly."""
        providers = self.engine.badge_providers

        required_badges = [
            "build_status",
            "coverage",
            "version",
            "license",
            "downloads",
        ]
        for badge_type in required_badges:
            assert badge_type in providers
            assert isinstance(providers[badge_type], dict)

    def test_project_type_enum(self) -> None:
        """Test ProjectType enum functionality."""
        assert ProjectType.LIBRARY.value == "library"
        assert ProjectType.APPLICATION.value == "application"
        assert ProjectType.TOOL.value == "tool"
        assert ProjectType.FRAMEWORK.value == "framework"

    def test_documentation_style_enum(self) -> None:
        """Test DocumentationStyle enum functionality."""
        assert DocumentationStyle.COMPREHENSIVE.value == "comprehensive"
        assert DocumentationStyle.MINIMAL.value == "minimal"
        assert DocumentationStyle.TECHNICAL.value == "technical"
        assert DocumentationStyle.USER_FRIENDLY.value == "user_friendly"

    def test_audience_type_enum(self) -> None:
        """Test AudienceType enum functionality."""
        assert AudienceType.DEVELOPERS.value == "developers"
        assert AudienceType.END_USERS.value == "end_users"
        assert AudienceType.CONTRIBUTORS.value == "contributors"
        assert AudienceType.MIXED.value == "mixed"

    def test_generate_overview_section(self) -> None:
        """Test overview section generation."""
        content = self.engine._generate_overview_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "# test-project" in content
        assert "A test project for README generation" in content
        assert "Python project" in content
        assert "## Key Benefits" in content
        assert "Easy to use" in content

    def test_generate_installation_section(self) -> None:
        """Test installation section generation."""
        content = self.engine._generate_installation_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## Installation" in content
        assert "pip install" in content
        assert "test-project" in content.lower()
        assert "System Requirements" in content
        assert "Python 3.7" in content

    def test_generate_usage_section(self) -> None:
        """Test usage section generation."""
        content = self.engine._generate_usage_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## Usage" in content
        assert "Quick Start" in content
        assert "```python" in content
        assert "from test_project import" in content
        assert "Advanced Usage" in content

    def test_generate_api_section(self) -> None:
        """Test API reference section generation."""
        content = self.engine._generate_api_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## API Reference" in content
        assert "Main Classes" in content
        assert "Configuration Options" in content
        assert "Error Handling" in content
        assert "| Option | Type |" in content  # Table format

    def test_generate_contributing_section(self) -> None:
        """Test contributing section generation."""
        content = self.engine._generate_contributing_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## Contributing" in content
        assert "Development Setup" in content
        assert "Making Changes" in content
        assert "Code Style" in content
        assert "git checkout -b" in content
        assert "pre-commit install" in content  # Python-specific

    def test_generate_license_section(self) -> None:
        """Test license section generation."""
        content = self.engine._generate_license_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## License" in content
        assert "MIT License" in content
        assert "LICENSE" in content

    def test_generate_features_section(self) -> None:
        """Test features section generation."""
        content = self.engine._generate_features_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## Features" in content
        assert "Core Features" in content
        assert "Fast and Efficient" in content
        assert "Framework Integration" in content
        assert "Flask" in content
        assert "Platform Support" in content

    def test_generate_configuration_section(self) -> None:
        """Test configuration section generation."""
        content = self.engine._generate_configuration_section(
            self.test_metadata, self.test_content_requirements, self.temp_dir,
        )

        assert "## Configuration" in content
        assert "config.yml" in content
        assert "```yaml" in content
        assert "Environment Variables" in content
        assert "| Variable |" in content

    def test_generate_badges(self) -> None:
        """Test badge generation."""
        badges = self.engine._generate_badges(self.test_metadata, self.temp_dir)

        assert isinstance(badges, list)
        # Would have badges if repo info was extracted
        # For now, just test the structure
        for badge in badges:
            assert isinstance(badge, Badge)
            assert badge.name is not None
            assert badge.url is not None
            assert badge.alt_text is not None

    @patch("subprocess.run")
    def test_extract_repo_info_success(self, mock_subprocess) -> None:
        """Test successful repository info extraction."""
        # Mock git command success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/testuser/testrepo.git\n"
        mock_subprocess.return_value = mock_result

        result = self.engine._extract_repo_info(self.temp_dir)

        assert result is not None
        assert result[0] == "testuser"
        assert result[1] == "testrepo"

    @patch("subprocess.run")
    def test_extract_repo_info_ssh(self, mock_subprocess) -> None:
        """Test repository info extraction from SSH URL."""
        # Mock git command success with SSH URL
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git@github.com:testuser/testrepo.git\n"
        mock_subprocess.return_value = mock_result

        result = self.engine._extract_repo_info(self.temp_dir)

        assert result is not None
        assert result[0] == "testuser"
        assert result[1] == "testrepo"

    @patch("subprocess.run")
    def test_extract_repo_info_failure(self, mock_subprocess) -> None:
        """Test repository info extraction failure."""
        # Mock git command failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        result = self.engine._extract_repo_info(self.temp_dir)

        assert result is None

    def test_apply_template(self) -> None:
        """Test template application."""
        template = "{PROJECT_NAME}\n\n{BADGES}\n\n{BRIEF_DESCRIPTION}"
        sections = {"overview": "Test overview"}
        badges = [
            Badge(name="test", url="http://test.com", alt_text="Test", provider="test"),
        ]

        result = self.engine._apply_template(
            template, self.test_metadata, sections, badges, self.test_generation_options,
        )

        assert "test-project" in result
        assert "![Test](http://test.com)" in result
        assert "A test project for README generation" in result

    def test_generate_quick_start(self) -> None:
        """Test quick start generation."""
        quick_start = self.engine._generate_quick_start(self.test_metadata)

        assert "```python" in quick_start
        assert "test_project" in quick_start
        assert "import" in quick_start

    def test_generate_toc(self) -> None:
        """Test table of contents generation."""
        content = """# Main Title
## Section 1
### Subsection 1.1
## Section 2
"""

        toc = self.engine._generate_toc(content)

        assert isinstance(toc, list)
        assert len(toc) > 0
        assert "[Section 1](#section-1)" in toc[0]
        assert "[Subsection 1.1](#subsection-11)" in toc[1]
        assert "  " in toc[1]  # Indentation for subsection

    def test_insert_toc(self) -> None:
        """Test table of contents insertion."""
        content = """# Main Title

Some content here.

## Section 1

More content."""

        toc = ["- [Section 1](#section-1)"]
        result = self.engine._insert_toc(content, toc)

        assert "## Table of Contents" in result
        assert "- [Section 1](#section-1)" in result
        # TOC should be inserted after title
        lines = result.split("\n")
        toc_index = next(
            i for i, line in enumerate(lines) if "Table of Contents" in line
        )
        title_index = next(
            i for i, line in enumerate(lines) if line.startswith("# Main Title")
        )
        assert toc_index > title_index

    def test_calculate_complexity_score(self) -> None:
        """Test complexity score calculation."""
        simple_content = "This is a simple document with short sentences."
        complex_content = """This is a more complex document with longer sentences and more technical content.

```python
# Code examples add complexity
def complex_function():
    pass
```

[Links](http://example.com) also add complexity.
"""

        simple_score = self.engine._calculate_complexity_score(simple_content)
        complex_score = self.engine._calculate_complexity_score(complex_content)

        assert isinstance(simple_score, float)
        assert isinstance(complex_score, float)
        assert complex_score > simple_score

    def test_calculate_completeness(self) -> None:
        """Test completeness calculation."""
        sections_generated = [
            SectionInfo("overview", 100, True, 80.0, "content"),
            SectionInfo("installation", 150, True, 85.0, "content"),
            SectionInfo("usage", 200, True, 90.0, "content"),
        ]
        requested_sections = ["overview", "installation", "usage", "api_reference"]

        completeness = self.engine._calculate_completeness(
            sections_generated, requested_sections,
        )

        assert completeness == 75.0  # 3 of 4 sections

    def test_calculate_section_quality(self) -> None:
        """Test section quality calculation."""
        high_quality_content = """## Installation

This is a comprehensive installation section with examples:

```bash
pip install package
```

For more information, see [docs](http://docs.example.com).

### Prerequisites

Requirements are listed below.
"""

        low_quality_content = "## Installation\n\nInstall it."

        high_score = self.engine._calculate_section_quality(
            high_quality_content, "installation",
        )
        low_score = self.engine._calculate_section_quality(
            low_quality_content, "installation",
        )

        assert high_score > low_score
        assert high_score > 50.0
        assert low_score < 50.0

    def test_generate_improvement_suggestions(self) -> None:
        """Test improvement suggestions generation."""
        sections = [
            SectionInfo("overview", 50, True, 40.0, "short content"),  # Low quality
            SectionInfo(
                "installation", 200, True, 85.0, "good content",
            ),  # Good quality
        ]

        quality_metrics = QualityMetrics(
            clarity=75.0,
            completeness=60.0,  # Low completeness
            accuracy=90.0,
            usefulness=80.0,
            overall_score=76.25,
        )

        suggestions = self.engine._generate_improvement_suggestions(
            sections, quality_metrics,
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Should suggest improving low-quality overview section
        overview_suggestions = [s for s in suggestions if s.section == "overview"]
        assert len(overview_suggestions) > 0
        assert overview_suggestions[0].priority == "high"

        # Should suggest adding missing sections due to low completeness
        completeness_suggestions = [
            s for s in suggestions if "missing" in s.suggestion.lower()
        ]
        assert len(completeness_suggestions) > 0

    def test_generate_readme_success(self) -> None:
        """Test successful README generation."""
        result = self.engine.generate_readme(
            self.temp_dir,
            "test-project",
            ProjectType.LIBRARY,
            self.test_content_requirements,
            self.test_generation_options,
        )

        assert isinstance(result, DocumentationResult)
        assert result.success
        assert result.operation == "generate"
        assert result.readme_content is not None
        assert len(result.sections_generated) > 0
        assert "word_count" in result.metadata
        assert "quality_metrics" in result.analysis

        # Check README content
        assert "# test-project" in result.readme_content
        assert "## Installation" in result.readme_content
        assert "## Usage" in result.readme_content

    def test_parse_existing_sections(self) -> None:
        """Test parsing of existing README sections."""
        content = """# Main Title

Some intro content.

## Installation

Install with pip.

## Usage

Use like this:

```python
import package
```

## License

MIT License
"""

        sections = self.engine._parse_existing_sections(content)

        assert "installation" in sections
        assert "usage" in sections
        assert "license" in sections
        assert "Install with pip" in sections["installation"]
        assert "```python" in sections["usage"]

    def test_identify_missing_sections(self) -> None:
        """Test identification of missing standard sections."""
        existing_sections = {"installation": "content", "usage": "content"}

        missing = self.engine._identify_missing_sections(existing_sections)

        assert "api_reference" in missing
        assert "contributing" in missing
        assert "license" in missing
        assert "installation" not in missing
        assert "usage" not in missing

    def test_analyze_structure(self) -> None:
        """Test document structure analysis."""
        content = """# Main Title
## Section 1
### Subsection 1.1
#### Sub-subsection
## Section 2
"""

        structure = self.engine._analyze_structure(content)

        assert "heading_count" in structure
        assert "max_heading_level" in structure
        assert "has_proper_hierarchy" in structure
        assert structure["heading_count"] == 5
        assert structure["max_heading_level"] == 4
        assert structure["has_proper_hierarchy"]

    def test_check_heading_hierarchy_valid(self) -> None:
        """Test valid heading hierarchy checking."""
        headings = [
            {"level": 1, "text": "Title"},
            {"level": 2, "text": "Section"},
            {"level": 3, "text": "Subsection"},
            {"level": 2, "text": "Another Section"},
        ]

        result = self.engine._check_heading_hierarchy(headings)
        assert result

    def test_check_heading_hierarchy_invalid(self) -> None:
        """Test invalid heading hierarchy checking."""
        # Skipped level (1 to 3)
        invalid_headings = [
            {"level": 1, "text": "Title"},
            {"level": 3, "text": "Subsection"},  # Skipped level 2
        ]

        result = self.engine._check_heading_hierarchy(invalid_headings)
        assert not result

        # Doesn't start with level 1
        invalid_start = [{"level": 2, "text": "Section"}]

        result = self.engine._check_heading_hierarchy(invalid_start)
        assert not result

    def test_analyze_links(self) -> None:
        """Test link analysis."""
        content = """# Test Document

Check out [our docs](https://example.com) and [internal section](#usage).

Also see [GitHub](https://github.com/test/repo).
"""

        analysis = self.engine._analyze_links(content)

        assert "total_links" in analysis
        assert "internal_links" in analysis
        assert "external_links" in analysis
        assert analysis["total_links"] == 3
        assert analysis["internal_links"] == 1  # #usage
        assert analysis["external_links"] == 2  # https links

    def test_analyze_readme(self) -> None:
        """Test README analysis."""
        # Create a temporary README file
        readme_content = """# Test Project

A test project for analysis.

## Installation

Install with pip:

```bash
pip install test-project
```

## Usage

Use like this:

```python
import test_project
```

## License

MIT License
"""

        readme_path = os.path.join(self.temp_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write(readme_content)

        result = self.engine.analyze_readme(readme_path, "detailed")

        assert result.success
        assert result.operation == "analyze"
        assert result.readme_content == readme_content
        assert "sections_found" in result.analysis
        assert "missing_sections" in result.analysis
        assert "quality_metrics" in result.analysis
        assert "word_count" in result.metadata

    def test_process_request_generate(self) -> None:
        """Test processing generate request."""
        request = {
            "operation": "generate",
            "target": {
                "repository_path": self.temp_dir,
                "project_name": "Test API Project",
                "project_type": "library",
            },
            "content_requirements": {
                "sections": ["overview", "installation", "usage"],
                "style": "comprehensive",
                "audience": "developers",
            },
            "options": {
                "include_badges": True,
                "include_toc": False,
                "template_name": "standard",
                "auto_discover": False,
            },
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert response["operation"] == "generate"
        assert "readme_content" in response
        assert "sections_generated" in response

    def test_process_request_analyze(self) -> None:
        """Test processing analyze request."""
        # Create test README
        readme_path = os.path.join(self.temp_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Test\n\nA test project.\n")

        request = {
            "operation": "analyze",
            "target": {"readme_path": readme_path},
            "analysis_options": {"depth": "detailed"},
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert response["operation"] == "analyze"
        assert "analysis" in response

    def test_process_request_unsupported(self) -> None:
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation"}
        response = self.engine.process_request(request)

        assert not response["success"]
        assert "Unsupported operation" in response["error"]

    def test_content_discoverer_initialization(self) -> None:
        """Test ContentDiscoverer initialization."""
        discoverer = ContentDiscoverer()
        assert discoverer is not None

    def test_discover_languages(self) -> None:
        """Test language discovery."""
        discoverer = ContentDiscoverer()

        # Create test files
        test_project = Path(self.temp_dir)
        (test_project / "main.py").touch()
        (test_project / "app.js").touch()
        (test_project / "styles.css").touch()

        languages = discoverer._discover_languages(test_project)

        assert "Python" in languages
        assert "JavaScript" in languages

    def test_parse_setup_py(self) -> None:
        """Test setup.py parsing."""
        discoverer = ContentDiscoverer()
        metadata = ProjectMetadata(
            name="",
            version=None,
            description=None,
            author=None,
            license=None,
            repository_url=None,
            homepage=None,
            languages=[],
            frameworks=[],
            dependencies={"runtime": [], "development": []},
            entry_points=[],
        )

        # Create test setup.py
        setup_content = """
from setuptools import setup

setup(
    name="test-package",
    version="1.2.3",
    description="A test package",
    author="Test Author"
)
"""

        setup_path = Path(self.temp_dir) / "setup.py"
        with open(setup_path, "w") as f:
            f.write(setup_content)

        discoverer._parse_setup_py(setup_path, metadata)

        assert metadata.name == "test-package"
        assert metadata.version == "1.2.3"
        assert metadata.description == "A test package"

    def test_parse_package_json(self) -> None:
        """Test package.json parsing."""
        discoverer = ContentDiscoverer()
        metadata = ProjectMetadata(
            name="",
            version=None,
            description=None,
            author=None,
            license=None,
            repository_url=None,
            homepage=None,
            languages=[],
            frameworks=[],
            dependencies={"runtime": [], "development": []},
            entry_points=[],
        )

        # Create test package.json
        package_data = {
            "name": "test-package",
            "version": "2.1.0",
            "description": "A Node.js test package",
            "author": "Node Author",
            "license": "Apache-2.0",
            "dependencies": {"express": "^4.18.0", "lodash": "^4.17.0"},
            "devDependencies": {"jest": "^28.0.0", "eslint": "^8.0.0"},
        }

        package_path = Path(self.temp_dir) / "package.json"
        with open(package_path, "w") as f:
            json.dump(package_data, f)

        discoverer._discover_nodejs_info(Path(self.temp_dir), metadata)

        assert metadata.name == "test-package"
        assert metadata.version == "2.1.0"
        assert metadata.description == "A Node.js test package"
        assert metadata.license == "Apache-2.0"
        assert "express" in metadata.dependencies["runtime"]
        assert "jest" in metadata.dependencies["development"]

    def test_discover_license(self) -> None:
        """Test license discovery."""
        discoverer = ContentDiscoverer()

        # Create test license file
        license_content = """MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted, free of charge..."""

        license_path = Path(self.temp_dir) / "LICENSE"
        with open(license_path, "w") as f:
            f.write(license_content)

        license_type = discoverer._discover_license(Path(self.temp_dir))

        assert license_type == "MIT"

    def test_quality_assessor_initialization(self) -> None:
        """Test QualityAssessor initialization."""
        assessor = QualityAssessor()
        assert assessor is not None

    def test_assess_quality(self) -> None:
        """Test quality assessment."""
        assessor = QualityAssessor()

        high_quality_content = """# Test Project

A comprehensive test project with detailed documentation.

## Installation

Install the package:

```bash
pip install test-project
```

## Usage

Here's how to use it:

```python
import test_project
result = test_project.process()
```

## API Reference

Complete API documentation with examples.

## Contributing

Guidelines for contributors.

## License

MIT License
"""

        sections = [
            SectionInfo("installation", 100, True, 85.0, "content"),
            SectionInfo("usage", 150, True, 90.0, "content"),
        ]

        metrics = assessor.assess_quality(high_quality_content, sections)

        assert isinstance(metrics, QualityMetrics)
        assert metrics.clarity > 70.0
        assert metrics.completeness > 70.0
        assert metrics.accuracy > 70.0
        assert metrics.usefulness > 70.0
        assert metrics.overall_score > 70.0

    def test_assess_clarity(self) -> None:
        """Test clarity assessment."""
        assessor = QualityAssessor()

        clear_content = """# Clear Title

## Well Structured Section

This content has **good formatting** and clear structure.

```bash
# With examples
echo "hello"
```
"""

        unclear_content = "some unclear text without structure"

        clear_score = assessor._assess_clarity(clear_content)
        unclear_score = assessor._assess_clarity(unclear_content)

        assert clear_score > unclear_score
        assert clear_score > 80.0

    def test_dataclass_functionality(self) -> None:
        """Test dataclass functionality."""
        # Test ContentRequirements
        content_req = ContentRequirements(
            sections=["overview", "usage"],
            style=DocumentationStyle.MINIMAL,
            audience=AudienceType.END_USERS,
        )

        assert len(content_req.sections) == 2
        assert content_req.style == DocumentationStyle.MINIMAL
        assert content_req.include_api  # Default value

        # Test GenerationOptions
        options = GenerationOptions(include_badges=False, template_name="custom")

        assert not options.include_badges
        assert options.include_toc  # Default value
        assert options.template_name == "custom"

        # Test ProjectMetadata
        metadata = ProjectMetadata(
            name="test",
            version="1.0",
            description="desc",
            author=None,
            license=None,
            repository_url=None,
            homepage=None,
            languages=["Python"],
            frameworks=[],
            dependencies={"runtime": [], "development": []},
            entry_points=[],
        )

        assert metadata.name == "test"
        assert metadata.author is None
        assert len(metadata.languages) == 1

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.engine.logger is not None
        assert self.engine.logger.name == "readme_agent"

        import logging

        assert self.engine.logger.level == logging.INFO

    def test_section_info_dataclass(self) -> None:
        """Test SectionInfo dataclass."""
        section = SectionInfo(
            name="test_section",
            content_length=500,
            auto_generated=True,
            quality_score=85.5,
            content="Test content",
        )

        assert section.name == "test_section"
        assert section.content_length == 500
        assert section.auto_generated
        assert section.quality_score == 85.5
        assert section.content == "Test content"

    def test_badge_dataclass(self) -> None:
        """Test Badge dataclass."""
        badge = Badge(
            name="build",
            url="https://img.shields.io/badge/build-passing-green",
            alt_text="Build Status",
            provider="github",
        )

        assert badge.name == "build"
        assert badge.url.startswith("https://")
        assert badge.alt_text == "Build Status"
        assert badge.provider == "github"

    def test_improvement_suggestion_dataclass(self) -> None:
        """Test ImprovementSuggestion dataclass."""
        suggestion = ImprovementSuggestion(
            section="installation",
            priority="high",
            suggestion="Add more examples",
            implementation="Include code examples",
        )

        assert suggestion.section == "installation"
        assert suggestion.priority == "high"
        assert "examples" in suggestion.suggestion
        assert suggestion.implementation is not None

    def test_documentation_result_dataclass(self) -> None:
        """Test DocumentationResult dataclass."""
        result = DocumentationResult(
            success=True,
            operation="generate",
            readme_content="# Test",
            sections_generated=[],
            metadata={"word_count": 2},
            analysis={"quality": 85.0},
            assets={"files": []},
            warnings=["Warning 1"],
            errors=[],
        )

        assert result.success
        assert result.operation == "generate"
        assert result.readme_content == "# Test"
        assert len(result.warnings) == 1
        assert len(result.errors) == 0


if __name__ == "__main__":
    unittest.main()
