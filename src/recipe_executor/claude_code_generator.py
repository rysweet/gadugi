"""Code generation using Claude Code CLI."""

from typing import Optional, Dict, List, Any
from pathlib import Path
import subprocess
from datetime import datetime
import logging
import os
import json
import shutil
import ast

from .recipe_model import Recipe, GeneratedCode, BuildContext, Requirements, ComponentDesign, Design
from .python_standards import PythonStandards
from .base_generator import BaseCodeGenerator, CodeGenerationError
from .stub_detector import StubDetector
from .intelligent_stub_detector import IntelligentStubDetector
from .prompt_loader import PromptLoader

# Set up logging
logger = logging.getLogger("recipe_executor.claude_generator")


class ClaudeCodeGenerationError(CodeGenerationError):
    """Raised when Claude Code generation fails."""

    def __init__(self, message: str, command: Optional[str] = None, stderr: Optional[str] = None):
        """Initialize with detailed error information.

        Args:
            message: Human-readable error message
            command: The command that failed
            stderr: Standard error output from the failed command
        """
        super().__init__(message)
        self.command = command
        self.stderr = stderr

        # Enhance message with details if available
        if stderr:
            self.message = f"{message}\nError output: {stderr}"
        if command:
            self.message = f"{self.message}\nCommand: {command}"


class ClaudeCodeGenerator(BaseCodeGenerator):
    """Generates code from recipes using Claude Code CLI."""

    def __init__(
        self,
        standards: Optional[PythonStandards] = None,
        guidelines_path: Optional[Path] = None,
        claude_command: str = "claude",
        enforce_no_stubs: bool = True,
    ):
        """Initialize with Python standards enforcement.

        Args:
            standards: Python standards enforcer
            guidelines_path: Path to guidelines file
            claude_command: Command to invoke Claude
            enforce_no_stubs: If True, strictly enforce no stub implementations
        """
        self.standards = standards or PythonStandards()
        self.guidelines_path = guidelines_path or Path(".claude/Guidelines.md")
        
        # Find claude command in PATH
        if claude_command == "claude":
            found_claude: Optional[str] = shutil.which("claude")
            if found_claude:
                self.claude_command = found_claude
                logger.info(f"Found claude at: {found_claude}")
            else:
                # Fallback to assuming it's in PATH
                self.claude_command = claude_command
                logger.warning("Could not find claude in PATH, using 'claude' and hoping subprocess finds it")
        else:
            self.claude_command = claude_command
            
        self.enforce_no_stubs = enforce_no_stubs
        self.stub_detector = StubDetector(strict_mode=True)
        self.intelligent_detector = IntelligentStubDetector(strict_mode=True)
        self.stub_remediator = None  # Will be set to StubRemediator(self) if needed
        self.prompt_loader = PromptLoader()  # Initialize prompt loader for template management

    def _validate_python_syntax(self, filepath: str, content: str) -> tuple[bool, str]:
        """Validate Python file syntax using ast.parse().
        
        Args:
            filepath: Path to the file (for error reporting)
            content: Python code content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filepath.endswith('.py'):
            return True, ""  # Skip non-Python files
            
        try:
            ast.parse(content)
            return True, ""
        except SyntaxError as e:
            error_msg = f"Syntax error in {filepath} at line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  Problem code: {e.text.strip()}"
            return False, error_msg
        except Exception as e:
            return False, f"Failed to parse {filepath}: {str(e)}"

    def generate(
        self,
        recipe: Recipe,
        context: Optional[BuildContext] = None,
        output_dir: Optional[Path] = None,
    ) -> GeneratedCode:
        """Generate code using Claude Code based on recipe."""
        if context is None:
            context = BuildContext(recipe=recipe)

        generated_files: Dict[str, str] = {}

        if not context.dry_run:
            # Use the provided output directory or create a subdirectory in current directory
            if output_dir:
                # Use output_dir directly, don't create nested generated_* subdirectory
                temp_path = output_dir
            else:
                temp_path = Path.cwd() / f"generated_{recipe.name}"

            # Create the directory if it doesn't exist
            temp_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using output directory: {temp_path}")

            max_iterations = 5  # Prevent infinite loops
            iteration = 0
            all_errors: List[str] = []  # Track ALL errors: syntax, stubs, quality
            syntax_errors: List[str] = []  # Track syntax errors separately
            stub_errors: List[str] = []  # Track stub errors separately
            quality_errors: List[str] = []  # Track pyright/ruff errors
            is_valid = False  # Initialize validation status

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Generation iteration {iteration} for {recipe.name}")

                if iteration == 1:
                    # First iteration: generate from recipe
                    impl_prompt = self._create_generation_prompt_with_path(recipe, temp_path)
                else:
                    # Subsequent iterations: fix ALL issues (syntax, stubs, quality)
                    impl_prompt = self._create_fix_all_issues_prompt(
                        recipe, temp_path, generated_files,
                        syntax_errors, stub_errors, quality_errors
                    )

                # Invoke Claude to write files (pass output_dir for --add-dir)
                self._invoke_claude_code(impl_prompt, recipe, temp_path)

                # Read files that Claude created (and check for syntax errors)
                generated_files, syntax_errors = self._read_generated_files_with_validation(temp_path, recipe)
                
                # Also check alternate location if files not found (handle relative path issues)
                if not generated_files and output_dir:
                    # Check if files were created relative to cwd instead of output_dir
                    alt_path = Path.cwd() / f"generated_{recipe.name}"
                    if alt_path.exists() and alt_path != temp_path:
                        logger.warning(f"Files found in alternate location: {alt_path}")
                        alt_files = self._read_generated_files(alt_path, recipe)
                        if alt_files:
                            generated_files = alt_files
                            # Move files to correct location
                            for filepath, content in alt_files.items():
                                correct_path = temp_path / Path(filepath).name
                                correct_path.parent.mkdir(parents=True, exist_ok=True)
                                correct_path.write_text(content)
                            logger.info(f"Moved {len(alt_files)} files to correct location")

                # Combine all errors for comprehensive validation
                all_errors = []
                
                # Check if any files were generated
                if not generated_files:
                    logger.error(f"No files generated in iteration {iteration}")
                    all_errors = ["No files were generated"]
                    is_valid = False
                else:
                    # Check for syntax errors first
                    if syntax_errors:
                        logger.warning(f"Iteration {iteration} has {len(syntax_errors)} syntax errors")
                        all_errors.extend(syntax_errors)
                        is_valid = False
                    
                    # Check for stubs and TODOs
                    if self.enforce_no_stubs:
                        # Try intelligent detection first (if iteration > 2, use Claude)
                        if iteration > 2:
                            try:
                                logger.info("Using intelligent stub detection with Claude...")
                                has_stubs, stub_errors = self.intelligent_detector.detect_stubs_with_claude(generated_files)
                                is_valid = not has_stubs
                            except Exception as e:
                                logger.warning(f"Intelligent detection failed: {e}, falling back to regex")
                                is_valid, stub_errors = self.stub_detector.validate_no_stubs(generated_files)
                        else:
                            # Use basic detection for early iterations (faster)
                            is_valid, stub_errors = self.stub_detector.validate_no_stubs(generated_files)

                        if not is_valid:
                            all_errors.extend(stub_errors)
                            stub_errors = stub_errors  # Track separately for reporting
                    
                    # Check if all validations passed
                    if not all_errors:
                        logger.info(f"Code generation successful after {iteration} iteration(s)")
                        break
                    else:
                        total_issues = len(all_errors)
                        logger.warning(
                            f"Iteration {iteration} has {total_issues} total issues: {len(syntax_errors)} syntax, {len(stub_errors)} stubs"
                        )
                        print(
                            f"      ⚠️  Iteration {iteration} has {total_issues} issues, requesting fixes..."
                        )

            if iteration >= max_iterations and all_errors:
                error_msg = (
                    f"Failed to generate clean code after {max_iterations} iterations:\n"
                    + f"Syntax errors: {len(syntax_errors)}\n"
                    + f"Stub errors: {len(stub_errors)}\n"
                    + "\n".join(all_errors[:50])  # Limit error output
                )
                raise ClaudeCodeGenerationError(error_msg)

            # Apply Python standards (format with ruff, check with pyright)
            # Don't use UV context since these are temp files not in a project yet
            for file_path in list(generated_files.keys()):
                content = generated_files[file_path]
                formatted = self.standards.format_code_with_ruff(content, use_project_context=False)
                generated_files[file_path] = formatted

            # Step 3: Detect and remediate any stub implementations
            if self.enforce_no_stubs:
                # Use intelligent detection for final validation
                try:
                    logger.info("Final validation using intelligent stub detection...")
                    has_stubs, stub_errors = self.intelligent_detector.detect_stubs_with_claude(generated_files)
                    is_valid = not has_stubs
                except Exception as e:
                    logger.warning(f"Intelligent detection failed in final validation: {e}")
                    is_valid, stub_errors = self.stub_detector.validate_no_stubs(generated_files)

                if not is_valid:
                    # Try to remediate stubs automatically
                    if not self.stub_remediator:
                        from .stub_detector import StubRemediator

                        self.stub_remediator = StubRemediator(self)

                    fixed_files, success, errors = self.stub_remediator.remediate_stubs(  # type: ignore[attr-defined]
                        generated_files, recipe  # type: ignore[arg-type]
                    )

                    if success:
                        generated_files = fixed_files
                    else:
                        error_msg = "Generated code contains stub implementations:\n" + "\n".join(
                            errors
                        )
                        raise ClaudeCodeGenerationError(error_msg)

        # Create GeneratedCode object
        generated = GeneratedCode(
            recipe_name=recipe.name,
            files=generated_files,
            language="python",
            timestamp=datetime.now(),
        )

        # Validate against requirements
        if not context.dry_run and not self._validate_against_requirements(
            generated, recipe.requirements
        ):
            raise ClaudeCodeGenerationError("Generated code doesn't satisfy requirements")

        return generated

    def _create_generation_prompt_with_path(self, recipe: Recipe, output_path: Path) -> str:
        """Create a comprehensive prompt for Claude Code from recipe with output path."""
        # START with clear context about the self-hosting task
        context_header = f"""
