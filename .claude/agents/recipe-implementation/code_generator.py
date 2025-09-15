"""Code generator for implementing recipe specifications."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .models import (
    EvaluationReport,
    GeneratedCode,
    ImplementationGap,
    InterfaceSpec,
    RecipeSpec,
    Requirement,
    RequirementType,
)


class CodeGenerator:
    """Generates code to implement recipe specifications."""

    def __init__(self):
        """Initialize code generator."""
        self.recipe_spec: Optional[RecipeSpec] = None
        self.evaluation_report: Optional[EvaluationReport] = None

    def generate_implementation(
        self,
        recipe: RecipeSpec,
        evaluation: EvaluationReport,
        output_path: Optional[Path] = None,
    ) -> List[GeneratedCode]:
        """Generate code to implement recipe requirements.

        Args:
            recipe: Recipe specification
            evaluation: Evaluation report with gaps
            output_path: Output directory for generated code

        Returns:
            List of generated code files
        """
        self.recipe_spec = recipe
        self.evaluation_report = evaluation

        generated_files = []

        # Generate main implementation file
        main_code = self._generate_main_implementation()
        if main_code:
            generated_files.append(main_code)

        # Generate interface implementations
        for interface in recipe.interfaces:
            interface_code = self._generate_interface_implementation(interface)
            if interface_code:
                generated_files.append(interface_code)

        # Generate code to fix critical gaps
        for gap in evaluation.get_critical_gaps():
            gap_fix = self._generate_gap_fix(gap)
            if gap_fix:
                generated_files.append(gap_fix)

        # Generate tests
        test_code = self._generate_tests()
        if test_code:
            generated_files.append(test_code)

        # Write files if output path provided
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            for code in generated_files:
                file_path = output_path / code.file_path.name
                file_path.write_text(code.content)
                code.file_path = file_path

        return generated_files

    def _generate_main_implementation(self) -> Optional[GeneratedCode]:
        """Generate main implementation file."""
        if not self.recipe_spec:
            return None

        # Generate imports
        imports = self._generate_imports()

        # Generate classes for main components
        classes = []
        for req in self.recipe_spec.get_requirements_by_type(
            RequirementType.FUNCTIONAL
        ):
            if (
                "service" in req.description.lower()
                or "manager" in req.description.lower()
            ):
                class_code = self._generate_class_from_requirement(req)
                if class_code:
                    classes.append(class_code)

        # Generate main functions
        functions = []
        for req in self.recipe_spec.get_requirements_by_type(
            RequirementType.FUNCTIONAL
        ):
            if (
                "function" in req.description.lower()
                or "method" in req.description.lower()
            ):
                func_code = self._generate_function_from_requirement(req)
                if func_code:
                    functions.append(func_code)

        # Combine into file content
        content_parts = [
            f'"""Implementation of {self.recipe_spec.name}."""',
            "",
            imports,
            "",
        ]

        if classes:
            content_parts.extend(classes)
            content_parts.append("")

        if functions:
            content_parts.extend(functions)
            content_parts.append("")

        # Add main block if needed
        if functions or classes:
            content_parts.extend(
                [
                    "",
                    'if __name__ == "__main__":',
                    "    # Example usage",
                    "    pass",
                ]
            )

        content = "\n".join(content_parts)

        return GeneratedCode(
            recipe_name=self.recipe_spec.name if self.recipe_spec else "unknown",
            file_path=Path(f"{self.recipe_spec.name.lower().replace(' ', '_')}.py"),
            content=content,
            classes_added=[
                c.split("class ")[1].split("(")[0].split(":")[0]
                for c in classes
                if "class " in c
            ],
            functions_added=[
                f.split("def ")[1].split("(")[0] for f in functions if "def " in f
            ],
        )

    def _generate_interface_implementation(
        self,
        interface: InterfaceSpec,
    ) -> Optional[GeneratedCode]:
        """Generate implementation for an interface."""
        if interface.type == "class":
            content = self._generate_class_interface(interface)
        elif interface.type == "function":
            content = self._generate_function_interface(interface)
        else:
            return None

        if not content:
            return None

        # Create complete file
        file_content = f'''"""Implementation of {interface.name} interface."""

from typing import Any, Dict, List, Optional

{content}
'''

        return GeneratedCode(
            recipe_name=self.recipe_spec.name if self.recipe_spec else "unknown",
            file_path=Path(f"{interface.name.lower()}.py"),
            content=file_content,
            is_new_file=True,
            classes_added=[interface.name] if interface.type == "class" else [],
            functions_added=[interface.name] if interface.type == "function" else [],
        )

    def _generate_gap_fix(self, gap: ImplementationGap) -> Optional[GeneratedCode]:
        """Generate code to fix a specific gap."""
        # Extract what needs to be implemented from the gap
        if "function" in gap.suggested_fix.lower():
            # Generate missing function
            func_name = self._extract_identifier(gap.suggested_fix)
            content = self._generate_function_stub(func_name, gap.expected_state)
        elif "class" in gap.suggested_fix.lower():
            # Generate missing class
            class_name = self._extract_identifier(gap.suggested_fix)
            content = self._generate_class_stub(class_name, gap.expected_state)
        else:
            # Generate generic fix
            content = f'''"""Fix for gap: {gap.requirement_id}."""

# TODO: Implement {gap.suggested_fix}
# Expected: {gap.expected_state}
# Current: {gap.current_state}

def fix_{gap.requirement_id.lower().replace("-", "_")}():
    """Placeholder for gap fix."""
    raise NotImplementedError("{gap.suggested_fix}")
'''

        return GeneratedCode(
            recipe_name=self.recipe_spec.name if self.recipe_spec else "unknown",
            file_path=Path(f"fix_{gap.requirement_id.lower()}.py"),
            content=content,
            is_new_file=True,
            modifications=[
                {
                    "type": "gap_fix",
                    "gap_id": gap.requirement_id,
                    "description": gap.suggested_fix,
                }
            ],
        )

    def _generate_tests(self) -> Optional[GeneratedCode]:
        """Generate test file for the implementation."""
        if not self.recipe_spec:
            return None

        test_content = f'''"""Tests for {self.recipe_spec.name}."""

import pytest
from typing import Any

# Import the implementation
# from {self.recipe_spec.name.lower().replace(" ", "_")} import *


class Test{self._to_class_name(self.recipe_spec.name)}:
    """Test suite for {self.recipe_spec.name}."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def teardown_method(self):
        """Clean up after tests."""
        pass
