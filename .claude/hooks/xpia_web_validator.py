#!/usr/bin/env python3
"""
XPIA Web Validator - Claude Code Hook for Web Operations
Validates WebFetch and WebSearch operations for security threats
"""

import sys
import json
from pathlib import Path

# Add shared modules to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from xpia_defense import XPIADefenseAgent, SecurityMode  # type: ignore[import]


def validate_web_operation(hook_data):
    """Validate web operations for XPIA threats"""
    try:
        # Initialize XPIA agent
        xpia_agent = XPIADefenseAgent(SecurityMode.BALANCED)

        # Extract operation details
        event_type = hook_data.get("event", "")
        tool_name = hook_data.get("toolName", "")

        # Handle PreToolUse events
        if event_type == "PreToolUse":
            tool_input = hook_data.get("toolInput", {})

            if tool_name == "WebFetch":
                url = tool_input.get("url", "")
                prompt = tool_input.get("prompt", "")

                # Validate URL
                url_result = xpia_agent.validate_user_input(
                    url, user_context="web_fetch_url"
                )

                # Validate prompt
                prompt_result = xpia_agent.validate_user_input(
                    prompt, user_context="web_fetch_prompt"
                )

                # Check for threats
                if not url_result.is_safe:
                    return {
                        "error": f"XPIA Security: Malicious URL detected - {url_result.threat_level.value}",
                        "block": True,
                        "threats": [
                            t["description"] for t in url_result.threats_detected
                        ],
                    }

                if not prompt_result.is_safe:
                    return {
                        "error": f"XPIA Security: Malicious prompt detected - {prompt_result.threat_level.value}",
                        "block": True,
                        "threats": [
                            t["description"] for t in prompt_result.threats_detected
                        ],
                    }

                # If safe but sanitized, return modified input
                if prompt_result.sanitization_applied:
                    return {
                        "modifiedToolInput": {
                            "url": url_result.sanitized_content,
                            "prompt": prompt_result.sanitized_content,
                        },
                        "warning": "XPIA: Content sanitized for safety",
                    }

            elif tool_name == "WebSearch":
                query = tool_input.get("query", "")

                # Validate search query
                result = xpia_agent.validate_user_input(
                    query, user_context="web_search_query"
                )

                if not result.is_safe:
                    return {
                        "error": f"XPIA Security: Malicious search query - {result.threat_level.value}",
                        "block": True,
                        "threats": [t["description"] for t in result.threats_detected],
                    }

                # Return sanitized query if needed
                if result.sanitization_applied:
                    return {
                        "modifiedToolInput": {"query": result.sanitized_content},
                        "warning": "XPIA: Search query sanitized",
                    }

        # Handle PostToolUse events
        elif event_type == "PostToolUse":
            tool_output = hook_data.get("toolOutput", "")

            # Validate returned content
            result = xpia_agent.validate_file_content(
                str(tool_output),
                filename=f"{tool_name}_output",
                file_type="web_content",
            )

            if not result.is_safe:
                return {
                    "modifiedToolOutput": "[XPIA: Web content blocked due to security threat]",
                    "warning": f"XPIA blocked malicious content from {tool_name}",
                }

            if result.sanitization_applied:
                return {
                    "modifiedToolOutput": result.sanitized_content,
                    "info": "XPIA: Web content sanitized",
                }

        # Allow by default
        return {"allow": True}

    except Exception as e:
        # Log error but don't block on failure
        return {"warning": f"XPIA validation error: {str(e)}", "allow": True}


def main():
    """Main entry point for the hook"""
    try:
        # Read hook data from stdin
        hook_data = json.load(sys.stdin)

        # Validate the operation
        result = validate_web_operation(hook_data)

        # Check if we should block
        if result.get("block"):
            print(
                json.dumps(
                    {
                        "error": result.get(
                            "error", "XPIA Security: Operation blocked"
                        ),
                        "details": result.get("threats", []),
                    }
                )
            )
            sys.exit(2)  # Blocking error

        # Output any modifications or warnings
        if "modifiedToolInput" in result or "modifiedToolOutput" in result:
            print(
                json.dumps(
                    {
                        "modifiedToolInput": result.get("modifiedToolInput"),
                        "modifiedToolOutput": result.get("modifiedToolOutput"),
                        "message": result.get("warning")
                        or result.get("info", "XPIA: Content modified"),
                    }
                )
            )
        elif "warning" in result:
            print(result["warning"])

        sys.exit(0)  # Success

    except Exception as e:
        print(f"XPIA hook error: {str(e)}", file=sys.stderr)
        sys.exit(0)  # Don't block on errors


if __name__ == "__main__":
    main()
