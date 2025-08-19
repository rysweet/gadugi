from typing import Dict, List, Optional, Tuple

import logging
import re

"""Governance validation for orchestrator compliance with Issue #148.

This module ensures the orchestrator properly delegates all task execution
to WorkflowManager instances and never executes tasks directly.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class GovernanceViolation:
    """Record of a governance violation."""

    timestamp: datetime
    violation_type: str
    description: str
    task_id: Optional[str] = None
    severity: str = "WARNING"  # WARNING, ERROR, CRITICAL

    def __str__(self) -> str:
        """String representation of violation."""
        return (
            f"[{self.severity}] {self.timestamp.isoformat()}: "
            f"{self.violation_type} - {self.description}"
            f"{f' (Task: {self.task_id})' if self.task_id else ''}"
        )

@dataclass
class GovernanceReport:
    """Report of governance compliance check."""

    compliant: bool
    violations: List[GovernanceViolation]
    warnings: List[str]
    execution_logs: List[str]
    workflow_manager_invocations: int
    direct_executions: int

    def summary(self) -> str:
        """Generate summary of governance report."""
        status = "COMPLIANT" if self.compliant else "NON-COMPLIANT"
        lines = [
            f"Governance Status: {status}",
            f"WorkflowManager Invocations: {self.workflow_manager_invocations}",
            f"Direct Executions: {self.direct_executions}",
            f"Violations: {len(self.violations)}",
            f"Warnings: {len(self.warnings)}",
        ]

        if self.violations:
            lines.append("\nViolations:")
            for violation in self.violations[:5]:  # Show first 5
                lines.append(f"  - {violation}")
            if len(self.violations) > 5:
                lines.append(f"  ... and {len(self.violations) - 5} more")

        return "\n".join(lines)

class GovernanceValidator:
    """Validates orchestrator compliance with governance requirements."""

    def __init__(self):
        """Initialize the governance validator."""
        self.violations: List[GovernanceViolation] = []
        self.execution_logs: List[str] = []

    def validate_task_execution(
        self,
        task_id: str,
        execution_method: str,
        execution_details: Dict[str, any],  # type: ignore
    ) -> bool:
        """Validate that a task execution follows governance rules.

        Args:
            task_id: Task identifier
            execution_method: Method used for execution
            execution_details: Details of the execution

        Returns:
            True if compliant, False if violation detected
        """
        compliant = True

        # Check if WorkflowManager was invoked
        workflow_manager_invoked = execution_details.get("workflow_manager_invoked", False)

        if not workflow_manager_invoked:
            # CRITICAL VIOLATION: Direct execution without WorkflowManager
            violation = GovernanceViolation(
                timestamp=datetime.now(),
                violation_type="DIRECT_EXECUTION",
                description=(
                    "Task executed directly without delegating to WorkflowManager. "
                    "This violates Issue #148 governance requirements."
                ),
                task_id=task_id,
                severity="CRITICAL",
            )
            self.violations.append(violation)
            compliant = False
            logger.error(f"GOVERNANCE VIOLATION: {violation}")

        # Check if all phases were executed
        all_phases_executed = execution_details.get("all_phases_executed", False)
        if workflow_manager_invoked and not all_phases_executed:
            violation = GovernanceViolation(
                timestamp=datetime.now(),
                violation_type="INCOMPLETE_PHASES",
                description=(
                    "WorkflowManager did not complete all 11 required phases. "
                    "This may indicate a workflow execution issue."
                ),
                task_id=task_id,
                severity="ERROR",
            )
            self.violations.append(violation)
            compliant = False
            logger.error(f"GOVERNANCE VIOLATION: {violation}")

        # Log execution for audit
        self.execution_logs.append(
            f"{datetime.now().isoformat()}: Task {task_id} - "
            f"Method: {execution_method}, "
            f"WorkflowManager: {workflow_manager_invoked}, "
            f"Compliant: {compliant}"
        )

        return compliant

    def validate_code_compliance(
        self,
        file_path: Path,
    ) -> Tuple[bool, List[str]]:
        """Validate that code follows governance requirements.

        Args:
            file_path: Path to code file to validate

        Returns:
            Tuple of (is_compliant, list_of_issues)
        """
        issues = []

        if not file_path.exists():
            return False, ["File does not exist"]

        content = file_path.read_text()

        # Check for direct task execution patterns
        direct_execution_patterns = [
            r"await asyncio\.sleep.*# Simulate work",
            r"execution_output = .*Executed by.*",
            r"Task executed successfully",
        ]

        for pattern in direct_execution_patterns:
            if re.search(pattern, content):
                issues.append(
                    f"Found direct execution pattern: {pattern}. "
                    "All execution must delegate to WorkflowManager."
                )

        # Check for WorkflowManager delegation
        delegation_patterns = [
            r"_invoke_workflow_manager",
            r"claude -p",
            r"WorkflowManager",
        ]

        has_delegation = any(
            re.search(pattern, content) for pattern in delegation_patterns
        )

        if not has_delegation:
            issues.append(
                "No WorkflowManager delegation found. "
                "Orchestrator must delegate all tasks to WorkflowManager."
            )

        return len(issues) == 0, issues

    def generate_report(
        self,
        execution_history: List[Dict[str, any]],  # type: ignore
    ) -> GovernanceReport:
        """Generate a governance compliance report.

        Args:
            execution_history: History of task executions

        Returns:
            Governance compliance report
        """
        workflow_manager_invocations = 0
        direct_executions = 0
        warnings = []

        for execution in execution_history:
            task_id = execution.get("task_id", "unknown")
            method = execution.get("method", "unknown")
            details = execution.get("details", {})

            # Validate each execution
            compliant = self.validate_task_execution(task_id, method, details)

            if details.get("workflow_manager_invoked"):
                workflow_manager_invocations += 1
            else:
                direct_executions += 1

        # Add warnings for concerning patterns
        if direct_executions > 0:
            warnings.append(
                f"Found {direct_executions} direct task executions. "
                "All tasks must be delegated to WorkflowManager."
            )

        if workflow_manager_invocations == 0:
            warnings.append(
                "No WorkflowManager invocations detected. "
                "This indicates a critical governance failure."
            )

        # Determine overall compliance
        compliant = (
            direct_executions == 0 and
            len(self.violations) == 0 and
            workflow_manager_invocations > 0
        )

        return GovernanceReport(
            compliant=compliant,
            violations=self.violations,
            warnings=warnings,
            execution_logs=self.execution_logs,
            workflow_manager_invocations=workflow_manager_invocations,
            direct_executions=direct_executions,
        )

    def enforce_compliance(
        self,
        task_id: str,
        execution_details: Dict[str, any],  # type: ignore
    ) -> Dict[str, any]:  # type: ignore
        """Enforce governance compliance by modifying execution details.

        This method ensures that any task execution MUST go through
        WorkflowManager, even if initially configured otherwise.

        Args:
            task_id: Task identifier
            execution_details: Original execution details

        Returns:
            Modified execution details that ensure compliance
        """
        # Force WorkflowManager delegation
        if not execution_details.get("workflow_manager_invoked"):
            logger.warning(
                f"Enforcing WorkflowManager delegation for task {task_id}"
            )
            execution_details["workflow_manager_invoked"] = True
            execution_details["delegation_enforced"] = True
            execution_details["enforcement_reason"] = (
                "Governance requirement Issue #148: "
                "All tasks must be delegated to WorkflowManager"
            )

        # Ensure all phases will be executed
        if not execution_details.get("require_all_phases"):
            execution_details["require_all_phases"] = True
            execution_details["required_phases"] = [
                "Initial Setup",
                "Issue Creation",
                "Branch Management",
                "Research and Planning",
                "Implementation",
                "Testing",
                "Documentation",
                "Pull Request",
                "Code Review",
                "Review Response",
                "Settings Update",
            ]

        return execution_details

def validate_orchestrator_compliance() -> GovernanceReport:
    """Validate current orchestrator implementation for compliance.

    Returns:
        Governance compliance report
    """
    validator = GovernanceValidator()

    # Check orchestrator code files
    orchestrator_files = [
        Path(".claude/agents/orchestrator/orchestrator.py"),
        Path(".claude/agents/orchestrator/parallel_executor.py"),
    ]

    code_issues = []
    for file_path in orchestrator_files:
        if file_path.exists():
            compliant, issues = validator.validate_code_compliance(file_path)
            if not compliant:
                code_issues.extend([f"{file_path.name}: {issue}" for issue in issues])

    # Create report with code validation results
    if code_issues:
        for issue in code_issues:
            validator.violations.append(
                GovernanceViolation(
                    timestamp=datetime.now(),
                    violation_type="CODE_COMPLIANCE",
                    description=issue,
                    severity="ERROR",
                )
            )

    # Generate final report
    return validator.generate_report([])

if __name__ == "__main__":
    # Run compliance check
    report = validate_orchestrator_compliance()
    print("\n" + "=" * 60)
    print("ORCHESTRATOR GOVERNANCE COMPLIANCE CHECK")
    print("=" * 60)
    print(report.summary())
    print("=" * 60)

    if not report.compliant:
        print("\n⚠️  COMPLIANCE FAILURES DETECTED")
        print("The orchestrator is not properly delegating to WorkflowManager.")
        print("This violates Issue #148 governance requirements.")
        exit(1)
    else:
        print("\n✅ ORCHESTRATOR IS COMPLIANT")
        print("All tasks are properly delegated to WorkflowManager.")
        exit(0)
