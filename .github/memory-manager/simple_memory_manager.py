#!/usr/bin/env python3
"""
Simple Memory Manager - GitHub Issues as Single Source of Truth

This module implements a simplified memory management system that uses GitHub Issues
exclusively for project memory storage, eliminating the complexity of Memory.md
synchronization and providing native GitHub integration.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sys
import os

# Add .claude/shared to path for imports
shared_path = Path(__file__).parent.parent.parent / ".claude" / "shared"
sys.path.insert(0, str(shared_path))

from github_operations import GitHubOperations, GitHubError


class MemorySection:
    """Represents a section of project memory"""

    def __init__(
        self,
        name: str,
        priority: str = "medium",
        related_issues: Optional[List[int]] = None,
    ):
        self.name = name
        self.priority = priority
        self.related_issues = related_issues or []
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "related_issues": self.related_issues,
            "timestamp": self.timestamp,
        }


class MemoryUpdate:
    """Represents a memory update"""

    def __init__(
        self,
        content: str,
        section: str,
        agent: str,
        priority: str = "medium",
        related_issues: Optional[List[int]] = None,
        related_prs: Optional[List[int]] = None,
        related_commits: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None,
    ):
        self.content = content
        self.section = section
        self.agent = agent
        self.priority = priority
        self.related_issues = related_issues or []
        self.related_prs = related_prs or []
        self.related_commits = related_commits or []
        self.related_files = related_files or []
        self.timestamp = datetime.now().isoformat()

    def format_comment(self) -> str:
        """Format memory update as structured GitHub issue comment"""

        comment = f"### {self.section.upper()} - {self.timestamp}\n\n"
        comment += f"**Type**: {self.section}\n"
        comment += f"**Priority**: {self.priority}\n"

        # Add related references
        references = []
        if self.related_issues:
            references.extend([f"#{issue}" for issue in self.related_issues])
        if self.related_prs:
            references.extend([f"#{pr}" for pr in self.related_prs])

        if references:
            comment += f"**Related**: {', '.join(references)}\n"

        comment += f"\n**Content**:\n{self.content}\n"

        # Add context links
        if self.related_commits or self.related_files:
            comment += "\n**Context Links**:\n"
            for commit in self.related_commits:
                comment += f"- Commit: {commit}\n"
            for file_path in self.related_files:
                comment += f"- File: {file_path}\n"

        comment += f"\n---\n*Added by: {self.agent}*"

        return comment


class SimpleMemoryManager:
    """
    Simplified memory manager using GitHub Issues as single source of truth.

    This replaces the complex bidirectional sync system with a streamlined
    GitHub Issues-only approach, eliminating Memory.md file operations and
    sync complexity.
    """

    MEMORY_ISSUE_TITLE = "🧠 Project Memory - AI Assistant Context"
    MEMORY_LABELS = ["enhancement"]  # Using standard GitHub labels
    DEFAULT_LOCK_REASON = "off-topic"  # Prevents non-collaborator comments

    def __init__(
        self,
        repo_path: Optional[str] = None,
        auto_lock: bool = True,
        lock_reason: Optional[str] = None,
        strict_security: bool = False,
    ):
        """
        Initialize Simple Memory Manager

        Args:
            repo_path: Path to repository (defaults to current directory)
            auto_lock: Whether to automatically lock memory issue for security (default: True)
            lock_reason: GitHub lock reason - one of: off-topic, too heated, resolved, spam (default: off-topic)
            strict_security: Enable strict security mode - fails initialization if auto-lock fails (default: False)
        """
        self.repo_path = Path(repo_path or os.getcwd())
        self.logger = logging.getLogger(__name__)
        self.auto_lock = auto_lock
        self.strict_security = strict_security
        self.lock_reason = lock_reason or self.DEFAULT_LOCK_REASON

        # Validate lock reason
        valid_reasons = ["off-topic", "too heated", "resolved", "spam"]
        if self.lock_reason not in valid_reasons:
            self.logger.warning(
                f"Invalid lock reason '{self.lock_reason}', using default"
            )
            self.lock_reason = self.DEFAULT_LOCK_REASON

        # Initialize GitHub operations using shared module
        self.github = GitHubOperations(task_id=getattr(self, "task_id", None))

        # Get or create the main memory issue
        self.memory_issue_number = self._get_or_create_memory_issue()

    def _get_or_create_memory_issue(self) -> int:
        """Get existing Project Memory issue or create new one"""
        try:
            # Search for existing memory issue
            search_result = self.github._execute_gh_command(
                ["issue", "list", "--state", "open", "--json", "number,title,labels"]
            )

            if search_result["success"] and search_result["data"]:
                for issue in search_result["data"]:
                    if issue.get("title") == self.MEMORY_ISSUE_TITLE:
                        self.logger.info(
                            f"Found existing memory issue #{issue['number']}"
                        )
                        return issue["number"]

            # Create new memory issue
            issue_body = self._create_memory_issue_body()

            result = self.github.create_issue(
                title=self.MEMORY_ISSUE_TITLE,
                body=issue_body,
                labels=self.MEMORY_LABELS,
            )

            if result["success"]:
                issue_number = result["data"]["number"]
                self.logger.info(f"Created new memory issue #{issue_number}")

                # Lock the issue if auto_lock is enabled
                if self.auto_lock:
                    if self._lock_memory_issue(issue_number):
                        self.logger.info(
                            f"Successfully locked memory issue #{issue_number} for security"
                        )
                    else:
                        error_msg = f"Failed to lock memory issue #{issue_number}"
                        if self.strict_security:
                            raise GitHubError(
                                f"{error_msg} - strict security mode enabled",
                                "lock_issue",
                                {},
                                None,
                            )
                        else:
                            self.logger.warning(f"{error_msg}, continuing anyway")

                return issue_number
            else:
                raise GitHubError(
                    "Failed to create memory issue", "create_issue", result, None
                )

        except Exception as e:
            self.logger.error(f"Failed to get or create memory issue: {e}")
            raise

    def _create_memory_issue_body(self) -> str:
        """Create the body content for the Project Memory issue"""
        return """This issue serves as the central memory store for AI assistant context.
