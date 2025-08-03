#!/usr/bin/env python3
"""
Test suite for Simple Memory Manager

This test suite validates the GitHub Issues-only memory management system,
ensuring all operations work correctly without Memory.md file dependencies.
"""

import unittest
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from simple_memory_manager import SimpleMemoryManager, MemoryUpdate, MemorySection


class TestMemoryUpdate(unittest.TestCase):
    """Test MemoryUpdate class"""
    
    def test_memory_update_creation(self):
        """Test MemoryUpdate object creation"""
        update = MemoryUpdate(
            content="Test memory content",
            section="test-section",
            agent="TestAgent",
            priority="high",
            related_issues=[123, 456],
            related_prs=[789],
            related_commits=["abc123"],
            related_files=["test.py"]
        )
        
        self.assertEqual(update.content, "Test memory content")
        self.assertEqual(update.section, "test-section")
        self.assertEqual(update.agent, "TestAgent")
        self.assertEqual(update.priority, "high")
        self.assertEqual(update.related_issues, [123, 456])
        self.assertIsNotNone(update.timestamp)
    
    def test_format_comment(self):
        """Test comment formatting"""
        update = MemoryUpdate(
            content="Test content",
            section="current-goals",
            agent="WorkflowManager",
            priority="medium",
            related_issues=[123],
            related_files=["src/test.py"]
        )
        
        comment = update.format_comment()
        
        self.assertIn("### CURRENT-GOALS", comment)
        self.assertIn("**Type**: current-goals", comment)
        self.assertIn("**Priority**: medium", comment)
        self.assertIn("**Related**: #123", comment)
        self.assertIn("**Content**:\nTest content", comment)
        self.assertIn("- File: src/test.py", comment)
        self.assertIn("*Added by: WorkflowManager*", comment)


class TestMemorySection(unittest.TestCase):
    """Test MemorySection class"""
    
    def test_memory_section_creation(self):
        """Test MemorySection object creation"""
        section = MemorySection(
            name="test-section",
            priority="high",
            related_issues=[123, 456]
        )
        
        self.assertEqual(section.name, "test-section")
        self.assertEqual(section.priority, "high")
        self.assertEqual(section.related_issues, [123, 456])
        self.assertIsNotNone(section.timestamp)
    
    def test_to_dict(self):
        """Test section serialization"""
        section = MemorySection("test", "low", [789])
        data = section.to_dict()
        
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["priority"], "low")
        self.assertEqual(data["related_issues"], [789])
        self.assertIn("timestamp", data)


