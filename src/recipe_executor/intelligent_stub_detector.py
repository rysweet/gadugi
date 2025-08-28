"""Intelligent stub detection using Claude for context-aware analysis."""

import re
import subprocess
import json
import tempfile
from typing import Dict, List, Tuple, Any
from pathlib import Path


class IntelligentStubDetector:
    """Uses Claude to intelligently detect real stubs vs false positives."""
    
    def __init__(self, strict_mode: bool = True):
        """Initialize intelligent stub detector.
        
        Args:
            strict_mode: If True, enforces zero tolerance for real stubs
        """
        self.strict_mode = strict_mode
        
        # Quick patterns for initial filtering (potential stubs)
        self.potential_stub_patterns = [
            r"raise\s+NotImplementedError",
            r"pass\s*$",
            r"#\s*TODO\b",
            r"#\s*FIXME\b",
            r"#\s*STUB\b",
            r"\.\.\..*#.*placeholder",
        ]
        
        # Context patterns that indicate legitimate use
        self.legitimate_contexts = [
            (r"class\s+\w+.*\(.*Exception.*\):", "Exception class definition"),
            (r"except\s*.*:", "Exception handler"),
            (r"@abstractmethod", "Abstract method"),
            (r"if\s+TYPE_CHECKING:", "Type checking block"),
            (r"pytest\.skip", "Test skip"),
            (r"unittest\.skip", "Test skip"),
        ]

    def detect_stubs_with_claude(self, files: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Use Claude to intelligently detect stubs with context awareness.
        
        Args:
            files: Dictionary of filename -> code content
            
        Returns:
            Tuple of (has_real_stubs, list_of_issues)
        """
        # First, collect potential stubs using quick patterns
        potential_stubs = self._collect_potential_stubs(files)
        
        if not potential_stubs:
            return False, []
        
        # Use Claude to evaluate each potential stub in context
        real_stubs = self._evaluate_with_claude(potential_stubs, files)
        
        if not real_stubs:
            return False, []
        
        # Format the real stub issues
        issues: List[str] = []
        for filename, stubs in real_stubs.items():
            issues.append(f"\nReal stubs detected in {filename}:")
            for line_num, context, verdict in stubs:
                issues.append(f"  Line {line_num}: {context}")
                issues.append(f"    Claude verdict: {verdict}")
        
        return True, issues

    def _collect_potential_stubs(self, files: Dict[str, str]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Collect potential stubs for Claude to evaluate.
        
        Returns:
            Dict of filename -> [(line_num, line_content, surrounding_context)]
        """
        potential: Dict[str, List[Tuple[int, str, str]]] = {}
        
        for filename, code in files.items():
            lines = code.split('\n')
            file_stubs: List[Tuple[int, str, str]] = []
            
            for i, line in enumerate(lines, 1):
                for pattern in self.potential_stub_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Get surrounding context (5 lines before and after)
                        start = max(0, i - 6)
                        end = min(len(lines), i + 5)
                        context = '\n'.join(lines[start:end])
                        
                        # Check if it's obviously legitimate
                        if not self._is_obviously_legitimate(context, line):
                            file_stubs.append((i, line.strip(), context))
                        break
            
            if file_stubs:
                potential[filename] = file_stubs
        
        return potential

    def _is_obviously_legitimate(self, context: str, line: str) -> bool:
        """Quick check for obviously legitimate uses."""
        # Check for legitimate contexts
        for pattern, _ in self.legitimate_contexts:
            if re.search(pattern, context, re.IGNORECASE | re.MULTILINE):
                return True
        
        # Check if it's in a comment or docstring (not code)
        if line.strip().startswith('#'):
            # It's a comment mentioning TODO/pass/etc
            return True
        
        # Check if it's in a string
        if '"""' in context or "'''" in context:
            # Could be in a docstring
            in_docstring = False
            for ctx_line in context.split('\n'):
                if '"""' in ctx_line or "'''" in ctx_line:
                    in_docstring = not in_docstring
                if ctx_line.strip() == line.strip() and in_docstring:
                    return True
        
        return False

    def _evaluate_with_claude(self, potential_stubs: Dict[str, List[Tuple[int, str, str]]], 
                             files: Dict[str, str]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Use Claude to evaluate if potential stubs are real stubs.
        
        Returns:
            Dict of filename -> [(line_num, line_content, verdict)]
        """
        # Create evaluation prompt for Claude
        prompt = self._create_evaluation_prompt(potential_stubs, files)
        
        # Call Claude for intelligent evaluation
        try:
            result = self._invoke_claude_for_evaluation(prompt)
            return self._parse_claude_evaluation(result, potential_stubs)
        except Exception as e:
            print(f"Warning: Claude evaluation failed, falling back to strict patterns: {e}")
            # Fallback to considering all potential stubs as real
            return potential_stubs

    def _create_evaluation_prompt(self, potential_stubs: Dict[str, List[Tuple[int, str, str]]], 
                                  files: Dict[str, str]) -> str:
        """Create a prompt for Claude to evaluate potential stubs."""
        prompt = """# Intelligent Stub Detection

You are an expert Python code analyzer. Your task is to determine whether the following potential stubs are REAL stubs (incomplete implementations) or FALSE POSITIVES (legitimate code).

## Context
The Recipe Executor is self-regenerating and must have ZERO real stubs. However, we need to distinguish between:

### REAL STUBS (Must be fixed):
- Empty function bodies with just `pass`
- Functions that raise NotImplementedError
- Actual TODO comments indicating incomplete work
- Placeholder implementations

### FALSE POSITIVES (Legitimate code):
- Exception classes with `pass` (standard Python pattern)
- Exception handlers with `pass` (intentional silent handling)
- The word "pass" in comments or documentation
- Abstract methods (with @abstractmethod decorator)
- Type checking blocks (if TYPE_CHECKING)
- Test skips (pytest.skip, unittest.skip)
- Intentional no-op implementations

## Potential Stubs to Evaluate

Please analyze each potential stub below and determine if it's a REAL stub or FALSE POSITIVE.

"""
        
        stub_id = 0
        for filename, stubs in potential_stubs.items():
            prompt += f"\n### File: {filename}\n\n"
            
            for line_num, line_content, context in stubs:
                stub_id += 1
                prompt += f"**Potential Stub #{stub_id}** (Line {line_num}):\n"
                prompt += f"Line content: `{line_content}`\n\n"
                prompt += f"Context:\n```python\n{context}\n```\n\n"
        
        prompt += """
## Your Task

For each potential stub above, respond with a JSON array where each element has:
- "id": The stub number
- "is_real_stub": true if it's a real stub that needs fixing, false if it's a false positive
- "reason": Brief explanation of your determination

Example response:
```json
[
  {"id": 1, "is_real_stub": false, "reason": "Exception class definition - pass is standard Python"},
  {"id": 2, "is_real_stub": true, "reason": "Empty function body - needs implementation"},
  {"id": 3, "is_real_stub": false, "reason": "Word 'pass' appears in comment, not code"}
]
```

Analyze each potential stub carefully considering the context. Be precise - we want ZERO real stubs but don't want to flag legitimate code.
"""
        
        return prompt

    def _invoke_claude_for_evaluation(self, prompt: str) -> str:
        """Invoke Claude to evaluate potential stubs."""
        # Write prompt to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            # Call Claude with evaluation prompt
            cmd = [
                'claude', 
                '-p', prompt_file,
                '--dangerously-skip-permissions',
                '--output-format', 'json',
                '--max-turns', '1'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
                # No timeout - let Claude complete its evaluation
            )
            
            if result.returncode != 0:
                raise Exception(f"Claude returned error: {result.stderr}")
            
            return result.stdout
            
        finally:
            # Clean up temp file
            Path(prompt_file).unlink(missing_ok=True)

    def _parse_claude_evaluation(self, claude_output: str, 
                                 potential_stubs: Dict[str, List[Tuple[int, str, str]]]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Parse Claude's evaluation response."""
        try:
            # Extract JSON from Claude's response
            json_match = re.search(r'\[.*\]', claude_output, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in Claude's response")
            
            evaluations = json.loads(json_match.group())
            
            # Build a flat list of all stubs with their IDs
            all_stubs: List[Tuple[str, Tuple[int, str, str]]] = []
            for filename, stubs in potential_stubs.items():
                for stub in stubs:
                    all_stubs.append((filename, stub))
            
            # Filter to only real stubs based on Claude's evaluation
            real_stubs: Dict[str, List[Tuple[int, str, str]]] = {}
            if isinstance(evaluations, list):
                for eval_item in evaluations:  # type: ignore[misc]
                    if isinstance(eval_item, dict):
                        eval_dict: Dict[str, Any] = eval_item  # type: ignore[assignment]
                        stub_id: int = int(eval_dict.get('id', 0)) - 1  # Convert to 0-based index
                        is_real: bool = bool(eval_dict.get('is_real_stub', False))
                        if 0 <= stub_id < len(all_stubs) and is_real:
                            stub_entry: Tuple[str, Tuple[int, str, str]] = all_stubs[stub_id]
                            filename: str = stub_entry[0]
                            stub_info: Tuple[int, str, str] = stub_entry[1]
                            line_num: int = stub_info[0]
                            line_content: str = stub_info[1]
                            reason: str = str(eval_dict.get('reason', 'Identified as real stub'))
                            if filename not in real_stubs:
                                real_stubs[filename] = []
                            real_stubs[filename].append((
                                line_num, 
                                line_content, 
                                reason
                            ))
            
            return real_stubs
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to parse Claude evaluation: {e}")
            # On parse failure, be conservative and flag all as potential issues
            result: Dict[str, List[Tuple[int, str, str]]] = {}
            for filename, stubs in potential_stubs.items():
                result[filename] = [(s[0], s[1], "Could not verify - flagged for review") for s in stubs]
            return result


def validate_no_stubs_intelligent(files: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Convenience function for intelligent stub validation.
    
    Args:
        files: Dictionary of filename -> code content
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    detector = IntelligentStubDetector(strict_mode=True)
    has_stubs, issues = detector.detect_stubs_with_claude(files)
    return not has_stubs, issues