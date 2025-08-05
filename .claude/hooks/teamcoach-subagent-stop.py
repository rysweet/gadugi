#!/usr/bin/env python3
"""
TeamCoach SubagentStop Hook - Agent Performance Analysis

This hook is triggered when subagents complete their tasks to automatically
invoke TeamCoach for individual agent performance analysis and capability updates.

Hook Type: SubagentStop
Purpose: Analyze individual agent performance and update capability assessments
"""

import json
import sys
import subprocess
import os
from datetime import datetime


def invoke_teamcoach_agent_analysis(agent_data):
    """Invoke TeamCoach for specific agent performance analysis."""

    # CRITICAL: Check for cascade prevention flag
    if os.environ.get("CLAUDE_HOOK_EXECUTION", "0") == "1":
        print(
            "🛡️ Cascade prevention: TeamCoach subagent hook skipped during hook execution"
        )
        return True

    # Extract agent information from hook input
    agent_name = agent_data.get("agent_name", "unknown-agent")
    task_result = agent_data.get("result", "unknown")
    duration = agent_data.get("duration", 0)

    # Create TeamCoach prompt for agent-specific analysis
    teamcoach_prompt = f"""
Task: Analyze individual agent performance and update capability assessment

Context:
- Subagent '{agent_name}' just completed a task
- Task result: {task_result}
- Duration: {duration} seconds
- Need to update performance metrics and capability profile

Agent Analysis Focus:
- Update performance metrics for agent '{agent_name}'
- Assess task execution quality and efficiency
- Update capability scores based on demonstrated performance
- Identify skill development opportunities
- Check for performance trends and patterns

Deliverables:
- Updated performance profile for agent '{agent_name}'
- Capability assessment updates with new evidence
- Performance trend analysis
- Coaching recommendations specific to this agent
- Strategic insights for future task assignments to this agent

Mode: Individual agent performance analysis with capability updates
Agent: {agent_name}
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
            timeout=180,
            env=env,
        )  # 3 minute timeout

        if result.returncode == 0:
            print(f"✅ TeamCoach agent analysis completed for {agent_name}")
            return True
        else:
            print(
                f"⚠️ TeamCoach agent analysis failed for {agent_name}: {result.stderr}"
            )
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️ TeamCoach agent analysis timed out for {agent_name}")
        return False
    except Exception as e:
        print(f"⚠️ Error in TeamCoach agent analysis for {agent_name}: {e}")
        return False


def main():
    """Main hook handler for subagent completion."""
    try:
        # Read hook input from stdin
        hook_input = sys.stdin.read()

        # Parse hook input JSON
        try:
            hook_data = json.loads(hook_input) if hook_input.strip() else {}
        except json.JSONDecodeError:
            hook_data = {}

        # Invoke TeamCoach for agent analysis
        success = invoke_teamcoach_agent_analysis(hook_data)

        # Output hook result
        result = {
            "action": "continue",  # Always continue, don't block
            "message": "TeamCoach agent analysis completed"
            if success
            else "TeamCoach agent analysis encountered issues",
            "timestamp": datetime.now().isoformat(),
        }

        print(json.dumps(result))

        # Exit with success regardless - we don't want to block the workflow
        sys.exit(0)

    except Exception as e:
        # Log error but don't block workflow
        error_result = {
            "action": "continue",
            "message": f"TeamCoach subagent hook error: {e}",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(error_result))
        sys.exit(0)


if __name__ == "__main__":
    main()
