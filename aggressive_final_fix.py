#!/usr/bin/env python3
"""
Aggressive final fix for all remaining pyright errors.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def analyze_errors():
    """Analyze current errors and group by type."""
    result = subprocess.run(
        ["uv", "run", "pyright", ".claude"], capture_output=True, text=True
    )

    errors = {}
    for line in result.stdout.split("\n"):
        if "error:" in line:
            # Extract error type
            if "is not defined" in line:
                errors.setdefault("undefined", []).append(line)
            elif "is not accessed" in line:
                errors.setdefault("unused", []).append(line)
            elif "Cannot access attribute" in line:
                errors.setdefault("attribute", []).append(line)
            elif "No parameter named" in line:
                errors.setdefault("parameter", []).append(line)
            elif "possibly unbound" in line:
                errors.setdefault("unbound", []).append(line)
            elif "Arguments missing" in line:
                errors.setdefault("missing_args", []).append(line)
            else:
                errors.setdefault("other", []).append(line)

    return errors


def fix_orchestrator_test_files():
    """Fix all orchestrator test files."""
    test_dir = Path(".claude/orchestrator/tests")
    if not test_dir.exists():
        return

    for test_file in test_dir.glob("test_*.py"):
        content = test_file.read_text()
        modified = False

        # Add common missing imports
        if "Mock" in content and "from unittest.mock import" not in content:
            content = (
                "from unittest.mock import Mock, patch, MagicMock, AsyncMock\n"
                + content
            )
            modified = True

        if "TestCase" in content and "import unittest" not in content:
            content = "import unittest\n" + content
            modified = True

        if "asyncio" in content and "import asyncio" not in content:
            content = "import asyncio\n" + content
            modified = True

        if "datetime" in content and "from datetime import" not in content:
            content = "from datetime import datetime, timedelta\n" + content
            modified = True

        if "Path" in content and "from pathlib import" not in content:
            content = "from pathlib import Path\n" + content
            modified = True

        # Fix undefined variables
        if '"docker" is not defined' in content or "'docker' is not defined" in content:
            content = "import docker\n" + content
            modified = True

        if modified:
            test_file.write_text(content)
            print(f"Fixed {test_file.name}")


def fix_event_router_test_file():
    """Fix event router test file issues."""
    test_file = Path(".claude/services/event-router/tests/test_event_router.py")
    if not test_file.exists():
        return

    content = test_file.read_text()

    # Add all necessary imports at once
    imports = """import asyncio
import unittest
from unittest import TestCase
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

"""

    # Remove existing imports to avoid duplicates
    lines = content.split("\n")
    new_lines = []
    skip_imports = True

    for line in lines:
        if skip_imports and (line.startswith("import ") or line.startswith("from ")):
            continue
        elif (
            skip_imports and line.strip() and not line.startswith(("import ", "from "))
        ):
            skip_imports = False
            # Add our imports before the first non-import line
            new_lines.extend(imports.split("\n"))
        new_lines.append(line)

    content = "\n".join(new_lines)

    # Fix specific undefined variables
    if "EventRouter" in content and "from ..event_router import" not in content:
        content = content.replace(
            imports, imports + "from ..event_router import EventRouter\n"
        )

    test_file.write_text(content)
    print("Fixed event router test file")


def fix_framework_tests():
    """Fix framework test files."""
    test_dir = Path(".claude/framework/tests")
    if test_dir.exists():
        for test_file in test_dir.glob("test_*.py"):
            content = test_file.read_text()

            # Add necessary imports
            if "BaseAgent" in content and "from ..base_agent import" not in content:
                content = "from ..base_agent import BaseAgent\n" + content

            if "Mock" in content and "from unittest.mock import" not in content:
                content = "from unittest.mock import Mock, patch\n" + content

            test_file.write_text(content)
            print(f"Fixed {test_file.name}")


def fix_mcp_service():
    """Fix MCP service files."""
    mcp_dir = Path(".claude/services/mcp")
    if mcp_dir.exists():
        for py_file in mcp_dir.glob("*.py"):
            content = py_file.read_text()

            # Fix common import issues
            if "FastAPI" in content and "from fastapi import" not in content:
                content = "from fastapi import FastAPI, HTTPException\n" + content

            if "BaseModel" in content and "from pydantic import" not in content:
                content = "from pydantic import BaseModel\n" + content

            py_file.write_text(content)
            print(f"Fixed {py_file.name}")


def fix_test_agent_files():
    """Fix test agent files."""
    agent_files = [
        ".claude/agents/test_writer_agent.py",
        ".claude/agents/test_solver_agent.py",
    ]

    for filepath in agent_files:
        path = Path(filepath)
        if path.exists():
            content = path.read_text()

            # Add necessary imports
            if "BaseAgent" in content and "from" not in content:
                content = (
                    """from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..framework.base_agent import BaseAgent

"""
                    + content
                )

            path.write_text(content)
            print(f"Fixed {path.name}")


def remove_all_unused_imports():
    """Remove all remaining unused imports."""
    result = subprocess.run(
        ["uv", "run", "pyright", ".claude"], capture_output=True, text=True
    )

    for line in result.stdout.split("\n"):
        if "is not accessed" in line and ".claude/" in line:
            # Extract file path and import name
            match = re.match(r'(.+\.py):\d+:\d+ - error: Import "([^"]+)"', line)
            if match:
                filepath = match.group(1)
                import_name = match.group(2)

                path = Path(filepath)
                if path.exists():
                    content = path.read_text()

                    # Remove the unused import
                    # Try different patterns
                    patterns = [
                        rf"import {import_name}\n",
                        rf"from .+ import .*{import_name}.*\n",
                        rf",\s*{import_name}(?=[,)])",
                        rf"{import_name}\s*,",
                    ]

                    for pattern in patterns:
                        new_content = re.sub(pattern, "", content)
                        if new_content != content:
                            content = new_content
                            break

                    # Clean up
                    content = re.sub(r",\s*\)", ")", content)
                    content = re.sub(r"\(\s*,", "(", content)
                    content = re.sub(r",\s*,", ",", content)

                    path.write_text(content)


def main():
    """Main execution."""
    print("Running aggressive final fixes...")

    # Analyze current errors
    errors = analyze_errors()
    print("Error breakdown:")
    for error_type, error_list in errors.items():
        print(f"  {error_type}: {len(error_list)} errors")

    # Apply fixes
    print("\nApplying fixes...")
    fix_orchestrator_test_files()
    fix_event_router_test_file()
    fix_framework_tests()
    fix_mcp_service()
    fix_test_agent_files()
    remove_all_unused_imports()

    # Final check
    result = subprocess.run(
        ["uv", "run", "pyright", ".claude"], capture_output=True, text=True
    )

    final_errors = [l for l in result.stdout.split("\n") if "error:" in l]
    print(f"\nFinal error count: {len(final_errors)}")

    if len(final_errors) > 0 and len(final_errors) < 20:
        print("\nRemaining errors:")
        for error in final_errors:
            print(f"  {error}")


if __name__ == "__main__":
    main()
