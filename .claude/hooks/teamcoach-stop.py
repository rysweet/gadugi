#!/usr/bin/env python3
"""
TeamCoach Stop Hook - Automated Team Performance Analysis

This hook is triggered when Claude Code sessions end (Stop event) to automatically
invoke TeamCoach for session outcome analysis and team coaching recommendations.

Hook Type: Stop
Purpose: Analyze session performance and provide team coaching insights
"""

import json
import sys
import subprocess
import os
from datetime import datetime


def invoke_teamcoach():
    """Invoke TeamCoach agent for session analysis."""

    # CRITICAL: Check for cascade prevention flag
    if os.environ.get("CLAUDE_HOOK_EXECUTION", "0") == "1":
        print("🛡️ Cascade prevention: TeamCoach hook skipped during hook execution")
        return True

    # Create TeamCoach prompt for session analysis
    teamcoach_prompt = """
Task: Analyze completed session and provide team coaching recommendations

Context:
- Claude Code session just completed - analyze performance and outcomes
- Update agent capability assessments based on recent work
- Identify coaching opportunities and optimization recommendations
- Detect any coordination issues or conflicts that occurred
- Provide actionable insights for future improvement

Analysis Focus:
- Performance metrics from the completed session
- Task success rates and execution efficiency
- Collaboration effectiveness and communication patterns
- Resource utilization and workflow optimization opportunities
- Strategic recommendations for ongoing team development

Deliverables:
- Updated performance analytics and capability profiles
- Specific coaching recommendations with evidence
- Process optimization suggestions
- Conflict resolution if issues detected
- Strategic insights for future task assignments

Mode: Post-session analysis with focus on continuous improvement
""".strip()

    try:
        # Set cascade prevention environment variable
        env = os.environ.copy()
        env["CLAUDE_HOOK_EXECUTION"] = "1"

        # Invoke TeamCoach using Claude Code CLI with cascade prevention
        result = subprocess.run(
            ["claude", "/agent:teamcoach", teamcoach_prompt],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )  # 5 minute timeout

        if result.returncode == 0:
            print("✅ TeamCoach analysis completed successfully")
            # Don't print the full output to avoid cluttering the hook output
            # The analysis will be visible in the main Claude interface
            return True
        else:
            print(f"⚠️ TeamCoach analysis failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️ TeamCoach analysis timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"⚠️ Error invoking TeamCoach: {e}")
        return False


def main():
    """Main hook handler."""
    try:
        # Read hook input from stdin (though we don't need it for this hook)
        sys.stdin.read()

        # Invoke TeamCoach for session analysis
        success = invoke_teamcoach()

        # Output hook result
        result = {
            "action": "continue",  # Always continue, don't block
            "message": "TeamCoach session analysis completed"
            if success
            else "TeamCoach analysis encountered issues",
            "timestamp": datetime.now().isoformat(),
        }

        print(json.dumps(result))

        # Exit with success regardless - we don't want to block the session end
        sys.exit(0)

    except Exception as e:
        # Log error but don't block session end
        error_result = {
            "action": "continue",
            "message": f"TeamCoach hook error: {e}",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(error_result))
        sys.exit(0)


if __name__ == "__main__":
    main()
