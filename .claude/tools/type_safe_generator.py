#!/usr/bin/env python3
"""
Type-Safe Python Code Generator

Generates Python code with complete type annotations from the start,
avoiding common pyright errors proactively.
"""

from __future__ import annotations

try:
    import black  # type: ignore[import-untyped]
    HAS_BLACK = True
except ImportError:
    black = None  # type: ignore[assignment]
    HAS_BLACK = False
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeAlias,
    Final,
)

# Type aliases
FieldSpec: TypeAlias = Dict[str, Any]
MethodSpec: TypeAlias = Dict[str, Any]
ImportSpec: TypeAlias = Tuple[str, Optional[List[str]]]

# Constants
DEFAULT_INDENT: Final[str] = "    "
MAX_LINE_LENGTH: Final[int] = 88


class CodeElementType(Enum):
    """Types of code elements to generate."""
    
    DATACLASS = auto()
    ENUM = auto()
    PROTOCOL = auto()
    ABC = auto()
    SERVICE = auto()
    TEST = auto()
    EXCEPTION = auto()


@dataclass
class ImportManager:
    """Manages imports for generated code."""
    
    standard_imports: Set[str] = field(default_factory=set)
    typing_imports: Set[str] = field(default_factory=set)
    third_party_imports: Set[str] = field(default_factory=set)
    local_imports: Set[str] = field(default_factory=set)
    
    def add_typing(self, *items: str) -> None:
        """Add typing imports."""
        self.typing_imports.update(items)
    
    def add_standard(self, *items: str) -> None:
        """Add standard library imports."""
        self.standard_imports.update(items)
    
    def add_third_party(self, *items: str) -> None:
        """Add third-party imports."""
        self.third_party_imports.update(items)
    
    def generate(self) -> str:
        """Generate import statements."""
        lines: List[str] = ["from __future__ import annotations", ""]
        
        # Standard library imports
        if self.standard_imports:
            for imp in sorted(self.standard_imports):
                lines.append(imp)
            lines.append("")
        
        # Typing imports
        if self.typing_imports:
            typing_list = ", ".join(sorted(self.typing_imports))
            lines.append(f"from typing import {typing_list}")
            lines.append("")
        
        # Third-party imports
        if self.third_party_imports:
            for imp in sorted(self.third_party_imports):
                lines.append(imp)
            lines.append("")
        
        # Local imports
        if self.local_imports:
            for imp in sorted(self.local_imports):
                lines.append(imp)
            lines.append("")
        
        return "\n".join(lines)


@dataclass
class TypeAnnotation:
    """Represents a type annotation."""
    
    base_type: str
    optional: bool = False
    generic_args: List[str] = field(default_factory=list)
    
    def render(self) -> str:
        """Render the type annotation."""
        if self.generic_args:
            args = ", ".join(self.generic_args)
            result = f"{self.base_type}[{args}]"
        else:
            result = self.base_type
        
        if self.optional:
            result = f"Optional[{result}]"
        
        return result


@dataclass
class FieldDefinition:
    """Definition of a class field."""
    
    name: str
    type_annotation: TypeAnnotation
    default: Optional[str] = None
    is_factory: bool = False
    is_required: bool = False
    docstring: Optional[str] = None
    validator: Optional[str] = None
    
    def render_dataclass(self) -> str:
        """Render as dataclass field."""
        type_str = self.type_annotation.render()
        
        if self.is_factory:
            return f"{self.name}: {type_str} = field(default_factory={self.default or 'list'})"
        elif self.default is not None:
            return f"{self.name}: {type_str} = {self.default}"
        elif not self.is_required and self.type_annotation.optional:
            return f"{self.name}: {type_str} = None"
        else:
            return f"{self.name}: {type_str}"


