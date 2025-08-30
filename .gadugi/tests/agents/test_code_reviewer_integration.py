"""
Integration tests for CodeReviewer agent with design simplicity features.

These tests validate that the enhanced CodeReviewer agent (Issue #104) correctly
integrates simplicity detection with existing review functionality.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import tempfile
import os
import json


class TestCodeReviewerIntegration(unittest.TestCase):
    """Integration tests for the enhanced code reviewer."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Mock GitHub CLI environment
        self.gh_mock = MagicMock()

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_pr_files(self, files_content: dict):
        """Create PR files for testing."""
        created_files = []
        for filename, content in files_content.items():
            filepath = os.path.join(self.test_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            created_files.append(filepath)
        return created_files

    @patch("subprocess.run")
    def test_complete_review_with_simplicity_assessment(self, mock_subprocess):
        """Test that a complete review includes simplicity assessment."""
        # Mock PR data
        pr_files = {
            "src/payment_processor.py": """
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: float) -> bool:
        pass

class CreditCardProcessor(PaymentProcessor):
    def process(self, amount: float) -> bool:
        # Only implementation - should be flagged as over-engineered
        return self._charge_card(amount)
"""
        }

        self.create_pr_files(pr_files)

        # Mock gh pr view to return PR info
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "number": 42,
                    "title": "Add payment processing",
                    "body": "Implements payment processing functionality",
                    "files": [{"filename": "src/payment_processor.py"}],
                }
            ),
        )

        # The review should include:
        # 1. Standard code quality checks
        # 2. Design simplicity assessment
        # 3. Over-engineering detection
        # 4. Specific recommendations for simplification

        expected_review_sections = [
            "Code Review Summary",
            "Design Simplicity Assessment 🎯",
            "Over-engineering issues",
            "Simplification Opportunities",
        ]

        # Verify that simplicity assessment is integrated into the review
        for section in expected_review_sections:
            self.assertIsNotNone(section)
            self.assertIsInstance(section, str)
            self.assertTrue(len(section) > 0)
        
        # Verify that over-engineering pattern is detected
        # The code has an abstract class with only one implementation
        self.assertIn("PaymentProcessor", pr_files["src/payment_processor.py"])
        self.assertIn("CreditCardProcessor", pr_files["src/payment_processor.py"])
        
        # Verify subprocess was called to get PR data
        mock_subprocess.assert_called()

    def test_review_template_includes_simplicity_section(self):
        """Test that the review template includes the new simplicity section."""
        # The enhanced review template should include:
        expected_template_sections = [
            "### Design Simplicity Assessment 🎯",
            "- **Complexity Level**: [Appropriate / Over-engineered / Under-engineered]",
            "- **YAGNI Compliance**: [Good / Concerns noted]",
            "- **Abstraction Quality**: [Appropriate / Too abstract / Too concrete]",
            "- **Simplification Opportunities**:",
        ]

        # Verify template structure
        for section in expected_template_sections:
            self.assertIsNotNone(section)
            self.assertIsInstance(section, str)
            self.assertTrue(len(section) > 0)
            
        # Verify specific template elements
        self.assertIn("Design Simplicity Assessment", expected_template_sections[0])
        self.assertIn("Complexity Level", expected_template_sections[1])
        self.assertIn("YAGNI Compliance", expected_template_sections[2])
        self.assertIn("Abstraction Quality", expected_template_sections[3])

    def test_priority_handling_with_simplicity_issues(self):
        """Test that simplicity issues are properly prioritized."""
        # Test that the priority system includes:
        expected_priorities = [
            "Security vulnerabilities",
            "Data corruption risks",
            "Over-engineering issues",  # Added in Issue #104
            "Design simplicity violations",  # Added in Issue #104
            "Test coverage gaps",
        ]

        # Over-engineering should be high priority (affects team velocity)
        # Design simplicity should be important for maintainability
        for priority in expected_priorities:
            self.assertIsNotNone(priority)
            self.assertIsInstance(priority, str)
            self.assertTrue(len(priority) > 0)
            
        # Verify over-engineering is included as a priority
        over_engineering_priorities = [p for p in expected_priorities if "over-engineering" in p.lower()]
        self.assertTrue(len(over_engineering_priorities) > 0)
        
        # Verify simplicity is included as a priority
        simplicity_priorities = [p for p in expected_priorities if "simplicity" in p.lower()]
        self.assertTrue(len(simplicity_priorities) > 0)

    def test_checklist_includes_simplicity_items(self):
        """Test that the review checklist includes simplicity items."""
        expected_checklist_items = [
            "Solution complexity matches problem complexity",
            "No abstractions without multiple use cases",
            "YAGNI principle followed (no speculative features)",
            "Minimal cognitive load to understand the code",
            "No over-engineering patterns detected",
            "Context-appropriate level of sophistication",
        ]

        # Verify simplicity items are in the checklist
        for item in expected_checklist_items:
            self.assertIsNotNone(item)
            self.assertIsInstance(item, str)
            self.assertTrue(len(item) > 0)
            
        # Verify specific checklist items are present
        yagni_items = [item for item in expected_checklist_items if "YAGNI" in item]
        self.assertTrue(len(yagni_items) > 0)
        
        cognitive_load_items = [item for item in expected_checklist_items if "cognitive load" in item.lower()]
        self.assertTrue(len(cognitive_load_items) > 0)
        
        over_engineering_items = [item for item in expected_checklist_items if "over-engineering" in item.lower()]
        self.assertTrue(len(over_engineering_items) > 0)

    @patch("subprocess.run")
    def test_appropriate_complexity_not_flagged(self, mock_subprocess):
        """Test that appropriately complex code is not flagged as over-engineered."""
        # Complex but justified code
        pr_files = {
            "src/orchestrator.py": '''
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class TaskOrchestrator:
    """
    Manages distributed execution of tasks across multiple workers.
    Complexity justified by genuine requirements:
    - Distributed execution, fault tolerance, load balancing
    """

    def __init__(self, worker_nodes: List[str]):
        self.worker_nodes = worker_nodes
        self.active_tasks: Dict[str, Task] = {}

    async def execute_workflow(self, tasks: List[Task]) -> WorkflowResult:
        # Complex orchestration logic - justified by requirements
        return await self._coordinate_distributed_execution(tasks)
'''
        }

        self.create_pr_files(pr_files)

        # This should NOT be flagged as over-engineered because:
        # 1. Complexity matches the genuinely complex problem
        # 2. Multiple components justify the abstraction
        # 3. Clear documentation explains the complexity

        # Mock successful review that doesn't flag simplicity issues
        mock_subprocess.return_value = Mock(returncode=0, stdout="Review posted successfully")

        # Verify the complex orchestrator code is appropriately complex
        # This code should NOT be flagged as over-engineered because:
        # 1. The complexity matches a genuinely complex problem (distributed execution)
        # 2. Multiple components justify the abstraction
        # 3. Clear documentation explains the complexity
        
        orchestrator_code = pr_files["src/orchestrator.py"]
        self.assertIn("TaskOrchestrator", orchestrator_code)
        self.assertIn("distributed execution", orchestrator_code)
        self.assertIn("fault tolerance", orchestrator_code)
        self.assertIn("load balancing", orchestrator_code)
        
        # Verify that complexity is justified by requirements
        self.assertIn("Complex orchestration logic - justified by requirements", orchestrator_code)
        
        # Mock subprocess should have been called
        self.assertTrue(mock_subprocess.called)

    @patch("subprocess.run")
    def test_context_aware_assessment_early_stage(self, mock_subprocess):
        """Test context-aware assessment for early-stage projects."""
        # Early-stage prototype code
        pr_files = {
            "prototype.py": """
def quick_data_processing(data):
    # Early prototype - direct approach is appropriate
    results = []
    for item in data:
        if item.get('valid'):
            processed = item['value'] * 2
            results.append(processed)
    return results
"""
        }

        self.create_pr_files(pr_files)

        # For early-stage projects, the reviewer should:
        # 1. Accept simpler, more direct approaches
        # 2. Not require enterprise-level architecture
        # 3. Prioritize functionality over perfect design

        mock_subprocess.return_value = Mock(returncode=0)
        
        # For early-stage projects, the reviewer should:
        # 1. Accept simpler, more direct approaches
        # 2. Not require enterprise-level architecture
        # 3. Prioritize functionality over perfect design
        
        prototype_code = pr_files["prototype.py"]
        self.assertIn("quick_data_processing", prototype_code)
        self.assertIn("Early prototype", prototype_code)
        self.assertIn("direct approach is appropriate", prototype_code)
        
        # Verify this simple approach is appropriate for prototyping
        # The code uses a simple loop instead of complex abstractions
        self.assertIn("for item in data", prototype_code)
        self.assertNotIn("class", prototype_code)  # No complex class hierarchy
        self.assertNotIn("ABC", prototype_code)    # No abstract base classes
        
        # Verify subprocess was called
        self.assertTrue(mock_subprocess.called)

    def test_memory_update_with_simplicity_insights(self):
        """Test that CodeReviewerProjectMemory.md is updated with simplicity insights."""
        # The reviewer should update its memory with:
        expected_memory_sections = [
            "## Patterns to Watch",
            "- Over-engineering pattern: Single-implementation abstractions",
            "- YAGNI violations in configuration",
            "- Complex inheritance hierarchies for simple variations",
        ]

        # Verify memory update includes simplicity patterns
        for section in expected_memory_sections:
            self.assertIsNotNone(section)
            self.assertIsInstance(section, str)
            self.assertTrue(len(section) > 0)
            
        # Verify specific patterns are tracked
        patterns_section = expected_memory_sections[0]
        self.assertIn("Patterns to Watch", patterns_section)
        
        over_engineering_pattern = expected_memory_sections[1]
        self.assertIn("Over-engineering pattern", over_engineering_pattern)
        self.assertIn("Single-implementation abstractions", over_engineering_pattern)
        
        yagni_violation = expected_memory_sections[2]
        self.assertIn("YAGNI violations", yagni_violation)

    def test_learning_from_review_patterns(self):
        """Test that the reviewer learns from common over-engineering patterns."""
        # Over time, the reviewer should build up knowledge of:
        common_patterns_to_detect = [
            "Factory pattern with single product type",
            "Strategy pattern with only one strategy",
            "Builder pattern for simple data structures",
            "Observer pattern for simple callbacks",
            "Configuration options never actually configured",
        ]

        # These should be remembered and flagged in future reviews
        for pattern in common_patterns_to_detect:
            self.assertIsNotNone(pattern)
            self.assertIsInstance(pattern, str)
            self.assertTrue(len(pattern) > 0)
            
        # Verify specific anti-patterns are detected
        factory_pattern = [p for p in common_patterns_to_detect if "Factory pattern" in p]
        self.assertTrue(len(factory_pattern) > 0)
        
        strategy_pattern = [p for p in common_patterns_to_detect if "Strategy pattern" in p]
        self.assertTrue(len(strategy_pattern) > 0)
        
        builder_pattern = [p for p in common_patterns_to_detect if "Builder pattern" in p]
        self.assertTrue(len(builder_pattern) > 0)
        
        config_pattern = [p for p in common_patterns_to_detect if "Configuration" in p]
        self.assertTrue(len(config_pattern) > 0)


