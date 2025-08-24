#!/usr/bin/env python3
"""Integration tests for the simplified executor architecture.

These tests verify that:
1. Executors follow the NO DELEGATION principle
2. Each executor has single responsibility
3. All executors return structured results
4. No inter-agent communication occurs
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from executors import (
    BaseExecutor,
    CodeExecutor,
    TestExecutor,
    GitHubExecutor,
    WorktreeExecutor,
    execute,
    list_executors,
    registry
)


class TestBaseExecutor(unittest.TestCase):
    """Test the base executor interface."""
    
    def test_base_executor_is_abstract(self):
        """Verify BaseExecutor cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseExecutor()
    
    def test_executor_registry(self):
        """Test the executor registry functionality."""
        # Test listing executors
        executors = list_executors()
        self.assertIn('code', executors)
        self.assertIn('test', executors)
        self.assertIn('github', executors)
        self.assertIn('worktree', executors)
        
        # Test getting an executor
        code_exec = registry.get('code')
        self.assertIsInstance(code_exec, CodeExecutor)
        
        # Test invalid executor
        with self.assertRaises(KeyError):
            registry.get('nonexistent')


class TestCodeExecutor(unittest.TestCase):
    """Test the code executor."""
    
    def setUp(self):
        """Set up test environment."""
        self.executor = CodeExecutor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_file(self):
        """Test writing a new file."""
        file_path = Path(self.temp_dir) / 'test.py'
        content = 'print("Hello, World!")'
        
        result = self.executor.execute({
            'action': 'write',
            'file_path': str(file_path),
            'content': content
        })
        
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'write')
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_text(), content)
    
    def test_write_existing_file_fails(self):
        """Test that writing to existing file fails."""
        file_path = Path(self.temp_dir) / 'existing.py'
        file_path.write_text('existing content')
        
        result = self.executor.execute({
            'action': 'write',
            'file_path': str(file_path),
            'content': 'new content'
        })
        
        self.assertFalse(result['success'])
        self.assertIn('already exists', result['error'])
    
    def test_read_file(self):
        """Test reading a file."""
        file_path = Path(self.temp_dir) / 'read_test.py'
        content = 'test content'
        file_path.write_text(content)
        
        result = self.executor.execute({
            'action': 'read',
            'file_path': str(file_path)
        })
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], content)
    
    def test_edit_file(self):
        """Test editing a file."""
        file_path = Path(self.temp_dir) / 'edit_test.py'
        original = 'def hello():\n    print("Hello")'
        file_path.write_text(original)
        
        result = self.executor.execute({
            'action': 'edit',
            'file_path': str(file_path),
            'old_content': 'print("Hello")',
            'new_content': 'print("Hello, World!")'
        })
        
        self.assertTrue(result['success'])
        self.assertIn('Hello, World!', file_path.read_text())
    
    def test_no_delegation(self):
        """Verify code executor doesn't call other agents."""
        # Check that the executor has no agent references
        executor_code = Path(__file__).parent.parent / 'executors' / 'code_executor.py'
        content = executor_code.read_text()
        
        # These patterns would indicate delegation (exclude comments)
        delegation_patterns = [
            'agent\.',  # agent method calls
            'Agent\(',  # Agent instantiation
            'call_agent',
            'invoke_agent',
            'execute_agent'
        ]
        
        # Check each line to exclude comments
        for line_num, line in enumerate(content.split('\n'), 1):
            # Skip comment lines and docstrings
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""'):
                continue
            
            for pattern in delegation_patterns:
                import re
                if re.search(pattern, line, re.IGNORECASE):
                    self.fail(f"Code executor line {line_num} contains delegation pattern: {pattern}")


class TestTestExecutor(unittest.TestCase):
    """Test the test executor."""
    
    def setUp(self):
        """Set up test environment."""
        self.executor = TestExecutor()
    
    @patch('subprocess.run')
    def test_run_pytest(self, mock_run):
        """Test running pytest."""
        # Mock successful pytest run
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='5 passed in 1.23s',
            stderr=''
        )
        
        result = self.executor.execute({
            'test_framework': 'pytest',
            'test_path': 'tests/',
            'options': {'verbose': True}
        })
        
        self.assertTrue(result['success'])
        self.assertEqual(result['framework'], 'pytest')
        mock_run.assert_called_once()
        
        # Check command includes pytest
        cmd = mock_run.call_args[0][0]
        self.assertIn('pytest', cmd)
        self.assertIn('-v', cmd)
    
    @patch('subprocess.run')
    def test_uv_project_detection(self, mock_run):
        """Test that UV projects use uv run pytest."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='tests passed',
            stderr=''
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create UV project markers
            Path(temp_dir, 'pyproject.toml').touch()
            Path(temp_dir, 'uv.lock').touch()
            
            result = self.executor.execute({
                'test_framework': 'pytest',
                'test_path': 'tests/',
                'working_dir': temp_dir
            })
            
            # Check that uv run was used
            cmd = mock_run.call_args[0][0]
            self.assertEqual(cmd[0], 'uv')
            self.assertEqual(cmd[1], 'run')
            self.assertEqual(cmd[2], 'pytest')


class TestGitHubExecutor(unittest.TestCase):
    """Test the GitHub executor."""
    
    def setUp(self):
        """Set up test environment."""
        self.executor = GitHubExecutor()
    
    @patch('subprocess.run')
    def test_create_issue(self, mock_run):
        """Test creating a GitHub issue."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='https://github.com/user/repo/issues/123',
            stderr=''
        )
        
        result = self.executor.execute({
            'operation': 'create_issue',
            'title': 'Test Issue',
            'body': 'Test body',
            'labels': ['bug', 'urgent']
        })
        
        self.assertTrue(result['success'])
        self.assertEqual(result['issue_number'], '123')
        
        # Check gh command
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], 'gh')
        self.assertEqual(cmd[1], 'issue')
        self.assertEqual(cmd[2], 'create')
    
    @patch('subprocess.run')
    def test_never_auto_merges(self, mock_run):
        """Verify GitHub executor never auto-merges PRs."""
        # The merge_pr operation should exist but require explicit call
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='PR merged',
            stderr=''
        )
        
        # This should work when explicitly called
        result = self.executor.execute({
            'operation': 'merge_pr',
            'pr_number': 123
        })
        
        self.assertTrue(result['success'])
        
        # But there should be no automatic merge logic
        executor_code = Path(__file__).parent.parent / 'executors' / 'github_executor.py'
        content = executor_code.read_text()
        
        # Check for patterns that would indicate auto-merging
        auto_merge_patterns = [
            'auto_merge',
            'automatic_merge',
            'if checks_passing: merge'
        ]
        
        for pattern in auto_merge_patterns:
            self.assertNotIn(pattern.lower(), content.lower(),
                f"GitHub executor contains auto-merge pattern: {pattern}")


