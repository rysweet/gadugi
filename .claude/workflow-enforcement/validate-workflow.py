#!/usr/bin/env python3
"""
Workflow Validation Script
Quick validation tool for checking workflow compliance before execution.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(color: str, message: str):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.END}")

def print_header(title: str):
    """Print formatted header."""
    print_colored(Colors.CYAN, f"\n{'=' * 60}")
    print_colored(Colors.WHITE + Colors.BOLD, f"  {title}")
    print_colored(Colors.CYAN, f"{'=' * 60}")

def print_section(title: str):
    """Print section header."""
    print_colored(Colors.BLUE, f"\n📋 {title}")
    print_colored(Colors.BLUE, "-" * (len(title) + 3))

class WorkflowValidator:
    """Validates workflow requirements and provides guidance."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.claude_dir = self.repo_root / ".claude"
        self.enforcement_dir = self.claude_dir / "workflow-enforcement"

    def validate_task(
        self,
        task_description: str,
        files: List[str] = None,
        execution_method: str = "direct"
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a task against workflow requirements.

        Returns:
            (is_compliant, violations, recommendations)
        """
        violations = []
        recommendations = []
        files = files or []

        # Check if task requires orchestrator
        requires_orchestrator = self._requires_orchestrator(task_description, files)

        if requires_orchestrator and execution_method != "orchestrator":
            violations.append(
                f"❌ Code change detected but orchestrator not being used"
            )
            violations.append(
                f"   Task: {task_description}"
            )
            if files:
                violations.append(
                    f"   Files: {', '.join(files)}"
                )

            recommendations.extend([
                "🚀 Use orchestrator for this task:",
                f"   python .claude/orchestrator/main.py --task \"{task_description}\"",
                "",
                "📚 Review workflow requirements:",
                "   cat .claude/workflow-enforcement/workflow-reminder.md"
            ])

        # Check orchestrator availability
        if requires_orchestrator:
            orchestrator_issues = self._check_orchestrator_setup()
            if orchestrator_issues:
                violations.extend(orchestrator_issues)

        is_compliant = len(violations) == 0

        return is_compliant, violations, recommendations

    def _requires_orchestrator(self, task_description: str, files: List[str]) -> bool:
        """Determine if a task requires orchestrator workflow."""

        # Check files
        if files:
            code_extensions = {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.c', '.h',
                '.json', '.yaml', '.yml', '.md', '.txt', '.sh', '.bash', '.zsh',
                '.css', '.scss', '.html', '.xml', '.sql', '.r', '.rb', '.php'
            }

            for file_path in files:
                if any(file_path.endswith(ext) for ext in code_extensions):
                    return True
                # Also check for config files
                config_indicators = ['config', 'settings', 'setup', 'requirements', 'package']
                if any(indicator in file_path.lower() for indicator in config_indicators):
                    return True

        # Check task description
        code_change_indicators = [
            # Direct modification words
            'fix', 'implement', 'create', 'add', 'update', 'modify', 'refactor',
            'delete', 'remove', 'change', 'edit', 'write', 'develop', 'build',
            'install', 'configure', 'setup', 'deploy', 'merge', 'commit',

            # Technical operation words
            'debug', 'optimize', 'enhance', 'improve', 'migrate', 'upgrade',
            'patch', 'rename', 'move', 'copy', 'generate', 'compile',

            # Git operations
            'branch', 'pull', 'push', 'rebase', 'cherry-pick', 'revert',

            # Package management
            'pip install', 'npm install', 'yarn add', 'gem install',
            'apt-get', 'brew install', 'conda install'
        ]

        task_lower = task_description.lower()

        for indicator in code_change_indicators:
            if indicator in task_lower:
                return True

        # Check for file operation patterns
        file_operation_patterns = [
            'create file', 'delete file', 'modify file', 'edit file',
            'new file', 'add file', 'remove file', 'update file'
        ]

        for pattern in file_operation_patterns:
            if pattern in task_lower:
                return True

        return False

    def _check_orchestrator_setup(self) -> List[str]:
        """Check if orchestrator is properly set up."""
        issues = []

        # Check if orchestrator exists
        orchestrator_main = self.claude_dir / "orchestrator" / "main.py"
        if not orchestrator_main.exists():
            issues.append(
                "⚠️ Orchestrator main.py not found at .claude/orchestrator/main.py"
            )

        # Check if workflow manager exists
        workflow_master = self.claude_dir / "agents" / "WorkflowMaster.md"
        if not workflow_master.exists():
            issues.append(
                "⚠️ WorkflowMaster agent not found at .claude/agents/WorkflowMaster.md"
            )

        return issues

    def show_workflow_guide(self):
        """Display comprehensive workflow guidance."""
        print_header("GADUGI WORKFLOW ENFORCEMENT GUIDE")

        print_section("🚨 CRITICAL: When to Use Orchestrator")

        print_colored(Colors.GREEN, "✅ REQUIRES ORCHESTRATOR:")
        orchestrator_tasks = [
            "• Any file modifications (.py, .js, .json, .md, etc.)",
            "• Creating or deleting files/directories",
            "• Installing or updating dependencies",
            "• Configuration changes",
            "• Bug fixes and feature implementations",
            "• Code refactoring or optimization",
            "• Git operations (commits, branches, merges)",
            "• Documentation updates that modify files"
        ]
        for task in orchestrator_tasks:
            print(f"  {task}")

        print_colored(Colors.YELLOW, "\n❌ DIRECT EXECUTION OK:")
        direct_tasks = [
            "• Reading and analyzing existing files",
            "• Answering questions about code structure",
            "• Generating reports (without file output)",
            "• Searching and exploring the codebase",
            "• Code reviews and analysis",
            "• Explaining how systems work"
        ]
        for task in direct_tasks:
            print(f"  {task}")

        print_section("📋 The 11-Phase Workflow")
        phases = [
            "1. Task Validation - Validate requirements and scope",
            "2. Environment Setup - Prepare development environment",
            "3. Dependency Analysis - Analyze impact and dependencies",
            "4. Worktree Creation - Create isolated development branch",
            "5. Implementation - Execute the actual code changes",
            "6. Testing - Run comprehensive test suites",
            "7. Quality Gates - Type checking, linting, security scans",
            "8. Documentation - Update relevant documentation",
            "9. Review - Code review and validation",
            "10. Integration - Merge to target branch",
            "11. Cleanup - Clean up temporary resources"
        ]

        for phase in phases:
            print_colored(Colors.WHITE, f"  {phase}")

        print_section("🚀 How to Use Orchestrator")
        print_colored(Colors.CYAN, "  cd /Users/ryan/src/gadugi5/gadugi")
        print_colored(Colors.CYAN, "  python .claude/orchestrator/main.py \\")
        print_colored(Colors.CYAN, "    --task \"Your task description\" \\")
        print_colored(Colors.CYAN, "    --auto-approve")

        print_section("🔍 Validation Commands")
        validation_commands = [
            "# Check if your task needs orchestrator:",
            ".claude/workflow-enforcement/validate-workflow.py --task \"your task\"",
            "",
            "# Quick compliance check:",
            ".claude/workflow-enforcement/compliance-monitor.py --check",
            "",
            "# View workflow reminder:",
            "cat .claude/workflow-enforcement/workflow-reminder.md"
        ]

        for cmd in validation_commands:
            if cmd.startswith("#"):
                print_colored(Colors.GREEN, f"  {cmd}")
            else:
                print_colored(Colors.WHITE, f"  {cmd}")

        print_colored(Colors.PURPLE, f"\n{'=' * 60}")
        print_colored(Colors.WHITE + Colors.BOLD, "  Remember: The workflow protects code quality!")
        print_colored(Colors.PURPLE, f"{'=' * 60}\n")

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Validate workflow compliance for tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task "Fix bug in user authentication"
  %(prog)s --task "Read config files" --files config.json settings.py
  %(prog)s --guide  # Show comprehensive workflow guide
  %(prog)s --task "Add new feature" --method orchestrator  # Should be compliant
        """
    )

    parser.add_argument(
        "--task",
        help="Task description to validate"
    )

    parser.add_argument(
        "--files",
        nargs="*",
        help="Files that will be modified"
    )

    parser.add_argument(
        "--method",
        default="direct",
        choices=["direct", "orchestrator"],
        help="Execution method (default: direct)"
    )

    parser.add_argument(
        "--guide",
        action="store_true",
        help="Show comprehensive workflow guide"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()

    validator = WorkflowValidator()

    if args.guide:
        validator.show_workflow_guide()
        return

    if not args.task:
        print_colored(Colors.RED, "❌ Error: --task is required (or use --guide)")
        parser.print_help()
        sys.exit(1)

    # Validate the task
    is_compliant, violations, recommendations = validator.validate_task(
        args.task,
        args.files or [],
        args.method
    )

    if args.json:
        # JSON output
        result = {
            "task": args.task,
            "files": args.files or [],
            "method": args.method,
            "compliant": is_compliant,
            "violations": violations,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print_header("WORKFLOW VALIDATION RESULTS")

        print_colored(Colors.BLUE, f"📝 Task: {args.task}")
        if args.files:
            print_colored(Colors.BLUE, f"📁 Files: {', '.join(args.files)}")
        print_colored(Colors.BLUE, f"⚙️  Method: {args.method}")

        if is_compliant:
            print_colored(Colors.GREEN, f"\n✅ WORKFLOW COMPLIANT")
            print_colored(Colors.GREEN, "   This task follows proper workflow requirements.")
        else:
            print_colored(Colors.RED, f"\n❌ WORKFLOW VIOLATION DETECTED")
            print_section("Issues Found")
            for violation in violations:
                print_colored(Colors.RED, f"  {violation}")

            if recommendations:
                print_section("Recommendations")
                for rec in recommendations:
                    if rec.startswith("🚀") or rec.startswith("📚"):
                        print_colored(Colors.GREEN, f"  {rec}")
                    else:
                        print_colored(Colors.WHITE, f"  {rec}")

    sys.exit(0 if is_compliant else 1)

if __name__ == "__main__":
    main()
