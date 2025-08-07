#!/usr/bin/env python3
"""
Tests for Test Writer Engine
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

from test_writer_engine import (
    TestWriterEngine,
    TestLanguage,
    TestFramework,
    TestType,
    TestStyle,
    AssertionStyle,
    TestRequirements,
    TestConfiguration,
    TestOptions,
    FunctionInfo,
    ClassInfo,
    SourceFileInfo,
    TestFileInfo,
    TestGap,
    QualityMetrics,
    TestGenerationResult,
    PythonCodeAnalyzer,
    JavaScriptCodeAnalyzer,
    TypeScriptCodeAnalyzer,
    PytestGenerator,
    JestGenerator
)


class TestTestWriterEngine(unittest.TestCase):
    """Test cases for Test Writer Engine."""
    
    def setUp(self):
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
            decorators=[]
        )
        
        # Sample class info
        self.sample_class = ClassInfo(
            name="Calculator",
            methods=[self.sample_function],
            init_parameters=["precision"],
            base_classes=[],
            docstring="A simple calculator class.",
            line_number=5
        )
        
        # Sample source file info
        self.sample_source_info = SourceFileInfo(
            filepath="src/calculator.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math", "typing"],
            complexity_score=3.5
        )
        
        # Sample test requirements
        self.sample_requirements = TestRequirements(
            test_types=[TestType.UNIT],
            coverage_target=95.0,
            test_style=TestStyle.COMPREHENSIVE,
            include_edge_cases=True,
            include_error_cases=True
        )
        
        # Sample configuration
        self.sample_configuration = TestConfiguration(
            testing_framework=TestFramework.PYTEST,
            assertion_style=AssertionStyle.ASSERT,
            mock_library="unittest.mock"
        )
        
        # Sample options
        self.sample_options = TestOptions(
            generate_fixtures=True,
            include_setup_teardown=True,
            add_docstrings=True
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
        self.assertIsNotNone(self.engine.analyzers)
        self.assertIsNotNone(self.engine.generators)
    
    def test_templates_loading(self):
        """Test that templates are loaded correctly."""
        templates = self.engine.templates
        
        # Check pytest templates
        self.assertIn(TestFramework.PYTEST.value, templates)
        pytest_templates = templates[TestFramework.PYTEST.value]
        self.assertIn("unit_class", pytest_templates)
        self.assertIn("unit_function", pytest_templates)
        self.assertIn("integration", pytest_templates)
        self.assertIn("fixture", pytest_templates)
        
        # Check jest templates
        self.assertIn(TestFramework.JEST.value, templates)
        jest_templates = templates[TestFramework.JEST.value]
        self.assertIn("unit_class", jest_templates)
        self.assertIn("unit_function", jest_templates)
    
    def test_analyzers_setup(self):
        """Test analyzers are set up correctly."""
        analyzers = self.engine.analyzers
        
        self.assertIn(TestLanguage.PYTHON.value, analyzers)
        self.assertIn(TestLanguage.JAVASCRIPT.value, analyzers)
        self.assertIn(TestLanguage.TYPESCRIPT.value, analyzers)
        
        self.assertIsInstance(analyzers[TestLanguage.PYTHON.value], PythonCodeAnalyzer)
        self.assertIsInstance(analyzers[TestLanguage.JAVASCRIPT.value], JavaScriptCodeAnalyzer)
        self.assertIsInstance(analyzers[TestLanguage.TYPESCRIPT.value], TypeScriptCodeAnalyzer)
    
    def test_generators_setup(self):
        """Test generators are set up correctly."""
        generators = self.engine.generators
        
        self.assertIn(TestFramework.PYTEST.value, generators)
        self.assertIn(TestFramework.JEST.value, generators)
        
        self.assertIsInstance(generators[TestFramework.PYTEST.value], PytestGenerator)
        self.assertIsInstance(generators[TestFramework.JEST.value], JestGenerator)
    
    def test_enum_values(self):
        """Test enum values are correct."""
        # TestLanguage
        self.assertEqual(TestLanguage.PYTHON.value, "python")
        self.assertEqual(TestLanguage.JAVASCRIPT.value, "javascript")
        self.assertEqual(TestLanguage.TYPESCRIPT.value, "typescript")
        
        # TestFramework
        self.assertEqual(TestFramework.PYTEST.value, "pytest")
        self.assertEqual(TestFramework.JEST.value, "jest")
        self.assertEqual(TestFramework.UNITTEST.value, "unittest")
        
        # TestType
        self.assertEqual(TestType.UNIT.value, "unit")
        self.assertEqual(TestType.INTEGRATION.value, "integration")
        self.assertEqual(TestType.E2E.value, "e2e")
        
        # TestStyle
        self.assertEqual(TestStyle.COMPREHENSIVE.value, "comprehensive")
        self.assertEqual(TestStyle.MINIMAL.value, "minimal")
        
        # AssertionStyle
        self.assertEqual(AssertionStyle.ASSERT.value, "assert")
        self.assertEqual(AssertionStyle.EXPECT.value, "expect")
    
    def test_function_info_dataclass(self):
        """Test FunctionInfo dataclass functionality."""
        func = FunctionInfo(
            name="test_func",
            parameters=["param1", "param2"],
            return_type="str",
            docstring="Test function",
            complexity=3,
            line_number=20,
            is_async=True,
            decorators=["property", "staticmethod"]
        )
        
        self.assertEqual(func.name, "test_func")
        self.assertEqual(len(func.parameters), 2)
        self.assertEqual(func.return_type, "str")
        self.assertTrue(func.is_async)
        self.assertIn("property", func.decorators)
        self.assertEqual(func.complexity, 3)
    
    def test_class_info_dataclass(self):
        """Test ClassInfo dataclass functionality."""
        method = FunctionInfo(
            name="method1", parameters=[], return_type=None,
            docstring=None, complexity=1, line_number=10
        )
        
        cls = ClassInfo(
            name="TestClass",
            methods=[method],
            init_parameters=["param1"],
            base_classes=["BaseClass"],
            docstring="Test class",
            line_number=5
        )
        
        self.assertEqual(cls.name, "TestClass")
        self.assertEqual(len(cls.methods), 1)
        self.assertEqual(cls.methods[0].name, "method1")
        self.assertIn("param1", cls.init_parameters)
        self.assertIn("BaseClass", cls.base_classes)
    
    def test_source_file_info_dataclass(self):
        """Test SourceFileInfo dataclass functionality."""
        info = SourceFileInfo(
            filepath="/test/file.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["os", "sys"],
            complexity_score=5.0
        )
        
        self.assertEqual(info.filepath, "/test/file.py")
        self.assertEqual(info.language, TestLanguage.PYTHON)
        self.assertEqual(len(info.functions), 1)
        self.assertEqual(len(info.classes), 1)
        self.assertIn("os", info.imports)
        self.assertEqual(info.complexity_score, 5.0)
    
    def test_test_requirements_dataclass(self):
        """Test TestRequirements dataclass functionality."""
        requirements = TestRequirements(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            coverage_target=90.0,
            test_style=TestStyle.FOCUSED,
            include_edge_cases=False,
            include_error_cases=True,
            include_performance_tests=True
        )
        
        self.assertEqual(len(requirements.test_types), 2)
        self.assertIn(TestType.UNIT, requirements.test_types)
        self.assertEqual(requirements.coverage_target, 90.0)
        self.assertEqual(requirements.test_style, TestStyle.FOCUSED)
        self.assertFalse(requirements.include_edge_cases)
        self.assertTrue(requirements.include_performance_tests)
    
    def test_test_configuration_dataclass(self):
        """Test TestConfiguration dataclass functionality."""
        config = TestConfiguration(
            testing_framework=TestFramework.JEST,
            assertion_style=AssertionStyle.EXPECT,
            mock_library="sinon",
            test_runner="jest",
            output_format="feature_based"
        )
        
        self.assertEqual(config.testing_framework, TestFramework.JEST)
        self.assertEqual(config.assertion_style, AssertionStyle.EXPECT)
        self.assertEqual(config.mock_library, "sinon")
        self.assertEqual(config.output_format, "feature_based")
    
    def test_test_options_dataclass(self):
        """Test TestOptions dataclass functionality."""
        options = TestOptions(
            generate_fixtures=False,
            include_setup_teardown=False,
            add_docstrings=True,
            use_parametrized_tests=True,
            create_test_data=False,
            validate_generated_tests=False
        )
        
        self.assertFalse(options.generate_fixtures)
        self.assertFalse(options.include_setup_teardown)
        self.assertTrue(options.add_docstrings)
        self.assertTrue(options.use_parametrized_tests)
        self.assertFalse(options.create_test_data)
    
    def test_generate_test_infrastructure_python(self):
        """Test Python test infrastructure generation."""
        test_dir = os.path.join(self.temp_dir, "tests")
        
        infrastructure = self.engine._generate_test_infrastructure(
            test_dir,
            TestLanguage.PYTHON,
            self.sample_configuration,
            self.sample_options
        )
        
        # Check directory was created
        self.assertTrue(os.path.exists(test_dir))
        
        # Check infrastructure files
        self.assertIn("fixtures_created", infrastructure)
        self.assertIn("configuration_files", infrastructure)
        
        # Check specific files
        self.assertIn("conftest.py", infrastructure["configuration_files"])
        self.assertIn("pytest.ini", infrastructure["configuration_files"])
        self.assertIn("fixtures.py", infrastructure["fixtures_created"])
        
        # Verify files exist
        self.assertTrue(os.path.exists(os.path.join(test_dir, "conftest.py")))
        self.assertTrue(os.path.exists(os.path.join(test_dir, "fixtures.py")))
    
    def test_generate_test_infrastructure_javascript(self):
        """Test JavaScript test infrastructure generation."""
        test_dir = os.path.join(self.temp_dir, "tests")
        
        config = TestConfiguration(testing_framework=TestFramework.JEST)
        infrastructure = self.engine._generate_test_infrastructure(
            test_dir,
            TestLanguage.JAVASCRIPT,
            config,
            self.sample_options
        )
        
        # Check infrastructure files
        self.assertIn("fixtures_created", infrastructure)
        self.assertIn("configuration_files", infrastructure)
        
        # Check specific files for Jest
        self.assertIn("jest.config.js", infrastructure["configuration_files"])
        self.assertIn("setup.js", infrastructure["fixtures_created"])
    
    def test_analyze_test_coverage(self):
        """Test test coverage analysis."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=6,
                coverage_estimate=90.0,
                test_types=[TestType.UNIT],
                file_size="2KB",
                source_file="calc.py"
            )
        ]
        
        analysis = self.engine._analyze_test_coverage([self.sample_source_info], test_files)
        
        self.assertIn("functions_tested", analysis)
        self.assertIn("functions_untested", analysis)
        self.assertIn("edge_cases_covered", analysis)
        self.assertIn("error_scenarios", analysis)
        self.assertIn("test_gaps", analysis)
        
        self.assertIsInstance(analysis["test_gaps"], list)
        self.assertGreaterEqual(analysis["functions_tested"], 0)
    
    def test_calculate_quality_metrics(self):
        """Test quality metrics calculation."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=12,
                coverage_estimate=95.0,
                test_types=[TestType.UNIT],
                file_size="3KB",
                source_file="calc.py"
            )
        ]
        
        metrics = self.engine._calculate_quality_metrics(test_files, [self.sample_source_info])
        
        self.assertIsInstance(metrics, QualityMetrics)
        self.assertGreater(metrics.test_maintainability, 0)
        self.assertGreater(metrics.test_readability, 0)
        self.assertGreater(metrics.assertion_quality, 0)
        self.assertGreater(metrics.test_organization, 0)
        
        # All metrics should be between 0 and 100
        self.assertLessEqual(metrics.test_maintainability, 100)
        self.assertLessEqual(metrics.test_readability, 100)
        self.assertLessEqual(metrics.assertion_quality, 100)
        self.assertLessEqual(metrics.test_organization, 100)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        analysis = {
            "functions_tested": 5,
            "functions_untested": 2,
            "edge_cases_covered": 10,
            "error_scenarios": 3,
            "test_gaps": [
                TestGap("complex_func", ["edge_case"], "high", "Complex function")
            ]
        }
        
        quality = QualityMetrics(
            test_maintainability=70.0,
            test_readability=85.0,
            assertion_quality=90.0,
            test_organization=95.0
        )
        
        recommendations = self.engine._generate_recommendations(analysis, quality)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend testing untested functions
        coverage_recs = [r for r in recommendations if r["category"] == "coverage"]
        self.assertGreater(len(coverage_recs), 0)
        
        # Should recommend addressing test gaps
        quality_recs = [r for r in recommendations if r["category"] == "quality"]
        self.assertGreater(len(quality_recs), 0)
        
        # Should recommend maintainability improvements (quality score < 80)
        maintainability_recs = [r for r in recommendations if r["category"] == "maintainability"]
        self.assertGreater(len(maintainability_recs), 0)
    
    def test_estimate_coverage(self):
        """Test coverage estimation."""
        test_files = [
            TestFileInfo(
                path="test_calc.py",
                test_count=8,
                coverage_estimate=85.0,
                test_types=[TestType.UNIT],
                file_size="2KB",
                source_file="calc.py"
            )
        ]
        
        coverage = self.engine._estimate_coverage([self.sample_source_info], test_files)
        
        self.assertIsInstance(coverage, float)
        self.assertGreaterEqual(coverage, 0.0)
        self.assertLessEqual(coverage, 95.0)  # Max estimate is 95%
    
    def test_create_error_result(self):
        """Test error result creation."""
        error_msg = "Test error message"
        result = self.engine._create_error_result(error_msg, "generate")
        
        self.assertIsInstance(result, TestGenerationResult)
        self.assertFalse(result.success)
        self.assertEqual(result.operation, "generate")
        self.assertIn(error_msg, result.errors)
        self.assertEqual(len(result.warnings), 0)
    
    def test_process_request_generate(self):
        """Test processing generate request."""
        # Create a simple Python file for testing
        source_file = os.path.join(self.temp_dir, "calculator.py")
        with open(source_file, 'w') as f:
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
                "framework": "pytest"
            },
            "test_requirements": {
                "test_types": ["unit"],
                "coverage_target": 90.0,
                "test_style": "comprehensive",
                "include_edge_cases": True
            },
            "configuration": {
                "testing_framework": "pytest",
                "assertion_style": "assert"
            },
            "options": {
                "generate_fixtures": True,
                "add_docstrings": True
            }
        }
        
        response = self.engine.process_request(request)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["operation"], "generate")
        self.assertIn("test_suite", response)
        self.assertIn("test_analysis", response)
        self.assertIn("recommendations", response)
        self.assertIn("test_infrastructure", response)
        self.assertIn("quality_metrics", response)
    
    def test_process_request_unsupported_operation(self):
        """Test processing unsupported operation."""
        request = {
            "operation": "unsupported_operation"
        }
        
        response = self.engine.process_request(request)
        
        self.assertFalse(response["success"])
        self.assertIn("Unsupported operation", response["error"])
    
    def test_process_request_unimplemented_operations(self):
        """Test unimplemented operations return appropriate errors."""
        operations = ["analyze", "enhance", "refactor", "validate"]
        
        for operation in operations:
            request = {"operation": operation}
            response = self.engine.process_request(request)
            
            self.assertFalse(response["success"])
            self.assertIn("not yet implemented", response["error"])
    
    def test_template_methods(self):
        """Test template methods return valid templates."""
        # Test pytest templates
        unit_class = self.engine._get_pytest_unit_class_template()
        self.assertIn("class Test{CLASS_NAME}:", unit_class)
        self.assertIn("def setup_method(self):", unit_class)
        
        unit_function = self.engine._get_pytest_unit_function_template()
        self.assertIn("def test_{FUNCTION_NAME}_success():", unit_function)
        self.assertIn("@pytest.mark.parametrize", unit_function)
        
        integration = self.engine._get_pytest_integration_template()
        self.assertIn("Integration tests", integration)
        self.assertIn("@requests_mock.Mocker()", integration)
        
        fixture = self.engine._get_pytest_fixture_template()
        self.assertIn("@pytest.fixture", fixture)
        
        # Test Jest templates
        jest_class = self.engine._get_jest_unit_class_template()
        self.assertIn("describe('{CLASS_NAME}'", jest_class)
        self.assertIn("beforeEach(() => {", jest_class)
        
        jest_function = self.engine._get_jest_unit_function_template()
        self.assertIn("it('should handle valid input correctly'", jest_function)
        self.assertIn("test.each([", jest_function)
    
    def test_infrastructure_templates(self):
        """Test infrastructure template methods."""
        # Test conftest template
        conftest = self.engine._get_conftest_template()
        self.assertIn("@pytest.fixture", conftest)
        self.assertIn("def pytest_configure", conftest)
        
        # Test pytest.ini template
        pytest_ini = self.engine._get_pytest_ini_template()
        self.assertIn("[tool:pytest]", pytest_ini)
        self.assertIn("testpaths = tests", pytest_ini)
        
        # Test common fixtures template
        fixtures = self.engine._get_common_fixtures_template()
        self.assertIn("def mock_database", fixtures)
        self.assertIn("def sample_user", fixtures)
        
        # Test Jest config template
        jest_config = self.engine._get_jest_config_template()
        self.assertIn("module.exports", jest_config)
        self.assertIn("testEnvironment:", jest_config)
        
        # Test Jest setup template
        jest_setup = self.engine._get_jest_setup_template()
        self.assertIn("process.env.NODE_ENV", jest_setup)
        self.assertIn("global.createMockUser", jest_setup)
    
    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        self.assertIsNotNone(self.engine.logger)
        self.assertEqual(self.engine.logger.name, "test_writer")
        
        import logging
        self.assertEqual(self.engine.logger.level, logging.INFO)


class TestPythonCodeAnalyzer(unittest.TestCase):
    """Test cases for Python Code Analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PythonCodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_analyze_simple_function(self):
        """Test analyzing a simple function."""
        code = '''
def add(a, b):
    """Add two numbers."""
    return a + b
'''
        
        source_file = os.path.join(self.temp_dir, "simple.py")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(result.language, TestLanguage.PYTHON)
        self.assertEqual(len(result.functions), 1)
        self.assertEqual(result.functions[0].name, "add")
        self.assertEqual(len(result.functions[0].parameters), 2)
        self.assertIn("a", result.functions[0].parameters)
        self.assertEqual(result.functions[0].docstring, "Add two numbers.")
    
    def test_analyze_class_with_methods(self):
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
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(len(result.classes), 1)
        
        calc_class = result.classes[0]
        self.assertEqual(calc_class.name, "Calculator")
        self.assertEqual(calc_class.docstring, "A simple calculator.")
        self.assertEqual(len(calc_class.methods), 3)  # __init__, add, _private_method
        self.assertIn("precision", calc_class.init_parameters)
        
        # Check method analysis
        add_method = next(m for m in calc_class.methods if m.name == "add")
        self.assertEqual(add_method.docstring, "Add two numbers.")
        self.assertIn("a", add_method.parameters)
        self.assertIn("b", add_method.parameters)
    
    def test_analyze_function_with_decorators(self):
        """Test analyzing function with decorators."""
        code = '''
@property
@staticmethod
def get_value():
    return 42
'''
        
        source_file = os.path.join(self.temp_dir, "decorated.py")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(len(result.functions), 1)
        func = result.functions[0]
        self.assertEqual(func.name, "get_value")
        self.assertIn("property", func.decorators)
        self.assertIn("staticmethod", func.decorators)
    
    def test_analyze_async_function(self):
        """Test analyzing async function."""
        code = '''
async def fetch_data():
    """Fetch data asynchronously."""
    return "data"
'''
        
        source_file = os.path.join(self.temp_dir, "async.py")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(len(result.functions), 1)
        func = result.functions[0]
        self.assertEqual(func.name, "fetch_data")
        self.assertTrue(func.is_async)
    
    def test_analyze_imports(self):
        """Test analyzing import statements."""
        code = '''
import os
import sys
from typing import Dict, List
from .local_module import LocalClass
'''
        
        source_file = os.path.join(self.temp_dir, "imports.py")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertIn("os", result.imports)
        self.assertIn("sys", result.imports)
        self.assertIn("typing.Dict", result.imports)
        self.assertIn("typing.List", result.imports)
        self.assertIn(".local_module.LocalClass", result.imports)
    
    def test_calculate_function_complexity(self):
        """Test function complexity calculation."""
        # Simple function (complexity = 1)
        simple_code = '''
def simple():
    return True
'''
        tree = ast.parse(simple_code)
        simple_func = tree.body[0]
        simple_complexity = self.analyzer._calculate_function_complexity(simple_func)
        self.assertEqual(simple_complexity, 1)
        
        # Complex function with branches
        complex_code = '''
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
'''
        tree = ast.parse(complex_code)
        complex_func = tree.body[0]
        complex_complexity = self.analyzer._calculate_function_complexity(complex_func)
        self.assertGreater(complex_complexity, simple_complexity)
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors in source code."""
        invalid_code = '''
def invalid_function(
    # Missing closing parenthesis and colon
    return "invalid"
'''
        
        source_file = os.path.join(self.temp_dir, "invalid.py")
        with open(source_file, 'w') as f:
            f.write(invalid_code)
        
        result = self.analyzer.analyze_file(source_file)
        
        # Should return empty result for invalid syntax
        self.assertEqual(len(result.functions), 0)
        self.assertEqual(len(result.classes), 0)
        self.assertEqual(result.complexity_score, 0.0)


class TestJavaScriptCodeAnalyzer(unittest.TestCase):
    """Test cases for JavaScript Code Analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = JavaScriptCodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_analyze_functions(self):
        """Test analyzing JavaScript functions."""
        code = '''
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
'''
        
        source_file = os.path.join(self.temp_dir, "functions.js")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(result.language, TestLanguage.JAVASCRIPT)
        self.assertEqual(len(result.functions), 3)
        
        # Check function names
        function_names = [f.name for f in result.functions]
        self.assertIn("add", function_names)
        self.assertIn("multiply", function_names)
        self.assertIn("complexFunction", function_names)
        
        # Check parameters
        add_func = next(f for f in result.functions if f.name == "add")
        self.assertEqual(len(add_func.parameters), 2)
        self.assertIn("a", add_func.parameters)
        self.assertIn("b", add_func.parameters)
    
    def test_analyze_classes(self):
        """Test analyzing JavaScript classes."""
        code = '''
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
'''
        
        source_file = os.path.join(self.temp_dir, "classes.js")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertEqual(len(result.classes), 2)
        
        # Check class names
        class_names = [c.name for c in result.classes]
        self.assertIn("Calculator", class_names)
        self.assertIn("AdvancedCalculator", class_names)
        
        # Check inheritance
        advanced_calc = next(c for c in result.classes if c.name == "AdvancedCalculator")
        self.assertIn("Calculator", advanced_calc.base_classes)
    
    def test_analyze_imports(self):
        """Test analyzing JavaScript imports."""
        code = '''
import { add, subtract } from './math';
import Calculator from './Calculator';
const { multiply } = require('./operations');
import React from 'react';
'''
        
        source_file = os.path.join(self.temp_dir, "imports.js")
        with open(source_file, 'w') as f:
            f.write(code)
        
        result = self.analyzer.analyze_file(source_file)
        
        self.assertIn("./math", result.imports)
        self.assertIn("./Calculator", result.imports)
        self.assertIn("./operations", result.imports)
        self.assertIn("react", result.imports)


