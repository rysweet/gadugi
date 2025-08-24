"""Claude Code generator for AI-powered code generation using TDD."""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .recipe_model import Recipe, Requirement
from .python_standards import PythonStandards

logger = logging.getLogger(__name__)


class ClaudeCodeGenerationError(Exception):
    """Error during Claude code generation."""
    pass


@dataclass
class BuildContext:
    """Context for building a recipe."""
    recipe: Recipe
    dependencies: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    verbose: bool = False
    output_dir: Optional[Path] = None
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """Get a built dependency by name."""
        return self.dependencies.get(name)
    
    def has_dependency(self, name: str) -> bool:
        """Check if a dependency is available."""
        return name in self.dependencies


@dataclass
class GeneratedCode:
    """Container for generated code files."""
    recipe_name: str
    files: Dict[str, str]  # filepath -> content
    tests: Dict[str, str]  # test filepath -> content
    language: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_files(self) -> Dict[str, str]:
        """Get all files including tests."""
        all_files = dict(self.files)
        all_files.update(self.tests)
        return all_files
    
    def get_main_files(self) -> List[str]:
        """Get main implementation files (not tests)."""
        return [f for f in self.files.keys() if not f.startswith('test')]
    
    def get_test_files(self) -> List[str]:
        """Get test files."""
        return list(self.tests.keys())
    
    def write_to_disk(self, output_dir: Path):
        """Write all generated files to disk."""
        for filepath, content in self.get_all_files().items():
            full_path = output_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)


