#!/usr/bin/env python3
"""
Workflow Enforcement Checker
Validates that all code changes follow the proper orchestrator and WorkflowManager process.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkflowChecker:
    """Validates workflow compliance for code changes."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.claude_dir = self.repo_root / ".claude"
        self.workflow_state_file = self.claude_dir / "workflow-enforcement" / "compliance_log.json"

        # Initialize compliance log
        self._ensure_compliance_log()

    def _ensure_compliance_log(self):
        """Ensure the compliance log file exists."""
        self.workflow_state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.workflow_state_file.exists():
            self.workflow_state_file.write_text(json.dumps({
                "violations": [],
                "compliant_executions": [],
                "last_check": None
            }, indent=2))

    def validate_execution_method(
        self,
        task_description: str,
        files_to_modify: List[str],
        execution_context: str = "direct"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates that the correct execution method is being used.

        Args:
            task_description: Description of the task being executed
            files_to_modify: List of files that will be modified
            execution_context: 'orchestrator', 'direct', or 'unknown'

        Returns:
            (is_valid, error_message, suggested_method)
        """
        logger.info(f"Validating execution method for task: {task_description}")

        # Determine if this is a code change
        is_code_change = self._is_code_change(task_description, files_to_modify)

        if is_code_change and execution_context != "orchestrator":
            error_msg = (
                f"❌ WORKFLOW VIOLATION: Code changes must use orchestrator.\n"
                f"Task: {task_description}\n"
                f"Files to modify: {', '.join(files_to_modify) if files_to_modify else 'None detected'}\n"
                f"Current method: {execution_context}\n"
                f"Required method: orchestrator"
            )

            # Log the violation
            self._log_violation(task_description, files_to_modify, execution_context)

            return False, error_msg, "OrchestratorAgent"

        # Log compliant execution
        if is_code_change and execution_context == "orchestrator":
            self._log_compliant_execution(task_description, files_to_modify, execution_context)

        return True, None, None

    def _is_code_change(self, task_description: str, files_to_modify: List[str]) -> bool:
        """Determine if a task constitutes a code change."""

        # Check file modifications
        if files_to_modify:
            code_extensions = {'.py', '.js', '.ts', '.go', '.java', '.cpp', '.c', '.h',
                             '.yml', '.yaml', '.json', '.md', '.txt', '.sh', '.bash'}

            for file_path in files_to_modify:
                if any(file_path.endswith(ext) for ext in code_extensions):
                    return True

        # Check task description for code change indicators
        code_change_indicators = [
            'fix', 'implement', 'create', 'add', 'update', 'modify', 'refactor',
            'delete', 'remove', 'change', 'edit', 'write', 'develop', 'build',
            'install', 'configure', 'setup', 'deploy', 'merge', 'commit'
        ]

        task_lower = task_description.lower()
        for indicator in code_change_indicators:
            if indicator in task_lower:
                return True

        return False

    def _log_violation(self, task: str, files: List[str], method: str):
        """Log a workflow violation."""
        try:
            with open(self.workflow_state_file, 'r') as f:
                data = json.load(f)

            violation = {
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "files": files,
                "method_used": method,
                "severity": "high"
            }

            data["violations"].append(violation)
            data["last_check"] = datetime.now().isoformat()

            with open(self.workflow_state_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log violation: {e}")

    def _log_compliant_execution(self, task: str, files: List[str], method: str):
        """Log a compliant execution."""
        try:
            with open(self.workflow_state_file, 'r') as f:
                data = json.load(f)

            execution = {
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "files": files,
                "method_used": method
            }

            data["compliant_executions"].append(execution)
            data["last_check"] = datetime.now().isoformat()

            with open(self.workflow_state_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log compliant execution: {e}")

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate a workflow compliance report."""
        try:
            with open(self.workflow_state_file, 'r') as f:
                data = json.load(f)

            violations = data.get("violations", [])
            compliant = data.get("compliant_executions", [])

            report = {
                "total_violations": len(violations),
                "total_compliant": len(compliant),
                "compliance_rate": len(compliant) / (len(compliant) + len(violations)) if (len(compliant) + len(violations)) > 0 else 1.0,
                "recent_violations": violations[-5:] if violations else [],
                "recent_compliant": compliant[-5:] if compliant else [],
                "report_generated": datetime.now().isoformat()
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {"error": str(e)}

    def check_workflow_phases(self) -> Dict[str, Any]:
        """Check if all 11 workflow phases are properly implemented."""
        required_phases = [
            "task_validation",
            "environment_setup",
            "dependency_analysis",
            "worktree_creation",
            "implementation",
            "testing",
            "quality_gates",
            "documentation",
            "review",
            "integration",
            "cleanup"
        ]

        # Check orchestrator implementation
        orchestrator_dir = self.claude_dir / "orchestrator"

        phase_status = {}
        for phase in required_phases:
            phase_file = orchestrator_dir / f"{phase}.py"
            phase_status[phase] = {
                "implemented": phase_file.exists(),
                "path": str(phase_file)
            }

        return {
            "phases": phase_status,
            "total_phases": len(required_phases),
            "implemented_phases": sum(1 for p in phase_status.values() if p["implemented"]),
            "compliance": sum(1 for p in phase_status.values() if p["implemented"]) / len(required_phases)
        }

def main():
    """Main function for command line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Check workflow compliance")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--files", nargs="*", help="Files to be modified")
    parser.add_argument("--method", default="direct", help="Execution method")
    parser.add_argument("--report", action="store_true", help="Generate compliance report")
    parser.add_argument("--phases", action="store_true", help="Check workflow phases")

    args = parser.parse_args()

    checker = WorkflowChecker()

    if args.report:
        report = checker.generate_compliance_report()
        print(json.dumps(report, indent=2))
    elif args.phases:
        phases = checker.check_workflow_phases()
        print(json.dumps(phases, indent=2))
    elif args.task:
        is_valid, error, suggestion = checker.validate_execution_method(
            args.task, args.files or [], args.method
        )

        if not is_valid:
            print(error, file=sys.stderr)
            if suggestion:
                print(f"\n✅ Correct approach: Use {suggestion}", file=sys.stderr)
            sys.exit(1)
        else:
            print("✅ Workflow compliance validated")

if __name__ == "__main__":
    main()
