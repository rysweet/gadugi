#!/usr/bin/env python3
"""Tests for Test Writer Engine."""

import os
import sys
import tempfile
import unittest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from test_writer_engine import (
    AssertionStyle,
    ClassInfo,
    FunctionInfo,
    JavaScriptCodeAnalyzer,
    JestGenerator,
    PytestGenerator,
    PythonCodeAnalyzer,
    QualityMetrics,
    SourceFileInfo,
    TestConfiguration,
    TestFileInfo,
    TestFramework,
    TestGap,
    TestGenerationResult,
    TestLanguage,
    TestOptions,
    TestRequirements,
    TestStyle,
    TestType,
    TestWriterEngine,
    TypeScriptCodeAnalyzer,
)


class TestTestWriterEngine(unittest.TestCase):
    """Test cases for Test Writer Engine."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = TestWriterEngine()

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Sample function info
        self.sample_function = FunctionInfo(
            name="calculate_sum",
            parameters=["a", "b"],
            return_type="int",
            docstring="Calculate sum of two numbers.",
            complexity=2,
            line_number=10,
            is_async=False,
            decorators=[],
        )

        # Sample class info
        self.sample_class = ClassInfo(
            name="Calculator",
            methods=[self.sample_function],
            init_parameters=["precision"],
            base_classes=[],
            docstring="A simple calculator class.",
            line_number=5,
        )

        # Sample source file info
        self.sample_source_info = SourceFileInfo(
            filepath="src/calculator.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math", "typing"],
            complexity_score=3.5,
        )

        # Sample test requirements
        self.sample_requirements = TestRequirements(
            test_types=[TestType.UNIT],
            coverage_target=95.0,
            test_style=TestStyle.COMPREHENSIVE,
            include_edge_cases=True,
            include_error_cases=True,
        )

        # Sample configuration
        self.sample_configuration = TestConfiguration(
            testing_framework=TestFramework.PYTEST,
            assertion_style=AssertionStyle.ASSERT,
            mock_library="unittest.mock",
        )

        # Sample options
        self.sample_options = TestOptions(
            generate_fixtures=True, include_setup_teardown=True, add_docstrings=True,
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
        assert self.engine.analyzers is not None
        assert self.engine.generators is not None

    def test_templates_loading(self) -> None:
        """Test that templates are loaded correctly."""
        templates = self.engine.templates

        # Check pytest templates
        assert TestFramework.PYTEST.value in templates
        pytest_templates = templates[TestFramework.PYTEST.value]
        assert "unit_class" in pytest_templates
        assert "unit_function" in pytest_templates
        assert "integration" in pytest_templates
        assert "fixture" in pytest_templates

        # Check jest templates
        assert TestFramework.JEST.value in templates
        jest_templates = templates[TestFramework.JEST.value]
        assert "unit_class" in jest_templates
        assert "unit_function" in jest_templates

    def test_analyzers_setup(self) -> None:
        """Test analyzers are set up correctly."""
        analyzers = self.engine.analyzers

        assert TestLanguage.PYTHON.value in analyzers
        assert TestLanguage.JAVASCRIPT.value in analyzers
        assert TestLanguage.TYPESCRIPT.value in analyzers

        assert isinstance(analyzers[TestLanguage.PYTHON.value], PythonCodeAnalyzer)
        assert isinstance(analyzers[TestLanguage.JAVASCRIPT.value], JavaScriptCodeAnalyzer)
        assert isinstance(analyzers[TestLanguage.TYPESCRIPT.value], TypeScriptCodeAnalyzer)

    def test_generators_setup(self) -> None:
        """Test generators are set up correctly."""
        generators = self.engine.generators

        assert TestFramework.PYTEST.value in generators
        assert TestFramework.JEST.value in generators

        assert isinstance(generators[TestFramework.PYTEST.value], PytestGenerator)
        assert isinstance(generators[TestFramework.JEST.value], JestGenerator)

    def test_enum_values(self) -> None:
        """Test enum values are correct."""
        # TestLanguage
        assert TestLanguage.PYTHON.value == "python"
        assert TestLanguage.JAVASCRIPT.value == "javascript"
        assert TestLanguage.TYPESCRIPT.value == "typescript"

        # TestFramework
        assert TestFramework.PYTEST.value == "pytest"
        assert TestFramework.JEST.value == "jest"
        assert TestFramework.UNITTEST.value == "unittest"

        # TestType
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.E2E.value == "e2e"

        # TestStyle
        assert TestStyle.COMPREHENSIVE.value == "comprehensive"
        assert TestStyle.MINIMAL.value == "minimal"

        # AssertionStyle
        assert AssertionStyle.ASSERT.value == "assert"
        assert AssertionStyle.EXPECT.value == "expect"

    def test_function_info_dataclass(self) -> None:
        """Test FunctionInfo dataclass functionality."""
        func = FunctionInfo(
            name="test_func",
            parameters=["param1", "param2"],
            return_type="str",
            docstring="Test function",
            complexity=3,
            line_number=20,
            is_async=True,
            decorators=["property", "staticmethod"],
        )

        assert func.name == "test_func"
        assert len(func.parameters) == 2
        assert func.return_type == "str"
        assert func.is_async
        assert "property" in func.decorators
        assert func.complexity == 3

    def test_class_info_dataclass(self) -> None:
        """Test ClassInfo dataclass functionality."""
        method = FunctionInfo(
            name="method1",
            parameters=[],
            return_type=None,
            docstring=None,
            complexity=1,
            line_number=10,
        )

        cls = ClassInfo(
            name="TestClass",
            methods=[method],
            init_parameters=["param1"],
            base_classes=["BaseClass"],
            docstring="Test class",
            line_number=5,
        )

        assert cls.name == "TestClass"
        assert len(cls.methods) == 1
        assert cls.methods[0].name == "method1"
        assert "param1" in cls.init_parameters
        assert "BaseClass" in cls.base_classes

    def test_source_file_info_dataclass(self) -> None:
        """Test SourceFileInfo dataclass functionality."""
        info = SourceFileInfo(
            filepath="/test/file.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["os", "sys"],
            complexity_score=5.0,
        )

        assert info.filepath == "/test/file.py"
        assert info.language == TestLanguage.PYTHON
        assert len(info.functions) == 1
        assert len(info.classes) == 1
        assert "os" in info.imports
        assert info.complexity_score == 5.0

    def test_test_requirements_dataclass(self) -> None:
        """Test TestRequirements dataclass functionality."""
        requirements = TestRequirements(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            coverage_target=90.0,
            test_style=TestStyle.FOCUSED,
            include_edge_cases=False,
            include_error_cases=True,
            include_performance_tests=True,
        )

        assert len(requirements.test_types) == 2
        assert TestType.UNIT in requirements.test_types
        assert requirements.coverage_target == 90.0
        assert requirements.test_style == TestStyle.FOCUSED
        assert not requirements.include_edge_cases
        assert requirements.include_performance_tests

    def test_test_configuration_dataclass(self) -> None:
        """Test TestConfiguration dataclass functionality."""
        config = TestConfiguration(
            testing_framework=TestFramework.JEST,
            assertion_style=AssertionStyle.EXPECT,
            mock_library="sinon",
            test_runner="jest",
            output_format="feature_based",
        )

        assert config.testing_framework == TestFramework.JEST
        assert config.assertion_style == AssertionStyle.EXPECT
        assert config.mock_library == "sinon"
        assert config.output_format == "feature_based"

    def test_test_options_dataclass(self) -> None:
        """Test TestOptions dataclass functionality."""
        options = TestOptions(
            generate_fixtures=False,
            include_setup_teardown=False,
            add_docstrings=True,
            use_parametrized_tests=True,
            create_test_data=False,
            validate_generated_tests=False,
        )

        assert not options.generate_fixtures
        assert not options.include_setup_teardown
        assert options.add_docstrings
        assert options.use_parametrized_tests
        assert not options.create_test_data

    def test_generate_test_infrastructure_python(self) -> None:
        """Test Python test infrastructure generation."""
        test_dir = os.path.join(self.temp_dir, "tests")

        infrastructure = self.engine._generate_test_infrastructure(
            test_dir,
            TestLanguage.PYTHON,
            self.sample_configuration,
            self.sample_options,
        )

        # Check directory was created
        assert os.path.exists(test_dir)

        # Check infrastructure files
        assert "fixtures_created" in infrastructure
        assert "configuration_files" in infrastructure

        # Check specific files
        assert "conftest.py" in infrastructure["configuration_files"]
        assert "pytest.ini" in infrastructure["configuration_files"]
        assert "fixtures.py" in infrastructure["fixtures_created"]

        # Verify files exist
        assert os.path.exists(os.path.join(test_dir, "conftest.py"))
        assert os.path.exists(os.path.join(test_dir, "fixtures.py"))

    def test_generate_test_infrastructure_javascript(self) -> None:
        """Test JavaScript test infrastructure generation."""
        test_dir = os.path.join(self.temp_dir, "tests")

        config = TestConfiguration(testing_framework=TestFramework.JEST)
        infrastructure = self.engine._generate_test_infrastructure(
            test_dir, TestLanguage.JAVASCRIPT, config, self.sample_options,
        )

        # Check infrastructure files
        assert "fixtures_created" in infrastructure
        assert "configuration_files" in infrastructure

        # Check specific files for Jest
        assert "jest.config.js" in infrastructure["configuration_files"]
        assert "setup.js" in infrastructure["fixtures_created"]

    def test_analyze_test_coverage(self) -> None:
        """Test test coverage analysis."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=6,
                coverage_estimate=90.0,
                test_types=[TestType.UNIT],
                file_size="2KB",
                source_file="calc.py",
            ),
        ]

        analysis = self.engine._analyze_test_coverage(
            [self.sample_source_info], test_files,
        )

        assert "functions_tested" in analysis
        assert "functions_untested" in analysis
        assert "edge_cases_covered" in analysis
        assert "error_scenarios" in analysis
        assert "test_gaps" in analysis

        assert isinstance(analysis["test_gaps"], list)
        assert analysis["functions_tested"] >= 0

    def test_calculate_quality_metrics(self) -> None:
        """Test quality metrics calculation."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=12,
                coverage_estimate=95.0,
                test_types=[TestType.UNIT],
                file_size="3KB",
                source_file="calc.py",
            ),
        ]

        metrics = self.engine._calculate_quality_metrics(
            test_files, [self.sample_source_info],
        )

        assert isinstance(metrics, QualityMetrics)
        assert metrics.test_maintainability > 0
        assert metrics.test_readability > 0
        assert metrics.assertion_quality > 0
        assert metrics.test_organization > 0

        # All metrics should be between 0 and 100
        assert metrics.test_maintainability <= 100
        assert metrics.test_readability <= 100
        assert metrics.assertion_quality <= 100
        assert metrics.test_organization <= 100

    def test_generate_recommendations(self) -> None:
        """Test recommendation generation."""
        analysis = {
            "functions_tested": 5,
            "functions_untested": 2,
            "edge_cases_covered": 10,
            "error_scenarios": 3,
            "test_gaps": [
                TestGap("complex_func", ["edge_case"], "high", "Complex function"),
            ],
        }

        quality = QualityMetrics(
            test_maintainability=70.0,
            test_readability=85.0,
            assertion_quality=90.0,
            test_organization=95.0,
        )

        recommendations = self.engine._generate_recommendations(analysis, quality)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should recommend testing untested functions
        coverage_recs = [r for r in recommendations if r["category"] == "coverage"]
        assert len(coverage_recs) > 0

        # Should recommend addressing test gaps
        quality_recs = [r for r in recommendations if r["category"] == "quality"]
        assert len(quality_recs) > 0

        # Should recommend maintainability improvements (quality score < 80)
        maintainability_recs = [
            r for r in recommendations if r["category"] == "maintainability"
        ]
        assert len(maintainability_recs) > 0

    def test_estimate_coverage(self) -> None:
        """Test coverage estimation."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=8,
                coverage_estimate=85.0,
                test_types=[TestType.UNIT],
                file_size="2KB",
                source_file="calc.py",
            ),
        ]

        coverage = self.engine._estimate_coverage([self.sample_source_info], test_files)

        assert isinstance(coverage, float)
        assert coverage >= 0.0
        assert coverage <= 95.0  # Max estimate is 95%

    def test_create_error_result(self) -> None:
        """Test error result creation."""
        error_msg = "Test error message"
        result = self.engine._create_error_result(error_msg, "generate")

        assert isinstance(result, TestGenerationResult)
        assert not result.success
        assert result.operation == "generate"
        assert error_msg in result.errors
        assert len(result.warnings) == 0

    def test_process_request_generate(self) -> None:
        """Test processing generate request."""
        # Create a simple Python file for testing
        source_file = os.path.join(self.temp_dir, "calculator.py")
        with open(source_file, "w") as f:
            f.write("""
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

class Calculator:
    def __init__(self):
        pass

    def multiply(self, x, y):
        return x * y
""")

        request = {
            "operation": "generate",
            "target": {
                "source_files": [source_file],
                "test_directory": os.path.join(self.temp_dir, "tests"),
                "language": "python",
                "framework": "pytest",
            },
            "test_requirements": {
                "test_types": ["unit"],
                "coverage_target": 90.0,
                "test_style": "comprehensive",
                "include_edge_cases": True,
            },
            "configuration": {
                "testing_framework": "pytest",
                "assertion_style": "assert",
            },
            "options": {"generate_fixtures": True, "add_docstrings": True},
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert response["operation"] == "generate"
        assert "test_suite" in response
        assert "test_analysis" in response
        assert "recommendations" in response
        assert "test_infrastructure" in response
        assert "quality_metrics" in response

    def test_process_request_unsupported_operation(self) -> None:
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation"}

        response = self.engine.process_request(request)

        assert not response["success"]
        assert "Unsupported operation" in response["error"]

    def test_process_request_unimplemented_operations(self) -> None:
        """Test unimplemented operations return appropriate errors."""
        operations = ["analyze", "enhance", "refactor", "validate"]

        for operation in operations:
            request = {"operation": operation}
            response = self.engine.process_request(request)

            assert not response["success"]
            assert "not yet implemented" in response["error"]

    def test_template_methods(self) -> None:
        """Test template methods return valid templates."""
        # Test pytest templates
        unit_class = self.engine._get_pytest_unit_class_template()
        assert "class Test{CLASS_NAME}:" in unit_class
        assert "def setup_method(self):" in unit_class

        unit_function = self.engine._get_pytest_unit_function_template()
        assert "def test_{FUNCTION_NAME}_success():" in unit_function
        assert "@pytest.mark.parametrize" in unit_function

        integration = self.engine._get_pytest_integration_template()
        assert "Integration tests" in integration
        assert "@requests_mock.Mocker()" in integration

        fixture = self.engine._get_pytest_fixture_template()
        assert "@pytest.fixture" in fixture

        # Test Jest templates
        jest_class = self.engine._get_jest_unit_class_template()
        assert "describe('{CLASS_NAME}'" in jest_class
        assert "beforeEach(() => {" in jest_class

        jest_function = self.engine._get_jest_unit_function_template()
        assert "it('should handle valid input correctly'" in jest_function
        assert "test.each([" in jest_function

    def test_infrastructure_templates(self) -> None:
        """Test infrastructure template methods."""
        # Test conftest template
        conftest = self.engine._get_conftest_template()
        assert "@pytest.fixture" in conftest
        assert "def pytest_configure" in conftest

        # Test pytest.ini template
        pytest_ini = self.engine._get_pytest_ini_template()
        assert "[tool:pytest]" in pytest_ini
        assert "testpaths = tests" in pytest_ini

        # Test common fixtures template
        fixtures = self.engine._get_common_fixtures_template()
        assert "def mock_database" in fixtures
        assert "def sample_user" in fixtures

        # Test Jest config template
        jest_config = self.engine._get_jest_config_template()
        assert "module.exports" in jest_config
        assert "testEnvironment:" in jest_config

        # Test Jest setup template
        jest_setup = self.engine._get_jest_setup_template()
        assert "process.env.NODE_ENV" in jest_setup
        assert "global.createMockUser" in jest_setup

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.engine.logger is not None
        assert self.engine.logger.name == "test_writer"

        import logging

        assert self.engine.logger.level == logging.INFO


class TestPythonCodeAnalyzer(unittest.TestCase):
    """Test cases for Python Code Analyzer."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.analyzer = PythonCodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_analyze_simple_function(self) -> None:
        """Test analyzing a simple function."""
        code = '''
def add(a, b):
    """Add two numbers."""
    return a + b
'''

        source_file = os.path.join(self.temp_dir, "simple.py")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert result.language == TestLanguage.PYTHON
        assert len(result.functions) == 1
        assert result.functions[0].name == "add"
        assert len(result.functions[0].parameters) == 2
        assert "a" in result.functions[0].parameters
        assert result.functions[0].docstring == "Add two numbers."

    def test_analyze_class_with_methods(self) -> None:
        """Test analyzing a class with methods."""
        code = '''
class Calculator:
    """A simple calculator."""

    def __init__(self, precision=2):
        self.precision = precision

    def add(self, a, b):
        """Add two numbers."""
        return round(a + b, self.precision)

    def _private_method(self):
        pass
'''

        source_file = os.path.join(self.temp_dir, "calculator.py")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert len(result.classes) == 1

        calc_class = result.classes[0]
        assert calc_class.name == "Calculator"
        assert calc_class.docstring == "A simple calculator."
        assert len(calc_class.methods) == 3  # __init__, add, _private_method
        assert "precision" in calc_class.init_parameters

        # Check method analysis
        add_method = next(m for m in calc_class.methods if m.name == "add")
        assert add_method.docstring == "Add two numbers."
        assert "a" in add_method.parameters
        assert "b" in add_method.parameters

    def test_analyze_function_with_decorators(self) -> None:
        """Test analyzing function with decorators."""
        code = """
@property
@staticmethod
def get_value():
    return 42
"""

        source_file = os.path.join(self.temp_dir, "decorated.py")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "get_value"
        assert "property" in func.decorators
        assert "staticmethod" in func.decorators

    def test_analyze_async_function(self) -> None:
        """Test analyzing async function."""
        code = '''
async def fetch_data():
    """Fetch data asynchronously."""
    return "data"
'''

        source_file = os.path.join(self.temp_dir, "async.py")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "fetch_data"
        assert func.is_async

    def test_analyze_imports(self) -> None:
        """Test analyzing import statements."""
        code = """
import os
import sys
from typing import Dict, List
from .local_module import LocalClass
"""

        source_file = os.path.join(self.temp_dir, "imports.py")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert "os" in result.imports
        assert "sys" in result.imports
        assert "typing.Dict" in result.imports
        assert "typing.List" in result.imports
        assert ".local_module.LocalClass" in result.imports

    def test_calculate_function_complexity(self) -> None:
        """Test function complexity calculation."""
        # Simple function (complexity = 1)
        simple_code = """
def simple():
    return True
"""
        tree = ast.parse(simple_code)
        simple_func = tree.body[0]
        simple_complexity = self.analyzer._calculate_function_complexity(simple_func)
        assert simple_complexity == 1

        # Complex function with branches
        complex_code = """
def complex(x, y):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x == 0:
        return y
    else:
        try:
            return x / y
        except ZeroDivisionError:
            return 0

    for i in range(10):
        if i % 2 == 0:
            continue
"""
        tree = ast.parse(complex_code)
        complex_func = tree.body[0]
        complex_complexity = self.analyzer._calculate_function_complexity(complex_func)
        assert complex_complexity > simple_complexity

    def test_syntax_error_handling(self) -> None:
        """Test handling of syntax errors in source code."""
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
    return "invalid"
"""

        source_file = os.path.join(self.temp_dir, "invalid.py")
        with open(source_file, "w") as f:
            f.write(invalid_code)

        result = self.analyzer.analyze_file(source_file)

        # Should return empty result for invalid syntax
        assert len(result.functions) == 0
        assert len(result.classes) == 0
        assert result.complexity_score == 0.0


class TestJavaScriptCodeAnalyzer(unittest.TestCase):
    """Test cases for JavaScript Code Analyzer."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.analyzer = JavaScriptCodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_analyze_functions(self) -> None:
        """Test analyzing JavaScript functions."""
        code = """
function add(a, b) {
    return a + b;
}

const multiply = (x, y) => x * y;

function complexFunction(param1, param2, param3) {
    if (param1 > 0) {
        return param2 + param3;
    }
    return param1;
}
"""

        source_file = os.path.join(self.temp_dir, "functions.js")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert result.language == TestLanguage.JAVASCRIPT
        assert len(result.functions) == 3

        # Check function names
        function_names = [f.name for f in result.functions]
        assert "add" in function_names
        assert "multiply" in function_names
        assert "complexFunction" in function_names

        # Check parameters
        add_func = next(f for f in result.functions if f.name == "add")
        assert len(add_func.parameters) == 2
        assert "a" in add_func.parameters
        assert "b" in add_func.parameters

    def test_analyze_classes(self) -> None:
        """Test analyzing JavaScript classes."""
        code = """
class Calculator {
    constructor(precision) {
        this.precision = precision;
    }

    add(a, b) {
        return a + b;
    }
}

class AdvancedCalculator extends Calculator {
    multiply(x, y) {
        return x * y;
    }
}
"""

        source_file = os.path.join(self.temp_dir, "classes.js")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert len(result.classes) == 2

        # Check class names
        class_names = [c.name for c in result.classes]
        assert "Calculator" in class_names
        assert "AdvancedCalculator" in class_names

        # Check inheritance
        advanced_calc = next(
            c for c in result.classes if c.name == "AdvancedCalculator"
        )
        assert "Calculator" in advanced_calc.base_classes

    def test_analyze_imports(self) -> None:
        """Test analyzing JavaScript imports."""
        code = """
import { add, subtract } from './math';
import Calculator from './Calculator';
const { multiply } = require('./operations');
import React from 'react';
"""

        source_file = os.path.join(self.temp_dir, "imports.js")
        with open(source_file, "w") as f:
            f.write(code)

        result = self.analyzer.analyze_file(source_file)

        assert "./math" in result.imports
        assert "./Calculator" in result.imports
        assert "./operations" in result.imports
        assert "react" in result.imports


class TestPytestGenerator(unittest.TestCase):
    """Test cases for Pytest Generator."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = PytestGenerator()
        self.temp_dir = tempfile.mkdtemp()

        # Create sample source info
        self.sample_function = FunctionInfo(
            name="calculate",
            parameters=["x", "y"],
            return_type="int",
            docstring="Calculate something.",
            complexity=2,
            line_number=10,
        )

        self.sample_class = ClassInfo(
            name="Calculator",
            methods=[self.sample_function],
            init_parameters=["precision"],
            base_classes=[],
            docstring="Calculator class.",
            line_number=5,
        )

        self.sample_source_info = SourceFileInfo(
            filepath="calculator.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math"],
            complexity_score=3.0,
        )

        self.sample_requirements = TestRequirements([TestType.UNIT])
        self.sample_configuration = TestConfiguration()
        self.sample_options = TestOptions()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_generate_test_file(self) -> None:
        """Test generating a pytest test file."""
        test_dir = os.path.join(self.temp_dir, "tests")

        result = self.generator.generate_test_file(
            self.sample_source_info,
            test_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options,
        )

        assert result is not None
        assert isinstance(result, TestFileInfo)
        assert result.path.endswith("test_calculator.py")
        assert result.test_count > 0
        assert result.coverage_estimate > 0

        # Check that file was actually created
        assert os.path.exists(result.path)

        # Check file contents
        with open(result.path) as f:
            content = f.read()

        assert "import pytest" in content
        assert "from unittest.mock import Mock, patch" in content
        assert "class TestCalculator:" in content
        assert "def test_calculate_success(self):" in content

    def test_generate_pytest_content(self) -> None:
        """Test generating pytest content."""
        content = self.generator._generate_pytest_content(
            self.sample_source_info,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options,
        )

        # Check imports
        assert "import pytest" in content
        assert "from calculator import Calculator, calculate" in content

        # Check class test structure
        assert "class TestCalculator:" in content
        assert "def setup_method(self):" in content
        assert "def teardown_method(self):" in content

        # Check function tests
        assert "def test_calculate_success():" in content
        assert "def test_calculate_edge_cases():" in content
        assert "def test_calculate_error_handling():" in content

    def test_generate_class_tests(self) -> None:
        """Test generating tests for a class."""
        tests = self.generator._generate_class_tests(
            self.sample_class, self.sample_options,
        )

        assert isinstance(tests, list)
        assert len(tests) > 0

        test_content = "\n".join(tests)
        assert "class TestCalculator:" in test_content
        assert "def setup_method(self):" in test_content
        assert "self.instance = Calculator" in test_content
        assert "def test_calculate_success(self):" in test_content

    def test_generate_function_tests(self) -> None:
        """Test generating tests for a function."""
        tests = self.generator._generate_function_tests(
            self.sample_function, self.sample_options,
        )

        assert isinstance(tests, list)
        assert len(tests) > 0

        test_content = "\n".join(tests)
        assert "def test_calculate_success():" in test_content
        assert "def test_calculate_edge_cases():" in test_content
        assert "def test_calculate_error_handling():" in test_content
        assert "with pytest.raises(Exception):" in test_content

    def test_empty_source_file(self) -> None:
        """Test handling empty source file."""
        empty_source_info = SourceFileInfo(
            filepath="empty.py",
            language=TestLanguage.PYTHON,
            functions=[],
            classes=[],
            imports=[],
            complexity_score=0.0,
        )

        result = self.generator.generate_test_file(
            empty_source_info,
            self.temp_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options,
        )

        assert result is None


