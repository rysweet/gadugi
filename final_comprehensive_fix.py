import os
import re
import subprocess

#!/usr/bin/env python3

"""
Comprehensive final fix for all remaining pyright errors.
"""

from pathlib import Path


def get_error_files() -> Set[str]:
    """Get all files with pyright errors."""
    result = subprocess.run(
        ["uv", "run", "pyright", ".claude"], capture_output=True, text=True
    )

    files = set()
    for line in result.stdout.split("\n"):
        if "error:" in line:
            # Extract file path
            if ".claude/" in line:
                path = line.split(":")[0].strip()
                files.add(path)

    return files


def fix_agent_performance_dataclass():
    """Properly fix AgentPerformance usage in all test files."""

    # Files that use AgentPerformance
    files = [
        ".claude/agents/team-coach/tests/test_coaching_engine.py",
        ".claude/agents/team-coach/tests/test_strategic_planner.py",
        ".claude/agents/teamcoach/tests/test_coaching_engine.py",
        ".claude/agents/teamcoach/tests/test_strategic_planner.py",
    ]

    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()

        # Remove any existing AgentPerformance class definitions that were added
        content = re.sub(
            r"@dataclass\s+class AgentPerformance:.*?(?=\n\n|\nclass |\ndef )",
            "",
            content,
            flags=re.DOTALL,
        )

        # Find where AgentPerformance is imported from
        if "from" in content and "AgentPerformance" in content:
            # It's imported, so we need to check the actual class definition
            import_match = re.search(r"from ([.\w]+) import.*AgentPerformance", content)
            if import_match:
                # The class is imported from somewhere else
                # We need to fix the usage, not the definition
                # Convert named parameters to positional
                content = re.sub(
                    r"AgentPerformance\(\s*"
                    r"agent_id=([^,]+),\s*"
                    r"success_rate=([^,]+),\s*"
                    r"average_execution_time=([^,]+),\s*"
                    r"total_tasks=([^,]+),\s*"
                    r"successful_tasks=([^,]+),\s*"
                    r"failed_tasks=([^,]+),\s*"
                    r"error_count=([^,]+),\s*"
                    r"error_types=([^)]+)\)",
                    r'{"agent_id": \1, "success_rate": \2, "average_execution_time": \3, '
                    r'"total_tasks": \4, "successful_tasks": \5, "failed_tasks": \6, '
                    r'"error_count": \7, "error_types": \8}',
                    content,
                )

        path.write_text(content)
        print(f"Fixed AgentPerformance usage in {filepath}")


def fix_unused_imports():
    """Remove all unused imports."""

    files_to_fix = {
        ".claude/agents/shared_test_instructions.py": ["Dict"],
        ".claude/agents/system_design_reviewer/core.py": [
            "ArchitecturalElement",
            "ChangeType",
            "ElementType",
        ],
        ".claude/agents/team-coach/phase2/task_matcher.py": [
            "TaskCapabilityRequirement"
        ],
        ".claude/agents/teamcoach/phase2/task_matcher.py": [
            "TaskCapabilityRequirement"
        ],
    }

    for filepath, unused_imports in files_to_fix.items():
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()

        for unused in unused_imports:
            # Remove from import statements
            # Handle different import patterns
            patterns = [
                rf",\s*{unused}(?=\s*[,)])",  # Middle or end of list
                rf"(?<=[(,]\s){unused}\s*,",  # Beginning of list
                rf"(?<=import\s){unused}$",  # Single import
                rf"{unused}\s*,\s*",  # With trailing comma
            ]

            for pattern in patterns:
                content = re.sub(pattern, "", content)

            # Clean up any double commas or empty imports
            content = re.sub(r",\s*,", ",", content)
            content = re.sub(r"\(\s*,", "(", content)
            content = re.sub(r",\s*\)", ")", content)
            content = re.sub(r"from\s+[\w.]+\s+import\s*\(\s*\)", "", content)

        path.write_text(content)
        print(f"Fixed unused imports in {filepath}")


