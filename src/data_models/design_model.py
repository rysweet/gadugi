"""Component architecture specifications with interfaces and dependencies.

This module defines models for system and component design, including interfaces,
dependencies, design patterns, and architectural structures.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo


class InterfaceType(str, Enum):
    """Types of interfaces that components can expose."""

    REST_API = "REST_API"
    GRPC = "GRPC"
    CLI = "CLI"
    PYTHON_API = "PYTHON_API"
    FILE_BASED = "FILE_BASED"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    WEBSOCKET = "WEBSOCKET"
    GRAPHQL = "GRAPHQL"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"


class ComponentType(str, Enum):
    """Types of components in the system (re-exported for convenience)."""

    SERVICE = "SERVICE"
    LIBRARY = "LIBRARY"
    CLI = "CLI"
    AGENT = "AGENT"
    MODULE = "MODULE"


class MethodSignature(BaseModel):
    """Method signature specification for interfaces."""

    name: str = Field(..., description="Method name")
    parameters: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of parameters with name and type"
    )
    return_type: str = Field("None", description="Return type specification")
    description: str = Field("", description="Method description")
    async_method: bool = Field(False, description="Whether the method is async")
    exceptions: List[str] = Field(default_factory=list, description="Exceptions that can be raised")

    def get_signature(self) -> str:
        """Generate a Python-like signature string.

        Returns:
            String representation of the method signature
        """
        params = ", ".join(
            f"{p.get('name', 'param')}: {p.get('type', 'Any')}" for p in self.parameters
        )
        async_prefix = "async " if self.async_method else ""
        return f"{async_prefix}def {self.name}({params}) -> {self.return_type}"

    def __str__(self) -> str:
        """Return a string representation of the method signature."""
        return self.get_signature()

    def __repr__(self) -> str:
        """Return a detailed representation of the method signature."""
        return f"MethodSignature(name='{self.name}', return_type='{self.return_type}')"


class Interface(BaseModel):
    """Interface specification with methods, properties, and events."""

    name: str = Field(..., description="Interface name")
    type: InterfaceType = Field(..., description="Type of interface")
    methods: List[MethodSignature] = Field(
        default_factory=list, description="Methods exposed by the interface"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Properties/attributes of the interface"
    )
    events: List[str] = Field(default_factory=list, description="Events emitted by the interface")
    description: str = Field("", description="Interface description")
    version: str = Field("1.0.0", description="Interface version")
    deprecated: bool = Field(False, description="Whether the interface is deprecated")

    def get_method(self, name: str) -> Optional[MethodSignature]:
        """Find method by name.

        Args:
            name: Name of the method to find

        Returns:
            MethodSignature if found, None otherwise
        """
        for method in self.methods:
            if method.name == name:
                return method
        return None

    def add_method(self, method: MethodSignature) -> None:
        """Add a method to the interface.

        Args:
            method: Method to add
        """
        if not self.get_method(method.name):
            self.methods.append(method)

    def __str__(self) -> str:
        """Return a string representation of the interface."""
        return f"{self.name} ({self.type.value}) with {len(self.methods)} methods"

    def __repr__(self) -> str:
        """Return a detailed representation of the interface."""
        return f"Interface(name='{self.name}', type={self.type}, methods={len(self.methods)})"


class Dependency(BaseModel):
    """Dependency specification for components."""

    name: str = Field(..., description="Dependency name")
    version: str = Field("*", description="Version specification (e.g., '>=1.0.0', '~2.1')")
    type: str = Field("internal", description="Type of dependency (internal/external)")
    optional: bool = Field(False, description="Whether the dependency is optional")
    description: str = Field("", description="Description of why this dependency is needed")
    source: Optional[str] = Field(None, description="Source location (e.g., PyPI, GitHub)")

    def is_external(self) -> bool:
        """Check if this is an external dependency.

        Returns:
            True if dependency type is 'external'
        """
        return self.type == "external"

    def __str__(self) -> str:
        """Return a string representation of the dependency."""
        optional_str = " (optional)" if self.optional else ""
        return f"{self.name}{self.version}{optional_str}"

    def __repr__(self) -> str:
        """Return a detailed representation of the dependency."""
        return f"Dependency(name='{self.name}', version='{self.version}', type='{self.type}')"


class DesignPattern(BaseModel):
    """Design pattern specification."""

    name: str = Field(..., description="Pattern name (e.g., 'Singleton', 'Factory')")
    category: str = Field(..., description="Pattern category (e.g., 'Creational', 'Structural')")
    description: str = Field(..., description="Description of the pattern and its purpose")
    participants: List[str] = Field(
        default_factory=list, description="Components participating in the pattern"
    )
    implementation_notes: str = Field("", description="Notes on how to implement the pattern")

    def __str__(self) -> str:
        """Return a string representation of the design pattern."""
        return f"{self.name} ({self.category})"

    def __repr__(self) -> str:
        """Return a detailed representation of the design pattern."""
        return f"DesignPattern(name='{self.name}', category='{self.category}')"


class ComponentArchitecture(BaseModel):
    """Detailed component design with all relationships."""

    name: str = Field(..., description="Component name")
    type: ComponentType = Field(..., description="Component type")
    description: str = Field(..., description="Component description")
    responsibilities: List[str] = Field(
        default_factory=list, description="List of component responsibilities"
    )
    interfaces: List[Interface] = Field(
        default_factory=list, description="Interfaces exposed by the component"
    )
    dependencies: List[Dependency] = Field(
        default_factory=list, description="Component dependencies"
    )
    patterns: List[DesignPattern] = Field(default_factory=list, description="Design patterns used")
    constraints: List[str] = Field(default_factory=list, description="Design constraints")
    quality_attributes: Dict[str, str] = Field(
        default_factory=dict, description="Quality attributes (e.g., performance, security)"
    )
    implementation_path: str = Field("", description="File system path for implementation")

    def get_external_dependencies(self) -> List[Dependency]:
        """Filter external dependencies.

        Returns:
            List of external dependencies only
        """
        return [dep for dep in self.dependencies if dep.is_external()]

    def get_internal_dependencies(self) -> List[Dependency]:
        """Filter internal dependencies.

        Returns:
            List of internal dependencies only
        """
        return [dep for dep in self.dependencies if not dep.is_external()]

    def to_component_diagram(self) -> str:
        """Generate PlantUML diagram for the component.

        Returns:
            PlantUML string representation of the component
        """
        lines = [
            "@startuml",
            f'package "{self.name}" {{',
            f"  component [{self.name}] as {self.name.replace(' ', '_').replace('-', '_')}",
        ]

        # Add interfaces
        for interface in self.interfaces:
            interface_name = interface.name.replace(" ", "_").replace("-", "_")
            lines.append(f'  interface "{interface.name}" as {interface_name}')
            lines.append(f"  {self.name.replace(' ', '_').replace('-', '_')} -- {interface_name}")

        lines.append("}")

        # Add dependencies
        for dep in self.dependencies:
            dep_name = dep.name.replace(" ", "_").replace("-", "_")
            arrow = "..>" if dep.optional else "-->"
            lines.append(
                f"{self.name.replace(' ', '_').replace('-', '_')} {arrow} {dep_name} : uses"
            )

        lines.append("@enduml")
        return "\n".join(lines)

    def validate_interfaces(self) -> List[str]:
        """Validate interface consistency.

        Returns:
            List of validation issues found
        """
        issues = []
        interface_names = [i.name for i in self.interfaces]
        if len(interface_names) != len(set(interface_names)):
            issues.append("Duplicate interface names found")

        for interface in self.interfaces:
            method_names = [m.name for m in interface.methods]
            if len(method_names) != len(set(method_names)):
                issues.append(f"Duplicate method names in interface {interface.name}")

        return issues

    def __str__(self) -> str:
        """Return a string representation of the component architecture."""
        return (
            f"{self.name} ({self.type.value}) with {len(self.interfaces)} interfaces, "
            f"{len(self.dependencies)} dependencies"
        )

    def __repr__(self) -> str:
        """Return a detailed representation of the component architecture."""
        return f"ComponentArchitecture(name='{self.name}', type={self.type})"


class SystemArchitecture(BaseModel):
    """Overall system architecture with components, layers, and data flow."""

    name: str = Field(..., description="System name")
    description: str = Field(..., description="System description")
    components: List[ComponentArchitecture] = Field(
        default_factory=list, description="All system components"
    )
    layers: Dict[str, List[str]] = Field(
        default_factory=dict, description="System layers and their components"
    )
    data_flow: List[Dict[str, str]] = Field(
        default_factory=list, description="Data flow between components"
    )
    external_systems: List[Dict[str, Any]] = Field(
        default_factory=list, description="External systems and integrations"
    )
    deployment_model: Dict[str, Any] = Field(
        default_factory=dict, description="Deployment architecture"
    )
    patterns: List[DesignPattern] = Field(
        default_factory=list, description="System-level design patterns"
    )

    def get_component(self, name: str) -> Optional[ComponentArchitecture]:
        """Find component by name.

        Args:
            name: Component name to find

        Returns:
            ComponentArchitecture if found, None otherwise
        """
        for component in self.components:
            if component.name == name:
                return component
        return None

    def add_component(self, component: ComponentArchitecture) -> None:
        """Add a component to the system.

        Args:
            component: Component to add
        """
        if not self.get_component(component.name):
            self.components.append(component)

    def get_layer_components(self, layer: str) -> List[str]:
        """Get components in a specific layer.

        Args:
            layer: Layer name

        Returns:
            List of component names in the layer
        """
        return self.layers.get(layer, [])

    def validate_dependencies(self) -> List[str]:
        """Check all dependencies are satisfied.

        Returns:
            List of unsatisfied dependencies
        """
        component_names = {comp.name for comp in self.components}
        unsatisfied = []

        for component in self.components:
            for dep in component.dependencies:
                if dep.type == "internal" and dep.name not in component_names:
                    unsatisfied.append(f"{component.name} depends on missing component: {dep.name}")

        return unsatisfied

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for the system.

        Returns:
            Dictionary mapping component names to their dependencies
        """
        graph: Dict[str, Set[str]] = {}
        for component in self.components:
            graph[component.name] = {
                dep.name for dep in component.dependencies if dep.type == "internal"
            }
        return graph

    def to_system_diagram(self) -> str:
        """Generate PlantUML diagram for the system.

        Returns:
            PlantUML string representation of the system
        """
        lines = ["@startuml", f"title {self.name} - System Architecture", ""]

        # Add layers if defined
        if self.layers:
            for layer, components in self.layers.items():
                lines.append(f'package "{layer}" {{')
                for comp_name in components:
                    comp = self.get_component(comp_name)
                    if comp:
                        lines.append(
                            f"  component [{comp_name}] as {comp_name.replace(' ', '_').replace('-', '_')}"
                        )
                lines.append("}")
                lines.append("")

        # Add components not in layers
        components_in_layers = set()
        for layer_comps in self.layers.values():
            components_in_layers.update(layer_comps)

        for component in self.components:
            if component.name not in components_in_layers:
                lines.append(
                    f"component [{component.name}] as {component.name.replace(' ', '_').replace('-', '_')}"
                )

        # Add dependencies
        for component in self.components:
            comp_alias = component.name.replace(" ", "_").replace("-", "_")
            for dep in component.dependencies:
                if dep.type == "internal":
                    dep_alias = dep.name.replace(" ", "_").replace("-", "_")
                    arrow = "..>" if dep.optional else "-->"
                    lines.append(f"{comp_alias} {arrow} {dep_alias}")

        lines.append("@enduml")
        return "\n".join(lines)

    def __str__(self) -> str:
        """Return a string representation of the system architecture."""
        return f"SystemArchitecture({self.name}) with {len(self.components)} components in {len(self.layers)} layers"

    def __repr__(self) -> str:
        """Return a detailed representation of the system architecture."""
        return f"SystemArchitecture(name='{self.name}', components={len(self.components)})"

    @field_validator("layers")
    @classmethod
    def validate_layers(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate that components in layers don't overlap.

        Args:
            v: Layers dictionary

        Returns:
            Validated layers

        Raises:
            ValueError: If a component appears in multiple layers
        """
        all_components = []
        for layer_components in v.values():
            all_components.extend(layer_components)

        if len(all_components) != len(set(all_components)):
            # Find duplicates
            seen = set()
            duplicates = set()
            for comp in all_components:
                if comp in seen:
                    duplicates.add(comp)
                seen.add(comp)
            raise ValueError(f"Components appear in multiple layers: {duplicates}")

        return v
