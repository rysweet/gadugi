"""
Workflow Validation System for WorkflowManager

This module provides comprehensive validation and integrity checking
for workflow execution to ensure consistent and reliable operation.

Key Features:
- Pre-execution prompt validation
- Phase completion verification
- Automatic issue and PR validation
- End-to-end workflow integrity checks
- Performance and quality metrics
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

# Import workflow engine components
try:
    from .workflow_engine import WorkflowPhase as EngineWorkflowPhase, WorkflowState as EngineWorkflowState  # type: ignore
    WorkflowPhase = EngineWorkflowPhase  # type: ignore
    WorkflowState = EngineWorkflowState  # type: ignore
except ImportError:
    try:
        # Try absolute import if relative import fails
        from workflow_engine import WorkflowPhase as EngineWorkflowPhase, WorkflowState as EngineWorkflowState  # type: ignore
        WorkflowPhase = EngineWorkflowPhase  # type: ignore
        WorkflowState = EngineWorkflowState  # type: ignore
    except ImportError:
        # Minimal definitions if workflow_engine not available
        class WorkflowPhase(Enum):
            INIT = auto()
            PROMPT_VALIDATION = auto()

        @dataclass
        class WorkflowState:
            """Minimal WorkflowState for when workflow_engine is not available"""
            prompt_file: str = ""
            current_phase: Optional[WorkflowPhase] = None
            phases_completed: Dict[str, bool] = field(default_factory=dict)
            context: Dict[str, Any] = field(default_factory=dict)

            def __post_init__(self):  # type: ignore
                if self.context is None:
                    self.context = {}


class ValidationLevel(Enum):
    """Validation strictness levels"""
    MINIMAL = auto()
    STANDARD = auto()
    STRICT = auto()
    COMPREHENSIVE = auto()


class ValidationCategory(Enum):
    """Categories of validation checks"""
    PROMPT_FORMAT = auto()
    GIT_STATE = auto()
    GITHUB_INTEGRATION = auto()
    PHASE_COMPLETION = auto()
    WORKFLOW_INTEGRITY = auto()
    PERFORMANCE = auto()


@dataclass
class ValidationRule:
    """Defines a validation rule"""
    name: str
    category: ValidationCategory
    level: ValidationLevel
    description: str
    validator_function: str  # Name of the method to call
    required_context: List[str] = field(default_factory=list)
    error_message: str = ""
    warning_message: str = ""


@dataclass
class ValidationResult:
    """Result of a validation check"""
    rule_name: str
    category: ValidationCategory
    passed: bool
    level: ValidationLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    timestamp: datetime
    validation_level: ValidationLevel
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    errors: int
    overall_status: str
    results: List[ValidationResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class WorkflowValidator:
    """
    Comprehensive workflow validation system that ensures
    quality, consistency, and integrity of workflow execution.
    """

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize validator with specified validation level"""

        self.validation_level = validation_level
        self.validation_rules = self._initialize_validation_rules()
        self.validation_history = []

        # Performance tracking
        self.metrics = {
            'total_validations': 0,
            'validation_time': 0,
            'success_rate': 0,
            'common_failures': {}
        }

    def validate_prompt_file(self, prompt_file: str) -> ValidationReport:
        """
        Validate prompt file format, content, and requirements

        Args:
            prompt_file: Path to the prompt file to validate

        Returns:
            ValidationReport with detailed validation results
        """

        start_time = datetime.now()
        results = []

        # Get rules for prompt validation
        prompt_rules = [
            rule for rule in self.validation_rules
            if rule.category == ValidationCategory.PROMPT_FORMAT
            and rule.level.value <= self.validation_level.value
        ]

        context = {'prompt_file': prompt_file}

        for rule in prompt_rules:
            result = self._execute_validation_rule(rule, context)
            results.append(result)

        return self._generate_report(results, start_time, 'Prompt File Validation')

    def validate_workflow_state(self, workflow_state: WorkflowState) -> ValidationReport:
        """
        Validate current workflow state and phase completion

        Args:
            workflow_state: Current workflow state to validate

        Returns:
            ValidationReport with state validation results
        """

        start_time = datetime.now()
        results = []

        # Get rules for state validation
        state_rules = [
            rule for rule in self.validation_rules
            if rule.category in [ValidationCategory.PHASE_COMPLETION, ValidationCategory.WORKFLOW_INTEGRITY]
            and rule.level.value <= self.validation_level.value
        ]

        context = {'workflow_state': workflow_state}

        for rule in state_rules:
            result = self._execute_validation_rule(rule, context)
            results.append(result)

        return self._generate_report(results, start_time, 'Workflow State Validation')

    def validate_git_environment(self) -> ValidationReport:
        """
        Validate git repository state and environment

        Returns:
            ValidationReport with git validation results
        """

        start_time = datetime.now()
        results = []

        # Get rules for git validation
        git_rules = [
            rule for rule in self.validation_rules
            if rule.category == ValidationCategory.GIT_STATE
            and rule.level.value <= self.validation_level.value
        ]

        context = {}

        for rule in git_rules:
            result = self._execute_validation_rule(rule, context)
            results.append(result)

        return self._generate_report(results, start_time, 'Git Environment Validation')

    def validate_github_integration(self, workflow_state: WorkflowState) -> ValidationReport:
        """
        Validate GitHub integration (PRs, issues, etc.)

        Args:
            workflow_state: Workflow state with GitHub integration details

        Returns:
            ValidationReport with GitHub validation results
        """

        start_time = datetime.now()
        results = []

        # Get rules for GitHub validation
        github_rules = [
            rule for rule in self.validation_rules
            if rule.category == ValidationCategory.GITHUB_INTEGRATION
            and rule.level.value <= self.validation_level.value
        ]

        context = {'workflow_state': workflow_state}

        for rule in github_rules:
            result = self._execute_validation_rule(rule, context)
            results.append(result)

        return self._generate_report(results, start_time, 'GitHub Integration Validation')

    def validate_end_to_end(self,
                           prompt_file: str,
                           workflow_state: WorkflowState) -> ValidationReport:
        """
        Comprehensive end-to-end workflow validation

        Args:
            prompt_file: Prompt file used for workflow
            workflow_state: Current workflow state

        Returns:
            ValidationReport with comprehensive validation results
        """

        start_time = datetime.now()
        all_results = []

        # Run all validation categories
        validation_reports = [
            self.validate_prompt_file(prompt_file),
            self.validate_workflow_state(workflow_state),
            self.validate_git_environment(),
            self.validate_github_integration(workflow_state)
        ]

        # Aggregate results
        for report in validation_reports:
            all_results.extend(report.results)

        # Add comprehensive integrity checks
        integrity_rules = [
            rule for rule in self.validation_rules
            if rule.category == ValidationCategory.WORKFLOW_INTEGRITY
            and rule.level.value <= self.validation_level.value
        ]

        context = {
            'prompt_file': prompt_file,
            'workflow_state': workflow_state,
            'validation_reports': validation_reports
        }

        for rule in integrity_rules:
            result = self._execute_validation_rule(rule, context)
            all_results.append(result)

        return self._generate_report(all_results, start_time, 'End-to-End Validation')

    # Validation rule implementations

    def _validate_prompt_file_exists(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate that prompt file exists and is readable"""

        prompt_file = context.get('prompt_file')
        start_time = datetime.now()

        if not prompt_file:
            return ValidationResult(
                rule_name='prompt_file_exists',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=False,
                level=ValidationLevel.MINIMAL,
                message='No prompt file specified',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        if not os.path.exists(prompt_file):
            return ValidationResult(
                rule_name='prompt_file_exists',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=False,
                level=ValidationLevel.MINIMAL,
                message=f'Prompt file does not exist: {prompt_file}',
                suggestions=['Check file path spelling', 'Ensure file was created'],
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return ValidationResult(
                rule_name='prompt_file_exists',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=True,
                level=ValidationLevel.MINIMAL,
                message=f'Prompt file exists and is readable',
                details={'file_size': len(content), 'file_path': prompt_file},
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ValidationResult(
                rule_name='prompt_file_exists',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=False,
                level=ValidationLevel.MINIMAL,
                message=f'Prompt file exists but is not readable: {str(e)}',
                suggestions=['Check file permissions', 'Verify file is not corrupted'],
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _validate_prompt_format(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate prompt file format and structure"""

        prompt_file = context.get('prompt_file')
        start_time = datetime.now()

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:  # type: ignore
                content = f.read()

            issues = []
            suggestions = []

            # Check for title
            if not content.strip().startswith('#'):
                issues.append('Missing markdown title (should start with #)')
                suggestions.append('Add a descriptive title starting with #')

            # Check minimum content length
            if len(content.strip()) < 100:
                issues.append('Content too short (less than 100 characters)')
                suggestions.append('Add more detailed description and requirements')

            # Check for key sections
            required_sections = ['Overview', 'Problem', 'Implementation', 'Success']
            missing_sections = []

            for section in required_sections:
                if section.lower() not in content.lower():
                    missing_sections.append(section)

            if missing_sections:
                issues.append(f'Missing recommended sections: {", ".join(missing_sections)}')
                suggestions.append('Add standard sections for better clarity')

            # Check for code blocks or implementation details
            if '```' not in content and 'implementation' in content.lower():
                issues.append('Implementation details present but no code examples')
                suggestions.append('Add code examples or implementation snippets')

            passed = len(issues) == 0
            message = 'Prompt format validation passed' if passed else f'Format issues found: {"; ".join(issues)}'

            return ValidationResult(
                rule_name='prompt_format',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=passed,
                level=ValidationLevel.STANDARD,
                message=message,
                details={
                    'content_length': len(content),
                    'issues_found': issues,
                    'missing_sections': missing_sections
                },
                suggestions=suggestions,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ValidationResult(
                rule_name='prompt_format',
                category=ValidationCategory.PROMPT_FORMAT,
                passed=False,
                level=ValidationLevel.STANDARD,
                message=f'Failed to validate prompt format: {str(e)}',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _validate_git_clean_state(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate git repository is in clean state"""

        start_time = datetime.now()

        try:
            # Check git status
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return ValidationResult(
                    rule_name='git_clean_state',
                    category=ValidationCategory.GIT_STATE,
                    passed=False,
                    level=ValidationLevel.STANDARD,
                    message='Failed to check git status',
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            status_output = result.stdout.strip()
            has_changes = len(status_output) > 0

            return ValidationResult(
                rule_name='git_clean_state',
                category=ValidationCategory.GIT_STATE,
                passed=not has_changes,
                level=ValidationLevel.STANDARD,
                message='Git repository is clean' if not has_changes else 'Git repository has uncommitted changes',
                details={'uncommitted_files': status_output.split('\n') if has_changes else []},
                suggestions=['Commit or stash changes before proceeding'] if has_changes else [],
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ValidationResult(
                rule_name='git_clean_state',
                category=ValidationCategory.GIT_STATE,
                passed=False,
                level=ValidationLevel.STANDARD,
                message=f'Git state validation failed: {str(e)}',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _validate_branch_exists(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate that workflow branch exists and is properly configured"""

        workflow_state = context.get('workflow_state')
        start_time = datetime.now()

        if not workflow_state or not workflow_state.branch_name:
            return ValidationResult(
                rule_name='branch_exists',
                category=ValidationCategory.GIT_STATE,
                passed=False,
                level=ValidationLevel.STANDARD,
                message='No branch name specified in workflow state',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Check if branch exists
            result = subprocess.run(['git', 'show-ref', '--verify', '--quiet',
                                   f'refs/heads/{workflow_state.branch_name}'],
                                  capture_output=True, timeout=10)

            branch_exists = result.returncode == 0

            if not branch_exists:
                return ValidationResult(
                    rule_name='branch_exists',
                    category=ValidationCategory.GIT_STATE,
                    passed=False,
                    level=ValidationLevel.STANDARD,
                    message=f'Branch does not exist: {workflow_state.branch_name}',
                    suggestions=['Create branch before proceeding with workflow'],
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # Check if currently on the branch
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  capture_output=True, text=True, timeout=10)

            current_branch = result.stdout.strip()
            on_correct_branch = current_branch == workflow_state.branch_name

            return ValidationResult(
                rule_name='branch_exists',
                category=ValidationCategory.GIT_STATE,
                passed=branch_exists and on_correct_branch,
                level=ValidationLevel.STANDARD,
                message=f'Branch validation: exists={branch_exists}, current={on_correct_branch}',
                details={
                    'branch_name': workflow_state.branch_name,
                    'current_branch': current_branch,
                    'on_correct_branch': on_correct_branch
                },
                suggestions=['Switch to workflow branch'] if not on_correct_branch else [],
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ValidationResult(
                rule_name='branch_exists',
                category=ValidationCategory.GIT_STATE,
                passed=False,
                level=ValidationLevel.STANDARD,
                message=f'Branch validation failed: {str(e)}',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _validate_pr_exists(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate that PR exists and is properly configured"""

        workflow_state = context.get('workflow_state')
        start_time = datetime.now()

        if not workflow_state or not workflow_state.pr_number:
            return ValidationResult(
                rule_name='pr_exists',
                category=ValidationCategory.GITHUB_INTEGRATION,
                passed=False,
                level=ValidationLevel.STANDARD,
                message='No PR number specified in workflow state',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        try:
            # Check if PR exists using GitHub CLI
            result = subprocess.run(['gh', 'pr', 'view', str(workflow_state.pr_number), '--json', 'state,title'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return ValidationResult(
                    rule_name='pr_exists',
                    category=ValidationCategory.GITHUB_INTEGRATION,
                    passed=False,
                    level=ValidationLevel.STANDARD,
                    message=f'PR #{workflow_state.pr_number} does not exist or is not accessible',
                    suggestions=['Verify PR number', 'Check GitHub authentication'],
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            pr_data = json.loads(result.stdout)
            pr_state = pr_data.get('state', 'unknown')
            pr_title = pr_data.get('title', 'unknown')

            return ValidationResult(
                rule_name='pr_exists',
                category=ValidationCategory.GITHUB_INTEGRATION,
                passed=True,
                level=ValidationLevel.STANDARD,
                message=f'PR #{workflow_state.pr_number} exists and is {pr_state}',
                details={
                    'pr_number': workflow_state.pr_number,
                    'pr_state': pr_state,
                    'pr_title': pr_title
                },
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            return ValidationResult(
                rule_name='pr_exists',
                category=ValidationCategory.GITHUB_INTEGRATION,
                passed=False,
                level=ValidationLevel.STANDARD,
                message=f'PR validation failed: {str(e)}',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _validate_phase_sequence(self, context: Dict[str, Any]) -> ValidationResult:
        """Validate that workflow phases are executed in correct sequence"""

        workflow_state = context.get('workflow_state')
        start_time = datetime.now()

        if not workflow_state:
            return ValidationResult(
                rule_name='phase_sequence',
                category=ValidationCategory.PHASE_COMPLETION,
                passed=False,
                level=ValidationLevel.STANDARD,
                message='No workflow state provided for phase sequence validation',
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        # Define expected phase sequence
        expected_sequence = [
            WorkflowPhase.INIT,
            WorkflowPhase.PROMPT_VALIDATION,
            # Add other phases as needed
        ]

        completed_phases = workflow_state.completed_phases
        issues = []

        # Check for sequence violations
        for i, phase in enumerate(completed_phases):
            if i < len(expected_sequence):
                if phase != expected_sequence[i]:
                    issues.append(f'Expected phase {expected_sequence[i].name} at position {i}, got {phase.name}')
            else:
                # Phase beyond expected sequence
                issues.append(f'Unexpected phase {phase.name} at position {i} (beyond expected sequence)')

        # Check if any expected phases are missing
        if len(completed_phases) < len(expected_sequence):
            for i in range(len(completed_phases), len(expected_sequence)):
                issues.append(f'Missing expected phase {expected_sequence[i].name} at position {i}')

        passed = len(issues) == 0
        message = 'Phase sequence is correct' if passed else f'Phase sequence issues: {"; ".join(issues)}'

        return ValidationResult(
            rule_name='phase_sequence',
            category=ValidationCategory.PHASE_COMPLETION,
            passed=passed,
            level=ValidationLevel.STANDARD,
            message=message,
            details={
                'completed_phases': [p.name for p in completed_phases],
                'expected_sequence': [p.name for p in expected_sequence],
                'sequence_issues': issues
            },
            suggestions=['Review workflow execution order'] if not passed else [],
            execution_time=(datetime.now() - start_time).total_seconds()
        )

    # Helper methods

    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize all validation rules"""

        return [
            # Prompt format rules
            ValidationRule(
                name='prompt_file_exists',
                category=ValidationCategory.PROMPT_FORMAT,
                level=ValidationLevel.MINIMAL,
                description='Validate prompt file exists and is readable',
                validator_function='_validate_prompt_file_exists',
                required_context=['prompt_file'],
                error_message='Prompt file is missing or unreadable'
            ),
            ValidationRule(
                name='prompt_format',
                category=ValidationCategory.PROMPT_FORMAT,
                level=ValidationLevel.STANDARD,
                description='Validate prompt file format and structure',
                validator_function='_validate_prompt_format',
                required_context=['prompt_file'],
                error_message='Prompt file format is invalid'
            ),

            # Git state rules
            ValidationRule(
                name='git_clean_state',
                category=ValidationCategory.GIT_STATE,
                level=ValidationLevel.STANDARD,
                description='Validate git repository is in clean state',
                validator_function='_validate_git_clean_state',
                warning_message='Git repository has uncommitted changes'
            ),
            ValidationRule(
                name='branch_exists',
                category=ValidationCategory.GIT_STATE,
                level=ValidationLevel.STANDARD,
                description='Validate workflow branch exists',
                validator_function='_validate_branch_exists',
                required_context=['workflow_state'],
                error_message='Workflow branch does not exist'
            ),

            # GitHub integration rules
            ValidationRule(
                name='pr_exists',
                category=ValidationCategory.GITHUB_INTEGRATION,
                level=ValidationLevel.STANDARD,
                description='Validate PR exists and is accessible',
                validator_function='_validate_pr_exists',
                required_context=['workflow_state'],
                error_message='PR does not exist or is not accessible'
            ),

            # Phase completion rules
            ValidationRule(
                name='phase_sequence',
                category=ValidationCategory.PHASE_COMPLETION,
                level=ValidationLevel.STANDARD,
                description='Validate phases are executed in correct sequence',
                validator_function='_validate_phase_sequence',
                required_context=['workflow_state'],
                error_message='Workflow phases executed out of sequence'
            )
        ]

    def _execute_validation_rule(self, rule: ValidationRule, context: Dict[str, Any]) -> ValidationResult:
        """Execute a single validation rule"""

        try:
            # Check if all required context is available
            missing_context = [ctx for ctx in rule.required_context if ctx not in context]
            if missing_context:
                return ValidationResult(
                    rule_name=rule.name,
                    category=rule.category,
                    passed=False,
                    level=rule.level,
                    message=f'Missing required context: {", ".join(missing_context)}',
                    execution_time=0.0
                )

            # Execute the validator function
            validator_method = getattr(self, rule.validator_function, None)
            if not validator_method:
                return ValidationResult(
                    rule_name=rule.name,
                    category=rule.category,
                    passed=False,
                    level=rule.level,
                    message=f'Validator function not found: {rule.validator_function}',
                    execution_time=0.0
                )

            return validator_method(context)

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                category=rule.category,
                passed=False,
                level=rule.level,
                message=f'Validation rule execution failed: {str(e)}',
                execution_time=0.0
            )

    def _generate_report(self,
                        results: List[ValidationResult],
                        start_time: datetime,
                        report_type: str) -> ValidationReport:
        """Generate comprehensive validation report"""

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        passed_checks = sum(1 for r in results if r.passed)
        failed_checks = len(results) - passed_checks

        # Count warnings and errors by severity
        warnings = sum(1 for r in results if not r.passed and r.level in [ValidationLevel.MINIMAL, ValidationLevel.STANDARD])
        errors = sum(1 for r in results if not r.passed and r.level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE])

        # Determine overall status
        if failed_checks == 0:
            overall_status = 'PASSED'
        elif errors > 0:
            overall_status = 'FAILED'
        else:
            overall_status = 'PASSED_WITH_WARNINGS'

        # Generate recommendations
        recommendations = []
        for result in results:
            if not result.passed and result.suggestions:
                recommendations.extend(result.suggestions)

        # Remove duplicates
        recommendations = list(set(recommendations))

        # Calculate metrics
        metrics = {
            'total_execution_time': total_time,
            'avg_check_time': total_time / len(results) if results else 0,
            'success_rate': passed_checks / len(results) if results else 0,
            'failure_rate': failed_checks / len(results) if results else 0,
            'categories_checked': list(set(r.category.name for r in results)),
            'validation_level': self.validation_level.name
        }

        report = ValidationReport(
            timestamp=end_time,
            validation_level=self.validation_level,
            total_checks=len(results),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            errors=errors,
            overall_status=overall_status,
            results=results,
            metrics=metrics,
            recommendations=recommendations
        )

        # Update global metrics
        self.metrics['total_validations'] += 1
        self.metrics['validation_time'] += total_time

        # Track common failures
        for result in results:
            if not result.passed:
                rule_name = result.rule_name
                if rule_name not in self.metrics['common_failures']:
                    self.metrics['common_failures'][rule_name] = 0
                self.metrics['common_failures'][rule_name] += 1

        # Update success rate
        if self.metrics['total_validations'] > 0:
            total_passed = sum(len([r for r in report.results if r.passed]) for report in self.validation_history)
            total_checks = sum(len(report.results) for report in self.validation_history)
            if total_checks > 0:
                self.metrics['success_rate'] = total_passed / total_checks

        # Store report in history
        self.validation_history.append(report)

        # Keep only last 50 reports to prevent memory issues
        if len(self.validation_history) > 50:
            self.validation_history = self.validation_history[-50:]

        return report

    def export_validation_report(self, report: ValidationReport, filename: str = None) -> str:  # type: ignore
        """Export validation report to JSON file"""

        if filename is None:
            timestamp = report.timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"validation_report_{timestamp}.json"

        # Convert report to dictionary for JSON serialization
        report_dict = {
            'metadata': {
                'timestamp': report.timestamp.isoformat(),
                'validation_level': report.validation_level.name,
                'overall_status': report.overall_status
            },
            'summary': {
                'total_checks': report.total_checks,
                'passed_checks': report.passed_checks,
                'failed_checks': report.failed_checks,
                'warnings': report.warnings,
                'errors': report.errors
            },
            'metrics': report.metrics,
            'recommendations': report.recommendations,
            'results': [
                {
                    'rule_name': r.rule_name,
                    'category': r.category.name,
                    'passed': r.passed,
                    'level': r.level.name,
                    'message': r.message,
                    'details': r.details,
                    'execution_time': r.execution_time,
                    'suggestions': r.suggestions
                }
                for r in report.results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)  # type: ignore

        return filename


# Convenience functions for standalone usage

def validate_prompt(prompt_file: str, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
    """Convenience function to validate a prompt file"""
    validator = WorkflowValidator(level)
    return validator.validate_prompt_file(prompt_file)


def validate_workflow(prompt_file: str, workflow_state, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
    """Convenience function to validate complete workflow"""
    validator = WorkflowValidator(level)
    return validator.validate_end_to_end(prompt_file, workflow_state)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python workflow_validator.py <prompt_file> [validation_level]")
        print("  validation_level: minimal, standard, strict, comprehensive (default: standard)")
        sys.exit(1)

    prompt_file = sys.argv[1]
    level_name = sys.argv[2].upper() if len(sys.argv) > 2 else 'STANDARD'

    try:
        validation_level = ValidationLevel[level_name]
    except KeyError:
        print(f"Error: Invalid validation level '{level_name}'. Use: minimal, standard, strict, comprehensive")
        sys.exit(1)

    # Run validation
    report = validate_prompt(prompt_file, validation_level)

    # Print results
    print(f"\n🔍 Validation Report - {report.overall_status}")
    print(f"📊 Checks: {report.passed_checks}/{report.total_checks} passed")

    if report.failed_checks > 0:
        print(f"⚠️  Warnings: {report.warnings}")
        print(f"❌ Errors: {report.errors}")

        print(f"\n📋 Failed Checks:")
        for result in report.results:
            if not result.passed:
                print(f"  • {result.rule_name}: {result.message}")
                if result.suggestions:
                    for suggestion in result.suggestions:
                        print(f"    → {suggestion}")

    if report.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    # Export detailed report
    validator = WorkflowValidator(validation_level)
    report_file = validator.export_validation_report(report)  # type: ignore
    print(f"\n📄 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if report.overall_status == 'PASSED' else 1)