# Recipe-Based Code Generation: Self-Hosting Exercise

## CRITICAL CONTEXT: Recipe Executor Self-Hosting

You are participating in a **self-hosting exercise** where the Recipe Executor system is using its own recipe specification to regenerate itself from scratch. This is a test of the Recipe Executor's capability to build software from recipes.

**KEY UNDERSTANDING**:
1. The Recipe Executor (which invoked you) is testing its ability to recreate itself from its recipe
2. You are working in an ISOLATED BUILD DIRECTORY that is separate from the main codebase
3. You must create a NEW, FRESH implementation based solely on the recipe specification
4. DO NOT modify any files outside your working directory
5. This is similar to how a compiler can compile itself - we're using Recipe Executor to build Recipe Executor

## YOUR WORKING DIRECTORY
You are in an isolated build directory. All file operations are relative to this directory.
- Your current working directory is the output directory where you should create all files
- Create the directory structure: src/recipe_executor/ for Python modules, tests/ for test files
- When creating files, use paths like: src/recipe_executor/recipe_model.py
- The recipe files are available in the recipes/ subdirectory if you need to reference them
- DO NOT try to access or modify files outside this directory

## YOUR TASK
Generate a complete, functional implementation of Recipe Executor based on the recipe below.

**Requirements**:
1. Create proper Python package structure (src/, tests/, etc.)
2. Implement ALL components described in the recipe
3. Ensure the implementation is complete and functional
4. Focus on the recipe requirements, not on existing code
5. Test your implementation as needed
6. Use any tools necessary to complete the task

## Recipe Name: {recipe.name}

This is a FRESH implementation. Let the recipe guide your implementation.
"""
        
        base_prompt = context_header + "\n\n" + self._create_generation_prompt(recipe, output_path)
        
        # Add explicit list of required files with exact Write tool usage
        path_instructions = """
## CRITICAL FILE CREATION INSTRUCTIONS

**MANDATORY: You MUST create files using the Write tool with THESE EXACT file_path parameters. Do NOT interpret these as examples - use these EXACT paths:**

**IMPORTANT**: Your current working directory is the isolated build directory. Create all files relative to this directory.

**STEP 1: Create the directory structure and files:**

When creating Python module files, use these exact paths relative to your current directory:
- src/recipe_executor/recipe_model.py
- src/recipe_executor/recipe_parser.py
- src/recipe_executor/__init__.py
- tests/test_recipe_executor.py
- etc.

The files will be created in the correct structure automatically when you use these paths.

## REQUIRED FILES - CREATE WITH EXACT PATHS

You MUST create EVERY file listed below using the Write tool with the EXACT file_path shown:

### 1. Project Configuration Files
```
Write tool with file_path="pyproject.toml"
Write tool with file_path="README.md"
Write tool with file_path=".gitignore"
```

### 2. Package Init Files
```
Write tool with file_path="src/__init__.py"
Write tool with file_path="src/recipe_executor/__init__.py"
Write tool with file_path="tests/__init__.py"
```

### 3. Core Recipe Models (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/recipe_model.py"
Write tool with file_path="src/recipe_executor/recipe_parser.py"
Write tool with file_path="src/recipe_executor/recipe_validator.py"
Write tool with file_path="src/recipe_executor/recipe_decomposer.py"
Write tool with file_path="src/recipe_executor/dependency_resolver.py"
```

### 4. Code Generation Components (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/claude_code_generator.py"
Write tool with file_path="src/recipe_executor/test_generator.py"
Write tool with file_path="src/recipe_executor/test_solver.py"
Write tool with file_path="src/recipe_executor/base_generator.py"
```

