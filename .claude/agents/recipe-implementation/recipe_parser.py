"""Recipe parser for extracting specifications from recipe files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import (
    Dependency,
    DesignDecision,
    InterfaceSpec,
    RecipeSpec,
    Requirement,
    RequirementType,
)


class RecipeParser:
    """Parser for recipe files."""
    
    def __init__(self):
        """Initialize recipe parser."""
        self.recipe_spec: Optional[RecipeSpec] = None
    
    def parse_recipe(self, recipe_path: Path) -> RecipeSpec:
        """Parse complete recipe from directory.
        
        Args:
            recipe_path: Path to recipe directory
            
        Returns:
            Complete recipe specification
        """
        if not recipe_path.exists():
            raise ValueError(f"Recipe path does not exist: {recipe_path}")
        
        # Initialize recipe spec
        self.recipe_spec = RecipeSpec(
            name=recipe_path.name,
            version="1.0.0",
            description="",
        )
        
        # Parse requirements.md
        requirements_file = recipe_path / "requirements.md"
        if requirements_file.exists():
            self._parse_requirements(requirements_file)
        
        # Parse design.md
        design_file = recipe_path / "design.md"
        if design_file.exists():
            self._parse_design(design_file)
        
        # Parse dependencies.json
        dependencies_file = recipe_path / "dependencies.json"
        if dependencies_file.exists():
            self._parse_dependencies(dependencies_file)
        
        # Parse interfaces.yaml
        interfaces_file = recipe_path / "interfaces.yaml"
        if interfaces_file.exists():
            self._parse_interfaces(interfaces_file)
        
        # Parse metadata.json
        metadata_file = recipe_path / "metadata.json"
        if metadata_file.exists():
            self._parse_metadata(metadata_file)
        
        return self.recipe_spec
    
    def _parse_requirements(self, file_path: Path) -> None:
        """Parse requirements from markdown file."""
        content = file_path.read_text()
        
        # Extract sections
        sections = self._extract_markdown_sections(content)
        
        # Parse functional requirements
        if "Functional Requirements" in sections:
            self._parse_functional_requirements(sections["Functional Requirements"])
        
        # Parse non-functional requirements
        if "Non-Functional Requirements" in sections:
            self._parse_non_functional_requirements(sections["Non-Functional Requirements"])
        
        # Parse interface requirements
        if "Interface Requirements" in sections:
            self._parse_interface_requirements(sections["Interface Requirements"])
        
        # Parse quality requirements
        if "Quality Requirements" in sections:
            self._parse_quality_requirements(sections["Quality Requirements"])
        
        # Parse constraints
        if "Constraints" in sections:
            self._parse_constraints(sections["Constraints"])
        
        # Parse assumptions
        if "Assumptions" in sections:
            self._parse_assumptions(sections["Assumptions"])
    
    def _parse_functional_requirements(self, content: str) -> None:
        """Parse functional requirements."""
        # Look for subsections
        subsections = self._extract_subsections(content)
        
        req_counter = 1
        for category, text in subsections.items():
            # Extract bullet points as requirements
            requirements = self._extract_bullet_points(text)
            
            for req_text in requirements:
                requirement = Requirement(
                    id=f"FR-{req_counter:03d}",
                    type=RequirementType.FUNCTIONAL,
                    category=category,
                    description=req_text,
                    priority=self._determine_priority(req_text),
                )
                if self.recipe_spec:
                    if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
                req_counter += 1
    
    def _parse_non_functional_requirements(self, content: str) -> None:
        """Parse non-functional requirements."""
        subsections = self._extract_subsections(content)
        
        req_counter = 1
        for category, text in subsections.items():
            requirements = self._extract_bullet_points(text)
            
            for req_text in requirements:
                requirement = Requirement(
                    id=f"NFR-{req_counter:03d}",
                    type=RequirementType.NON_FUNCTIONAL,
                    category=category,
                    description=req_text,
                    priority=self._determine_priority(req_text),
                )
                if self.recipe_spec:
                    if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
                req_counter += 1
    
    def _parse_interface_requirements(self, content: str) -> None:
        """Parse interface requirements."""
        # Look for code blocks with interface definitions
        code_blocks = self._extract_code_blocks(content)
        
        for i, block in enumerate(code_blocks, 1):
            # Parse Python-style interface definitions
            interfaces = self._parse_python_interfaces(block)
            for interface in interfaces:
                if self.recipe_spec:
                    self.recipe_spec.interfaces.append(interface)
            
            # Also create requirements for interfaces
            requirement = Requirement(
                id=f"IR-{i:03d}",
                type=RequirementType.INTERFACE,
                category="Interface",
                description=f"Implement interface: {block[:100]}...",
                priority=3,
            )
            if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
    
    def _parse_quality_requirements(self, content: str) -> None:
        """Parse quality requirements."""
        subsections = self._extract_subsections(content)
        
        quality_reqs = {}
        for category, text in subsections.items():
            requirements = self._extract_bullet_points(text)
            quality_reqs[category.lower().replace(" ", "_")] = requirements
        
        if self.recipe_spec:
            self.recipe_spec.quality_requirements = quality_reqs
        
        # Also create requirement objects
        req_counter = 1
        for category, reqs in quality_reqs.items():
            for req_text in reqs:
                requirement = Requirement(
                    id=f"QR-{req_counter:03d}",
                    type=RequirementType.QUALITY,
                    category=category,
                    description=req_text,
                    priority=2,
                )
                if self.recipe_spec:
                    if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
                req_counter += 1
    
    def _parse_constraints(self, content: str) -> None:
        """Parse constraints."""
        constraints = self._extract_bullet_points(content)
        if self.recipe_spec:
            self.recipe_spec.constraints = constraints
        
        # Create requirement objects
        for i, constraint in enumerate(constraints, 1):
            requirement = Requirement(
                id=f"C-{i:03d}",
                type=RequirementType.CONSTRAINT,
                category="Constraint",
                description=constraint,
                priority=4,
            )
            if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
    
    def _parse_assumptions(self, content: str) -> None:
        """Parse assumptions."""
        assumptions = self._extract_bullet_points(content)
        if self.recipe_spec:
            self.recipe_spec.assumptions = assumptions
        
        # Create requirement objects
        for i, assumption in enumerate(assumptions, 1):
            requirement = Requirement(
                id=f"A-{i:03d}",
                type=RequirementType.ASSUMPTION,
                category="Assumption",
                description=assumption,
                priority=1,
            )
            if self.recipe_spec:
                self.recipe_spec.requirements.append(requirement)
    
    def _parse_design(self, file_path: Path) -> None:
        """Parse design decisions from markdown file."""
        content = file_path.read_text()
        sections = self._extract_markdown_sections(content)
        
        decision_counter = 1
        for section_name, section_content in sections.items():
            if "decision" in section_name.lower() or "architecture" in section_name.lower():
                subsections = self._extract_subsections(section_content)
                
                for category, text in subsections.items():
                    # Extract design decisions
                    decisions = self._extract_design_decisions(text)
                    
                    for decision_text, rationale in decisions:
                        design_decision = DesignDecision(
                            id=f"DD-{decision_counter:03d}",
                            category=category,
                            decision=decision_text,
                            rationale=rationale,
                        )
                        if self.recipe_spec:
                            self.recipe_spec.design_decisions.append(design_decision)
                        decision_counter += 1
    
    def _parse_dependencies(self, file_path: Path) -> None:
        """Parse dependencies from JSON file."""
        try:
            data = json.loads(file_path.read_text())
            
            # Parse different dependency types
            for dep_type in ["libraries", "services", "components"]:
                if dep_type in data:
                    for name, info in data[dep_type].items():
                        dependency = Dependency(
                            name=name,
                            version=info.get("version"),
                            type=dep_type.rstrip("s"),  # Remove plural 's'
                            required=info.get("required", True),
                            alternatives=info.get("alternatives", []),
                        )
                        if self.recipe_spec:
                            self.recipe_spec.dependencies.append(dependency)
        
        except json.JSONDecodeError as e:
            print(f"Error parsing dependencies.json: {e}")
    
    def _parse_interfaces(self, file_path: Path) -> None:
        """Parse interfaces from YAML file."""
        try:
            data = yaml.safe_load(file_path.read_text())
            
            if "interfaces" in data:
                for interface_data in data["interfaces"]:
                    interface = InterfaceSpec(
                        name=interface_data.get("name", ""),
                        type=interface_data.get("type", "function"),
                        description=interface_data.get("description", ""),
                        signature=interface_data.get("signature"),
                        parameters=interface_data.get("parameters", []),
                        returns=interface_data.get("returns"),
                        exceptions=interface_data.get("exceptions", []),
                        examples=interface_data.get("examples", []),
                    )
                    if self.recipe_spec:
                        self.recipe_spec.interfaces.append(interface)
        
        except yaml.YAMLError as e:
            print(f"Error parsing interfaces.yaml: {e}")
    
    def _parse_metadata(self, file_path: Path) -> None:
        """Parse metadata from JSON file."""
        try:
            data = json.loads(file_path.read_text())
            
            if self.recipe_spec:
                self.recipe_spec.name = data.get("name", self.recipe_spec.name)
                self.recipe_spec.version = data.get("version", self.recipe_spec.version)
                self.recipe_spec.description = data.get("description", self.recipe_spec.description)
                self.recipe_spec.metadata = data.get("metadata", {})
        
        except json.JSONDecodeError as e:
            print(f"Error parsing metadata.json: {e}")
    
    def _parse_python_interfaces(self, code: str) -> List[InterfaceSpec]:
        """Parse Python interface definitions from code block."""
        interfaces = []
        
        # Simple regex patterns for Python interfaces
        class_pattern = r"class\s+(\w+).*?:"
        method_pattern = r"(?:async\s+)?def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*(.+?))?:"
        
        # Find classes
        for match in re.finditer(class_pattern, code):
            class_name = match.group(1)
            interfaces.append(InterfaceSpec(
                name=class_name,
                type="class",
                description=f"Class {class_name}",
            ))
        
        # Find functions/methods
        for match in re.finditer(method_pattern, code):
            func_name = match.group(1)
            params = match.group(2)
            returns = match.group(3)
            
            # Parse parameters
            param_list = []
            if params and params.strip() != "self":
                for param in params.split(","):
                    param = param.strip()
                    if param and param != "self":
                        param_parts = param.split(":")
                        param_name = param_parts[0].strip()
                        param_type = param_parts[1].strip() if len(param_parts) > 1 else "Any"
                        param_list.append({"name": param_name, "type": param_type})
            
            interfaces.append(InterfaceSpec(
                name=func_name,
                type="function",
                description=f"Function {func_name}",
                parameters=param_list,
                returns={"type": returns} if returns else None,
            ))
        
        return interfaces
    
    # Helper methods
    
    def _extract_markdown_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def _extract_subsections(self, content: str) -> Dict[str, str]:
        """Extract subsections from content."""
        subsections = {}
        current_subsection = "General"
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("### "):
                if current_content:
                    subsections[current_subsection] = "\n".join(current_content)
                current_subsection = line[4:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            subsections[current_subsection] = "\n".join(current_content)
        
        return subsections
    
    def _extract_bullet_points(self, content: str) -> List[str]:
        """Extract bullet points from content."""
        points = []
        current_point = []
        
        for line in content.split("\n"):
            if line.strip().startswith("- "):
                if current_point:
                    points.append(" ".join(current_point))
                current_point = [line[2:].strip()]
            elif line.strip() and current_point:
                # Continuation of previous point
                current_point.append(line.strip())
            elif not line.strip() and current_point:
                # End of point
                points.append(" ".join(current_point))
                current_point = []
        
        if current_point:
            points.append(" ".join(current_point))
        
        return points
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from markdown."""
        code_blocks = []
        in_code_block = False
        current_block = []
        
        for line in content.split("\n"):
            if line.strip().startswith("```"):
                if in_code_block:
                    code_blocks.append("\n".join(current_block))
                    current_block = []
                in_code_block = not in_code_block
            elif in_code_block:
                current_block.append(line)
        
        return code_blocks
    
    def _extract_design_decisions(self, content: str) -> List[tuple[str, str]]:
        """Extract design decisions and rationales."""
        decisions = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if "decision:" in line.lower() or "choice:" in line.lower():
                decision = line.split(":", 1)[1].strip() if ":" in line else line
                
                # Look for rationale in next lines
                rationale = ""
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if "rationale:" in next_line.lower() or "because" in next_line.lower():
                        rationale = next_line.split(":", 1)[1].strip() if ":" in next_line else next_line
                
                decisions.append((decision, rationale))
        
        return decisions
    
    def _determine_priority(self, text: str) -> int:
        """Determine requirement priority from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["must", "critical", "required"]):
            return 5
        elif any(word in text_lower for word in ["should", "important"]):
            return 4
        elif any(word in text_lower for word in ["could", "nice"]):
            return 2
        else:
            return 3  # Default priority