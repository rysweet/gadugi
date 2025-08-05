"""
AST Parser Abstraction Layer - Pluggable architecture for multi-language code analysis

Provides pluggable AST parsing capabilities for identifying architectural elements
and changes across different programming languages.
"""

import ast
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Union
from pathlib import Path
from enum import Enum


class ChangeType(Enum):
    """Types of architectural changes"""
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"


class ImpactLevel(Enum):
    """Impact levels for architectural changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ElementType(Enum):
    """Types of architectural elements"""
    CLASS = "class"
    FUNCTION = "function"
    MODULE = "module"
    INTERFACE = "interface"
    DECORATOR = "decorator"
    IMPORT = "import"
    CONSTANT = "constant"
    ASYNC_FUNCTION = "async_function"


@dataclass
class ArchitecturalElement:
    """Represents an architectural element extracted from code"""
    element_type: ElementType
    name: str
    location: str  # file:line format
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parent_element: Optional[str] = None
    is_async: bool = False
    is_public: bool = True
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None

    def __hash__(self):
        return hash((self.element_type, self.name, self.location))


@dataclass
class ArchitecturalChange:
    """Represents a change with architectural impact"""
    change_type: ChangeType
    element: ArchitecturalElement
    impact_level: ImpactLevel
    affected_components: List[str] = field(default_factory=list)
    design_implications: List[str] = field(default_factory=list)
    old_element: Optional[ArchitecturalElement] = None
    confidence_score: float = 1.0
    requires_adr: bool = False
    
    def get_description(self) -> str:
        """Get human-readable description of the change"""
        action_map = {
            ChangeType.ADDED: "Added",
            ChangeType.MODIFIED: "Modified", 
            ChangeType.REMOVED: "Removed",
            ChangeType.RENAMED: "Renamed"
        }
        
        action = action_map[self.change_type]
        element_type = self.element.element_type.value
        
        if self.change_type == ChangeType.RENAMED and self.old_element:
            return f"{action} {element_type} '{self.old_element.name}' to '{self.element.name}'"
        else:
            return f"{action} {element_type} '{self.element.name}'"


class ASTParser(ABC):
    """Base class for language-specific AST parsers"""
    
    def __init__(self):
        self.supported_extensions: Set[str] = set()
        self.architectural_patterns: Dict[str, List[str]] = {}
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[ArchitecturalElement]:
        """Parse file and extract architectural elements"""
        pass
    
    @abstractmethod
    def analyze_changes(self, old_elements: List[ArchitecturalElement], 
                       new_elements: List[ArchitecturalElement]) -> List[ArchitecturalChange]:
        """Analyze changes between old and new elements"""
        pass
    
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def detect_patterns(self, element: ArchitecturalElement, content: str) -> List[str]:
        """Detect architectural patterns in the element"""
        detected_patterns = []
        
        for pattern_name, indicators in self.architectural_patterns.items():
            if any(indicator in content.lower() for indicator in indicators):
                detected_patterns.append(pattern_name)
        
        return detected_patterns
    
    def calculate_complexity(self, node: Any) -> Dict[str, Any]:
        """Calculate complexity metrics for a code element"""
        # Base implementation - subclasses can override
        return {
            "cyclomatic_complexity": 1,
            "cognitive_complexity": 1,
            "nesting_depth": 0
        }


class PythonASTParser(ASTParser):
    """Python-specific AST parser using built-in ast module"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = {'.py', '.pyx', '.pyi'}
        self.architectural_patterns = {
            "singleton": ["__new__", "_instance", "instance"],
            "factory": ["create", "build", "make", "factory"],
            "observer": ["notify", "subscribe", "observer", "listener"],
            "decorator": ["@", "wrapper", "decorator"],
            "context_manager": ["__enter__", "__exit__", "contextmanager"],
            "async_context_manager": ["__aenter__", "__aexit__"],
            "dataclass": ["@dataclass", "dataclasses"],
            "abc": ["ABC", "abstractmethod", "@abstractmethod"],
            "enum": ["Enum", "IntEnum", "Flag"],
            "protocol": ["Protocol", "runtime_checkable"]
        }
    
    def parse_file(self, file_path: str) -> List[ArchitecturalElement]:
        """Parse Python file and extract architectural elements"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            elements = []
            
            # Extract elements using visitor pattern
            visitor = PythonASTVisitor(file_path, content, self)
            visitor.visit(tree)
            elements.extend(visitor.elements)
            
            return elements
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def analyze_changes(self, old_elements: List[ArchitecturalElement], 
                       new_elements: List[ArchitecturalElement]) -> List[ArchitecturalChange]:
        """Analyze changes between old and new Python elements"""
        changes = []
        
        # Create lookups for efficient comparison
        old_by_name = {elem.name: elem for elem in old_elements}
        new_by_name = {elem.name: elem for elem in new_elements}
        
        # Find added elements
        for elem in new_elements:
            if elem.name not in old_by_name:
                impact = self._assess_impact_level(elem, ChangeType.ADDED)
                change = ArchitecturalChange(
                    change_type=ChangeType.ADDED,
                    element=elem,
                    impact_level=impact,
                    requires_adr=impact in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
                )
                change.design_implications = self._get_design_implications(change)
                changes.append(change)
        
        # Find removed elements  
        for elem in old_elements:
            if elem.name not in new_by_name:
                impact = self._assess_impact_level(elem, ChangeType.REMOVED)
                change = ArchitecturalChange(
                    change_type=ChangeType.REMOVED,
                    element=elem,
                    impact_level=impact,
                    old_element=elem,
                    requires_adr=impact in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
                )
                change.design_implications = self._get_design_implications(change)
                changes.append(change)
        
        # Find modified elements
        for elem in new_elements:
            if elem.name in old_by_name:
                old_elem = old_by_name[elem.name]
                if self._elements_differ(old_elem, elem):
                    impact = self._assess_impact_level(elem, ChangeType.MODIFIED)
                    change = ArchitecturalChange(
                        change_type=ChangeType.MODIFIED,
                        element=elem,
                        impact_level=impact,
                        old_element=old_elem,
                        requires_adr=impact in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
                    )
                    change.design_implications = self._get_design_implications(change)
                    changes.append(change)
        
        return changes
    
    def _elements_differ(self, old: ArchitecturalElement, new: ArchitecturalElement) -> bool:
        """Check if two elements are significantly different"""
        # Check important attributes that indicate architectural changes
        return (
            old.dependencies != new.dependencies or
            old.interfaces != new.interfaces or
            old.patterns != new.patterns or
            old.decorators != new.decorators or
            old.is_async != new.is_async or
            old.parameters != new.parameters or
            old.return_type != new.return_type
        )
    
    def _assess_impact_level(self, element: ArchitecturalElement, change_type: ChangeType) -> ImpactLevel:
        """Assess the architectural impact level of a change"""
        # High impact indicators
        high_impact_patterns = ["abc", "protocol", "singleton", "factory"]
        high_impact_decorators = ["@abstractmethod", "@classmethod", "@staticmethod", "@property"]
        
        # Critical impact indicators
        critical_patterns = ["__init__", "__new__", "__enter__", "__exit__"]
        
        if any(pattern in element.patterns for pattern in high_impact_patterns):
            return ImpactLevel.HIGH
        
        if any(decorator in element.decorators for decorator in high_impact_decorators):
            return ImpactLevel.HIGH
            
        if element.element_type == ElementType.CLASS:
            return ImpactLevel.MEDIUM
        
        if element.name.startswith("__") and element.name.endswith("__"):
            return ImpactLevel.HIGH
        
        if any(pattern in element.name.lower() for pattern in critical_patterns):
            return ImpactLevel.CRITICAL
        
        return ImpactLevel.LOW
    
    def _get_design_implications(self, change: ArchitecturalChange) -> List[str]:
        """Get design implications for a change"""
        implications = []
        element = change.element
        
        if element.element_type == ElementType.CLASS:
            implications.append("May affect inheritance hierarchy and client code")
            
        if "abc" in element.patterns:
            implications.append("Abstract base class change affects all implementations")
            
        if "singleton" in element.patterns:
            implications.append("Singleton pattern change affects global state management")
            
        if element.is_async:
            implications.append("Async function change affects concurrency patterns")
            
        if len(element.dependencies) > 5:
            implications.append("High coupling - consider dependency reduction")
        
        return implications


class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for extracting architectural elements from Python code"""
    
    def __init__(self, file_path: str, content: str, parser: PythonASTParser):
        self.file_path = file_path
        self.content = content
        self.parser = parser
        self.elements: List[ArchitecturalElement] = []
        self.current_class: Optional[str] = None
        self.imports: Set[str] = set()
    
    def visit_Import(self, node: ast.Import):
        """Handle import statements"""
        for alias in node.names:
            self.imports.add(alias.name)
            element = ArchitecturalElement(
                element_type=ElementType.IMPORT,
                name=alias.name,
                location=f"{self.file_path}:{node.lineno}"
            )
            self.elements.append(element)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from...import statements"""
        module_name = node.module or ""
        for alias in node.names:
            import_name = f"{module_name}.{alias.name}"
            self.imports.add(import_name)
            element = ArchitecturalElement(
                element_type=ElementType.IMPORT,
                name=import_name,
                location=f"{self.file_path}:{node.lineno}"
            )
            self.elements.append(element)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions"""
        old_class = self.current_class
        self.current_class = node.name
        
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        base_classes = [self._get_base_name(base) for base in node.bases]
        
        element = ArchitecturalElement(
            element_type=ElementType.CLASS,
            name=node.name,
            location=f"{self.file_path}:{node.lineno}",
            dependencies=list(self.imports),
            interfaces=base_classes,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            patterns=self.parser.detect_patterns(None, self.content),
            complexity_metrics=self.parser.calculate_complexity(node),
            is_public=not node.name.startswith('_')
        )
        
        self.elements.append(element)
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions"""
        self._handle_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions"""
        self._handle_function(node, is_async=True)
    
    def _handle_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Common handler for function and async function definitions"""
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        parameters = [arg.arg for arg in node.args.args]
        
        element_type = ElementType.ASYNC_FUNCTION if is_async else ElementType.FUNCTION
        
        element = ArchitecturalElement(
            element_type=element_type,
            name=node.name,
            location=f"{self.file_path}:{node.lineno}",
            dependencies=list(self.imports),
            decorators=decorators,
            docstring=ast.get_docstring(node),
            parent_element=self.current_class,
            is_async=is_async,
            is_public=not node.name.startswith('_'),
            parameters=parameters,
            return_type=self._get_return_type(node),
            patterns=self.parser.detect_patterns(None, self.content),
            complexity_metrics=self.parser.calculate_complexity(node)
        )
        
        self.elements.append(element)
        self.generic_visit(node)
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_attr_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_attr_name(base.value)}.{base.attr}"
        return str(base)
    
    def _get_attr_name(self, node: ast.expr) -> str:
        """Extract attribute name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_return_type(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:
        """Extract return type annotation if present"""
        if node.returns:
            return ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        return None


class TypeScriptASTParser(ASTParser):
    """TypeScript-specific AST parser (placeholder for future implementation)"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = {'.ts', '.tsx', '.js', '.jsx'}
        self.architectural_patterns = {
            "decorator": ["@", "decorator"],
            "singleton": ["singleton", "instance"],
            "factory": ["factory", "create", "build"],
            "observer": ["observer", "subscribe", "emit"],
            "promise": ["Promise", "async", "await"],
            "component": ["Component", "component"],
            "service": ["Service", "@Injectable"],
            "module": ["Module", "@NgModule"]
        }
    
    def parse_file(self, file_path: str) -> List[ArchitecturalElement]:
        """Parse TypeScript file - placeholder implementation"""
        # TODO: Implement TypeScript AST parsing using a TypeScript parser
        # For now, return basic file-level element
        return [
            ArchitecturalElement(
                element_type=ElementType.MODULE,
                name=Path(file_path).stem,
                location=f"{file_path}:1",
                patterns=["typescript_module"]
            )
        ]
    
    def analyze_changes(self, old_elements: List[ArchitecturalElement], 
                       new_elements: List[ArchitecturalElement]) -> List[ArchitecturalChange]:
        """Analyze TypeScript changes - placeholder implementation"""
        # TODO: Implement TypeScript-specific change analysis
        return []


class ASTParserFactory:
    """Factory for creating appropriate AST parsers based on file type"""
    
    def __init__(self):
        self._parsers = {
            'python': PythonASTParser(),
            'typescript': TypeScriptASTParser(),
        }
    
    def get_parser(self, file_path: str) -> Optional[ASTParser]:
        """Get appropriate parser for the given file"""
        for parser in self._parsers.values():
            if parser.can_parse(file_path):
                return parser
        return None
    
    def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions"""
        extensions = set()
        for parser in self._parsers.values():
            extensions.update(parser.supported_extensions)
        return extensions
    
    def register_parser(self, name: str, parser: ASTParser):
        """Register a new parser"""
        self._parsers[name] = parser
    
    def get_parser_by_name(self, name: str) -> Optional[ASTParser]:
        """Get parser by name"""
        return self._parsers.get(name)