#!/usr/bin/env python3
"""
GitHub Issues Integration - Manage GitHub issues for Memory.md tasks

This module provides functionality to create, update, and synchronize GitHub issues
based on tasks extracted from Memory.md files.
"""

import json
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import tempfile
import os

from memory_parser import Task, TaskStatus, TaskPriority, MemoryDocument


@dataclass
class GitHubIssue:
    """Represents a GitHub issue"""
    number: int
    title: str
    body: str
    state: str  # open, closed
    labels: List[str]
    assignees: List[str]
    created_at: datetime
    updated_at: datetime
    html_url: str
    memory_task_id: Optional[str] = None
    
    @classmethod
    def from_gh_json(cls, issue_data: Dict[str, Any]) -> 'GitHubIssue':
        """Create GitHubIssue from GitHub CLI JSON response"""
        return cls(
            number=issue_data['number'],
            title=issue_data['title'],
            body=issue_data.get('body', ''),
            state=issue_data['state'],
            labels=[label['name'] for label in issue_data.get('labels', [])],
            assignees=[assignee['login'] for assignee in issue_data.get('assignees', [])],
            created_at=datetime.fromisoformat(issue_data['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(issue_data['updatedAt'].replace('Z', '+00:00')),
            html_url=issue_data['htmlUrl'],
            memory_task_id=cls._extract_memory_task_id(issue_data.get('body', ''))
        )
    
    @staticmethod
    def _extract_memory_task_id(body: str) -> Optional[str]:
        """Extract memory task ID from issue body"""
        import re
        match = re.search(r'<!-- memory-task-id: ([^>]+) -->', body)
        return match.group(1) if match else None


class GitHubIntegration:
    """Manages GitHub Issues integration for Memory.md tasks"""
    
    # Default labels for memory-sync issues
    DEFAULT_LABELS = ["memory-sync", "ai-assistant"]
    
    # Issue templates
    TASK_ISSUE_TEMPLATE = """# Memory.md Task

{content}

## Task Details
- **Source**: Memory.md `{section}` section
- **Priority**: {priority}
- **Status**: {status}
- **Line**: {line_number}

## Context
This issue was automatically created from a Memory.md task to enable better project visibility and collaboration.

## AI Assistant Attribution
*Note: This issue was created by an AI agent on behalf of the repository owner.*

<!-- memory-task-id: {task_id} -->
<!-- memory-sync-metadata: {metadata} -->
"""
    
    def __init__(self, repo_path: str = None):
        """Initialize GitHub integration"""
        self.repo_path = repo_path or os.getcwd()
        self._validate_gh_cli()
    
    def _validate_gh_cli(self):
        """Validate GitHub CLI is available and authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True, cwd=self.repo_path)
            if result.returncode != 0:
                raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
        except FileNotFoundError:
            raise RuntimeError("GitHub CLI not found. Install with 'brew install gh' or equivalent")
    
    def create_issue_from_task(self, task: Task, additional_context: str = "") -> GitHubIssue:
        """Create GitHub issue from Memory.md task"""
        # Generate issue title (truncate if too long)
        title = self._generate_issue_title(task)
        
        # Generate issue body using template
        body = self.TASK_ISSUE_TEMPLATE.format(
            content=task.content,
            section=task.section,
            priority=task.priority.value.title(),
            status=task.status.value.replace('_', ' ').title(),
            line_number=task.line_number,
            task_id=task.id,
            metadata=json.dumps(task.metadata or {})
        )
        
        if additional_context:
            body += f"\n\n## Additional Context\n{additional_context}"
        
        # Determine labels
        labels = self.DEFAULT_LABELS.copy()
        labels.append(f"priority:{task.priority.value}")
        if task.status == TaskStatus.COMPLETED:
            labels.append("completed")
        
        # Create issue using GitHub CLI
        issue_data = self._create_gh_issue(title, body, labels)
        
        # Update task with issue number
        task.issue_number = issue_data['number']
        
        return GitHubIssue.from_gh_json(issue_data)
    
    def update_issue_from_task(self, issue_number: int, task: Task) -> GitHubIssue:
        """Update existing GitHub issue from Memory.md task"""
        title = self._generate_issue_title(task)
        
        body = self.TASK_ISSUE_TEMPLATE.format(
            content=task.content,
            section=task.section,
            priority=task.priority.value.title(),
            status=task.status.value.replace('_', ' ').title(),
            line_number=task.line_number,
            task_id=task.id,
            metadata=json.dumps(task.metadata or {})
        )
        
        # Update issue state based on task status
        if task.status == TaskStatus.COMPLETED:
            self._close_issue(issue_number)
        else:
            self._reopen_issue(issue_number)
        
        # Update issue content
        issue_data = self._update_gh_issue(issue_number, title, body)
        
        return GitHubIssue.from_gh_json(issue_data)
    
    def get_all_memory_issues(self) -> List[GitHubIssue]:
        """Get all GitHub issues with memory-sync label"""
        try:
            cmd = ['gh', 'issue', 'list', '--label', 'memory-sync', '--json', 
                   'number,title,body,state,labels,assignees,createdAt,updatedAt,url']
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to list issues: {result.stderr}")
            
            issues_data = json.loads(result.stdout)
            return [GitHubIssue.from_gh_json(issue) for issue in issues_data]
            
        except Exception as e:
            print(f"Error getting memory issues: {e}")
            return []
    
    def get_issue_by_number(self, issue_number: int) -> Optional[GitHubIssue]:
        """Get specific issue by number"""
        try:
            cmd = ['gh', 'issue', 'view', str(issue_number), '--json',
                   'number,title,body,state,labels,assignees,createdAt,updatedAt,url']
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                return None
            
            issue_data = json.loads(result.stdout)
            return GitHubIssue.from_gh_json(issue_data)
            
        except Exception:
            return None
    
    def close_completed_tasks(self, tasks: List[Task]) -> List[int]:
        """Close GitHub issues for completed tasks"""
        closed_issues = []
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED and task.issue_number:
                try:
                    self._close_issue(task.issue_number)
                    closed_issues.append(task.issue_number)
                except Exception as e:
                    print(f"Failed to close issue #{task.issue_number}: {e}")
        
        return closed_issues
    
    def sync_memory_with_issues(self, memory_doc: MemoryDocument) -> Dict[str, Any]:
        """Synchronize Memory.md tasks with GitHub issues"""
        sync_stats = {
            'created_issues': 0,
            'updated_issues': 0,
            'closed_issues': 0,
            'errors': []
        }
        
        # Get existing memory issues
        existing_issues = {issue.memory_task_id: issue for issue in self.get_all_memory_issues() 
                          if issue.memory_task_id}
        
        for task in memory_doc.tasks:
            try:
                if task.id in existing_issues:
                    # Update existing issue
                    issue = existing_issues[task.id]
                    self.update_issue_from_task(issue.number, task)
                    sync_stats['updated_issues'] += 1
                else:
                    # Create new issue
                    self.create_issue_from_task(task)
                    sync_stats['created_issues'] += 1
                    
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Failed to sync task {task.id}: {e}"
                sync_stats['errors'].append(error_msg)
                print(error_msg)
        
        return sync_stats
    
    def _generate_issue_title(self, task: Task) -> str:
        """Generate GitHub issue title from task"""
        # Remove markdown formatting and truncate
        title = task.content.replace('**', '').replace('*', '').replace('`', '')
        
        # Add priority prefix for high priority tasks
        if task.priority == TaskPriority.HIGH:
            title = f"[HIGH] {title}"
        
        # Truncate to reasonable length
        if len(title) > 80:
            title = title[:77] + "..."
        
        return title
    
    def _create_gh_issue(self, title: str, body: str, labels: List[str]) -> Dict[str, Any]:
        """Create GitHub issue using CLI"""
        # Write body to temporary file to handle special characters
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(body)
            body_file = f.name
        
        try:
            cmd = ['gh', 'issue', 'create', 
                   '--title', title,
                   '--body-file', body_file,
                   '--label', ','.join(labels),
                   '--json', 'number,title,body,state,labels,assignees,createdAt,updatedAt,url']
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create issue: {result.stderr}")
            
            return json.loads(result.stdout)
            
        finally:
            os.unlink(body_file)
    
    def _update_gh_issue(self, issue_number: int, title: str, body: str) -> Dict[str, Any]:
        """Update GitHub issue using CLI"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(body)
            body_file = f.name
        
        try:
            cmd = ['gh', 'issue', 'edit', str(issue_number),
                   '--title', title,
                   '--body-file', body_file,
                   '--json', 'number,title,body,state,labels,assignees,createdAt,updatedAt,url']
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to update issue: {result.stderr}")
            
            return json.loads(result.stdout)
            
        finally:
            os.unlink(body_file)
    
    def _close_issue(self, issue_number: int):
        """Close GitHub issue"""
        cmd = ['gh', 'issue', 'close', str(issue_number)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to close issue #{issue_number}: {result.stderr}")
    
    def _reopen_issue(self, issue_number: int):
        """Reopen GitHub issue"""
        cmd = ['gh', 'issue', 'reopen', str(issue_number)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to reopen issue #{issue_number}: {result.stderr}")


def main():
    """Example usage of GitHubIntegration"""
    from memory_parser import MemoryParser
    
    try:
        # Parse Memory.md
        parser = MemoryParser()
        memory_path = "/Users/ryan/src/gadugi/.github/Memory.md"
        doc = parser.parse_file(memory_path)
        
        # Initialize GitHub integration
        gh = GitHubIntegration("/Users/ryan/src/gadugi")
        
        print(f"Found {len(doc.tasks)} tasks in Memory.md")
        
        # Get existing memory issues
        existing_issues = gh.get_all_memory_issues()
        print(f"Found {len(existing_issues)} existing memory issues")
        
        # Show sync preview
        print("\nSync preview:")
        for task in doc.tasks[:3]:  # Show first 3 tasks
            print(f"  Task: {task.content[:50]}... [{task.status.value}]")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()