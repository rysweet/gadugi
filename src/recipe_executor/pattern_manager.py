"""Design Pattern management for Recipe Executor."""

from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import json
from datetime import datetime

from .recipe_model import Requirements, Design, Recipe, Requirement, RequirementPriority
from .recipe_parser import RecipeParser


@dataclass
class DesignPattern:
    """Represents a reusable design pattern."""

    name: str
    description: str
    version: str
    requirements: Requirements
    design: Design
    templates: Dict[str, str] = field(default_factory=lambda: {})  # filepath -> content
    depends_on: List[str] = field(default_factory=lambda: [])  # Other patterns this depends on
    metadata: Dict[str, Any] = field(default_factory=lambda: {})

    def applies_to(self, recipe: Recipe) -> bool:
        """Check if this pattern should be applied to a recipe.

        Args:
            recipe: The recipe to check

        Returns:
            True if this pattern applies to the recipe
        """
        # Check if recipe explicitly requests this pattern
        if "patterns" in recipe.components.metadata:
            return self.name in recipe.components.metadata["patterns"]

        # Check if recipe type matches pattern targets
        if "target_types" in self.metadata:
            return recipe.components.type.value in self.metadata["target_types"]

        return False


@dataclass
class PatternConfig:
    """Configuration for a design pattern from pattern.json."""

    name: str
    version: str
    description: str
    depends_on: List[str] = field(default_factory=lambda: [])
    target_types: List[str] = field(default_factory=lambda: [])
    auto_apply: bool = False
    metadata: Dict[str, Any] = field(default_factory=lambda: {})


