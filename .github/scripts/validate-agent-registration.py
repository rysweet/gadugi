#!/usr/bin/env python3
"""Validate agent registration files for proper YAML frontmatter.

This script ensures all agent files have valid YAML frontmatter with required
fields to prevent runtime registration failures.
"""

import sys
import yaml
from pathlib import Path
import re
import argparse
from typing import Dict, List, Tuple, Optional


class AgentValidator:
    """Validates agent files for proper registration requirements."""

    REQUIRED_FIELDS = ["name", "description", "version", "tools"]
    AGENT_DIRECTORIES = [".claude/agents", ".github/agents"]

    def __init__(self, verbose: bool = False):
        """Initialize the validator.

        Args:
            verbose: Enable verbose output for debugging
        """
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{level}] {message}", file=sys.stderr)

    def extract_frontmatter(self, content: str) -> Optional[str]:
        """Extract YAML frontmatter from file content.

        Args:
            content: The file content

        Returns:
            The frontmatter content or None if not found
        """
        # Match content between --- markers at the start of file
        pattern = r"^---\s*\n(.*?)\n---\s*$"
        match = re.match(pattern, content, re.MULTILINE | re.DOTALL)

        if match:
            return match.group(1)
        return None

    def validate_semver(self, version: str) -> bool:
        """Validate if a string is a valid semantic version.

        Args:
            version: Version string to validate

        Returns:
            True if valid semver, False otherwise
        """
        # Basic semver pattern (supports major.minor.patch with optional pre-release)
        pattern = r"^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
        return bool(re.match(pattern, str(version)))

    def validate_agent_file(self, filepath: Path) -> Tuple[bool, List[str]]:
        """Validate a single agent file.

        Args:
            filepath: Path to the agent file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        self.log(f"Validating {filepath}")

        try:
            # Read file content
            content = filepath.read_text(encoding="utf-8")

            # Extract frontmatter
            frontmatter_content = self.extract_frontmatter(content)

            if frontmatter_content is None:
                errors.append(
                    "Missing YAML frontmatter (should be between --- markers)"
                )
                return False, errors

            # Parse YAML
            try:
                frontmatter = yaml.safe_load(frontmatter_content)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {e}")
                return False, errors

            if not isinstance(frontmatter, dict):
                errors.append("Frontmatter is not a dictionary/object")
                return False, errors

            # Check required fields
            for field in self.REQUIRED_FIELDS:
                if field not in frontmatter:
                    errors.append(f"Missing required field: '{field}'")
                elif frontmatter[field] is None:
                    errors.append(f"Field '{field}' is null/empty")
                elif (
                    field in ["name", "description"]
                    and not str(frontmatter[field]).strip()
                ):
                    errors.append(f"Field '{field}' is empty or whitespace only")

            # Validate version format
            if "version" in frontmatter and frontmatter["version"]:
                if not self.validate_semver(frontmatter["version"]):
                    errors.append(
                        f"Invalid version format: '{frontmatter['version']}' (expected semver like 1.0.0)"
                    )

            # Validate tools field
            if "tools" in frontmatter:
                if frontmatter["tools"] is not None and not isinstance(
                    frontmatter["tools"], list
                ):
                    errors.append("Field 'tools' must be a list (can be empty list)")

            # Check if agent name matches filename (warning only)
            if "name" in frontmatter and frontmatter["name"]:
                expected_name = filepath.stem  # filename without .md extension
                if frontmatter["name"] != expected_name:
                    # This is a warning, not an error
                    self.warnings.append(
                        f"{filepath}: Agent name '{frontmatter['name']}' doesn't match filename '{expected_name}'"
                    )

            # Check for 'model' field (optional but recommended)
            if "model" not in frontmatter:
                self.warnings.append(
                    f"{filepath}: Consider adding 'model' field (e.g., 'model: inherit')"
                )

        except Exception as e:
            errors.append(f"Unexpected error reading file: {e}")
            return False, errors

        return len(errors) == 0, errors

    def find_agent_files(self) -> List[Path]:
        """Find all agent files in the standard directories.

        Returns:
            List of paths to agent markdown files
        """
        agent_files = []

        for dir_path in self.AGENT_DIRECTORIES:
            directory = Path(dir_path)
            if directory.exists() and directory.is_dir():
                # Find all .md files in the directory
                for md_file in directory.glob("*.md"):
                    # Skip README files
                    if md_file.name.lower() != "readme.md":
                        agent_files.append(md_file)
                        self.log(f"Found agent file: {md_file}")

        return agent_files

    def validate_all(self) -> int:
        """Validate all agent files.

        Returns:
            Exit code (0 for success, 1 for validation failures)
        """
        # Find all agent files
        agent_files = self.find_agent_files()

        if not agent_files:
            print("ℹ️  No agent files found to validate")
            return 0

        print(f"🔍 Validating {len(agent_files)} agent file(s)...")

        failed_files = []

        for filepath in agent_files:
            is_valid, errors = self.validate_agent_file(filepath)

            if not is_valid:
                failed_files.append(filepath)
                print(f"\n❌ {filepath}")
                for error in errors:
                    print(f"   - {error}")
            else:
                print(f"✅ {filepath}")

        # Print warnings if any
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")

        # Summary
        print(
            f"\n📊 Summary: {len(agent_files) - len(failed_files)}/{len(agent_files)} files valid"
        )

        if failed_files:
            print("\n❌ Validation failed! Fix the errors above and try again.")
            print("\n💡 Common fixes:")
            print(
                "   - Ensure frontmatter is between --- markers at the start of the file"
            )
            print("   - Include all required fields: name, description, version, tools")
            print("   - Use valid semver format for version (e.g., 1.0.0)")
            print("   - Make tools field a list (can be empty: [])")
            return 1
        else:
            print("\n✅ All agent files are valid!")
            return 0


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate agent registration files for proper YAML frontmatter"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output for debugging",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix common issues (not implemented yet)",
    )

    args = parser.parse_args()

    if args.fix:
        print("⚠️  Auto-fix feature not implemented yet")
        return 1

    validator = AgentValidator(verbose=args.verbose)
    return validator.validate_all()


if __name__ == "__main__":
    sys.exit(main())
