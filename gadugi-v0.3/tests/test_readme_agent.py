#!/usr/bin/env python3
"""
Tests for README Agent Engine
"""

import unittest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'orchestrator'))

from readme_agent_engine import (
    ReadmeAgentEngine,
    ProjectType,
    DocumentationStyle,
    AudienceType,
    ContentRequirements,
    GenerationOptions,
    ProjectMetadata,
    SectionInfo,
    QualityMetrics,
    Badge,
    ImprovementSuggestion,
    DocumentationResult,
    ContentDiscoverer,
    QualityAssessor
)


class TestReadmeAgentEngine(unittest.TestCase):
    """Test cases for README Agent Engine."""
    
    def setUp(self):
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
            dependencies={"runtime": ["flask>=2.0.0"], "development": ["pytest>=6.0.0"]},
            entry_points=[{"type": "cli", "command": "test-project"}]
        )
        
        # Sample content requirements
        self.test_content_requirements = ContentRequirements(
            sections=["overview", "installation", "usage", "api_reference"],
            style=DocumentationStyle.COMPREHENSIVE,
            audience=AudienceType.DEVELOPERS
        )
        
        # Sample generation options
        self.test_generation_options = GenerationOptions(
            include_badges=True,
            include_toc=True,
            include_examples=True,
            auto_discover=False,  # Use provided metadata
            template_name="standard"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_engine_initialization(self):
        """Test engine initializes properly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.logger)
        self.assertIsNotNone(self.engine.templates)
        self.assertIsNotNone(self.engine.badge_providers)
        self.assertIsInstance(self.engine.quality_assessor, QualityAssessor)
        self.assertIsInstance(self.engine.content_discoverer, ContentDiscoverer)
    
    def test_templates_loading(self):
        """Test that templates are loaded correctly."""
        templates = self.engine.templates
        
        required_templates = ["standard", "library", "application", "framework", "minimal"]
        for template_name in required_templates:
            self.assertIn(template_name, templates)
            self.assertIsInstance(templates[template_name], str)
            self.assertGreater(len(templates[template_name]), 100)
    
    def test_badge_providers_setup(self):
        """Test badge providers are set up correctly."""
        providers = self.engine.badge_providers
        
        required_badges = ["build_status", "coverage", "version", "license", "downloads"]
        for badge_type in required_badges:
            self.assertIn(badge_type, providers)
            self.assertIsInstance(providers[badge_type], dict)
    
    def test_project_type_enum(self):
        """Test ProjectType enum functionality."""
        self.assertEqual(ProjectType.LIBRARY.value, "library")
        self.assertEqual(ProjectType.APPLICATION.value, "application")
        self.assertEqual(ProjectType.TOOL.value, "tool")
        self.assertEqual(ProjectType.FRAMEWORK.value, "framework")
    
    def test_documentation_style_enum(self):
        """Test DocumentationStyle enum functionality."""
        self.assertEqual(DocumentationStyle.COMPREHENSIVE.value, "comprehensive")
        self.assertEqual(DocumentationStyle.MINIMAL.value, "minimal")
        self.assertEqual(DocumentationStyle.TECHNICAL.value, "technical")
        self.assertEqual(DocumentationStyle.USER_FRIENDLY.value, "user_friendly")
    
    def test_audience_type_enum(self):
        """Test AudienceType enum functionality."""
        self.assertEqual(AudienceType.DEVELOPERS.value, "developers")
        self.assertEqual(AudienceType.END_USERS.value, "end_users")
        self.assertEqual(AudienceType.CONTRIBUTORS.value, "contributors")
        self.assertEqual(AudienceType.MIXED.value, "mixed")
    
    def test_generate_overview_section(self):
        """Test overview section generation."""
        content = self.engine._generate_overview_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("# test-project", content)
        self.assertIn("A test project for README generation", content)
        self.assertIn("Python project", content)
        self.assertIn("## Key Benefits", content)
        self.assertIn("Easy to use", content)
    
    def test_generate_installation_section(self):
        """Test installation section generation."""
        content = self.engine._generate_installation_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## Installation", content)
        self.assertIn("pip install", content)
        self.assertIn("test-project", content.lower())
        self.assertIn("System Requirements", content)
        self.assertIn("Python 3.7", content)
    
    def test_generate_usage_section(self):
        """Test usage section generation."""
        content = self.engine._generate_usage_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## Usage", content)
        self.assertIn("Quick Start", content)
        self.assertIn("```python", content)
        self.assertIn("from test_project import", content)
        self.assertIn("Advanced Usage", content)
    
    def test_generate_api_section(self):
        """Test API reference section generation."""
        content = self.engine._generate_api_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## API Reference", content)
        self.assertIn("Main Classes", content)
        self.assertIn("Configuration Options", content)
        self.assertIn("Error Handling", content)
        self.assertIn("| Option | Type |", content)  # Table format
    
    def test_generate_contributing_section(self):
        """Test contributing section generation."""
        content = self.engine._generate_contributing_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## Contributing", content)
        self.assertIn("Development Setup", content)
        self.assertIn("Making Changes", content)
        self.assertIn("Code Style", content)
        self.assertIn("git checkout -b", content)
        self.assertIn("pre-commit install", content)  # Python-specific
    
    def test_generate_license_section(self):
        """Test license section generation."""
        content = self.engine._generate_license_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## License", content)
        self.assertIn("MIT License", content)
        self.assertIn("LICENSE", content)
    
    def test_generate_features_section(self):
        """Test features section generation."""
        content = self.engine._generate_features_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## Features", content)
        self.assertIn("Core Features", content)
        self.assertIn("Fast and Efficient", content)
        self.assertIn("Framework Integration", content)
        self.assertIn("Flask", content)
        self.assertIn("Platform Support", content)
    
    def test_generate_configuration_section(self):
        """Test configuration section generation."""
        content = self.engine._generate_configuration_section(
            self.test_metadata,
            self.test_content_requirements,
            self.temp_dir
        )
        
        self.assertIn("## Configuration", content)
        self.assertIn("config.yml", content)
        self.assertIn("```yaml", content)
        self.assertIn("Environment Variables", content)
        self.assertIn("| Variable |", content)
    
    def test_generate_badges(self):
        """Test badge generation."""
        badges = self.engine._generate_badges(self.test_metadata, self.temp_dir)
        
        self.assertIsInstance(badges, list)
        # Would have badges if repo info was extracted
        # For now, just test the structure
        for badge in badges:
            self.assertIsInstance(badge, Badge)
            self.assertIsNotNone(badge.name)
            self.assertIsNotNone(badge.url)
            self.assertIsNotNone(badge.alt_text)
    
    @patch('subprocess.run')
    def test_extract_repo_info_success(self, mock_subprocess):
        """Test successful repository info extraction."""
        # Mock git command success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/testuser/testrepo.git\n"
        mock_subprocess.return_value = mock_result
        
        result = self.engine._extract_repo_info(self.temp_dir)
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "testuser")
        self.assertEqual(result[1], "testrepo")
    
    @patch('subprocess.run')
    def test_extract_repo_info_ssh(self, mock_subprocess):
        """Test repository info extraction from SSH URL."""
        # Mock git command success with SSH URL
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git@github.com:testuser/testrepo.git\n"
        mock_subprocess.return_value = mock_result
        
        result = self.engine._extract_repo_info(self.temp_dir)
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "testuser")
        self.assertEqual(result[1], "testrepo")
    
    @patch('subprocess.run')
    def test_extract_repo_info_failure(self, mock_subprocess):
        """Test repository info extraction failure."""
        # Mock git command failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        result = self.engine._extract_repo_info(self.temp_dir)
        
        self.assertIsNone(result)
    
    def test_apply_template(self):
        """Test template application."""
        template = "{PROJECT_NAME}\n\n{BADGES}\n\n{BRIEF_DESCRIPTION}"
        sections = {"overview": "Test overview"}
        badges = [
            Badge(name="test", url="http://test.com", alt_text="Test", provider="test")
        ]
        
        result = self.engine._apply_template(
            template,
            self.test_metadata,
            sections,
            badges,
            self.test_generation_options
        )
        
        self.assertIn("test-project", result)
        self.assertIn("![Test](http://test.com)", result)
        self.assertIn("A test project for README generation", result)
    
    def test_generate_quick_start(self):
        """Test quick start generation."""
        quick_start = self.engine._generate_quick_start(self.test_metadata)
        
        self.assertIn("```python", quick_start)
        self.assertIn("test_project", quick_start)
        self.assertIn("import", quick_start)
    
    def test_generate_toc(self):
        """Test table of contents generation."""
        content = """# Main Title
## Section 1
### Subsection 1.1
## Section 2
"""
        
        toc = self.engine._generate_toc(content)
        
        self.assertIsInstance(toc, list)
        self.assertGreater(len(toc), 0)
        self.assertIn("[Section 1](#section-1)", toc[0])
        self.assertIn("[Subsection 1.1](#subsection-11)", toc[1])
        self.assertIn("  ", toc[1])  # Indentation for subsection
    
    def test_insert_toc(self):
        """Test table of contents insertion."""
        content = """# Main Title

Some content here.

## Section 1

More content."""
        
        toc = ["- [Section 1](#section-1)"]
        result = self.engine._insert_toc(content, toc)
        
        self.assertIn("## Table of Contents", result)
        self.assertIn("- [Section 1](#section-1)", result)
        # TOC should be inserted after title
        lines = result.split('\n')
        toc_index = next(i for i, line in enumerate(lines) if "Table of Contents" in line)
        title_index = next(i for i, line in enumerate(lines) if line.startswith("# Main Title"))
        self.assertGreater(toc_index, title_index)
    
    def test_calculate_complexity_score(self):
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
        
        self.assertIsInstance(simple_score, float)
        self.assertIsInstance(complex_score, float)
        self.assertGreater(complex_score, simple_score)
    
    def test_calculate_completeness(self):
        """Test completeness calculation."""
        sections_generated = [
            SectionInfo("overview", 100, True, 80.0, "content"),
            SectionInfo("installation", 150, True, 85.0, "content"),
            SectionInfo("usage", 200, True, 90.0, "content")
        ]
        requested_sections = ["overview", "installation", "usage", "api_reference"]
        
        completeness = self.engine._calculate_completeness(sections_generated, requested_sections)
        
        self.assertEqual(completeness, 75.0)  # 3 of 4 sections
    
    def test_calculate_section_quality(self):
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
        
        high_score = self.engine._calculate_section_quality(high_quality_content, "installation")
        low_score = self.engine._calculate_section_quality(low_quality_content, "installation")
        
        self.assertGreater(high_score, low_score)
        self.assertGreater(high_score, 50.0)
        self.assertLess(low_score, 50.0)
    
    def test_generate_improvement_suggestions(self):
        """Test improvement suggestions generation."""
        sections = [
            SectionInfo("overview", 50, True, 40.0, "short content"),  # Low quality
            SectionInfo("installation", 200, True, 85.0, "good content")  # Good quality
        ]
        
        quality_metrics = QualityMetrics(
            clarity=75.0,
            completeness=60.0,  # Low completeness
            accuracy=90.0,
            usefulness=80.0,
            overall_score=76.25
        )
        
        suggestions = self.engine._generate_improvement_suggestions(sections, quality_metrics)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest improving low-quality overview section
        overview_suggestions = [s for s in suggestions if s.section == "overview"]
        self.assertGreater(len(overview_suggestions), 0)
        self.assertEqual(overview_suggestions[0].priority, "high")
        
        # Should suggest adding missing sections due to low completeness
        completeness_suggestions = [s for s in suggestions if "missing" in s.suggestion.lower()]
        self.assertGreater(len(completeness_suggestions), 0)
    
    def test_generate_readme_success(self):
        """Test successful README generation."""
        result = self.engine.generate_readme(
            self.temp_dir,
            "test-project",
            ProjectType.LIBRARY,
            self.test_content_requirements,
            self.test_generation_options
        )
        
        self.assertIsInstance(result, DocumentationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "generate")
        self.assertIsNotNone(result.readme_content)
        self.assertGreater(len(result.sections_generated), 0)
        self.assertIn("word_count", result.metadata)
        self.assertIn("quality_metrics", result.analysis)
        
        # Check README content
        self.assertIn("# test-project", result.readme_content)
        self.assertIn("## Installation", result.readme_content)
        self.assertIn("## Usage", result.readme_content)
    
    def test_parse_existing_sections(self):
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
        
        self.assertIn("installation", sections)
        self.assertIn("usage", sections)
        self.assertIn("license", sections)
        self.assertIn("Install with pip", sections["installation"])
        self.assertIn("```python", sections["usage"])
    
    def test_identify_missing_sections(self):
        """Test identification of missing standard sections."""
        existing_sections = {
            "installation": "content",
            "usage": "content"
        }
        
        missing = self.engine._identify_missing_sections(existing_sections)
        
        self.assertIn("api_reference", missing)
        self.assertIn("contributing", missing)
        self.assertIn("license", missing)
        self.assertNotIn("installation", missing)
        self.assertNotIn("usage", missing)
    
    def test_analyze_structure(self):
        """Test document structure analysis."""
        content = """# Main Title
## Section 1
### Subsection 1.1
#### Sub-subsection
## Section 2
"""
        
        structure = self.engine._analyze_structure(content)
        
        self.assertIn("heading_count", structure)
        self.assertIn("max_heading_level", structure)
        self.assertIn("has_proper_hierarchy", structure)
        self.assertEqual(structure["heading_count"], 5)
        self.assertEqual(structure["max_heading_level"], 4)
        self.assertTrue(structure["has_proper_hierarchy"])
    
    def test_check_heading_hierarchy_valid(self):
        """Test valid heading hierarchy checking."""
        headings = [
            {"level": 1, "text": "Title"},
            {"level": 2, "text": "Section"},
            {"level": 3, "text": "Subsection"},
            {"level": 2, "text": "Another Section"}
        ]
        
        result = self.engine._check_heading_hierarchy(headings)
        self.assertTrue(result)
    
    def test_check_heading_hierarchy_invalid(self):
        """Test invalid heading hierarchy checking."""
        # Skipped level (1 to 3)
        invalid_headings = [
            {"level": 1, "text": "Title"},
            {"level": 3, "text": "Subsection"}  # Skipped level 2
        ]
        
        result = self.engine._check_heading_hierarchy(invalid_headings)
        self.assertFalse(result)
        
        # Doesn't start with level 1
        invalid_start = [
            {"level": 2, "text": "Section"}
        ]
        
        result = self.engine._check_heading_hierarchy(invalid_start)
        self.assertFalse(result)
    
    def test_analyze_links(self):
        """Test link analysis."""
        content = """# Test Document

Check out [our docs](https://example.com) and [internal section](#usage).

Also see [GitHub](https://github.com/test/repo).
"""
        
        analysis = self.engine._analyze_links(content)
        
        self.assertIn("total_links", analysis)
        self.assertIn("internal_links", analysis)
        self.assertIn("external_links", analysis)
        self.assertEqual(analysis["total_links"], 3)
        self.assertEqual(analysis["internal_links"], 1)  # #usage
        self.assertEqual(analysis["external_links"], 2)  # https links
    
    def test_analyze_readme(self):
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
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        result = self.engine.analyze_readme(readme_path, "detailed")
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "analyze")
        self.assertEqual(result.readme_content, readme_content)
        self.assertIn("sections_found", result.analysis)
        self.assertIn("missing_sections", result.analysis)
        self.assertIn("quality_metrics", result.analysis)
        self.assertIn("word_count", result.metadata)
    
    def test_process_request_generate(self):
        """Test processing generate request."""
        request = {
            "operation": "generate",
            "target": {
                "repository_path": self.temp_dir,
                "project_name": "Test API Project",
                "project_type": "library"
            },
            "content_requirements": {
                "sections": ["overview", "installation", "usage"],
                "style": "comprehensive",
                "audience": "developers"
            },
            "options": {
                "include_badges": True,
                "include_toc": False,
                "template_name": "standard",
                "auto_discover": False
            }
        }
        
        response = self.engine.process_request(request)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["operation"], "generate")
        self.assertIn("readme_content", response)
        self.assertIn("sections_generated", response)
    
    def test_process_request_analyze(self):
        """Test processing analyze request."""
        # Create test README
        readme_path = os.path.join(self.temp_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write("# Test\n\nA test project.\n")
        
        request = {
            "operation": "analyze",
            "target": {
                "readme_path": readme_path
            },
            "analysis_options": {
                "depth": "detailed"
            }
        }
        
        response = self.engine.process_request(request)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["operation"], "analyze")
        self.assertIn("analysis", response)
    
    def test_process_request_unsupported(self):
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation"}
        response = self.engine.process_request(request)
        
        self.assertFalse(response["success"])
        self.assertIn("Unsupported operation", response["error"])
    
    def test_content_discoverer_initialization(self):
        """Test ContentDiscoverer initialization."""
        discoverer = ContentDiscoverer()
        self.assertIsNotNone(discoverer)
    
    def test_discover_languages(self):
        """Test language discovery."""
        discoverer = ContentDiscoverer()
        
        # Create test files
        test_project = Path(self.temp_dir)
        (test_project / "main.py").touch()
        (test_project / "app.js").touch()
        (test_project / "styles.css").touch()
        
        languages = discoverer._discover_languages(test_project)
        
        self.assertIn("Python", languages)
        self.assertIn("JavaScript", languages)
    
    def test_parse_setup_py(self):
        """Test setup.py parsing."""
        discoverer = ContentDiscoverer()
        metadata = ProjectMetadata(
            name="", version=None, description=None, author=None,
            license=None, repository_url=None, homepage=None,
            languages=[], frameworks=[], dependencies={"runtime": [], "development": []},
            entry_points=[]
        )
        
        # Create test setup.py
        setup_content = '''
from setuptools import setup

setup(
    name="test-package",
    version="1.2.3",
    description="A test package",
    author="Test Author"
)
'''
        
        setup_path = Path(self.temp_dir) / "setup.py"
        with open(setup_path, 'w') as f:
            f.write(setup_content)
        
        discoverer._parse_setup_py(setup_path, metadata)
        
        self.assertEqual(metadata.name, "test-package")
        self.assertEqual(metadata.version, "1.2.3")
        self.assertEqual(metadata.description, "A test package")
    
    def test_parse_package_json(self):
        """Test package.json parsing."""
        discoverer = ContentDiscoverer()
        metadata = ProjectMetadata(
            name="", version=None, description=None, author=None,
            license=None, repository_url=None, homepage=None,
            languages=[], frameworks=[], dependencies={"runtime": [], "development": []},
            entry_points=[]
        )
        
        # Create test package.json
        package_data = {
            "name": "test-package",
            "version": "2.1.0",
            "description": "A Node.js test package",
            "author": "Node Author",
            "license": "Apache-2.0",
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.0"
            },
            "devDependencies": {
                "jest": "^28.0.0",
                "eslint": "^8.0.0"
            }
        }
        
        package_path = Path(self.temp_dir) / "package.json"
        with open(package_path, 'w') as f:
            json.dump(package_data, f)
        
        discoverer._discover_nodejs_info(Path(self.temp_dir), metadata)
        
        self.assertEqual(metadata.name, "test-package")
        self.assertEqual(metadata.version, "2.1.0")
        self.assertEqual(metadata.description, "A Node.js test package")
        self.assertEqual(metadata.license, "Apache-2.0")
        self.assertIn("express", metadata.dependencies["runtime"])
        self.assertIn("jest", metadata.dependencies["development"])
    
    def test_discover_license(self):
        """Test license discovery."""
        discoverer = ContentDiscoverer()
        
        # Create test license file
        license_content = """MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted, free of charge..."""
        
        license_path = Path(self.temp_dir) / "LICENSE"
        with open(license_path, 'w') as f:
            f.write(license_content)
        
        license_type = discoverer._discover_license(Path(self.temp_dir))
        
        self.assertEqual(license_type, "MIT")
    
    def test_quality_assessor_initialization(self):
        """Test QualityAssessor initialization."""
        assessor = QualityAssessor()
        self.assertIsNotNone(assessor)
    
    def test_assess_quality(self):
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
            SectionInfo("usage", 150, True, 90.0, "content")
        ]
        
        metrics = assessor.assess_quality(high_quality_content, sections)
        
        self.assertIsInstance(metrics, QualityMetrics)
        self.assertGreater(metrics.clarity, 70.0)
        self.assertGreater(metrics.completeness, 70.0)
        self.assertGreater(metrics.accuracy, 70.0)
        self.assertGreater(metrics.usefulness, 70.0)
        self.assertGreater(metrics.overall_score, 70.0)
    
    def test_assess_clarity(self):
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
        
        self.assertGreater(clear_score, unclear_score)
        self.assertGreater(clear_score, 80.0)
    
    def test_dataclass_functionality(self):
        """Test dataclass functionality."""
        # Test ContentRequirements
        content_req = ContentRequirements(
            sections=["overview", "usage"],
            style=DocumentationStyle.MINIMAL,
            audience=AudienceType.END_USERS
        )
        
        self.assertEqual(len(content_req.sections), 2)
        self.assertEqual(content_req.style, DocumentationStyle.MINIMAL)
        self.assertTrue(content_req.include_api)  # Default value
        
        # Test GenerationOptions
        options = GenerationOptions(
            include_badges=False,
            template_name="custom"
        )
        
        self.assertFalse(options.include_badges)
        self.assertTrue(options.include_toc)  # Default value
        self.assertEqual(options.template_name, "custom")
        
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
            entry_points=[]
        )
        
        self.assertEqual(metadata.name, "test")
        self.assertIsNone(metadata.author)
        self.assertEqual(len(metadata.languages), 1)
    
    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.engine.logger)
        self.assertEqual(self.engine.logger.name, "readme_agent")
        
        import logging
        self.assertEqual(self.engine.logger.level, logging.INFO)
    
    def test_section_info_dataclass(self):
        """Test SectionInfo dataclass."""
        section = SectionInfo(
            name="test_section",
            content_length=500,
            auto_generated=True,
            quality_score=85.5,
            content="Test content"
        )
        
        self.assertEqual(section.name, "test_section")
        self.assertEqual(section.content_length, 500)
        self.assertTrue(section.auto_generated)
        self.assertEqual(section.quality_score, 85.5)
        self.assertEqual(section.content, "Test content")
    
    def test_badge_dataclass(self):
        """Test Badge dataclass."""
        badge = Badge(
            name="build",
            url="https://img.shields.io/badge/build-passing-green",
            alt_text="Build Status",
            provider="github"
        )
        
        self.assertEqual(badge.name, "build")
        self.assertTrue(badge.url.startswith("https://"))
        self.assertEqual(badge.alt_text, "Build Status")
        self.assertEqual(badge.provider, "github")
    
    def test_improvement_suggestion_dataclass(self):
        """Test ImprovementSuggestion dataclass."""
        suggestion = ImprovementSuggestion(
            section="installation",
            priority="high",
            suggestion="Add more examples",
            implementation="Include code examples"
        )
        
        self.assertEqual(suggestion.section, "installation")
        self.assertEqual(suggestion.priority, "high")
        self.assertIn("examples", suggestion.suggestion)
        self.assertIsNotNone(suggestion.implementation)
    
    def test_documentation_result_dataclass(self):
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
            errors=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "generate")
        self.assertEqual(result.readme_content, "# Test")
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.errors), 0)


if __name__ == '__main__':
    unittest.main()