All memory updates are added as comments below with structured formatting.

## Current Structure
- **Current Goals** (comments with 'current-goals' section)
- **Recent Accomplishments** (comments with 'completed-tasks' section)
- **Important Context** (comments with 'important-context' section)
- **Next Steps** (comments with 'next-steps' section)
- **Reflections** (comments with 'reflections' section)

## Usage
AI agents update this memory by adding structured comments with the following format:

```
### [SECTION] - [TIMESTAMP]

**Type**: Current Goals / Completed Tasks / Important Context / etc.
**Priority**: High / Medium / Low
**Related**: #123, #456 (reference related issues/PRs)

**Content**:
[Structured content here]

**Context Links**:
- PR: #123
- Commit: abc123
- Files: src/module.py

---
*Added by: [Agent Name]*
```

## Benefits
- **Single Source of Truth**: No synchronization complexity
- **Native GitHub Integration**: Built-in search, filtering, notifications
- **Team Collaboration**: Natural issue-based collaboration
- **Version History**: Complete audit trail of all changes
- **Cross-Referencing**: Native GitHub issue/PR linking

## Security
This issue is automatically locked to prevent unauthorized memory modifications.
Only repository collaborators with write access can add comments.

This approach eliminates the complexity of Memory.md file operations and provides
enhanced integration with GitHub's collaboration features."""

    def read_memory(
        self, section: Optional[str] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Read memory from GitHub Issues comments.

        Args:
            section: Filter by specific section (e.g., 'current-goals')
            limit: Maximum number of comments to retrieve

        Returns:
            Dictionary containing parsed memory data
        """
        try:
            # Get all comments from memory issue
            result = self.github._execute_gh_command(
                [
                    "issue",
                    "view",
                    str(self.memory_issue_number),
                    "--json",
                    "comments,createdAt,updatedAt",
                ]
            )

            if not result["success"]:
                raise GitHubError(
                    "Failed to read memory issue", "read_memory", result, None
                )

            issue_data = result["data"]
            comments = issue_data.get("comments", [])

            # Parse memory comments
            memory_data = {
                "issue_number": self.memory_issue_number,
                "last_updated": issue_data.get("updatedAt"),
                "total_comments": len(comments),
                "sections": {},
                "all_updates": [],
            }

            for comment in comments:
                parsed_comment = self._parse_memory_comment(comment["body"])
                if parsed_comment:
                    # Add to all updates
                    memory_data["all_updates"].append(
                        {
                            **parsed_comment,
                            "comment_id": comment.get("id"),
                            "created_at": comment.get("createdAt"),
                            "author": comment.get("author", {}).get("login", "unknown"),
                        }
                    )

                    # Group by section
                    comment_section = parsed_comment.get("section", "uncategorized")
                    if comment_section not in memory_data["sections"]:
                        memory_data["sections"][comment_section] = []

                    memory_data["sections"][comment_section].append(parsed_comment)

            # Filter by section if requested
            if section:
                memory_data["filtered_section"] = memory_data["sections"].get(
                    section, []
                )
                if limit:
                    memory_data["filtered_section"] = memory_data["filtered_section"][
                        -limit:
                    ]

            # Apply limit to all updates if specified
            if limit:
                memory_data["all_updates"] = memory_data["all_updates"][-limit:]

            return memory_data

        except Exception as e:
            self.logger.error(f"Failed to read memory: {e}")
            raise

    def _parse_memory_comment(self, comment_body: str) -> Optional[Dict[str, Any]]:
        """Parse a structured memory comment"""
        try:
            lines = comment_body.strip().split("\n")

            # Look for section header (### SECTION - TIMESTAMP)
            section_line = None
            for line in lines:
                if line.startswith("### ") and " - " in line:
                    section_line = line
                    break

            if not section_line:
                return None  # Not a structured memory comment

            # Extract section and timestamp
            header_parts = section_line[4:].split(" - ", 1)
            section = header_parts[0].lower().strip()
            timestamp = header_parts[1].strip() if len(header_parts) > 1 else None

            # Parse metadata
            parsed = {
                "section": section,
                "timestamp": timestamp,
                "priority": "medium",
                "content": "",
                "related_issues": [],
                "related_prs": [],
                "agent": "unknown",
            }

            # Parse content
            content_lines = []
            in_content = False

            for line in lines:
                if line.startswith("**Type**:"):
                    continue
                elif line.startswith("**Priority**:"):
                    parsed["priority"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("**Related**:"):
                    # Extract issue/PR references
                    refs = line.split(":", 1)[1].strip()
                    for ref in refs.split(","):
                        ref = ref.strip()
                        if ref.startswith("#"):
                            try:
                                parsed["related_issues"].append(int(ref[1:]))
                            except ValueError:
                                pass
                elif line.startswith("**Content**:"):
                    in_content = True
                    continue
                elif line.startswith("**Context Links**:"):
                    in_content = False
                    continue
                elif line.startswith("---"):
                    in_content = False
                    continue
                elif line.startswith("*Added by:"):
                    agent_part = line.split(":", 1)
                    if len(agent_part) > 1:
                        parsed["agent"] = agent_part[1].strip(" *")
                elif in_content and line.strip():
                    content_lines.append(line)

            parsed["content"] = "\n".join(content_lines).strip()

            return parsed

        except Exception as e:
            self.logger.warning(f"Failed to parse memory comment: {e}")
            return None

    def update_memory(
        self,
        content: str,
        section: str,
        agent: str,
        priority: str = "medium",
        related_issues: Optional[List[int]] = None,
        related_prs: Optional[List[int]] = None,
        related_commits: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add memory update as GitHub issue comment.

        Args:
            content: Memory content to add
            section: Memory section (e.g., 'current-goals', 'completed-tasks')
            agent: Name of the agent adding the memory
            priority: Priority level ('high', 'medium', 'low')
            related_issues: List of related issue numbers
            related_prs: List of related PR numbers
            related_commits: List of related commit hashes
            related_files: List of related file paths

        Returns:
            Result dictionary with success status and comment details
        """
        try:
            # Create memory update object
            update = MemoryUpdate(
                content=content,
                section=section,
                agent=agent,
                priority=priority,
                related_issues=related_issues,
                related_prs=related_prs,
                related_commits=related_commits,
                related_files=related_files,
            )

            # Format as comment
            comment_body = update.format_comment()

            # Add comment to memory issue
            result = self.github.add_comment(self.memory_issue_number, comment_body)

            if result["success"]:
                self.logger.info(
                    f"Added memory update to section '{section}' by {agent}"
                )
                return {
                    "success": True,
                    "comment_id": result["data"].get("id"),
                    "comment_url": result["data"].get("html_url"),
                    "section": section,
                    "agent": agent,
                    "timestamp": update.timestamp,
                }
            else:
                raise GitHubError(
                    "Failed to add memory comment", "update_memory", result, None
                )

        except Exception as e:
            self.logger.error(f"Failed to update memory: {e}")
            return {
                "success": False,
                "error": str(e),
                "section": section,
                "agent": agent,
            }

    def search_memory(
        self, query: str, section: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search memory using GitHub Issues search.

        Args:
            query: Search query
            section: Optional section filter

        Returns:
            Search results with matching memory updates
        """
        try:
            # Use GitHub's search API through the memory issue
            search_query = f"{query} in:comments"

            result = self.github._execute_gh_command(
                [
                    "search",
                    "issues",
                    "--query",
                    search_query,
                    "--json",
                    "number,title,comments",
                ]
            )

            if not result["success"]:
                raise GitHubError("Memory search failed", "search_memory", result, None)

            # Filter results to memory issue only
            search_results = []
            if result["data"]:
                for item in result["data"].get("items", []):
                    if item.get("number") == self.memory_issue_number:
                        # Parse comments for matches
                        for comment in item.get("comments", []):
                            if query.lower() in comment.get("body", "").lower():
                                parsed_comment = self._parse_memory_comment(
                                    comment["body"]
                                )
                                if parsed_comment:
                                    if (
                                        not section
                                        or parsed_comment.get("section") == section
                                    ):
                                        search_results.append(parsed_comment)

            return {
                "success": True,
                "query": query,
                "section_filter": section,
                "total_results": len(search_results),
                "results": search_results,
            }

        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return {"success": False, "error": str(e), "query": query}

    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory system status"""
        try:
            # Get memory issue details
            issue_result = self.github.get_issue(self.memory_issue_number)

            if not issue_result["success"]:
                raise GitHubError(
                    "Failed to get memory issue status",
                    "get_status",
                    issue_result,
                    None,
                )

            issue_data = issue_result["data"]

            # Get memory content
            memory_data = self.read_memory()

            return {
                "success": True,
                "memory_issue": {
                    "number": self.memory_issue_number,
                    "title": issue_data.get("title"),
                    "state": issue_data.get("state"),
                    "created_at": issue_data.get("created_at"),
                    "updated_at": issue_data.get("updated_at"),
                    "url": issue_data.get("html_url"),
                    "labels": [
                        label.get("name") for label in issue_data.get("labels", [])
                    ],
                },
                "memory_content": {
                    "total_comments": memory_data.get("total_comments", 0),
                    "sections": list(memory_data.get("sections", {}).keys()),
                    "section_counts": {
                        k: len(v) for k, v in memory_data.get("sections", {}).items()
                    },
                    "last_updated": memory_data.get("last_updated"),
                },
                "configuration": {
                    "repo_path": str(self.repo_path),
                    "memory_issue_title": self.MEMORY_ISSUE_TITLE,
                    "memory_labels": self.MEMORY_LABELS,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to get memory status: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_issue_number": self.memory_issue_number,
            }

    def cleanup_old_memory(
        self, days_old: int = 30, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Archive old memory comments by moving them to a separate issue.

        Args:
            days_old: Age threshold in days for archiving
            dry_run: If True, only report what would be archived

        Returns:
            Results of cleanup operation
        """
        try:
            # This is a placeholder for future archival functionality
            # For now, we rely on GitHub's natural issue history

            memory_data = self.read_memory()
            total_comments = memory_data.get("total_comments", 0)

            return {
                "success": True,
                "dry_run": dry_run,
                "total_comments": total_comments,
                "comments_to_archive": 0,  # Would calculate based on age
                "note": "GitHub Issues provide natural archival through issue history. Manual archival not implemented yet.",
            }

        except Exception as e:
            self.logger.error(f"Memory cleanup failed: {e}")
            return {"success": False, "error": str(e)}

    def _lock_memory_issue(self, issue_number: int) -> bool:
        """
        Lock the memory issue to prevent unauthorized modifications.

        Only collaborators with write access can comment on locked issues,
        providing protection against memory poisoning from external users.

        Args:
            issue_number: GitHub issue number to lock

        Returns:
            True if successfully locked, False otherwise
        """
        try:
            result = self.github._execute_gh_command(
                ["issue", "lock", str(issue_number), "--reason", self.lock_reason]
            )

            if result["success"]:
                self.logger.info(
                    f"Locked issue #{issue_number} with reason: {self.lock_reason}"
                )
                return True
            else:
                self.logger.error(
                    f"Failed to lock issue #{issue_number}: {result.get('error', 'Unknown error')}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Exception while locking issue #{issue_number}: {e}")
            return False

    def unlock_memory_issue(self) -> bool:
        """
        Unlock the memory issue (administrative function).

        Warning: Unlocking allows non-collaborators to comment,
        potentially enabling memory poisoning attacks.

        Returns:
            True if successfully unlocked, False otherwise
        """
        try:
            result = self.github._execute_gh_command(
                ["issue", "unlock", str(self.memory_issue_number)]
            )

            if result["success"]:
                self.logger.warning(
                    f"Unlocked memory issue #{self.memory_issue_number} - security protection disabled!"
                )
                return True
            else:
                self.logger.error(
                    f"Failed to unlock issue: {result.get('error', 'Unknown error')}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Exception while unlocking issue: {e}")
            return False

    def check_lock_status(self) -> Dict[str, Any]:
        """
        Check if the memory issue is locked.

        Returns:
            Dictionary with lock status and details
        """
        try:
            result = self.github._execute_gh_command(
                [
                    "api",
                    f"repos/:owner/:repo/issues/{self.memory_issue_number}",
                    "--jq",
                    "{ locked: .locked, lock_reason: .active_lock_reason }",
                ]
            )

            if result["success"] and result["data"]:
                return {
                    "success": True,
                    "locked": result["data"].get("locked", False),
                    "lock_reason": result["data"].get("activeLockReason", None),
                    "issue_number": self.memory_issue_number,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to get lock status"),
                }

        except Exception as e:
            self.logger.error(f"Failed to check lock status: {e}")
            return {"success": False, "error": str(e)}

    def lock_memory_issue(self) -> bool:
        """
        Manually lock the memory issue for security.
        This is the public interface to _lock_memory_issue.

        Returns:
            True if successfully locked, False otherwise
        """
        return self._lock_memory_issue(self.memory_issue_number)

    def get_security_status(self) -> Dict[str, Any]:
        """
        Get comprehensive security status of the memory system.

        Returns:
            Dictionary with security status information including:
            - success: Whether the check was successful
            - security_level: HIGH/MEDIUM/LOW
            - locked: Whether memory issue is locked
            - auto_lock_enabled: Whether auto-lock is configured
            - strict_security_enabled: Whether strict security mode is enabled
            - warnings: List of security warnings
            - recommendations: List of security recommendations
        """
        try:
            # Check if memory issue is locked
            lock_status = self.check_lock_status()
            is_locked = (
                lock_status.get("locked", False)
                if lock_status.get("success")
                else False
            )

            # Determine security level
            security_level = (
                "HIGH"
                if (is_locked and self.auto_lock and self.strict_security)
                else "MEDIUM"
                if (is_locked or self.auto_lock)
                else "LOW"
            )

            # Collect warnings and recommendations
            warnings = []
            recommendations = []

            if not is_locked:
                warnings.append(
                    "Memory issue is NOT locked - vulnerable to memory poisoning attacks from non-collaborators"
                )
                recommendations.append(
                    "Lock the memory issue using lock_memory_issue() method"
                )

            if not self.auto_lock:
                warnings.append(
                    "Auto-lock is disabled - new memory issues won't be automatically protected"
                )
                recommendations.append(
                    "Enable auto_lock=True in constructor for automatic protection"
                )

            if self.auto_lock and not is_locked:
                warnings.append(
                    "Auto-lock is enabled but memory issue is not locked - auto-lock may have failed"
                )
                recommendations.append(
                    "Check GitHub permissions and manually lock the issue"
                )

            if not self.strict_security:
                warnings.append(
                    "Strict security mode is disabled - initialization won't fail on lock failures"
                )
                recommendations.append(
                    "Enable strict_security=True for maximum security"
                )

            return {
                "success": True,
                "security_level": security_level,
                "locked": is_locked,
                "auto_lock_enabled": self.auto_lock,
                "strict_security_enabled": self.strict_security,
                "warnings": warnings,
                "recommendations": recommendations,
                "memory_issue_number": self.memory_issue_number,
            }

        except Exception as e:
            self.logger.error(f"Failed to get security status: {e}")
            return {
                "success": False,
                "error": str(e),
                "security_level": "UNKNOWN",
                "locked": False,
                "auto_lock_enabled": self.auto_lock,
                "strict_security_enabled": self.strict_security,
                "warnings": [f"Security status check failed: {e}"],
                "recommendations": ["Fix the underlying error and try again"],
            }
