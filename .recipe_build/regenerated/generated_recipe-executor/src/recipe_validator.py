"""Recipe validator for checking WHAT/HOW separation and structure."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .recipe_model import Recipe


@dataclass
class ValidationIssue:
    """Single validation issue found in recipe."""
    severity: str  # "error", "warning", "info"
    location: str  # "requirements", "design", "components"
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of recipe validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    corrections: Dict[str, str] = field(default_factory=dict)
    
    def add_error(self, location: str, message: str, suggestion: Optional[str] = None):
        """Add an error-level issue."""
        self.issues.append(ValidationIssue(
            severity="error",
            location=location,
            message=message,
            suggestion=suggestion
        ))
        self.valid = False
    
    def add_warning(self, location: str, message: str, suggestion: Optional[str] = None):
        """Add a warning-level issue."""
        self.issues.append(ValidationIssue(
            severity="warning",
            location=location,
            message=message,
            suggestion=suggestion
        ))
    
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return any(issue.severity == "error" for issue in self.issues)
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.severity == "error"]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == "warning"]


class RecipeValidator:
    """Validates recipe structure and WHAT/HOW separation."""
    
    def __init__(self):
        """Initialize validator with patterns."""
        # Patterns that indicate HOW (implementation details) in requirements
        self.how_patterns = [
            (r'MUST use (PostgreSQL|MySQL|Redis|MongoDB|SQLite)', 
             "Specific database technology"),
            (r'MUST implement using (\w+)', 
             "Implementation method specified"),
            (r'using Claude', 
             "Tool choice specified"),
            (r'MUST call (\w+) API', 
             "Specific API integration"),
            (r'MUST inherit from', 
             "Implementation inheritance"),
            (r'MUST extend', 
             "Implementation extension"),
            (r'written in (Python|Java|Go|Rust)', 
             "Language specification"),
            (r'using (asyncio|threading|multiprocessing)', 
             "Concurrency implementation"),
            (r'with (Flask|Django|FastAPI)', 
             "Framework specification"),
        ]
        
        # Patterns that indicate WHAT (functional requirements) in design
        self.what_patterns = [
            (r'MUST \w+', 
             "Requirements language in design"),
            (r'SHALL \w+', 
             "Requirements language in design"),
            (r'system shall', 
             "Functional requirement in design"),
            (r'user can', 
             "User story in design"),
            (r'system must', 
             "Requirement in design"),
            (r'required to', 
             "Requirement in design"),
        ]
        
        # Valid requirement starter words
        self.valid_requirement_starters = [
            'MUST', 'SHOULD', 'COULD', 'SHALL', 'MAY'
        ]
    
    def validate(self, recipe: Recipe) -> ValidationResult:
        """Perform complete validation of a recipe.
        
        Args:
            recipe: Recipe to validate
            
        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(valid=True)
        
        # Validate WHAT/HOW separation
        self._validate_separation(recipe, result)
        
        # Validate recipe structure
        self._validate_structure(recipe, result)
        
        # Validate requirements completeness
        self._validate_requirements(recipe, result)
        
        # Validate design completeness
        self._validate_design(recipe, result)
        
        # Validate components metadata
        self._validate_components(recipe, result)
        
        # Validate dependencies
        self._validate_dependencies(recipe, result)
        
        # Generate corrections if needed
        if result.has_errors():
            result.corrections = self._generate_corrections(recipe, result)
        
        return result
    
    def validate_separation(self, recipe: Recipe) -> ValidationResult:
        """Validate WHAT/HOW separation in recipe.
        
        Args:
            recipe: Recipe to validate
            
        Returns:
            ValidationResult focused on separation issues
        """
        result = ValidationResult(valid=True)
        self._validate_separation(recipe, result)
        
        if result.has_errors():
            result.corrections = self._generate_corrections(recipe, result)
        
        return result
    
    def _validate_separation(self, recipe: Recipe, result: ValidationResult):
        """Check for WHAT/HOW separation violations.
        
        Args:
            recipe: Recipe to check
            result: Result to add issues to
        """
        # Read raw content for pattern matching
        req_path = recipe.path / "requirements.md"
        design_path = recipe.path / "design.md"
        
        if req_path.exists():
            req_content = req_path.read_text()
            self._check_how_in_requirements(req_content, result)
        
        if design_path.exists():
            design_content = design_path.read_text()
            self._check_what_in_design(design_content, result)
    
    def _check_how_in_requirements(self, content: str, result: ValidationResult):
        """Check for HOW (implementation details) in requirements.
        
        Args:
            content: Requirements content
            result: Result to add issues to
        """
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip non-requirement lines
            if not line.strip() or line.startswith('#'):
                continue
            
            # Check each HOW pattern
            for pattern, description in self.how_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    result.add_error(
                        location="requirements",
                        message=f"Line {line_num}: Requirements contain HOW ({description}): {line.strip()[:100]}",
                        suggestion=f"Move implementation detail '{description}' to design.md"
                    )
    
    def _check_what_in_design(self, content: str, result: ValidationResult):
        """Check for WHAT (functional requirements) in design.
        
        Args:
            content: Design content
            result: Result to add issues to
        """
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip code blocks
            if line.strip().startswith('```'):
                continue
            
            # Check each WHAT pattern
            for pattern, description in self.what_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Allow some patterns in implementation notes
                    if 'Implementation' in line or 'Note' in line:
                        continue
                    
                    result.add_warning(
                        location="design",
                        message=f"Line {line_num}: Design contains WHAT ({description}): {line.strip()[:100]}",
                        suggestion=f"Move functional requirement to requirements.md"
                    )
    
    def _validate_structure(self, recipe: Recipe, result: ValidationResult):
        """Validate overall recipe structure.
        
        Args:
            recipe: Recipe to validate
            result: Result to add issues to
        """
        # Check recipe has required components
        if not recipe.requirements.get_all():
            result.add_error(
                location="requirements",
                message="Recipe has no requirements defined",
                suggestion="Add at least one MUST requirement"
            )
        
        if not recipe.design.components:
            result.add_error(
                location="design",
                message="Recipe has no components designed",
                suggestion="Add at least one component design"
            )
        
        # Check name consistency
        if recipe.name != recipe.components.name:
            result.add_error(
                location="components",
                message=f"Recipe name mismatch: '{recipe.name}' vs '{recipe.components.name}'",
                suggestion="Ensure components.json name matches recipe directory name"
            )
        
        # Check version format
        version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        if not version_pattern.match(recipe.components.version):
            result.add_warning(
                location="components",
                message=f"Invalid version format: {recipe.components.version}",
                suggestion="Use semantic versioning (e.g., 1.0.0)"
            )
    
    def _validate_requirements(self, recipe: Recipe, result: ValidationResult):
        """Validate requirements completeness and quality.
        
        Args:
            recipe: Recipe to validate
            result: Result to add issues to
        """
        requirements = recipe.requirements
        
        # Check for at least one MUST requirement
        must_reqs = requirements.get_must_requirements()
        if not must_reqs:
            result.add_warning(
                location="requirements",
                message="No MUST requirements found",
                suggestion="Add at least one MUST requirement for core functionality"
            )
        
        # Check for testable requirements
        testable_reqs = requirements.get_testable_requirements()
        untestable_count = len(requirements.get_all()) - len(testable_reqs)
        
        if untestable_count > 0:
            result.add_warning(
                location="requirements",
                message=f"{untestable_count} requirements have no validation criteria",
                suggestion="Add validation criteria to make requirements testable"
            )
        
        # Check for duplicate requirements
        seen_descriptions = set()
        for req in requirements.get_all():
            desc_lower = req.description.lower()
            if desc_lower in seen_descriptions:
                result.add_warning(
                    location="requirements",
                    message=f"Duplicate requirement: {req.description[:50]}",
                    suggestion="Combine or differentiate duplicate requirements"
                )
            seen_descriptions.add(desc_lower)
        
        # Check success criteria
        if not requirements.success_criteria:
            result.add_warning(
                location="requirements",
                message="No success criteria defined",
                suggestion="Add measurable success criteria for the recipe"
            )
    
    def _validate_design(self, recipe: Recipe, result: ValidationResult):
        """Validate design completeness and consistency.
        
        Args:
            recipe: Recipe to validate
            result: Result to add issues to
        """
        design = recipe.design
        
        # Check architecture description
        if not design.architecture or design.architecture == "No architecture description found":
            result.add_warning(
                location="design",
                message="Missing architecture description",
                suggestion="Add an Architecture or Overview section to design.md"
            )
        
        # Check component designs have enough detail
        for component in design.components:
            if not component.methods:
                result.add_warning(
                    location="design",
                    message=f"Component '{component.name}' has no methods defined",
                    suggestion="Add method signatures to component design"
                )
            
            if not component.description:
                result.add_warning(
                    location="design",
                    message=f"Component '{component.name}' has no description",
                    suggestion="Add description explaining component purpose"
                )
        
        # Check for orphaned code blocks
        if len(design.code_blocks) > len(design.components) * 2:
            result.add_warning(
                location="design",
                message="Many code blocks without associated components",
                suggestion="Ensure code examples are linked to specific components"
            )
    
    def _validate_components(self, recipe: Recipe, result: ValidationResult):
        """Validate components.json metadata.
        
        Args:
            recipe: Recipe to validate
            result: Result to add issues to
        """
        components = recipe.components
        
        # Check description
        if not components.description:
            result.add_warning(
                location="components",
                message="Missing component description",
                suggestion="Add a description field to components.json"
            )
        
        # Check type validity
        try:
            _ = components.type.value
        except Exception:
            result.add_error(
                location="components",
                message=f"Invalid component type",
                suggestion="Use one of: SERVICE, AGENT, LIBRARY, TOOL, CORE"
            )
        
        # Check self-hosting flag for recipe-executor
        if recipe.name == "recipe-executor" and not components.is_self_hosting():
            result.add_warning(
                location="components",
                message="Recipe executor should be marked as self-hosting",
                suggestion='Add "self_hosting": true to metadata in components.json'
            )
    
    def _validate_dependencies(self, recipe: Recipe, result: ValidationResult):
        """Validate recipe dependencies.
        
        Args:
            recipe: Recipe to validate
            result: Result to add issues to
        """
        dependencies = recipe.get_dependencies()
        
        # Check for circular self-dependency
        if recipe.name in dependencies:
            result.add_error(
                location="components",
                message="Recipe depends on itself",
                suggestion="Remove self-dependency from dependencies list"
            )
        
        # Check dependency format
        for dep in dependencies:
            if not re.match(r'^[a-z0-9-]+$', dep):
                result.add_warning(
                    location="components",
                    message=f"Invalid dependency name format: {dep}",
                    suggestion="Use lowercase alphanumeric with hyphens"
                )
        
        # Warn about too many dependencies
        if len(dependencies) > 10:
            result.add_warning(
                location="components",
                message=f"Recipe has {len(dependencies)} dependencies",
                suggestion="Consider breaking down the recipe if it has too many dependencies"
            )
    
    def _generate_corrections(self, recipe: Recipe, result: ValidationResult) -> Dict[str, str]:
        """Generate corrections for validation issues.
        
        Args:
            recipe: Recipe with issues
            result: Validation result with issues
            
        Returns:
            Dictionary of file paths to corrected content
        """
        corrections = {}
        
        # Group issues by location
        req_issues = [i for i in result.issues if i.location == "requirements"]
        design_issues = [i for i in result.issues if i.location == "design"]
        comp_issues = [i for i in result.issues if i.location == "components"]
        
        # Generate corrected requirements if needed
        if req_issues:
            corrections["requirements.md"] = self._correct_requirements(
                recipe.path / "requirements.md",
                req_issues
            )
        
        # Generate corrected design if needed
        if design_issues:
            corrections["design.md"] = self._correct_design(
                recipe.path / "design.md",
                design_issues
            )
        
        # Generate corrected components.json if needed
        if comp_issues:
            corrections["components.json"] = self._correct_components(
                recipe.path / "components.json",
                comp_issues
            )
        
        return corrections
    
    def _correct_requirements(self, path: Path, issues: List[ValidationIssue]) -> str:
        """Generate corrected requirements content.
        
        Args:
            path: Path to requirements file
            issues: Issues to fix
            
        Returns:
            Corrected content
        """
        if not path.exists():
            return ""
        
        content = path.read_text()
        lines = content.split('\n')
        
        # Apply corrections based on issues
        for issue in issues:
            if "HOW" in issue.message:
                # Remove implementation details
                for pattern, _ in self.how_patterns:
                    content = re.sub(pattern, "MUST [implementation detail moved to design]", content, flags=re.IGNORECASE)
        
        return content
    
    def _correct_design(self, path: Path, issues: List[ValidationIssue]) -> str:
        """Generate corrected design content.
        
        Args:
            path: Path to design file
            issues: Issues to fix
            
        Returns:
            Corrected content
        """
        if not path.exists():
            return ""
        
        content = path.read_text()
        
        # Apply corrections based on issues
        for issue in issues:
            if "WHAT" in issue.message:
                # Remove functional requirements
                for pattern, _ in self.what_patterns:
                    content = re.sub(pattern, "[requirement moved to requirements.md]", content, flags=re.IGNORECASE)
        
        return content
    
    def _correct_components(self, path: Path, issues: List[ValidationIssue]) -> str:
        """Generate corrected components.json content.
        
        Args:
            path: Path to components.json
            issues: Issues to fix
            
        Returns:
            Corrected content
        """
        import json
        
        if not path.exists():
            return ""
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Apply corrections based on issues
        for issue in issues:
            if "name mismatch" in issue.message:
                # Fix name to match directory
                parent_dir = path.parent.name
                data['name'] = parent_dir
            elif "version format" in issue.message:
                # Fix version format
                data['version'] = "1.0.0"
            elif "self-hosting" in issue.message:
                # Add self-hosting flag
                if 'metadata' not in data:
                    data['metadata'] = {}
                data['metadata']['self_hosting'] = True
        
        return json.dumps(data, indent=2)