def fix_unused_variables():
    """Fix unused variable warnings."""

    files_with_unused = {
        ".claude/agents/team-coach/tests/test_conflict_resolver.py": ["i"],
        ".claude/agents/team-coach/tests/test_strategic_planner.py": ["timeframe"],
    }

    for filepath, unused_vars in files_with_unused.items():
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()

        for var in unused_vars:
            # Replace unused loop variables with _
            content = re.sub(rf"\bfor\s+{var}\s+in\b", "for _ in", content)
            # Remove unused assignments
            content = re.sub(rf"^\s*{var}\s*=.*$", "", content, flags=re.MULTILINE)

        path.write_text(content)
        print(f"Fixed unused variables in {filepath}")


def fix_attribute_access():
    """Fix attribute access errors."""

    path = Path(".claude/agents/team-coach/tests/test_strategic_planner.py")
    if path.exists():
        content = path.read_text()

        # Fix implementation_steps attribute access
        content = content.replace(".implementation_steps", ".steps")

        path.write_text(content)
        print("Fixed attribute access in test_strategic_planner.py")


def fix_shared_test_redeclaration():
    """Fix redeclaration in shared_test_instructions.py."""

    path = Path(".claude/agents/shared_test_instructions.py")
    if path.exists():
        content = path.read_text()

        # Remove duplicate AgentConfig declaration
        # Count occurrences
        occurrences = content.count("class AgentConfig")
        if occurrences > 1:
            # Keep only the first one
            lines = content.split("\n")
            new_lines = []
            found_first = False
            skip_until_next_class = False

            for line in lines:
                if "class AgentConfig" in line:
                    if not found_first:
                        found_first = True
                        new_lines.append(line)
                    else:
                        skip_until_next_class = True
                        continue
                elif skip_until_next_class:
                    if line.strip() and not line.startswith(" "):
                        skip_until_next_class = False
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            content = "\n".join(new_lines)

        path.write_text(content)
        print("Fixed redeclaration in shared_test_instructions.py")


def fix_test_file_syntax():
    """Fix remaining syntax issues in test files."""

    test_files = Path(".claude").rglob("test_*.py")

    for test_file in test_files:
        content = test_file.read_text()
        modified = False

        # Fix imports that are on wrong lines
        lines = content.split("\n")
        new_lines = []

        for i, line in enumerate(lines):
            # Check for statements on same line
            if ";" not in line and "import" in line and len(line.split("import")) > 2:
                # Split into separate lines
                parts = line.split("import")
                for j, part in enumerate(parts):
                    if j == 0:
                        new_lines.append(part + "import")
                    elif j < len(parts) - 1:
                        new_lines.append("import" + part + "import")
                    else:
                        new_lines.append("import" + part)
                modified = True
            else:
                new_lines.append(line)

        if modified:
            content = "\n".join(new_lines)
            test_file.write_text(content)
            print(f"Fixed syntax in {test_file.name}")


def fix_orchestrator_tests():
    """Fix specific issues in orchestrator test files."""

    # Fix test_containerized_execution.py
    path = Path(".claude/orchestrator/tests/test_containerized_execution.py")
    if path.exists():
        content = path.read_text()

        # Add missing imports

        if "import unittest" not in content and "TestCase" in content:
            content = "import unittest\n" + content

        path.write_text(content)
        print("Fixed orchestrator test imports")


def fix_event_router_tests():
    """Fix event router test issues."""

    path = Path(".claude/services/event-router/tests/test_event_router.py")
    if path.exists():
        content = path.read_text()

        # Add missing imports and fix undefined references
        if "import asyncio" not in content and "asyncio" in content:
            content = "import asyncio\n" + content

        path.write_text(content)
        print("Fixed event router test imports")


def main():
    """Main execution."""
    print("Running comprehensive final fixes...")

    # Get initial count
    initial_errors = get_error_files()
    print(f"Files with errors: {len(initial_errors)}")

    # Run all fixes
    fix_agent_performance_dataclass()
    fix_unused_imports()
    fix_unused_variables()
    fix_attribute_access()
    fix_shared_test_redeclaration()
    fix_test_file_syntax()
    fix_orchestrator_tests()
    fix_event_router_tests()

    # Get final count
    result = subprocess.run(
        ["uv", "run", "pyright", ".claude"], capture_output=True, text=True
    )

    error_lines = [l for l in result.stdout.split("\n") if "error:" in l]
    print(f"\nTotal errors remaining: {len(error_lines)}")

    if len(error_lines) > 0:
        print("\nSample of remaining errors:")
        for error in error_lines[:10]:
            print(f"  {error}")


if __name__ == "__main__":
    main()