### 5. Quality and Review Components (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/code_reviewer.py"
Write tool with file_path="src/recipe_executor/code_review_response.py"
Write tool with file_path="src/recipe_executor/requirements_validator.py"
Write tool with file_path="src/recipe_executor/validator.py"
Write tool with file_path="src/recipe_executor/quality_gates.py"
```

### 6. Stub Detection Components (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/stub_detector.py"
Write tool with file_path="src/recipe_executor/intelligent_stub_detector.py"
```

### 7. Orchestration Components (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/orchestrator.py"
Write tool with file_path="src/recipe_executor/state_manager.py"
Write tool with file_path="src/recipe_executor/parallel_builder.py"
```

### 8. Standards and Utilities (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/python_standards.py"
Write tool with file_path="src/recipe_executor/pattern_manager.py"
Write tool with file_path="src/recipe_executor/prompt_loader.py"
Write tool with file_path="src/recipe_executor/language_detector.py"
Write tool with file_path="src/recipe_executor/uv_environment.py"
```

### 9. Entry Points (MUST CREATE ALL)
```
Write tool with file_path="src/recipe_executor/__main__.py"
Write tool with file_path="src/recipe_executor/cli.py"
```

### 10. Test Files (MUST CREATE ALL)
```
Write tool with file_path="tests/test_recipe_executor.py"
Write tool with file_path="tests/conftest.py"
```

**VALIDATION CHECK**: You MUST create EXACTLY 31 Python files in src/recipe_executor/ directory.

**DO NOT CREATE**:
- Files with different names (e.g., "models.py" instead of "recipe_model.py")
- Files in wrong locations (e.g., root directory instead of src/recipe_executor/)
- Stub files that just import from other files
- Any files not explicitly listed above

**EVERY FILE MUST**:
- Have complete implementation (no pass statements, no NotImplementedError)
- Include proper type hints for all functions
- Have docstrings for all classes and functions
- Pass pyright type checking

**FORBIDDEN PATTERNS - NEVER USE THESE**:
```python
# ❌ NEVER write stubs like this:
def some_method(self):
    pass  # FORBIDDEN!

def another_method(self):
    raise NotImplementedError  # FORBIDDEN!

def third_method(self):
    ...  # FORBIDDEN!

def fourth_method(self):
    return  # FORBIDDEN - empty return!

def fifth_method(self):
    return None  # FORBIDDEN if that's the only line!
```

