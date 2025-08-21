"""Code generation from recipes with Python standards enforcement."""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
import re
import json
from datetime import datetime
from jinja2 import Template

from .recipe_model import Recipe, GeneratedCode, BuildContext, ComponentDesign, Requirements
from .python_standards import PythonStandards


class CodeGenerationError(Exception):
    """Raised when code generation fails."""

    pass


@dataclass
class CodeTemplate:
    """Template for generating code."""

    name: str
    template: str
    file_pattern: str

    def render(self, context: Dict[str, Any]) -> str:
        """Render template with context."""
        tmpl = Template(self.template)
        return tmpl.render(**context)


class CodeGenerator:
    """Generates code from design specifications with Python standards."""

    def __init__(self, standards: Optional[PythonStandards] = None):
        """Initialize with Python standards enforcement."""
        self.standards = standards or PythonStandards()
        self.templates = self._load_templates()

    def generate(self, recipe: Recipe, context: Optional[BuildContext] = None) -> GeneratedCode:
        """Generate code based on design and requirements."""
        if context is None:
            context = BuildContext(recipe=recipe)

        generated = GeneratedCode(recipe_name=recipe.name, files={}, language="python")

        # Generate main module files
        for component in recipe.design.components:
            code = self._generate_component(component, recipe, context)
            # Format with ruff
            code = self.standards.format_code_with_ruff(code)
            # Add type annotations if missing
            code = self.standards.add_type_stubs(code)

            # Validate with pyright
            passed, errors = self.standards.check_code_with_pyright(code, component.name)
            if not passed and errors:
                # Try to fix common type errors
                code = self._fix_type_errors(code, errors)
                # Re-check
                passed, errors = self.standards.check_code_with_pyright(code, component.name)
                if not passed:
                    raise CodeGenerationError(f"Generated code has type errors: {errors}")

            # Determine file path
            file_path = self._get_component_path(component, recipe)
            generated.add_file(file_path, code)

        # Generate __init__.py files
        init_files = self._generate_init_files(recipe, generated)
        for path, content in init_files.items():
            generated.add_file(path, content)

        # Note: pyproject.toml and other Python project files should be
        # managed by UV directly, not generated from recipes

        # Validate against requirements
        validation_result = self._validate_against_requirements(generated, recipe.requirements)
        if not validation_result:
            raise CodeGenerationError("Generated code doesn't satisfy requirements")

        return generated

    def _generate_component(
        self, component: ComponentDesign, recipe: Recipe, context: BuildContext
    ) -> str:
        """Generate code for a single component."""
        # Check if we have a code snippet in the design
        if component.code_snippet:
            # Use the provided code as base
            code = component.code_snippet
        else:
            # Generate from template
            code = self._generate_from_template(component, recipe, context)

        # Ensure proper imports
        code = self._add_required_imports(code, component, recipe)

        # Add docstrings if missing
        code = self._add_docstrings(code, component)

        return code

    def _generate_from_template(
        self, component: ComponentDesign, recipe: Recipe, context: BuildContext
    ) -> str:
        """Generate code from template."""
        # Select appropriate template
        template = self._select_template(component)

        # Build template context
        tmpl_context = {
            "component": component,
            "recipe": recipe,
            "requirements": recipe.requirements,
            "design": recipe.design,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

        # Render template
        return template.render(tmpl_context)

    def _select_template(self, component: ComponentDesign) -> CodeTemplate:
        """Select appropriate template for component."""
        # Determine template based on component type
        if component.class_name:
            # Class-based component
            if "Parser" in component.class_name:
                return self.templates.get("parser", self.templates["class"])
            elif "Manager" in component.class_name:
                return self.templates.get("manager", self.templates["class"])
            elif "Generator" in component.class_name:
                return self.templates.get("generator", self.templates["class"])
            else:
                return self.templates["class"]
        else:
            # Module-level functions
            return self.templates["module"]

    def _load_templates(self) -> Dict[str, "CodeTemplate"]:
        """Load code generation templates."""
        templates = {}

        # Basic class template
        templates["class"] = CodeTemplate(
            name="class",
            template='''"""{{ component.description }}"""

from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from pathlib import Path


class {{ component.class_name }}:
    """{{ component.description }}"""
    
    def __init__(self) -> None:
        """Initialize {{ component.class_name }}."""
        pass
    
    {% for method in component.methods %}
    def {{ method }}(self) -> None:
        """{{ method }} implementation."""
        raise NotImplementedError("{{ method }} not yet implemented")
    
    {% endfor %}
''',
            file_pattern="{component_name}.py",
        )

        # Module template
        templates["module"] = CodeTemplate(
            name="module",
            template='''"""{{ component.description }}"""

from typing import Any, Optional, Dict, List
from pathlib import Path


{% for method in component.methods %}
def {{ method }}() -> None:
    """{{ method }} implementation."""
    raise NotImplementedError("{{ method }} not yet implemented")


{% endfor %}
''',
            file_pattern="{component_name}.py",
        )

        # Parser template
        templates["parser"] = CodeTemplate(
            name="parser",
            template='''"""{{ component.description }}"""

from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
import json


class {{ component.class_name }}:
    """{{ component.description }}"""
    
    def __init__(self) -> None:
        """Initialize {{ component.class_name }}."""
        pass
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse content and return structured data."""
        raise NotImplementedError("parse not yet implemented")
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate parsed data and return issues."""
        issues: List[str] = []
        # TODO: Implement validation
        return issues
''',
            file_pattern="{component_name}.py",
        )

        return templates

    def _add_required_imports(self, code: str, component: ComponentDesign, recipe: Recipe) -> str:
        """Add required imports based on code analysis."""
        lines = code.split("\n")

        # Check what's being used in the code
        needs_typing = any(word in code for word in ["Optional", "Dict", "List", "Any", "Tuple"])
        needs_dataclasses = "dataclass" in code or "@dataclass" in code
        needs_pathlib = "Path" in code
        needs_datetime = "datetime" in code or "timestamp" in code

        # Build import block
        imports = []
        if needs_typing:
            imports.append("from typing import Any, Optional, Dict, List, Tuple, Union")
        if needs_dataclasses:
            imports.append("from dataclasses import dataclass, field")
        if needs_pathlib:
            imports.append("from pathlib import Path")
        if needs_datetime:
            imports.append("from datetime import datetime")

        # Add imports after docstring
        result_lines = []
        docstring_ended = False
        imports_added = False

        for line in lines:
            if not docstring_ended and line.strip().startswith('"""'):
                result_lines.append(line)
                if line.count('"""') >= 2:  # Single line docstring
                    docstring_ended = True
            elif not docstring_ended and '"""' in line:
                result_lines.append(line)
                docstring_ended = True
            elif docstring_ended and not imports_added:
                # Add imports here
                result_lines.append("")
                for imp in imports:
                    result_lines.append(imp)
                result_lines.append("")
                result_lines.append(line)
                imports_added = True
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _add_docstrings(self, code: str, component: ComponentDesign) -> str:
        """Add docstrings to functions and classes if missing."""
        lines = code.split("\n")
        result = []

        for i, line in enumerate(lines):
            result.append(line)

            # Check for function or class definition
            if line.strip().startswith("def ") or line.strip().startswith("class "):
                # Check if next line is a docstring
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        # Add docstring
                        indent = len(line) - len(line.lstrip())
                        func_or_class_name = (
                            line.strip().split("(")[0].replace("def ", "").replace("class ", "")
                        )
                        result.append(
                            " " * (indent + 4) + f'"""Implementation of {func_or_class_name}."""'
                        )

        return "\n".join(result)

    def _fix_type_errors(self, code: str, errors: List[str]) -> str:
        """Attempt to fix common type errors."""
        # Fix missing return type annotations
        if any("Return type" in error for error in errors):
            code = self._add_return_types(code)

        # Fix missing parameter type annotations
        if any("Parameter" in error for error in errors):
            code = self._add_parameter_types(code)

        # Fix Optional types
        if any("None" in error for error in errors):
            code = self._fix_optional_types(code)

        return code

    def _add_return_types(self, code: str) -> str:
        """Add return type annotations to functions."""
        lines = code.split("\n")
        result = []

        for line in lines:
            if line.strip().startswith("def ") and "->" not in line and line.rstrip().endswith(":"):
                # Determine return type based on function name/content
                if "init" in line:
                    line = line.rstrip(":") + " -> None:"
                elif "get_" in line or "find_" in line:
                    line = line.rstrip(":") + " -> Optional[Any]:"
                elif "is_" in line or "has_" in line or "validate" in line:
                    line = line.rstrip(":") + " -> bool:"
                elif "list_" in line or "get_all" in line:
                    line = line.rstrip(":") + " -> List[Any]:"
                else:
                    line = line.rstrip(":") + " -> Any:"

            result.append(line)

        return "\n".join(result)

    def _add_parameter_types(self, code: str) -> str:
        """Add type annotations to function parameters."""
        # This is a simplified implementation
        # In practice, would need more sophisticated analysis
        return code

    def _fix_optional_types(self, code: str) -> str:
        """Fix Optional type annotations."""
        # Replace ': None' with ': Optional[None]' doesn't make sense
        # Instead, look for places where None is assigned
        code = code.replace("= None", "= field(default=None)")
        return code

    def _get_component_path(self, component: ComponentDesign, recipe: Recipe) -> str:
        """Determine file path for component."""
        # Convert component name to snake_case
        name = component.name.lower().replace(" ", "_").replace("-", "_")

        # Determine directory structure
        if recipe.components.type.value == "core":
            return f"src/recipe_executor/{name}.py"
        else:
            recipe_name = recipe.name.replace("-", "_")
            return f"src/{recipe_name}/{name}.py"

    def _generate_init_files(self, recipe: Recipe, generated: GeneratedCode) -> Dict[str, str]:
        """Generate __init__.py files for packages."""
        init_files = {}

        # Collect all directories that need __init__.py
        dirs_needing_init = set()
        for file_path in generated.files.keys():
            path = Path(file_path)
            if path.suffix == ".py":
                # Add all parent directories
                for parent in path.parents:
                    if parent.name in ["src", "tests"] or parent.parent.name in ["src", "tests"]:
                        dirs_needing_init.add(parent)

        # Generate __init__.py for each directory
        for dir_path in dirs_needing_init:
            # Collect exports from this directory
            exports = []
            for file_path in generated.files.keys():
                path = Path(file_path)
                if path.parent == dir_path and path.stem != "__init__":
                    # Extract classes and functions from file
                    content = generated.files[file_path]
                    exports.extend(self._extract_exports(content))

            # Generate __init__.py content
            if exports:
                init_content = self.standards.get_init_template().format(
                    module=dir_path.name, exports=str(exports)
                )
            else:
                init_content = '"""Package initialization."""\n\n__all__: List[str] = []\n'

            init_path = dir_path / "__init__.py"
            init_files[str(init_path)] = init_content

        return init_files

    def _extract_exports(self, code: str) -> List[str]:
        """Extract exportable names from Python code."""
        exports = []

        # Find class definitions
        class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)
        exports.extend(class_pattern.findall(code))

        # Find function definitions (excluding private)
        func_pattern = re.compile(r"^def\s+([a-zA-Z]\w*)", re.MULTILINE)
        exports.extend(func_pattern.findall(code))

        return exports

    def _generate_project_files(self, recipe: Recipe) -> Dict[str, str]:
        """Generate project configuration files."""
        files = {}

        # Generate pyproject.toml
        pyproject_content = self.standards.get_pyproject_template().format(
            name=recipe.name,
            version=recipe.components.version,
            description=recipe.components.description or recipe.requirements.purpose,
            dependencies=json.dumps(recipe.components.external_dependencies.get("third_party", [])),
        )
        files["pyproject.toml"] = pyproject_content

        # Generate pyrightconfig.json
        files["pyrightconfig.json"] = self.standards.get_pyrightconfig_template()

        # Generate .gitignore
        files[".gitignore"] = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# UV
.uv/
uv.lock

# Testing
.coverage
.pytest_cache/
htmlcov/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

        return files

    def _validate_against_requirements(
        self, code: GeneratedCode, requirements: Requirements
    ) -> bool:
        """Validate generated code satisfies requirements."""
        # This is a simplified validation
        # In practice, would need more sophisticated analysis

        # Check that we have generated files
        if not code.files:
            return False

        # Check that all MUST requirements have corresponding code
        for req in requirements.get_must_requirements():
            # Simple check: requirement keywords should appear in code
            req_keywords = req.description.lower().split()
            code_text = " ".join(code.files.values()).lower()

            # At least some keywords should be in the code
            if not any(keyword in code_text for keyword in req_keywords[:3]):
                return False

        return True