@dataclass
class MethodDefinition:
    """Definition of a class method."""
    
    name: str
    params: List[Tuple[str, str]]  # (name, type)
    return_type: str
    body: List[str]
    is_async: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_abstract: bool = False
    docstring: Optional[str] = None
    
    def render(self, indent: int = 1) -> List[str]:
        """Render method definition."""
        lines: List[str] = []
        indent_str = DEFAULT_INDENT * indent
        
        # Decorators
        if self.is_property:
            lines.append(f"{indent_str}@property")
        elif self.is_classmethod:
            lines.append(f"{indent_str}@classmethod")
        elif self.is_staticmethod:
            lines.append(f"{indent_str}@staticmethod")
        elif self.is_abstract:
            lines.append(f"{indent_str}@abstractmethod")
        
        # Method signature
        params_str = ", ".join(
            f"{name}: {type_}" for name, type_ in self.params
        )
        
        if not self.is_staticmethod:
            if self.is_classmethod:
                params_str = f"cls, {params_str}" if params_str else "cls"
            else:
                params_str = f"self, {params_str}" if params_str else "self"
        
        async_prefix = "async " if self.is_async else ""
        lines.append(
            f"{indent_str}{async_prefix}def {self.name}({params_str}) -> {self.return_type}:"
        )
        
        # Docstring
        if self.docstring:
            lines.append(f'{indent_str}{DEFAULT_INDENT}"""{self.docstring}"""')
        
        # Body
        if self.body:
            for line in self.body:
                lines.append(f"{indent_str}{DEFAULT_INDENT}{line}")
        elif self.is_abstract:
            lines.append(f"{indent_str}{DEFAULT_INDENT}...")
        else:
            lines.append(f"{indent_str}{DEFAULT_INDENT}pass")
        
        return lines