**REQUIRED PATTERNS - ALWAYS USE THESE**:
```python
# ✅ ALWAYS write complete implementations:
def some_method(self):
    logger.debug("Processing started")
    result = self._process_internal()
    self._validate_result(result)
    return result

def another_method(self):
    if not self.data:
        raise ValueError("No data available")
    processed = [self._transform(item) for item in self.data]
    return ProcessedData(items=processed)
```
"""
        return base_prompt + "\n" + path_instructions

    def _create_fix_stubs_prompt(
        self,
        recipe: Recipe,
        output_path: Path,
        current_files: Dict[str, str],
        stub_errors: List[str],
    ) -> str:
        """Create a prompt to fix stubs and TODOs in existing code using PromptLoader."""
        # Use the path as-is for Claude (don't try to make it relative to cwd)
        rel_output_path = output_path
        
        # Prepare variables for prompt template
        variables = {
            "recipe_name": recipe.name,
            "stub_errors": chr(10).join(
                f"- {error}" for error in stub_errors[:20]
            ),  # First 20 errors
            "output_path": str(rel_output_path),
            "requirements": self._format_requirements(recipe.requirements),
            "design": self._format_design(recipe.design),
        }

        # Use PromptLoader to assemble the prompt with context
        prompt = self.prompt_loader.assemble_prompt(
            template_name="fix_stubs_prompt",
            variables=variables,
            include_context=True,  # Include CRITICAL_GUIDELINES.md
        )

        # Add supplementary documentation if available
        if recipe.metadata.supplementary_docs:
            supp_docs = [
                "\n## Additional Context Documentation\n",
                "The following supplementary documentation provides additional context:\n",
            ]

            for doc_name, doc_content in recipe.metadata.supplementary_docs.items():
                supp_docs.extend(
                    [
                        f"\n### {doc_name}\n",
                        doc_content[:1500],  # Include first 1500 chars
                        "\n",
                    ]
                )

            prompt += "\n".join(supp_docs)

        return prompt

    def _create_fix_all_issues_prompt(
        self,
        recipe: Recipe,
        output_path: Path,
        current_files: Dict[str, str],
        syntax_errors: List[str],
        stub_errors: List[str],
        quality_errors: List[str],
    ) -> str:
        """Create a comprehensive prompt to fix ALL issues: syntax, stubs, and quality."""
        # Use the path as-is for Claude (don't try to make it relative to cwd)
        rel_output_path = output_path
        
        # Prepare comprehensive error summary
        all_issues = []
        
        if syntax_errors:
            all_issues.append("## CRITICAL: Syntax Errors (MUST FIX FIRST)")
            all_issues.append("The following files have syntax errors that prevent them from being imported:")
            for error in syntax_errors[:10]:  # Show first 10
                all_issues.append(f"  - {error}")
            if len(syntax_errors) > 10:
                all_issues.append(f"  ... and {len(syntax_errors) - 10} more syntax errors")
            all_issues.append("")
        
        if stub_errors:
            all_issues.append("## Stub Implementations (MUST REPLACE)")
            all_issues.append("The following stub implementations were detected:")
            for error in stub_errors[:10]:  # Show first 10
                all_issues.append(f"  - {error}")
            if len(stub_errors) > 10:
                all_issues.append(f"  ... and {len(stub_errors) - 10} more stubs")
            all_issues.append("")
        
        if quality_errors:
            all_issues.append("## Quality Issues (MUST RESOLVE)")
            all_issues.append("The following quality issues were detected:")
            for error in quality_errors[:10]:  # Show first 10
                all_issues.append(f"  - {error}")
            if len(quality_errors) > 10:
                all_issues.append(f"  ... and {len(quality_errors) - 10} more quality issues")
            all_issues.append("")
        
        # Prepare variables for prompt template
        variables = {
            "recipe_name": recipe.name,
            "all_issues": chr(10).join(all_issues),
            "output_path": str(rel_output_path),
            "requirements": self._format_requirements(recipe.requirements),
            "design": self._format_design(recipe.design),
            "syntax_count": str(len(syntax_errors)),
            "stub_count": str(len(stub_errors)),
            "quality_count": str(len(quality_errors)),
        }

        # Check if we have a comprehensive fix template, otherwise use fix_stubs_prompt
        template_name = "fix_all_issues_prompt"
        # Try to use fix_all_issues_prompt if it exists, otherwise fall back to fix_stubs_prompt
        try:
            # Try to load the fix_all_issues_prompt template
            from pathlib import Path
            prompts_dir = Path(__file__).parent / "prompts"
            if not (prompts_dir / f"{template_name}.md").exists():
                # Fall back to fix_stubs_prompt but modify variables
                template_name = "fix_stubs_prompt"
                variables["stub_errors"] = variables["all_issues"]
        except Exception:
            # Fall back to fix_stubs_prompt
            template_name = "fix_stubs_prompt"
            variables["stub_errors"] = variables["all_issues"]
        
        # Use PromptLoader to assemble the prompt with context
        prompt = self.prompt_loader.assemble_prompt(
            template_name=template_name,
            variables=variables,
            include_context=True,  # Include CRITICAL_GUIDELINES.md
        )
        
        # Add quality enforcement instructions
        prompt += "\n\n## CRITICAL: Quality Gates MUST Pass\n"
        prompt += "Your implementation MUST:\n"
        prompt += "1. Fix ALL syntax errors first - every file must be valid Python\n"
        prompt += "2. Replace ALL stub implementations with real working code\n"
        prompt += "3. Pass pyright type checking with ZERO errors\n"
        prompt += "4. Be formatted with ruff format\n"
        prompt += "5. Pass ruff check with no linting issues\n"
        prompt += "\nDO NOT return until ALL issues are resolved. This is iteration focused on FIXING issues.\n"
        
        # Add supplementary documentation if available
        if recipe.metadata.supplementary_docs:
            supp_docs = [
                "\n## Additional Context Documentation\n",
                "The following supplementary documentation provides additional context:\n",
            ]

            for doc_name, doc_content in recipe.metadata.supplementary_docs.items():
                supp_docs.extend(
                    [
                        f"\n### {doc_name}\n",
                        doc_content[:1500],  # Include first 1500 chars
                        "\n",
                    ]
                )

            prompt += "\n".join(supp_docs)

        return prompt

    def _create_generation_prompt(self, recipe: Recipe, output_path: Optional[Path] = None) -> str:
        """Create a comprehensive prompt for Claude Code from recipe using PromptLoader."""
        from .language_detector import LanguageDetector, Language

        # Detect target language
        detector = LanguageDetector()
        language = detector.detect_language(recipe.path)
        
        # Check if this is a decomposed/component recipe
        is_component_recipe = self._is_component_recipe(recipe)

        # Use different prompt for component recipes
        if is_component_recipe:
            # Simple direct prompt for component recipes - let Claude read the files
            # Use a default output path if not provided
            if output_path is None:
                output_path = Path(".recipe_build") / "generated"
            prompt = self._create_simple_component_prompt(recipe, output_path)
        else:
            # Prepare variables for prompt template
            variables = {
                "recipe_name": recipe.name,
                "language": language.value.capitalize() if language != Language.UNKNOWN else "Python",
                "requirements": self._format_requirements(recipe.requirements),
                "design": self._format_design(recipe.design),
                "components": self._format_components(recipe.design.components),
                "implementation_notes": recipe.design.implementation_notes or "No additional notes",
                "dependencies": ", ".join(recipe.get_dependencies())
                if recipe.get_dependencies()
                else "None",
                "success_criteria": self._format_success_criteria(recipe.requirements.success_criteria),
            }
            
            # Use PromptLoader to assemble the prompt with context
            prompt = self.prompt_loader.assemble_prompt(
                template_name="generation_prompt",
                variables=variables,
                include_context=True,  # This will include CRITICAL_GUIDELINES.md and Guidelines.md
            )

        # Add supplementary documentation if available
        if recipe.metadata.supplementary_docs:
            supp_docs = [
                "\n## Additional Context Documentation\n",
                "The following supplementary documentation provides additional context:\n",
            ]

            for doc_name, doc_content in recipe.metadata.supplementary_docs.items():
                supp_docs.extend(
                    [
                        f"\n### {doc_name}\n",
                        doc_content[:2000],  # Include first 2000 chars
                        "\n",
                    ]
                )

            prompt += "\n".join(supp_docs)

        # Add self-hosting requirement if applicable
        if recipe.components.is_self_hosting():
            self_hosting = "\n## SELF-HOSTING REQUIREMENT\n"
            self_hosting += (
                "This component MUST be able to regenerate itself from its own recipe.\n"
            )
            # Insert at beginning of prompt after context
            prompt = prompt.replace(
                "# Generate Implementation", self_hosting + "\n# Generate Implementation"
            )

        return prompt

    def _get_default_guidelines(self) -> str:
        """Get default guidelines when file not found."""
        return """### Zero BS Principle
**NO BULLSHIT. NO CLAIMS WITHOUT EVIDENCE. NO FAKE COMPLETIONS.**
- If code doesn't exist, say "NOT IMPLEMENTED"
- If it's a stub, say "STUB ONLY"
- If it's untested, say "UNTESTED"
- NEVER claim something is complete unless it actually works end-to-end

### Core Requirements
1. **Test-Driven Development (TDD)**:
   - FIRST write comprehensive tests based on requirements
   - THEN implement code to make tests pass
   - FINALLY refactor while keeping tests green
2. **Quality Gates**: All code MUST pass `uv run pyright` with ZERO errors
3. **Python Standards**: MUST use UV, ruff formatting, strict pyright
4. **Testing**: Every function needs a test that actually proves it works
5. **Humility**: No performance claims without benchmarks

## MANDATORY: Test-Driven Development Process

You MUST follow this TDD workflow:

1. **STEP 1 - Write Tests First**:
   - Create comprehensive test files in tests/ directory
   - Write tests for ALL requirements (especially MUST requirements)
   - Tests should initially FAIL (since no implementation exists yet)
   - Use pytest with proper fixtures and parameterization
   - Include unit tests AND integration tests

2. **STEP 2 - Implement Code**:
   - Write the minimum code needed to make tests pass
   - Focus on functionality over optimization
   - Ensure all tests turn green

