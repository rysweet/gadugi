"""
GitHub Actions Integration for PR Backlog Manager.

Provides specialized integration capabilities for running PR Backlog Manager
in GitHub Actions environments with auto-approve and security constraints.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GitHubEventType(Enum):
    """GitHub Actions event types."""

    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    WORKFLOW_DISPATCH = "workflow_dispatch"
    PUSH = "push"
    UNKNOWN = "unknown"


class ProcessingMode(Enum):
    """Processing modes for different GitHub events."""

    SINGLE_PR = "single_pr"
    FULL_BACKLOG = "full_backlog"
    TARGETED_BATCH = "targeted_batch"


@dataclass
class GitHubContext:
    """GitHub Actions context information."""

    event_type: GitHubEventType
    repository: str
    pr_number: Optional[int]
    actor: str
    ref: str
    sha: str
    workflow_run_id: str
    run_attempt: int

    @classmethod
    def from_environment(cls) -> "GitHubContext":
        """Create GitHub context from environment variables."""
        return cls(
            event_type=GitHubEventType(os.getenv("GITHUB_EVENT_NAME", "unknown")),
            repository=os.getenv("GITHUB_REPOSITORY", "unknown/unknown"),
            pr_number=cls._extract_pr_number(),
            actor=os.getenv("GITHUB_ACTOR", "unknown"),
            ref=os.getenv("GITHUB_REF", "unknown"),
            sha=os.getenv("GITHUB_SHA", "unknown"),
            workflow_run_id=os.getenv("GITHUB_RUN_ID", "unknown"),
            run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "1")),
        )

    @staticmethod
    def _extract_pr_number() -> Optional[int]:
        """Extract PR number from GitHub event context."""
        try:
            # Try to get from event payload
            event_path = os.getenv("GITHUB_EVENT_PATH")
            if event_path and os.path.exists(event_path):
                with open(event_path, "r") as f:
                    event_data = json.load(f)

                if "pull_request" in event_data:
                    return event_data["pull_request"]["number"]
                elif "number" in event_data:
                    return event_data["number"]

            # Try to extract from ref
            ref = os.getenv("GITHUB_REF", "")
            if ref.startswith("refs/pull/"):
                return int(ref.split("/")[2])

            return None
        except Exception:
            return None


@dataclass
class SecurityConstraints:
    """Security constraints for GitHub Actions environment."""

    auto_approve_enabled: bool
    restricted_operations: List[str]
    max_processing_time: int
    rate_limit_threshold: int

    @classmethod
    def from_environment(cls) -> "SecurityConstraints":
        """Create security constraints from environment."""
        return cls(
            auto_approve_enabled=os.getenv("CLAUDE_AUTO_APPROVE", "false").lower()
            == "true",
            restricted_operations=[
                "delete_repository",
                "force_push",
                "delete_branch",
                "close_issue",
                "merge_pr",
            ],
            max_processing_time=int(
                os.getenv("MAX_PROCESSING_TIME", "600")
            ),  # 10 minutes
            rate_limit_threshold=int(os.getenv("RATE_LIMIT_THRESHOLD", "50")),
        )


class GitHubActionsIntegration:
    """
    Specialized integration for GitHub Actions environments.

    Handles GitHub Actions-specific requirements including:
    - Event-driven processing mode selection
    - Security constraint enforcement
    - Auto-approve safety validation
    - Workflow artifact management
    """

    def __init__(self, pr_backlog_manager):
        """Initialize GitHub Actions integration."""
        self.pr_backlog_manager = pr_backlog_manager
        self.github_context = GitHubContext.from_environment()
        self.security_constraints = SecurityConstraints.from_environment()

        # Validate environment
        self._validate_github_actions_environment()

        logger.info(
            f"Initialized GitHub Actions integration - Event: {self.github_context.event_type.value}"
        )

    def _validate_github_actions_environment(self) -> None:
        """Validate that we're running in a proper GitHub Actions environment."""
        if not os.getenv("GITHUB_ACTIONS"):
            raise RuntimeError(
                "GitHub Actions integration requires GITHUB_ACTIONS=true"
            )

        if not os.getenv("GITHUB_TOKEN"):
            raise RuntimeError("GitHub Actions integration requires GITHUB_TOKEN")

        if self.security_constraints.auto_approve_enabled:
            if not os.getenv("CLAUDE_AUTO_APPROVE"):
                raise RuntimeError(
                    "Auto-approve requires explicit CLAUDE_AUTO_APPROVE=true"
                )

            # Validate allowed event types for auto-approve
            allowed_events = [
                GitHubEventType.PULL_REQUEST,
                GitHubEventType.SCHEDULE,
                GitHubEventType.WORKFLOW_DISPATCH,
            ]
            if self.github_context.event_type not in allowed_events:
                raise RuntimeError(
                    f"Auto-approve not allowed for event type: {self.github_context.event_type.value}"
                )

    def determine_processing_mode(self) -> Tuple[ProcessingMode, Dict[str, Any]]:
        """
        Determine processing mode based on GitHub event context.

        Returns:
            Tuple of (ProcessingMode, processing_config)
        """
        if self.github_context.event_type == GitHubEventType.PULL_REQUEST:
            if self.github_context.pr_number:
                return ProcessingMode.SINGLE_PR, {
                    "pr_number": self.github_context.pr_number,
                    "reason": "pull_request_event",
                }

        elif self.github_context.event_type == GitHubEventType.WORKFLOW_DISPATCH:
            # Check for manual PR number input
            pr_number = self._get_workflow_dispatch_pr_number()
            if pr_number:
                return ProcessingMode.SINGLE_PR, {
                    "pr_number": pr_number,
                    "reason": "manual_dispatch",
                }
            else:
                return ProcessingMode.FULL_BACKLOG, {
                    "reason": "manual_backlog_dispatch"
                }

        elif self.github_context.event_type == GitHubEventType.SCHEDULE:
            return ProcessingMode.FULL_BACKLOG, {
                "reason": "scheduled_backlog_processing"
            }

        else:
            # Default to full backlog for unknown events
            return ProcessingMode.FULL_BACKLOG, {
                "reason": f"unknown_event_{self.github_context.event_type.value}"
            }

    def _get_workflow_dispatch_pr_number(self) -> Optional[int]:
        """Get PR number from workflow_dispatch inputs."""
        try:
            event_path = os.getenv("GITHUB_EVENT_PATH")
            if event_path and os.path.exists(event_path):
                with open(event_path, "r") as f:
                    event_data = json.load(f)

                inputs = event_data.get("inputs", {})
                pr_input = inputs.get("pr_number", "").strip()

                if pr_input:
                    return int(pr_input)

            return None
        except Exception:
            return None

    def execute_processing(self) -> Dict[str, Any]:
        """
        Execute PR backlog processing based on GitHub Actions context.

        Returns:
            Processing results and metrics
        """
        start_time = datetime.now()

        try:
            # Determine processing mode
            mode, config = self.determine_processing_mode()
            logger.info(f"Processing mode: {mode.value} - Config: {config}")

            # Execute based on mode
            if mode == ProcessingMode.SINGLE_PR:
                result = self._execute_single_pr_processing(config["pr_number"])
            elif mode == ProcessingMode.FULL_BACKLOG:
                result = self._execute_full_backlog_processing()
            else:
                raise ValueError(f"Unsupported processing mode: {mode}")

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Prepare final result
            final_result = {
                "github_context": {
                    "event_type": self.github_context.event_type.value,
                    "repository": self.github_context.repository,
                    "pr_number": self.github_context.pr_number,
                    "workflow_run_id": self.github_context.workflow_run_id,
                    "run_attempt": self.github_context.run_attempt,
                },
                "processing_mode": mode.value,
                "processing_config": config,
                "processing_time": processing_time,
                "results": result,
                "success": True,
            }

            # Create workflow artifacts
            self._create_workflow_artifacts(final_result)

            # Generate workflow summary
            self._generate_workflow_summary(final_result)

            return final_result

        except Exception as e:
            logger.error(f"GitHub Actions processing failed: {e}")

            error_result = {
                "github_context": {
                    "event_type": self.github_context.event_type.value,
                    "repository": self.github_context.repository,
                },
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

            self._create_error_artifacts(error_result)
            return error_result

    def _execute_single_pr_processing(self, pr_number: int) -> Dict[str, Any]:
        """Execute processing for a single PR."""
        logger.info(f"Processing single PR #{pr_number}")

        # Validate security constraints
        self._validate_operation_safety("process_single_pr")

        # Process the PR
        assessment = self.pr_backlog_manager.process_single_pr(pr_number)

        return {
            "mode": "single_pr",
            "pr_number": pr_number,
            "assessment": {
                "status": assessment.status.value,
                "readiness_score": assessment.readiness_score,
                "is_ready": assessment.is_ready,
                "blocking_issues_count": len(assessment.blocking_issues),
                "resolution_actions_count": len(assessment.resolution_actions),
                "processing_time": assessment.processing_time,
            },
            "blocking_issues": assessment.blocking_issues,
            "resolution_actions": assessment.resolution_actions,
        }

    def _execute_full_backlog_processing(self) -> Dict[str, Any]:
        """Execute processing for the full PR backlog."""
        logger.info("Processing full PR backlog")

        # Validate security constraints
        self._validate_operation_safety("process_backlog")

        # Process the backlog
        metrics = self.pr_backlog_manager.process_backlog()

        return {
            "mode": "full_backlog",
            "metrics": {
                "total_prs": metrics.total_prs,
                "ready_prs": metrics.ready_prs,
                "blocked_prs": metrics.blocked_prs,
                "processing_time": metrics.processing_time,
                "automation_rate": metrics.automation_rate,
                "success_rate": metrics.success_rate,
            },
        }

    def _validate_operation_safety(self, operation: str) -> None:
        """Validate that operation is safe for current context."""
        if operation in self.security_constraints.restricted_operations:
            raise RuntimeError(
                f"Operation {operation} is restricted in auto-approve mode"
            )

        # Additional safety checks for auto-approve
        if self.security_constraints.auto_approve_enabled:
            # Ensure we're not processing too many PRs in auto-approve mode
            if operation == "process_backlog":
                # Could add checks for backlog size limits
                pass

    def _create_workflow_artifacts(self, result: Dict[str, Any]) -> None:
        """Create workflow artifacts for debugging and reporting."""
        try:
            # Create artifacts directory
            artifacts_dir = os.path.expanduser("~/.claude/artifacts")
            os.makedirs(artifacts_dir, exist_ok=True)

            # Create detailed result artifact
            result_file = os.path.join(
                artifacts_dir,
                f"pr-backlog-result-{self.github_context.workflow_run_id}.json",
            )

            with open(result_file, "w") as f:
                json.dump(result, f, indent=2, default=str)

            logger.info(f"Created workflow artifact: {result_file}")

            # Create summary artifact
            summary_file = os.path.join(
                artifacts_dir,
                f"pr-backlog-summary-{self.github_context.workflow_run_id}.txt",
            )

            with open(summary_file, "w") as f:
                f.write(self._format_text_summary(result))

            logger.info(f"Created summary artifact: {summary_file}")

        except Exception as e:
            logger.warning(f"Failed to create workflow artifacts: {e}")

    def _create_error_artifacts(self, error_result: Dict[str, Any]) -> None:
        """Create error artifacts for debugging."""
        try:
            artifacts_dir = os.path.expanduser("~/.claude/artifacts")
            os.makedirs(artifacts_dir, exist_ok=True)

            error_file = os.path.join(
                artifacts_dir,
                f"pr-backlog-error-{self.github_context.workflow_run_id}.json",
            )

            with open(error_file, "w") as f:
                json.dump(error_result, f, indent=2, default=str)

            logger.info(f"Created error artifact: {error_file}")

        except Exception as e:
            logger.warning(f"Failed to create error artifacts: {e}")

    def _generate_workflow_summary(self, result: Dict[str, Any]) -> None:
        """Generate GitHub Actions workflow summary."""
        try:
            # Check if we can write to GitHub Actions summary
            if not os.getenv("GITHUB_STEP_SUMMARY"):
                return

            summary_content = self._format_github_summary(result)

            # Append to GitHub Actions summary
            with open(os.getenv("GITHUB_STEP_SUMMARY"), "a") as f:
                f.write(summary_content)

            logger.info("Generated GitHub Actions workflow summary")

        except Exception as e:
            logger.warning(f"Failed to generate workflow summary: {e}")

    def _format_github_summary(self, result: Dict[str, Any]) -> str:
        """Format result as GitHub Actions summary markdown."""
        processing_mode = result.get("processing_mode", "unknown")
        success = result.get("success", False)

        summary = f"""
## 🤖 PR Backlog Manager Results

**Status:** {"✅ Success" if success else "❌ Failed"}
**Mode:** {processing_mode}
**Repository:** {self.github_context.repository}
**Workflow Run:** [{self.github_context.workflow_run_id}](https://github.com/{self.github_context.repository}/actions/runs/{self.github_context.workflow_run_id})
**Processing Time:** {result.get("processing_time", 0):.2f}s

"""

        if success:
            if processing_mode == "single_pr":
                assessment = result["results"]["assessment"]
                summary += f"""
### Single PR Assessment

**PR Number:** #{result["results"]["pr_number"]}
**Status:** {assessment["status"]}
**Readiness Score:** {assessment["readiness_score"]:.1f}%
**Ready for Review:** {"✅ Yes" if assessment["is_ready"] else "❌ No"}

"""
                if result["results"]["blocking_issues"]:
                    summary += "**Blocking Issues:**\n"
                    for issue in result["results"]["blocking_issues"]:
                        summary += f"- {issue}\n"
                    summary += "\n"

                if result["results"]["resolution_actions"]:
                    summary += "**Resolution Actions:**\n"
                    for action in result["results"]["resolution_actions"]:
                        summary += f"- {action}\n"
                    summary += "\n"

            elif processing_mode == "full_backlog":
                metrics = result["results"]["metrics"]
                summary += f"""
### Backlog Processing Results

**Total PRs Processed:** {metrics["total_prs"]}
**Ready PRs:** {metrics["ready_prs"]}
**Blocked PRs:** {metrics["blocked_prs"]}
**Automation Rate:** {metrics["automation_rate"]:.1f}%
**Success Rate:** {metrics["success_rate"]:.1f}%

"""
        else:
            summary += f"""
### Error Details

**Error Type:** {result.get("error_type", "Unknown")}
**Error Message:** {result.get("error", "No details available")}

"""

        summary += f"""
---
*Generated by PR Backlog Manager at {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}*
"""

        return summary

    def _format_text_summary(self, result: Dict[str, Any]) -> str:
        """Format result as plain text summary."""
        lines = [
            "PR Backlog Manager Results",
            "=" * 30,
            f"Event Type: {result['github_context']['event_type']}",
            f"Repository: {result['github_context']['repository']}",
            f"Workflow Run: {result['github_context']['workflow_run_id']}",
            f"Processing Mode: {result['processing_mode']}",
            f"Processing Time: {result['processing_time']:.2f}s",
            f"Success: {result['success']}",
            "",
        ]

        if result["success"]:
            if result["processing_mode"] == "single_pr":
                assessment = result["results"]["assessment"]
                lines.extend(
                    [
                        f"PR Number: #{result['results']['pr_number']}",
                        f"Status: {assessment['status']}",
                        f"Readiness Score: {assessment['readiness_score']:.1f}%",
                        f"Ready for Review: {assessment['is_ready']}",
                        f"Blocking Issues: {assessment['blocking_issues_count']}",
                        f"Resolution Actions: {assessment['resolution_actions_count']}",
                        "",
                    ]
                )

            elif result["processing_mode"] == "full_backlog":
                metrics = result["results"]["metrics"]
                lines.extend(
                    [
                        f"Total PRs: {metrics['total_prs']}",
                        f"Ready PRs: {metrics['ready_prs']}",
                        f"Blocked PRs: {metrics['blocked_prs']}",
                        f"Automation Rate: {metrics['automation_rate']:.1f}%",
                        f"Success Rate: {metrics['success_rate']:.1f}%",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    f"Error Type: {result.get('error_type', 'Unknown')}",
                    f"Error Message: {result.get('error', 'No details')}",
                    "",
                ]
            )

        lines.append(f"Timestamp: {datetime.now().isoformat()}")

        return "\n".join(lines)

    def set_github_outputs(self, result: Dict[str, Any]) -> None:
        """Set GitHub Actions outputs for use in subsequent steps."""
        try:
            if not os.getenv("GITHUB_OUTPUT"):
                return

            outputs = {
                "success": str(result["success"]).lower(),
                "processing_mode": result["processing_mode"],
                "processing_time": str(result["processing_time"]),
            }

            if result["success"] and result["processing_mode"] == "single_pr":
                assessment = result["results"]["assessment"]
                outputs.update(
                    {
                        "pr_number": str(result["results"]["pr_number"]),
                        "pr_ready": str(assessment["is_ready"]).lower(),
                        "readiness_score": str(assessment["readiness_score"]),
                        "blocking_issues_count": str(
                            assessment["blocking_issues_count"]
                        ),
                    }
                )

            elif result["success"] and result["processing_mode"] == "full_backlog":
                metrics = result["results"]["metrics"]
                outputs.update(
                    {
                        "total_prs": str(metrics["total_prs"]),
                        "ready_prs": str(metrics["ready_prs"]),
                        "automation_rate": str(metrics["automation_rate"]),
                    }
                )

            # Write outputs to GitHub Actions
            with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
                for key, value in outputs.items():
                    f.write(f"{key}={value}\n")

            logger.info(f"Set {len(outputs)} GitHub Actions outputs")

        except Exception as e:
            logger.warning(f"Failed to set GitHub outputs: {e}")

    def check_rate_limits(self) -> Dict[str, Any]:
        """Check GitHub API rate limits before processing."""
        try:
            # This would check actual rate limits via GitHub API
            # For now, return a placeholder
            return {
                "core": {"remaining": 5000, "limit": 5000},
                "search": {"remaining": 30, "limit": 30},
                "graphql": {"remaining": 5000, "limit": 5000},
            }
        except Exception as e:
            logger.warning(f"Failed to check rate limits: {e}")
            return {}

    def should_throttle_processing(self) -> bool:
        """Determine if processing should be throttled due to rate limits."""
        try:
            rate_limits = self.check_rate_limits()
            core_remaining = rate_limits.get("core", {}).get("remaining", 0)

            return core_remaining < self.security_constraints.rate_limit_threshold
        except Exception:
            # Conservative approach - don't throttle if we can't check
            return False


def main():
    """Main entry point for GitHub Actions integration."""
    # Configure logging for GitHub Actions
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Import here to avoid circular imports
    from .core import PRBacklogManager

    try:
        # Initialize PR Backlog Manager
        manager = PRBacklogManager(auto_approve=True)

        # Initialize GitHub Actions integration
        integration = GitHubActionsIntegration(manager)

        # Execute processing
        result = integration.execute_processing()

        # Set GitHub Actions outputs
        integration.set_github_outputs(result)

        # Exit with appropriate code
        exit_code = 0 if result["success"] else 1

        if result["success"]:
            print("✅ PR Backlog Manager completed successfully")
            if result["processing_mode"] == "single_pr":
                assessment = result["results"]["assessment"]
                print(
                    f"PR #{result['results']['pr_number']}: {assessment['status']} "
                    f"(Score: {assessment['readiness_score']:.1f}%)"
                )
            else:
                metrics = result["results"]["metrics"]
                print(
                    f"Processed {metrics['total_prs']} PRs: "
                    f"{metrics['ready_prs']} ready, {metrics['blocked_prs']} blocked"
                )
        else:
            print(f"❌ PR Backlog Manager failed: {result['error']}")

        exit(exit_code)

    except Exception as e:
        logger.error(f"GitHub Actions integration failed: {e}")
        print(f"❌ Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
