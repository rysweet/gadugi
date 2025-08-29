#!/usr/bin/env python3
"""
Fix syntax errors introduced by previous fixes.
"""

from pathlib import Path
from typing import List, Tuple, Union


def fix_file(filepath: str, fixes: List[Tuple[str, str]]) -> None:
    """Apply fixes to a file.

    Args:
        filepath: Path to the file to fix
        fixes: List of (old_text, new_text) tuples to replace
    """
    path = Path(filepath)
    if not path.exists():
        return

    content: str = path.read_text()

    for old, new in fixes:
        content = content.replace(old, new)

    path.write_text(content)
    print(f"Fixed {filepath}")


def main() -> None:
    """Main function to apply syntax fixes."""
    # Fix files with syntax errors
    fixes: List[Tuple[str, List[Tuple[str, str]]]] = [
        (
            '.claude/orchestrator/components/task_analyzer.py',
            [
                ('"""CLI entry point for TaskAnalyzer""))', '"""CLI entry point for TaskAnalyzer""")')
            ]
        ),
        (
            '.claude/agents/shared_test_instructions.py',
            [
                ('@dataclass\nclass TestStatus(Enum):', 'class TestStatus(Enum):')
            ]
        ),
        (
            '.claude/agents/orchestrator/orchestrator.py',
            [
                ('from pathlib import   # type: ignore', 'from pathlib import Path  # type: ignore')
            ]
        ),
        (
            '.claude/shared/task_tracking.py',
            [
                ('from pathlib import   # type: ignore', 'from pathlib import Path  # type: ignore')
            ]
        ),
        (
            '.claude/orchestrator/tests/test_task_analyzer.py',
            [
                ('mock_walk.return_value = [import', 'mock_walk.return_value = []')
            ]
        ),
        (
            '.claude/framework/tests/test_base_agent.py',
            [
                ('from pathlib import\n', 'from pathlib import Path\n')
            ]
        )
    ]

    for filepath, file_fixes in fixes:
        fix_file(filepath, file_fixes)

    # Fix indentation issue in test_containerized_execution.py
    path = Path('.claude/orchestrator/tests/test_containerized_execution.py')
    if path.exists():
        lines: List[str] = path.read_text().split('\n')
        new_lines: List[str] = []

        for i, line in enumerate(lines):
            # Fix the specific indentation error
            if i == 322 and '"""Test TaskExecutor uses containerized execution"""' in line:
                # This docstring should be indented properly
                new_lines.append('    ' + line.strip())
            else:
                new_lines.append(line)

        path.write_text('\n'.join(new_lines))
        print("Fixed test_containerized_execution.py indentation")

    print("All syntax errors fixed")


if __name__ == "__main__":
    main()