3. **STEP 3 - Refactor**:
   - Improve code quality while keeping tests passing
   - Add type hints, docstrings, error handling
   - Ensure pyright and ruff compliance"""

    def _load_guidelines(self) -> str:
        """Load guidelines from file."""
        if self.guidelines_path.exists():
            return self.guidelines_path.read_text()
        return "# Guidelines not found\n\nUsing default guidelines."

    def _format_requirements(self, requirements: Requirements) -> str:
        """Format requirements for inclusion in prompt."""
        lines: List[str] = [f"**Purpose**: {requirements.purpose}", ""]

        if requirements.functional_requirements:
            lines.append("### Functional Requirements")
            for req in requirements.functional_requirements:
                priority = req.priority.value.upper()
                lines.append(f"- **{req.id}** ({priority}): {req.description}")
                if req.validation_criteria:
                    for criterion in req.validation_criteria:
                        lines.append(f"  - Validation: {criterion}")
            lines.append("")

        if requirements.non_functional_requirements:
            lines.append("### Non-Functional Requirements")
            for req in requirements.non_functional_requirements:
                priority = req.priority.value.upper()
                lines.append(f"- **{req.id}** ({priority}): {req.description}")
                if req.validation_criteria:
                    for criterion in req.validation_criteria:
                        lines.append(f"  - Validation: {criterion}")
            lines.append("")

        if requirements.success_criteria:
            lines.append("### Success Criteria")
            for criterion in requirements.success_criteria:
                lines.append(f"- {criterion}")
            lines.append("")

        return "\n".join(lines)

    def _format_components(self, components: List[ComponentDesign]) -> str:
        """Format component designs for the prompt."""
        lines: List[str] = []
        for component in components:
            lines.append(f"**{component.name}**")
            lines.append(f"{component.description}")
            if component.class_name:
                lines.append(f"- Class: `{component.class_name}`")
            if component.methods:
                lines.append(f"- Methods: {', '.join(component.methods)}")
            if component.code_snippet:
                lines.append("- Reference Implementation:")
                lines.append("```python")
                lines.append(component.code_snippet)
                lines.append("```")
            lines.append("")
        return "\n".join(lines)

    def _format_success_criteria(self, criteria: List[str]) -> str:
        """Format success criteria as a checklist."""
        return "\n".join(f"- {criterion}" for criterion in criteria)

    def _format_design(self, design: Design) -> str:
        """Format design specification for prompt."""
        lines: List[str] = []

        lines.append(f"**Architecture:** {design.architecture}")
        lines.append("")

        if design.components:
            lines.append("**Components:**")
            for component in design.components:
                lines.append(f"- **{component.name}**: {component.description}")
                if component.class_name:
                    lines.append(f"  - Class: `{component.class_name}`")
                if component.methods:
                    lines.append(f"  - Methods: `{'`, `'.join(component.methods)}`")
            lines.append("")

        if design.implementation_notes:
            lines.append(f"**Implementation Notes:** {design.implementation_notes}")
            lines.append("")

        if design.code_blocks:
            lines.append("**Code Examples:**")
            for block in design.code_blocks:
                lines.append("```python")
                lines.append(block)
                lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def _prepare_isolated_environment(self, output_dir: Path, recipe: Recipe, prompt_file: Path) -> None:
        """Prepare an isolated environment for Claude to work in.
        
        This copies necessary context files to the output directory so Claude
        can work in isolation without seeing the existing Recipe Executor code.
        
        Args:
            output_dir: The isolated directory where Claude will work
            recipe: The recipe being built
            prompt_file: The prompt file to copy
        """
        logger.info(f"Preparing isolated environment in {output_dir}")
        
        # Create .claude subdirectory for context
        claude_dir = output_dir / ".claude"
        claude_dir.mkdir(exist_ok=True)
        
        # Copy the Guidelines file if it exists
        if self.guidelines_path.exists():
            target_guidelines = claude_dir / "Guidelines.md"
            shutil.copy2(self.guidelines_path, target_guidelines)
            logger.debug(f"Copied guidelines to {target_guidelines}")
        
        # Copy the prompt file to the isolated directory
        target_prompt = output_dir / "generation_prompt.md"
        shutil.copy2(prompt_file, target_prompt)
        logger.debug(f"Copied prompt to {target_prompt}")
        
        # Copy the recipe files to the isolated environment
        recipes_dir = Path("recipes")
        if recipes_dir.exists():
            target_recipes = output_dir / "recipes"
            if target_recipes.exists():
                shutil.rmtree(target_recipes)
            shutil.copytree(recipes_dir, target_recipes)
            logger.debug(f"Copied recipes directory to {target_recipes}")
        
        # Create a README explaining the context
        readme_content = f"""# Isolated Build Environment for {recipe.name}

This is an isolated build directory for generating a fresh implementation
of {recipe.name} from its recipe specification.

## Important Notes

1. This directory is completely isolated from the main codebase
2. All files should be created relative to this directory
3. Use the Write tool to create new files
4. Do not attempt to access files outside this directory
5. The recipe specification is your sole guide for implementation

## Your Task

Generate a complete implementation based on the recipe specification
provided in generation_prompt.md.

## Directory Structure

Create your implementation with proper Python package structure:
- src/ - Source code
- tests/ - Test files
- Any other directories as needed by the recipe