class ClaudeCodeGenerator:
    """Generates code using Claude Code CLI with TDD approach."""
    
    def __init__(self, claude_command: str = "claude"):
        """Initialize the generator.
        
        Args:
            claude_command: Command to invoke Claude CLI
        """
        self.claude_command = claude_command
        self.standards = PythonStandards()
        self.context_dir = Path("context")
        self.prompts_dir = Path("prompts")
        
    def generate(self, recipe: Recipe, context: BuildContext) -> GeneratedCode:
        """Generate code using TDD methodology.
        
        Args:
            recipe: Recipe to generate code for
            context: Build context with dependencies
            
        Returns:
            Generated code and tests
            
        Raises:
            ClaudeCodeGenerationError: If generation fails
        """
        logger.info(f"Starting TDD code generation for {recipe.name}")
        
        # Determine output directory
        output_dir = context.output_dir or Path(f".recipe_build/{recipe.name}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate comprehensive tests first (TDD Red phase)
        logger.info("Phase 1: Generating tests (TDD Red)")
        test_prompt = self._create_tdd_test_prompt(recipe, context)
        test_files = self._invoke_claude_for_tests(test_prompt, output_dir)
        
        # Step 2: Generate implementation to pass tests (TDD Green phase)
        logger.info("Phase 2: Generating implementation (TDD Green)")
        impl_prompt = self._create_implementation_prompt(recipe, test_files, context)
        impl_files = self._invoke_claude_for_implementation(impl_prompt, output_dir)
        
        # Step 3: Apply Python standards (TDD Refactor phase)
        logger.info("Phase 3: Applying standards (TDD Refactor)")
        all_files = self._apply_standards(impl_files)
        
        # Create GeneratedCode object
        generated = GeneratedCode(
            recipe_name=recipe.name,
            files=all_files,
            tests=test_files,
            language=recipe.design.language,
            timestamp=datetime.now(),
            metadata={
                "tdd_approach": True,
                "standards_applied": True,
                "recipe_version": recipe.components.version
            }
        )
        
        # Validate generated code satisfies requirements
        if not context.dry_run:
            self._validate_against_requirements(generated, recipe.requirements)
        
        logger.info(f"Successfully generated code for {recipe.name}")
        return generated
    
    def _create_tdd_test_prompt(self, recipe: Recipe, context: BuildContext) -> str:
        """Create prompt for generating tests first (TDD approach).
        
        Args:
            recipe: Recipe to generate tests for
            context: Build context
            
        Returns:
            Test generation prompt
        """
        prompt = f"""# Generate Tests for {recipe.name}

## CRITICAL: NO TIMEOUTS WHEN INVOKING CLAUDE CODE

When calling this as a subprocess, NEVER use timeouts. Let Claude complete its work.

## Test-Driven Development (TDD) Approach

You are following TDD methodology. Generate comprehensive tests FIRST that will initially FAIL.
These tests will drive the implementation.

## Requirements to Test

{self._format_requirements(recipe.requirements)}

## Success Criteria
{self._format_success_criteria(recipe.requirements.success_criteria)}

## Component Designs to Test

{self._format_component_designs(recipe.design.components)}

## Test Guidelines

1. Create pytest-compatible test files
2. Test ALL MUST requirements with specific test cases
3. Include unit tests for each component
4. Include integration tests for component interactions
5. Use fixtures and parameterized tests where appropriate
6. Tests should be comprehensive enough to drive implementation
7. Include edge cases and error conditions
8. Test both positive and negative scenarios
9. Include performance tests for critical paths
10. Add docstrings explaining what each test validates

## Test Structure

Create test files following this structure:
- tests/test_{component_name}.py for each component
- tests/test_integration.py for integration tests
- tests/test_requirements.py for requirement validation
- tests/conftest.py for shared fixtures

## Expected Test Coverage

- Every MUST requirement: At least 2 test cases
- Every component method: At least 1 test
- Every error condition: Explicit test
- Integration paths: End-to-end tests

## Output Location

Write all test files to: {context.output_dir or f'.recipe_build/{recipe.name}'}/tests/

Generate test files that will fail initially (since no implementation exists yet).
Make tests specific, measurable, and directly tied to requirements.
"""
        
        # Add critical guidelines
        prompt = self._add_critical_guidelines(prompt)
        
        return prompt
    
    def _create_implementation_prompt(self, recipe: Recipe, test_files: Dict[str, str], 
                                     context: BuildContext) -> str:
        """Create prompt for implementing code to pass tests.
        
        Args:
            recipe: Recipe to implement
            test_files: Generated test files
            context: Build context
            
        Returns:
            Implementation prompt
        """
        prompt = f"""# Implement Code to Pass Tests for {recipe.name}

## CRITICAL: COMPLETE IMPLEMENTATION REQUIRED

NO STUBS, NO PLACEHOLDERS, NO TODOs. Every function must be fully implemented.

## Your Task

Implement the code needed to make all the following tests pass.

## Existing Tests

{self._format_test_files(test_files)}

## Requirements

{self._format_requirements(recipe.requirements)}

## Design Specification

{self._format_design(recipe.design)}

## Implementation Guidelines

1. Write the minimal code needed to make tests pass
2. Follow the design specification closely
3. Use proper type hints throughout
4. Ensure all tests pass (make all tests green)
5. No stub implementations - everything must work
6. Include comprehensive error handling
7. Add logging for debugging and monitoring
8. Follow Python best practices
9. Make code production-ready

## Code Structure

Implement the following structure:
- src/{recipe.name}/__init__.py - Package initialization
- src/{recipe.name}/*.py - Component implementations
- src/{recipe.name}/models.py - Data models if needed
- src/{recipe.name}/utils.py - Utility functions if needed

## Dependencies Available

{self._format_dependencies(context.dependencies)}

## Output Location

Write all implementation files to: {context.output_dir or f'.recipe_build/{recipe.name}'}/src/

Generate the implementation that makes all tests pass.
Every method must have real logic, no placeholders.
"""
        
        # Add critical guidelines
        prompt = self._add_critical_guidelines(prompt)
        
        return prompt
    
    def _invoke_claude_for_tests(self, prompt: str, output_dir: Path) -> Dict[str, str]:
        """Invoke Claude to generate test files.
        
        Args:
            prompt: Test generation prompt
            output_dir: Directory to write files to
            
        Returns:
            Dictionary of test file paths to content
        """
        # Create test output directory
        test_dir = output_dir / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Invoke Claude CLI
        self._invoke_claude_code(prompt, test_dir)
        
        # Read generated test files
        test_files = {}
        for test_file in test_dir.glob("**/*.py"):
            relative_path = test_file.relative_to(output_dir)
            test_files[str(relative_path)] = test_file.read_text()
        
        return test_files
    
    def _invoke_claude_for_implementation(self, prompt: str, output_dir: Path) -> Dict[str, str]:
        """Invoke Claude to generate implementation files.
        
        Args:
            prompt: Implementation prompt
            output_dir: Directory to write files to
            
        Returns:
            Dictionary of file paths to content
        """
        # Create src output directory
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Invoke Claude CLI
        self._invoke_claude_code(prompt, src_dir)
        
        # Read generated implementation files
        impl_files = {}
        for impl_file in src_dir.glob("**/*.py"):
            relative_path = impl_file.relative_to(output_dir)
            impl_files[str(relative_path)] = impl_file.read_text()
        
        return impl_files
    
    def _invoke_claude_code(self, prompt: str, output_dir: Path):
        """Invoke Claude CLI for code generation with proper automation flags.
        
        CRITICAL: NO TIMEOUTS - Let Claude complete its work
        
        Args:
            prompt: Generation prompt
            output_dir: Directory for output files
        """
        # Add output directory instruction to prompt
        prompt += f"\n\nIMPORTANT: Write all files to: {output_dir.absolute()}"
        
        # Write prompt to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(prompt)
            prompt_file = Path(f.name)
        
        try:
            # Get model from environment or use default
            model = os.environ.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
            
            # Build command
            cmd = [
                self.claude_command,
                "-p", str(prompt_file),
                "--dangerously-skip-permissions",
                "--output-format", "stream-json",
                "--verbose",
                "--model", model,
                "--allowedTools", "Write", "Edit", "MultiEdit", "Bash", "Read"
            ]
            
            logger.info(f"Invoking Claude with command: {' '.join(cmd)}")
            
            # Run Claude WITHOUT timeout - let it complete
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                # NO timeout parameter - Claude needs time to work
                check=False  # Don't raise on non-zero exit
            )
            
            # Process output
            if result.returncode != 0:
                logger.error(f"Claude returned non-zero exit code: {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                
                # Check for specific error conditions
                if "rate limit" in result.stderr.lower():
                    raise ClaudeCodeGenerationError("Claude API rate limit exceeded. Please wait and retry.")
                elif "authentication" in result.stderr.lower():
                    raise ClaudeCodeGenerationError("Claude authentication failed. Check API credentials.")
                else:
                    raise ClaudeCodeGenerationError(f"Claude Code failed: {result.stderr}")
            
            # Parse streaming JSON output to monitor progress
            if result.stdout:
                for line in result.stdout.splitlines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            if event.get('type') == 'tool_use':
                                tool_name = event.get('name', 'unknown')
                                logger.debug(f"Claude using tool: {tool_name}")
                            elif event.get('type') == 'error':
                                logger.error(f"Claude error: {event.get('message')}")
                        except json.JSONDecodeError:
                            # Not JSON, might be plain output
                            logger.debug(f"Claude output: {line[:100]}")
            
            logger.info("Claude code generation completed successfully")
            
        finally:
            # Clean up prompt file
            prompt_file.unlink(missing_ok=True)
    
    def _apply_standards(self, files: Dict[str, str]) -> Dict[str, str]:
        """Apply Python standards to generated code.
        
        Args:
            files: Generated files
            
        Returns:
            Files with standards applied
        """
        formatted_files = {}
        
        for filepath, content in files.items():
            if filepath.endswith('.py'):
                # Apply formatting
                try:
                    formatted_content = self.standards.format_code_with_ruff(content)
                    formatted_files[filepath] = formatted_content
                except Exception as e:
                    logger.warning(f"Could not format {filepath}: {e}")
                    formatted_files[filepath] = content
            else:
                formatted_files[filepath] = content
        
        return formatted_files
    
    def _validate_against_requirements(self, generated: GeneratedCode, requirements):
        """Validate generated code satisfies requirements.
        
        Args:
            generated: Generated code
            requirements: Recipe requirements
            
        Raises:
            ClaudeCodeGenerationError: If requirements not satisfied
        """
        # Basic validation - check that key files exist
        if not generated.files:
            raise ClaudeCodeGenerationError("No implementation files generated")
        
        if not generated.tests:
            raise ClaudeCodeGenerationError("No test files generated")
        
        # Check for stub implementations
        for filepath, content in generated.files.items():
            if self._contains_stubs(content):
                raise ClaudeCodeGenerationError(f"File {filepath} contains stub implementations")
    
    def _contains_stubs(self, content: str) -> bool:
        """Check if code contains stub implementations.
        
        Args:
            content: File content
            
        Returns:
            True if stubs detected
        """
        stub_indicators = [
            'pass  # TODO',
            'raise NotImplementedError',
            '# TODO: implement',
            'return None  # placeholder',
            '...  # stub'
        ]
        
        for indicator in stub_indicators:
            if indicator in content:
                return True
        
        # Check for functions with only pass
        import ast
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        return True
        except:
            # If parsing fails, assume it might have issues
            pass
        
        return False
    
    def _format_requirements(self, requirements) -> str:
        """Format requirements for prompt."""
        lines = []
        
        lines.append("### Functional Requirements")
        for req in requirements.functional_requirements:
            lines.append(f"- {req.priority.value} {req.description}")
            for criterion in req.validation_criteria:
                lines.append(f"  - Validation: {criterion}")
        
        lines.append("\n### Non-Functional Requirements")
        for req in requirements.non_functional_requirements:
            lines.append(f"- {req.priority.value} {req.description}")
            for criterion in req.validation_criteria:
                lines.append(f"  - Validation: {criterion}")
        
        return '\n'.join(lines)
    
    def _format_success_criteria(self, criteria: List[str]) -> str:
        """Format success criteria for prompt."""
        lines = []
        for i, criterion in enumerate(criteria, 1):
            lines.append(f"{i}. {criterion}")
        return '\n'.join(lines)
    
    def _format_component_designs(self, components) -> str:
        """Format component designs for prompt."""
        lines = []
        
        for comp in components:
            lines.append(f"\n### {comp.name}")
            lines.append(f"Description: {comp.description}")
            
            if comp.class_name:
                lines.append(f"Class: `{comp.class_name}`")
            
            if comp.methods:
                lines.append("Methods:")
                for method in comp.methods:
                    lines.append(f"- `{method}`")
            
            if comp.properties:
                lines.append("Properties:")
                for prop in comp.properties:
                    lines.append(f"- `{prop}`")
        
        return '\n'.join(lines)
    
    def _format_test_files(self, test_files: Dict[str, str]) -> str:
        """Format test files for prompt."""
        lines = []
        
        for filepath, content in test_files.items():
            lines.append(f"\n### {filepath}")
            lines.append("```python")
            # Include first 100 lines of each test file
            content_lines = content.split('\n')[:100]
            lines.extend(content_lines)
            if len(content.split('\n')) > 100:
                lines.append("# ... (truncated)")
            lines.append("```")
        
        return '\n'.join(lines)
    
    def _format_design(self, design) -> str:
        """Format design specification for prompt."""
        lines = []
        
        lines.append(f"### Architecture")
        lines.append(design.architecture)
        
        lines.append("\n### Components")
        for comp in design.components:
            lines.append(f"\n**{comp.name}**")
            lines.append(comp.description)
            
            if comp.code_snippet:
                lines.append("```python")
                lines.append(comp.code_snippet)
                lines.append("```")
        
        if design.implementation_notes:
            lines.append("\n### Implementation Notes")
            lines.append(design.implementation_notes)
        
        return '\n'.join(lines)
    
    def _format_dependencies(self, dependencies: Dict[str, Any]) -> str:
        """Format available dependencies for prompt."""
        if not dependencies:
            return "No dependencies required."
        
        lines = ["The following dependencies have been built and are available:"]
        for name, dep in dependencies.items():
            lines.append(f"- {name}: Available for import")
        
        return '\n'.join(lines)
    
    def _add_critical_guidelines(self, prompt: str) -> str:
        """Add critical guidelines to prompt."""
        guidelines_path = self.context_dir / "CRITICAL_GUIDELINES.md"
        if guidelines_path.exists():
            guidelines = guidelines_path.read_text()
            prompt = guidelines + "\n\n" + prompt
        
        # Add project guidelines
        project_guidelines_path = Path(".claude/Guidelines.md")
        if project_guidelines_path.exists():
            project_guidelines = project_guidelines_path.read_text()
            prompt += "\n\n" + project_guidelines
        
        return prompt