#!/usr/bin/env python3
"""Worktree Executor - Single-purpose executor for git worktree operations.

This executor manages git worktrees directly without delegating to other agents.
It follows the NO DELEGATION principle - all operations use direct git commands.
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_executor import BaseExecutor


class WorktreeExecutor(BaseExecutor):
    """Single-purpose executor for git worktree operations.
    
    CRITICAL: This executor MUST NOT call or delegate to other agents.
    All operations must be direct git commands only.
    """
    
    def __init__(self):
        """Initialize the worktree executor."""
        self.worktrees = {}
        self.base_path = Path('.worktrees')
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution entry point for worktree operations.
        
        Args:
            params: Dictionary containing:
                - operation: 'create' | 'remove' | 'list' | 'cleanup'
                - task_id: Unique identifier for the task
                - branch_name: Branch name for the worktree
                - base_branch: Base branch to create from (default: main)
                
        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - operation: Operation performed
                - worktree_path: Path to the worktree (for create)
                - branch_name: Branch name created/used
                - error: Error message if failed
        """
        operation = params.get('operation', 'create')
        
        try:
            if operation == 'create':
                return self._create_worktree(params)
            elif operation == 'remove':
                return self._remove_worktree(params)
            elif operation == 'list':
                return self._list_worktrees()
            elif operation == 'cleanup':
                return self._cleanup_worktrees(params)
            elif operation == 'status':
                return self._worktree_status(params)
            else:
                return {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }
        except Exception as e:
            return {
                'success': False,
                'operation': operation,
                'error': str(e)
            }
    
    def _create_worktree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new git worktree.
        
        Direct git command execution - no agent delegation.
        """
        task_id = params.get('task_id')
        branch_name = params.get('branch_name')
        base_branch = params.get('base_branch', 'main')
        
        if not task_id:
            return {
                'success': False,
                'operation': 'create',
                'error': 'task_id is required'
            }
        
        # Generate branch name if not provided
        if not branch_name:
            branch_type = params.get('branch_type', 'feature')
            branch_name = f"{branch_type}/task-{task_id}"
        
        # Create worktree path
        worktree_path = self.base_path / f"task-{task_id}"
        
        # Check if worktree already exists
        if worktree_path.exists():
            # Try to remove it first
            self._force_remove_worktree(str(worktree_path))
        
        # Ensure base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch latest changes
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin', base_branch],
            capture_output=True,
            text=True
        )
        
        if fetch_result.returncode != 0:
            return {
                'success': False,
                'operation': 'create',
                'error': f'Failed to fetch {base_branch}: {fetch_result.stderr}'
            }
        
        # Create worktree with new branch
        cmd = [
            'git', 'worktree', 'add',
            str(worktree_path),
            '-b', branch_name,
            f'origin/{base_branch}'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Check if branch already exists
            if 'already exists' in result.stderr:
                # Try without creating new branch
                cmd = [
                    'git', 'worktree', 'add',
                    str(worktree_path),
                    branch_name
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'operation': 'create',
                    'error': result.stderr
                }
        
        # Initialize task metadata
        self._init_task_metadata(worktree_path, task_id, branch_name)
        
        # Setup environment if needed
        env_result = self._setup_environment(worktree_path, params)
        
        # Store worktree info
        self.worktrees[task_id] = {
            'path': str(worktree_path),
            'branch': branch_name,
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'operation': 'create',
            'task_id': task_id,
            'worktree_path': str(worktree_path),
            'branch_name': branch_name,
            'base_branch': base_branch,
            'environment': env_result
        }
    
    def _remove_worktree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a git worktree.
        
        Direct git command execution - no agent delegation.
        """
        task_id = params.get('task_id')
        worktree_path = params.get('worktree_path')
        
        if not task_id and not worktree_path:
            return {
                'success': False,
                'operation': 'remove',
                'error': 'task_id or worktree_path is required'
            }
        
        # Determine worktree path
        if not worktree_path:
            worktree_path = str(self.base_path / f"task-{task_id}")
        
        # Force remove worktree
        success = self._force_remove_worktree(worktree_path)
        
        if success:
            # Remove from tracking
            if task_id in self.worktrees:
                del self.worktrees[task_id]
            
            return {
                'success': True,
                'operation': 'remove',
                'worktree_path': worktree_path,
                'message': f'Worktree {worktree_path} removed successfully'
            }
        else:
            return {
                'success': False,
                'operation': 'remove',
                'worktree_path': worktree_path,
                'error': 'Failed to remove worktree'
            }
    
    def _list_worktrees(self) -> Dict[str, Any]:
        """List all git worktrees.
        
        Direct git command execution - no agent delegation.
        """
        cmd = ['git', 'worktree', 'list', '--porcelain']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {
                'success': False,
                'operation': 'list',
                'error': result.stderr
            }
        
        # Parse worktree list
        worktrees = []
        current_worktree = {}
        
        for line in result.stdout.strip().split('\n'):
            if line.startswith('worktree '):
                if current_worktree:
                    worktrees.append(current_worktree)
                current_worktree = {'path': line.replace('worktree ', '')}
            elif line.startswith('HEAD '):
                current_worktree['head'] = line.replace('HEAD ', '')
            elif line.startswith('branch '):
                current_worktree['branch'] = line.replace('branch ', '')
            elif line == 'bare':
                current_worktree['bare'] = True  # type: ignore[assignment]
        
        if current_worktree:
            worktrees.append(current_worktree)
        
        # Filter to only show .worktrees directory
        task_worktrees = [
            wt for wt in worktrees 
            if '.worktrees' in wt.get('path', '')
        ]
        
        return {
            'success': True,
            'operation': 'list',
            'worktrees': task_worktrees,
            'count': len(task_worktrees)
        }
    
    def _cleanup_worktrees(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old or orphaned worktrees.
        
        Direct git command execution - no agent delegation.
        """
        dry_run = params.get('dry_run', True)
        max_age_days = params.get('max_age_days', 7)
        
        # Prune worktrees first
        prune_cmd = ['git', 'worktree', 'prune']
        if dry_run:
            prune_cmd.append('--dry-run')
        
        prune_result = subprocess.run(
            prune_cmd,
            capture_output=True,
            text=True
        )
        
        # Find old worktrees
        old_worktrees = []
        if self.base_path.exists():
            for worktree_dir in self.base_path.iterdir():
                if worktree_dir.is_dir():
                    # Check age
                    stat = worktree_dir.stat()
                    age_days = (datetime.now().timestamp() - stat.st_mtime) / 86400
                    
                    if age_days > max_age_days:
                        old_worktrees.append({
                            'path': str(worktree_dir),
                            'age_days': int(age_days)
                        })
        
        # Remove old worktrees if not dry run
        removed = []
        if not dry_run:
            for wt in old_worktrees:
                if self._force_remove_worktree(wt['path']):
                    removed.append(wt['path'])
        
        return {
            'success': True,
            'operation': 'cleanup',
            'dry_run': dry_run,
            'pruned': prune_result.stdout if prune_result.stdout else 'None',
            'old_worktrees': old_worktrees,
            'removed': removed if not dry_run else []
        }
    
    def _worktree_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific worktree.
        
        Direct git command execution - no agent delegation.
        """
        task_id = params.get('task_id')
        worktree_path = params.get('worktree_path')
        
        if not task_id and not worktree_path:
            return {
                'success': False,
                'operation': 'status',
                'error': 'task_id or worktree_path is required'
            }
        
        # Determine worktree path
        if not worktree_path:
            worktree_path = str(self.base_path / f"task-{task_id}")
        
        path = Path(worktree_path)
        
        if not path.exists():
            return {
                'success': False,
                'operation': 'status',
                'error': f'Worktree does not exist: {worktree_path}'
            }
        
        # Get git status in worktree
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        
        # Get current branch
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        
        # Get last commit
        commit_result = subprocess.run(
            ['git', 'log', '-1', '--oneline'],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        
        # Check task metadata if exists
        task_metadata = None
        task_file = path / '.task' / 'metadata.json'
        if task_file.exists():
            try:
                with open(task_file) as f:
                    task_metadata = json.load(f)
            except:
                pass
        
        return {
            'success': True,
            'operation': 'status',
            'worktree_path': worktree_path,
            'exists': True,
            'branch': branch_result.stdout.strip(),
            'has_changes': bool(status_result.stdout.strip()),
            'changes': status_result.stdout.strip().split('\n') if status_result.stdout.strip() else [],
            'last_commit': commit_result.stdout.strip(),
            'task_metadata': task_metadata
        }
    
    def _force_remove_worktree(self, worktree_path: str) -> bool:
        """Forcefully remove a worktree.
        
        Direct git command execution - no agent delegation.
        """
        # Try git worktree remove first
        result = subprocess.run(
            ['git', 'worktree', 'remove', '--force', worktree_path],
            capture_output=True,
            text=True
        )
        
        # If git command failed, try manual removal
        if result.returncode != 0:
            path = Path(worktree_path)
            if path.exists():
                try:
                    shutil.rmtree(path)
                except:
                    return False
        
        return True
    
    def _init_task_metadata(self, worktree_path: Path, task_id: str, branch_name: str):
        """Initialize task metadata in worktree.
        
        Direct file operations - no agent delegation.
        """
        task_dir = worktree_path / '.task'
        task_dir.mkdir(exist_ok=True)
        
        metadata = {
            'task_id': task_id,
            'branch': branch_name,
            'created_at': datetime.now().isoformat(),
            'worktree_path': str(worktree_path),
            'status': 'initialized'
        }
        
        metadata_file = task_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _setup_environment(self, worktree_path: Path, params: Dict[str, Any]) -> Dict[str, str]:
        """Setup development environment in worktree.
        
        Direct command execution - no agent delegation.
        """
        env_info = {}
        
        # Check for UV project
        pyproject = worktree_path / 'pyproject.toml'
        uv_lock = worktree_path / 'uv.lock'
        
        if pyproject.exists() and uv_lock.exists():
            # UV project - run uv sync
            result = subprocess.run(
                ['uv', 'sync', '--all-extras'],
                cwd=worktree_path,
                capture_output=True,
                text=True
            )
            
            env_info['uv_sync'] = 'success' if result.returncode == 0 else 'failed'
            env_info['project_type'] = 'uv'
        elif pyproject.exists():
            env_info['project_type'] = 'python'
        else:
            env_info['project_type'] = 'unknown'
        
        return env_info


# Single-purpose function interface for direct usage
def execute_worktree_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a worktree operation without creating an instance.
    
    This is the primary interface for CLAUDE.md orchestration.
    No agent delegation - direct git commands only.
    
    Args:
        params: Worktree operation parameters
        
    Returns:
        Operation result dictionary
    """
    executor = WorktreeExecutor()
    return executor.execute(params)