Remember: This is a self-hosting exercise where Recipe Executor is
rebuilding itself from its own recipe. Focus on the recipe requirements,
not on any existing implementation.
"""
        readme_file = output_dir / "README.md"
        readme_file.write_text(readme_content)
        logger.debug("Created README in isolated directory")
        
    def _invoke_claude_code(self, prompt: str, recipe: Recipe, output_dir: Path) -> str:  # noqa: ARG002
        """Invoke Claude Code CLI to generate implementation.

        Uses Claude's actual CLI interface to generate code based on the recipe.
        NO FALLBACK - must use Claude or fail.
        
        Args:
            prompt: The generation prompt
            recipe: The recipe being generated
            output_dir: The directory where Claude should write files
        """
        logger.info(f"Invoking Claude for {recipe.name}")
        logger.debug(f"Prompt size: {len(prompt)} characters")
        logger.debug(f"Output directory: {output_dir}")

        # Create prompt file in project-relative directory (NOT /tmp)
        # Claude subprocesses need access to write files, so we avoid /tmp
        prompt_dir = Path(".recipe_build/prompts")
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
        # Use timestamp to ensure unique prompt filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_file = prompt_dir / f"prompt_{recipe.name}_{timestamp}.md"
        
        # Write prompt to file in project directory
        prompt_file.write_text(prompt)
        logger.debug(f"Wrote prompt to {prompt_file}")

        try:
            # Build Claude command with all required flags for automation
            model = os.environ.get("CLAUDE_MODEL", "opus")  # Default to opus
            # Use the prompt file from the isolated directory
            isolated_prompt = output_dir / "generation_prompt.md"
            cmd: List[str] = [
                self.claude_command,
                "-p",  # Print mode for non-interactive
                str(isolated_prompt),  # Use prompt from isolated dir
                "--dangerously-skip-permissions",  # Skip ALL permission prompts
                "--output-format",
                "stream-json",  # Stream JSON output for parsing
                "--verbose",  # Required for stream-json output
                "--model",
                model,  # Use specified model
                # NO --allowedTools - Claude should inherit tools from parent context
                # NO --add-dir needed since we're running IN the directory
            ]

            # Execute Claude with the prompt file
            # NO TIMEOUT - Recipe Executor must be patient for complex recipes
            print(f"      🤖 Calling Claude to generate {recipe.name}...")
            print(f"      📝 Prompt size: {len(prompt)} characters")
            print("      ⏳ Waiting for Claude to complete (no timeout - be patient)...")

            logger.info(f"Executing Claude command: {' '.join(cmd)}")

            # Prepare isolated environment for Claude
            # Copy necessary context files to the output directory
            self._prepare_isolated_environment(output_dir, recipe, prompt_file)
            
            # Use Popen to handle streaming JSON output
            # Include current environment to ensure PATH is available
            env = os.environ.copy()
            # Add npm-global bin to PATH if not already there
            npm_bin = os.path.expanduser("~/.npm-global/bin")
            if npm_bin not in env.get("PATH", ""):
                env["PATH"] = f"{npm_bin}:{env.get('PATH', '')}"
            
            # CRITICAL: Run Claude in the isolated output directory
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                env=env,  # Pass environment to find claude in PATH
                cwd=str(output_dir.absolute()),  # Run Claude IN the output directory
            )

            # Read streaming JSON output line by line in real-time with proper non-blocking I/O
            import threading
            import queue
            
            output_lines: List[str] = []
            output_queue: queue.Queue[Optional[str]] = queue.Queue()
            
            # Create Claude-specific log file for better visibility
            claude_log_file = prompt_dir / f"claude_{recipe.name}_{timestamp}.log"
            claude_log = open(claude_log_file, 'w', buffering=1)  # Line buffered
            logger.info(f"Claude output will be logged to: {claude_log_file}")
            print(f"      📋 Claude output log: {claude_log_file}")
            
            def read_output(pipe: Any, q: queue.Queue[Optional[str]]) -> None:
                """Read lines from pipe and put them in queue."""
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            q.put(line)
                        else:
                            break
                finally:
                    q.put(None)  # Signal end of stream
            
            # Start reader thread
            reader_thread = threading.Thread(
                target=read_output,
                args=(process.stdout, output_queue),
                daemon=True
            )
            reader_thread.start()
            
            # Variables for timeout handling (not used but kept for future)
            # last_output_time = time.time()
            # no_output_warnings = 0
            
            if process.stdout:
                while True:
                    try:
                        # Try to get output with a short timeout
                        line = output_queue.get(timeout=1.0)
                        
                        if line is None:
                            # End of stream
                            logger.info("Claude output stream ended")
                            break
                        
                        # Update timeout tracking (not used but kept for future)
                        # last_output_time = time.time()
                        # no_output_warnings = 0
                        output_lines.append(line)
                        
                        # Write to Claude log file
                        claude_log.write(line)
                        claude_log.flush()
                        
                        # Parse JSON events as they come in and emit progress
                        try:
                            event: Dict[str, Any] = json.loads(line.strip())
                            event_type: Optional[str] = event.get("type")  # type: ignore[assignment]

                            if event_type == "assistant" and "tool_use" in str(event.get("message", {})):
                                # Extract tool use information
                                message: Any = event.get("message", {})
                                if isinstance(message, dict):
                                    content_raw = message.get("content", [])  # type: ignore[assignment]
                                    content_list: List[Any] = content_raw if isinstance(content_raw, list) else [content_raw]  # type: ignore[misc]
                                    for item in content_list:
                                        if isinstance(item, dict) and item.get("type") == "tool_use":  # type: ignore[arg-type]
                                            tool_name: str = str(item.get("name", "unknown"))  # type: ignore[arg-type]
                                            tool_input_raw = item.get("input", {})  # type: ignore[assignment]
                                            tool_input: Dict[str, Any] = tool_input_raw if isinstance(tool_input_raw, dict) else {}  # type: ignore[arg-type]
                                            if tool_name == "Write" and "file_path" in tool_input:
                                                file_path: str = str(tool_input["file_path"])
                                                # Extract just the relative path
                                                if "/" in file_path:
                                                    path_parts: List[str] = file_path.split("/")
                                                    # Find and remove the generated_<recipe> directory prefix if present
                                                    rel_path: str = ""
                                                    for i, part in enumerate(path_parts):
                                                        if part.startswith("generated_"):
                                                            rel_path = "/".join(path_parts[i+1:]) if i+1 < len(path_parts) else path_parts[-1]
                                                            break
                                                    else:
                                                        # No generated_ prefix, just use the last part
                                                        rel_path = path_parts[-1]
                                                else:
                                                    rel_path = file_path
                                                print(f"      📝 Creating: {rel_path}")
                                                logger.info(f"Claude creating file: {rel_path}")
                                            else:
                                                print(f"      🔧 Using tool: {tool_name}")
                                                logger.info(f"Claude using tool: {tool_name}")
                            elif event_type == "text":
                                # Log text output from Claude
                                text = event.get("text", "")
                                if text and len(text) > 1:
                                    # Print first 200 chars to console for visibility
                                    if len(text) > 200:
                                        print(f"      💭 Claude: {text[:200]}...")
                                    else:
                                        print(f"      💭 Claude: {text}")
                                    logger.debug(f"Claude output: {text[:100]}")
                        except json.JSONDecodeError:
                            # Not a JSON line, just collect it
                            pass
                        except Exception as e:
                            logger.debug(f"Error parsing event: {e}")
                    
                    except queue.Empty:
                        # No output available, check if process is still alive
                        poll_result = process.poll()
                        if poll_result is not None:
                            # Process has terminated
                            logger.info(f"Claude process terminated with code {poll_result}")
                            break
                        
                        # NO TIMEOUT - Be patient with Claude
                        # Complex recipes may take a long time to process
                        # Continue waiting
                        continue

            # Wait for process to complete and get any remaining output
            process.wait()
            stderr = process.stderr.read() if process.stderr else ""
            stdout = "".join(output_lines)

            logger.debug(f"Claude returned with code {process.returncode}")
            logger.debug(f"Stdout length: {len(stdout) if stdout else 0}")
            logger.debug(f"Stderr length: {len(stderr) if stderr else 0}")

            if process.returncode == 0:
                print("      ✅ Claude completed successfully")
                logger.info(f"Claude successfully generated code for {recipe.name}")
                return stdout
            else:
                # Claude failed - NO FALLBACK, must fail
                error_msg = f"Claude CLI failed with exit code {process.returncode}"
                if stderr:
                    error_msg += f"\nStderr: {stderr}"
                logger.error(f"Claude failed for {recipe.name}: {error_msg}")
                raise ClaudeCodeGenerationError(
                    error_msg, command=" ".join(cmd[:2] + ["<prompt_file>"]), stderr=stderr
                )
        finally:
            # Close Claude log file
            if 'claude_log' in locals():
                try:
                    claude_log.close()  # type: ignore[possibly-unbound]
                except:
                    pass
            
            # Clean up temp file
            if prompt_file.exists():
                prompt_file.unlink()
                logger.debug(f"Cleaned up prompt file {prompt_file}")

    def _to_class_name(self, name: str) -> str:
        """Convert kebab-case to CamelCase."""
        parts = name.split("-")
        return "".join(part.capitalize() for part in parts)
    
    def _is_component_recipe(self, recipe: Recipe) -> bool:
        """Detect if this is a decomposed/component recipe."""
        # Component recipes have certain characteristics:
        # 1. Focused on a single responsibility (e.g., data-models, parser, validation)
        # 2. Fewer dependencies
        # 3. Smaller scope (fewer components)
        # 4. Name patterns like "data-models", "parser", "file-system"
        
        component_indicators = [
            'data-model', 'parser', 'file-system', 'validation',
            'dependency', 'code-gen', 'state', 'quality-tool',
            'execution', 'design-model', 'requirement'
        ]
        
        name_lower = recipe.name.lower()
        
        # Check name patterns
        is_component_name = any(indicator in name_lower for indicator in component_indicators)
        
        # Check scope - component recipes typically have fewer than 10 components
        is_focused_scope = len(recipe.design.components) <= 10
        
        # Check dependencies - component recipes have fewer dependencies
        has_few_deps = len(recipe.get_dependencies()) <= 3
        
        return is_component_name or (is_focused_scope and has_few_deps)
    
    def _create_simple_component_prompt(self, recipe: Recipe, output_path: Path) -> str:
        """Create a simple prompt for component recipes based on requirements and design."""
        abs_output_path = output_path.absolute()
        
        prompt = f"""# Component Implementation Task

