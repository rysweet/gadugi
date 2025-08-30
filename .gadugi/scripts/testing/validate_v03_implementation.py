#!/usr/bin/env python3
"""
Validate Gadugi v0.3 Implementation
Checks what's ACTUALLY implemented vs claimed
"""

import subprocess
from pathlib import Path
from typing import List, Tuple


class ImplementationValidator:
    def __init__(self):
        self.results = {
            "components": {},
            "quality": {},
            "integration": {},
            "summary": {},
        }

    def check_file_exists(self, path: str) -> bool:
        """Check if a file actually exists"""
        return Path(path).exists()

    def check_directory_has_python(self, path: str) -> Tuple[bool, int]:
        """Check if directory has actual Python implementation files"""
        dir_path = Path(path)
        if not dir_path.exists():
            return False, 0

        py_files = list(dir_path.glob("*.py"))
        # Exclude __init__.py and test files
        impl_files = [
            f for f in py_files if f.name != "__init__.py" and not f.name.startswith("test_")
        ]
        return len(impl_files) > 0, len(impl_files)

    def run_pyright(self, path: str) -> Tuple[int, int, int]:
        """Run pyright and return (errors, warnings, infos)"""
        try:
            result = subprocess.run(
                ["uv", "run", "pyright", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr

            # Parse output for counts
            errors = output.count(" error:")
            warnings = output.count(" warning:")
            infos = output.count(" information:")

            return errors, warnings, infos
        except Exception as e:
            print(f"Error running pyright on {path}: {e}")
            return -1, -1, -1

    def check_imports_work(self, module_path: str) -> bool:
        """Try to import a Python module to see if it's valid"""
        try:
            # Convert path to module name
            module = module_path.replace("/", ".").replace(".py", "")
            cmd = f"python3 -c 'import {module}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def validate_component(self, name: str, path: str, requirements: List[str]):
        """Validate a single component"""
        print(f"\n{'=' * 60}")
        print(f"Validating: {name}")
        print(f"Path: {path}")
        print("-" * 40)

        result = {
            "exists": False,
            "has_implementation": False,
            "file_count": 0,
            "pyright_errors": -1,
            "requirements_met": [],
            "status": "NOT_FOUND",
        }

        # Check existence
        if Path(path).exists():
            result["exists"] = True

            # Check for actual implementation
            has_impl, count = self.check_directory_has_python(path)
            result["has_implementation"] = has_impl
            result["file_count"] = count

            if has_impl:
                # Run pyright
                errors, warnings, infos = self.run_pyright(path)
                result["pyright_errors"] = errors
                result["pyright_warnings"] = warnings  # Use warnings
                result["pyright_infos"] = infos  # Use infos

                # Determine status
                if errors == 0:
                    result["status"] = "WORKING"
                elif errors > 0:
                    result["status"] = "HAS_ERRORS"
                else:
                    result["status"] = "UNKNOWN"
            else:
                result["status"] = "EMPTY_DIR"

        # Print results
        print(f"  Exists: {'✅' if result['exists'] else '❌'}")
        print(f"  Has Implementation: {'✅' if result['has_implementation'] else '❌'}")
        print(f"  Python Files: {result['file_count']}")
        if result["pyright_errors"] >= 0:
            print(f"  Pyright Errors: {result['pyright_errors']}")
        print(f"  Status: {result['status']}")

        self.results["components"][name] = result
        return result

    def validate_all(self):
        """Validate all components"""
        print("\n" + "=" * 60)
        print("GADUGI v0.3 IMPLEMENTATION VALIDATION")
        print("=" * 60)

        components = {
            "Recipe Executor": (
                ".claude/agents/RecipeExecutor",
                ["Parse recipe files", "Generate implementation", "Create tests"],
            ),
            "Event Router": (
                ".claude/services/event-router",
                ["Spawn agent processes", "Handle events", "Dead letter queue"],
            ),
            "MCP Service": (
                ".claude/services/mcp",
                ["FastAPI REST API", "Neo4j integration", "Memory operations"],
            ),
            "Neo4j Service": (
                "neo4j",
                ["Docker compose file", "Schema definition", "Init scripts"],
            ),
            "Agent Framework": (
                ".claude/framework",
                ["BaseAgent class", "Event integration", "Tool registry"],
            ),
            "Orchestrator": (
                ".claude/agents/orchestrator",
                [
                    "WorkflowManager delegation",
                    "Parallel execution",
                    "Worktree management",
                ],
            ),
            "Task Decomposer": (
                ".claude/agents/TaskDecomposer",
                ["Task analysis", "Dependency detection", "Parallel opportunities"],
            ),
            "Team Coach": (
                ".claude/agents/TeamCoach",
                ["Session analysis", "GitHub integration", "Performance tracking"],
            ),
        }

        for name, (path, reqs) in components.items():
            self.validate_component(name, path, reqs)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        total = len(self.results["components"])
        exists = sum(1 for c in self.results["components"].values() if c["exists"])
        has_impl = sum(1 for c in self.results["components"].values() if c["has_implementation"])
        working = sum(1 for c in self.results["components"].values() if c["status"] == "WORKING")
        has_errors = sum(
            1 for c in self.results["components"].values() if c["status"] == "HAS_ERRORS"
        )
        empty = sum(1 for c in self.results["components"].values() if c["status"] == "EMPTY_DIR")

        print(f"\nTotal Components: {total}")
        print(f"  Directories Exist: {exists}/{total} ({exists / total * 100:.0f}%)")
        print(f"  Have Implementation: {has_impl}/{total} ({has_impl / total * 100:.0f}%)")
        print(f"  Working (no pyright errors): {working}/{total} ({working / total * 100:.0f}%)")
        print(f"  Have Errors: {has_errors}/{total}")
        print(f"  Empty Directories: {empty}/{total}")

        print("\n" + "-" * 40)
        print("Component Status:")
        for name, result in self.results["components"].items():
            status_emoji = {
                "WORKING": "✅",
                "HAS_ERRORS": "⚠️",
                "EMPTY_DIR": "📁",
                "NOT_FOUND": "❌",
                "UNKNOWN": "❓",
            }.get(result["status"], "❓")

            print(f"  {status_emoji} {name}: {result['status']}")
            if result["status"] == "HAS_ERRORS":
                print(f"     → {result['pyright_errors']} pyright errors")
            elif result["status"] == "EMPTY_DIR":
                print("     → Directory exists but no implementation")

        # Overall verdict
        print("\n" + "=" * 60)
        if working == total:
            print("✅ ALL COMPONENTS WORKING!")
        elif has_impl >= total * 0.7:
            print("⚠️  MOSTLY IMPLEMENTED but needs fixes")
        elif has_impl >= total * 0.3:
            print("🚧 PARTIALLY IMPLEMENTED - significant work remains")
        else:
            print("❌ MOSTLY NOT IMPLEMENTED - claims don't match reality")
        print("=" * 60)


if __name__ == "__main__":
    validator = ImplementationValidator()
    validator.validate_all()
