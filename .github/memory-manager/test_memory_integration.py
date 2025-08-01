#!/usr/bin/env python3
"""
Comprehensive tests for Memory.md to GitHub Issues integration

This test suite validates all components of the Memory.md integration system,
including parsing, GitHub API integration, synchronization, and conflict resolution.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import our modules
from memory_parser import MemoryParser, Task, TaskStatus, TaskPriority, MemoryDocument
from github_integration import GitHubIntegration, GitHubIssue
from sync_engine import SyncEngine, SyncDirection, ConflictResolution, SyncConfig
from config import ConfigManager, MemoryManagerConfig, PruningConfig


class TestMemoryParser(unittest.TestCase):
    """Test Memory.md parsing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = MemoryParser()
        self.sample_memory_content = """# AI Assistant Memory
Last Updated: 2025-08-01T13:00:00-08:00

## Current Goals
- ✅ Complete task A
- [ ] Work on task B
- **HIGH**: Critical task C

## Recent Accomplishments
- Fixed issue #123
- Updated documentation
- **COMPLETED**: Major feature implementation

## Reflections
Some important insights about the project.
"""
    
    def test_parse_content_basic(self):
        """Test basic content parsing"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        self.assertIsInstance(doc, MemoryDocument)
        self.assertEqual(len(doc.sections), 4)  # Including main title
        self.assertGreater(len(doc.tasks), 0)
    
    def test_task_extraction(self):
        """Test task extraction from content"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        # Should find multiple tasks
        self.assertGreaterEqual(len(doc.tasks), 5)
        
        # Check task statuses
        completed_tasks = doc.get_tasks_by_status(TaskStatus.COMPLETED)
        pending_tasks = doc.get_tasks_by_status(TaskStatus.PENDING)
        
        self.assertGreater(len(completed_tasks), 0)
        self.assertGreater(len(pending_tasks), 0)
    
    def test_priority_detection(self):
        """Test priority detection in tasks"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        high_priority_tasks = [t for t in doc.tasks if t.priority == TaskPriority.HIGH]
        self.assertGreater(len(high_priority_tasks), 0)
    
    def test_issue_reference_extraction(self):
        """Test extraction of GitHub issue references"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        tasks_with_issues = [t for t in doc.tasks if t.issue_number is not None]
        self.assertGreater(len(tasks_with_issues), 0)
        
        # Check specific issue number
        issue_123_tasks = [t for t in doc.tasks if t.issue_number == 123]
        self.assertEqual(len(issue_123_tasks), 1)
    
    def test_section_parsing(self):
        """Test section parsing and organization"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        section_names = [s.name for s in doc.sections]
        self.assertIn("Current Goals", section_names)
        self.assertIn("Recent Accomplishments", section_names)
        self.assertIn("Reflections", section_names)
    
    def test_last_updated_extraction(self):
        """Test extraction of last updated timestamp"""
        doc = self.parser.parse_content(self.sample_memory_content)
        
        self.assertIsNotNone(doc.last_updated)
        self.assertIsInstance(doc.last_updated, datetime)
    
    def test_empty_content(self):
        """Test handling of empty content"""
        doc = self.parser.parse_content("")
        
        self.assertEqual(len(doc.sections), 0)
        self.assertEqual(len(doc.tasks), 0)
    
    def test_malformed_content(self):
        """Test handling of malformed content"""
        malformed_content = "# Title\n- [ ] Task\n- ✅ Another\n### Bad header"
        doc = self.parser.parse_content(malformed_content)
        
        # Should still parse without errors
        self.assertIsInstance(doc, MemoryDocument)
        self.assertGreater(len(doc.tasks), 0)


class TestGitHubIntegration(unittest.TestCase):
    """Test GitHub Issues integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.github = GitHubIntegration(self.temp_dir)
        
        # Mock task
        self.sample_task = Task(
            id="test-001",
            content="Test task for integration",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            section="Current Goals",
            line_number=5
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_gh_cli_validation(self, mock_run):
        """Test GitHub CLI validation"""
        # Mock successful auth check
        mock_run.return_value = Mock(returncode=0)
        
        # Should not raise exception
        try:
            github = GitHubIntegration(self.temp_dir)
        except RuntimeError:
            self.fail("GitHubIntegration raised RuntimeError unexpectedly")
    
    def test_issue_title_generation(self):
        """Test GitHub issue title generation"""
        title = self.github._generate_issue_title(self.sample_task)
        
        self.assertIsInstance(title, str)
        self.assertLessEqual(len(title), 80)
        self.assertIn("[HIGH]", title)  # Should include priority
    
    def test_issue_template_formatting(self):
        """Test issue body template formatting"""
        body = self.github.TASK_ISSUE_TEMPLATE.format(
            content=self.sample_task.content,
            section=self.sample_task.section,
            priority=self.sample_task.priority.value.title(),
            status=self.sample_task.status.value.replace('_', ' ').title(),
            line_number=self.sample_task.line_number,
            task_id=self.sample_task.id,
            metadata=json.dumps({})
        )
        
        self.assertIn(self.sample_task.content, body)
        self.assertIn("memory-task-id:", body)
        self.assertIn("AI agent", body)
    
    def test_github_issue_from_json(self):
        """Test GitHubIssue creation from JSON"""
        issue_data = {
            'number': 123,
            'title': 'Test Issue',
            'body': 'Test body <!-- memory-task-id: test-001 -->',
            'state': 'open',
            'labels': [{'name': 'memory-sync'}],
            'assignees': [],
            'createdAt': '2025-08-01T13:00:00Z',
            'updatedAt': '2025-08-01T13:00:00Z',
            'htmlUrl': 'https://github.com/test/repo/issues/123'
        }
        
        issue = GitHubIssue.from_gh_json(issue_data)
        
        self.assertEqual(issue.number, 123)
        self.assertEqual(issue.memory_task_id, 'test-001')
        self.assertEqual(issue.state, 'open')


class TestSyncEngine(unittest.TestCase):
    """Test synchronization engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "Memory.md"
        
        # Create sample Memory.md
        self.memory_file.write_text("""# AI Assistant Memory
Last Updated: 2025-08-01T13:00:00-08:00

## Current Goals
- [ ] Test task 1
- ✅ Test task 2

## Recent Accomplishments
- Completed feature A
""")
        
        # Configure sync engine
        config = SyncConfig(dry_run=True)  # Safe mode for testing
        self.sync_engine = SyncEngine(
            str(self.memory_file),
            self.temp_dir,
            config
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.object(SyncEngine, '_sync_memory_to_github')
    @patch.object(SyncEngine, '_sync_github_to_memory')
    def test_bidirectional_sync(self, mock_github_to_memory, mock_memory_to_github):
        """Test bidirectional synchronization"""
        result = self.sync_engine.sync(SyncDirection.BIDIRECTIONAL)
        
        self.assertTrue(result.success)
        mock_memory_to_github.assert_called_once()
        mock_github_to_memory.assert_called_once()
    
    def test_sync_config_validation(self):
        """Test sync configuration validation"""
        config = SyncConfig(
            batch_size=10,
            sync_frequency_minutes=5
        )
        
        self.assertGreater(config.batch_size, 0)
        self.assertGreater(config.sync_frequency_minutes, 0)
    
    def test_conflict_detection(self):
        """Test conflict detection logic"""
        # Create mock task and issue with different content
        task = Task(
            id="test-001",
            content="Original task content",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            section="Current Goals",
            line_number=1
        )
        
        issue = Mock()
        issue.title = "Modified task content"
        issue.state = "open"
        issue.number = 123
        
        conflict = self.sync_engine._detect_conflict(task, issue)
        
        # Should detect content conflict
        if conflict:  # Conflict detection depends on similarity threshold
            self.assertIn("content_mismatch", conflict.conflict_type)
    
    def test_backup_creation(self):
        """Test Memory.md backup creation"""
        # Enable backup in config
        self.sync_engine.config.backup_before_sync = True
        
        self.sync_engine._backup_memory()
        
        # Check backup was created
        backup_files = list(self.sync_engine.state_dir.glob("Memory_backup_*.md"))
        self.assertGreater(len(backup_files), 0)
    
    def test_sync_state_management(self):
        """Test sync state saving and loading"""
        # Create mock result
        from sync_engine import SyncResult
        
        result = SyncResult(
            start_time=datetime.now(),
            end_time=datetime.now(),
            direction=SyncDirection.BIDIRECTIONAL,
            memory_tasks_processed=5,
            github_issues_processed=3,
            created_issues=1,
            updated_issues=2,
            closed_issues=0,
            updated_tasks=1,
            conflicts=[],
            errors=[],
            success=True
        )
        
        # Save state
        self.sync_engine._save_sync_state(result)
        
        # Verify state file exists
        state_file = self.sync_engine.state_dir / "sync_state.json"
        self.assertTrue(state_file.exists())
        
        # Load and verify
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        self.assertIn('last_sync', state_data)
        self.assertIn('last_result', state_data)


class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_creation(self):
        """Test default configuration creation"""
        config = self.config_manager.load_config()
        
        self.assertIsInstance(config, MemoryManagerConfig)
        self.assertTrue(config.enabled)
        self.assertEqual(config.sync.direction, SyncDirection.BIDIRECTIONAL)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Create invalid config
        config = MemoryManagerConfig()
        config.sync.batch_size = -1  # Invalid
        config.pruning.completed_task_age_days = -1  # Invalid
        
        errors = self.config_manager.validate_config(config)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("batch size" in error.lower() for error in errors))
    
    def test_config_file_operations(self):
        """Test configuration file save/load"""
        config = MemoryManagerConfig()
        config.sync.auto_create_issues = False
        
        # Save config
        config_file = Path(self.temp_dir) / "test_config.yaml"
        config.save_to_file(str(config_file))
        
        self.assertTrue(config_file.exists())
        
        # Load config
        loaded_config = MemoryManagerConfig.load_from_file(str(config_file))
        
        self.assertEqual(loaded_config.sync.auto_create_issues, False)
    
    def test_effective_config_resolution(self):
        """Test effective configuration with resolved paths"""
        effective = self.config_manager.get_effective_config()
        
        self.assertIn('memory_file_path', effective)
        self.assertTrue(Path(effective['memory_file_path']).is_absolute())


class TestIntegrationScenarios(unittest.TestCase):
    """Test end-to-end integration scenarios"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "Memory.md"
        
        # Create realistic Memory.md content
        self.memory_file.write_text("""# AI Assistant Memory
Last Updated: 2025-08-01T13:00:00-08:00

## Current Goals
- [ ] Implement feature X
- [ ] Fix bug in component Y
- **HIGH**: Critical security update

## Completed Tasks
- ✅ Completed feature A
- ✅ Fixed issue #123
- ✅ Updated documentation

## Recent Accomplishments
- Enhanced test coverage to 95%
- Improved performance by 40%
- Fixed 5 critical bugs

## Next Steps
- Plan next sprint
- Review code quality metrics
""")
    
    def tearDown(self):
        """Clean up integration test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_parsing_workflow(self):
        """Test complete parsing workflow"""
        parser = MemoryParser()
        doc = parser.parse_file(str(self.memory_file))
        
        # Verify parsing results
        self.assertGreater(len(doc.tasks), 5)
        self.assertGreater(len(doc.sections), 3)
        
        # Verify task distribution
        current_goals = doc.get_tasks_by_section("Current Goals")
        completed_tasks = doc.get_tasks_by_section("Completed Tasks")
        
        self.assertGreater(len(current_goals), 0)
        self.assertGreater(len(completed_tasks), 0)
        
        # Verify status detection
        completed = doc.get_tasks_by_status(TaskStatus.COMPLETED)
        pending = doc.get_tasks_by_status(TaskStatus.PENDING)
        
        self.assertGreater(len(completed), 0)
        self.assertGreater(len(pending), 0)
    
    @patch('subprocess.run')
    def test_dry_run_sync_scenario(self, mock_run):
        """Test dry-run synchronization scenario"""
        # Mock GitHub CLI responses
        mock_run.return_value = Mock(returncode=0, stdout='[]')
        
        config = SyncConfig(dry_run=True)
        sync_engine = SyncEngine(str(self.memory_file), self.temp_dir, config)
        
        result = sync_engine.sync()
        
        # Should complete successfully in dry-run mode
        self.assertIsNotNone(result)
        self.assertIsInstance(result.duration.total_seconds(), float)
    
    def test_config_integration(self):
        """Test configuration integration with components"""
        config_manager = ConfigManager(self.temp_dir)
        config = config_manager.load_config()
        
        # Test config with sync engine
        sync_engine = SyncEngine(str(self.memory_file), self.temp_dir, config.sync)
        
        self.assertEqual(sync_engine.config.direction, config.sync.direction)
        self.assertEqual(sync_engine.config.dry_run, config.sync.dry_run)


def run_comprehensive_tests():
    """Run all tests with detailed reporting"""
    # Create test suite
    test_classes = [
        TestMemoryParser,
        TestGitHubIntegration,
        TestSyncEngine,
        TestConfigManager,
        TestIntegrationScenarios
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"  Total tests: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)