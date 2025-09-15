#!/usr/bin/env python3
"""
Memory.md Parser - Extract tasks, goals, and context from Memory.md files

This module provides functionality to parse Memory.md files and extract structured
information including tasks, goals, accomplishments, and context for integration
with GitHub Issues and project management systems.
"""

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Task status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """Task priority enumeration"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """Represents a task extracted from Memory.md"""

    id: str
    content: str
    status: TaskStatus
    priority: TaskPriority
    section: str
    line_number: int
    metadata: Dict[str, Any] = None
    issue_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        result = asdict(self)
        result["status"] = self.status.value
        result["priority"] = self.priority.value
        return result


@dataclass
class MemorySection:
    """Represents a section from Memory.md"""

    name: str
    content: str
    level: int
    line_start: int
    line_end: int
    tasks: List[Task] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []


@dataclass
class MemoryDocument:
    """Represents the parsed Memory.md document"""

    last_updated: Optional[datetime]
    sections: List[MemorySection]
    tasks: List[Task]
    metadata: Dict[str, Any]
    raw_content: str
    file_path: str

    def get_section(self, name: str) -> Optional[MemorySection]:
        """Get section by name"""
        for section in self.sections:
            if section.name.lower() == name.lower():
                return section
        return None

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status"""
        return [task for task in self.tasks if task.status == status]

    def get_tasks_by_section(self, section_name: str) -> List[Task]:
        """Get tasks from specific section"""
        return [
            task for task in self.tasks if task.section.lower() == section_name.lower()
        ]