## Context
You are implementing a component based on its recipe specification.

Recipe: {recipe.name}
Output Directory: {abs_output_path}/

## Requirements
{self._format_requirements(recipe.requirements)}

## Design
{self._format_design(recipe.design)}

## CRITICAL QUALITY REQUIREMENTS

**ALL GENERATED PYTHON CODE MUST:**
1. ✅ Pass pyright type checking with ZERO errors in strict mode
2. ✅ Be properly formatted according to ruff standards
3. ✅ Include comprehensive type hints for ALL functions, methods, and variables
4. ✅ Use proper Python typing (Optional, List, Dict, Union, etc.)
5. ✅ Handle None values explicitly with Optional types
6. ✅ Have NO stubs, placeholders, or NotImplementedError

## Instructions
1. Analyze the requirements and design above
2. Create all necessary files to satisfy the requirements
3. All files should be created in: {abs_output_path}/
4. Write pyright-compliant code with proper type annotations
5. Follow ruff formatting standards (line length, imports, etc.)

## EXAMPLE OF REQUIRED IMPLEMENTATION QUALITY

Every function MUST have substantive logic like this:

```python
# ❌ FORBIDDEN - This will FAIL:
def validate_recipe(self, recipe: Recipe) -> bool:
    return True  # STUB - FORBIDDEN

# ✅ REQUIRED - Real implementation:
def validate_recipe(self, recipe: Recipe) -> bool:
    errors = []
    
    # Check required fields
    if not recipe.name:
        errors.append("Recipe name is required")
    if not recipe.path or not recipe.path.exists():
        errors.append(f"Recipe path does not exist: {{recipe.path}}")
    
    # Validate requirements
    if not recipe.requirements:
        errors.append("Recipe must have requirements")
    else:
        if not recipe.requirements.purpose:
            errors.append("Requirements must have a purpose")
        if not recipe.requirements.functional_requirements:
            errors.append("At least one functional requirement is needed")
    
    # Validate design
    if not recipe.design:
        errors.append("Recipe must have a design")
    elif not recipe.design.components:
        errors.append("Design must have at least one component")
    
    # Log any errors found
    if errors:
        logger.error(f"Recipe validation failed: {{errors}}")
        return False
    
    logger.info(f"Recipe {{recipe.name}} validated successfully")
    return True
```

## IMPLEMENTATION PATTERNS TO USE

### For Validation Functions:
- Check all required fields exist
- Validate data types and formats
- Check business rules and constraints
- Log errors with context
- Return detailed results

### For Processing Functions:
- Parse and transform input data
- Apply business logic and calculations
- Handle edge cases and errors
- Update state or generate output
- Log processing steps

### For Model Classes:
- Include validation in __init__ or validators
- Add computed properties with logic
- Include serialization/deserialization
- Add helper methods with functionality
- Include proper __str__ and __repr__

## FORBIDDEN PATTERNS
```python
# ALL OF THESE ARE FORBIDDEN:
def process(self, data):
    pass  # NO!

def validate(self, item):
    return True  # NO!

def transform(self, input):
    return input  # NO!

def calculate(self, values):
    return {{}}  # NO!
    
class MyClass:
    pass  # NO!
```

## START IMMEDIATELY
1. Read the recipe files NOW
2. Generate COMPLETE implementations
3. Every function must have REAL logic
4. NO STUBS, NO PLACEHOLDERS