class TypeSafeGenerator:
    """Generates type-safe Python code."""
    
    def __init__(self) -> None:
        """Initialize generator."""
        self.imports = ImportManager()
    
    def generate_dataclass(
        self,
        name: str,
        fields: List[FieldDefinition],
        methods: Optional[List[MethodDefinition]] = None,
        docstring: Optional[str] = None,
        frozen: bool = False,
        eq: bool = True,
        order: bool = False,
    ) -> str:
        """Generate a type-safe dataclass.
        
        Args:
            name: Class name.
            fields: Field definitions.
            methods: Method definitions.
            docstring: Class docstring.
            frozen: Whether dataclass is frozen.
            eq: Whether to generate __eq__.
            order: Whether to generate ordering methods.
            
        Returns:
            Generated code.
        """
        self.imports.add_standard(
            "from dataclasses import dataclass, field",
            "from datetime import datetime"
        )
        
        # Determine required typing imports
        for field_def in fields:
            if field_def.type_annotation.optional:
                self.imports.add_typing("Optional")
            
            base = field_def.type_annotation.base_type
            if base in ["List", "Dict", "Set", "Tuple"]:
                self.imports.add_typing(base)
            
            if "Any" in str(field_def.type_annotation.generic_args):
                self.imports.add_typing("Any")
        
        lines: List[str] = []
        
        # Imports
        lines.append(self.imports.generate())
        
        # Dataclass decorator
        decorator_args = []
        if frozen:
            decorator_args.append("frozen=True")
        if not eq:
            decorator_args.append("eq=False")
        if order:
            decorator_args.append("order=True")
        
        if decorator_args:
            decorator = f"@dataclass({', '.join(decorator_args)})"
        else:
            decorator = "@dataclass"
        
        lines.append(decorator)
        lines.append(f"class {name}:")
        
        # Docstring
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append("")
        
        # Required fields first, then optional, then collections
        required_fields = [f for f in fields if f.is_required]
        optional_fields = [f for f in fields if not f.is_required and not f.is_factory]
        factory_fields = [f for f in fields if f.is_factory]
        
        # Add fields
        if required_fields:
            lines.append("    # Required fields")
            for field_def in required_fields:
                lines.append(f"    {field_def.render_dataclass()}")
            lines.append("")
        
        if optional_fields:
            lines.append("    # Optional fields")
            for field_def in optional_fields:
                lines.append(f"    {field_def.render_dataclass()}")
            lines.append("")
        
        if factory_fields:
            lines.append("    # Collection fields")
            for field_def in factory_fields:
                lines.append(f"    {field_def.render_dataclass()}")
            lines.append("")
        
        # Add __post_init__ if we have validators
        validators = [f for f in fields if f.validator]
        if validators:
            lines.append("    def __post_init__(self) -> None:")
            lines.append('        """Validate after initialization."""')
            for field_def in validators:
                if field_def.validator:
                    lines.append(f"        {field_def.validator}")
            lines.append("")
        
        # Add methods
        if methods:
            for method in methods:
                lines.extend(method.render())
                lines.append("")
        
        # Format with black if available
        code = "\n".join(lines)
        if HAS_BLACK and black is not None:
            try:
                code = black.format_str(code, mode=black.Mode())
            except Exception:
                pass  # Return unformatted if black fails
        
        return code
    
    def generate_enum(
        self,
        name: str,
        values: List[str],
        docstring: Optional[str] = None,
        use_auto: bool = True,
    ) -> str:
        """Generate type-safe enum.
        
        Args:
            name: Enum class name.
            values: Enum values.
            docstring: Enum docstring.
            use_auto: Use auto() for values.
            
        Returns:
            Generated code.
        """
        self.imports.add_standard("from enum import Enum, auto")
        
        lines: List[str] = [
            self.imports.generate(),
            "",
            f"class {name}(Enum):",
        ]
        
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append("")
        
        for value in values:
            if use_auto:
                lines.append(f"    {value.upper()} = auto()")
            else:
                lines.append(f'    {value.upper()} = "{value.lower()}"')
        
        return "\n".join(lines)
    
    def generate_protocol(
        self,
        name: str,
        methods: List[MethodDefinition],
        docstring: Optional[str] = None,
    ) -> str:
        """Generate type-safe protocol.
        
        Args:
            name: Protocol class name.
            methods: Protocol methods.
            docstring: Protocol docstring.
            
        Returns:
            Generated code.
        """
        self.imports.add_typing("Protocol")
        
        lines: List[str] = [
            self.imports.generate(),
            "",
            f"class {name}(Protocol):",
        ]
        
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append("")
        
        for method in methods:
            # Protocol methods should have ... as body
            method.body = ["..."]
            lines.extend(method.render())
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_exception(
        self,
        name: str,
        base: str = "Exception",
        attributes: Optional[List[FieldDefinition]] = None,
        docstring: Optional[str] = None,
    ) -> str:
        """Generate type-safe exception class.
        
        Args:
            name: Exception class name.
            base: Base exception class.
            attributes: Exception attributes.
            docstring: Exception docstring.
            
        Returns:
            Generated code.
        """
        self.imports.add_typing("Optional", "Any")
        
        lines: List[str] = [
            self.imports.generate(),
            "",
            f"class {name}({base}):",
        ]
        
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append("")
        
        # Constructor
        if attributes:
            params = ["self", "message: str"]
            for attr in attributes:
                type_str = attr.type_annotation.render()
                if attr.default:
                    params.append(f"{attr.name}: {type_str} = {attr.default}")
                else:
                    params.append(f"{attr.name}: {type_str}")
            
            lines.append(f"    def __init__({', '.join(params)}) -> None:")
            lines.append('        """Initialize exception."""')
            lines.append("        super().__init__(message)")
            lines.append("        self.message = message")
            
            for attr in attributes:
                lines.append(f"        self.{attr.name} = {attr.name}")
        else:
            lines.append("    pass")
        
        return "\n".join(lines)
    
    def generate_test_class(
        self,
        name: str,
        test_methods: List[MethodDefinition],
        fixtures: Optional[List[MethodDefinition]] = None,
        docstring: Optional[str] = None,
    ) -> str:
        """Generate type-safe test class.
        
        Args:
            name: Test class name.
            test_methods: Test methods.
            fixtures: Fixture methods.
            docstring: Test class docstring.
            
        Returns:
            Generated code.
        """
        self.imports.add_standard(
            "import pytest",
            "from unittest.mock import Mock, MagicMock, patch",
        )
        self.imports.add_typing("Any", "Optional", "List", "Dict")
        
        lines: List[str] = [
            self.imports.generate(),
            "",
            f"class {name}:",
        ]
        
        if docstring:
            lines.append(f'    """{docstring}"""')
            lines.append("")
        
        # Add fixtures
        if fixtures:
            for fixture in fixtures:
                lines.append("    @pytest.fixture")
                lines.extend(fixture.render()[1:])  # Skip decorator we just added
                lines.append("")
        
        # Add test methods
        for method in test_methods:
            if method.name.startswith("test_"):
                lines.extend(method.render())
            else:
                # Add test prefix if missing
                method.name = f"test_{method.name}"
                lines.extend(method.render())
            lines.append("")
        
        return "\n".join(lines)


