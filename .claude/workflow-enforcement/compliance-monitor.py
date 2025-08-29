#!/usr/bin/env python3
"""
Workflow Compliance Monitoring System
Provides automated checks and monitoring for workflow compliance.
"""

import os
import sys
import json
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplianceMonitor:
    """Monitors and enforces workflow compliance in real-time."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.claude_dir = self.repo_root / ".claude"
        self.enforcement_dir = self.claude_dir / "workflow-enforcement"
        self.compliance_log = self.enforcement_dir / "compliance_log.json"
        self.monitor_log = self.enforcement_dir / "monitor.log"

        self.monitoring_active = False
        self.monitor_thread = None

        # Ensure directories exist
        self.enforcement_dir.mkdir(parents=True, exist_ok=True)
        self._init_compliance_log()

    def _init_compliance_log(self):
        """Initialize compliance log if it doesn't exist."""
        if not self.compliance_log.exists():
            initial_data = {
                "violations": [],
                "compliant_executions": [],
                "monitoring_sessions": [],
                "statistics": {
                    "total_checks": 0,
                    "total_violations": 0,
                    "total_compliant": 0,
                    "compliance_rate": 1.0
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(self.compliance_log, 'w') as f:
                json.dump(initial_data, f, indent=2)

    def start_monitoring(self, interval: int = 30):
        """Start real-time workflow monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()

        logger.info(f"Started workflow monitoring with {interval}s interval")
        self._log_monitoring_session("started", {"interval": interval})

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Stopped workflow monitoring")
        self._log_monitoring_session("stopped", {})

    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self._check_git_activity()
                self._check_file_modifications()
                self._check_orchestrator_status()
                self._update_statistics()

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def _check_git_activity(self):
        """Check for git activity that might indicate direct modifications."""
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )

            if result.returncode == 0 and result.stdout.strip():
                # There are uncommitted changes
                changes = result.stdout.strip().split('\n')
                modified_files = []

                for change in changes:
                    if change.strip():
                        status = change[:2]
                        filepath = change[3:].strip()
                        modified_files.append(filepath)

                # Check if orchestrator is active
                if not self._is_orchestrator_active():
                    self._log_potential_violation(
                        "direct_git_modification",
                        f"Uncommitted changes detected without orchestrator",
                        modified_files
                    )

        except subprocess.SubprocessError as e:
            logger.debug(f"Git status check failed: {e}")

    def _check_file_modifications(self):
        """Check for file modifications in real-time."""
        # This is a simplified version - in production, you might use
        # filesystem monitoring libraries like watchdog
        pass

    def _check_orchestrator_status(self):
        """Check if orchestrator is properly running when needed."""
        # Check for orchestrator process
        try:
            result = subprocess.run(
                ["pgrep", "-f", "orchestrator.*main.py"],
                capture_output=True,
                text=True
            )

            orchestrator_running = result.returncode == 0 and result.stdout.strip()

            # Check for environment variables
            env_indicators = [
                "GADUGI_ORCHESTRATOR_ACTIVE",
                "ORCHESTRATOR_TASK_ID",
                "WORKFLOW_PHASE",
                "GADUGI_WORKFLOW_ID"
            ]

            env_active = any(os.getenv(var) for var in env_indicators)

            return orchestrator_running or env_active

        except subprocess.SubprocessError:
            return False

    def _is_orchestrator_active(self) -> bool:
        """Check if orchestrator is currently active."""
        return self._check_orchestrator_status()

    def _log_potential_violation(self, violation_type: str, description: str, files: List[str]):
        """Log a potential workflow violation."""
        try:
            with open(self.compliance_log, 'r') as f:
                data = json.load(f)

            violation = {
                "timestamp": datetime.now().isoformat(),
                "type": violation_type,
                "description": description,
                "files": files,
                "severity": "medium",
                "auto_detected": True
            }

            # Avoid duplicate violations within short time periods
            recent_violations = [
                v for v in data["violations"]
                if (datetime.now() - datetime.fromisoformat(v["timestamp"])).seconds < 300
            ]

            # Check if similar violation already recorded recently
            similar_recent = any(
                v.get("type") == violation_type and v.get("description") == description
                for v in recent_violations
            )

            if not similar_recent:
                data["violations"].append(violation)
                data["statistics"]["total_violations"] += 1
                data["last_updated"] = datetime.now().isoformat()

                with open(self.compliance_log, 'w') as f:
                    json.dump(data, f, indent=2)

                logger.warning(f"Potential workflow violation detected: {violation_type}")

        except Exception as e:
            logger.error(f"Failed to log potential violation: {e}")

    def _log_monitoring_session(self, action: str, metadata: Dict[str, Any]):
        """Log monitoring session events."""
        try:
            with open(self.compliance_log, 'r') as f:
                data = json.load(f)

            session_event = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "metadata": metadata
            }

            data["monitoring_sessions"].append(session_event)
            data["last_updated"] = datetime.now().isoformat()

            with open(self.compliance_log, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log monitoring session: {e}")

    def _update_statistics(self):
        """Update compliance statistics."""
        try:
            with open(self.compliance_log, 'r') as f:
                data = json.load(f)

            total_violations = len(data.get("violations", []))
            total_compliant = len(data.get("compliant_executions", []))
            total_checks = total_violations + total_compliant

            compliance_rate = total_compliant / total_checks if total_checks > 0 else 1.0

            data["statistics"] = {
                "total_checks": total_checks,
                "total_violations": total_violations,
                "total_compliant": total_compliant,
                "compliance_rate": compliance_rate,
                "last_calculated": datetime.now().isoformat()
            }

            data["last_updated"] = datetime.now().isoformat()

            with open(self.compliance_log, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        try:
            with open(self.compliance_log, 'r') as f:
                data = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter recent data
            recent_violations = [
                v for v in data.get("violations", [])
                if datetime.fromisoformat(v["timestamp"]) >= cutoff_date
            ]

            recent_compliant = [
                c for c in data.get("compliant_executions", [])
                if datetime.fromisoformat(c["timestamp"]) >= cutoff_date
            ]

            # Analyze violation patterns
            violation_types = {}
            for violation in recent_violations:
                v_type = violation.get("type", "unknown")
                violation_types[v_type] = violation_types.get(v_type, 0) + 1

            # Calculate trends
            total_recent = len(recent_violations) + len(recent_compliant)
            recent_compliance_rate = len(recent_compliant) / total_recent if total_recent > 0 else 1.0

            report = {
                "period": f"Last {days} days",
                "generated": datetime.now().isoformat(),
                "summary": {
                    "total_activities": total_recent,
                    "violations": len(recent_violations),
                    "compliant_executions": len(recent_compliant),
                    "compliance_rate": recent_compliance_rate,
                    "compliance_percentage": f"{recent_compliance_rate * 100:.1f}%"
                },
                "violation_breakdown": violation_types,
                "recent_violations": recent_violations[-10:],  # Last 10
                "statistics": data.get("statistics", {}),
                "recommendations": self._generate_recommendations(recent_violations)
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on violation patterns."""
        recommendations = []

        if not violations:
            recommendations.append("✅ Excellent! No workflow violations detected.")
            return recommendations

        # Analyze violation patterns
        violation_types = {}
        for violation in violations:
            v_type = violation.get("type", "unknown")
            violation_types[v_type] = violation_types.get(v_type, 0) + 1

        if "direct_git_modification" in violation_types:
            recommendations.append(
                "🔧 Consider using git hooks to prevent direct modifications without orchestrator"
            )

        if len(violations) > 5:
            recommendations.append(
                "📚 Review workflow documentation with your team: .claude/workflow-enforcement/workflow-reminder.md"
            )

        if any(v.get("severity") == "high" for v in violations):
            recommendations.append(
                "⚠️ High-severity violations detected - consider mandatory workflow training"
            )

        recommendations.append(
            "🚀 Use orchestrator for all code changes: python .claude/orchestrator/main.py"
        )

        return recommendations

    def check_compliance_now(self) -> Dict[str, Any]:
        """Perform immediate compliance check."""
        logger.info("Performing immediate compliance check")

        issues = []

        # Check for uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )

            if result.returncode == 0 and result.stdout.strip():
                if not self._is_orchestrator_active():
                    issues.append({
                        "type": "uncommitted_changes",
                        "severity": "medium",
                        "description": "Uncommitted changes without orchestrator context"
                    })
        except Exception as e:
            logger.debug(f"Git status check failed: {e}")

        # Check orchestrator configuration
        orchestrator_path = self.claude_dir / "orchestrator" / "main.py"
        if not orchestrator_path.exists():
            issues.append({
                "type": "missing_orchestrator",
                "severity": "high",
                "description": "Orchestrator main.py not found"
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "compliant": len(issues) == 0,
            "issues": issues,
            "orchestrator_active": self._is_orchestrator_active()
        }

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="Workflow Compliance Monitor")
    parser.add_argument("--start", action="store_true", help="Start monitoring")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring")
    parser.add_argument("--report", action="store_true", help="Generate compliance report")
    parser.add_argument("--check", action="store_true", help="Immediate compliance check")
    parser.add_argument("--days", type=int, default=7, help="Days for report (default: 7)")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")

    args = parser.parse_args()

    monitor = ComplianceMonitor()

    if args.start:
        print("🔍 Starting workflow compliance monitoring...")
        monitor.start_monitoring(args.interval)

        try:
            # Keep the main thread alive
            while monitor.monitoring_active:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            monitor.stop_monitoring()

    elif args.stop:
        print("🛑 Stopping workflow compliance monitoring...")
        monitor.stop_monitoring()

    elif args.report:
        print(f"📊 Generating compliance report for last {args.days} days...")
        report = monitor.generate_report(args.days)
        print(json.dumps(report, indent=2))

    elif args.check:
        print("🔍 Performing immediate compliance check...")
        result = monitor.check_compliance_now()
        print(json.dumps(result, indent=2))

        if not result["compliant"]:
            sys.exit(1)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
