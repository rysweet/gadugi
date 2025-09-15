#!/usr/bin/env python3
"""
Update Agent Instructions with Workflow Requirements
Adds workflow enforcement requirements to all agent markdown files.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import argparse


class AgentInstructionUpdater:
    """Updates agent markdown files with workflow enforcement requirements."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.claude_dir = self.repo_root / ".claude"
        self.agents_dir = self.claude_dir / "agents"

        self.workflow_section = """
## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**
"""

    def find_agent_files(self) -> List[Path]:
        """Find all agent markdown files."""
        agent_files = []

        if self.agents_dir.exists():
            # Find all .md files recursively
            for md_file in self.agents_dir.rglob("*.md"):
                if md_file.is_file():
                    agent_files.append(md_file)

        return sorted(agent_files)

    def has_workflow_section(self, content: str) -> bool:
        """Check if the file already has workflow enforcement section."""
        return (
            "CRITICAL: Workflow Enforcement" in content
            or "WORKFLOW ENFORCEMENT ACTIVE" in content
        )

    def update_agent_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Update a single agent file with workflow requirements.

        Returns:
            (success, message)
        """
        try:
            # Read existing content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if already updated
            if self.has_workflow_section(content):
                return True, "Already has workflow section"

            # Find insertion point (after title and before first section)
            lines = content.split("\n")
            insertion_point = 1  # Default to after first line

            # Look for title pattern
            for i, line in enumerate(lines):
                if line.startswith("# "):  # Main title
                    # Look for first ## section or content after title
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("##") or (
                            lines[j].strip() and not lines[j].startswith("#")
                        ):
                            insertion_point = j
                            break
                    break

            # Insert workflow section
            lines.insert(insertion_point, self.workflow_section)
            updated_content = "\n".join(lines)

            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Write updated content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return True, "Updated successfully"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def update_all_agents(self, dry_run: bool = False) -> Tuple[int, int, List[str]]:
        """
        Update all agent files with workflow requirements.

        Returns:
            (updated_count, total_count, error_messages)
        """
        agent_files = self.find_agent_files()
        updated_count = 0
        error_messages = []

        print(f"Found {len(agent_files)} agent files")

        for file_path in agent_files:
            relative_path = file_path.relative_to(self.repo_root)

            if dry_run:
                # Read and check only
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if self.has_workflow_section(content):
                        print(f"  ✅ {relative_path} (already has workflow section)")
                    else:
                        print(f"  📝 {relative_path} (would be updated)")
                        updated_count += 1

                except Exception as e:
                    error_msg = f"Error reading {relative_path}: {str(e)}"
                    error_messages.append(error_msg)
                    print(f"  ❌ {relative_path} (error: {str(e)})")

            else:
                # Actually update the file
                success, message = self.update_agent_file(file_path)

                if success:
                    if "Already has" in message:
                        print(f"  ✅ {relative_path} ({message})")
                    else:
                        print(f"  📝 {relative_path} ({message})")
                        updated_count += 1
                else:
                    error_messages.append(f"{relative_path}: {message}")
                    print(f"  ❌ {relative_path} ({message})")

        return updated_count, len(agent_files), error_messages

    def remove_workflow_sections(self) -> Tuple[int, int, List[str]]:
        """
        Remove workflow sections from all agent files (for testing/rollback).

        Returns:
            (updated_count, total_count, error_messages)
        """
        agent_files = self.find_agent_files()
        updated_count = 0
        error_messages = []

        print(f"Removing workflow sections from {len(agent_files)} agent files")

        for file_path in agent_files:
            relative_path = file_path.relative_to(self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Remove workflow section if present
                if self.has_workflow_section(content):
                    # Find and remove the workflow section
                    lines = content.split("\n")
                    new_lines = []
                    skip_section = False

                    for line in lines:
                        if "CRITICAL: Workflow Enforcement" in line:
                            skip_section = True
                            continue
                        elif (
                            skip_section
                            and line.startswith("##")
                            and "Workflow Enforcement" not in line
                        ):
                            skip_section = False
                        elif (
                            skip_section and "REMEMBER: This workflow protects" in line
                        ):
                            skip_section = False
                            continue

                        if not skip_section:
                            new_lines.append(line)

                    # Write updated content
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(new_lines))

                    updated_count += 1
                    print(f"  📝 {relative_path} (workflow section removed)")
                else:
                    print(f"  ✅ {relative_path} (no workflow section found)")

            except Exception as e:
                error_msg = f"Error processing {relative_path}: {str(e)}"
                error_messages.append(error_msg)
                print(f"  ❌ {relative_path} (error: {str(e)})")

        return updated_count, len(agent_files), error_messages

    def restore_backups(self) -> Tuple[int, int, List[str]]:
        """
        Restore agent files from backups.

        Returns:
            (restored_count, total_backups, error_messages)
        """
        backup_files = list(self.agents_dir.rglob("*.md.backup"))
        restored_count = 0
        error_messages = []

        print(f"Found {len(backup_files)} backup files")

        for backup_path in backup_files:
            original_path = backup_path.with_suffix("")
            relative_path = original_path.relative_to(self.repo_root)

            try:
                # Restore from backup
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_content = f.read()

                with open(original_path, "w", encoding="utf-8") as f:
                    f.write(backup_content)

                # Remove backup file
                backup_path.unlink()

                restored_count += 1
                print(f"  📁 {relative_path} (restored from backup)")

            except Exception as e:
                error_msg = f"Error restoring {relative_path}: {str(e)}"
                error_messages.append(error_msg)
                print(f"  ❌ {relative_path} (error: {str(e)})")

        return restored_count, len(backup_files), error_messages


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Update agent instructions with workflow requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --update          # Update all agent files
  %(prog)s --dry-run         # See what would be updated
  %(prog)s --remove          # Remove workflow sections
  %(prog)s --restore         # Restore from backups
        """,
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update all agent files with workflow requirements",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    parser.add_argument(
        "--remove", action="store_true", help="Remove workflow sections from all files"
    )

    parser.add_argument(
        "--restore", action="store_true", help="Restore all files from backups"
    )

    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory (default: current directory)",
    )

    args = parser.parse_args()

    # Change to repo root
    if args.repo_root != ".":
        os.chdir(args.repo_root)

    updater = AgentInstructionUpdater()

    if args.dry_run:
        print("🔍 DRY RUN: Checking what would be updated...")
        updated_count, total_count, errors = updater.update_all_agents(dry_run=True)
        print(
            f"\n📊 Summary: {updated_count} files would be updated out of {total_count} total"
        )

        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  {error}")

    elif args.update:
        print("📝 Updating all agent files with workflow requirements...")
        updated_count, total_count, errors = updater.update_all_agents(dry_run=False)
        print(f"\n📊 Summary: {updated_count} files updated out of {total_count} total")

        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  {error}")

    elif args.remove:
        print("🗑️  Removing workflow sections from all agent files...")
        updated_count, total_count, errors = updater.remove_workflow_sections()
        print(f"\n📊 Summary: {updated_count} files updated out of {total_count} total")

        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  {error}")

    elif args.restore:
        print("📁 Restoring all agent files from backups...")
        restored_count, total_backups, errors = updater.restore_backups()
        print(
            f"\n📊 Summary: {restored_count} files restored from {total_backups} backups"
        )

        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  {error}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
