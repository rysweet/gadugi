"""State tracking for recipe execution, generation results, and test outcomes.

This module provides models for tracking the execution lifecycle of recipe builds,
including phase transitions, error handling, and result reporting.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ExecutionPhase(str, Enum):
    """Phases of recipe execution."""

    INITIALIZING = "INITIALIZING"
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    GENERATING = "GENERATING"
    TESTING = "TESTING"
    BUILDING = "BUILDING"
    DEPLOYING = "DEPLOYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ErrorSeverity(str, Enum):
    """Severity levels for execution errors."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExecutionError(BaseModel):
    """Error that occurred during execution."""

    phase: ExecutionPhase = Field(..., description="Phase where error occurred")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="When error occurred")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    recoverable: bool = Field(True, description="Whether execution can continue")

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return f"[{self.severity.value}] {self.phase.value}: {self.message}"

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        return f"ExecutionError(phase={self.phase}, severity={self.severity}, message='{self.message[:50]}...')"


class ComponentStatus(BaseModel):
    """Track individual component build status."""

    name: str = Field(..., description="Component name")
    phase: ExecutionPhase = Field(ExecutionPhase.INITIALIZING, description="Current phase")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    success: bool = Field(False, description="Whether component build succeeded")
    output_files: List[str] = Field(default_factory=list, description="Generated output files")
    errors: List[ExecutionError] = Field(default_factory=list, description="Errors encountered")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Build metrics")

    def mark_started(self) -> None:
        """Mark component as started."""
        self.started_at = datetime.now()
        self.phase = ExecutionPhase.GENERATING

    def mark_completed(self, output_files: List[str]) -> None:
        """Update status with output files.

        Args:
            output_files: List of generated files
        """
        self.completed_at = datetime.now()
        self.output_files = output_files
        self.success = True
        self.phase = ExecutionPhase.COMPLETED

    def mark_failed(self, error: ExecutionError) -> None:
        """Mark component as failed.

        Args:
            error: The error that caused failure
        """
        self.completed_at = datetime.now()
        self.errors.append(error)
        self.success = False
        self.phase = ExecutionPhase.FAILED

    def get_duration(self) -> Optional[timedelta]:
        """Calculate build duration.

        Returns:
            Duration if both start and end times exist, None otherwise
        """
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def __str__(self) -> str:
        """Return a string representation of the component status."""
        status = "✓" if self.success else "✗" if self.phase == ExecutionPhase.FAILED else "..."
        return f"{status} {self.name} ({self.phase.value})"

    def __repr__(self) -> str:
        """Return a detailed representation of the component status."""
        return f"ComponentStatus(name='{self.name}', phase={self.phase}, success={self.success})"