class TestPytestGenerator(unittest.TestCase):
    """Test cases for Pytest Generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = PytestGenerator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample source info
        self.sample_function = FunctionInfo(
            name="calculate", parameters=["x", "y"], return_type="int",
            docstring="Calculate something.", complexity=2, line_number=10
        )
        
        self.sample_class = ClassInfo(
            name="Calculator", methods=[self.sample_function],
            init_parameters=["precision"], base_classes=[],
            docstring="Calculator class.", line_number=5
        )
        
        self.sample_source_info = SourceFileInfo(
            filepath="calculator.py",
            language=TestLanguage.PYTHON,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math"],
            complexity_score=3.0
        )
        
        self.sample_requirements = TestRequirements([TestType.UNIT])
        self.sample_configuration = TestConfiguration()
        self.sample_options = TestOptions()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generate_test_file(self):
        """Test generating a pytest test file."""
        test_dir = os.path.join(self.temp_dir, "tests")
        
        result = self.generator.generate_test_file(
            self.sample_source_info,
            test_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TestFileInfo)
        self.assertTrue(result.path.endswith("test_calculator.py"))
        self.assertGreater(result.test_count, 0)
        self.assertGreater(result.coverage_estimate, 0)
        
        # Check that file was actually created
        self.assertTrue(os.path.exists(result.path))
        
        # Check file contents
        with open(result.path, 'r') as f:
            content = f.read()
        
        self.assertIn("import pytest", content)
        self.assertIn("from unittest.mock import Mock, patch", content)
        self.assertIn("class TestCalculator:", content)
        self.assertIn("def test_calculate_success(self):", content)
    
    def test_generate_pytest_content(self):
        """Test generating pytest content."""
        content = self.generator._generate_pytest_content(
            self.sample_source_info,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options
        )
        
        # Check imports
        self.assertIn("import pytest", content)
        self.assertIn("from calculator import Calculator, calculate", content)
        
        # Check class test structure
        self.assertIn("class TestCalculator:", content)
        self.assertIn("def setup_method(self):", content)
        self.assertIn("def teardown_method(self):", content)
        
        # Check function tests
        self.assertIn("def test_calculate_success():", content)
        self.assertIn("def test_calculate_edge_cases():", content)
        self.assertIn("def test_calculate_error_handling():", content)
    
    def test_generate_class_tests(self):
        """Test generating tests for a class."""
        tests = self.generator._generate_class_tests(self.sample_class, self.sample_options)
        
        self.assertIsInstance(tests, list)
        self.assertGreater(len(tests), 0)
        
        test_content = "\n".join(tests)
        self.assertIn("class TestCalculator:", test_content)
        self.assertIn("def setup_method(self):", test_content)
        self.assertIn("self.instance = Calculator", test_content)
        self.assertIn("def test_calculate_success(self):", test_content)
    
    def test_generate_function_tests(self):
        """Test generating tests for a function."""
        tests = self.generator._generate_function_tests(self.sample_function, self.sample_options)
        
        self.assertIsInstance(tests, list)
        self.assertGreater(len(tests), 0)
        
        test_content = "\n".join(tests)
        self.assertIn("def test_calculate_success():", test_content)
        self.assertIn("def test_calculate_edge_cases():", test_content)
        self.assertIn("def test_calculate_error_handling():", test_content)
        self.assertIn("with pytest.raises(Exception):", test_content)
    
    def test_empty_source_file(self):
        """Test handling empty source file."""
        empty_source_info = SourceFileInfo(
            filepath="empty.py",
            language=TestLanguage.PYTHON,
            functions=[],
            classes=[],
            imports=[],
            complexity_score=0.0
        )
        
        result = self.generator.generate_test_file(
            empty_source_info,
            self.temp_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options
        )
        
        self.assertIsNone(result)


class TestJestGenerator(unittest.TestCase):
    """Test cases for Jest Generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = JestGenerator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample source info
        self.sample_function = FunctionInfo(
            name="calculate", parameters=["x", "y"], return_type="number",
            docstring="Calculate something.", complexity=2, line_number=10
        )
        
        self.sample_class = ClassInfo(
            name="Calculator", methods=[self.sample_function],
            init_parameters=[], base_classes=[],
            docstring="Calculator class.", line_number=5
        )
        
        self.sample_source_info = SourceFileInfo(
            filepath="calculator.js",
            language=TestLanguage.JAVASCRIPT,
            functions=[self.sample_function],
            classes=[self.sample_class],
            imports=["math"],
            complexity_score=3.0
        )
        
        self.sample_requirements = TestRequirements([TestType.UNIT])
        self.sample_configuration = TestConfiguration(testing_framework=TestFramework.JEST)
        self.sample_options = TestOptions()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generate_test_file(self):
        """Test generating a Jest test file."""
        test_dir = os.path.join(self.temp_dir, "tests")
        
        result = self.generator.generate_test_file(
            self.sample_source_info,
            test_dir,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TestFileInfo)
        self.assertTrue(result.path.endswith("calculator.test.js"))
        self.assertGreater(result.test_count, 0)
        
        # Check that file was actually created
        self.assertTrue(os.path.exists(result.path))
        
        # Check file contents
        with open(result.path, 'r') as f:
            content = f.read()
        
        self.assertIn("import { Calculator, calculate }", content)
        self.assertIn("describe('Calculator'", content)
        self.assertIn("describe('calculate'", content)
    
    def test_generate_jest_content(self):
        """Test generating Jest content."""
        content = self.generator._generate_jest_content(
            self.sample_source_info,
            self.sample_requirements,
            self.sample_configuration,
            self.sample_options
        )
        
        # Check imports
        self.assertIn("import { Calculator, calculate }", content)
        
        # Check test structure
        self.assertIn("describe('Calculator'", content)
        self.assertIn("beforeEach(() => {", content)
        self.assertIn("afterEach(() => {", content)
        self.assertIn("jest.clearAllMocks()", content)
    
    def test_generate_jest_class_tests(self):
        """Test generating Jest tests for a class."""
        tests = self.generator._generate_jest_class_tests(self.sample_class, self.sample_options)
        
        self.assertIsInstance(tests, list)
        self.assertGreater(len(tests), 0)
        
        test_content = "\n".join(tests)
        self.assertIn("describe('Calculator'", test_content)
        self.assertIn("beforeEach(() => {", test_content)
        self.assertIn("calculator = new Calculator()", test_content)
        self.assertIn("describe('calculate'", test_content)
    
    def test_generate_jest_function_tests(self):
        """Test generating Jest tests for a function."""
        tests = self.generator._generate_jest_function_tests(self.sample_function, self.sample_options)
        
        self.assertIsInstance(tests, list)
        self.assertGreater(len(tests), 0)
        
        test_content = "\n".join(tests)
        self.assertIn("describe('calculate'", test_content)
        self.assertIn("it('should work with valid input'", test_content)
        self.assertIn("it('should handle invalid input'", test_content)
        self.assertIn("expect(() => {", test_content)
        self.assertIn("}).toThrow()", test_content)


if __name__ == '__main__':
    unittest.main()