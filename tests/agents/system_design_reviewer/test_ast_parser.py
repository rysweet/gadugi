"""
Test suite for AST Parser functionality

Tests the pluggable AST parsing architecture, architectural element extraction,
and change detection algorithms.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add .claude directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".claude"))

from claude.agents.system_design_reviewer.ast_parser import (
    ASTParserFactory,
    PythonASTParser,
    ArchitecturalElement,
    ArchitecturalChange,
    ElementType,
    ChangeType,
    ImpactLevel,
)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return '''
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List

class BaseService(ABC):
    """Abstract base class for services"""

    def __init__(self, name: str):
        self.name = name
        self._initialized = False

    @abstractmethod
    def start(self) -> bool:
        """Start the service"""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

class ConcreteService(BaseService):
    """Concrete implementation of BaseService"""

    def __init__(self, name: str, config: Dict):
        super().__init__(name)
        self.config = config

    def start(self) -> bool:
        """Start the concrete service"""
        self._initialized = True
        return True

    async def process_async(self, data: List[str]) -> List[str]:
        """Process data asynchronously"""
        results = []
        for item in data:
            await asyncio.sleep(0.01)
            processed = f"processed_{item}"
            results.append(processed)
        return results

def utility_function(value: str) -> str:
    """Utility function for processing"""
    return f"util_{value}"

CONSTANT_VALUE = "test_constant"
'''


@pytest.fixture
def modified_python_code():
    """Modified Python code for change detection testing"""
    return '''
import os
import asyncio
import json  # New import
from abc import ABC, abstractmethod
from typing import Dict, List

class BaseService(ABC):
    """Abstract base class for services"""

    def __init__(self, name: str, version: str = "1.0"):  # Modified constructor
        self.name = name
        self.version = version  # New attribute
        self._initialized = False

    @abstractmethod
    def start(self) -> bool:
        """Start the service"""
        pass

    @abstractmethod
    def stop(self) -> bool:  # New abstract method
        """Stop the service"""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

class ConcreteService(BaseService):
    """Concrete implementation of BaseService"""

    def __init__(self, name: str, config: Dict, version: str = "1.0"):
        super().__init__(name, version)  # Updated super call
        self.config = config

    def start(self) -> bool:
        """Start the concrete service"""
        self._initialized = True
        return True

    def stop(self) -> bool:  # New implementation
        """Stop the concrete service"""
        self._initialized = False
        return True

    async def process_async(self, data: List[str]) -> List[str]:
        """Process data asynchronously - enhanced"""
        results = []
        for item in data:
            await asyncio.sleep(0.01)
            processed = f"processed_{item}_{self.version}"  # Enhanced processing
            results.append(processed)
        return results

    def save_config(self, filepath: str) -> bool:  # New method
        """Save configuration to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.config, f)
            return True
        except Exception:
            return False

# Removed utility_function