class ExecutionState(BaseModel):
    """Complete execution state with phases and errors."""

    id: str = Field(..., description="Unique execution ID")
    recipe_name: str = Field(..., description="Name of recipe being executed")
    current_phase: ExecutionPhase = Field(ExecutionPhase.INITIALIZING, description="Current phase")
    phases_completed: List[ExecutionPhase] = Field(
        default_factory=list, description="Completed phases"
    )
    components: List[ComponentStatus] = Field(
        default_factory=list, description="Component statuses"
    )
    errors: List[ExecutionError] = Field(default_factory=list, description="All errors encountered")
    started_at: datetime = Field(default_factory=datetime.now, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )

    def update_phase(self, new_phase: ExecutionPhase) -> None:
        """Transition between execution phases.

        Args:
            new_phase: The new phase to transition to
        """
        if self.current_phase not in [
            ExecutionPhase.FAILED,
            ExecutionPhase.CANCELLED,
            ExecutionPhase.COMPLETED,
        ]:
            if self.current_phase not in self.phases_completed:
                self.phases_completed.append(self.current_phase)
            self.current_phase = new_phase

            if new_phase in [
                ExecutionPhase.COMPLETED,
                ExecutionPhase.FAILED,
                ExecutionPhase.CANCELLED,
            ]:
                self.completed_at = datetime.now()

    def get_progress(self) -> float:
        """Calculate percentage complete.

        Returns:
            Progress percentage (0.0 to 100.0)
        """
        total_phases = len(ExecutionPhase) - 3  # Exclude FAILED, CANCELLED, COMPLETED
        completed = len(self.phases_completed)

        if self.current_phase == ExecutionPhase.COMPLETED:
            return 100.0
        elif self.current_phase in [ExecutionPhase.FAILED, ExecutionPhase.CANCELLED]:
            # Return progress up to failure/cancellation
            return (completed / total_phases) * 100.0
        else:
            # Add 0.5 for current phase in progress
            return ((completed + 0.5) / total_phases) * 100.0

    def add_component(self, component_name: str) -> ComponentStatus:
        """Add a component to track.

        Args:
            component_name: Name of the component

        Returns:
            The created ComponentStatus
        """
        component = ComponentStatus(name=component_name)
        self.components.append(component)
        return component

    def get_component(self, name: str) -> Optional[ComponentStatus]:
        """Get component status by name.

        Args:
            name: Component name

        Returns:
            ComponentStatus if found, None otherwise
        """
        for component in self.components:
            if component.name == name:
                return component
        return None

    def add_error(self, error: ExecutionError) -> None:
        """Add an error to the execution state.

        Args:
            error: Error to add
        """
        self.errors.append(error)
        if error.severity == ErrorSeverity.CRITICAL or not error.recoverable:
            self.update_phase(ExecutionPhase.FAILED)

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ExecutionError]:
        """Get errors filtered by severity.

        Args:
            severity: Severity level to filter by

        Returns:
            List of errors with specified severity
        """
        return [error for error in self.errors if error.severity == severity]

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors.

        Returns:
            True if critical errors exist
        """
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    def is_complete(self) -> bool:
        """Check if execution is complete (success or failure).

        Returns:
            True if execution has finished
        """
        return self.current_phase in [
            ExecutionPhase.COMPLETED,
            ExecutionPhase.FAILED,
            ExecutionPhase.CANCELLED,
        ]

    def get_duration(self) -> Optional[timedelta]:
        """Calculate total execution duration.

        Returns:
            Duration if execution is complete, None otherwise
        """
        if self.completed_at:
            return self.completed_at - self.started_at
        return None

    def __str__(self) -> str:
        """Return a string representation of the execution state."""
        progress = self.get_progress()
        return f"ExecutionState({self.recipe_name}): {self.current_phase.value} ({progress:.1f}%)"

    def __repr__(self) -> str:
        """Return a detailed representation of the execution state."""
        return f"ExecutionState(id='{self.id}', recipe='{self.recipe_name}', phase={self.current_phase})"


class GenerationResult(BaseModel):
    """Result of code generation for a component."""

    component_name: str = Field(..., description="Name of the component")
    success: bool = Field(..., description="Whether generation succeeded")
    files_generated: List[str] = Field(default_factory=list, description="List of generated files")
    iterations: int = Field(1, description="Number of generation iterations")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Generation metrics")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated")
    generation_time: timedelta = Field(..., description="Time taken to generate")
    stub_count: int = Field(0, description="Number of stubs generated")
    implementation_count: int = Field(0, description="Number of implementations generated")

    def add_file(self, file_path: str) -> None:
        """Track generated files.

        Args:
            file_path: Path of generated file
        """
        if file_path not in self.files_generated:
            self.files_generated.append(file_path)

    def add_metric(self, key: str, value: Any) -> None:
        """Add a generation metric.

        Args:
            key: Metric name
            value: Metric value
        """
        self.metrics[key] = value

    def get_completion_rate(self) -> float:
        """Calculate implementation completion rate.

        Returns:
            Percentage of implementations vs stubs
        """
        total = self.stub_count + self.implementation_count
        if total == 0:
            return 0.0
        return (self.implementation_count / total) * 100.0

    def __str__(self) -> str:
        """Return a string representation of the generation result."""
        status = "✓" if self.success else "✗"
        return f"{status} {self.component_name}: {len(self.files_generated)} files generated"

    def __repr__(self) -> str:
        """Return a detailed representation of the generation result."""
        return f"GenerationResult(component='{self.component_name}', success={self.success}, files={len(self.files_generated)})"


class TestResult(BaseModel):
    """Test execution results with pass/fail counts."""

    component_name: str = Field(..., description="Component being tested")
    test_suite: str = Field(..., description="Test suite name")
    total_tests: int = Field(..., description="Total number of tests")
    passed: int = Field(0, description="Number of tests passed")
    failed: int = Field(0, description="Number of tests failed")
    skipped: int = Field(0, description="Number of tests skipped")
    errors: int = Field(0, description="Number of tests with errors")
    execution_time: timedelta = Field(..., description="Test execution time")
    coverage_percentage: Optional[float] = Field(None, description="Code coverage percentage")
    failure_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Details of failures"
    )
    output: str = Field("", description="Test output")

    def success_rate(self) -> float:
        """Calculate test pass percentage.

        Returns:
            Success rate as percentage
        """
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100.0

    def is_passing(self) -> bool:
        """Check if all tests passed.

        Returns:
            True if all tests passed (no failures or errors)
        """
        return self.failed == 0 and self.errors == 0

    def add_failure(self, test_name: str, error_message: str, stack_trace: str = "") -> None:
        """Add a test failure detail.

        Args:
            test_name: Name of the failed test
            error_message: Error message
            stack_trace: Optional stack trace
        """
        self.failure_details.append(
            {"test": test_name, "error": error_message, "stack_trace": stack_trace}
        )

    def __str__(self) -> str:
        """Return a string representation of the test result."""
        status = "✓" if self.is_passing() else "✗"
        return f"{status} {self.test_suite}: {self.passed}/{self.total_tests} passed ({self.success_rate():.1f}%)"

    def __repr__(self) -> str:
        """Return a detailed representation of the test result."""
        return f"TestResult(suite='{self.test_suite}', passed={self.passed}/{self.total_tests})"

    @field_validator("total_tests")
    @classmethod
    def validate_total_tests(cls, v: int, info) -> int:
        """Validate that total tests is non-negative.

        Args:
            v: Total tests value
            info: Validation context

        Returns:
            Validated value

        Raises:
            ValueError: If total_tests is negative
        """
        if v < 0:
            raise ValueError("Total tests cannot be negative")
        return v


class ExecutionReport(BaseModel):
    """Complete execution summary."""

    execution_id: str = Field(..., description="Unique execution ID")
    recipe_name: str = Field(..., description="Recipe that was executed")
    success: bool = Field(..., description="Overall success status")
    execution_state: ExecutionState = Field(..., description="Execution state details")
    generation_results: List[GenerationResult] = Field(
        default_factory=list, description="Generation results"
    )
    test_results: List[TestResult] = Field(default_factory=list, description="Test results")
    total_duration: timedelta = Field(..., description="Total execution time")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")

    def generate_summary(self) -> None:
        """Generate summary statistics."""
        self.summary = {
            "total_components": len(self.generation_results),
            "successful_generations": sum(1 for r in self.generation_results if r.success),
            "total_files_generated": sum(len(r.files_generated) for r in self.generation_results),
            "total_tests_run": sum(r.total_tests for r in self.test_results),
            "total_tests_passed": sum(r.passed for r in self.test_results),
            "overall_test_success_rate": self.calculate_overall_test_success_rate(),
            "average_coverage": self.calculate_average_coverage(),
            "critical_errors": len(
                self.execution_state.get_errors_by_severity(ErrorSeverity.CRITICAL)
            ),
            "warnings": len(self.execution_state.get_errors_by_severity(ErrorSeverity.WARNING)),
        }

    def calculate_overall_test_success_rate(self) -> float:
        """Calculate overall test success rate.

        Returns:
            Overall success rate as percentage
        """
        total_tests = sum(r.total_tests for r in self.test_results)
        if total_tests == 0:
            return 0.0
        total_passed = sum(r.passed for r in self.test_results)
        return (total_passed / total_tests) * 100.0

    def calculate_average_coverage(self) -> Optional[float]:
        """Calculate average code coverage.

        Returns:
            Average coverage percentage if available, None otherwise
        """
        coverage_values = [
            r.coverage_percentage for r in self.test_results if r.coverage_percentage is not None
        ]
        if not coverage_values:
            return None
        return sum(coverage_values) / len(coverage_values)

    def to_markdown(self) -> str:
        """Generate a markdown report.

        Returns:
            Markdown formatted report
        """
        self.generate_summary()
        lines = [
            f"# Execution Report: {self.recipe_name}",
            "",
            f"**Execution ID:** {self.execution_id}",
            f"**Status:** {'✓ Success' if self.success else '✗ Failed'}",
            f"**Duration:** {self.total_duration}",
            "",
            "## Summary",
            f"- Components Generated: {self.summary['successful_generations']}/{self.summary['total_components']}",
            f"- Files Created: {self.summary['total_files_generated']}",
            f"- Tests Passed: {self.summary['total_tests_passed']}/{self.summary['total_tests_run']} ({self.summary['overall_test_success_rate']:.1f}%)",
        ]

        if self.summary["average_coverage"] is not None:
            lines.append(f"- Average Coverage: {self.summary['average_coverage']:.1f}%")

        lines.extend(
            [
                "",
                "## Component Results",
            ]
        )

        for result in self.generation_results:
            status = "✓" if result.success else "✗"
            lines.append(
                f"- {status} **{result.component_name}**: {len(result.files_generated)} files"
            )

        if self.test_results:
            lines.extend(
                [
                    "",
                    "## Test Results",
                ]
            )
            for result in self.test_results:
                status = "✓" if result.is_passing() else "✗"
                lines.append(
                    f"- {status} **{result.test_suite}**: {result.passed}/{result.total_tests} passed"
                )

        if self.execution_state.errors:
            lines.extend(
                [
                    "",
                    "## Errors and Warnings",
                ]
            )
            for error in self.execution_state.errors:
                icon = "⚠️" if error.severity == ErrorSeverity.WARNING else "❌"
                lines.append(f"- {icon} [{error.severity.value}] {error.message}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return a string representation of the execution report."""
        status = "Success" if self.success else "Failed"
        return f"ExecutionReport({self.recipe_name}): {status} in {self.total_duration}"

    def __repr__(self) -> str:
        """Return a detailed representation of the execution report."""
        return f"ExecutionReport(id='{self.execution_id}', recipe='{self.recipe_name}', success={self.success})"
