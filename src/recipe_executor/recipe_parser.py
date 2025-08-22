"""Recipe parser for reading and parsing recipe files."""

import json
import re
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Optional

from .recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    RecipeMetadata,
    Requirement,
    RequirementPriority,
    ComponentDesign,
    Interface,
    ComponentType,
)


class RecipeParseError(Exception):
    """Raised when recipe parsing fails."""

    pass


class RecipeParser:
    """Parses recipe files into structured models."""

    def __init__(self):
        self.requirement_pattern = re.compile(r"^[\-\*]\s+MUST\s+(.+)$", re.MULTILINE)
        self.should_pattern = re.compile(r"^[\-\*]\s+SHOULD\s+(.+)$", re.MULTILINE)
        self.could_pattern = re.compile(r"^[\-\*]\s+COULD\s+(.+)$", re.MULTILINE)
        self.code_block_pattern = re.compile(r"```(?:python|py)?\n(.*?)\n```", re.DOTALL)

    def parse_recipe(self, recipe_path: Path) -> Recipe:
        """Parse a complete recipe from directory."""
        if not recipe_path.exists():
            raise RecipeParseError(f"Recipe path does not exist: {recipe_path}")

        # Parse individual files
        requirements_path = recipe_path / "requirements.md"
        design_path = recipe_path / "design.md"
        components_path = recipe_path / "components.json"

        # Check all required files exist
        for path in [requirements_path, design_path, components_path]:
            if not path.exists():
                raise RecipeParseError(f"Required recipe file missing: {path}")

        # Parse each component
        requirements = self._parse_requirements(requirements_path)
        design = self._parse_design(design_path)
        components = self._parse_components(components_path)

        # Load supplementary documentation files if they exist
        supplementary_docs = self._load_supplementary_docs(recipe_path)

        # Create metadata including supplementary docs
        metadata = self._create_metadata(recipe_path)
        metadata.supplementary_docs = supplementary_docs

        # Extract recipe name from path or components
        recipe_name = components.name or recipe_path.name

        return Recipe(
            name=recipe_name,
            path=recipe_path,
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata,
        )

    def _parse_requirements(self, path: Path) -> Requirements:
        """Parse requirements.md using markdown parser."""
        content = path.read_text()

        # Extract purpose from first paragraph or header
        purpose = self._extract_purpose(content)

        # Extract functional requirements
        functional_reqs = self._extract_requirements(content, "Functional Requirements")

        # Extract non-functional requirements
        non_functional_reqs = self._extract_requirements(content, "Non-Functional Requirements")

        # Extract success criteria
        success_criteria = self._extract_success_criteria(content)

        return Requirements(
            purpose=purpose,
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            success_criteria=success_criteria,
        )

    def _parse_design(self, path: Path) -> Design:
        """Parse design.md extracting code blocks and architecture."""
        content = path.read_text()

        # Extract architecture overview
        architecture = self._extract_section(content, "Architecture Overview")

        # Extract component designs
        components = self._extract_component_designs(content)

        # Extract interfaces
        interfaces = self._extract_interfaces(content)

        # Extract implementation notes
        implementation_notes = self._extract_section(content, "Implementation")

        # Extract code blocks
        code_blocks = self.code_block_pattern.findall(content)

        return Design(
            architecture=architecture,
            components=components,
            interfaces=interfaces,
            implementation_notes=implementation_notes,
            code_blocks=code_blocks,
        )

    def _parse_components(self, path: Path) -> Components:
        """Parse components.json for dependencies."""
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise RecipeParseError(f"Invalid JSON in components.json: {e}")

        # Parse component type
        type_str = data.get("type", "library")
        try:
            component_type = ComponentType(type_str)
        except ValueError:
            component_type = ComponentType.LIBRARY

        return Components(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            type=component_type,
            dependencies=data.get("dependencies", []),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def _extract_purpose(self, content: str) -> str:
        """Extract purpose from requirements content."""
        # Look for "Purpose" or "Core Purpose" section
        purpose_match = re.search(
            r"##?\s*(?:Core\s+)?Purpose\s*\n(.*?)(?:\n##|\Z)", content, re.DOTALL
        )
        if purpose_match:
            return purpose_match.group(1).strip()

        # Fallback to first paragraph
        lines = content.split("\n")
        for line in lines:
            if line.strip() and not line.startswith("#"):
                return line.strip()

        return "No purpose specified"

    def _extract_requirements(self, content: str, section_name: str) -> list[Requirement]:
        """Extract requirements from a specific section."""
        requirements: list[Requirement] = []

        # Find the section
        section_pattern = re.compile(rf"##?\s*{section_name}.*?\n(.*?)(?:\n##|\Z)", re.DOTALL)
        section_match = section_pattern.search(content)

        if not section_match:
            return requirements

        section_content = section_match.group(1)

        # Extract MUST requirements
        for match in self.requirement_pattern.finditer(section_content):
            req_text = match.group(1).strip()
            req_id = f"req_{len(requirements) + 1}"
            requirements.append(
                Requirement(id=req_id, description=req_text, priority=RequirementPriority.MUST)
            )

        # Extract SHOULD requirements
        for match in self.should_pattern.finditer(section_content):
            req_text = match.group(1).strip()
            req_id = f"req_{len(requirements) + 1}"
            requirements.append(
                Requirement(id=req_id, description=req_text, priority=RequirementPriority.SHOULD)
            )

        # Extract COULD requirements
        for match in self.could_pattern.finditer(section_content):
            req_text = match.group(1).strip()
            req_id = f"req_{len(requirements) + 1}"
            requirements.append(
                Requirement(id=req_id, description=req_text, priority=RequirementPriority.COULD)
            )

        return requirements

    def _extract_success_criteria(self, content: str) -> list[str]:
        """Extract success criteria from content."""
        criteria: list[str] = []

        # Find Success Criteria section
        section_pattern = re.compile(r"##?\s*Success\s+Criteria.*?\n(.*?)(?:\n##|\Z)", re.DOTALL)
        section_match = section_pattern.search(content)

        if section_match:
            section_content = section_match.group(1)
            # Extract numbered or bulleted items
            item_pattern = re.compile(r"^[\d\-\*\.]+\s+(.+)$", re.MULTILINE)
            for match in item_pattern.finditer(section_content):
                criteria.append(match.group(1).strip())

        return criteria

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content from a named section."""
        pattern = re.compile(rf"##?\s*{section_name}.*?\n(.*?)(?:\n##|\Z)", re.DOTALL)
        match = pattern.search(content)

        if match:
            return match.group(1).strip()

        return ""

    def _extract_component_designs(self, content: str) -> list[ComponentDesign]:
        """Extract component designs from design content."""
        components: list[ComponentDesign] = []

        # Look for component definitions in code blocks or sections
        component_pattern = re.compile(
            r"###?\s*(?:\d+\.\s+)?(\w+(?:\s+\w+)*?)\s*\(`([^`]+)`\)", re.MULTILINE
        )

        for match in component_pattern.finditer(content):
            component_name = match.group(1).strip()
            _file_name = match.group(2).strip()  # Not used currently

            # Find the content after this component header
            start_pos = match.end()
            next_component = component_pattern.search(content, start_pos)
            end_pos = next_component.start() if next_component else len(content)

            component_content = content[start_pos:end_pos]

            # Extract code snippet if present
            code_match = self.code_block_pattern.search(component_content)
            code_snippet = code_match.group(1) if code_match else None

            # Extract class name from code snippet
            class_name = None
            if code_snippet:
                class_match = re.search(r"class\s+(\w+)", code_snippet)
                if class_match:
                    class_name = class_match.group(1)

            components.append(
                ComponentDesign(
                    name=component_name,
                    description=component_content[:200],  # First 200 chars as description
                    class_name=class_name,
                    code_snippet=code_snippet,
                )
            )

        return components

    def _extract_interfaces(self, content: str) -> list[Interface]:
        """Extract interface definitions from design."""
        interfaces: list[Interface] = []

        # Look for interface definitions
        interface_section = self._extract_section(content, "Interfaces")
        if interface_section:
            # Parse interface definitions
            # This is a simplified implementation
            lines = interface_section.split("\n")
            current_interface: Optional[Interface] = None

            for line in lines:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    if current_interface:
                        interfaces.append(current_interface)
                    interface_name = line.strip().lstrip("-*").strip()
                    current_interface = Interface(
                        name=interface_name, description="", methods=[], events=[], data_types=[]
                    )

            if current_interface:
                interfaces.append(current_interface)

        return interfaces

    def _create_metadata(self, recipe_path: Path) -> RecipeMetadata:
        """Create metadata for a recipe."""
        now = datetime.now()

        # Calculate checksum of recipe files
        checksum = self._calculate_recipe_checksum(recipe_path)

        return RecipeMetadata(created_at=now, updated_at=now, checksum=checksum)

    def _calculate_recipe_checksum(self, recipe_path: Path) -> str:
        """Calculate checksum of all recipe files."""
        hasher = hashlib.sha256()

        for file_name in ["requirements.md", "design.md", "components.json"]:
            file_path = recipe_path / file_name
            if file_path.exists():
                hasher.update(file_path.read_bytes())

        return hasher.hexdigest()

    def validate_recipe(self, recipe: Recipe) -> list[str]:
        """Validate a parsed recipe and return list of issues."""
        issues: list[str] = []

        # Check recipe validity
        if not recipe.is_valid():
            issues.append("Recipe is not valid - missing required components")

        # Check for empty requirements
        if not recipe.requirements.get_all_requirements():
            issues.append("No requirements defined")

        # Check for empty design
        if not recipe.design.components:
            issues.append("No components defined in design")

        # Check for circular self-dependency
        if recipe.name in recipe.get_dependencies():
            issues.append(f"Recipe {recipe.name} depends on itself")

        # Check that component type is valid
        if not recipe.components.type:
            issues.append("Component type not specified in components.json")

        return issues

    def _load_supplementary_docs(self, recipe_path: Path) -> dict[str, str]:
        """Load any supplementary documentation files from recipe directory.

        Args:
            recipe_path: Path to recipe directory

        Returns:
            Dictionary mapping filename to content for supplementary docs
        """
        supplementary_docs = {}

        # List of known supplementary doc patterns to look for
        supplementary_patterns = [
            "complete-design.md",
            "execution-flow.md",
            "implementation-notes.md",
            "architecture.md",
            "examples.md",
            "validation.md",
        ]

        for pattern in supplementary_patterns:
            doc_path = recipe_path / pattern
            if doc_path.exists():
                try:
                    content = doc_path.read_text()
                    supplementary_docs[pattern] = content
                except Exception as e:
                    # Log but don't fail if supplementary doc can't be read
                    print(f"Warning: Could not read supplementary doc {doc_path}: {e}")

        # Also load any other .md files that aren't the core files
        core_files = {"requirements.md", "design.md", "README.md"}
        for md_file in recipe_path.glob("*.md"):
            if md_file.name not in core_files and md_file.name not in supplementary_docs:
                try:
                    supplementary_docs[md_file.name] = md_file.read_text()
                except Exception as e:
                    print(f"Warning: Could not read {md_file}: {e}")

        return supplementary_docs