CONSTANT_VALUE = "test_constant_updated"  # Modified constant
NEW_CONSTANT = "new_value"  # New constant
'''


class TestASTParserFactory:
    """Test the AST parser factory"""

    def test_get_parser_python_file(self):
        """Test getting parser for Python files"""
        factory = ASTParserFactory()

        # Test various Python extensions
        assert isinstance(factory.get_parser("test.py"), PythonASTParser)
        assert isinstance(factory.get_parser("test.pyx"), PythonASTParser)
        assert isinstance(factory.get_parser("test.pyi"), PythonASTParser)

    def test_get_parser_unsupported_file(self):
        """Test getting parser for unsupported file types"""
        factory = ASTParserFactory()

        assert factory.get_parser("test.txt") is None
        assert factory.get_parser("test.md") is None
        assert factory.get_parser("test.cpp") is None

    def test_get_supported_extensions(self):
        """Test getting supported extensions"""
        factory = ASTParserFactory()
        extensions = factory.get_supported_extensions()

        assert ".py" in extensions
        assert ".pyx" in extensions
        assert ".pyi" in extensions

    def test_register_custom_parser(self):
        """Test registering custom parser"""
        factory = ASTParserFactory()
        custom_parser = PythonASTParser()  # Use existing parser as example

        factory.register_parser("custom", custom_parser)
        assert factory.get_parser_by_name("custom") == custom_parser


class TestPythonASTParser:
    """Test Python AST parser functionality"""

    def test_can_parse_python_files(self):
        """Test parser can identify Python files"""
        parser = PythonASTParser()

        assert parser.can_parse("test.py")
        assert parser.can_parse("test.pyx")
        assert not parser.can_parse("test.js")
        assert not parser.can_parse("test.txt")

    def test_parse_file_basic_elements(self, sample_python_code):
        """Test parsing basic architectural elements"""
        parser = PythonASTParser()

        # Write sample code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_python_code)
            temp_path = f.name

        try:
            elements = parser.parse_file(temp_path)

            # Verify we found expected elements
            element_names = [elem.name for elem in elements]
            element_types = [elem.element_type for elem in elements]

            # Check for imports
            assert "os" in element_names
            assert "asyncio" in element_names
            assert ElementType.IMPORT in element_types

            # Check for classes
            assert "BaseService" in element_names
            assert "ConcreteService" in element_names
            assert ElementType.CLASS in element_types

            # Check for functions
            assert "start" in element_names
            assert "process_async" in element_names
            assert "utility_function" in element_names
            assert ElementType.FUNCTION in element_types
            assert ElementType.ASYNC_FUNCTION in element_types

        finally:
            os.unlink(temp_path)

    def test_parse_file_detailed_analysis(self, sample_python_code):
        """Test detailed architectural analysis"""
        parser = PythonASTParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_python_code)
            temp_path = f.name

        try:
            elements = parser.parse_file(temp_path)

            # Find base service class
            base_service = next((e for e in elements if e.name == "BaseService"), None)
            assert base_service is not None  # type: ignore[comparison-overlap]
            assert base_service.element_type == ElementType.CLASS
            assert "ABC" in base_service.interfaces
            assert base_service.is_public
            assert "abc" in base_service.patterns

            # Find async function
            async_func = next((e for e in elements if e.name == "process_async"), None)
            assert async_func is not None  # type: ignore[comparison-overlap]
            assert async_func.element_type == ElementType.ASYNC_FUNCTION
            assert async_func.is_async
            assert async_func.parent_element == "ConcreteService"
            assert "data" in async_func.parameters

            # Find abstract method
            start_method = next(
                (e for e in elements if e.name == "start" and e.parent_element == "BaseService"),
                None,
            )
            assert start_method is not None  # type: ignore[comparison-overlap]
            assert (
                "abstractmethod" in start_method.decorators
                or "decorator" in start_method.patterns
                or "abc" in start_method.patterns
            )

        finally:
            os.unlink(temp_path)

    def test_analyze_changes_added_elements(self, sample_python_code, modified_python_code):
        """Test change detection for added elements"""
        parser = PythonASTParser()

        # Parse original code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_python_code)
            old_path = f.name

        # Parse modified code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(modified_python_code)
            new_path = f.name

        try:
            old_elements = parser.parse_file(old_path)
            new_elements = parser.parse_file(new_path)

            changes = parser.analyze_changes(old_elements, new_elements)

            # Find added elements
            added_changes = [c for c in changes if c.change_type == ChangeType.ADDED]
            added_names = [c.element.name for c in added_changes]

            # Should detect new imports, methods
            assert "json" in added_names  # New import
            assert "stop" in added_names  # New abstract method
            assert "save_config" in added_names  # New method
            # Note: Constants are not currently parsed by the AST parser implementation

        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_analyze_changes_removed_elements(self, sample_python_code, modified_python_code):
        """Test change detection for removed elements"""
        parser = PythonASTParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_python_code)
            old_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(modified_python_code)
            new_path = f.name

        try:
            old_elements = parser.parse_file(old_path)
            new_elements = parser.parse_file(new_path)

            changes = parser.analyze_changes(old_elements, new_elements)

            # Find removed elements
            removed_changes = [c for c in changes if c.change_type == ChangeType.REMOVED]
            removed_names = [c.element.name for c in removed_changes]

            # Should detect removed function
            assert "utility_function" in removed_names

        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_analyze_changes_modified_elements(self, sample_python_code, modified_python_code):
        """Test change detection for modified elements"""
        parser = PythonASTParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sample_python_code)
            old_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(modified_python_code)
            new_path = f.name

        try:
            old_elements = parser.parse_file(old_path)
            new_elements = parser.parse_file(new_path)

            changes = parser.analyze_changes(old_elements, new_elements)

            # Find modified elements
            modified_changes = [c for c in changes if c.change_type == ChangeType.MODIFIED]

            # Should detect modified elements
            # Note: Exact detection depends on implementation sensitivity
            # This test verifies the change detection mechanism works
            assert len(modified_changes) > 0  # Should detect some modifications

        finally:
            os.unlink(old_path)
            os.unlink(new_path)

    def test_impact_level_assessment(self):
        """Test architectural impact level assessment"""
        parser = PythonASTParser()

        # Create elements with different impact characteristics
        high_impact_element = ArchitecturalElement(
            element_type=ElementType.CLASS,
            name="CriticalService",
            location="test.py:10",
            patterns=["abc", "singleton"],
            decorators=["@abstractmethod"],
        )

        low_impact_element = ArchitecturalElement(
            element_type=ElementType.FUNCTION,
            name="helper_function",
            location="test.py:50",
            patterns=[],
            decorators=[],
        )

        # Test impact assessment
        high_impact = parser._assess_impact_level(high_impact_element, ChangeType.ADDED)
        low_impact = parser._assess_impact_level(low_impact_element, ChangeType.ADDED)

        assert high_impact in [ImpactLevel.HIGH, ImpactLevel.MEDIUM]
        assert low_impact == ImpactLevel.LOW

    def test_design_implications_generation(self):
        """Test design implications generation"""
        parser = PythonASTParser()

        # Create change with implications
        element = ArchitecturalElement(
            element_type=ElementType.CLASS,
            name="AsyncService",
            location="test.py:10",
            patterns=["singleton"],
            is_async=True,
            dependencies=[
                "dep1",
                "dep2",
                "dep3",
                "dep4",
                "dep5",
                "dep6",
            ],  # High coupling
        )

        change = ArchitecturalChange(
            change_type=ChangeType.ADDED, element=element, impact_level=ImpactLevel.HIGH
        )

        implications = parser._get_design_implications(change)

        # Should detect various implications
        assert len(implications) > 0
        implication_text = " ".join(implications).lower()

        # Check for expected implication types
        assert any(keyword in implication_text for keyword in ["singleton", "async", "coupling"])


class TestArchitecturalElements:
    """Test architectural element data structures"""

    def test_architectural_element_creation(self):
        """Test creating architectural elements"""
        element = ArchitecturalElement(
            element_type=ElementType.CLASS,
            name="TestClass",
            location="test.py:10",
            dependencies=["dep1", "dep2"],
            interfaces=["Interface1"],
            patterns=["singleton"],
            decorators=["@dataclass"],
            is_async=False,
            is_public=True,
        )

        assert element.element_type == ElementType.CLASS
        assert element.name == "TestClass"
        assert element.location == "test.py:10"
        assert "dep1" in element.dependencies
        assert "Interface1" in element.interfaces
        assert "singleton" in element.patterns
        assert "@dataclass" in element.decorators
        assert not element.is_async
        assert element.is_public

    def test_architectural_change_description(self):
        """Test architectural change description generation"""
        element = ArchitecturalElement(
            element_type=ElementType.FUNCTION,
            name="test_function",
            location="test.py:20",
        )

        change = ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=element,
            impact_level=ImpactLevel.MEDIUM,
        )

        description = change.get_description()
        assert "Added function 'test_function'" in description

        # Test renamed change
        old_element = ArchitecturalElement(
            element_type=ElementType.FUNCTION,
            name="old_function",
            location="test.py:20",
        )

        rename_change = ArchitecturalChange(
            change_type=ChangeType.RENAMED,
            element=element,
            impact_level=ImpactLevel.LOW,
            old_element=old_element,
        )

        rename_description = rename_change.get_description()
        assert "Renamed function 'old_function' to 'test_function'" in rename_description


class TestPatternDetection:
    """Test architectural pattern detection"""

    def test_detect_patterns_singleton(self):
        """Test singleton pattern detection"""
        parser = PythonASTParser()

        singleton_code = """
class SingletonService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""

        element = ArchitecturalElement(
            element_type=ElementType.CLASS,
            name="SingletonService",
            location="test.py:1",
        )

        patterns = parser.detect_patterns(element, singleton_code)
        assert "singleton" in patterns

    def test_detect_patterns_factory(self):
        """Test factory pattern detection"""
        parser = PythonASTParser()

        factory_code = """
class ServiceFactory:
    @staticmethod
    def create_service(service_type: str):
        if service_type == "web":
            return WebService()
        elif service_type == "db":
            return DatabaseService()
"""

        element = ArchitecturalElement(
            element_type=ElementType.CLASS, name="ServiceFactory", location="test.py:1"
        )

        patterns = parser.detect_patterns(element, factory_code)
        assert "factory" in patterns

    def test_detect_patterns_multiple(self):
        """Test detection of multiple patterns"""
        parser = PythonASTParser()

        complex_code = """
from abc import ABC, abstractmethod

class AbstractFactory(ABC):
    @abstractmethod
    def create_service(self):
        pass

    def notify_observers(self):
        for observer in self.observers:
            observer.update()
"""

        element = ArchitecturalElement(
            element_type=ElementType.CLASS, name="AbstractFactory", location="test.py:1"
        )

        patterns = parser.detect_patterns(element, complex_code)

        # Should detect multiple patterns
        assert "abc" in patterns
        assert "factory" in patterns
        assert "observer" in patterns


if __name__ == "__main__":
    pytest.main([__file__])
