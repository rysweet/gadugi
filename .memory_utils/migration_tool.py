#!/usr/bin/env python3
"""
Migration Tool for Hierarchical Memory System

This tool migrates content from the old Memory.md + GitHub Issues sync system
to the new hierarchical Markdown-based memory system.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

from memory_manager import MemoryManager, MemoryLevel
from security_manager import SecurityManager


class MigrationTool:
    """
    Tool for migrating from old Memory.md system to hierarchical memory system.
    
    Handles:
    - Parsing existing Memory.md content
    - Categorizing content into appropriate memory levels
    - Creating new memory files with proper structure
    - Validating migrated content
    - Generating migration report
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path or os.getcwd())
        self.old_memory_path = self.repo_path / ".github" / "Memory.md"
        self.memory_manager = MemoryManager(str(self.repo_path))
        self.security_manager = SecurityManager()
        self.logger = logging.getLogger(__name__)
        
        # Migration statistics
        self.stats = {
            "sections_migrated": 0,
            "entries_migrated": 0,
            "issues_found": 0,
            "files_created": 0
        }
    
    def analyze_old_memory(self) -> Dict[str, Any]:
        """Analyze existing Memory.md file structure and content"""
        if not self.old_memory_path.exists():
            return {
                "exists": False,
                "path": str(self.old_memory_path),
                "content": None
            }
        
        content = self.old_memory_path.read_text(encoding='utf-8')
        
        # Parse sections
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return {
            "exists": True,
            "path": str(self.old_memory_path),
            "size": len(content),
            "sections": sections,
            "last_updated": self._extract_last_updated(content)
        }
    
    def _extract_last_updated(self, content: str) -> Optional[str]:
        """Extract last updated timestamp from Memory.md"""
        match = re.search(r'Last Updated:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\n]*)', content)
        return match.group(1) if match else None
    
    def categorize_content(self, sections: Dict[str, str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Categorize old Memory.md sections into new memory levels
        
        Returns:
            Dictionary mapping memory levels to sections and content
        """
        categorized = {
            MemoryLevel.PROJECT: {},
            MemoryLevel.TEAM: {},
            MemoryLevel.AGENT: {},
            MemoryLevel.ORGANIZATION: {},
            MemoryLevel.KNOWLEDGE: {}
        }
        
        # Mapping rules for common sections
        section_mappings = {
            # Project level
            "Current Goals": (MemoryLevel.PROJECT, "Goals"),
            "Active Orchestration": (MemoryLevel.PROJECT, "Active Work"),
            "Phase Strategy": (MemoryLevel.PROJECT, "Implementation Phases"),
            "Shared Components Created": (MemoryLevel.PROJECT, "Architecture Components"),
            
            # Team level  
            "Code Review Summary": (MemoryLevel.TEAM, "Code Review Practices"),
            "Git Workflow Best Practices": (MemoryLevel.TEAM, "Git Workflow"),
            "Development Process": (MemoryLevel.TEAM, "Development Process"),
            
            # Agent level
            "Recent Accomplishments": (MemoryLevel.AGENT, "Accomplishments"),
            "Completed Tasks": (MemoryLevel.AGENT, "Task History"),
            "Next Steps": (MemoryLevel.AGENT, "Planned Work"),
            
            # Organization level
            "Important Context": (MemoryLevel.ORGANIZATION, "Project Context"),
            "System Maturity": (MemoryLevel.ORGANIZATION, "System Evolution"),
            "Reflections": (MemoryLevel.ORGANIZATION, "Lessons Learned"),
            
            # Knowledge level
            "Technical Excellence": (MemoryLevel.KNOWLEDGE, "Technical Patterns"),
            "Architecture Integration": (MemoryLevel.KNOWLEDGE, "Architecture Decisions"),
            "Issue Fix Summary": (MemoryLevel.KNOWLEDGE, "Problem Solutions")
        }
        
        for section_name, content in sections.items():
            # Clean and parse content
            entries = self._parse_section_content(content)
            
            # Find appropriate memory level
            mapped = False
            for pattern, (level, new_name) in section_mappings.items():
                if pattern.lower() in section_name.lower():
                    categorized[level][new_name] = entries
                    mapped = True
                    break
            
            # Default categorization if not mapped
            if not mapped:
                if any(word in section_name.lower() for word in ["review", "workflow", "practice", "guideline"]):
                    categorized[MemoryLevel.TEAM][section_name] = entries
                elif any(word in section_name.lower() for word in ["accomplishment", "complete", "task", "fix"]):
                    categorized[MemoryLevel.AGENT][section_name] = entries
                elif any(word in section_name.lower() for word in ["context", "reflection", "lesson"]):
                    categorized[MemoryLevel.ORGANIZATION][section_name] = entries
                else:
                    categorized[MemoryLevel.PROJECT][section_name] = entries
        
        return categorized
    
    def _parse_section_content(self, content: str) -> List[str]:
        """Parse section content into individual entries"""
        entries = []
        current_entry = []
        
        for line in content.strip().split('\n'):
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('#'):
                if current_entry:
                    entries.append(' '.join(current_entry))
                    current_entry = []
                continue
            
            # Bullet points indicate new entries
            if line.startswith(('- ', '* ', '+ ')):
                if current_entry:
                    entries.append(' '.join(current_entry))
                current_entry = [line[2:].strip()]
            else:
                current_entry.append(line)
        
        # Add last entry
        if current_entry:
            entries.append(' '.join(current_entry))
        
        return [e for e in entries if e and not e.isspace()]
    
    def migrate(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Perform the migration from old to new memory system
        
        Args:
            dry_run: If True, analyze but don't create files
            
        Returns:
            Migration report with statistics and issues
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "source": str(self.old_memory_path),
            "results": {},
            "issues": [],
            "statistics": {}
        }
        
        # Analyze old memory
        old_memory = self.analyze_old_memory()
        if not old_memory["exists"]:
            report["issues"].append("No existing Memory.md file found")
            return report
        
        # Categorize content
        categorized = self.categorize_content(old_memory["sections"])
        
        # Migrate each memory level
        for level, sections in categorized.items():
            if not sections:
                continue
            
            level_results = []
            
            # Determine file names based on content
            if level == MemoryLevel.PROJECT:
                files = {"context": ["Project Context", sections]}
            elif level == MemoryLevel.TEAM:
                files = {"workflow": ["Development Workflow", sections]}
            elif level == MemoryLevel.AGENT:
                files = {"orchestrator_agent": ["OrchestratorAgent Memory", sections]}
            elif level == MemoryLevel.ORGANIZATION:
                files = {"practices": ["Organizational Practices", sections]}
            elif level == MemoryLevel.KNOWLEDGE:
                files = {"patterns": ["Technical Patterns", sections]}
            else:
                files = {}
            
            for filename, (title, section_data) in files.items():
                if dry_run:
                    level_results.append({
                        "file": f"{level}/{filename}.md",
                        "sections": list(section_data.keys()),
                        "entries": sum(len(entries) for entries in section_data.values())
                    })
                else:
                    # Validate content before writing
                    all_content = '\n'.join([
                        f"## {name}\n" + '\n'.join(entries)
                        for name, entries in section_data.items()
                    ])
                    
                    security_result = self.security_manager.validate_content(
                        all_content, level, strict_mode=False
                    )
                    
                    if not security_result.is_safe and security_result.sanitized_content:
                        all_content = security_result.sanitized_content
                        report["issues"].extend(security_result.issues)
                    
                    # Write memory file
                    try:
                        self.memory_manager.write_memory(
                            level, filename, title, section_data,
                            metadata={
                                "managed_by": "migration-tool",
                                "migrated_from": "Memory.md",
                                "migration_date": datetime.now().isoformat()
                            }
                        )
                        
                        level_results.append({
                            "file": f"{level}/{filename}.md",
                            "status": "created",
                            "sections": len(section_data),
                            "entries": sum(len(entries) for entries in section_data.values())
                        })
                        
                        self.stats["files_created"] += 1
                        self.stats["sections_migrated"] += len(section_data)
                        self.stats["entries_migrated"] += sum(len(entries) for entries in section_data.values())
                        
                    except Exception as e:
                        level_results.append({
                            "file": f"{level}/{filename}.md",
                            "status": "failed",
                            "error": str(e)
                        })
                        report["issues"].append(f"Failed to create {level}/{filename}.md: {e}")
            
            report["results"][level] = level_results
        
        # Add statistics
        report["statistics"] = self.stats
        report["statistics"]["total_sections"] = len(old_memory["sections"])
        
        return report
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful"""
        validation = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": []
        }
        
        # Check each memory level
        all_memories = self.memory_manager.list_memories()
        
        for level, files in all_memories.items():
            if level == MemoryLevel.TASK:
                continue  # Skip task memories
            
            level_checks = {
                "files_found": len(files),
                "files": files,
                "readable": True,
                "valid_format": True
            }
            
            # Try to read each file
            for filename in files:
                try:
                    memory_data = self.memory_manager.read_memory(level, filename)
                    if not memory_data["exists"]:
                        level_checks["readable"] = False
                        validation["issues"].append(f"Cannot read {level}/{filename}")
                    
                    # Validate has sections
                    if not memory_data.get("sections"):
                        level_checks["valid_format"] = False
                        validation["issues"].append(f"No sections in {level}/{filename}")
                        
                except Exception as e:
                    level_checks["readable"] = False
                    validation["issues"].append(f"Error reading {level}/{filename}: {e}")
            
            validation["checks"][level] = level_checks
        
        # Overall validation
        validation["success"] = len(validation["issues"]) == 0
        validation["files_migrated"] = sum(
            len(files) for level, files in all_memories.items()
            if level != MemoryLevel.TASK
        )
        
        return validation
    
    def generate_rollback_script(self) -> str:
        """Generate a script to rollback the migration if needed"""
        script = """#!/bin/bash
# Rollback script for memory migration
# Generated: {timestamp}

echo "Rolling back memory migration..."

# Remove new memory directories
rm -rf .memory/project
rm -rf .memory/team  
rm -rf .memory/agents
rm -rf .memory/organization
rm -rf .memory/knowledge

# Restore old Memory.md if backed up
if [ -f .github/Memory.md.backup ]; then
    mv .github/Memory.md.backup .github/Memory.md
    echo "Restored original Memory.md"
fi

echo "Rollback complete"
""".format(timestamp=datetime.now().isoformat())
        
        return script


# CLI interface
if __name__ == "__main__":
    import sys
    import json
    
    tool = MigrationTool()
    
    if len(sys.argv) < 2:
        print("Usage: migration_tool.py [analyze|migrate|validate|rollback]")
        print("       migration_tool.py migrate --dry-run")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        analysis = tool.analyze_old_memory()
        print("Old Memory.md Analysis:")
        print(f"  Exists: {analysis['exists']}")
        if analysis['exists']:
            print(f"  Size: {analysis['size']} bytes")
            print(f"  Sections: {len(analysis['sections'])}")
            print(f"  Last Updated: {analysis['last_updated']}")
            print("\nSections found:")
            for section in analysis['sections'].keys():
                print(f"  - {section}")
    
    elif command == "migrate":
        dry_run = "--dry-run" in sys.argv
        print(f"Starting migration {'(DRY RUN)' if dry_run else ''}...")
        
        report = tool.migrate(dry_run=dry_run)
        
        print("\nMigration Report:")
        print(f"  Timestamp: {report['timestamp']}")
        print(f"  Statistics: {report['statistics']}")
        
        if report['issues']:
            print(f"\nIssues ({len(report['issues'])}):")
            for issue in report['issues']:
                print(f"  - {issue}")
        
        print("\nResults by level:")
        for level, results in report['results'].items():
            print(f"\n  {level}:")
            for result in results:
                print(f"    - {result}")
        
        # Save report
        report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
    
    elif command == "validate":
        print("Validating migration...")
        validation = tool.validate_migration()
        
        print(f"\nValidation Report:")
        print(f"  Success: {validation['success']}")
        print(f"  Files Migrated: {validation['files_migrated']}")
        
        if validation['issues']:
            print(f"\nIssues:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        print(f"\nChecks by level:")
        for level, checks in validation['checks'].items():
            print(f"  {level}: {checks}")
    
    elif command == "rollback":
        script = tool.generate_rollback_script()
        script_path = "rollback_migration.sh"
        
        with open(script_path, 'w') as f:
            f.write(script)
        
        os.chmod(script_path, 0o755)
        print(f"Rollback script created: {script_path}")
        print("Review the script and run './rollback_migration.sh' to rollback")
    
    else:
        print(f"Unknown command: {command}")