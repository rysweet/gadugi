"""Recipe parser for extracting structured data from recipe files."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .recipe_model import (
    ComponentDesign,
    ComponentType,
    Components,
    Design,
    Interface,
    Recipe,
    RecipeMetadata,
    Requirement,
    RequirementPriority,
    Requirements,
)


class RecipeParseError(Exception):
    """Error parsing recipe files.
    
    Raised when recipe files cannot be parsed due to:
    - Missing required files (requirements.md, design.md, dependencies.json)
    - Invalid file format or structure
    - Malformed YAML/JSON content
    - Missing required sections in recipe files
    """
    
    def __init__(self, message: str, recipe_path: Optional[Path] = None, file_path: Optional[Path] = None):
        """Initialize the parse error with context.
        
        Args:
            message: Error description
            recipe_path: Path to the recipe directory
            file_path: Specific file that caused the error
        """
        self.recipe_path = recipe_path
        self.file_path = file_path
        
        # Build detailed error message
        error_parts = [message]
        if recipe_path:
            error_parts.append(f"Recipe: {recipe_path}")
        if file_path:
            error_parts.append(f"File: {file_path}")
            
        super().__init__(" | ".join(error_parts))
        
    def __str__(self) -> str:
        """Return string representation of the error."""
        return super().__str__()


class RecipeParser:
    """Parses recipe files into structured models."""
    
    def __init__(self):
        """Initialize the parser."""
        self.requirement_pattern = re.compile(
            r'^\s*-\s*(MUST|SHOULD|COULD|WONT)\s+(.+)$',
            re.MULTILINE
        )
        self.success_criteria_pattern = re.compile(
            r'^\s*-\s*\*\*(.+?)\*\*:\s*(.+)$',
            re.MULTILINE
        )
        self.component_pattern = re.compile(
            r'^\s*-\s*\*\*(.+?)\*\*:\s*(.+)$',
            re.MULTILINE
        )
        
    def parse_recipe(self, recipe_path: Path) -> Recipe:
        """Parse a complete recipe from directory.
        
        Args:
            recipe_path: Path to recipe directory
            
        Returns:
            Parsed Recipe object
            
        Raises:
            RecipeParseError: If required files are missing or invalid
        """
        # Validate all required files exist
        self._validate_recipe_structure(recipe_path)
        
        # Parse each component
        requirements = self._parse_requirements(recipe_path / "requirements.md")
        design = self._parse_design(recipe_path / "design.md")
        components = self._parse_components(recipe_path / "components.json")
        
        # Create metadata with checksums for change detection
        metadata = self._create_metadata(recipe_path)
        
        # Create and validate recipe
        recipe = Recipe(
            name=components.name,
            path=recipe_path,
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata
        )
        
        if not recipe.is_valid():
            raise RecipeParseError(f"Invalid recipe structure for {recipe.name}")
        
        return recipe
    
    def _validate_recipe_structure(self, recipe_path: Path):
        """Validate that all required recipe files exist.
        
        Args:
            recipe_path: Path to recipe directory
            
        Raises:
            RecipeParseError: If required files are missing
        """
        required_files = ["requirements.md", "design.md", "components.json"]
        missing_files = []
        
        for file_name in required_files:
            file_path = recipe_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            raise RecipeParseError(
                f"Missing required files in {recipe_path}: {', '.join(missing_files)}"
            )
    
    def _parse_requirements(self, path: Path) -> Requirements:
        """Parse requirements.md using markdown parser.
        
        Args:
            path: Path to requirements.md
            
        Returns:
            Parsed Requirements object
        """
        content = path.read_text()
        
        # Extract purpose from first paragraph after title
        purpose = self._extract_purpose(content)
        
        # Extract structured requirements with priorities
        functional_reqs = self._extract_requirements(content, "Functional Requirements")
        non_functional_reqs = self._extract_requirements(content, "Non-Functional Requirements")
        
        # Extract success criteria
        success_criteria = self._extract_success_criteria(content)
        
        return Requirements(
            purpose=purpose,
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            success_criteria=success_criteria
        )
    
    def _extract_purpose(self, content: str) -> str:
        """Extract the purpose statement from requirements.
        
        Args:
            content: Requirements file content
            
        Returns:
            Purpose statement
        """
        # Look for Purpose or Overview section
        purpose_match = re.search(
            r'##?\s*(?:Purpose|Overview)\s*\n+(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if purpose_match:
            purpose = purpose_match.group(1).strip()
            # Take first paragraph only
            paragraphs = purpose.split('\n\n')
            return paragraphs[0].replace('\n', ' ').strip()
        
        # Fallback: take first non-title paragraph
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if not line.startswith('#') and line.strip():
                # Found first content line
                paragraph = []
                for j in range(i, len(lines)):
                    if not lines[j].strip():
                        break
                    paragraph.append(lines[j])
                return ' '.join(paragraph).strip()
        
        return "No purpose statement found"
    
    def _extract_requirements(self, content: str, section: str) -> List[Requirement]:
        """Extract requirements with MUST/SHOULD/COULD priorities.
        
        Args:
            content: Requirements file content
            section: Section name to extract from
            
        Returns:
            List of parsed requirements
        """
        requirements = []
        
        # Find the section
        section_pattern = re.compile(
            rf'##?\s*{re.escape(section)}\s*\n+(.+?)(?:\n##|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        section_match = section_pattern.search(content)
        
        if not section_match:
            return requirements
        
        section_content = section_match.group(1)
        
        # Extract requirements with priorities
        req_id = 1
        for match in self.requirement_pattern.finditer(section_content):
            priority_str = match.group(1)
            description = match.group(2).strip()
            
            # Extract validation criteria if present (indented under requirement)
            criteria = self._extract_validation_criteria(section_content, match.end())
            
            try:
                priority = RequirementPriority[priority_str]
            except KeyError:
                priority = RequirementPriority.SHOULD
            
            requirements.append(Requirement(
                id=f"{section.lower().replace(' ', '_')}_{req_id}",
                description=description,
                priority=priority,
                validation_criteria=criteria,
                implemented=False
            ))
            req_id += 1
        
        return requirements
    
    def _extract_validation_criteria(self, content: str, start_pos: int) -> List[str]:
        """Extract validation criteria for a requirement.
        
        Args:
            content: Section content
            start_pos: Position after requirement line
            
        Returns:
            List of validation criteria
        """
        criteria = []
        lines = content[start_pos:].split('\n')
        
        for line in lines:
            # Stop at next requirement or section
            if self.requirement_pattern.match(line) or line.startswith('#'):
                break
            
            # Look for indented criteria (starts with spaces/tabs and -)
            criteria_match = re.match(r'^\s{2,}-\s*(.+)$', line)
            if criteria_match:
                criteria.append(criteria_match.group(1).strip())
        
        return criteria
    
    def _extract_success_criteria(self, content: str) -> List[str]:
        """Extract success criteria from requirements.
        
        Args:
            content: Requirements file content
            
        Returns:
            List of success criteria
        """
        criteria = []
        
        # Find Success Criteria section
        section_pattern = re.compile(
            r'##?\s*Success\s+Criteria\s*\n+(.+?)(?:\n##|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        section_match = section_pattern.search(content)
        
        if not section_match:
            return criteria
        
        section_content = section_match.group(1)
        
        # Extract each criterion
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                criterion = line[1:].strip()
                # Remove markdown formatting
                criterion = re.sub(r'\*\*(.+?)\*\*', r'\1', criterion)
                if criterion:
                    criteria.append(criterion)
        
        return criteria
    
    def _parse_design(self, path: Path) -> Design:
        """Parse design.md for architecture and components.
        
        Args:
            path: Path to design.md
            
        Returns:
            Parsed Design object
        """
        content = path.read_text()
        
        # Extract architecture overview
        architecture = self._extract_architecture(content)
        
        # Extract component designs
        components = self._extract_component_designs(content)
        
        # Extract interfaces
        interfaces = self._extract_interfaces(content)
        
        # Extract implementation notes
        implementation_notes = self._extract_implementation_notes(content)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(content)
        
        # Extract target language
        language = self._extract_language(content)
        
        return Design(
            architecture=architecture,
            components=components,
            interfaces=interfaces,
            implementation_notes=implementation_notes,
            code_blocks=code_blocks,
            language=language
        )
    
    def _extract_architecture(self, content: str) -> str:
        """Extract architecture overview from design.
        
        Args:
            content: Design file content
            
        Returns:
            Architecture description
        """
        # Look for Architecture section
        arch_match = re.search(
            r'##?\s*(?:Architecture|Overview)\s*\n+(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if arch_match:
            architecture = arch_match.group(1).strip()
            # Take first paragraph or diagram
            if '```' in architecture:
                # Include the diagram
                diagram_end = architecture.find('```', architecture.find('```') + 3)
                if diagram_end > 0:
                    return architecture[:diagram_end + 3]
            else:
                paragraphs = architecture.split('\n\n')
                return paragraphs[0]
        
        return "No architecture description found"
    
    def _extract_component_designs(self, content: str) -> List[ComponentDesign]:
        """Extract component designs from design document.
        
        Args:
            content: Design file content
            
        Returns:
            List of component designs
        """
        components = []
        
        # Look for Components section
        comp_pattern = re.compile(
            r'##?\s*(?:Components|Classes)\s*\n+(.+?)(?:\n##|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        comp_match = comp_pattern.search(content)
        
        if not comp_match:
            # Try to find component definitions in code blocks
            return self._extract_components_from_code(content)
        
        section_content = comp_match.group(1)
        
        # Parse each component
        component_pattern = re.compile(
            r'-\s*\*\*(.+?)\*\*:\s*(.+?)(?=\n-|\Z)',
            re.DOTALL
        )
        
        for match in component_pattern.finditer(section_content):
            name = match.group(1).strip()
            description = match.group(2).strip()
            
            # Extract class name if present
            class_match = re.search(r'Class:\s*`(.+?)`', description)
            class_name = class_match.group(1) if class_match else name.replace(' ', '')
            
            # Extract methods if listed
            methods = self._extract_methods(description)
            
            # Extract properties if listed
            properties = self._extract_properties(description)
            
            # Extract code snippet if present
            code_snippet = self._extract_code_snippet(description)
            
            components.append(ComponentDesign(
                name=name,
                description=description.split('\n')[0],  # First line only
                class_name=class_name,
                methods=methods,
                properties=properties,
                code_snippet=code_snippet
            ))
        
        return components
    
    def _extract_components_from_code(self, content: str) -> List[ComponentDesign]:
        """Extract components from code blocks as fallback.
        
        Args:
            content: Design file content
            
        Returns:
            List of component designs extracted from code
        """
        components = []
        code_blocks = self._extract_code_blocks(content)
        
        for code in code_blocks:
            # Look for class definitions
            class_matches = re.finditer(
                r'class\s+(\w+).*?:\s*\n\s*"""(.+?)"""',
                code,
                re.DOTALL
            )
            
            for match in class_matches:
                class_name = match.group(1)
                docstring = match.group(2).strip()
                
                # Extract methods from the class
                methods = re.findall(r'def\s+(\w+)\s*\(', code)
                
                components.append(ComponentDesign(
                    name=class_name,
                    description=docstring,
                    class_name=class_name,
                    methods=methods,
                    properties=[],
                    code_snippet=code
                ))
        
        return components
    
    def _extract_methods(self, description: str) -> List[str]:
        """Extract method names from component description.
        
        Args:
            description: Component description
            
        Returns:
            List of method names
        """
        methods = []
        
        # Look for method definitions
        method_pattern = re.compile(r'`(\w+)\s*\([^)]*\)`')
        for match in method_pattern.finditer(description):
            methods.append(match.group(1))
        
        return methods
    
    def _extract_properties(self, description: str) -> List[str]:
        """Extract property names from component description.
        
        Args:
            description: Component description
            
        Returns:
            List of property names
        """
        properties = []
        
        # Look for property definitions
        prop_pattern = re.compile(r'`self\.(\w+)`')
        for match in prop_pattern.finditer(description):
            properties.append(match.group(1))
        
        return properties
    
    def _extract_code_snippet(self, description: str) -> Optional[str]:
        """Extract code snippet from component description.
        
        Args:
            description: Component description
            
        Returns:
            Code snippet if present
        """
        # Look for code block in description
        code_match = re.search(r'```python\n(.+?)```', description, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return None
    
    def _extract_interfaces(self, content: str) -> List[Interface]:
        """Extract interface definitions from design.
        
        Args:
            content: Design file content
            
        Returns:
            List of interfaces
        """
        interfaces = []
        
        # Look for Interfaces section
        interface_pattern = re.compile(
            r'##?\s*Interfaces?\s*\n+(.+?)(?:\n##|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        interface_match = interface_pattern.search(content)
        
        if not interface_match:
            return interfaces
        
        section_content = interface_match.group(1)
        
        # Parse interface definitions
        # Similar to component parsing but for interfaces
        
        return interfaces
    
    def _extract_implementation_notes(self, content: str) -> str:
        """Extract implementation notes from design.
        
        Args:
            content: Design file content
            
        Returns:
            Implementation notes
        """
        # Look for Implementation Notes section
        notes_match = re.search(
            r'##?\s*Implementation\s+Notes?\s*\n+(.+?)(?:\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if notes_match:
            return notes_match.group(1).strip()
        
        return ""
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract all code blocks from content.
        
        Args:
            content: File content
            
        Returns:
            List of code blocks
        """
        code_blocks = []
        
        # Find all fenced code blocks
        code_pattern = re.compile(r'```(?:python|py)?\n(.+?)```', re.DOTALL)
        for match in code_pattern.finditer(content):
            code = match.group(1).strip()
            if code:
                code_blocks.append(code)
        
        return code_blocks
    
    def _extract_language(self, content: str) -> str:
        """Extract target language from design.
        
        Args:
            content: Design file content
            
        Returns:
            Target language (default: python)
        """
        # Look for Language specification
        lang_match = re.search(
            r'##?\s*(?:Target\s+)?Language\s*\n+(.+?)$',
            content,
            re.MULTILINE | re.IGNORECASE
        )
        
        if lang_match:
            language = lang_match.group(1).strip().lower()
            # Clean up language specification
            language = re.sub(r'[^a-z]+', '', language)
            return language
        
        return "python"
    
    def _parse_components(self, path: Path) -> Components:
        """Parse components.json for metadata.
        
        Args:
            path: Path to components.json
            
        Returns:
            Parsed Components object
            
        Raises:
            RecipeParseError: If JSON is invalid
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RecipeParseError(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            raise RecipeParseError(f"Error reading {path}: {e}")
        
        # Extract required fields
        try:
            name = data['name']
            version = data.get('version', '1.0.0')
            type_str = data.get('type', 'LIBRARY')
            dependencies = data.get('dependencies', [])
            description = data.get('description', '')
            metadata = data.get('metadata', {})
        except KeyError as e:
            raise RecipeParseError(f"Missing required field in components.json: {e}")
        
        # Parse component type
        try:
            component_type = ComponentType[type_str.upper()]
        except KeyError:
            component_type = ComponentType.LIBRARY
        
        return Components(
            name=name,
            version=version,
            type=component_type,
            dependencies=dependencies,
            description=description,
            metadata=metadata
        )
    
    def _create_metadata(self, recipe_path: Path) -> RecipeMetadata:
        """Create metadata for the recipe.
        
        Args:
            recipe_path: Path to recipe directory
            
        Returns:
            Recipe metadata
        """
        # Get file modification times
        req_mtime = (recipe_path / "requirements.md").stat().st_mtime
        design_mtime = (recipe_path / "design.md").stat().st_mtime
        comp_mtime = (recipe_path / "components.json").stat().st_mtime
        
        # Use latest modification time
        latest_mtime = max(req_mtime, design_mtime, comp_mtime)
        last_modified = datetime.fromtimestamp(latest_mtime)
        
        # Calculate initial checksum (will be updated after full parsing)
        checksum = ""
        
        return RecipeMetadata(
            created_at=last_modified,  # Use modification time as creation time
            last_modified=last_modified,
            checksum=checksum,
            author="recipe-executor",
            tags=[]
        )