Use Read tool to read the recipe files, then Write tool to create the Python files.
DO NOT use any other tools. Start reading the recipe files immediately.
"""
        return prompt

    def _parse_and_write_files(
        self, claude_output: str, output_path: Path, recipe: Recipe
    ) -> Dict[str, str]:
        """Parse Claude's output for file blocks and write them to disk."""
        generated_files: Dict[str, str] = {}

        logger.info(f"Parsing Claude's output ({len(claude_output)} chars)")

        # Parse output looking for file markers
        lines = claude_output.split("\n")
        current_file = None
        current_content: List[str] = []
        in_code_block = False

        for line in lines:
            # Check for file header like "### File: path/to/file.py"
            if (
                line.startswith("### File:")
                or line.startswith("## File:")
                or line.startswith("File:")
            ):
                # Save previous file if exists
                if current_file and current_content:
                    file_content: str = "\n".join(current_content)
                    generated_files[current_file] = file_content

                    # Write to disk
                    full_path = output_path / current_file
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(file_content)
                    logger.debug(f"Wrote file: {current_file} ({len(file_content)} chars)")

                # Start new file
                current_file = line.split(":", 1)[1].strip()
                current_content: List[str] = []
                in_code_block = False

            # Check for code block start
            elif line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    # Language could be extracted here if needed: line[3:].strip()
                else:
                    in_code_block = False

            # Add content if we're in a code block for a file
            elif in_code_block and current_file:
                current_content.append(line)

        # Save last file if exists
        if current_file and current_content:
            file_content: str = "\n".join(current_content)
            generated_files[current_file] = file_content

            # Write to disk
            full_path = output_path / current_file
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file_content)
            logger.debug(f"Wrote file: {current_file} ({len(file_content)} chars)")

        logger.info(f"Parsed and wrote {len(generated_files)} files")
        return generated_files

    def _read_generated_files(self, output_path: Path, recipe: Recipe) -> Dict[str, str]:
        """Read all files that Claude generated in the output directory."""
        generated_files: Dict[str, str] = {}

        logger.info(f"Reading generated files from {output_path}")

        # Walk through the directory and read all files
        for file_path in output_path.rglob("*"):
            if file_path.is_file():
                # Get relative path from output directory
                rel_path = file_path.relative_to(output_path)

                # Skip common non-source files
                if file_path.suffix in [".pyc", ".pyo", ".pyd", ".so", ".dll"]:
                    continue
                if "__pycache__" in str(rel_path):
                    continue

                try:
                    content = file_path.read_text()
                    
                    # Validate Python syntax before accepting the file
                    if file_path.suffix == '.py':
                        is_valid, error_msg = self._validate_python_syntax(str(rel_path), content)
                        if not is_valid:
                            logger.error(f"Syntax validation failed: {error_msg}")
                            # Skip files with syntax errors to prevent ruff formatting failures
                            continue
                    
                    generated_files[str(rel_path)] = content
                    logger.debug(f"Read file: {rel_path} ({len(content)} chars)")
                except Exception as e:
                    logger.warning(f"Could not read file {rel_path}: {e}")

        logger.info(f"Read {len(generated_files)} files from {output_path}")
        return generated_files
    
    def _read_generated_files_with_validation(self, output_path: Path, recipe: Recipe) -> tuple[Dict[str, str], List[str]]:
        """Read all files and track syntax errors instead of skipping them."""
        generated_files: Dict[str, str] = {}
        syntax_errors: List[str] = []

        logger.info(f"Reading generated files from {output_path}")

        # Walk through the directory and read all files
        for file_path in output_path.rglob("*"):
            if file_path.is_file():
                # Get relative path from output directory
                rel_path = file_path.relative_to(output_path)

                # Skip common non-source files
                if file_path.suffix in [".pyc", ".pyo", ".pyd", ".so", ".dll"]:
                    continue
                if "__pycache__" in str(rel_path):
                    continue

                try:
                    content = file_path.read_text()
                    
                    # Validate Python syntax and track errors
                    if file_path.suffix == '.py':
                        is_valid, error_msg = self._validate_python_syntax(str(rel_path), content)
                        if not is_valid:
                            syntax_errors.append(f"SYNTAX ERROR: {error_msg}")
                            # Still include the file so Claude can fix it
                    
                    generated_files[str(rel_path)] = content
                    logger.debug(f"Read file: {rel_path} ({len(content)} chars)")
                except Exception as e:
                    logger.warning(f"Could not read file {rel_path}: {e}")

        logger.info(f"Read {len(generated_files)} files with {len(syntax_errors)} syntax errors")
        return generated_files, syntax_errors

    def _parse_generated_files(self, claude_output: str, recipe: Recipe) -> Dict[str, str]:
        """Parse files from Claude output."""
        generated_files: Dict[str, str] = {}

        # Parse output to extract generated files
        # This is a simplified parser - actual implementation would be more robust
        lines = claude_output.split("\n")
        current_file = None
        current_content: List[str] = []
        in_code_block = False

        for line in lines:
            if "Creating file:" in line or "File:" in line:
                # Save previous file if exists
                if current_file and current_content:
                    generated_files[current_file] = "\n".join(current_content)
                # Start new file
                file_path = line.split(":", 1)[1].strip()
                # Normalize path - ensure it's relative to the recipe
                if not file_path.startswith("src/") and not file_path.startswith("tests/"):
                    # If path doesn't have proper prefix, add it
                    if file_path.startswith(f"{recipe.name}/"):
                        # Recipe-relative path, normalize it
                        file_path = file_path.replace(
                            f"{recipe.name}/", f"src/{recipe.name.replace('-', '_')}/"
                        )
                    elif "/" not in file_path:
                        # Simple filename, put in recipe src dir
                        file_path = f"src/{recipe.name.replace('-', '_')}/{file_path}"
                current_file = file_path
                current_content: List[str] = []
                in_code_block = False
            elif line.strip() == "```python" or line.strip() == "```":
                in_code_block = not in_code_block
            elif in_code_block and current_file:
                current_content.append(line)

        # Save last file
        if current_file and current_content:
            generated_files[current_file] = "\n".join(current_content)

        return generated_files

    def _validate_against_requirements(
        self, code: GeneratedCode, requirements: Requirements
    ) -> bool:
        """Validate generated code satisfies requirements."""
        # Simple validation - in practice would be more sophisticated
        if not code.files:
            return False

        # Check that all MUST requirements have corresponding code
        all_code = " ".join(code.files.values()).lower()

        for req in requirements.get_must_requirements():
            # Simple heuristic: key requirement words should appear in code
            req_keywords = req.description.lower().split()[:5]

            # At least half of the keywords should be in the code
            matches = sum(1 for keyword in req_keywords if keyword in all_code)
            if matches < len(req_keywords) // 2:
                return False

        return True

    def _validate_generated_code(self, files: Dict[str, str]) -> bool:
        """Validate that generated code is non-empty and valid."""
        if not files:
            return False

        # Check that we have actual code content
        for content in files.values():
            if content.strip():
                return True

        return False

    def _create_tdd_test_prompt(self, recipe: Recipe) -> str:
        """Create a prompt specifically for generating tests first (TDD)."""
        prompt = f"""# Generate Tests for {recipe.name}

## Test-Driven Development (TDD) Approach

You are implementing Test-Driven Development. Your task is to:
1. Write comprehensive tests based on the requirements below
2. Tests should cover ALL functional and non-functional requirements
3. Tests should initially be expected to FAIL (since no implementation exists yet)
4. Use pytest with proper fixtures and parameterization

## Requirements to Test

{self._format_requirements(recipe.requirements)}

## Design Components to Test

{self._format_components(recipe.design.components)}

## Test Structure Required

Create test files that:
- Test each requirement with specific test cases
- Use proper pytest fixtures for setup
- Include both unit tests and integration tests
- Have clear, descriptive test names
- Include edge cases and error conditions

Generate comprehensive test coverage for all requirements.
"""
        return prompt

    def _create_implementation_prompt(self, recipe: Recipe, test_files: Dict[str, str]) -> str:
        """Create a prompt for implementing code to pass existing tests."""
        prompt = f"""# Implement Code to Pass Tests for {recipe.name}

## Your Task

Implement the code needed to make all the following tests pass.

## Existing Tests

"""
        for file_path, content in test_files.items():
            prompt += f"\n### {file_path}\n```python\n{content}\n```\n"

        prompt += f"""

## Requirements

{self._format_requirements(recipe.requirements)}

## Design Specification

{self._format_design(recipe.design)}

## Implementation Guidelines

1. Write the minimal code needed to make tests pass
2. Follow the design specification closely
3. Use proper type hints throughout
4. Ensure all tests pass (make all tests pass)
5. No stub implementations - everything must work

Generate the implementation that makes all tests pass.
"""
        return prompt