'''

        # Generate test methods for functional requirements
        test_methods = []
        for req in self.recipe_spec.get_requirements_by_type(
            RequirementType.FUNCTIONAL
        )[:5]:
            test_method = self._generate_test_method(req)
            if test_method:
                test_methods.append(test_method)

        if test_methods:
            test_content += "\n" + "\n".join(test_methods)

        # Add test for interfaces
        for interface in self.recipe_spec.interfaces[:3]:
            test_method = self._generate_interface_test(interface)
            if test_method:
                test_content += "\n" + test_method

        return GeneratedCode(
            recipe_name=self.recipe_spec.name if self.recipe_spec else "unknown",
            file_path=Path(
                f"test_{self.recipe_spec.name.lower().replace(' ', '_')}.py"
            ),
            content=test_content,
            is_new_file=True,
            tests_generated=[
                f"test_{req.id.lower()}" for req in self.recipe_spec.requirements[:5]
            ],
        )

    # Helper methods for code generation

    def _generate_imports(self) -> str:
        """Generate import statements."""
        imports = [
            "from __future__ import annotations",
            "",
            "import logging",
            "from dataclasses import dataclass",
            "from datetime import datetime",
            "from pathlib import Path",
            "from typing import Any, Dict, List, Optional",
        ]

        # Add imports based on dependencies
        if self.recipe_spec and self.recipe_spec.dependencies:
            for dep in self.recipe_spec.dependencies:
                if dep.type == "library":
                    if dep.name == "asyncio":
                        imports.append("import asyncio")
                    elif dep.name == "fastapi":
                        imports.append("from fastapi import FastAPI, HTTPException")
                # Add more library imports as needed

        return "\n".join(imports)

    def _generate_class_from_requirement(self, requirement: Requirement) -> str:
        """Generate a class based on a requirement."""
        class_name = self._extract_class_name(requirement.description)
        if not class_name:
            class_name = f"{requirement.category}Handler"

        class_code = f'''
class {class_name}:
    """Implementation for: {requirement.description}."""

    def __init__(self):
        """Initialize {class_name}."""
        self.logger = logging.getLogger(__name__)
        # TODO: Initialize based on requirement

    def process(self, data: Any) -> Any:
        """Process data according to requirement {requirement.id}."""
        # TODO: Implement {requirement.description}
        self.logger.info(f"Processing {{data}}")
        raise NotImplementedError("{requirement.description}")
'''
        return class_code

    def _generate_function_from_requirement(self, requirement: Requirement) -> str:
        """Generate a function based on a requirement."""
        func_name = self._extract_function_name(requirement.description)
        if not func_name:
            func_name = f"handle_{requirement.id.lower().replace('-', '_')}"

        func_code = f'''
def {func_name}(input_data: Any) -> Any:
    """Implementation for: {requirement.description}.

    Requirement: {requirement.id}
    Priority: {requirement.priority}
    """
    # TODO: Implement {requirement.description}
    raise NotImplementedError("{requirement.description}")
