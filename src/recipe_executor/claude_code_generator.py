"""Code generation using Claude Code CLI."""

from typing import Optional, Dict, List
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime

from .recipe_model import Recipe, GeneratedCode, BuildContext, Requirements, ComponentDesign, Design
from .python_standards import PythonStandards


class ClaudeCodeGenerationError(Exception):
    """Raised when Claude Code generation fails."""
    pass


class ClaudeCodeGenerator:
    """Generates code from recipes using Claude Code CLI."""
    
    def __init__(self, standards: Optional[PythonStandards] = None, guidelines_path: Optional[Path] = None, claude_command: str = "claude"):
        """Initialize with Python standards enforcement."""
        self.standards = standards or PythonStandards()
        self.guidelines_path = guidelines_path or Path(".claude/Guidelines.md")
        self.claude_command = claude_command
    
    def generate(self, recipe: Recipe, context: Optional[BuildContext] = None) -> GeneratedCode:
        """Generate code using Claude Code based on recipe (TDD approach)."""
        if context is None:
            context = BuildContext(recipe=recipe)
        
        generated_files: Dict[str, str] = {}
        
        if not context.dry_run:
            # Step 1: Generate tests first (TDD)
            test_prompt = self._create_tdd_test_prompt(recipe)
            test_output = self._invoke_claude_code(test_prompt, recipe)
            test_files = self._parse_generated_files(test_output, recipe)
            
            # Step 2: Generate implementation to pass tests
            impl_prompt = self._create_implementation_prompt(recipe, test_files)
            impl_output = self._invoke_claude_code(impl_prompt, recipe)
            impl_files = self._parse_generated_files(impl_output, recipe)
            
            # Combine test and implementation files
            generated_files.update(test_files)
            generated_files.update(impl_files)
            
            # Apply Python standards (format with ruff, check with pyright)
            for file_path in list(generated_files.keys()):
                content = generated_files[file_path]
                formatted = self.standards.format_code_with_ruff(content)
                generated_files[file_path] = formatted
        
        # Create GeneratedCode object
        generated = GeneratedCode(
            recipe_name=recipe.name,
            files=generated_files,
            language="python",
            timestamp=datetime.now()
        )
        
        # Validate against requirements
        if not context.dry_run and not self._validate_against_requirements(generated, recipe.requirements):
            raise ClaudeCodeGenerationError("Generated code doesn't satisfy requirements")
        
        return generated
    
    def _create_generation_prompt(self, recipe: Recipe) -> str:
        """Create a comprehensive prompt for Claude Code from recipe."""
        guidelines = self._load_guidelines()
        
        prompt_parts: List[str] = [
            f"# Generate Implementation for {recipe.name}",
            "",
            "## CRITICAL: Development Guidelines (from Guidelines.md)",
            "",
            guidelines if guidelines else self._get_default_guidelines(),
            "",
            "## Context",
            "You are implementing a component based on the following recipe. Generate production-quality Python code that:",
            "1. Satisfies ALL requirements listed below",
            "2. Follows the design specification",
            "3. Uses UV for package management",
            "4. Passes strict pyright type checking with ZERO errors",
            "5. Is formatted with ruff",
            "6. Includes comprehensive docstrings",
            "7. NO STUBS - real implementations only",
            "",
            "## Requirements",
            "",
            self._format_requirements(recipe.requirements),
            "",
            "## Design Specification",
            "",
            self._format_design(recipe.design),
            "",
            "### Components to Implement",
            "",
            self._format_components(recipe.design.components),
            "",
            "### Implementation Notes",
            "",
            recipe.design.implementation_notes or "No additional notes",
            "",
            "## Python Standards",
            "",
            "- MUST use type hints for all functions and methods",
            "- MUST pass strict pyright checking with zero errors",
            "- MUST be formatted with ruff",
            "- MUST include docstrings for all classes and functions",
            "- MUST handle errors appropriately",
            "- MUST NOT use Any type unless absolutely necessary",
            "",
            "## Output Structure",
            "",
            "Generate files in the following structure:",
            f"- src/{recipe.name.replace('-', '_')}/",
            "  - __init__.py (with proper exports)",
            "  - One .py file per component",
            "  - All necessary type stubs",
            "",
            "## Dependencies",
            "",
            f"This recipe depends on: {', '.join(recipe.get_dependencies()) if recipe.get_dependencies() else 'None'}",
            "",
            "## Success Criteria",
            "",
            self._format_success_criteria(recipe.requirements.success_criteria),
            "",
            "## Additional Instructions",
            "",
            "- Follow the Zero BS Principle: no stubs, no placeholders, real working implementations",
            "- If you need to import from other recipes/modules, use proper relative imports",
            "- Ensure all code is production-ready, not prototypes",
            "- Include proper error handling and logging where appropriate",
        ]
        
        # Add self-hosting requirement if applicable
        if recipe.components.is_self_hosting():
            prompt_parts.insert(2, "## SELF-HOSTING REQUIREMENT")
            prompt_parts.insert(3, "This component MUST be able to regenerate itself from its own recipe.")
            prompt_parts.insert(4, "")
        
        return '\n'.join(prompt_parts)
    
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
        return ""
    
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
        
        return '\n'.join(lines)
    
    def _format_components(self, components: List[ComponentDesign]) -> str:
        """Format component designs for the prompt."""
        lines: List[str] = []
        for component in components:
            lines.append(f"**{component.name}**")
            lines.append(f"{component.description}")
            if component.class_name:
                lines.append(f"- Class Name: `{component.class_name}`")
            if component.methods:
                lines.append(f"- Methods: {', '.join(component.methods)}")
            if component.code_snippet:
                lines.append("- Reference Implementation:")
                lines.append("```python")
                lines.append(component.code_snippet)
                lines.append("```")
            lines.append("")
        return '\n'.join(lines)
    
    def _format_success_criteria(self, criteria: List[str]) -> str:
        """Format success criteria as a checklist."""
        return '\n'.join(f"- {criterion}" for criterion in criteria)
    
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
        
        return '\n'.join(lines)
    
    def _invoke_claude_code(self, prompt: str, recipe: Recipe) -> str:
        """Use Claude Code CLI to generate implementation."""
        # Create temporary directory for operation
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_file = Path(tmpdir) / "prompt.md"
            prompt_file.write_text(prompt)
            
            # Build Claude Code command
            cmd = [
                self.claude_command,
                "--prompt-file", str(prompt_file),
            ]
            
            try:
                # Execute Claude Code
                result = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    raise ClaudeCodeGenerationError(
                        f"Claude Code failed: {result.stderr}"
                    )
                
                return result.stdout
                    
            except subprocess.TimeoutExpired:
                raise ClaudeCodeGenerationError(
                    f"Claude Code timed out after 300 seconds"
                )
    
    def _parse_generated_files(self, claude_output: str, recipe: Recipe) -> Dict[str, str]:
        """Parse files from Claude output."""
        generated_files: Dict[str, str] = {}
        
        # Parse output to extract generated files
        # This is a simplified parser - actual implementation would be more robust
        lines = claude_output.split('\n')
        current_file = None
        current_content: List[str] = []
        in_code_block = False
        
        for line in lines:
            if 'Creating file:' in line or 'File:' in line:
                # Save previous file if exists
                if current_file and current_content:
                    generated_files[current_file] = '\n'.join(current_content)
                # Start new file
                file_path = line.split(':', 1)[1].strip()
                # Normalize path - ensure it's relative to the recipe
                if not file_path.startswith('src/') and not file_path.startswith('tests/'):
                    # If path doesn't have proper prefix, add it
                    if '/' not in file_path:
                        # Simple filename, put in recipe src dir
                        file_path = f"src/{recipe.name.replace('-', '_')}/{file_path}"
                current_file = file_path
                current_content = []
                in_code_block = False
            elif line.strip() == '```python' or line.strip() == '```':
                in_code_block = not in_code_block
            elif in_code_block and current_file:
                current_content.append(line)
        
        # Save last file
        if current_file and current_content:
            generated_files[current_file] = '\n'.join(current_content)
        
        return generated_files
    
    def _validate_against_requirements(
        self, code: GeneratedCode, requirements: Requirements
    ) -> bool:
        """Validate generated code satisfies requirements."""
        # Simple validation - in practice would be more sophisticated
        if not code.files:
            return False
        
        # Check that all MUST requirements have corresponding code
        all_code = ' '.join(code.files.values()).lower()
        
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
4. Ensure all tests pass
5. No stub implementations - everything must work

Generate the implementation that makes all tests pass.
"""
        return prompt