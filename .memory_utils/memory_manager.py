#!/usr/bin/env python3
"""
Hierarchical Memory Manager - Simple file-based memory management for Gadugi

This module provides a simplified memory management system using pure Markdown files
organized in a hierarchical structure, replacing the complex GitHub Issues sync system.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import logging


class MemoryLevel:
    """Memory hierarchy levels"""

    PROJECT = "project"
    TEAM = "team"
    AGENT = "agents"
    ORGANIZATION = "organization"
    KNOWLEDGE = "knowledge"
    TASK = "tasks"

    ALL_LEVELS = [PROJECT, TEAM, AGENT, ORGANIZATION, KNOWLEDGE, TASK]
    PERSISTENT_LEVELS = [
        PROJECT,
        TEAM,
        AGENT,
        ORGANIZATION,
        KNOWLEDGE,
    ]  # Checked into git


class MemoryEntry:
    """Represents a single memory entry with timestamp"""

    def __init__(self, content: str, timestamp: Optional[datetime] = None):
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def format(self) -> str:
        """Format entry with timestamp prefix"""
        return f"- {self.timestamp.isoformat()} - {self.content}"

    @classmethod
    def parse(cls, line: str) -> Optional["MemoryEntry"]:
        """Parse a formatted memory entry line"""
        match = re.match(
            r"^- (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*) - (.+)$", line
        )
        if match:
            timestamp_str, content = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                return cls(content, timestamp)
            except:
                pass
        return None


class MemorySection:
    """Represents a section within a memory file"""

    def __init__(self, name: str):
        self.name = name
        self.entries: List[MemoryEntry] = []
        self.last_updated = datetime.now()

    def add_entry(self, content: str, timestamp: Optional[datetime] = None):
        """Add a new entry to the section"""
        entry = MemoryEntry(content, timestamp)
        self.entries.append(entry)
        self.entries.sort(key=lambda e: e.timestamp, reverse=True)  # Most recent first
        self.last_updated = datetime.now()

    def format(self) -> str:
        """Format section as Markdown"""
        lines = [f"## {self.name}", f"*Updated: {self.last_updated.isoformat()}*", ""]
        for entry in self.entries:
            lines.append(entry.format())
        return "\n".join(lines)


class MemoryManager:
    """
    Simplified memory manager for hierarchical Markdown-based memory system.

    This replaces the complex GitHub Issues sync with simple file operations.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize Memory Manager with repository path"""
        self.repo_path = Path(repo_path or os.getcwd())
        self.memory_root = self.repo_path / ".memory"
        self.logger = logging.getLogger(__name__)

        # Ensure directory structure exists
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        """Create memory directory structure if it doesn't exist"""
        for level in MemoryLevel.ALL_LEVELS:
            level_path = self.memory_root / level
            level_path.mkdir(parents=True, exist_ok=True)

    def read_memory(self, level: str, filename: str) -> Dict[str, Any]:
        """
        Read a memory file and parse its contents

        Args:
            level: Memory level (project, team, agent, etc.)
            filename: Name of the memory file (without .md extension)

        Returns:
            Dictionary with parsed memory content
        """
        if level not in MemoryLevel.ALL_LEVELS:
            raise ValueError(f"Invalid memory level: {level}")

        filepath = self.memory_root / level / f"{filename}.md"
        if not filepath.exists():
            return {
                "exists": False,
                "path": str(filepath),
                "level": level,
                "sections": {},
            }

        try:
            content = filepath.read_text(encoding="utf-8")
            sections = self._parse_memory_content(content)

            # Extract metadata
            metadata = {
                "last_updated": None,
                "memory_level": level,
                "security_level": "public",
                "managed_by": None,
            }

            # Parse header metadata
            for line in content.split("\n"):
                if line.startswith("*Last Updated:"):
                    match = re.search(
                        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\*]*)", line
                    )
                    if match:
                        metadata["last_updated"] = match.group(1)
                elif line.startswith("*Memory Level:"):
                    metadata["memory_level"] = line.split(":")[1].strip().rstrip("*")
                elif line.startswith("*Security level:"):
                    metadata["security_level"] = line.split(":")[1].strip().rstrip("*")
                elif line.startswith("*Memory managed by:"):
                    metadata["managed_by"] = line.split(":")[1].strip().rstrip("*")

            return {
                "exists": True,
                "path": str(filepath),
                "level": level,
                "metadata": metadata,
                "sections": sections,
            }

        except Exception as e:
            self.logger.error(f"Error reading memory file {filepath}: {e}")
            raise

    def _parse_memory_content(self, content: str) -> Dict[str, MemorySection]:
        """Parse Markdown content into memory sections"""
        sections = {}
        current_section = None

        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for section header
            if line.startswith("## "):
                section_name = line[3:].strip()
                current_section = MemorySection(section_name)
                sections[section_name] = current_section

                # Look for update timestamp on next line
                if i + 1 < len(lines) and lines[i + 1].startswith("*Updated:"):
                    match = re.search(
                        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\*]*)", lines[i + 1]
                    )
                    if match:
                        current_section.last_updated = datetime.fromisoformat(
                            match.group(1).replace("Z", "+00:00")
                        )
                    i += 1  # Skip the timestamp line

            # Parse memory entries
            elif current_section and line.startswith("- "):
                entry = MemoryEntry.parse(line)
                if entry:
                    current_section.entries.append(entry)

            i += 1

        return sections

    def write_memory(
        self,
        level: str,
        filename: str,
        title: str,
        sections: Dict[str, List[str]],
        metadata: Optional[Dict[str, str]] = None,
    ):
        """
        Write or update a memory file

        Args:
            level: Memory level (project, team, agent, etc.)
            filename: Name of the memory file (without .md extension)
            title: Title for the memory file
            sections: Dictionary of section names to list of memory entries
            metadata: Optional metadata (security_level, managed_by, etc.)
        """
        if level not in MemoryLevel.ALL_LEVELS:
            raise ValueError(f"Invalid memory level: {level}")

        filepath = self.memory_root / level / f"{filename}.md"

        # Build content
        lines = [
            f"# {title}",
            f"*Last Updated: {datetime.now().isoformat()}*",
            f"*Memory Level: {level}*",
            "",
        ]

        # Add overview if provided
        if "Overview" in sections:
            lines.extend(
                [
                    "## Overview",
                    sections["Overview"][0] if sections["Overview"] else "",
                    "",
                ]
            )
            del sections["Overview"]

        # Add other sections
        for section_name, entries in sections.items():
            section = MemorySection(section_name)
            for entry in entries:
                section.add_entry(entry)
            lines.extend([section.format(), ""])

        # Add footer metadata
        if metadata is None:
            metadata = {}
        lines.extend(
            [
                "---",
                f"*Memory managed by: {metadata.get('managed_by', 'memory-manager')}*",
                f"*Security level: {metadata.get('security_level', 'public')}*",
            ]
        )

        # Write file
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("\n".join(lines), encoding="utf-8")

        self.logger.info(f"Wrote memory file: {filepath}")

    def add_memory_entry(self, level: str, filename: str, section: str, content: str):
        """
        Add a single entry to an existing memory file

        Args:
            level: Memory level
            filename: Memory file name (without .md)
            section: Section name to add entry to
            content: Entry content
        """
        # Read existing memory
        memory_data = self.read_memory(level, filename)

        if not memory_data["exists"]:
            # Create new memory file
            self.write_memory(
                level,
                filename,
                filename.replace("-", " ").title(),
                {section: [content]},
            )
            return

        # Parse existing content and add new entry
        filepath = Path(memory_data["path"])
        content_lines = filepath.read_text(encoding="utf-8").split("\n")

        # Find section or create it
        section_found = False

        for i, line in enumerate(content_lines):
            if line.strip() == f"## {section}":
                section_found = True
                # Find where to insert (after timestamp line and blank line)
                j = i + 1
                while j < len(content_lines) and (
                    content_lines[j].startswith("*Updated:")
                    or content_lines[j].strip() == ""
                ):
                    j += 1

                # Insert new entry at the beginning of the section
                timestamp = datetime.now().isoformat()
                new_entry = f"- {timestamp} - {content}"
                content_lines.insert(j, new_entry)

                # Update section timestamp
                for k in range(i, j):
                    if content_lines[k].startswith("*Updated:"):
                        content_lines[k] = f"*Updated: {timestamp}*"
                        break
                break

        if not section_found:
            # Add new section before the footer
            footer_index = len(content_lines) - 1
            while footer_index > 0 and (
                content_lines[footer_index].startswith("*")
                or content_lines[footer_index].strip() == "---"
                or content_lines[footer_index].strip() == ""
            ):
                footer_index -= 1

            timestamp = datetime.now().isoformat()
            new_section = [
                "",
                f"## {section}",
                f"*Updated: {timestamp}*",
                "",
                f"- {timestamp} - {content}",
            ]

            for line in reversed(new_section):
                content_lines.insert(footer_index + 1, line)

        # Update last updated timestamp
        for i, line in enumerate(content_lines):
            if line.startswith("*Last Updated:"):
                content_lines[i] = f"*Last Updated: {datetime.now().isoformat()}*"
                break

        # Write updated content
        filepath.write_text("\n".join(content_lines), encoding="utf-8")
        self.logger.info(f"Added entry to {filepath} in section '{section}'")

    def list_memories(self, level: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all memory files by level

        Args:
            level: Optional specific level to list (None for all levels)

        Returns:
            Dictionary mapping levels to list of memory filenames
        """
        result = {}

        levels_to_check = [level] if level else MemoryLevel.ALL_LEVELS

        for memory_level in levels_to_check:
            level_path = self.memory_root / memory_level
            if level_path.exists():
                memory_files = [f.stem for f in level_path.glob("*.md") if f.is_file()]
                result[memory_level] = sorted(memory_files)
            else:
                result[memory_level] = []

        return result

    def search_memories(
        self, query: str, level: Optional[str] = None
    ) -> List[Tuple[str, str, str]]:
        """
        Search for content across memory files

        Args:
            query: Search query (case-insensitive)
            level: Optional level to restrict search to

        Returns:
            List of tuples (level, filename, matching_line)
        """
        results = []
        query_lower = query.lower()

        levels_to_search = [level] if level else MemoryLevel.ALL_LEVELS

        for memory_level in levels_to_search:
            level_path = self.memory_root / memory_level
            if not level_path.exists():
                continue

            for filepath in level_path.glob("*.md"):
                try:
                    content = filepath.read_text(encoding="utf-8")
                    for line_num, line in enumerate(content.split("\n"), 1):
                        if query_lower in line.lower():
                            results.append(
                                (
                                    memory_level,
                                    filepath.stem,
                                    f"Line {line_num}: {line.strip()}",
                                )
                            )
                except Exception as e:
                    self.logger.warning(f"Error searching {filepath}: {e}")

        return results


# Simple CLI interface for testing
if __name__ == "__main__":
    import sys

    manager = MemoryManager()

    if len(sys.argv) < 2:
        print("Usage: memory_manager.py [list|read|add|search] ...")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        memories = manager.list_memories()
        for level, files in memories.items():
            print(f"\n{level}:")
            for file in files:
                print(f"  - {file}")

    elif command == "read" and len(sys.argv) >= 4:
        level = sys.argv[2]
        filename = sys.argv[3]
        data = manager.read_memory(level, filename)
        print(json.dumps(data, indent=2, default=str))

    elif command == "add" and len(sys.argv) >= 6:
        level = sys.argv[2]
        filename = sys.argv[3]
        section = sys.argv[4]
        content = " ".join(sys.argv[5:])
        manager.add_memory_entry(level, filename, section, content)
        print(f"Added entry to {level}/{filename} in section '{section}'")

    elif command == "search" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        results = manager.search_memories(query)
        for level, filename, match in results:
            print(f"{level}/{filename}: {match}")

    else:
        print("Invalid command or arguments")
        sys.exit(1)