'''
        return func_code

    def _generate_class_interface(self, interface: InterfaceSpec) -> str:
        """Generate class from interface specification."""
        # Generate methods
        methods = []
        for param_dict in interface.parameters:
            if isinstance(param_dict, dict) and "name" in param_dict:
                method_name = param_dict["name"]
                methods.append(self._generate_method_stub(method_name))

        methods_str = "\n".join(methods) if methods else "    pass"

        class_code = f'''
class {interface.name}:
    """{interface.description}"""

    def __init__(self):
        """Initialize {interface.name}."""
        pass

{methods_str}
'''
        return class_code

    def _generate_function_interface(self, interface: InterfaceSpec) -> str:
        """Generate function from interface specification."""
        # Build parameter list
        params = ["self"] if interface.type == "method" else []
        for param in interface.parameters:
            if isinstance(param, dict):
                param_name = param.get("name", "param")
                param_type = param.get("type", "Any")
                params.append(f"{param_name}: {param_type}")

        param_str = ", ".join(params) if params else ""

        # Build return type
        return_type = "Any"
        if interface.returns:
            if isinstance(interface.returns, dict):
                return_type = interface.returns.get("type", "Any")

        func_code = f'''
def {interface.name}({param_str}) -> {return_type}:
    """{interface.description}"""
    # TODO: Implement interface
    raise NotImplementedError("{interface.description}")
'''
        return func_code

    def _generate_function_stub(self, name: str, description: str) -> str:
        """Generate a function stub."""
        return f'''
def {name}(input_data: Any) -> Any:
    """{description}"""
    # TODO: Implement this function
    raise NotImplementedError("{description}")
'''

    def _generate_class_stub(self, name: str, description: str) -> str:
        """Generate a class stub."""
        return f'''
class {name}:
    """{description}"""

    def __init__(self):
        """Initialize {name}."""
        # TODO: Add initialization
        pass

    def execute(self, data: Any) -> Any:
        """Execute main functionality."""
        # TODO: Implement
        raise NotImplementedError("{description}")
'''

    def _generate_method_stub(self, name: str) -> str:
        """Generate a method stub."""
        return f'''    def {name}(self, *args, **kwargs) -> Any:
        """Method {name}."""
        # TODO: Implement
        raise NotImplementedError("Method {name}")
'''

    def _generate_test_method(self, requirement: Requirement) -> str:
        """Generate a test method for a requirement."""
        test_name = f"test_{requirement.id.lower().replace('-', '_')}"

        return f'''
    def {test_name}(self):
        """Test for requirement {requirement.id}: {requirement.description[:50]}..."""
        # TODO: Implement test for {requirement.id}
        # Test criteria: {", ".join(requirement.test_criteria[:2])}
        assert False, "Test not implemented"
'''

    def _generate_interface_test(self, interface: InterfaceSpec) -> str:
        """Generate a test for an interface."""
        test_name = f"test_{interface.name.lower()}_interface"

        return f'''
    def {test_name}(self):
        """Test {interface.name} interface implementation."""
        # TODO: Test that {interface.name} is properly implemented
        # Expected: {interface.description}
        assert False, "Interface test not implemented"
'''

    def _extract_identifier(self, text: str) -> str:
        """Extract an identifier from text."""
        # Look for CamelCase or snake_case identifiers
        patterns = [
            r"\b([A-Z][a-zA-Z0-9]+)\b",  # CamelCase
            r"\b([a-z_][a-z0-9_]+)\b",  # snake_case
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # Fallback: create from first significant word
        words = text.split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                return word.lower()

        return "component"

    def _extract_class_name(self, text: str) -> Optional[str]:
        """Extract a class name from text."""
        # Look for patterns like "Service", "Manager", "Handler"
        patterns = [
            r"(\w+Service)",
            r"(\w+Manager)",
            r"(\w+Handler)",
            r"(\w+Controller)",
            r"(\w+Repository)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_function_name(self, text: str) -> Optional[str]:
        """Extract a function name from text."""
        # Look for verb patterns
        verbs = [
            "create",
            "get",
            "set",
            "update",
            "delete",
            "process",
            "handle",
            "validate",
            "check",
        ]

        text_lower = text.lower()
        for verb in verbs:
            if verb in text_lower:
                # Extract the object after the verb
                words = text_lower.split()
                try:
                    verb_idx = words.index(verb)
                    if verb_idx + 1 < len(words):
                        obj = words[verb_idx + 1]
                        return f"{verb}_{obj}"
                except ValueError:
                    pass

        return None

    def _to_class_name(self, text: str) -> str:
        """Convert text to a class name."""
        words = text.split()
        return "".join(word.capitalize() for word in words)