class TestSimpleMemoryManager(unittest.TestCase):
    """Test SimpleMemoryManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Mock GitHubOperations
        self.github_mock = Mock()
        self.github_patcher = patch('simple_memory_manager.GitHubOperations')
        self.mock_github_class = self.github_patcher.start()
        self.mock_github_class.return_value = self.github_mock
        
        # Setup default mock responses
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': []
        }
        
        self.github_mock.create_issue.return_value = {
            'success': True,
            'data': {'number': 42, 'html_url': 'https://github.com/test/repo/issues/42'}
        }
    
    def tearDown(self):
        """Clean up test environment"""
        self.github_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test SimpleMemoryManager initialization"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        self.assertEqual(manager.repo_path, self.repo_path)
        self.assertEqual(manager.memory_issue_number, 42)
        self.github_mock.create_issue.assert_called_once()
    
    def test_get_or_create_memory_issue_existing(self):
        """Test finding existing memory issue"""
        # Mock existing memory issue
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': [
                {
                    'number': 123,
                    'title': '🧠 Project Memory - AI Assistant Context',
                    'labels': [{'name': 'memory'}]
                }
            ]
        }
        
        manager = SimpleMemoryManager(str(self.repo_path))
        
        self.assertEqual(manager.memory_issue_number, 123)
        self.github_mock.create_issue.assert_not_called()
    
    def test_get_or_create_memory_issue_new(self):
        """Test creating new memory issue"""
        # Mock no existing issues
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': []
        }
        
        manager = SimpleMemoryManager(str(self.repo_path))
        
        self.assertEqual(manager.memory_issue_number, 42)
        self.github_mock.create_issue.assert_called_once()
        
        # Verify issue creation parameters
        call_args = self.github_mock.create_issue.call_args
        self.assertEqual(call_args[1]['title'], '🧠 Project Memory - AI Assistant Context')
        self.assertIn('memory', call_args[1]['labels'])
    
    def test_create_memory_issue_body(self):
        """Test memory issue body creation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        body = manager._create_memory_issue_body()
        
        self.assertIn("central memory store", body)
        self.assertIn("Current Goals", body)
        self.assertIn("Recent Accomplishments", body)
        self.assertIn("Usage", body)
        self.assertIn("Benefits", body)
    
    def test_update_memory(self):
        """Test memory update operation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock successful comment creation
        self.github_mock.add_comment.return_value = {
            'success': True,
            'data': {
                'id': 789,
                'html_url': 'https://github.com/test/repo/issues/42#issuecomment-789'
            }
        }
        
        result = manager.update_memory(
            content="Test memory update",
            section="current-goals",
            agent="TestAgent",
            priority="high",
            related_issues=[123]
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['section'], "current-goals")
        self.assertEqual(result['agent'], "TestAgent")
        self.assertIn('comment_id', result)
        self.assertIn('timestamp', result)
        
        # Verify comment was added to correct issue
        self.github_mock.add_comment.assert_called_once_with(42, unittest.mock.ANY)
        
        # Verify comment format
        comment_body = self.github_mock.add_comment.call_args[0][1]
        self.assertIn("### CURRENT-GOALS", comment_body)
        self.assertIn("Test memory update", comment_body)
        self.assertIn("TestAgent", comment_body)
    
    def test_read_memory(self):
        """Test memory reading operation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock issue with comments
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': {
                'comments': [
                    {
                        'id': 'comment1',
                        'body': '### CURRENT-GOALS - 2025-01-01T12:00:00\n\n**Type**: current-goals\n**Priority**: high\n**Related**: #123\n\n**Content**:\nTest goal content\n\n---\n*Added by: TestAgent*',
                        'createdAt': '2025-01-01T12:00:00Z',
                        'author': {'login': 'testuser'}
                    }
                ],
                'createdAt': '2025-01-01T10:00:00Z',
                'updatedAt': '2025-01-01T12:00:00Z'
            }
        }
        
        result = manager.read_memory()
        
        self.assertEqual(result['issue_number'], 42)
        self.assertEqual(result['total_comments'], 1)
        self.assertIn('current-goals', result['sections'])
        self.assertEqual(len(result['sections']['current-goals']), 1)
        
        # Check parsed comment
        comment_data = result['sections']['current-goals'][0]
        self.assertEqual(comment_data['section'], 'current-goals')
        self.assertEqual(comment_data['priority'], 'high')
        self.assertEqual(comment_data['content'], 'Test goal content')
        self.assertEqual(comment_data['agent'], 'TestAgent')
        self.assertEqual(comment_data['related_issues'], [123])
    
    def test_read_memory_filtered_section(self):
        """Test reading memory with section filter"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock issue with multiple section comments
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': {
                'comments': [
                    {
                        'id': 'comment1',
                        'body': '### CURRENT-GOALS - 2025-01-01T12:00:00\n\n**Content**:\nGoal content',
                        'createdAt': '2025-01-01T12:00:00Z',
                        'author': {'login': 'testuser'}
                    },
                    {
                        'id': 'comment2', 
                        'body': '### COMPLETED-TASKS - 2025-01-01T13:00:00\n\n**Content**:\nCompleted task',
                        'createdAt': '2025-01-01T13:00:00Z',
                        'author': {'login': 'testuser'}
                    }
                ]
            }
        }
        
        result = manager.read_memory(section='current-goals')
        
        self.assertIn('filtered_section', result)
        self.assertEqual(len(result['filtered_section']), 1)
        self.assertEqual(result['filtered_section'][0]['section'], 'current-goals')
    
    def test_parse_memory_comment_valid(self):
        """Test parsing valid memory comment"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        comment_body = """### IMPORTANT-CONTEXT - 2025-01-01T12:00:00

**Type**: important-context
**Priority**: high
**Related**: #123, #456

**Content**:
This is important context information
spanning multiple lines.

**Context Links**:
- Commit: abc123
- File: src/test.py

