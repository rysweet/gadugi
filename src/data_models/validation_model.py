"""Structured validation results with categorized issues and recommendations.

This module provides comprehensive validation models for tracking and reporting
validation issues, rules, and results across the Recipe Executor system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationCategory(str, Enum):
    """Categories for organizing validation issues."""

    SYNTAX = "SYNTAX"
    SEMANTIC = "SEMANTIC"
    STRUCTURE = "STRUCTURE"
    CONSISTENCY = "CONSISTENCY"
    COMPLETENESS = "COMPLETENESS"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    STYLE = "STYLE"
    DEPENDENCY = "DEPENDENCY"
    CONFIGURATION = "CONFIGURATION"


class ValidationIssue(BaseModel):
    """Base class for validation issues."""

    severity: ValidationSeverity = Field(..., description="Issue severity level")
    category: ValidationCategory = Field(..., description="Issue category")
    message: str = Field(..., description="Issue message")
    location: Optional[str] = Field(None, description="Location of the issue (file:line)")
    component: Optional[str] = Field(None, description="Component where issue was found")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")
    rule_id: Optional[str] = Field(
        None, description="ID of the validation rule that triggered this issue"
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    timestamp: datetime = Field(default_factory=datetime.now, description="When issue was detected")

    def to_formatted_string(self) -> str:
        """Generate a formatted string representation.

        Returns:
            Formatted issue string
        """
        parts = [f"[{self.severity.value}]"]
        if self.location:
            parts.append(f"{self.location}:")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"\n  Suggestion: {self.suggestion}")
        return " ".join(parts)

    def __str__(self) -> str:
        """Return a string representation of the issue."""
        location_str = f" at {self.location}" if self.location else ""
        return f"[{self.severity.value}] {self.message}{location_str}"

    def __repr__(self) -> str:
        """Return a detailed representation of the issue."""
        return f"ValidationIssue(severity={self.severity}, category={self.category}, message='{self.message[:50]}...')"


class ValidationError(ValidationIssue):
    """Errors that must be fixed."""

    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity level (always ERROR or CRITICAL for ValidationError)",
    )
    must_fix: bool = Field(True, description="Whether this error blocks execution")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: ValidationSeverity) -> ValidationSeverity:
        """Ensure severity is ERROR or CRITICAL.

        Args:
            v: Severity value

        Returns:
            Validated severity

        Raises:
            ValueError: If severity is not ERROR or CRITICAL
        """
        if v not in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            raise ValueError("ValidationError severity must be ERROR or CRITICAL")
        return v


class ValidationWarning(ValidationIssue):
    """Issues that should be reviewed."""

    severity: ValidationSeverity = Field(
        default=ValidationSeverity.WARNING, description="Severity level (always WARNING)"
    )
    can_ignore: bool = Field(True, description="Whether this warning can be ignored")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: ValidationSeverity) -> ValidationSeverity:
        """Ensure severity is WARNING.

        Args:
            v: Severity value

        Returns:
            Validated severity

        Raises:
            ValueError: If severity is not WARNING
        """
        if v != ValidationSeverity.WARNING:
            raise ValueError("ValidationWarning severity must be WARNING")
        return v


class ValidationInfo(ValidationIssue):
    """Informational messages."""

    severity: ValidationSeverity = Field(
        default=ValidationSeverity.INFO, description="Severity level (always INFO)"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: ValidationSeverity) -> ValidationSeverity:
        """Ensure severity is INFO.

        Args:
            v: Severity value

        Returns:
            Validated severity

        Raises:
            ValueError: If severity is not INFO
        """
        if v != ValidationSeverity.INFO:
            raise ValueError("ValidationInfo severity must be INFO")
        return v


class ValidationRule(BaseModel):
    """Rule specification for validation."""

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="What the rule validates")
    category: ValidationCategory = Field(..., description="Rule category")
    severity: ValidationSeverity = Field(..., description="Default severity for violations")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    applies_to: List[str] = Field(
        default_factory=list, description="Components/files this rule applies to"
    )

    def matches(self, component: str) -> bool:
        """Check if rule applies to a component.

        Args:
            component: Component name to check

        Returns:
            True if rule applies to the component
        """
        if not self.applies_to:
            return True  # Applies to all if not specified
        return component in self.applies_to

    def __str__(self) -> str:
        """Return a string representation of the rule."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({self.category.value}, {status})"

    def __repr__(self) -> str:
        """Return a detailed representation of the rule."""
        return f"ValidationRule(id='{self.id}', name='{self.name}', category={self.category})"