def create_example_dataclass() -> str:
    """Create example dataclass with full type safety."""
    generator = TypeSafeGenerator()
    
    # Define fields
    fields = [
        FieldDefinition(
            name="id",
            type_annotation=TypeAnnotation("str"),
            is_required=True,
        ),
        FieldDefinition(
            name="name",
            type_annotation=TypeAnnotation("str"),
            is_required=True,
            validator="if not self.name: raise ValueError('Name cannot be empty')",
        ),
        FieldDefinition(
            name="priority",
            type_annotation=TypeAnnotation("int"),
            default="1",
        ),
        FieldDefinition(
            name="description",
            type_annotation=TypeAnnotation("str", optional=True),
        ),
        FieldDefinition(
            name="tags",
            type_annotation=TypeAnnotation("List", generic_args=["str"]),
            is_factory=True,
            default="list",
        ),
        FieldDefinition(
            name="metadata",
            type_annotation=TypeAnnotation("Dict", generic_args=["str", "Any"]),
            is_factory=True,
            default="dict",
        ),
        FieldDefinition(
            name="created_at",
            type_annotation=TypeAnnotation("datetime"),
            is_factory=True,
            default="datetime.now",
        ),
    ]
    
    # Define methods
    methods = [
        MethodDefinition(
            name="is_high_priority",
            params=[],
            return_type="bool",
            body=["return self.priority >= 5"],
            docstring="Check if task is high priority.",
        ),
        MethodDefinition(
            name="add_tag",
            params=[("tag", "str")],
            return_type="None",
            body=[
                "if tag not in self.tags:",
                "    self.tags.append(tag)",
            ],
            docstring="Add a tag to the task.",
        ),
        MethodDefinition(
            name="to_dict",
            params=[],
            return_type="Dict[str, Any]",
            body=[
                "return {",
                '    "id": self.id,',
                '    "name": self.name,',
                '    "priority": self.priority,',
                '    "description": self.description,',
                '    "tags": self.tags,',
                '    "metadata": self.metadata,',
                '    "created_at": self.created_at.isoformat(),',
                "}",
            ],
            docstring="Convert to dictionary.",
        ),
    ]
    
    return generator.generate_dataclass(
        name="Task",
        fields=fields,
        methods=methods,
        docstring="Task with full type safety.",
    )


def main() -> None:
    """Main function demonstrating usage."""
    # Generate example dataclass
    print("=== Generated Dataclass ===")
    print(create_example_dataclass())
    print()
    
    # Generate example enum
    generator = TypeSafeGenerator()
    print("=== Generated Enum ===")
    print(generator.generate_enum(
        name="TaskStatus",
        values=["pending", "running", "completed", "failed"],
        docstring="Task status enumeration.",
    ))
    print()
    
    # Generate example protocol
    generator = TypeSafeGenerator()
    methods = [
        MethodDefinition(
            name="process",
            params=[("item", "Any")],
            return_type="bool",
            body=[],
            docstring="Process an item.",
        ),
        MethodDefinition(
            name="validate",
            params=[("data", "Dict[str, Any]")],
            return_type="bool",
            body=[],
            docstring="Validate data.",
        ),
    ]
    print("=== Generated Protocol ===")
    print(generator.generate_protocol(
        name="Processor",
        methods=methods,
        docstring="Processor protocol.",
    ))


if __name__ == "__main__":
    main()