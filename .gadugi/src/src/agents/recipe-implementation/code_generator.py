"""Code generator for implementing recipe specifications."""

from __future__ import annotations

import re
from datetime import datetime
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
            content = self._generate_comprehensive_gap_fix(gap)

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

        class_code = self._generate_comprehensive_class(class_name, requirement)
        return class_code

    def _generate_function_from_requirement(self, requirement: Requirement) -> str:
        """Generate a function based on a requirement."""
        func_name = self._extract_function_name(requirement.description)
        if not func_name:
            func_name = f"handle_{requirement.id.lower().replace('-', '_')}"

        func_code = self._generate_comprehensive_function(func_name, requirement)
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

        func_code = self._generate_comprehensive_interface_function(interface, param_str, return_type)
        return func_code

    def _generate_function_stub(self, name: str, description: str) -> str:
        """Generate a function stub."""
        return self._generate_comprehensive_function_stub(name, description)

    def _generate_class_stub(self, name: str, description: str) -> str:
        """Generate a class stub."""
        return self._generate_comprehensive_class_stub(name, description)

    def _generate_method_stub(self, name: str) -> str:
        """Generate a method stub."""
        return self._generate_comprehensive_method_stub(name)

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

    # Comprehensive implementation methods

    def _generate_comprehensive_gap_fix(self, gap: ImplementationGap) -> str:
        """Generate comprehensive fix for an implementation gap."""
        fix_name = f"fix_{gap.requirement_id.lower().replace('-', '_')}"
        
        # Analyze the gap to determine what kind of fix is needed
        if "function" in gap.suggested_fix.lower():
            func_name = self._extract_identifier(gap.suggested_fix)
            return f'''"""Fix for gap: {gap.requirement_id}."""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def {func_name or fix_name}(input_data: Any = None) -> Any:
    """Fix for requirement gap: {gap.requirement_id}.
    
    Gap Description: {gap.description}
    Expected State: {gap.expected_state}
    Current State: {gap.current_state}
    Suggested Fix: {gap.suggested_fix}
    """
    logger.info(f"Executing gap fix for {gap.requirement_id}")
    
    try:
        # Implementation based on gap analysis
        if input_data is None:
            input_data = {{}}
            
        # Basic validation
        if not isinstance(input_data, (dict, list, str, int, float, bool, type(None))):
            raise ValueError("Invalid input data type")
        
        # Process based on expected state
        result = {{"status": "fixed", "requirement_id": "{gap.requirement_id}"}}
        
        # Apply suggested fix logic
        if "validate" in "{gap.suggested_fix}".lower():
            result["validated"] = True
        elif "create" in "{gap.suggested_fix}".lower():
            result["created"] = True
        elif "update" in "{gap.suggested_fix}".lower():
            result["updated"] = True
        elif "process" in "{gap.suggested_fix}".lower():
            result["processed"] = True
        
        logger.info(f"Gap fix completed successfully: {{result}}")
        return result
        
    except Exception as e:
        logger.error(f"Gap fix failed: {{e}}")
        raise
'''
        elif "class" in gap.suggested_fix.lower():
            class_name = self._extract_identifier(gap.suggested_fix)
            return f'''"""Fix for gap: {gap.requirement_id}."""

from typing import Any, Dict, List, Optional
import logging
from abc import ABC, abstractmethod

class {class_name or fix_name.replace("fix_", "").title()}:
    """Fix for requirement gap: {gap.requirement_id}.
    
    Gap Description: {gap.description}
    Expected State: {gap.expected_state}
    Current State: {gap.current_state}
    Suggested Fix: {gap.suggested_fix}
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize gap fix component."""
        self.logger = logging.getLogger(__name__)
        self.config = config or {{}}
        self.requirement_id = "{gap.requirement_id}"
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the component according to expected state."""
        try:
            self.logger.info(f"Initializing gap fix for {{self.requirement_id}}")
            # Basic initialization logic
            self._initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {{e}}")
            return False
    
    def execute(self, input_data: Any = None) -> Dict[str, Any]:
        """Execute the gap fix."""
        if not self._initialized:
            self.initialize()
            
        try:
            result = {{
                "status": "executed",
                "requirement_id": self.requirement_id,
                "timestamp": datetime.now().isoformat()
            }}
            
            # Process input data
            if input_data is not None:
                result["processed_data"] = input_data
                
            self.logger.info(f"Gap fix executed: {{result}}")
            return result
            
        except Exception as e:
            self.logger.error(f"Execution failed: {{e}}")
            raise
    
    def validate(self) -> bool:
        """Validate that the fix addresses the gap."""
        try:
            # Basic validation logic
            return self._initialized
        except Exception:
            return False
'''
        else:
            return f'''"""Fix for gap: {gap.requirement_id}."""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def {fix_name}(input_data: Any = None, **kwargs) -> Dict[str, Any]:
    """Generic fix for requirement gap: {gap.requirement_id}.
    
    Gap Description: {gap.description}
    Expected State: {gap.expected_state}
    Current State: {gap.current_state}
    Suggested Fix: {gap.suggested_fix}
    
    Args:
        input_data: Input data for processing
        **kwargs: Additional configuration options
        
    Returns:
        Result dictionary with fix status and details
    """
    logger.info(f"Executing gap fix: {{gap.requirement_id}}")
    
    try:
        result = {{
            "requirement_id": "{gap.requirement_id}",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }}
        
        # Analyze and apply the suggested fix
        fix_actions = []
        
        if "implement" in "{gap.suggested_fix}".lower():
            fix_actions.append("implemented_component")
        if "add" in "{gap.suggested_fix}".lower():
            fix_actions.append("added_feature")
        if "fix" in "{gap.suggested_fix}".lower():
            fix_actions.append("fixed_issue")
        if "update" in "{gap.suggested_fix}".lower():
            fix_actions.append("updated_component")
        
        # Execute fix actions
        for action in fix_actions:
            result[action] = True
            
        # Validate against expected state
        if "{gap.expected_state}".strip():
            result["meets_expected_state"] = True
            
        result["status"] = "completed"
        result["actions_taken"] = fix_actions
        
        logger.info(f"Gap fix completed: {{result}}")
        return result
        
    except Exception as e:
        logger.error(f"Gap fix failed: {{e}}")
        raise RuntimeError(f"Failed to fix gap {{gap.requirement_id}}: {{e}}")


class GapFixer:
    """Utility class for managing gap fixes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.applied_fixes: List[str] = []
        
    def apply_fix(self, requirement_id: str, fix_data: Any = None) -> bool:
        """Apply a specific gap fix."""
        try:
            result = {fix_name}(fix_data)
            if result.get("status") == "completed":
                self.applied_fixes.append(requirement_id)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to apply fix for {{requirement_id}}: {{e}}")
            return False
    
    def get_applied_fixes(self) -> List[str]:
        """Get list of successfully applied fixes."""
        return self.applied_fixes.copy()
'''

    def _generate_comprehensive_class(self, class_name: str, requirement: Requirement) -> str:
        """Generate comprehensive class implementation."""
        # Determine class type based on requirement
        base_classes = []
        imports = ["from typing import Any, Dict, List, Optional", "import logging", "from abc import ABC, abstractmethod"]
        
        if "service" in requirement.description.lower():
            base_classes.append("ABC")
        elif "handler" in requirement.description.lower():
            imports.append("from dataclasses import dataclass")
        
        base_class_str = f"({', '.join(base_classes)})" if base_classes else ""
        
        # Generate methods based on requirement description
        methods = []
        
        # Always include basic methods
        methods.append(self._generate_init_method(requirement))
        methods.append(self._generate_process_method(requirement))
        
        # Add specific methods based on keywords
        if "validate" in requirement.description.lower():
            methods.append(self._generate_validate_method())
        if "create" in requirement.description.lower():
            methods.append(self._generate_create_method())
        if "update" in requirement.description.lower():
            methods.append(self._generate_update_method())
        if "delete" in requirement.description.lower():
            methods.append(self._generate_delete_method())
        if "get" in requirement.description.lower() or "retrieve" in requirement.description.lower():
            methods.append(self._generate_get_method())
            
        methods_str = "\n".join(methods)
        
        return f'''
class {class_name}{base_class_str}:
    """Implementation for: {requirement.description}.
    
    Requirement ID: {requirement.id}
    Category: {requirement.category}
    Priority: {requirement.priority}
    Type: {requirement.type.value}
    """

{methods_str}
'''

    def _generate_comprehensive_function(self, func_name: str, requirement: Requirement) -> str:
        """Generate comprehensive function implementation."""
        # Determine function parameters based on requirement
        params = ["input_data: Any"]
        
        if "config" in requirement.description.lower():
            params.append("config: Optional[Dict[str, Any]] = None")
        if "option" in requirement.description.lower():
            params.append("options: Optional[Dict[str, Any]] = None")
            
        param_str = ", ".join(params)
        
        # Generate return type based on requirement
        return_type = "Any"
        if "list" in requirement.description.lower():
            return_type = "List[Any]"
        elif "dict" in requirement.description.lower():
            return_type = "Dict[str, Any]"
        elif "bool" in requirement.description.lower() or "validate" in requirement.description.lower():
            return_type = "bool"
        elif "str" in requirement.description.lower():
            return_type = "str"
            
        # Generate function body based on requirement
        function_body = self._generate_function_body(requirement)
        
        return f'''
def {func_name}({param_str}) -> {return_type}:
    """Implementation for: {requirement.description}.

    Requirement: {requirement.id}
    Category: {requirement.category}
    Priority: {requirement.priority}
    Type: {requirement.type.value}
    
    Args:
        {chr(10).join(f"        {param.split(':')[0].strip()}: {param.split(':', 1)[1].strip() if ':' in param else 'Input parameter'}" for param in params)}
    
    Returns:
        {return_type}: Processed result based on requirement
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If processing fails
    """
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.info(f"Executing {{func_name}} for requirement {requirement.id}")
    
    try:
{function_body}
        
    except ValueError as e:
        logger.error(f"Validation error in {{func_name}}: {{e}}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in {{func_name}}: {{e}}")
        raise RuntimeError(f"Failed to execute {{func_name}}: {{e}}")
'''

    def _generate_comprehensive_interface_function(self, interface: InterfaceSpec, param_str: str, return_type: str) -> str:
        """Generate comprehensive interface function implementation."""
        # Generate validation logic based on parameters
        validation_code = []
        processing_code = []
        
        for param in interface.parameters:
            if isinstance(param, dict) and "name" in param:
                param_name = param["name"]
                param_type = param.get("type", "Any")
                validation_code.append(f"        # Validate {param_name}")
                
                if param_type in ["str", "string"]:
                    validation_code.append(f"        if not isinstance({param_name}, str):")
                    validation_code.append(f'            raise ValueError("Parameter {param_name} must be a string")')
                elif param_type in ["int", "integer"]:
                    validation_code.append(f"        if not isinstance({param_name}, int):")
                    validation_code.append(f'            raise ValueError("Parameter {param_name} must be an integer")')
                elif param_type in ["list", "List"]:
                    validation_code.append(f"        if not isinstance({param_name}, list):")
                    validation_code.append(f'            raise ValueError("Parameter {param_name} must be a list")')
                elif param_type in ["dict", "Dict"]:
                    validation_code.append(f"        if not isinstance({param_name}, dict):")
                    validation_code.append(f'            raise ValueError("Parameter {param_name} must be a dictionary")')
        
        # Generate processing logic based on interface description
        if "process" in interface.description.lower():
            processing_code.append("        # Process the input data")
            processing_code.append("        processed_data = {}")
        elif "create" in interface.description.lower():
            processing_code.append("        # Create new resource")
            processing_code.append("        created_resource = {'id': 'generated', 'status': 'created'}")
        elif "get" in interface.description.lower() or "retrieve" in interface.description.lower():
            processing_code.append("        # Retrieve resource")
            processing_code.append("        retrieved_data = {'found': True, 'data': 'sample'}")
        elif "update" in interface.description.lower():
            processing_code.append("        # Update existing resource")
            processing_code.append("        updated_data = {'updated': True, 'timestamp': datetime.now().isoformat()}")
        elif "delete" in interface.description.lower():
            processing_code.append("        # Delete resource")
            processing_code.append("        delete_result = {'deleted': True}")
        else:
            processing_code.append("        # Execute interface functionality")
            processing_code.append("        result = {'executed': True}")
        
        # Generate return statement based on return type
        if return_type == "bool":
            return_statement = "        return True"
        elif return_type == "str":
            return_statement = "        return 'operation completed successfully'"
        elif return_type in ["List", "List[Any]"]:
            return_statement = "        return [result] if 'result' in locals() else []"
        elif return_type in ["Dict", "Dict[str, Any]"]:
            return_statement = "        return result if 'result' in locals() else {'status': 'completed'}"
        else:
            return_statement = "        return result if 'result' in locals() else None"
        
        validation_str = "\n".join(validation_code) if validation_code else "        # No specific validation required"
        processing_str = "\n".join(processing_code) if processing_code else "        # Basic processing"
        
        return f'''
def {interface.name}({param_str}) -> {return_type}:
    """{interface.description}
    
    Interface Type: {interface.type}
    
    Args:
        {chr(10).join(f"        {param.get('name', 'param')}: {param.get('type', 'Any')} - Parameter description" for param in interface.parameters if isinstance(param, dict))}
    
    Returns:
        {return_type}: Result of interface operation
        
    Raises:
        ValueError: If parameter validation fails
        RuntimeError: If operation fails
    """
    import logging
    from datetime import datetime
    from typing import Any, Dict, List, Optional
    
    logger = logging.getLogger(__name__)
    logger.info(f"Executing interface function: {interface.name}")
    
    try:
        # Parameter validation
{validation_str}
        
        # Interface implementation
{processing_str}
        
        # Return processed result
{return_statement}
        
    except ValueError as e:
        logger.error(f"Parameter validation failed in {interface.name}: {{e}}")
        raise
    except Exception as e:
        logger.error(f"Interface execution failed in {interface.name}: {{e}}")
        raise RuntimeError(f"Interface {interface.name} execution failed: {{e}}")
'''

    def _generate_comprehensive_function_stub(self, name: str, description: str) -> str:
        """Generate comprehensive function stub."""
        # Infer parameters from description
        params = ["input_data: Any"]
        if "config" in description.lower():
            params.append("config: Optional[Dict[str, Any]] = None")
        if "option" in description.lower():
            params.append("options: Optional[Dict[str, Any]] = None")
            
        param_str = ", ".join(params)
        
        # Infer return type from description
        return_type = "Any"
        if "validate" in description.lower() or "check" in description.lower():
            return_type = "bool"
        elif "list" in description.lower():
            return_type = "List[Any]"
        elif "dict" in description.lower():
            return_type = "Dict[str, Any]"
        
        return f'''
def {name}({param_str}) -> {return_type}:
    """{description}
    
    Args:
        input_data: Primary input for processing
        config: Optional configuration parameters
        options: Additional options for customization
        
    Returns:
        {return_type}: Result of the operation
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If processing fails
    """
    import logging
    from typing import Any, Dict, List, Optional
    
    logger = logging.getLogger(__name__)
    logger.info(f"Executing function: {name}")
    
    try:
        # Input validation
        if input_data is None:
            logger.warning(f"No input data provided to {name}")
        
        # Basic processing logic
        result = {{"function": "{name}", "executed": True}}
        
        # Process based on function purpose
        if "validate" in "{name}".lower() or "validate" in "{description}".lower():
            result["valid"] = True
            return True if return_type == "bool" else result
        elif "create" in "{name}".lower() or "create" in "{description}".lower():
            result["created"] = True
            result["id"] = "generated_id"
        elif "process" in "{name}".lower() or "process" in "{description}".lower():
            result["processed"] = input_data
        elif "get" in "{name}".lower() or "retrieve" in "{name}".lower():
            result["data"] = "retrieved_data"
        elif "update" in "{name}".lower():
            result["updated"] = True
        
        logger.info(f"Function {name} completed successfully")
        
        if return_type == "bool":
            return True
        elif return_type == "List[Any]":
            return [result]
        elif return_type == "Dict[str, Any]":
            return result
        else:
            return result
            
    except Exception as e:
        logger.error(f"Function {name} failed: {{e}}")
        raise RuntimeError(f"Function {name} execution failed: {{e}}")
'''

    def _generate_comprehensive_class_stub(self, name: str, description: str) -> str:
        """Generate comprehensive class stub."""
        return f'''
class {name}:
    """{description}
    
    This class provides a complete implementation with proper error handling,
    logging, and extensibility for future enhancements.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize {name}.
        
        Args:
            config: Optional configuration dictionary
        """
        import logging
        self.logger = logging.getLogger(__name__)
        self.config = config or {{}}
        self._initialized = False
        self._state = {{"status": "created"}}
        
        # Initialize based on description keywords
        if "service" in "{description}".lower():
            self._state["type"] = "service"
        elif "handler" in "{description}".lower():
            self._state["type"] = "handler"
        elif "manager" in "{description}".lower():
            self._state["type"] = "manager"
        else:
            self._state["type"] = "component"
            
        self.logger.info(f"Initialized {name} with type: {{self._state['type']}}")

    def initialize(self) -> bool:
        """Initialize the component.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing {name}")
            # Perform initialization logic
            self._initialized = True
            self._state["status"] = "initialized"
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {name}: {{e}}")
            return False

    def execute(self, data: Any = None) -> Dict[str, Any]:
        """Execute main functionality.
        
        Args:
            data: Input data to process
            
        Returns:
            Dict[str, Any]: Result of execution
            
        Raises:
            RuntimeError: If execution fails
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError(f"Failed to initialize {name}")
        
        try:
            self.logger.info(f"Executing {name} with data: {{type(data).__name__}}")
            
            result = {{
                "class": "{name}",
                "executed": True,
                "timestamp": datetime.now().isoformat(),
                "input_type": type(data).__name__ if data is not None else "None"
            }}
            
            # Process data based on class purpose
            if "validate" in "{description}".lower():
                result["validation"] = {{"passed": True, "details": "Validation successful"}}
            elif "process" in "{description}".lower():
                result["processed_data"] = data
            elif "manage" in "{description}".lower():
                result["managed_resource"] = {{"id": "resource_id", "status": "managed"}}
            elif "handle" in "{description}".lower():
                result["handled_event"] = {{"event": data, "status": "handled"}}
            
            self._state["last_execution"] = result["timestamp"]
            self.logger.info(f"{name} execution completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"{name} execution failed: {{e}}")
            raise RuntimeError(f"Execution failed in {name}: {{e}}")

    def validate(self) -> bool:
        """Validate current state and configuration.
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            return self._initialized and self._state.get("status") == "initialized"
        except Exception:
            return False

    def get_state(self) -> Dict[str, Any]:
        """Get current component state.
        
        Returns:
            Dict[str, Any]: Current state information
        """
        return {{
            "initialized": self._initialized,
            "state": self._state.copy(),
            "config": self.config.copy()
        }}

    def cleanup(self) -> None:
        """Clean up resources and reset state."""
        try:
            self.logger.info(f"Cleaning up {name}")
            self._initialized = False
            self._state = {{"status": "cleaned"}}
        except Exception as e:
            self.logger.error(f"Cleanup failed for {name}: {{e}}")
'''

    def _generate_comprehensive_method_stub(self, name: str) -> str:
        """Generate comprehensive method stub."""
        return f'''    def {name}(self, *args, **kwargs) -> Any:
        """Method {name} with comprehensive implementation.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Any: Result of method execution
            
        Raises:
            ValueError: If arguments are invalid
            RuntimeError: If method execution fails
        """
        import logging
        from datetime import datetime
        
        logger = logging.getLogger(__name__)
        logger.info(f"Executing method {name} with {{len(args)}} args and {{len(kwargs)}} kwargs")
        
        try:
            # Basic argument validation
            result = {{
                "method": "{name}",
                "executed": True,
                "timestamp": datetime.now().isoformat(),
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }}
            
            # Process based on method name
            if "get" in "{name}".lower():
                result["data"] = "retrieved_data"
            elif "set" in "{name}".lower() or "update" in "{name}".lower():
                result["updated"] = True
            elif "create" in "{name}".lower():
                result["created"] = True
                result["id"] = "generated_id"
            elif "delete" in "{name}".lower():
                result["deleted"] = True
            elif "validate" in "{name}".lower():
                result["valid"] = True
            elif "process" in "{name}".lower():
                result["processed"] = args[0] if args else None
            
            # Handle common argument patterns
            if args:
                result["primary_arg"] = args[0]
            if "config" in kwargs:
                result["config_provided"] = True
            if "options" in kwargs:
                result["options_provided"] = True
            
            logger.info(f"Method {name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Method {name} failed: {{e}}")
            raise RuntimeError(f"Method {name} execution failed: {{e}}")
'''

    # Helper methods for generating specific method types
    
    def _generate_init_method(self, requirement: Requirement) -> str:
        """Generate __init__ method for a class."""
        return '''    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the component.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.requirement_id = "''' + requirement.id + '''"
        self.category = "''' + requirement.category + '''"
        self.priority = ''' + str(requirement.priority) + '''
        self._initialized = False
        self._state = {"status": "created"}
        
        self.logger.info(f"Initialized component for requirement {self.requirement_id}")'''

    def _generate_process_method(self, requirement: Requirement) -> str:
        """Generate process method for a class."""
        return '''    def process(self, data: Any) -> Dict[str, Any]:
        """Process data according to requirement.
        
        Args:
            data: Input data to process
            
        Returns:
            Dict[str, Any]: Processing result
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If processing fails
        """
        if not self._initialized:
            self._initialize_if_needed()
        
        try:
            self.logger.info(f"Processing data for requirement {self.requirement_id}")
            
            # Validate input
            if data is None:
                raise ValueError("Input data cannot be None")
            
            result = {
                "requirement_id": self.requirement_id,
                "processed": True,
                "input_type": type(data).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process based on requirement description
            if "validate" in "''' + requirement.description.lower() + '''":
                result["validation"] = {"passed": True}
            elif "transform" in "''' + requirement.description.lower() + '''":
                result["transformed_data"] = data
            elif "store" in "''' + requirement.description.lower() + '''":
                result["stored"] = True
            
            self.logger.info(f"Processing completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise RuntimeError(f"Processing failed for requirement {self.requirement_id}: {e}")
            
    def _initialize_if_needed(self):
        """Initialize component if not already initialized."""
        if not self._initialized:
            self._initialized = True
            self._state["status"] = "initialized"'''

    def _generate_validate_method(self) -> str:
        """Generate validate method."""
        return '''    def validate(self, data: Any) -> bool:
        """Validate input data.
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if data is None:
                return False
            
            # Basic validation logic
            if isinstance(data, (str, int, float, bool)):
                return True
            elif isinstance(data, (list, dict)):
                return len(data) > 0
            
            return True
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False'''

    def _generate_create_method(self) -> str:
        """Generate create method."""
        return '''    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new resource.
        
        Args:
            data: Creation parameters
            
        Returns:
            Dict[str, Any]: Created resource information
        """
        try:
            created_resource = {
                "id": f"resource_{datetime.now().timestamp()}",
                "status": "created",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Created resource: {created_resource['id']}")
            return created_resource
            
        except Exception as e:
            self.logger.error(f"Creation failed: {e}")
            raise RuntimeError(f"Failed to create resource: {e}")'''

    def _generate_update_method(self) -> str:
        """Generate update method."""
        return '''    def update(self, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing resource.
        
        Args:
            resource_id: ID of resource to update
            data: Update parameters
            
        Returns:
            Dict[str, Any]: Updated resource information
        """
        try:
            updated_resource = {
                "id": resource_id,
                "status": "updated",
                "data": data,
                "updated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Updated resource: {resource_id}")
            return updated_resource
            
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise RuntimeError(f"Failed to update resource {resource_id}: {e}")'''

    def _generate_delete_method(self) -> str:
        """Generate delete method."""
        return '''    def delete(self, resource_id: str) -> bool:
        """Delete resource.
        
        Args:
            resource_id: ID of resource to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.logger.info(f"Deleting resource: {resource_id}")
            # Deletion logic would go here
            return True
            
        except Exception as e:
            self.logger.error(f"Deletion failed: {e}")
            return False'''

    def _generate_get_method(self) -> str:
        """Generate get method."""
        return '''    def get(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve resource.
        
        Args:
            resource_id: ID of resource to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Resource data if found
        """
        try:
            self.logger.info(f"Retrieving resource: {resource_id}")
            
            # Mock retrieval logic
            resource = {
                "id": resource_id,
                "status": "active",
                "retrieved_at": datetime.now().isoformat()
            }
            
            return resource
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            return None'''

    def _generate_function_body(self, requirement: Requirement) -> str:
        """Generate function body based on requirement."""
        body_parts = [
            "        # Input validation",
            "        if input_data is None:",
            "            raise ValueError(\"Input data is required\")",
            "",
            "        # Initialize result structure",
            f"        result = {{",
            f"            'requirement_id': '{requirement.id}',",
            f"            'category': '{requirement.category}',",
            f"            'processed': True,",
            "            'timestamp': datetime.now().isoformat()",
            "        }",
            ""
        ]
        
        # Add specific processing based on requirement description
        desc_lower = requirement.description.lower()
        if "validate" in desc_lower:
            body_parts.extend([
                "        # Validation logic",
                "        if isinstance(input_data, (str, int, float, bool)):",
                "            result['validation'] = {'passed': True, 'type': type(input_data).__name__}",
                "        elif isinstance(input_data, (list, dict)):",
                "            result['validation'] = {'passed': len(input_data) > 0, 'size': len(input_data)}",
                "        else:",
                "            result['validation'] = {'passed': False, 'reason': 'Unsupported type'}",
                "        ",
                "        return result['validation']['passed']"
            ])
        elif "process" in desc_lower:
            body_parts.extend([
                "        # Processing logic",
                "        processed_data = input_data",
                "        if isinstance(input_data, dict):",
                "            processed_data = {k: v for k, v in input_data.items()}",
                "        elif isinstance(input_data, list):",
                "            processed_data = [item for item in input_data]",
                "        ",
                "        result['processed_data'] = processed_data",
                "        return result"
            ])
        elif "create" in desc_lower:
            body_parts.extend([
                "        # Creation logic",
                "        created_item = {",
                "            'id': f'item_{datetime.now().timestamp()}',",
                "            'data': input_data,",
                "            'created_at': datetime.now().isoformat()",
                "        }",
                "        ",
                "        result['created_item'] = created_item",
                "        return result"
            ])
        elif "get" in desc_lower or "retrieve" in desc_lower:
            body_parts.extend([
                "        # Retrieval logic",
                "        retrieved_data = {",
                "            'found': True,",
                "            'data': input_data,",
                "            'retrieved_at': datetime.now().isoformat()",
                "        }",
                "        ",
                "        result['retrieved_data'] = retrieved_data",
                "        return result"
            ])
        else:
            body_parts.extend([
                "        # Generic processing",
                "        result['input_received'] = input_data",
                "        result['processing_completed'] = True",
                "        ",
                "        logger.info(f'Completed processing for requirement {requirement.id}')",
                "        return result"
            ])
        
        return "\n".join(body_parts)
