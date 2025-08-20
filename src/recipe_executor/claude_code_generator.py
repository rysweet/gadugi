"""Code generation using Claude Code CLI."""

from typing import Optional, Dict, List, Any
from pathlib import Path
import subprocess
import tempfile
import json
from datetime import datetime

from .recipe_model import Recipe, GeneratedCode, BuildContext, Requirements
from .python_standards import PythonStandards


class ClaudeCodeGenerationError(Exception):
    """Raised when Claude Code generation fails."""
    pass


class ClaudeCodeGenerator:
    """Generates code from recipes using Claude Code CLI."""
    
    def __init__(self, standards: Optional[PythonStandards] = None, guidelines_path: Optional[Path] = None):
        """Initialize with Python standards enforcement."""
        self.standards = standards or PythonStandards()
        self.guidelines_path = guidelines_path or Path(".claude/Guidelines.md")
        self.guidelines = self._load_guidelines()
    
    def generate(self, recipe: Recipe, context: Optional[BuildContext] = None) -> GeneratedCode:
        """Generate code using Claude Code based on recipe."""
        if context is None:
            context = BuildContext(recipe=recipe)
        
        # Create generation prompt from recipe
        prompt = self._create_generation_prompt(recipe)
        
        # Write prompt to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(prompt)
            prompt_file = Path(f.name)
        
        try:
            # Determine output directory
            output_dir = recipe.get_output_path()
            
            # Invoke Claude Code to generate implementation
            if not context.dry_run:
                self._invoke_claude_code(prompt_file, output_dir, recipe)
            
            # Read generated files
            generated_files = self._read_generated_files(output_dir, recipe)
            
            # Apply Python standards (format with ruff, check with pyright)
            for file_path, content in generated_files.items():
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
            if not self._validate_against_requirements(generated, recipe.requirements):
                raise ClaudeCodeGenerationError("Generated code doesn't satisfy requirements")
            
            return generated
            
        finally:
            # Clean up prompt file
            prompt_file.unlink(missing_ok=True)
    
    def _create_generation_prompt(self, recipe: Recipe) -> str:
        """Create a comprehensive prompt for Claude Code from recipe."""
        prompt = f"""# Generate Implementation for {recipe.name}

## CRITICAL: Development Guidelines (from Guidelines.md)

### Zero BS Principle
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
   - Ensure pyright and ruff compliance

## Context
You are implementing a component based on the following recipe. Generate production-quality Python code that:
1. Satisfies ALL requirements listed below
2. Follows the design specification
3. Uses UV for package management
4. Passes strict pyright type checking with ZERO errors
5. Is formatted with ruff
6. Includes comprehensive docstrings
7. NO STUBS - real implementations only

## Requirements

{self._format_requirements(recipe.requirements)}

## Design Specification

{recipe.design.architecture}

### Components to Implement

{self._format_components(recipe.design.components)}

### Implementation Notes

{recipe.design.implementation_notes}

## Python Standards

- MUST use type hints for all functions and methods
- MUST pass strict pyright checking with zero errors
- MUST be formatted with ruff
- MUST include docstrings for all classes and functions
- MUST handle errors appropriately
- MUST NOT use Any type unless absolutely necessary

## Output Structure

Generate files in the following structure:
- src/{recipe.name.replace('-', '_')}/
  - __init__.py (with proper exports)
  - One .py file per component
  - All necessary type stubs

## Dependencies

This recipe depends on: {', '.join(recipe.get_dependencies()) if recipe.get_dependencies() else 'None'}

## Success Criteria

The implementation is complete when:
{self._format_success_criteria(recipe.requirements.success_criteria)}

## Additional Instructions

- Follow the Zero BS Principle: no stubs, no placeholders, real working implementations
- If you need to import from other recipes/modules, use proper relative imports
- Ensure all code is production-ready, not prototypes
- Include proper error handling and logging where appropriate
"""
        return prompt
    
    def _load_guidelines(self) -> str:
        """Load Guidelines.md content if available."""
        if self.guidelines_path.exists():
            return self.guidelines_path.read_text()
        else:
            # Fallback to embedded guidelines
            return """# Gadugi Development Guidelines

## CRITICAL: Zero BS Principle

**NO BULLSHIT. NO CLAIMS WITHOUT EVIDENCE. NO FAKE COMPLETIONS.**

- If code doesn't exist, say "NOT IMPLEMENTED"
- If it's a stub, say "STUB ONLY"
- If it's untested, say "UNTESTED"
- If it doesn't work, say "BROKEN"
- NEVER claim something is complete unless it actually works end-to-end

## Core Development Principles

### 1. Implementation Before Claims
- Write the code first
- Test it second
- Document it third
- Claim completion only after all three

### 2. Quality Gates (MANDATORY)
Before ANY code is considered complete:
- ✅ Passes `uv run pyright` with ZERO errors
- ✅ Formatted with `uv run ruff format`
- ✅ Passes `uv run ruff check`
- ✅ Has actual tests that pass with `uv run pytest`

### 3. Python Standards
- MUST use UV for package management
- MUST use ruff for formatting
- MUST use pyright for type checking (strict mode)
- ALL generated code must be pyright-green
"""
    
    def _format_requirements(self, requirements: Requirements) -> str:
        """Format requirements for the prompt."""
        lines = [f"**Purpose**: {requirements.purpose}", ""]
        
        if requirements.functional_requirements:
            lines.append("### Functional Requirements")
            for req in requirements.functional_requirements:
                priority = req.priority.value.upper()
                lines.append(f"- **{priority}** {req.description}")
            lines.append("")
        
        if requirements.non_functional_requirements:
            lines.append("### Non-Functional Requirements")
            for req in requirements.non_functional_requirements:
                priority = req.priority.value.upper()
                lines.append(f"- **{priority}** {req.description}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_components(self, components: List[Any]) -> str:
        """Format component designs for the prompt."""
        lines = []
        for component in components:
            lines.append(f"#### {component.name}")
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
    
    def _invoke_claude_code(self, prompt_file: Path, output_dir: Path, recipe: Recipe) -> None:
        """Use Claude Code CLI to generate implementation."""
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build Claude Code command
        cmd = [
            "claude",
            "-p", str(prompt_file),
            "--yes"  # Auto-confirm file operations
        ]
        
        try:
            # Execute Claude Code
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise ClaudeCodeGenerationError(
                    f"Claude Code failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            raise ClaudeCodeGenerationError("Claude Code generation timed out")
        except FileNotFoundError:
            raise ClaudeCodeGenerationError(
                "Claude Code CLI not found. Please ensure 'claude' is installed and in PATH"
            )
    
    def _read_generated_files(self, output_dir: Path, recipe: Recipe) -> Dict[str, str]:
        """Read files generated by Claude Code."""
        generated_files = {}
        
        if not output_dir.exists():
            return generated_files
        
        # Read all Python files in the output directory
        for py_file in output_dir.rglob("*.py"):
            relative_path = py_file.relative_to(output_dir.parent.parent)
            content = py_file.read_text()
            generated_files[str(relative_path)] = content
        
        return generated_files
    
    def _validate_against_requirements(
        self, code: GeneratedCode, requirements: Requirements
    ) -> bool:
        """Validate generated code satisfies requirements."""
        # Check that we have generated files
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