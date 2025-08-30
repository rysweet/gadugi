#!/usr/bin/env python3
"""
Setup Workflow Enforcement System
Comprehensive setup and initialization for the workflow enforcement system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import argparse


class WorkflowEnforcementSetup:
    """Sets up and initializes the complete workflow enforcement system."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.claude_dir = self.repo_root / ".claude"
        self.enforcement_dir = self.claude_dir / "workflow-enforcement"
        self.hooks_dir = self.claude_dir / "hooks"

        # Ensure directories exist
        self.enforcement_dir.mkdir(parents=True, exist_ok=True)
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def setup_git_hooks(self) -> Tuple[bool, List[str]]:
        """Set up git hooks for workflow enforcement."""
        messages = []

        try:
            git_hooks_dir = self.repo_root / ".git" / "hooks"
            if not git_hooks_dir.exists():
                messages.append("❌ .git/hooks directory not found")
                return False, messages

            # Create pre-commit hook
            pre_commit_hook = git_hooks_dir / "pre-commit"
            hook_content = f"""#!/bin/bash
# Workflow Enforcement Pre-commit Hook
# Ensures all commits go through proper workflow

echo "🚨 Workflow Enforcement: Validating commit..."

# Check if orchestrator is active
if [[ -z "${{GADUGI_ORCHESTRATOR_ACTIVE}}" && -z "${{ORCHESTRATOR_TASK_ID}}" ]]; then
    echo "❌ WORKFLOW VIOLATION: Direct commit detected!"
    echo "   All code changes must go through orchestrator workflow."
    echo ""
    echo "✅ Correct approach:"
    echo "   python .gadugi/.gadugi/src/orchestrator/main.py --task 'your changes description'"
    echo ""
    echo "🔓 Emergency override (use with caution):"
    echo "   export GADUGI_EMERGENCY_OVERRIDE=true"
    echo "   git commit -m 'your message' # then unset the variable"
    echo ""

    # Check for emergency override
    if [[ -n "${{GADUGI_EMERGENCY_OVERRIDE}}" ]]; then
        echo "⚠️  Emergency override detected - logging violation"
        echo "$(date): Emergency commit override used" >> {self.enforcement_dir}/emergency_overrides.log
    else
        echo "🛑 Commit blocked by workflow enforcement"
        exit 1
    fi
fi

echo "✅ Workflow compliance validated"
exit 0
"""

            with open(pre_commit_hook, "w") as f:
                f.write(hook_content)

            # Make hook executable
            os.chmod(pre_commit_hook, 0o755)
            messages.append("✅ Pre-commit hook installed")

            # Create commit-msg hook
            commit_msg_hook = git_hooks_dir / "commit-msg"
            commit_msg_content = f"""#!/bin/bash
# Workflow Enforcement Commit Message Hook
# Validates commit messages and logs workflow events

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Log the commit event
echo "$(date): Commit: $COMMIT_MSG" >> {self.enforcement_dir}/workflow_activity.log

# Check for proper commit message format if not emergency override
if [[ -z "${{GADUGI_EMERGENCY_OVERRIDE}}" ]]; then
    # Validate commit message includes workflow context
    if [[ ! "$COMMIT_MSG" =~ (orchestrator|workflow|phase) ]] && [[ ! "$COMMIT_MSG" =~ ^(fix|feat|docs|style|refactor|test|chore): ]]; then
        echo "⚠️  Commit message should indicate workflow context or follow conventional format"
        echo "   Examples: 'feat: add user authentication via orchestrator workflow'"
        echo "   Or: 'fix: resolve type errors (workflow phase 7)'"
    fi
fi

exit 0
"""

            with open(commit_msg_hook, "w") as f:
                f.write(commit_msg_content)

            os.chmod(commit_msg_hook, 0o755)
            messages.append("✅ Commit-msg hook installed")

            return True, messages

        except Exception as e:
            messages.append(f"❌ Error setting up git hooks: {str(e)}")
            return False, messages

    def create_workflow_config(self) -> Tuple[bool, List[str]]:
        """Create workflow enforcement configuration file."""
        messages = []

        try:
            config_file = self.enforcement_dir / "config.json"

            config = {
                "enforcement_level": "warning",  # "off", "warning", "strict"
                "auto_redirect": True,
                "log_violations": True,
                "log_compliant": True,
                "monitoring": {
                    "enabled": True,
                    "interval": 30,
                    "check_git_status": True,
                    "check_file_changes": True,
                    "check_orchestrator_status": True,
                },
                "notifications": {
                    "violation_warnings": True,
                    "compliance_reminders": True,
                    "weekly_reports": False,
                },
                "emergency_override": {
                    "enabled": True,
                    "require_justification": True,
                    "log_overrides": True,
                },
                "excluded_paths": [
                    ".git/",
                    "node_modules/",
                    "__pycache__/",
                    "*.pyc",
                    "*.log",
                    ".DS_Store",
                ],
                "required_workflow_phases": [
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
                    "cleanup",
                ],
            }

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            messages.append("✅ Workflow configuration created")
            return True, messages

        except Exception as e:
            messages.append(f"❌ Error creating config: {str(e)}")
            return False, messages

    def initialize_logs(self) -> Tuple[bool, List[str]]:
        """Initialize logging system."""
        messages = []

        try:
            log_files = [
                "compliance_log.json",
                "workflow_activity.log",
                "emergency_overrides.log",
                "monitoring.log",
            ]

            for log_file in log_files:
                log_path = self.enforcement_dir / log_file

                if log_file.endswith(".json"):
                    # Initialize JSON log files
                    if not log_path.exists():
                        initial_data = {
                            "created": datetime.now().isoformat(),
                            "violations": [],
                            "compliant_executions": [],
                            "statistics": {
                                "total_checks": 0,
                                "total_violations": 0,
                                "total_compliant": 0,
                                "compliance_rate": 1.0,
                            },
                        }
                        with open(log_path, "w") as f:
                            json.dump(initial_data, f, indent=2)
                else:
                    # Initialize text log files
                    if not log_path.exists():
                        with open(log_path, "w") as f:
                            f.write(
                                f"# Workflow Enforcement Log - Created {datetime.now().isoformat()}\\n"
                            )

                messages.append(f"✅ Initialized {log_file}")

            return True, messages

        except Exception as e:
            messages.append(f"❌ Error initializing logs: {str(e)}")
            return False, messages

    def setup_shell_integration(self) -> Tuple[bool, List[str]]:
        """Set up shell integration for workflow enforcement."""
        messages = []

        try:
            # Create shell function that can be sourced
            shell_integration = self.enforcement_dir / "shell_integration.sh"

            shell_content = f"""#!/bin/bash
# Workflow Enforcement Shell Integration
# Source this file in your shell profile for enhanced workflow support

# Function to validate workflow before common operations
gadugi_validate() {{
    local task_desc="${{1:-}}"
    local files="${{@:2}}"

    if [[ -n "$task_desc" ]]; then
        python "{self.enforcement_dir}/validate-workflow.py" \\
            --task "$task_desc" \\
            --files $files
    else
        echo "🚨 Gadugi Workflow Enforcement Active"
        echo "💡 Use: gadugi_validate 'task description' [files...]"
    fi
}}

# Enhanced git commands with workflow validation
git_with_validation() {{
    local git_command="$1"
    shift

    case "$git_command" in
        "commit"|"add"|"rm"|"mv")
            if [[ -z "${{GADUGI_ORCHESTRATOR_ACTIVE}}" && -z "${{GADUGI_EMERGENCY_OVERRIDE}}" ]]; then
                echo "⚠️  Git operation detected without orchestrator context"
                echo "   Consider using: python .gadugi/.gadugi/src/orchestrator/main.py"
                read -p "Continue anyway? [y/N]: " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    return 1
                fi
            fi
            ;;
    esac

    command git "$git_command" "$@"
}}

# Aliases for common operations
alias gvalidate='gadugi_validate'
alias gwf='gadugi_validate'
alias orchestrator='cd "{self.repo_root}" && python .gadugi/.gadugi/src/orchestrator/main.py'

# Environment variables
export GADUGI_WORKFLOW_ENFORCEMENT_ACTIVE=1
export GADUGI_ENFORCEMENT_DIR="{self.enforcement_dir}"

echo "✅ Gadugi Workflow Enforcement loaded"
echo "💡 Available commands:"
echo "   gvalidate 'task' [files...]  - Validate workflow compliance"
echo "   orchestrator                 - Launch orchestrator"
"""

            with open(shell_integration, "w") as f:
                f.write(shell_content)

            os.chmod(shell_integration, 0o755)
            messages.append("✅ Shell integration created")

            # Instructions for user
            messages.append(
                "💡 To enable shell integration, add to your shell profile:"
            )
            messages.append(f"   source {shell_integration}")

            return True, messages

        except Exception as e:
            messages.append(f"❌ Error setting up shell integration: {str(e)}")
            return False, messages

    def create_quick_reference(self) -> Tuple[bool, List[str]]:
        """Create quick reference guide."""
        messages = []

        try:
            reference_file = self.enforcement_dir / "QUICK_REFERENCE.md"

            reference_content = """# Workflow Enforcement Quick Reference

## 🚀 Common Commands

### Validate Task Compliance
```bash
# Check if your task needs orchestrator
.gadugi/.gadugi/src/workflow-enforcement/validate-workflow.py --task "fix user authentication"

# Check with specific files
.gadugi/.gadugi/src/workflow-enforcement/validate-workflow.py --task "update config" --files config.json settings.py
```

### Use Orchestrator (Required for Code Changes)
```bash
cd /Users/ryan/src/gadugi5/gadugi
python .gadugi/.gadugi/src/orchestrator/main.py --task "your task description"
```

### Monitoring and Compliance
```bash
# Start real-time monitoring
.gadugi/.gadugi/src/workflow-enforcement/compliance-monitor.py --start

# Generate compliance report
.gadugi/.gadugi/src/workflow-enforcement/compliance-monitor.py --report

# Immediate compliance check
.gadugi/.gadugi/src/workflow-enforcement/compliance-monitor.py --check
```

### Emergency Override (Use Sparingly)
```bash
# Set emergency override for direct git operations
export GADUGI_EMERGENCY_OVERRIDE=true
git commit -m "Critical hotfix - justification here"
unset GADUGI_EMERGENCY_OVERRIDE  # Always unset after use
```

## 🎯 Decision Matrix

| Task Type | Use Orchestrator? | Why |
|-----------|-------------------|-----|
| Fix bugs | ✅ YES | Code changes need testing |
| Add features | ✅ YES | New code needs validation |
| Update config | ✅ YES | Config affects system behavior |
| Read files | ❌ NO | No modifications made |
| Code analysis | ❌ NO | Read-only operation |
| Answer questions | ❌ NO | Informational only |

## 📋 The 11-Phase Workflow

1. **Task Validation** - Validate requirements and scope
2. **Environment Setup** - Prepare development environment
3. **Dependency Analysis** - Analyze impact and dependencies
4. **Worktree Creation** - Create isolated development branch
5. **Implementation** - Execute the actual code changes
6. **Testing** - Run comprehensive test suites
7. **Quality Gates** - Type checking, linting, security scans
8. **Documentation** - Update relevant documentation
9. **Review** - Code review and validation
10. **Integration** - Merge to target branch
11. **Cleanup** - Clean up temporary resources

## 🔧 Troubleshooting

### "Workflow violation detected"
- **Cause**: Attempting code changes without orchestrator
- **Solution**: Use `python .gadugi/.gadugi/src/orchestrator/main.py --task "your task"`

### "Pre-commit hook blocked commit"
- **Cause**: Direct git commit without orchestrator context
- **Solution**: Use orchestrator workflow or emergency override with justification

### "Orchestrator not found"
- **Cause**: Missing orchestrator setup
- **Solution**: Check that `.gadugi/.gadugi/src/orchestrator/main.py` exists

## 📊 Monitoring

### View Recent Activity
```bash
tail -f .gadugi/.gadugi/src/workflow-enforcement/workflow_activity.log
```

### Check Compliance Status
```bash
python .gadugi/.gadugi/src/workflow-enforcement/workflow-checker.py --report
```

### View Emergency Overrides
```bash
cat .gadugi/.gadugi/src/workflow-enforcement/emergency_overrides.log
```

## 🚨 Emergency Procedures

### Production Hotfix
1. Set emergency override: `export GADUGI_EMERGENCY_OVERRIDE=true`
2. Make minimal changes
3. Commit with clear justification
4. Unset override: `unset GADUGI_EMERGENCY_OVERRIDE`
5. Schedule proper workflow review

### Disable Enforcement Temporarily
```bash
# Disable git hooks temporarily
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Re-enable when ready
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

---
Remember: The workflow exists to protect code quality and ensure proper testing!
"""

            with open(reference_file, "w") as f:
                f.write(reference_content)

            messages.append("✅ Quick reference guide created")
            return True, messages

        except Exception as e:
            messages.append(f"❌ Error creating quick reference: {str(e)}")
            return False, messages

    def validate_setup(self) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate the complete workflow enforcement setup."""
        messages = []
        validation_results = {
            "files_present": {},
            "git_hooks": {},
            "permissions": {},
            "configuration": {},
            "overall_status": "unknown",
        }

        try:
            # Check required files
            required_files = [
                "workflow-checker.py",
                "workflow-reminder.md",
                "pre-task-hook.sh",
                "compliance-monitor.py",
                "validate-workflow.py",
                "update-agent-instructions.py",
                "setup-workflow-enforcement.py",
                "config.json",
                "QUICK_REFERENCE.md",
            ]

            for file_name in required_files:
                file_path = self.enforcement_dir / file_name
                exists = file_path.exists()
                validation_results["files_present"][file_name] = exists

                if exists:
                    messages.append(f"✅ {file_name} present")
                else:
                    messages.append(f"❌ {file_name} missing")

            # Check git hooks
            git_hooks_dir = self.repo_root / ".git" / "hooks"
            hooks_to_check = ["pre-commit", "commit-msg"]

            for hook in hooks_to_check:
                hook_path = git_hooks_dir / hook
                exists = hook_path.exists()
                executable = exists and os.access(hook_path, os.X_OK)

                validation_results["git_hooks"][hook] = {
                    "exists": exists,
                    "executable": executable,
                }

                if exists and executable:
                    messages.append(f"✅ Git hook {hook} installed and executable")
                elif exists:
                    messages.append(f"⚠️  Git hook {hook} exists but not executable")
                else:
                    messages.append(f"❌ Git hook {hook} not installed")

            # Check permissions on scripts
            scripts = [
                "workflow-checker.py",
                "pre-task-hook.sh",
                "compliance-monitor.py",
                "validate-workflow.py",
            ]

            for script in scripts:
                script_path = self.enforcement_dir / script
                if script_path.exists():
                    executable = os.access(script_path, os.X_OK)
                    validation_results["permissions"][script] = executable

                    if executable:
                        messages.append(f"✅ {script} is executable")
                    else:
                        messages.append(f"⚠️  {script} is not executable")

            # Check configuration
            config_file = self.enforcement_dir / "config.json"
            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                    validation_results["configuration"]["valid"] = True
                    validation_results["configuration"]["enforcement_level"] = (
                        config.get("enforcement_level", "unknown")
                    )
                    messages.append("✅ Configuration file is valid JSON")
                except json.JSONDecodeError:
                    validation_results["configuration"]["valid"] = False
                    messages.append("❌ Configuration file is invalid JSON")

            # Overall status
            files_ok = all(validation_results["files_present"].values())
            hooks_ok = all(
                hook_data["exists"] and hook_data["executable"]
                for hook_data in validation_results["git_hooks"].values()
            )
            permissions_ok = all(validation_results["permissions"].values())
            config_ok = validation_results["configuration"].get("valid", False)

            if files_ok and hooks_ok and permissions_ok and config_ok:
                validation_results["overall_status"] = "healthy"
                messages.append("🎉 Workflow enforcement system is fully operational!")
            else:
                validation_results["overall_status"] = "needs_attention"
                messages.append("⚠️  Workflow enforcement system needs attention")

            return True, messages, validation_results

        except Exception as e:
            messages.append(f"❌ Error during validation: {str(e)}")
            validation_results["overall_status"] = "error"
            return False, messages, validation_results

    def run_complete_setup(self) -> Tuple[bool, List[str]]:
        """Run the complete workflow enforcement setup."""
        all_messages = []
        all_success = True

        print("🚀 Setting up Workflow Enforcement System...")
        print("=" * 50)

        # 1. Create git hooks
        print("\\n1. Setting up Git hooks...")
        success, messages = self.setup_git_hooks()
        all_messages.extend(messages)
        all_success = all_success and success

        # 2. Create configuration
        print("\\n2. Creating configuration...")
        success, messages = self.create_workflow_config()
        all_messages.extend(messages)
        all_success = all_success and success

        # 3. Initialize logs
        print("\\n3. Initializing logging system...")
        success, messages = self.initialize_logs()
        all_messages.extend(messages)
        all_success = all_success and success

        # 4. Set up shell integration
        print("\\n4. Setting up shell integration...")
        success, messages = self.setup_shell_integration()
        all_messages.extend(messages)
        all_success = all_success and success

        # 5. Create quick reference
        print("\\n5. Creating quick reference guide...")
        success, messages = self.create_quick_reference()
        all_messages.extend(messages)
        all_success = all_success and success

        # 6. Validate setup
        print("\\n6. Validating setup...")
        success, messages, validation = self.validate_setup()
        all_messages.extend(messages)

        print("\\n" + "=" * 50)
        if all_success and validation["overall_status"] == "healthy":
            print("🎉 Workflow Enforcement System Setup Complete!")
            print("\\n📚 Next steps:")
            print("   1. Review: cat .gadugi/.gadugi/src/workflow-enforcement/QUICK_REFERENCE.md")
            print(
                "   2. Test: .gadugi/.gadugi/src/workflow-enforcement/validate-workflow.py --guide"
            )
            print(
                "   3. Monitor: .gadugi/.gadugi/src/workflow-enforcement/compliance-monitor.py --start"
            )
        else:
            print("⚠️  Setup completed with some issues - review messages above")

        return all_success, all_messages


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Setup Workflow Enforcement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --setup          # Run complete setup
  %(prog)s --validate       # Validate existing setup
  %(prog)s --git-hooks      # Setup git hooks only
  %(prog)s --config         # Create configuration only
        """,
    )

    parser.add_argument(
        "--setup", action="store_true", help="Run complete workflow enforcement setup"
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate existing setup"
    )

    parser.add_argument("--git-hooks", action="store_true", help="Setup git hooks only")

    parser.add_argument(
        "--config", action="store_true", help="Create configuration only"
    )

    parser.add_argument(
        "--shell-integration", action="store_true", help="Setup shell integration only"
    )

    args = parser.parse_args()

    setup = WorkflowEnforcementSetup()

    if args.setup:
        success, messages = setup.run_complete_setup()
        sys.exit(0 if success else 1)

    elif args.validate:
        print("🔍 Validating workflow enforcement setup...")
        success, messages, validation = setup.validate_setup()

        for message in messages:
            print(message)

        print(f"\\n📊 Overall Status: {validation['overall_status']}")
        sys.exit(0 if validation["overall_status"] == "healthy" else 1)

    elif args.git_hooks:
        print("🔧 Setting up Git hooks...")
        success, messages = setup.setup_git_hooks()

        for message in messages:
            print(message)

        sys.exit(0 if success else 1)

    elif args.config:
        print("📝 Creating configuration...")
        success, messages = setup.create_workflow_config()

        for message in messages:
            print(message)

        sys.exit(0 if success else 1)

    elif args.shell_integration:
        print("🐚 Setting up shell integration...")
        success, messages = setup.setup_shell_integration()

        for message in messages:
            print(message)

        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