class PatternManager:
    """Manages design patterns for recipe execution."""

    def __init__(self, patterns_root: Optional[Path] = None):
        """Initialize pattern manager.

        Args:
            patterns_root: Root directory for patterns (default: patterns/)
        """
        self.patterns_root = patterns_root or Path("patterns")
        self.parser = RecipeParser()
        self._pattern_cache: Dict[str, DesignPattern] = {}

    def load_pattern(self, pattern_name: str) -> Optional[DesignPattern]:
        """Load a design pattern by name.

        Args:
            pattern_name: Name of the pattern to load

        Returns:
            DesignPattern object or None if not found
        """
        # Check cache first
        if pattern_name in self._pattern_cache:
            return self._pattern_cache[pattern_name]

        pattern_dir = self.patterns_root / pattern_name
        if not pattern_dir.exists():
            return None

        # Load pattern.json
        config_path = pattern_dir / "pattern.json"
        if not config_path.exists():
            return None

        try:
            with open(config_path) as f:
                config_data = json.load(f)

            config = PatternConfig(
                name=config_data["name"],
                version=config_data.get("version", "1.0.0"),
                description=config_data.get("description", ""),
                depends_on=config_data.get("depends_on", []),
                target_types=config_data.get("target_types", []),
                auto_apply=config_data.get("auto_apply", False),
                metadata=config_data.get("metadata", {}),
            )

            # Load requirements and design
            requirements = self._load_pattern_requirements(pattern_dir)
            design = self._load_pattern_design(pattern_dir)

            # Load templates if they exist
            templates = self._load_pattern_templates(pattern_dir)

            # Create pattern object
            pattern = DesignPattern(
                name=config.name,
                description=config.description,
                version=config.version,
                requirements=requirements,
                design=design,
                templates=templates,
                depends_on=config.depends_on,
                metadata={
                    "target_types": config.target_types,
                    "auto_apply": config.auto_apply,
                    **config.metadata,
                },
            )

            # Cache it
            self._pattern_cache[pattern_name] = pattern

            return pattern

        except Exception as e:
            print(f"Error loading pattern {pattern_name}: {e}")
            return None

    def get_patterns_for_recipe(self, recipe: Recipe) -> List[DesignPattern]:
        """Get all patterns that should be applied to a recipe.

        Args:
            recipe: The recipe to get patterns for

        Returns:
            List of applicable design patterns
        """
        patterns: List[DesignPattern] = []

        # Check for explicitly requested patterns
        if "patterns" in recipe.components.metadata:
            for pattern_name in recipe.components.metadata["patterns"]:
                pattern = self.load_pattern(pattern_name)
                if pattern:
                    patterns.append(pattern)

        # Check for auto-apply patterns
        for pattern_dir in self.patterns_root.glob("*/"):
            if pattern_dir.is_dir():
                pattern = self.load_pattern(pattern_dir.name)
                if pattern and pattern.metadata.get("auto_apply"):
                    if pattern.applies_to(recipe):
                        if pattern not in patterns:
                            patterns.append(pattern)

        # Resolve pattern dependencies
        patterns = self._resolve_pattern_dependencies(patterns)

        return patterns

    def apply_patterns_to_recipe(self, recipe: Recipe, patterns: List[DesignPattern]) -> Recipe:
        """Apply design patterns to a recipe.

        This merges pattern requirements and design into the recipe.

        Args:
            recipe: The recipe to enhance
            patterns: Patterns to apply

        Returns:
            Enhanced recipe with patterns applied
        """
        # Start with original recipe
        enhanced = recipe

        # Apply each pattern in order
        for pattern in patterns:
            # Merge requirements
            enhanced = self._merge_requirements(enhanced, pattern.requirements)

            # Merge design
            enhanced = self._merge_design(enhanced, pattern.design)

            # Add pattern metadata
            if "applied_patterns" not in enhanced.components.metadata:
                enhanced.components.metadata["applied_patterns"] = []

            # Type assertion for pyright
            applied_patterns = enhanced.components.metadata.get("applied_patterns", [])
            if isinstance(applied_patterns, list):
                applied_patterns.append(
                    {  # type: ignore[reportUnknownMemberType]
                        "name": pattern.name,
                        "version": pattern.version,
                        "applied_at": datetime.now().isoformat(),
                    }
                )
                enhanced.components.metadata["applied_patterns"] = applied_patterns

        return enhanced

    def get_pattern_templates(self, patterns: List[DesignPattern]) -> Dict[str, str]:
        """Get all template files from patterns.

        Args:
            patterns: List of patterns to get templates from

        Returns:
            Combined dictionary of filepath -> content
        """
        all_templates: Dict[str, str] = {}

        for pattern in patterns:
            for filepath, content in pattern.templates.items():
                # Handle conflicts by prefixing with pattern name
                if filepath in all_templates:
                    filepath = f"{pattern.name}/{filepath}"
                all_templates[filepath] = content

        return all_templates

    def _load_pattern_requirements(self, pattern_dir: Path) -> Requirements:
        """Load requirements from a pattern directory."""
        req_path = pattern_dir / "requirements.md"
        if req_path.exists():
            # Parse requirements similar to recipe parsing
            # We need to call the public parse_recipe method with a fake recipe dir
            # or extract the parsing logic. For now, create a simple parser.
            content = req_path.read_text()
            return self._parse_pattern_requirements(content)

        # Return empty requirements if not found
        return Requirements(
            purpose="",
            functional_requirements=[],
            non_functional_requirements=[],
            success_criteria=[],
        )

    def _parse_pattern_requirements(self, content: str) -> Requirements:
        """Parse requirements from markdown content."""
        # Simple parsing - in production would be more robust
        lines = content.split("\n")
        purpose = ""
        functional_reqs: List[Requirement] = []
        non_functional_reqs: List[Requirement] = []
        success_criteria: List[str] = []

        current_section = ""
        req_counter = 0
        for line in lines:
            if line.startswith("## Purpose"):
                current_section = "purpose"
            elif line.startswith("## Functional Requirements"):
                current_section = "functional"
            elif line.startswith("## Non-Functional Requirements"):
                current_section = "non-functional"
            elif line.startswith("## Success Criteria"):
                current_section = "success"
            elif line.strip() and not line.startswith("#"):
                if current_section == "purpose" and not purpose:
                    purpose = line.strip()
                elif current_section == "functional" and line.startswith("-"):
                    req_counter += 1
                    functional_reqs.append(
                        Requirement(
                            id=f"pattern-fr-{req_counter}",
                            description=line[1:].strip(),
                            priority=RequirementPriority.SHOULD,
                            validation_criteria=[],
                            implemented=False,
                        )
                    )
                elif current_section == "non-functional" and line.startswith("-"):
                    req_counter += 1
                    non_functional_reqs.append(
                        Requirement(
                            id=f"pattern-nfr-{req_counter}",
                            description=line[1:].strip(),
                            priority=RequirementPriority.SHOULD,
                            validation_criteria=[],
                            implemented=False,
                        )
                    )
                elif current_section == "success" and line.startswith("-"):
                    success_criteria.append(line[1:].strip())

        return Requirements(
            purpose=purpose,
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            success_criteria=success_criteria,
        )

    def _load_pattern_design(self, pattern_dir: Path) -> Design:
        """Load design from a pattern directory."""
        design_path = pattern_dir / "design.md"
        if design_path.exists():
            content = design_path.read_text()
            return self._parse_pattern_design(content)

        # Return empty design if not found
        return Design(architecture="", components=[], interfaces=[], implementation_notes="")

    def _parse_pattern_design(self, content: str) -> Design:
        """Parse design from markdown content."""
        lines = content.split("\n")
        architecture = ""
        components: List[Any] = []
        implementation_notes = ""
        code_blocks: List[str] = []

        current_section = ""
        in_code_block = False
        current_code: List[str] = []

        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    # End of code block
                    if current_code:
                        code_blocks.append("\n".join(current_code))
                        current_code = []
                    in_code_block = False
                else:
                    in_code_block = True
            elif in_code_block:
                current_code.append(line)
            elif line.startswith("## Architecture"):
                current_section = "architecture"
            elif line.startswith("## Implementation Notes"):
                current_section = "implementation"
            elif line.strip() and not line.startswith("#"):
                if current_section == "architecture" and not architecture:
                    architecture = line.strip()
                elif current_section == "implementation":
                    if implementation_notes:
                        implementation_notes += "\n" + line.strip()
                    else:
                        implementation_notes = line.strip()

        return Design(
            architecture=architecture,
            components=components,
            interfaces=[],
            implementation_notes=implementation_notes,
            code_blocks=code_blocks,
        )

    def _load_pattern_templates(self, pattern_dir: Path) -> Dict[str, str]:
        """Load template files from a pattern directory."""
        templates: Dict[str, str] = {}
        templates_dir = pattern_dir / "templates"

        if templates_dir.exists():
            for template_file in templates_dir.rglob("*"):
                if template_file.is_file():
                    # Get relative path from templates dir
                    rel_path = template_file.relative_to(templates_dir)
                    templates[str(rel_path)] = template_file.read_text()

        return templates

    def _resolve_pattern_dependencies(self, patterns: List[DesignPattern]) -> List[DesignPattern]:
        """Resolve dependencies between patterns.

        Args:
            patterns: Initial list of patterns

        Returns:
            Complete list with all dependencies resolved
        """
        resolved: List[DesignPattern] = []
        seen: set[str] = set()

        def add_with_deps(pattern: DesignPattern) -> None:
            if pattern.name in seen:
                return

            seen.add(pattern.name)

            # Add dependencies first
            for dep_name in pattern.depends_on:
                dep_pattern = self.load_pattern(dep_name)
                if dep_pattern:
                    add_with_deps(dep_pattern)

            # Then add this pattern
            resolved.append(pattern)

        for pattern in patterns:
            add_with_deps(pattern)

        return resolved

    def _merge_requirements(self, recipe: Recipe, pattern_reqs: Requirements) -> Recipe:
        """Merge pattern requirements into recipe requirements."""
        # Add pattern's functional requirements
        recipe.requirements.functional_requirements.extend(pattern_reqs.functional_requirements)

        # Add pattern's non-functional requirements
        recipe.requirements.non_functional_requirements.extend(
            pattern_reqs.non_functional_requirements
        )

        # Add pattern's success criteria
        recipe.requirements.success_criteria.extend(pattern_reqs.success_criteria)

        return recipe

    def _merge_design(self, recipe: Recipe, pattern_design: Design) -> Recipe:
        """Merge pattern design into recipe design."""
        # Merge architecture notes
        if pattern_design.architecture:
            if recipe.design.architecture:
                recipe.design.architecture += f"\n\n{pattern_design.architecture}"
            else:
                recipe.design.architecture = pattern_design.architecture

        # Add pattern components
        recipe.design.components.extend(pattern_design.components)

        # Add pattern interfaces
        recipe.design.interfaces.extend(pattern_design.interfaces)

        # Merge implementation notes
        if pattern_design.implementation_notes:
            if recipe.design.implementation_notes:
                recipe.design.implementation_notes += f"\n\n{pattern_design.implementation_notes}"
            else:
                recipe.design.implementation_notes = pattern_design.implementation_notes

        # Add code blocks
        if pattern_design.code_blocks:
            recipe.design.code_blocks.extend(pattern_design.code_blocks)

        return recipe
