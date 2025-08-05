#!/usr/bin/env python3
"""
Memory Compactor - Automatic Memory.md compaction with LongTermMemoryDetails.md archiving

This module implements automatic compaction of Memory.md files when they exceed
size thresholds, moving detailed historical information to LongTermMemoryDetails.md
while preserving essential current information.
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from memory_parser import MemoryDocument, MemoryParser, MemorySection, Task, TaskStatus


class CompactionRule:
    """Defines rules for compacting specific content types"""

    def __init__(
        self,
        section_name: str,
        max_age_days: Optional[int] = None,
        max_items: Optional[int] = None,
        preserve_patterns: Optional[List[str]] = None,
        priority_preserve: bool = False,
    ):
        self.section_name = section_name
        self.max_age_days = max_age_days
        self.max_items = max_items
        self.preserve_patterns = preserve_patterns or []
        self.priority_preserve = priority_preserve

    def should_preserve(self, content: str, age_days: int = 0) -> bool:
        """Determine if content should be preserved during compaction"""
        # Always preserve if within age limit
        if self.max_age_days and age_days < self.max_age_days:
            return True

        # Check preserve patterns
        for pattern in self.preserve_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # Check for priority markers
        if self.priority_preserve and any(
            marker in content.upper()
            for marker in ["CRITICAL", "HIGH", "URGENT", "IMPORTANT"]
        ):
            return True

        return False


class MemoryCompactor:
    """Handles automatic Memory.md compaction with archiving"""

    # Default compaction rules
    DEFAULT_RULES = {
        "Current Goals": CompactionRule(
            "Current Goals", preserve_patterns=["🔄", "⏳"], priority_preserve=True
        ),
        "Completed Tasks": CompactionRule(
            "Completed Tasks", max_age_days=7, max_items=15
        ),
        "Recent Accomplishments": CompactionRule(
            "Recent Accomplishments", max_age_days=14, max_items=20
        ),
        "Reflections": CompactionRule("Reflections", max_age_days=30, max_items=10),
        "Important Context": CompactionRule(
            "Important Context", max_items=15, priority_preserve=True
        ),
        "Next Steps": CompactionRule(
            "Next Steps", preserve_patterns=["🔄", "⏳"], priority_preserve=True
        ),
    }

    # Size thresholds for triggering compaction
    DEFAULT_SIZE_THRESHOLDS = {
        "max_lines": 100,
        "max_chars": 50000,
        "target_lines": 80,  # Target size after compaction
        "min_compaction_benefit": 0.2,  # Minimum 20% size reduction
    }

    def __init__(
        self,
        memory_file_path: str,
        details_file_path: Optional[str] = None,
        rules: Optional[Dict[str, CompactionRule]] = None,
        size_thresholds: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Memory Compactor

        Args:
            memory_file_path: Path to Memory.md file
            details_file_path: Path to LongTermMemoryDetails.md (defaults to same dir)
            rules: Custom compaction rules
            size_thresholds: Custom size thresholds
        """
        self.memory_path = Path(memory_file_path)
        self.details_path = Path(
            details_file_path
            or self.memory_path.parent / "LongTermMemoryDetails.md"
        )

        self.rules = rules or self.DEFAULT_RULES.copy()
        self.size_thresholds = {**self.DEFAULT_SIZE_THRESHOLDS, **(size_thresholds or {})}

        self.parser = MemoryParser()

    def needs_compaction(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if Memory.md needs compaction

        Returns:
            Tuple of (needs_compaction, analysis_info)
        """
        if not self.memory_path.exists():
            return False, {"error": "Memory.md file not found"}

        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            line_count = len(lines)
            char_count = len(content)

            analysis = {
                "current_lines": line_count,
                "current_chars": char_count,
                "threshold_lines": self.size_thresholds["max_lines"],
                "threshold_chars": self.size_thresholds["max_chars"],
                "exceeds_line_threshold": line_count > self.size_thresholds["max_lines"],
                "exceeds_char_threshold": char_count > self.size_thresholds["max_chars"],
                "last_modified": datetime.fromtimestamp(
                    self.memory_path.stat().st_mtime
                ).isoformat(),
            }

            needs_compaction = (
                analysis["exceeds_line_threshold"] or analysis["exceeds_char_threshold"]
            )

            return needs_compaction, analysis

        except Exception as e:
            return False, {"error": str(e)}

    def compact_memory(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Perform automatic compaction of Memory.md

        Args:
            dry_run: If True, only analyze what would be compacted

        Returns:
            Compaction results and statistics
        """
        try:
            needs_compaction, analysis = self.needs_compaction()

            if not needs_compaction:
                return {
                    "success": True,
                    "compaction_needed": False,
                    "analysis": analysis,
                    "message": "No compaction needed",
                }

            # Parse current Memory.md
            memory_doc = self.parser.parse_file(str(self.memory_path))

            # Determine what to compact
            compaction_plan = self._create_compaction_plan(memory_doc)

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "compaction_needed": True,
                    "analysis": analysis,
                    "compaction_plan": compaction_plan,
                }

            # Execute compaction
            result = self._execute_compaction(memory_doc, compaction_plan)

            return {
                "success": True,
                "compaction_needed": True,
                "compaction_executed": True,
                "analysis": analysis,
                "compaction_plan": compaction_plan,
                "result": result,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_compaction_plan(self, memory_doc: MemoryDocument) -> Dict[str, Any]:
        """Create a plan for what content to compact"""
        plan = {
            "sections_to_compact": [],
            "items_to_archive": [],
            "items_to_preserve": [],
            "estimated_size_reduction": 0,
        }

        current_date = datetime.now()

        for section in memory_doc.sections:
            section_rule = self.rules.get(section.name)
            if not section_rule:
                continue

            section_analysis = self._analyze_section_for_compaction(
                section, section_rule, current_date
            )

            if section_analysis["items_to_archive"]:
                plan["sections_to_compact"].append(
                    {
                        "section_name": section.name,
                        "current_items": section_analysis["total_items"],
                        "items_to_archive": len(section_analysis["items_to_archive"]),
                        "items_to_preserve": len(section_analysis["items_to_preserve"]),
                        "estimated_chars_saved": section_analysis["chars_to_archive"],
                    }
                )

                plan["items_to_archive"].extend(section_analysis["items_to_archive"])
                plan["items_to_preserve"].extend(section_analysis["items_to_preserve"])
                plan["estimated_size_reduction"] += section_analysis["chars_to_archive"]

        return plan

    def _analyze_section_for_compaction(
        self, section: MemorySection, rule: CompactionRule, current_date: datetime
    ) -> Dict[str, Any]:
        """Analyze a section to determine what should be compacted"""
        items = self._extract_section_items(section.content)

        items_to_archive = []
        items_to_preserve = []
        chars_to_archive = 0

        for item in items:
            # Estimate age (simplified - would need more sophisticated date extraction)
            age_days = self._estimate_item_age(item, current_date)

            if rule.should_preserve(item, age_days):
                items_to_preserve.append(item)
            else:
                items_to_archive.append(item)
                chars_to_archive += len(item)

        # Apply max_items limit if specified
        if rule.max_items and len(items_to_preserve) > rule.max_items:
            # Keep most recent items
            excess_items = items_to_preserve[: -rule.max_items]
            items_to_preserve = items_to_preserve[-rule.max_items :]
            items_to_archive.extend(excess_items)
            chars_to_archive += sum(len(item) for item in excess_items)

        return {
            "total_items": len(items),
            "items_to_archive": items_to_archive,
            "items_to_preserve": items_to_preserve,
            "chars_to_archive": chars_to_archive,
        }

    def _extract_section_items(self, content: str) -> List[str]:
        """Extract individual items from section content"""
        # Split by bullet points and filter empty lines
        items = []
        current_item = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if this starts a new item (bullet point, number, etc.)
            if re.match(r"^[-*+•]\s+", line) or re.match(r"^\d+\.\s+", line):
                if current_item:
                    items.append("\n".join(current_item))
                current_item = [line]
            elif line.startswith("#"):
                # Skip section headers
                continue
            else:
                # Continuation of current item
                if current_item:
                    current_item.append(line)

        # Add final item
        if current_item:
            items.append("\n".join(current_item))

        return items

    def _estimate_item_age(self, item: str, current_date: datetime) -> int:
        """Estimate the age of an item in days (simplified heuristic)"""
        # Look for date patterns in the item
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\d{2}/\d{2}/\d{4})",  # MM/DD/YYYY
            r"(\d{1,2}/\d{1,2}/\d{2})",  # M/D/YY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, item)
            if match:
                try:
                    date_str = match.group(1)
                    if "-" in date_str:
                        item_date = datetime.strptime(date_str, "%Y-%m-%d")
                    elif "/" in date_str and len(date_str) > 8:
                        item_date = datetime.strptime(date_str, "%m/%d/%Y")
                    else:
                        item_date = datetime.strptime(date_str, "%m/%d/%y")

                    return (current_date - item_date).days
                except ValueError:
                    continue

        # Default: assume recent if no date found
        return 0

    def _execute_compaction(
        self, memory_doc: MemoryDocument, compaction_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the compaction plan"""
        # Create backup
        backup_path = self.memory_path.with_suffix(".md.backup")
        with open(self.memory_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)

        # Archive items to LongTermMemoryDetails.md
        archived_count = self._archive_items(compaction_plan["items_to_archive"])

        # Create compacted Memory.md
        compacted_content = self._create_compacted_memory(memory_doc, compaction_plan)

        # Write compacted version
        with open(self.memory_path, "w", encoding="utf-8") as f:
            f.write(compacted_content)

        # Calculate actual size reduction
        original_size = len(original_content)
        new_size = len(compacted_content)
        size_reduction = original_size - new_size
        reduction_percentage = (size_reduction / original_size) * 100

        return {
            "backup_created": str(backup_path),
            "archived_items": archived_count,
            "original_size": original_size,
            "new_size": new_size,
            "size_reduction": size_reduction,
            "reduction_percentage": reduction_percentage,
            "compacted_file": str(self.memory_path),
            "archive_file": str(self.details_path),
        }

    def _archive_items(self, items_to_archive: List[str]) -> int:
        """Archive items to LongTermMemoryDetails.md"""
        if not items_to_archive:
            return 0

        # Prepare archive content
        timestamp = datetime.now().isoformat()
        archive_section = f"\n\n## Memory Compaction Archive - {timestamp}\n\n"
        archive_section += "The following items were archived during automatic compaction:\n\n"

        for item in items_to_archive:
            archive_section += f"{item}\n\n"

        # Append to existing details file or create new one
        if self.details_path.exists():
            with open(self.details_path, "a", encoding="utf-8") as f:
                f.write(archive_section)
        else:
            # Create new details file with header
            header = f"""# AI Assistant Long-Term Memory Details
Last Updated: {timestamp}

This file contains detailed historical context and implementation details archived from Memory.md. 
For current status, see `.github/Memory.md`.

## Automatic Compaction System

This file is automatically maintained by the Memory Compactor system. When Memory.md exceeds
size thresholds, older and less critical information is automatically moved here to keep
the main memory file concise and focused on current activities.

"""
            with open(self.details_path, "w", encoding="utf-8") as f:
                f.write(header + archive_section)

        return len(items_to_archive)

    def _create_compacted_memory(
        self, memory_doc: MemoryDocument, compaction_plan: Dict[str, Any]
    ) -> str:
        """Create compacted version of Memory.md"""
        timestamp = datetime.now().isoformat()

        # Start with header
        compacted = f"""# AI Assistant Memory
Last Updated: {timestamp}

## Current Goals
"""

        # Add essential sections with preserved content
        sections_to_compact = {
            section["section_name"]: section for section in compaction_plan["sections_to_compact"]
        }

        for section in memory_doc.sections:
            if section.name in sections_to_compact:
                # Add compacted version of this section
                compacted += f"\n## {section.name}\n"

                # Add preserved items
                preserved_items = [
                    item
                    for item in compaction_plan["items_to_preserve"]
                    if any(
                        item in archived_item
                        for compaction_section in compaction_plan["sections_to_compact"]
                        if compaction_section["section_name"] == section.name
                        for archived_item in compaction_plan["items_to_archive"]
                    )
                ]

                for item in preserved_items[:10]:  # Limit to prevent over-preservation
                    compacted += f"{item}\n\n"

                # Add reference to archived content
                archived_count = sections_to_compact[section.name]["items_to_archive"]
                if archived_count > 0:
                    compacted += f"*{archived_count} items archived to LongTermMemoryDetails.md*\n\n"
            else:
                # Preserve section as-is if not being compacted
                compacted += f"\n## {section.name}\n{section.content}\n"

        # Add reference footer
        compacted += """
---
*For detailed history and implementation details, see `.github/LongTermMemoryDetails.md`*
"""

        return compacted


def main():
    """Example usage of MemoryCompactor"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python memory_compactor.py <memory_file_path> [--dry-run]")
        sys.exit(1)

    memory_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    compactor = MemoryCompactor(memory_file)

    print(f"Checking compaction needs for: {memory_file}")

    # Check if compaction is needed
    needs_compaction, analysis = compactor.needs_compaction()
    print(f"Needs compaction: {needs_compaction}")
    print(f"Analysis: {analysis}")

    if needs_compaction:
        print(f"\nPerforming compaction (dry_run={dry_run})...")
        result = compactor.compact_memory(dry_run=dry_run)

        if result["success"]:
            if dry_run:
                print("Dry run completed successfully")
                print(f"Compaction plan: {result['compaction_plan']}")
            else:
                print("Compaction completed successfully")
                print(f"Size reduction: {result['result']['reduction_percentage']:.1f}%")
                print(f"Archived items: {result['result']['archived_items']}")
        else:
            print(f"Compaction failed: {result['error']}")
            sys.exit(1)
    else:
        print("No compaction needed")


if __name__ == "__main__":
    main()