class ValidationResult(BaseModel):
    """Complete validation result with errors, warnings, and info."""

    validator_name: str = Field(..., description="Name of the validator that produced this result")
    target: str = Field(..., description="What was validated (e.g., recipe name, file path)")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationWarning] = Field(
        default_factory=list, description="Validation warnings"
    )
    info: List[ValidationInfo] = Field(default_factory=list, description="Informational messages")
    rules_applied: List[str] = Field(
        default_factory=list, description="IDs of rules that were applied"
    )
    validation_time: datetime = Field(
        default_factory=datetime.now, description="When validation occurred"
    )
    duration_ms: Optional[int] = Field(None, description="Validation duration in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Returns:
            True if no errors, False otherwise
        """
        return len(self.errors) == 0

    def has_critical_errors(self) -> bool:
        """Check for blocking errors.

        Returns:
            True if critical errors exist
        """
        return any(error.severity == ValidationSeverity.CRITICAL for error in self.errors)

    def get_all_issues(self) -> List[ValidationIssue]:
        """Get all issues (errors, warnings, info) combined.

        Returns:
            List of all validation issues
        """
        all_issues: List[ValidationIssue] = []
        all_issues.extend(self.errors)
        all_issues.extend(self.warnings)
        all_issues.extend(self.info)
        return all_issues

    def get_errors_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Group issues by severity level.

        Args:
            severity: Severity level to filter by

        Returns:
            List of issues with specified severity
        """
        return [issue for issue in self.get_all_issues() if issue.severity == severity]

    def get_errors_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Group issues by category.

        Args:
            category: Category to filter by

        Returns:
            List of issues in specified category
        """
        return [issue for issue in self.get_all_issues() if issue.category == category]

    def add_error(self, message: str, category: ValidationCategory, **kwargs: Any) -> None:
        """Add a validation error.

        Args:
            message: Error message
            category: Error category
            **kwargs: Additional fields for ValidationError
        """
        error = ValidationError(message=message, category=category, **kwargs)
        self.errors.append(error)

    def add_warning(self, message: str, category: ValidationCategory, **kwargs: Any) -> None:
        """Add a validation warning.

        Args:
            message: Warning message
            category: Warning category
            **kwargs: Additional fields for ValidationWarning
        """
        warning = ValidationWarning(message=message, category=category, **kwargs)
        self.warnings.append(warning)

    def add_info(self, message: str, category: ValidationCategory, **kwargs: Any) -> None:
        """Add an informational message.

        Args:
            message: Info message
            category: Info category
            **kwargs: Additional fields for ValidationInfo
        """
        info = ValidationInfo(message=message, category=category, **kwargs)
        self.info.append(info)

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of validation results.

        Returns:
            Dictionary with summary statistics
        """
        return {
            "valid": self.is_valid(),
            "total_issues": len(self.get_all_issues()),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "critical_errors": sum(
                1 for e in self.errors if e.severity == ValidationSeverity.CRITICAL
            ),
            "categories": list(set(issue.category.value for issue in self.get_all_issues())),
            "rules_applied": len(self.rules_applied),
        }

    def __str__(self) -> str:
        """Return a string representation of the validation result."""
        status = "✓ Valid" if self.is_valid() else "✗ Invalid"
        return f"{status} - {self.target}: {len(self.errors)} errors, {len(self.warnings)} warnings"

    def __repr__(self) -> str:
        """Return a detailed representation of the validation result."""
        return f"ValidationResult(target='{self.target}', errors={len(self.errors)}, warnings={len(self.warnings)})"


class ValidationContext(BaseModel):
    """Context for validation operations."""

    recipe_name: str = Field(..., description="Name of the recipe being validated")
    validation_phase: str = Field(..., description="Current validation phase")
    strict_mode: bool = Field(False, description="Whether to use strict validation")
    skip_rules: List[str] = Field(default_factory=list, description="Rule IDs to skip")
    custom_rules: List[ValidationRule] = Field(
        default_factory=list, description="Custom validation rules"
    )
    config: Dict[str, Any] = Field(default_factory=dict, description="Validation configuration")

    def should_apply_rule(self, rule: ValidationRule) -> bool:
        """Check if a rule should be applied in this context.

        Args:
            rule: The validation rule

        Returns:
            True if rule should be applied
        """
        if rule.id in self.skip_rules:
            return False
        if not rule.enabled:
            return False
        return True

    def __str__(self) -> str:
        """Return a string representation of the validation context."""
        mode = "strict" if self.strict_mode else "normal"
        return f"ValidationContext({self.recipe_name}, phase={self.validation_phase}, mode={mode})"

    def __repr__(self) -> str:
        """Return a detailed representation of the validation context."""
        return f"ValidationContext(recipe='{self.recipe_name}', phase='{self.validation_phase}')"


class ValidationReport(BaseModel):
    """Comprehensive validation report with recommendations."""

    id: str = Field(..., description="Unique report identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Report generation time")
    results: List[ValidationResult] = Field(
        default_factory=list, description="All validation results"
    )
    overall_valid: bool = Field(True, description="Overall validation status")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    execution_time_ms: Optional[int] = Field(
        None, description="Total validation time in milliseconds"
    )

    def aggregate_results(self, results: List[ValidationResult]) -> None:
        """Combine multiple validation results.

        Args:
            results: List of validation results to aggregate
        """
        self.results = results
        self.overall_valid = all(result.is_valid() for result in results)
        self.generate_summary()
        self.generate_recommendations()

    def generate_summary(self) -> None:
        """Create statistics summary."""
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)
        total_info = sum(len(r.info) for r in self.results)

        # Collect all unique categories
        all_categories = set()
        for result in self.results:
            for issue in result.get_all_issues():
                all_categories.add(issue.category.value)

        # Count critical errors
        critical_count = sum(
            sum(1 for e in r.errors if e.severity == ValidationSeverity.CRITICAL)
            for r in self.results
        )

        self.summary_stats = {
            "total_validators": len(self.results),
            "passed_validators": sum(1 for r in self.results if r.is_valid()),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "critical_errors": critical_count,
            "categories_affected": list(all_categories),
            "overall_valid": self.overall_valid,
        }

    def generate_recommendations(self) -> None:
        """Generate recommended actions based on validation results."""
        self.recommendations = []

        # Check for critical errors
        critical_count = self.summary_stats.get("critical_errors", 0)
        if critical_count > 0:
            self.recommendations.append(
                f"URGENT: Fix {critical_count} critical error(s) before proceeding"
            )

        # Check for high error count
        total_errors = self.summary_stats.get("total_errors", 0)
        if total_errors > 10:
            self.recommendations.append(
                "Consider reviewing the recipe structure - high number of validation errors detected"
            )

        # Check for specific category issues
        for result in self.results:
            security_issues = result.get_errors_by_category(ValidationCategory.SECURITY)
            if security_issues:
                self.recommendations.append(
                    f"Security review needed: {len(security_issues)} security issue(s) found"
                )

            dependency_issues = result.get_errors_by_category(ValidationCategory.DEPENDENCY)
            if dependency_issues:
                self.recommendations.append(
                    f"Dependency resolution required: {len(dependency_issues)} dependency issue(s)"
                )

        # Check for consistency issues
        consistency_issues = sum(
            len(r.get_errors_by_category(ValidationCategory.CONSISTENCY)) for r in self.results
        )
        if consistency_issues > 0:
            self.recommendations.append("Review component interfaces for consistency")

        # Add general recommendation if valid
        if self.overall_valid and not self.recommendations:
            self.recommendations.append("Recipe validation passed - ready for generation")

    def to_markdown(self) -> str:
        """Generate a markdown formatted report.

        Returns:
            Markdown string of the report
        """
        lines = [
            "# Validation Report",
            f"**Report ID:** {self.id}",
            f"**Generated:** {self.timestamp.isoformat()}",
            "",
            "## Summary",
            f"**Overall Status:** {'✓ VALID' if self.overall_valid else '✗ INVALID'}",
            "",
            "### Statistics",
            f"- Validators Run: {self.summary_stats.get('total_validators', 0)}",
            f"- Validators Passed: {self.summary_stats.get('passed_validators', 0)}",
            f"- Total Errors: {self.summary_stats.get('total_errors', 0)}",
            f"- Critical Errors: {self.summary_stats.get('critical_errors', 0)}",
            f"- Total Warnings: {self.summary_stats.get('total_warnings', 0)}",
            "",
        ]

        if self.recommendations:
            lines.extend(["## Recommendations", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # Detail section for errors
        if any(r.errors for r in self.results):
            lines.extend(["## Validation Errors", ""])
            for result in self.results:
                if result.errors:
                    lines.append(f"### {result.target}")
                    for error in result.errors:
                        lines.append(f"- [{error.severity.value}] {error.message}")
                        if error.suggestion:
                            lines.append(f"  - Suggestion: {error.suggestion}")
            lines.append("")

        # Detail section for warnings
        if any(r.warnings for r in self.results):
            lines.extend(["## Validation Warnings", ""])
            for result in self.results:
                if result.warnings:
                    lines.append(f"### {result.target}")
                    for warning in result.warnings:
                        lines.append(f"- {warning.message}")
                        if warning.suggestion:
                            lines.append(f"  - Suggestion: {warning.suggestion}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return a string representation of the validation report."""
        status = "VALID" if self.overall_valid else "INVALID"
        stats = self.summary_stats
        return f"ValidationReport({status}): {stats.get('total_errors', 0)} errors, {stats.get('total_warnings', 0)} warnings"

    def __repr__(self) -> str:
        """Return a detailed representation of the validation report."""
        return f"ValidationReport(id='{self.id}', valid={self.overall_valid}, results={len(self.results)})"