class MemoryParser:
    """Parser for Memory.md files"""

    # Task patterns for different formats
    TASK_PATTERNS = [
        # Completed tasks with checkmark emoji
        (r"^- ✅ (.+)", TaskStatus.COMPLETED),
        # Completed tasks with [x] format
        (r"^- \[x\] (.+)", TaskStatus.COMPLETED),
        # Pending tasks with [ ] format
        (r"^- \[ \] (.+)", TaskStatus.PENDING),
        # Bold priority markers
        (r"^- \*\*([A-Z]+)\*\*: (.+)", TaskStatus.PENDING),
        # General bullet points (default to pending)
        (r"^- (.+)", TaskStatus.PENDING),
    ]

    # Section headers pattern
    SECTION_PATTERN = r"^(#{1,6})\s+(.+)"

    # Priority detection patterns
    PRIORITY_PATTERNS = [
        (r"\*\*(CRITICAL|HIGH|URGENT)\*\*", TaskPriority.HIGH),
        (r"\*\*(MEDIUM|NORMAL)\*\*", TaskPriority.MEDIUM),
        (r"\*\*(LOW|MINOR)\*\*", TaskPriority.LOW),
    ]

    # Issue reference pattern
    ISSUE_PATTERN = r"#(\d+)"

    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), status)
            for pattern, status in self.TASK_PATTERNS
        ]
        self.section_pattern = re.compile(self.SECTION_PATTERN)
        self.priority_patterns = [
            (re.compile(pattern, re.IGNORECASE), priority)
            for pattern, priority in self.PRIORITY_PATTERNS
        ]
        self.issue_pattern = re.compile(self.ISSUE_PATTERN)

    def parse_file(self, file_path: str) -> MemoryDocument:
        """Parse Memory.md file and return structured document"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Memory.md file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content, str(path))

    def parse_content(self, content: str, file_path: str = "") -> MemoryDocument:
        """Parse Memory.md content and return structured document"""
        lines = content.split("\n")

        # Extract metadata
        last_updated = self._extract_last_updated(lines)

        # Parse sections
        sections = self._parse_sections(lines)

        # Extract tasks from all sections
        tasks = self._extract_tasks(lines, sections)

        # Build metadata
        metadata = self._build_metadata(content, sections, tasks)

        return MemoryDocument(
            last_updated=last_updated,
            sections=sections,
            tasks=tasks,
            metadata=metadata,
            raw_content=content,
            file_path=file_path,
        )

    def _extract_last_updated(self, lines: List[str]) -> Optional[datetime]:
        """Extract last updated timestamp from Memory.md"""
        for line in lines[:10]:  # Check first 10 lines
            if "Last Updated:" in line:
                # Extract ISO timestamp
                match = re.search(
                    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})", line
                )
                if match:
                    try:
                        return datetime.fromisoformat(match.group(1))
                    except ValueError:
                        pass
        return None

    def _parse_sections(self, lines: List[str]) -> List[MemorySection]:
        """Parse sections from Memory.md"""
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            match = self.section_pattern.match(line)
            if match:
                # Save previous section
                if current_section:
                    current_section.line_end = i - 1
                    sections.append(current_section)

                # Start new section
                level = len(match.group(1))
                name = match.group(2).strip()
                current_section = MemorySection(
                    name=name,
                    content="",
                    level=level,
                    line_start=i,
                    line_end=len(lines) - 1,
                )
            elif current_section:
                current_section.content += line + "\n"

        # Add final section
        if current_section:
            sections.append(current_section)

        return sections

    def _extract_tasks(
        self, lines: List[str], sections: List[MemorySection]
    ) -> List[Task]:
        """Extract tasks from all sections"""
        tasks = []
        task_id_counter = 1

        # Find which section each line belongs to
        section_map = {}
        for section in sections:
            for i in range(section.line_start, min(section.line_end + 1, len(lines))):
                section_map[i] = section.name

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Try to match task patterns
            for pattern, default_status in self.compiled_patterns:
                match = pattern.match(stripped)
                if match:
                    # Extract task content
                    if len(match.groups()) == 2:  # Priority pattern
                        priority_text = match.group(1)
                        content = match.group(2).strip()
                        priority = self._extract_priority_from_text(priority_text)
                    else:
                        content = match.group(1).strip()
                        priority = self._extract_priority(content)

                    # Determine section
                    section_name = section_map.get(i, "Unknown")

                    # Extract issue references
                    issue_number = self._extract_issue_number(content)

                    # Create task
                    task = Task(
                        id=f"task-{task_id_counter:03d}",
                        content=content,
                        status=default_status,
                        priority=priority,
                        section=section_name,
                        line_number=i + 1,
                        issue_number=issue_number,
                        metadata={},
                    )

                    tasks.append(task)
                    task_id_counter += 1
                    break

        return tasks

    def _extract_priority(self, content: str) -> TaskPriority:
        """Extract priority from task content"""
        for pattern, priority in self.priority_patterns:
            if pattern.search(content):
                return priority
        return TaskPriority.MEDIUM  # Default priority

    def _extract_priority_from_text(self, text: str) -> TaskPriority:
        """Extract priority from explicit priority text"""
        text_upper = text.upper()
        if text_upper in ["CRITICAL", "HIGH", "URGENT"]:
            return TaskPriority.HIGH
        elif text_upper in ["MEDIUM", "NORMAL"]:
            return TaskPriority.MEDIUM
        elif text_upper in ["LOW", "MINOR"]:
            return TaskPriority.LOW
        return TaskPriority.MEDIUM

    def _extract_issue_number(self, content: str) -> Optional[int]:
        """Extract GitHub issue number from content"""
        match = self.issue_pattern.search(content)
        if match:
            return int(match.group(1))
        return None

    def _build_metadata(
        self, content: str, sections: List[MemorySection], tasks: List[Task]
    ) -> Dict[str, Any]:
        """Build document metadata"""
        return {
            "total_lines": len(content.split("\n")),
            "total_sections": len(sections),
            "total_tasks": len(tasks),
            "completed_tasks": len(
                [t for t in tasks if t.status == TaskStatus.COMPLETED]
            ),
            "pending_tasks": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "sections_with_tasks": len(
                [s for s in sections if any(t.section == s.name for t in tasks)]
            ),
            "avg_tasks_per_section": len(tasks) / max(len(sections), 1),
            "issue_references": len([t for t in tasks if t.issue_number is not None]),
        }

    def update_task_status(
        self, content: str, task_id: str, new_status: TaskStatus
    ) -> str:
        """Update task status in Memory.md content"""
        # This would be implemented to modify the content
        # For now, return unchanged content
        return content

    def add_task_metadata(
        self, content: str, task_id: str, metadata: Dict[str, Any]
    ) -> str:
        """Add metadata to task in Memory.md content"""
        # This would be implemented to add HTML comments with metadata
        # For now, return unchanged content
        return content


def main():
    """Example usage of MemoryParser"""
    parser = MemoryParser()

    try:
        # Parse the current Memory.md file
        memory_path = "/Users/ryan/src/gadugi/.github/Memory.md"
        doc = parser.parse_file(memory_path)

        print(f"Parsed Memory.md: {len(doc.tasks)} tasks found")
        print(f"Sections: {[s.name for s in doc.sections]}")
        print(f"Completed tasks: {len(doc.get_tasks_by_status(TaskStatus.COMPLETED))}")
        print(f"Pending tasks: {len(doc.get_tasks_by_status(TaskStatus.PENDING))}")

        # Show sample tasks
        print("\nSample tasks:")
        for task in doc.tasks[:5]:
            print(f"  {task.id}: {task.content[:50]}... [{task.status.value}]")

    except Exception as e:
        print(f"Error parsing Memory.md: {e}")


if __name__ == "__main__":
    main()
