"""
Test suite for Code Reviewer V0.3 Agent
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the current directory to Python path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "base"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "engines"))

from code_reviewer_v03 import CodeReviewerV03, ReviewFeedback, DeveloperPattern, ModulePattern


class TestCodeReviewerV03(unittest.TestCase):
    """Test cases for Code Reviewer V0.3."""

    def setUp(self):
        """Set up test fixtures."""
        self.reviewer = CodeReviewerV03()

    def test_agent_initialization(self):
        """Test that the agent initializes with correct capabilities."""
        # Check agent properties
        self.assertEqual(self.reviewer.agent_id, "code_reviewer_v03")
        self.assertEqual(self.reviewer.agent_type, "code-reviewer")

        # Check capabilities
        capabilities = self.reviewer.capabilities
        self.assertTrue(capabilities.can_review_code)
        self.assertTrue(capabilities.can_parallelize)
        self.assertTrue(capabilities.can_test)
        self.assertEqual(capabilities.max_parallel_tasks, 5)
        self.assertIn("python", capabilities.expertise_areas)
        self.assertIn("security", capabilities.expertise_areas)

    def test_can_handle_task(self):
        """Test task handling detection."""
        # Should handle code review tasks
        self.assertTrue(asyncio.run(self.reviewer.can_handle_task("review this code")))
        self.assertTrue(asyncio.run(self.reviewer.can_handle_task("check code quality")))
        self.assertTrue(asyncio.run(self.reviewer.can_handle_task("security review needed")))

        # Should not handle unrelated tasks
        self.assertFalse(asyncio.run(self.reviewer.can_handle_task("deploy to production")))
        self.assertFalse(asyncio.run(self.reviewer.can_handle_task("write documentation")))

    def test_developer_pattern_creation(self):
        """Test developer pattern tracking."""
        # Create a pattern
        pattern = DeveloperPattern(developer="test_user")

        # Check initial state
        self.assertEqual(pattern.developer, "test_user")
        self.assertEqual(len(pattern.common_issues), 0)
        self.assertEqual(len(pattern.ignored_rules), 0)
        self.assertEqual(len(pattern.preferred_patterns), 0)
        self.assertIsNone(pattern.last_reviewed)

    def test_module_pattern_creation(self):
        """Test module pattern tracking."""
        # Create a pattern
        pattern = ModulePattern(module_path="test/file.py")

        # Check initial state
        self.assertEqual(pattern.module_path, "test/file.py")
        self.assertEqual(len(pattern.frequent_issues), 0)
        self.assertEqual(len(pattern.complexity_trends), 0)
        self.assertEqual(len(pattern.security_hotspots), 0)
        self.assertIsNone(pattern.last_reviewed)

    def test_review_feedback_creation(self):
        """Test review feedback tracking."""
        # Create feedback
        feedback = ReviewFeedback(
            issue_id="test_issue",
            issue_type="warning",
            category="style",
            rule_id="E501",
            developer="test_user",
            module="test.py",
            file_path="/path/to/test.py",
            accepted=True,
            feedback_reason="Good catch"
        )

        # Check properties
        self.assertEqual(feedback.issue_id, "test_issue")
        self.assertEqual(feedback.rule_id, "E501")
        self.assertTrue(feedback.accepted)
        self.assertEqual(feedback.feedback_reason, "Good catch")


class TestCodeReviewerIntegration(unittest.TestCase):
    """Integration tests with mocked memory system."""

    def setUp(self):
        """Set up test with mocked dependencies."""
        self.reviewer = CodeReviewerV03()

        # Mock the memory interface
        self.mock_memory = Mock()
        self.mock_memory.__aenter__ = AsyncMock(return_value=self.mock_memory)
        self.mock_memory.__aexit__ = AsyncMock(return_value=None)
        self.mock_memory.remember_short_term = AsyncMock(return_value="memory_id")
        self.mock_memory.remember_long_term = AsyncMock(return_value="memory_id")
        self.mock_memory.search_memories = AsyncMock(return_value=[])
        self.mock_memory.recall_memories = AsyncMock(return_value=[])

        self.reviewer.memory = self.mock_memory

    @patch('code_reviewer_v03.CodeReviewerEngine')
    def test_review_files_task_execution(self, mock_engine_class):
        """Test file review task execution."""
        # Mock the review engine
        mock_engine = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {"status": "approved", "score": 85}
        mock_result.file_reviews = []
        mock_result.recommendations = ["Good code quality"]
        mock_engine.review_files = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        # Create task
        task = {
            "type": "review_files",
            "files": ["test.py"],
            "author": "test_user"
        }

        # Execute task
        async def run_test():
            await self.reviewer.start_task("Test review")
            outcome = await self.reviewer.execute_task(task)
            return outcome

        outcome = asyncio.run(run_test())

        # Verify outcome
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.task_type, "review_files")
        self.assertIn("review completed successfully", outcome.lessons_learned.lower())

        # Verify engine was called
        mock_engine.review_files.assert_called_once_with(["test.py"])

    def test_learn_from_feedback_task(self):
        """Test learning from feedback."""
        task = {
            "type": "learn_from_feedback",
            "feedback": [
                {
                    "issue_id": "1",
                    "rule_id": "E501",
                    "developer": "test_user",
                    "file_path": "test.py",
                    "accepted": False,
                    "reason": "We prefer longer lines"
                }
            ]
        }

        async def run_test():
            await self.reviewer.start_task("Learn from feedback")
            outcome = await self.reviewer.execute_task(task)
            return outcome

        outcome = asyncio.run(run_test())

        # Verify outcome
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.task_type, "learn_from_feedback")

        # Check that pattern was updated
        self.assertIn("test_user", self.reviewer.developer_patterns)
        dev_pattern = self.reviewer.developer_patterns["test_user"]
        self.assertIn("E501", dev_pattern.ignored_rules)

    def test_analyze_patterns_task(self):
        """Test pattern analysis."""
        # Set up some patterns first
        self.reviewer.developer_patterns["user1"] = DeveloperPattern(developer="user1")
        self.reviewer.developer_patterns["user1"].common_issues = {"E501": 5, "F401": 3}

        self.reviewer.module_patterns["test.py"] = ModulePattern(module_path="test.py")
        self.reviewer.module_patterns["test.py"].frequent_issues = {"E501": 8, "W292": 2}

        task = {"type": "analyze_patterns"}

        async def run_test():
            await self.reviewer.start_task("Analyze patterns")
            outcome = await self.reviewer.execute_task(task)
            return outcome

        outcome = asyncio.run(run_test())

        # Verify outcome
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.task_type, "analyze_patterns")

        # Check that insights were generated
        result = outcome.steps_taken
        self.assertTrue(any("Analyzing developer patterns" in step for step in result))
        self.assertTrue(any("Analyzing module patterns" in step for step in result))

    def test_get_developer_insights(self):
        """Test getting developer insights."""
        # Set up a developer pattern
        pattern = DeveloperPattern(developer="test_user")
        pattern.common_issues = {"E501": 10, "F401": 5, "W292": 3}
        pattern.ignored_rules = {"E702", "W391"}
        pattern.preferred_patterns = ["factory", "observer"]
        self.reviewer.developer_patterns["test_user"] = pattern

        async def run_test():
            return await self.reviewer.get_developer_insights("test_user")

        insights = asyncio.run(run_test())

        # Check insights
        self.assertEqual(insights["developer"], "test_user")
        self.assertEqual(len(insights["common_issues"]), 3)
        self.assertIn("E501", insights["common_issues"])
        self.assertEqual(insights["common_issues"]["E501"], 10)
        self.assertIn("E702", insights["ignored_rules"])
        self.assertIn("factory", insights["preferred_patterns"])
        self.assertEqual(insights["total_reviews"], 18)  # Sum of common issues

    def test_get_module_insights(self):
        """Test getting module insights."""
        # Set up a module pattern
        pattern = ModulePattern(module_path="test/module.py")
        pattern.frequent_issues = {"E501": 15, "F401": 8, "W292": 4}
        pattern.complexity_trends = [5.0, 6.5, 8.0, 7.2, 9.1]
        pattern.security_hotspots = ["test/module.py", "other.py"]
        self.reviewer.module_patterns["test/module.py"] = pattern

        async def run_test():
            return await self.reviewer.get_module_insights("test/module.py")

        insights = asyncio.run(run_test())

        # Check insights
        self.assertEqual(insights["module"], "test/module.py")
        self.assertEqual(len(insights["frequent_issues"]), 3)
        self.assertIn("E501", insights["frequent_issues"])
        self.assertEqual(insights["frequent_issues"]["E501"], 15)
        self.assertEqual(len(insights["complexity_trend"]), 5)  # Last 5 trends
        self.assertTrue(insights["is_security_hotspot"])
        self.assertEqual(insights["total_issues"], 27)  # Sum of frequent issues

    def test_missing_pattern_insights(self):
        """Test getting insights for non-existent patterns."""
        async def run_test():
            dev_insights = await self.reviewer.get_developer_insights("missing_user")
            mod_insights = await self.reviewer.get_module_insights("missing/file.py")
            return dev_insights, mod_insights

        dev_insights, mod_insights = asyncio.run(run_test())

        # Should return helpful messages
        self.assertIn("No pattern data", dev_insights["message"])
        self.assertIn("No pattern data", mod_insights["message"])


class TestPatternUpdating(unittest.TestCase):
    """Test pattern updating functionality."""

    def setUp(self):
        """Set up test."""
        self.reviewer = CodeReviewerV03()
        # Mock memory to avoid actual memory operations
        self.reviewer.memory = Mock()
        self.reviewer.memory.remember_long_term = AsyncMock(return_value="id")

    def test_update_patterns_from_feedback_accepted(self):
        """Test updating patterns when feedback is accepted."""
        feedback = ReviewFeedback(
            issue_id="1",
            issue_type="warning",
            category="style",
            rule_id="E501",
            developer="user1",
            module="test.py",
            file_path="test.py",
            accepted=True
        )

        async def run_test():
            await self.reviewer._update_patterns_from_feedback(feedback)

        asyncio.run(run_test())

        # Check that common issue was incremented
        pattern = self.reviewer.developer_patterns["user1"]
        self.assertEqual(pattern.common_issues["E501"], 1)
        self.assertNotIn("E501", pattern.ignored_rules)

    def test_update_patterns_from_feedback_rejected(self):
        """Test updating patterns when feedback is rejected."""
        feedback = ReviewFeedback(
            issue_id="1",
            issue_type="warning",
            category="style",
            rule_id="E501",
            developer="user1",
            module="test.py",
            file_path="test.py",
            accepted=False
        )

        async def run_test():
            await self.reviewer._update_patterns_from_feedback(feedback)

        asyncio.run(run_test())

        # Check that rule was added to ignored
        pattern = self.reviewer.developer_patterns["user1"]
        self.assertIn("E501", pattern.ignored_rules)
        self.assertNotIn("E501", pattern.common_issues)


def create_test_file():
    """Create a temporary test file for integration tests."""
    content = '''
def test_function():
    """Test function with some issues."""
    x = 1
    y = 2
    return x + y

def another_function(param1, param2, param3, param4, param5, param6):
    """Function with too many parameters."""
    if param1:
        if param2:
            if param3:
                return param4 + param5 + param6
    return 0
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        return f.name


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCodeReviewerV03))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeReviewerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternUpdating))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    print(f"\nTests {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    print(f"Ran {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")

    exit(exit_code)
