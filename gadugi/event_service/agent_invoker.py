"""
Agent invocation system for Gadugi Event Service

Handles the actual execution of agents in response to events.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from .config import AgentInvocation
from .events import Event

logger = logging.getLogger(__name__)


class AgentInvoker:
    """Handles agent invocation for event responses."""

    def __init__(self):
        """Initialize the agent invoker."""
        self.claude_cli_path = self._find_claude_cli()
        logger.info(f"Claude CLI path: {self.claude_cli_path}")

    def _find_claude_cli(self) -> str:
        """Find the Claude CLI executable."""
        # Check common locations
        possible_paths = [
            "claude",  # In PATH
            "/usr/local/bin/claude",
            "~/.local/bin/claude",
            "~/bin/claude",
        ]

        for path in possible_paths:
            expanded_path = os.path.expanduser(path)
            if self._is_executable(expanded_path):
                return expanded_path

        # Fallback to just "claude" and hope it's in PATH
        return "claude"

    def _is_executable(self, path: str) -> bool:
        """Check if a file exists and is executable."""
        try:
            return Path(path).is_file() and os.access(path, os.X_OK)
        except Exception:
            return False

    async def invoke_agent(
        self, invocation: AgentInvocation, event: Event
    ) -> Dict[str, Any]:
        """Invoke an agent based on the invocation configuration."""
        method = invocation.method.lower()

        if method == "claude_cli":
            return await self._invoke_claude_cli(invocation, event)
        elif method == "direct":
            return await self._invoke_direct(invocation, event)
        elif method == "subprocess":
            return await self._invoke_subprocess(invocation, event)
        else:
            raise ValueError(f"Unknown invocation method: {method}")

    async def _invoke_claude_cli(
        self, invocation: AgentInvocation, event: Event
    ) -> Dict[str, Any]:
        """Invoke agent using Claude CLI."""
        try:
            # Generate prompt from template
            prompt = self._generate_prompt(invocation, event)

            # Prepare command
            cmd = [self.claude_cli_path, f"/agent:{invocation.agent_name}"]

            # Set working directory
            working_dir = invocation.working_directory or os.getcwd()

            # Prepare environment
            env = os.environ.copy()
            env.update(invocation.environment)

            # Add event context to environment
            env["GADUGI_EVENT_ID"] = event.event_id
            env["GADUGI_EVENT_TYPE"] = event.event_type
            env["GADUGI_EVENT_SOURCE"] = event.source

            logger.info(f"Invoking Claude CLI: {' '.join(cmd)}")
            logger.debug(f"Working directory: {working_dir}")
            logger.debug(f"Prompt: {prompt[:200]}...")

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env,
            )

            # Send prompt and wait for completion
            stdout, stderr = await process.communicate(input=prompt.encode("utf-8"))

            # Check result
            success = process.returncode == 0

            result = {
                "success": success,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "method": "claude_cli",
                "agent_name": invocation.agent_name,
                "event_id": event.event_id,
            }

            if success:
                logger.info(f"Agent {invocation.agent_name} completed successfully")
            else:
                logger.error(
                    f"Agent {invocation.agent_name} failed with return code {process.returncode}"
                )
                logger.error(f"stderr: {result['stderr']}")

            return result

        except Exception as e:
            logger.error(
                f"Error invoking Claude CLI agent {invocation.agent_name}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "method": "claude_cli",
                "agent_name": invocation.agent_name,
                "event_id": event.event_id,
            }

    async def _invoke_direct(
        self, invocation: AgentInvocation, event: Event
    ) -> Dict[str, Any]:
        """Invoke agent directly (for Python agents)."""
        try:
            # This would require importing and calling agent modules directly
            # For now, we'll use subprocess as fallback
            logger.warning(
                f"Direct invocation not yet implemented for {invocation.agent_name}, using subprocess"
            )
            return await self._invoke_subprocess(invocation, event)

        except Exception as e:
            logger.error(f"Error invoking direct agent {invocation.agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "direct",
                "agent_name": invocation.agent_name,
                "event_id": event.event_id,
            }

    async def _invoke_subprocess(
        self, invocation: AgentInvocation, event: Event
    ) -> Dict[str, Any]:
        """Invoke agent as subprocess."""
        try:
            # Generate prompt
            prompt = self._generate_prompt(invocation, event)

            # Create temporary file for prompt
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(prompt)
                prompt_file = f.name

            try:
                # Prepare command (assume it's a script that takes prompt file as argument)
                cmd = [invocation.agent_name, prompt_file]

                # Set working directory
                working_dir = invocation.working_directory or os.getcwd()

                # Prepare environment
                env = os.environ.copy()
                env.update(invocation.environment)
                env["GADUGI_EVENT_ID"] = event.event_id
                env["GADUGI_EVENT_TYPE"] = event.event_type
                env["GADUGI_EVENT_SOURCE"] = event.source

                logger.info(f"Invoking subprocess: {' '.join(cmd)}")

                # Execute command
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir,
                    env=env,
                )

                stdout, stderr = await process.communicate()

                success = process.returncode == 0

                result = {
                    "success": success,
                    "returncode": process.returncode,
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "method": "subprocess",
                    "agent_name": invocation.agent_name,
                    "event_id": event.event_id,
                }

                if success:
                    logger.info(
                        f"Subprocess agent {invocation.agent_name} completed successfully"
                    )
                else:
                    logger.error(
                        f"Subprocess agent {invocation.agent_name} failed with return code {process.returncode}"
                    )

                return result

            finally:
                # Clean up temporary file
                try:
                    os.unlink(prompt_file)
                except FileNotFoundError:
                    # File may already be deleted, ignore
                    pass
                except Exception as e:
                    logger.warning(f"Error deleting temp prompt file: {e}")

        except Exception as e:
            logger.error(
                f"Error invoking subprocess agent {invocation.agent_name}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "method": "subprocess",
                "agent_name": invocation.agent_name,
                "event_id": event.event_id,
            }

    def _generate_prompt(self, invocation: AgentInvocation, event: Event) -> str:
        """Generate agent prompt from template and event data."""
        template = invocation.prompt_template

        if not template:
            # Default template
            template = (
                f"Process event: {event.event_type}\n\nEvent data: {event.to_json()}"
            )

        # Prepare template variables
        variables = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "source": event.source,
        }

        # Add metadata
        variables.update(event.metadata)

        # Add event-specific variables
        if event.is_github_event():
            github_event = event.get_github_event()
            if github_event:
                variables.update(
                    {
                        "repository": github_event.repository,
                        "number": github_event.number or "",
                        "action": github_event.action,
                        "actor": github_event.actor,
                        "title": github_event.title,
                        "body": github_event.body,
                        "state": github_event.state,
                        "labels": ", ".join(github_event.labels),
                        "assignees": ", ".join(github_event.assignees),
                        "milestone": github_event.milestone,
                        "ref": github_event.ref,
                    }
                )

        elif event.is_local_event():
            local_event = event.get_local_event()
            if local_event:
                variables.update(
                    {
                        "event_name": local_event.event_name,
                        "working_directory": local_event.working_directory,
                        "files_changed": ", ".join(local_event.files_changed),
                    }
                )

        elif event.is_agent_event():
            agent_event = event.get_agent_event()
            if agent_event:
                variables.update(
                    {
                        "agent_name": agent_event.agent_name,
                        "task_id": agent_event.task_id,
                        "phase": agent_event.phase,
                        "status": agent_event.status,
                        "message": agent_event.message,
                    }
                )

        # Add invocation parameters
        variables.update(invocation.parameters)

        # Perform template substitution
        try:
            prompt = template.format(**variables)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}, using template as-is")
            prompt = template

        return prompt

    def validate_invocation(self, invocation: AgentInvocation) -> bool:
        """Validate that an invocation configuration is valid."""
        if not invocation.agent_name:
            logger.error("Agent name is required")
            return False

        if invocation.method not in ["claude_cli", "direct", "subprocess"]:
            logger.error(f"Invalid invocation method: {invocation.method}")
            return False

        if invocation.method == "claude_cli":
            if (
                not self._is_executable(self.claude_cli_path)
                and self.claude_cli_path != "claude"
            ):
                logger.warning(f"Claude CLI not found at {self.claude_cli_path}")
                # Don't fail validation - might be in PATH

        return True