---
*Added by: WorkflowManager*"""
        
        result = manager._parse_memory_comment(comment_body)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['section'], 'important-context')
        self.assertEqual(result['priority'], 'high')
        self.assertEqual(result['timestamp'], '2025-01-01T12:00:00')
        self.assertEqual(result['related_issues'], [123, 456])
        self.assertEqual(result['agent'], 'WorkflowManager')
        self.assertIn('This is important context', result['content'])
    
    def test_parse_memory_comment_invalid(self):
        """Test parsing invalid memory comment"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Regular comment without memory structure
        comment_body = "This is just a regular comment without structure."
        
        result = manager._parse_memory_comment(comment_body)
        
        self.assertIsNone(result)
    
    def test_search_memory(self):
        """Test memory search operation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock search results
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': {
                'items': [
                    {
                        'number': 42,
                        'comments': [
                            {
                                'body': '### CURRENT-GOALS - 2025-01-01T12:00:00\n\n**Content**:\nImplement search functionality'
                            }
                        ]
                    }
                ]
            }
        }
        
        result = manager.search_memory("search functionality")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['query'], "search functionality")
        self.assertEqual(result['total_results'], 1)
        self.assertEqual(len(result['results']), 1)
    
    def test_get_memory_status(self):
        """Test memory status operation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock issue details
        self.github_mock.get_issue.return_value = {
            'success': True,
            'data': {
                'title': '🧠 Project Memory - AI Assistant Context',
                'state': 'open',
                'created_at': '2025-01-01T10:00:00Z',
                'updated_at': '2025-01-01T12:00:00Z',
                'html_url': 'https://github.com/test/repo/issues/42',
                'labels': [{'name': 'memory'}, {'name': 'ai-assistant'}]
            }
        }
        
        # Mock memory content
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': {
                'comments': [
                    {'body': '### CURRENT-GOALS - 2025-01-01T12:00:00\n\n**Content**:\nTest'}
                ],
                'updatedAt': '2025-01-01T12:00:00Z'
            }
        }
        
        result = manager.get_memory_status()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['memory_issue']['number'], 42)
        self.assertEqual(result['memory_issue']['state'], 'open')
        self.assertEqual(result['memory_content']['total_comments'], 1)
        self.assertIn('current-goals', result['memory_content']['sections'])
    
    def test_cleanup_old_memory(self):
        """Test memory cleanup operation"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock memory content for cleanup
        self.github_mock._execute_command.return_value = {
            'success': True,
            'data': {
                'comments': [
                    {'body': 'test comment 1'},
                    {'body': 'test comment 2'}
                ]
            }
        }
        
        result = manager.cleanup_old_memory(days_old=30, dry_run=True)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['dry_run'])
        self.assertEqual(result['total_comments'], 2)
        self.assertIn('GitHub Issues provide natural archival', result['note'])
    
    def test_error_handling_github_failure(self):
        """Test error handling when GitHub operations fail"""
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Mock GitHub API failure
        self.github_mock.add_comment.return_value = {
            'success': False,
            'error': 'API rate limit exceeded'
        }
        
        result = manager.update_memory(
            content="Test",
            section="current-goals", 
            agent="TestAgent"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for SimpleMemoryManager"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('simple_memory_manager.GitHubOperations')
    def test_end_to_end_memory_workflow(self, mock_github_class):
        """Test complete memory management workflow"""
        # Setup mocks
        github_mock = Mock()
        mock_github_class.return_value = github_mock
        
        # Mock memory issue creation
        github_mock._execute_command.return_value = {'success': True, 'data': []}
        github_mock.create_issue.return_value = {
            'success': True, 
            'data': {'number': 100, 'html_url': 'https://github.com/test/repo/issues/100'}
        }
        
        # Mock comment creation
        github_mock.add_comment.return_value = {
            'success': True,
            'data': {'id': 500, 'html_url': 'https://github.com/test/repo/issues/100#issuecomment-500'}
        }
        
        # Mock reading memory
        github_mock._execute_command.side_effect = [
            {'success': True, 'data': []},  # Initial search for existing issue
            {
                'success': True,
                'data': {
                    'comments': [
                        {
                            'id': 'comment1',
                            'body': '### CURRENT-GOALS - 2025-01-01T12:00:00\n\n**Type**: current-goals\n**Priority**: high\n\n**Content**:\nComplete memory manager implementation\n\n---\n*Added by: WorkflowManager*',
                            'createdAt': '2025-01-01T12:00:00Z',
                            'author': {'login': 'testuser'}
                        }
                    ],
                    'updatedAt': '2025-01-01T12:00:00Z'
                }
            }
        ]
        
        # Initialize manager
        manager = SimpleMemoryManager(str(self.repo_path))
        
        # Test memory update
        update_result = manager.update_memory(
            content="Complete memory manager implementation",
            section="current-goals",
            agent="WorkflowManager",
            priority="high"
        )
        
        self.assertTrue(update_result['success'])
        self.assertEqual(update_result['section'], "current-goals")
        
        # Test memory reading
        memory_data = manager.read_memory()
        
        self.assertEqual(memory_data['issue_number'], 100)
        self.assertEqual(memory_data['total_comments'], 1)
        self.assertIn('current-goals', memory_data['sections'])
        
        # Verify the parsed content
        goal_data = memory_data['sections']['current-goals'][0]
        self.assertEqual(goal_data['section'], 'current-goals')
        self.assertEqual(goal_data['priority'], 'high')
        self.assertEqual(goal_data['agent'], 'WorkflowManager')
        self.assertIn('Complete memory manager', goal_data['content'])


if __name__ == '__main__':
    # Setup test logging
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main(verbosity=2)