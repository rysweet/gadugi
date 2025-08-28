"""
Unit tests for WorkflowValidator

Tests the comprehensive validation and integrity checking system
for workflow execution.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from datetime import datetime

# Import the module under test
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "shared")
)

from workflow_validator import (
    WorkflowValidator,
    ValidationLevel,
    ValidationCategory,
    ValidationRule,
    ValidationResult,
    ValidationReport,
    validate_prompt,
    validate_workflow,
)

# Import workflow engine for WorkflowPhase and WorkflowState
from workflow_engine import WorkflowPhase, WorkflowState


class TestWorkflowValidator:
    """Test suite for WorkflowValidator class"""

    def setup_method(self):
        """Setup test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = WorkflowValidator(ValidationLevel.STANDARD)

        # Create test prompt files
        self.good_prompt_file = os.path.join(self.temp_dir, "good_prompt.md")
        self.bad_prompt_file = os.path.join(self.temp_dir, "bad_prompt.md")
        self.short_prompt_file = os.path.join(self.temp_dir, "short_prompt.md")

        # Good prompt file with proper structure
        with open(self.good_prompt_file, "w") as f:
            f.write("""# Test Workflow Implementation

## Overview
This prompt describes a comprehensive test workflow implementation for validating
the WorkflowValidator system functionality and ensuring proper operation.

## Problem Statement
We need to test various validation scenarios to ensure the validator correctly
identifies issues and provides useful feedback for workflow improvements.

## Implementation Plan
1. Create comprehensive test cases
2. Validate different prompt formats
3. Test git state validation
4. Verify GitHub integration checks

## Code Example
```python
# Example validation code
def validate_workflow(state):
    validator = WorkflowValidator()
    return validator.validate(state)
```

## Success Criteria
- All validation tests pass successfully
- Proper error messages are generated
- Performance metrics are collected
- Integration with workflow engine works correctly

The implementation should be robust and handle various edge cases properly.
""")

        # Bad prompt file without proper structure
        with open(self.bad_prompt_file, "w") as f:
            f.write("""Bad Prompt File

This file doesn't have proper markdown headers and lacks the required sections.
It also doesn't have enough content to be considered a valid prompt.
""")

        # Short prompt file
        with open(self.short_prompt_file, "w") as f:
            f.write("# Short")

        # Create test workflow state
        self.workflow_state = WorkflowState(
            task_id="test-validation",
            prompt_file=self.good_prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
            branch_name="feature/test-validation",
            issue_number=123,
            pr_number=456,
        )

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflow_validator_initialization(self):
        """Test WorkflowValidator initialization"""
        validator = WorkflowValidator(ValidationLevel.STRICT)

        assert validator.validation_level == ValidationLevel.STRICT
        assert len(validator.validation_rules) > 0
        assert validator.validation_history == []
        assert "total_validations" in validator.metrics
        assert validator.metrics["total_validations"] == 0  # type: ignore[index]

    def test_validation_level_enum(self):
        """Test ValidationLevel enum values"""
        levels = [
            ValidationLevel.MINIMAL,
            ValidationLevel.STANDARD,
            ValidationLevel.STRICT,
            ValidationLevel.COMPREHENSIVE,
        ]

        for level in levels:
            assert isinstance(level, ValidationLevel)

        # Test ordering (lower values are less strict)
        assert ValidationLevel.MINIMAL.value < ValidationLevel.STANDARD.value
        assert ValidationLevel.STANDARD.value < ValidationLevel.STRICT.value
        assert ValidationLevel.STRICT.value < ValidationLevel.COMPREHENSIVE.value

    def test_validation_category_enum(self):
        """Test ValidationCategory enum values"""
        categories = [
            ValidationCategory.PROMPT_FORMAT,
            ValidationCategory.GIT_STATE,
            ValidationCategory.GITHUB_INTEGRATION,
            ValidationCategory.PHASE_COMPLETION,
            ValidationCategory.WORKFLOW_INTEGRITY,
            ValidationCategory.PERFORMANCE,
        ]

        for category in categories:
            assert isinstance(category, ValidationCategory)

    def test_validation_rule_creation(self):
        """Test ValidationRule creation and properties"""
        rule = ValidationRule(
            name="test_rule",
            category=ValidationCategory.PROMPT_FORMAT,
            level=ValidationLevel.STANDARD,
            description="Test validation rule",
            validator_function="_test_validator",
            required_context=["prompt_file"],
            error_message="Test error",
            warning_message="Test warning",
        )

        assert rule.name == "test_rule"
        assert rule.category == ValidationCategory.PROMPT_FORMAT
        assert rule.level == ValidationLevel.STANDARD
        assert rule.description == "Test validation rule"
        assert rule.validator_function == "_test_validator"
        assert rule.required_context == ["prompt_file"]
        assert rule.error_message == "Test error"
        assert rule.warning_message == "Test warning"

    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties"""
        result = ValidationResult(
            rule_name="test_rule",
            category=ValidationCategory.PROMPT_FORMAT,
            passed=True,
            level=ValidationLevel.STANDARD,
            message="Validation passed",
            details={"test": "data"},
            execution_time=1.5,
            suggestions=["suggestion1", "suggestion2"],
        )

        assert result.rule_name == "test_rule"
        assert result.category == ValidationCategory.PROMPT_FORMAT
        assert result.passed is True
        assert result.level == ValidationLevel.STANDARD
        assert result.message == "Validation passed"
        assert result.details == {"test": "data"}
        assert result.execution_time == 1.5
        assert result.suggestions == ["suggestion1", "suggestion2"]

    def test_validation_report_creation(self):
        """Test ValidationReport creation and properties"""
        timestamp = datetime.now()
        results = [
            ValidationResult(
                "rule1",
                ValidationCategory.PROMPT_FORMAT,
                True,
                ValidationLevel.STANDARD,
                "Pass",
            ),
            ValidationResult(
                "rule2",
                ValidationCategory.GIT_STATE,
                False,
                ValidationLevel.STANDARD,
                "Fail",
            ),
        ]

        report = ValidationReport(
            timestamp=timestamp,
            validation_level=ValidationLevel.STANDARD,
            total_checks=2,
            passed_checks=1,
            failed_checks=1,
            warnings=1,
            errors=0,
            overall_status="PASSED_WITH_WARNINGS",
            results=results,
            metrics={"test": "metric"},
            recommendations=["Fix failing check"],
        )

        assert report.timestamp == timestamp
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks == 2
        assert report.passed_checks == 1
        assert report.failed_checks == 1
        assert report.warnings == 1
        assert report.errors == 0
        assert report.overall_status == "PASSED_WITH_WARNINGS"
        assert len(report.results) == 2
        assert report.metrics == {"test": "metric"}
        assert report.recommendations == ["Fix failing check"]

    def test_validate_prompt_file_exists_success(self):
        """Test successful prompt file existence validation"""
        context = {"prompt_file": self.good_prompt_file}
        result = self.validator._validate_prompt_file_exists(context)

        assert result.passed is True
        assert result.rule_name == "prompt_file_exists"
        assert result.category == ValidationCategory.PROMPT_FORMAT
        assert "exists and is readable" in result.message
        assert "file_size" in result.details
        assert result.details["file_path"] == self.good_prompt_file  # type: ignore[index]

    def test_validate_prompt_file_exists_missing(self):
        """Test prompt file existence validation with missing file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.md")
        context = {"prompt_file": nonexistent_file}

        result = self.validator._validate_prompt_file_exists(context)

        assert result.passed is False
        assert "does not exist" in result.message
        assert len(result.suggestions) > 0

    def test_validate_prompt_file_exists_no_file_specified(self):
        """Test prompt file validation with no file specified"""
        context = {}

        result = self.validator._validate_prompt_file_exists(context)

        assert result.passed is False
        assert "no prompt file specified" in result.message.lower()

    def test_validate_prompt_format_success(self):
        """Test successful prompt format validation"""
        context = {"prompt_file": self.good_prompt_file}
        result = self.validator._validate_prompt_format(context)

        assert result.passed is True
        assert result.rule_name == "prompt_format"
        assert "validation passed" in result.message.lower()
        assert result.details["content_length"] > 0  # type: ignore[index]

    def test_validate_prompt_format_bad_format(self):
        """Test prompt format validation with bad format"""
        context = {"prompt_file": self.bad_prompt_file}
        result = self.validator._validate_prompt_format(context)

        assert result.passed is False
        assert "format issues found" in result.message.lower()
        assert len(result.details["issues_found"]) > 0  # type: ignore[index]
        assert len(result.suggestions) > 0

    def test_validate_prompt_format_short_content(self):
        """Test prompt format validation with short content"""
        context = {"prompt_file": self.short_prompt_file}
        result = self.validator._validate_prompt_format(context)

        assert result.passed is False
        assert "too short" in result.message.lower()

    @patch("subprocess.run")
    def test_validate_git_clean_state_success(self, mock_subprocess):
        """Test successful git clean state validation"""
        # Mock git status returning empty (clean state)
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        result = self.validator._validate_git_clean_state({})

        assert result.passed is True
        assert "repository is clean" in result.message.lower()
        assert result.details["uncommitted_files"] == []  # type: ignore[index]

    @patch("subprocess.run")
    def test_validate_git_clean_state_dirty(self, mock_subprocess):
        """Test git clean state validation with uncommitted changes"""
        # Mock git status returning changes
        mock_subprocess.return_value = Mock(
            returncode=0, stdout=" M file1.py\n?? file2.md\n", stderr=""
        )

        result = self.validator._validate_git_clean_state({})

        assert result.passed is False
        assert "uncommitted changes" in result.message.lower()
        assert len(result.details["uncommitted_files"]) == 2  # type: ignore[index]
        assert len(result.suggestions) > 0

    @patch("subprocess.run")
    def test_validate_git_clean_state_failure(self, mock_subprocess):
        """Test git clean state validation with git command failure"""
        # Mock git command failure
        mock_subprocess.return_value = Mock(
            returncode=1, stdout="", stderr="Not a git repo"
        )

        result = self.validator._validate_git_clean_state({})

        assert result.passed is False
        assert "failed to check git status" in result.message.lower()

    @patch("subprocess.run")
    def test_validate_branch_exists_success(self, mock_subprocess):
        """Test successful branch existence validation"""
        # Mock git commands for branch existence and current branch
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git show-ref (branch exists)
            Mock(
                returncode=0, stdout="feature/test-validation\n", stderr=""
            ),  # git branch --show-current
        ]

        context = {"workflow_state": self.workflow_state}
        result = self.validator._validate_branch_exists(context)

        assert result.passed is True
        assert "exists=True" in result.message
        assert "current=True" in result.message
        assert result.details["on_correct_branch"] is True  # type: ignore[index]

    @patch("subprocess.run")
    def test_validate_branch_exists_wrong_branch(self, mock_subprocess):
        """Test branch validation when on wrong branch"""
        # Mock branch exists but we're on different branch
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # git show-ref (branch exists)
            Mock(
                returncode=0, stdout="main\n", stderr=""
            ),  # git branch --show-current (wrong branch)
        ]

        context = {"workflow_state": self.workflow_state}
        result = self.validator._validate_branch_exists(context)

        assert result.passed is False
        assert result.details["on_correct_branch"] is False  # type: ignore[index]
        assert len(result.suggestions) > 0

    @patch("subprocess.run")
    def test_validate_branch_exists_missing_branch(self, mock_subprocess):
        """Test branch validation when branch doesn't exist"""
        # Mock branch doesn't exist
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="")

        context = {"workflow_state": self.workflow_state}
        result = self.validator._validate_branch_exists(context)

        assert result.passed is False
        assert "does not exist" in result.message
        assert len(result.suggestions) > 0

    def test_validate_branch_exists_no_workflow_state(self):
        """Test branch validation without workflow state"""
        context = {}
        result = self.validator._validate_branch_exists(context)

        assert result.passed is False
        assert "no branch name specified" in result.message.lower()

    @patch("subprocess.run")
    def test_validate_pr_exists_success(self, mock_subprocess):
        """Test successful PR existence validation"""
        # Mock successful gh pr view
        mock_pr_data = {"state": "OPEN", "title": "Test PR"}
        mock_subprocess.return_value = Mock(
            returncode=0, stdout=json.dumps(mock_pr_data), stderr=""
        )

        context = {"workflow_state": self.workflow_state}
        result = self.validator._validate_pr_exists(context)

        assert result.passed is True
        assert "exists and is OPEN" in result.message
        assert result.details["pr_state"] == "OPEN"  # type: ignore[index]
        assert result.details["pr_title"] == "Test PR"  # type: ignore[index]

    @patch("subprocess.run")
    def test_validate_pr_exists_failure(self, mock_subprocess):
        """Test PR validation when PR doesn't exist"""
        # Mock gh pr view failure
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Not found")

        context = {"workflow_state": self.workflow_state}
        result = self.validator._validate_pr_exists(context)

        assert result.passed is False
        assert "does not exist or is not accessible" in result.message
        assert len(result.suggestions) > 0

    def test_validate_pr_exists_no_pr_number(self):
        """Test PR validation without PR number"""
        workflow_state = WorkflowState(
            task_id="test",
            prompt_file="test.md",
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
            pr_number=None,
        )

        context = {"workflow_state": workflow_state}
        result = self.validator._validate_pr_exists(context)

        assert result.passed is False
        assert "no pr number specified" in result.message.lower()

    def test_validate_phase_sequence_success(self):
        """Test successful phase sequence validation"""
        workflow_state = WorkflowState(
            task_id="test-sequence",
            prompt_file="test.md",
            current_phase=WorkflowPhase.PROMPT_VALIDATION,
            completed_phases=[WorkflowPhase.INIT, WorkflowPhase.PROMPT_VALIDATION],
        )

        context = {"workflow_state": workflow_state}
        result = self.validator._validate_phase_sequence(context)

        assert result.passed is True
        assert "sequence is correct" in result.message.lower()

    def test_validate_phase_sequence_no_workflow_state(self):
        """Test phase sequence validation without workflow state"""
        context = {}
        result = self.validator._validate_phase_sequence(context)

        assert result.passed is False
        assert "no workflow state provided" in result.message.lower()

    def test_validate_prompt_file_complete(self):
        """Test complete prompt file validation"""
        report = self.validator.validate_prompt_file(self.good_prompt_file)

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0
        assert report.overall_status in ["PASSED", "PASSED_WITH_WARNINGS", "FAILED"]
        assert len(report.results) > 0

    def test_validate_workflow_state_complete(self):
        """Test complete workflow state validation"""
        report = self.validator.validate_workflow_state(self.workflow_state)

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0
        assert len(report.results) > 0

    @patch("subprocess.run")
    def test_validate_git_environment_complete(self, mock_subprocess):
        """Test complete git environment validation"""
        # Mock git status as clean
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        report = self.validator.validate_git_environment()

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0

    @patch("subprocess.run")
    def test_validate_github_integration_complete(self, mock_subprocess):
        """Test complete GitHub integration validation"""
        # Mock successful GitHub operations
        mock_pr_data = {"state": "OPEN", "title": "Test PR"}
        mock_subprocess.return_value = Mock(
            returncode=0, stdout=json.dumps(mock_pr_data), stderr=""
        )

        report = self.validator.validate_github_integration(self.workflow_state)

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0

    @patch("subprocess.run")
    def test_validate_end_to_end_complete(self, mock_subprocess):
        """Test complete end-to-end validation"""
        # Mock all external calls to succeed
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"state": "OPEN", "title": "Test PR"}),
            stderr="",
        )

        report = self.validator.validate_end_to_end(
            self.good_prompt_file, self.workflow_state
        )

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0
        assert len(report.results) > 0

    def test_execute_validation_rule_missing_context(self):
        """Test validation rule execution with missing context"""
        rule = ValidationRule(
            name="test_rule",
            category=ValidationCategory.PROMPT_FORMAT,
            level=ValidationLevel.STANDARD,
            description="Test rule",
            validator_function="_validate_prompt_file_exists",
            required_context=["prompt_file", "missing_context"],
        )

        context = {"prompt_file": self.good_prompt_file}
        result = self.validator._execute_validation_rule(rule, context)

        assert result.passed is False
        assert "missing required context" in result.message.lower()
        assert "missing_context" in result.message

    def test_execute_validation_rule_missing_validator(self):
        """Test validation rule execution with missing validator function"""
        rule = ValidationRule(
            name="test_rule",
            category=ValidationCategory.PROMPT_FORMAT,
            level=ValidationLevel.STANDARD,
            description="Test rule",
            validator_function="_nonexistent_validator",
            required_context=[],
        )

        result = self.validator._execute_validation_rule(rule, {})

        assert result.passed is False
        assert "validator function not found" in result.message.lower()

    def test_generate_report_all_passed(self):
        """Test report generation when all validations pass"""
        results = [
            ValidationResult(
                "rule1",
                ValidationCategory.PROMPT_FORMAT,
                True,
                ValidationLevel.STANDARD,
                "Pass 1",
            ),
            ValidationResult(
                "rule2",
                ValidationCategory.GIT_STATE,
                True,
                ValidationLevel.STANDARD,
                "Pass 2",
            ),
        ]

        start_time = datetime.now()
        report = self.validator._generate_report(results, start_time, "Test Report")

        assert report.overall_status == "PASSED"
        assert report.passed_checks == 2
        assert report.failed_checks == 0
        assert report.warnings == 0
        assert report.errors == 0

    def test_generate_report_with_failures(self):
        """Test report generation with failures"""
        results = [
            ValidationResult(
                "rule1",
                ValidationCategory.PROMPT_FORMAT,
                True,
                ValidationLevel.STANDARD,
                "Pass",
            ),
            ValidationResult(
                "rule2",
                ValidationCategory.GIT_STATE,
                False,
                ValidationLevel.STANDARD,
                "Fail warning",
            ),
            ValidationResult(
                "rule3",
                ValidationCategory.GITHUB_INTEGRATION,
                False,
                ValidationLevel.STRICT,
                "Fail error",
            ),
        ]

        start_time = datetime.now()
        report = self.validator._generate_report(results, start_time, "Test Report")

        assert report.overall_status == "FAILED"  # Has errors
        assert report.passed_checks == 1
        assert report.failed_checks == 2
        assert report.warnings == 1  # STANDARD level failure
        assert report.errors == 1  # STRICT level failure

    def test_generate_report_with_suggestions(self):
        """Test report generation includes suggestions"""
        results = [
            ValidationResult(
                "rule1",
                ValidationCategory.PROMPT_FORMAT,
                False,
                ValidationLevel.STANDARD,
                "Fail",
                suggestions=["Fix this", "Do that"],
            ),
            ValidationResult(
                "rule2",
                ValidationCategory.GIT_STATE,
                False,
                ValidationLevel.STANDARD,
                "Fail",
                suggestions=["Fix this", "Another fix"],  # Duplicate suggestion
            ),
        ]

        start_time = datetime.now()
        report = self.validator._generate_report(results, start_time, "Test Report")

        # Should have unique suggestions only
        assert len(report.recommendations) == 3
        assert "Fix this" in report.recommendations
        assert "Do that" in report.recommendations
        assert "Another fix" in report.recommendations

    def test_validation_history_tracking(self):
        """Test that validation history is properly tracked"""
        initial_count = len(self.validator.validation_history)

        # Run a validation
        report = self.validator.validate_prompt_file(self.good_prompt_file)

        # Check history was updated
        assert len(self.validator.validation_history) == initial_count + 1
        assert self.validator.validation_history[-1] == report  # type: ignore[index]

        # Check metrics were updated
        assert self.validator.metrics["total_validations"] == initial_count + 1  # type: ignore[index]

    def test_validation_history_limit(self):
        """Test that validation history is limited to prevent memory issues"""
        # Add many fake reports to history
        for i in range(55):  # More than the 50 limit
            fake_report = ValidationReport(
                timestamp=datetime.now(),
                validation_level=ValidationLevel.STANDARD,
                total_checks=1,
                passed_checks=1,
                failed_checks=0,
                warnings=0,
                errors=0,
                overall_status="PASSED",
                results=[],
                metrics={},
                recommendations=[],
            )
            self.validator.validation_history.append(fake_report)

        # Run another validation
        self.validator.validate_prompt_file(self.good_prompt_file)

        # Should be limited to 50
        assert len(self.validator.validation_history) == 50

    def test_export_validation_report(self):
        """Test validation report export to JSON"""
        report = self.validator.validate_prompt_file(self.good_prompt_file)
        filename = self.validator.export_validation_report(report)

        # Check file was created
        assert os.path.exists(filename)

        # Check file content
        with open(filename, "r") as f:
            report_data = json.load(f)

        assert "metadata" in report_data
        assert "summary" in report_data
        assert "metrics" in report_data
        assert "recommendations" in report_data
        assert "results" in report_data

        assert report_data["metadata"]["overall_status"] == report.overall_status  # type: ignore[index]
        assert report_data["summary"]["total_checks"] == report.total_checks  # type: ignore[index]
        assert len(report_data["results"]) == len(report.results)  # type: ignore[index]

        # Cleanup
        os.remove(filename)

    def test_validation_levels_filtering(self):
        """Test that validation rules are filtered by validation level"""
        # Create validators with different levels
        minimal_validator = WorkflowValidator(ValidationLevel.MINIMAL)
        comprehensive_validator = WorkflowValidator(ValidationLevel.COMPREHENSIVE)

        # Run same validation with different levels
        minimal_report = minimal_validator.validate_prompt_file(self.good_prompt_file)
        comprehensive_report = comprehensive_validator.validate_prompt_file(
            self.good_prompt_file
        )

        # Comprehensive should have more checks
        assert comprehensive_report.total_checks >= minimal_report.total_checks


class TestConvenienceFunctions:
    """Test suite for convenience functions"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_file = os.path.join(self.temp_dir, "test_prompt.md")

        with open(self.prompt_file, "w") as f:
            f.write("""# Test Prompt

## Overview
Test prompt for convenience function testing.

## Implementation
Test implementation details.

## Success Criteria
- Validation should work correctly
- Report should be generated
""")

    def teardown_method(self):
        """Cleanup after each test"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_prompt_convenience_function(self):
        """Test validate_prompt convenience function"""
        report = validate_prompt(self.prompt_file, ValidationLevel.STANDARD)

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0

    def test_validate_workflow_convenience_function(self):
        """Test validate_workflow convenience function"""
        workflow_state = WorkflowState(
            task_id="test-convenience",
            prompt_file=self.prompt_file,
            current_phase=WorkflowPhase.INIT,
            completed_phases=[],
        )

        with patch("subprocess.run") as mock_subprocess:
            # Mock external calls
            mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

            report = validate_workflow(
                self.prompt_file, workflow_state, ValidationLevel.STANDARD
            )

        assert isinstance(report, ValidationReport)
        assert report.validation_level == ValidationLevel.STANDARD
        assert report.total_checks > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