class TestJestGenerator(unittest.TestCase):
    """Test cases for Jest Generator."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.generator = JestGenerator()
        self.temp_dir = tempfile.mkdtemp()

        # Create sample source info
        self.sample_function = FunctionInfo(
            name="calculate",
            parameters=["x", "y"],
            return_type="number",
            docstring="Calculate something.",
            complexity=2,
            line_number=10,
        )

        self.sample_class = ClassInfo(
            name="Calculator",
            methods=[self.sample_function],
            init_parameters=[],
            base_classes=[],
            docstring="Calculator class.",
            line_number=5,
        )

        self.sample_source_info = SourceFileInfo(
            filepath="calculator.js",
            language=TestLanguage.JAVASCRIPT,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math"],
            complexity_score=3.0,
        )

        self.sample_requirements = TestRequirements([TestType.UNIT])
        self.sample_configuration = TestConfiguration(
            testing_framework=TestFramework.JEST,
        )
        self.sample_options = TestOptions()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_generate_test_file(self) -> None:
        """Test generating a Jest test file."""
        test_dir = os.path.join(self.temp_dir, "tests")

        result = self.generator.generate_test_file(
            self.sample_source_info,
            test_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options,
        )

        assert result is not None
        assert isinstance(result, TestFileInfo)
        assert result.path.endswith("calculator.test.js")
        assert result.test_count > 0

        # Check that file was actually created
        assert os.path.exists(result.path)

        # Check file contents
        with open(result.path) as f:
            content = f.read()

        assert "import { Calculator, calculate }" in content
        assert "describe('Calculator'" in content
        assert "describe('calculate'" in content

    def test_generate_jest_content(self) -> None:
        """Test generating Jest content."""
        content = self.generator._generate_jest_content(
            self.sample_source_info,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options,
        )

        # Check imports
        assert "import { Calculator, calculate }" in content

        # Check test structure
        assert "describe('Calculator'" in content
        assert "beforeEach(() => {" in content
        assert "afterEach(() => {" in content
        assert "jest.clearAllMocks()" in content

    def test_generate_jest_class_tests(self) -> None:
        """Test generating Jest tests for a class."""
        tests = self.generator._generate_jest_class_tests(
            self.sample_class, self.sample_options,
        )

        assert isinstance(tests, list)
        assert len(tests) > 0

        test_content = "\n".join(tests)
        assert "describe('Calculator'" in test_content
        assert "beforeEach(() => {" in test_content
        assert "calculator = new Calculator()" in test_content
        assert "describe('calculate'" in test_content

    def test_generate_jest_function_tests(self) -> None:
        """Test generating Jest tests for a function."""
        tests = self.generator._generate_jest_function_tests(
            self.sample_function, self.sample_options,
        )

        assert isinstance(tests, list)
        assert len(tests) > 0

        test_content = "\n".join(tests)
        assert "describe('calculate'" in test_content
        assert "it('should work with valid input'" in test_content
        assert "it('should handle invalid input'" in test_content
        assert "expect(() => {" in test_content
        assert "}).toThrow()" in test_content


if __name__ == "__main__":
    unittest.main()