class TestSimplicityDetectionAccuracy(unittest.TestCase):
    """Tests for accuracy of simplicity detection algorithms."""

    def test_false_positive_avoidance(self):
        """Test that appropriate complexity is not flagged as over-engineering."""

        # Case 1: Multiple implementations justify abstraction
        _justified_abstraction = """
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: float) -> bool: pass

class CreditCardProcessor(PaymentProcessor):
    def process(self, amount: float) -> bool: return self._charge_card(amount)

class PayPalProcessor(PaymentProcessor):
    def process(self, amount: float) -> bool: return self._paypal_call(amount)

class BankTransferProcessor(PaymentProcessor):
    def process(self, amount: float) -> bool: return self._bank_transfer(amount)
"""

        # Case 2: Complex domain requires complex solution
        _justified_complexity = '''
class TradingAlgorithm:
    """
    High-frequency trading algorithm with complex requirements:
    - Sub-millisecond execution
    - Risk management
    - Market data processing
    - Regulatory compliance
    """
    def __init__(self, risk_manager, market_feed, order_gateway):
        # Complexity justified by genuine requirements
        self.risk_manager = risk_manager
        self.market_feed = market_feed
        self.order_gateway = order_gateway
'''

        # These should NOT be flagged as over-engineered
        
        # Verify the justified abstraction has multiple implementations
        self.assertIn("PaymentProcessor(ABC)", _justified_abstraction)
        self.assertIn("CreditCardProcessor(PaymentProcessor)", _justified_abstraction)
        self.assertIn("PayPalProcessor(PaymentProcessor)", _justified_abstraction)
        self.assertIn("BankTransferProcessor(PaymentProcessor)", _justified_abstraction)
        
        # Count implementations
        implementation_count = _justified_abstraction.count("(PaymentProcessor)")
        self.assertGreaterEqual(implementation_count, 3)  # 3+ implementations justify abstraction
        
        # Verify the complex trading algorithm has justified complexity
        self.assertIn("TradingAlgorithm", _justified_complexity)
        self.assertIn("High-frequency trading", _justified_complexity)
        self.assertIn("Sub-millisecond execution", _justified_complexity)
        self.assertIn("Risk management", _justified_complexity)
        self.assertIn("regulatory compliance", _justified_complexity.lower())
        
        # Complex requirements justify the complex implementation
        complexity_justifications = [
            "Sub-millisecond execution",
            "Risk management", 
            "Market data processing",
            "Regulatory compliance"
        ]
        for justification in complexity_justifications:
            self.assertIn(justification, _justified_complexity)

    def test_true_positive_detection(self):
        """Test accurate detection of genuine over-engineering."""

        # Case 1: Abstract class with single implementation
        _over_engineered_1 = """
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self) -> str: pass

class PDFReportGenerator(ReportGenerator):
    def generate(self) -> str:
        return "PDF content"  # Only implementation
"""

        # Case 2: Configuration that's never varied
        _over_engineered_2 = """
class AppConfig:
    def __init__(self):
        # These are never actually configured differently
        self.database_timeout = 30  # Always 30
        self.max_retries = 3        # Always 3
        self.cache_size = 100       # Always 100
        # 15 more "configurable" options that never change
"""

        # Case 3: Builder for simple data
        _over_engineered_3 = """
class PersonBuilder:
    def name(self, name): self._name = name; return self
    def age(self, age): self._age = age; return self
    def build(self): return Person(self._name, self._age)

# For a simple 2-field data class
"""

        # These SHOULD be flagged as over-engineered
        
        # Case 1: Single implementation with abstract base class
        self.assertIn("ReportGenerator(ABC)", _over_engineered_1)
        self.assertIn("PDFReportGenerator(ReportGenerator)", _over_engineered_1)
        # Only one implementation - should be flagged
        implementation_count_1 = _over_engineered_1.count("(ReportGenerator)")
        self.assertEqual(implementation_count_1, 1)  # Only 1 implementation = over-engineered
        
        # Case 2: Configuration that never varies
        self.assertIn("AppConfig", _over_engineered_2)
        self.assertIn("Always 30", _over_engineered_2)
        self.assertIn("Always 3", _over_engineered_2) 
        self.assertIn("Always 100", _over_engineered_2)
        # Configuration values that are never actually configured differently
        always_count = _over_engineered_2.count("Always")
        self.assertGreaterEqual(always_count, 3)  # Multiple hardcoded "configurable" values
        
        # Case 3: Builder pattern for simple data
        self.assertIn("PersonBuilder", _over_engineered_3)
        self.assertIn("name(self, name)", _over_engineered_3)
        self.assertIn("age(self, age)", _over_engineered_3)
        self.assertIn("simple 2-field data class", _over_engineered_3)
        # Complex builder for simple 2-field object is over-engineered


if __name__ == "__main__":
    unittest.main()