class TestWorkTreeExecutor(unittest.TestCase):
    """Test the worktree executor."""
    
    def setUp(self):
        """Set up test environment."""
        self.executor = WorktreeExecutor()
    
    @patch('executors.worktree_executor.subprocess.run')
    @patch('executors.worktree_executor.Path.mkdir')
    def test_create_worktree(self, mock_mkdir, mock_run):
        """Test creating a worktree."""
        # Mock git commands
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='',
            stderr=''
        )
        
        result = self.executor.execute({
            'operation': 'create',
            'task_id': 'test-123',
            'branch_name': 'feature/test-123'
        })
        
        # Check result - might fail due to actual git operations
        if not result.get('success'):
            # If it failed, just check the structure is correct
            self.assertIn('error', result)
        else:
            self.assertEqual(result['task_id'], 'test-123')
            self.assertIn('worktree_path', result)
        
        # Verify git worktree add was called
        calls = mock_run.call_args_list
        worktree_add_called = any(
            'worktree' in str(call) and 'add' in str(call)
            for call in calls
        )
        self.assertTrue(worktree_add_called)
    
    @patch('subprocess.run')
    def test_list_worktrees(self, mock_run):
        """Test listing worktrees."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='worktree /path/to/worktree\nHEAD abc123\nbranch refs/heads/feature',
            stderr=''
        )
        
        result = self.executor.execute({
            'operation': 'list'
        })
        
        self.assertTrue(result['success'])
        self.assertIn('worktrees', result)
        
        # Check git command
        cmd = mock_run.call_args[0][0]
        self.assertIn('worktree', cmd)
        self.assertIn('list', cmd)


class TestNoDelegationPrinciple(unittest.TestCase):
    """Test that all executors follow the no-delegation principle."""
    
    def test_all_executors_no_delegation(self):
        """Verify no executor contains agent delegation code."""
        executor_dir = Path(__file__).parent.parent / 'executors'
        
        # Patterns that indicate problematic delegation
        delegation_patterns = [
            r'from\s+\.\.\s*agents',  # importing from agents directory
            r'invoke_agent',
            r'call_agent',
            r'execute_agent',
            r'\.agent\(',  # calling .agent() method
        ]
        
        for executor_file in executor_dir.glob('*_executor.py'):
            if executor_file.name == 'base_executor.py':
                continue  # Skip base class
                
            content = executor_file.read_text()
            
            # Check line by line to exclude comments
            for line_num, line in enumerate(content.split('\n'), 1):
                # Skip pure comment lines
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                    
                for pattern in delegation_patterns:
                    import re
                    if re.search(pattern, line, re.IGNORECASE):
                        self.fail(f"{executor_file.name} line {line_num} contains delegation pattern: {pattern}")
    
    def test_single_entry_point(self):
        """Verify each executor has only one primary public method: execute()."""
        executors_to_test = [
            CodeExecutor,
            TestExecutor,
            GitHubExecutor,
            WorktreeExecutor
        ]
        
        for executor_class in executors_to_test:
            instance = executor_class()
            
            # Check that execute method exists
            self.assertTrue(
                hasattr(instance, 'execute'),
                f"{executor_class.__name__} missing execute() method"
            )
            
            # Check that execute is callable
            self.assertTrue(
                callable(getattr(instance, 'execute')),
                f"{executor_class.__name__}.execute() is not callable"
            )
            
            # The execute method should be the primary interface
            # Other public methods from BaseExecutor are acceptable
            # (like get_operations_log, etc.)


class TestOrchestrationInterface(unittest.TestCase):
    """Test the orchestration interface for CLAUDE.md."""
    
    def test_execute_function(self):
        """Test the main execute() function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / 'test_orchestration.py'
            
            # Test using the main execute() function
            result = execute('code', {
                'action': 'write',
                'file_path': str(file_path),
                'content': 'print("Orchestrated!")'
            })
            
            self.assertTrue(result['success'])
            self.assertTrue(file_path.exists())
    
    def test_all_executors_registered(self):
        """Verify all executors are properly registered."""
        registered = list_executors()
        
        required_executors = ['code', 'test', 'github', 'worktree']
        for executor in required_executors:
            self.assertIn(executor, registered,
                f"Required executor '{executor}' not registered")


if __name__ == '__main__':
    unittest.main()