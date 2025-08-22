"""Stub detection and remediation for generated code."""

from typing import Dict, List, Tuple
import re


class StubDetector:
    """Detects and reports stub implementations in generated code."""

    # Patterns that indicate stub implementations
    STUB_PATTERNS = [
        # Direct stub indicators
        r"raise\s+NotImplementedError",
        r"raise\s+NotImplemented\b",
        r"pass\s*$",  # pass as the only statement
        r"^\s*pass\s*#",  # pass with comment
        r"#\s*TODO\b",
        r"#\s*FIXME\b",
        r"#\s*XXX\b",
        r"#\s*HACK\b",
        r"#\s*STUB\b",
        r"\.\.\.  # Ellipsis as placeholder",
        r"^\s*\.\.\.\s*$",  # Ellipsis alone
        # Common placeholder patterns
        r'"[^"]*not\s+yet\s+implemented[^"]*"',
        r"'[^']*not\s+yet\s+implemented[^']*'",
        r'"[^"]*to\s+be\s+implemented[^"]*"',
        r"'[^']*to\s+be\s+implemented[^']*'",
        r'"[^"]*placeholder[^"]*"',
        r"'[^']*placeholder[^']*'",
        # Empty implementations (function with only docstring and pass)
        r'def\s+\w+\([^)]*\)[^:]*:\s*"""[^"]*"""\s*pass',
        r"def\s+\w+\([^)]*\)[^:]*:\s*'''[^']*'''\s*pass",
    ]

    # Patterns that are allowed (false positives to ignore)
    ALLOWED_PATTERNS = [
        r"#.*bypass",  # Comments about bypassing
        r"#.*password",  # Comments mentioning password
        r"#.*compass",  # Other words containing "pass"
        r"unittest\.skip",  # Skipped tests are OK
        r"pytest\.skip",  # Skipped tests are OK
        r"@skip",  # Skip decorators
        r"\.click_pass_context",  # Click library pattern
        r"\.click_pass_obj",  # Click library pattern
    ]

    def __init__(self, strict_mode: bool = True):
        """Initialize stub detector.

        Args:
            strict_mode: If True, enforces zero tolerance for stubs
        """
        self.strict_mode = strict_mode
        self.compiled_patterns = [
            re.compile(p, re.MULTILINE | re.IGNORECASE) for p in self.STUB_PATTERNS
        ]
        self.compiled_allowed = [
            re.compile(p, re.MULTILINE | re.IGNORECASE) for p in self.ALLOWED_PATTERNS
        ]

    def detect_stubs_in_code(
        self, code: str, filename: str = "unknown"
    ) -> List[Tuple[int, str, str]]:
        """Detect stub implementations in code.

        Args:
            code: The code to analyze
            filename: Name of the file for reporting

        Returns:
            List of (line_number, pattern_matched, line_content) tuples
        """
        stubs_found: List[Tuple[int, str, str]] = []
        lines = code.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check if line matches any allowed pattern (skip if it does)
            if any(pattern.search(line) for pattern in self.compiled_allowed):
                continue

            # Check against stub patterns
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    # Extract the pattern as string for reporting
                    pattern_str = next(
                        (
                            p
                            for p in self.STUB_PATTERNS
                            if re.compile(p, re.MULTILINE | re.IGNORECASE).search(line)
                        ),
                        "unknown pattern",
                    )
                    stubs_found.append((line_num, pattern_str, line.strip()))
                    break  # Only report once per line

        return stubs_found

    def detect_stubs_in_files(self, files: Dict[str, str]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Detect stubs in multiple files.

        Args:
            files: Dictionary of filename -> code content

        Returns:
            Dictionary of filename -> list of stub detections
        """
        results: Dict[str, List[Tuple[int, str, str]]] = {}

        for filename, code in files.items():
            stubs = self.detect_stubs_in_code(code, filename)
            if stubs:
                results[filename] = stubs

        return results

    def validate_no_stubs(self, files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate that files contain no stub implementations.

        Args:
            files: Dictionary of filename -> code content

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        stub_results = self.detect_stubs_in_files(files)

        if not stub_results:
            return True, []

        errors: List[str] = []
        for filename, stubs in stub_results.items():
            errors.append(f"\nStubs detected in {filename}:")
            for line_num, pattern, content in stubs:
                errors.append(f"  Line {line_num}: {content}")
                errors.append(f"    Pattern matched: {pattern}")

        return False, errors

    def generate_remediation_prompt(
        self, files: Dict[str, str], stub_results: Dict[str, List[Tuple[int, str, str]]]
    ) -> str:
        """Generate a prompt for Claude to fix the detected stubs.

        Args:
            files: Original files with stubs
            stub_results: Detection results

        Returns:
            Prompt for Claude Code to fix the stubs
        """
        prompt = """# Fix Stub Implementations

## CRITICAL: Zero BS Principle Violation Detected

The following stub implementations violate the Zero BS principle and MUST be fixed with real, working code.

## Detected Stubs

"""

        for filename, stubs in stub_results.items():
            prompt += f"\n### {filename}\n"
            for line_num, pattern, content in stubs:
                prompt += f"- Line {line_num}: `{content}`\n"

        prompt += """

## Requirements

You MUST:
1. Replace ALL `raise NotImplementedError` with actual working implementations
2. Replace ALL `pass` statements with real code that does something meaningful
3. Replace ALL TODO/FIXME comments with completed implementations
4. Ensure every function and method has a real, working implementation
5. NO PLACEHOLDERS - every piece of code must actually work

## Current Code

"""

        for filename, code in files.items():
            if filename in stub_results:
                prompt += f"\n### {filename}\n```python\n{code}\n```\n"

        prompt += """

## Your Task

Generate the complete, working implementations for all the stub code above. 
Every function must do real work - no exceptions.
Follow the Zero BS Principle: if you can't implement it properly, say so rather than creating stubs.
"""

        return prompt

    def check_implementation_completeness(self, code: str) -> Tuple[bool, List[str]]:
        """Check if an implementation appears complete (not just stub-free).

        Args:
            code: Code to check

        Returns:
            Tuple of (is_complete, list_of_issues)
        """
        issues: List[str] = []

        # Check for empty function bodies (just docstring)
        empty_func_pattern = re.compile(
            r'def\s+(\w+)\([^)]*\)[^:]*:\s*"""[^"]*"""\s*$', re.MULTILINE
        )
        empty_funcs = empty_func_pattern.findall(code)
        if empty_funcs:
            issues.append(f"Empty function implementations found: {', '.join(empty_funcs)}")

        # Check for suspiciously short implementations
        func_pattern = re.compile(r"def\s+(\w+)\([^)]*\)[^:]*:(.*?)(?=\ndef|\nclass|\Z)", re.DOTALL)
        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            func_body = match.group(2).strip()

            # Remove docstring and comments
            body_without_docs = re.sub(r'""".*?"""', "", func_body, flags=re.DOTALL)
            body_without_docs = re.sub(r"'''.*?'''", "", body_without_docs, flags=re.DOTALL)
            body_without_docs = re.sub(r"#.*$", "", body_without_docs, flags=re.MULTILINE)

            # Count actual code lines
            code_lines = [
                line.strip()
                for line in body_without_docs.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            # Functions should have at least some meaningful implementation
            if len(code_lines) < 2 and func_name not in ["__init__", "__str__", "__repr__"]:
                issues.append(f"Function '{func_name}' appears to have minimal implementation")

        return len(issues) == 0, issues


class StubRemediator:
    """Handles automatic remediation of stub implementations."""

    def __init__(self, claude_generator):
        """Initialize with a Claude code generator.

        Args:
            claude_generator: Instance of ClaudeCodeGenerator
        """
        self.generator = claude_generator
        self.detector = StubDetector(strict_mode=True)
        self.max_remediation_attempts = 3

    def remediate_stubs(
        self, files: Dict[str, str], recipe
    ) -> Tuple[Dict[str, str], bool, List[str]]:
        """Attempt to automatically fix stub implementations.

        Args:
            files: Dictionary of filename -> code with stubs
            recipe: Recipe object for context

        Returns:
            Tuple of (fixed_files, success, error_messages)
        """
        attempts = 0
        current_files = files.copy()
        all_errors: List[str] = []

        while attempts < self.max_remediation_attempts:
            attempts += 1

            # Detect stubs
            stub_results = self.detector.detect_stubs_in_files(current_files)

            if not stub_results:
                # No stubs found - success!
                return current_files, True, []

            # Generate remediation prompt
            prompt = self.detector.generate_remediation_prompt(current_files, stub_results)

            try:
                # Use Claude to fix the stubs
                fixed_output = self.generator._invoke_claude_code(prompt, recipe)
                fixed_files = self.generator._parse_generated_files(fixed_output, recipe)

                if fixed_files:
                    # Update with fixed versions
                    for filename, fixed_code in fixed_files.items():
                        # Find matching file in current_files
                        for orig_filename in current_files:
                            if filename.endswith(orig_filename) or orig_filename.endswith(filename):
                                current_files[orig_filename] = fixed_code
                                break

            except Exception as e:
                all_errors.append(f"Remediation attempt {attempts} failed: {str(e)}")
                continue

        # Final validation
        is_valid, final_errors = self.detector.validate_no_stubs(current_files)
        if not is_valid:
            all_errors.extend(final_errors)

        return current_files, is_valid, all_errors
