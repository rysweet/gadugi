#!/usr/bin/env python3
"""
SubprocessManager - Real subprocess management for orchestrator

This module handles actual subprocess spawning for Claude CLI processes,
ensuring proper WorkflowManager delegation and real parallel execution.
"""

import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SubprocessManager:
    """Manages real Claude CLI subprocess execution"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.process_lock = threading.Lock()

    def spawn_workflow_manager(self, task_id: str, worktree_path: Path,
                             original_prompt: str, task_context: dict) -> subprocess.Popen:
        """Spawn real WorkflowManager subprocess"""

        # Create WorkflowManager prompt with task context
        workflow_prompt = self._create_workflow_manager_prompt(
            task_id, original_prompt, task_context, worktree_path
        )

        # Set up environment for subprocess
        env = os.environ.copy()
        env['ORCHESTRATOR_TASK_ID'] = task_id
        env['ORCHESTRATOR_SUBPROCESS_MODE'] = 'true'
        env['ORCHESTRATOR_WORKTREE'] = str(worktree_path)

        # Use UV if this is a UV project
        if self._is_uv_project(worktree_path):
            env['ORCHESTRATOR_UV_PROJECT'] = 'true'

        # Real Claude CLI command for WorkflowManager delegation
        claude_cmd = [
            "claude",
            "-p", workflow_prompt,
            "--dangerously-skip-permissions",
            "--verbose",
            "--max-turns=50",
            "--output-format=json"
        ]

        logger.info(f"Spawning real subprocess for task {task_id}: {' '.join(claude_cmd)}")
        logger.info(f"Working directory: {worktree_path}")

        # Spawn the actual subprocess
        process = subprocess.Popen(
            claude_cmd,
            cwd=worktree_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Track the process
        with self.process_lock:
            self.active_processes[task_id] = process

        logger.info(f"✅ Real subprocess spawned for task {task_id}: PID {process.pid}")
        return process

    def _create_workflow_manager_prompt(self, task_id: str, original_prompt: str,
                                      task_context: dict, worktree_path: Path) -> str:
        """Create WorkflowManager delegation prompt"""

        # Read original prompt content if it's a file
        original_content = ""
        if original_prompt and Path(original_prompt).exists():
            try:
                with open(original_prompt, 'r') as f:
                    original_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read original prompt {original_prompt}: {e}")
                original_content = f"Original prompt file: {original_prompt}"
        else:
            original_content = original_prompt or f"Task: {task_id}"

        # Create comprehensive WorkflowManager prompt
        workflow_prompt = f"""Execute complete WorkflowManager workflow for task: {task_id}

Task Context: {original_content}

## Orchestrator Context
- **Spawned by**: SimpleOrchestrator (subprocess mode)
- **Task ID**: {task_id}
- **Worktree**: {worktree_path}
- **Parallel Execution**: TRUE
- **Workflow Manager Delegation**: MANDATORY
- **All 11 phases must be executed**

## Task Requirements
{json.dumps(task_context, indent=2)}

CRITICAL: Execute all 11 phases of the WorkflowManager workflow:
1. Initial Setup
2. Issue Creation
3. Branch Management
4. Research and Planning
5. Implementation
6. Testing
7. Documentation
8. Pull Request
9. Review
10. Review Response
11. Settings Update

Begin workflow execution now.
"""

        # Save the prompt to a file
        prompt_file = worktree_path / f".orchestrator_workflow_prompt_{task_id}.md"
        try:
            with open(prompt_file, 'w') as f:
                f.write(workflow_prompt)
            logger.info(f"WorkflowManager prompt saved to: {prompt_file}")
            return str(prompt_file)
        except Exception as e:
            logger.error(f"Failed to save workflow prompt: {e}")
            return workflow_prompt  # Return content directly as fallback

    def _is_uv_project(self, worktree_path: Path) -> bool:
        """Check if worktree contains UV project"""
        return (worktree_path / "pyproject.toml").exists() and (worktree_path / "uv.lock").exists()

    def wait_for_process(self, task_id: str, timeout: Optional[int] = None) -> tuple:
        """Wait for subprocess to complete and return (stdout, stderr, exit_code)"""
        process = self.active_processes.get(task_id)
        if not process:
            return "", f"Process {task_id} not found", -1

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode

            logger.info(f"Process {task_id} completed with exit code: {exit_code}")

            # Clean up
            with self.process_lock:
                if task_id in self.active_processes:
                    del self.active_processes[task_id]

            return stdout, stderr, exit_code

        except subprocess.TimeoutExpired:
            logger.warning(f"Process {task_id} timed out after {timeout} seconds")
            process.kill()
            stdout, stderr = process.communicate()

            with self.process_lock:
                if task_id in self.active_processes:
                    del self.active_processes[task_id]

            return stdout, stderr, -1

        except Exception as e:
            logger.error(f"Error waiting for process {task_id}: {e}")
            return "", str(e), -1

    def cancel_process(self, task_id: str) -> bool:
        """Cancel a running subprocess"""
        process = self.active_processes.get(task_id)
        if not process:
            return False

        try:
            process.terminate()
            # Give it a moment to terminate gracefully
            time.sleep(2)
            if process.poll() is None:
                process.kill()

            with self.process_lock:
                if task_id in self.active_processes:
                    del self.active_processes[task_id]

            logger.info(f"Process {task_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Error cancelling process {task_id}: {e}")
            return False

    def get_process_status(self, task_id: str) -> dict:
        """Get status of subprocess"""
        process = self.active_processes.get(task_id)
        if not process:
            return {"status": "not_found", "pid": None, "exit_code": None}

        exit_code = process.poll()
        if exit_code is None:
            return {"status": "running", "pid": process.pid, "exit_code": None}
        else:
            return {"status": "completed", "pid": process.pid, "exit_code": exit_code}

    def cleanup_all_processes(self):
        """Clean up all running processes"""
        logger.info(f"Cleaning up {len(self.active_processes)} active processes")

        with self.process_lock:
            for task_id, process in list(self.active_processes.items()):
                try:
                    if process.poll() is None:  # Still running
                        process.terminate()
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                    del self.active_processes[task_id]
                except Exception as e:
                    logger.error(f"Error cleaning up process {task_id}: {e}")

        logger.info("All processes cleaned up")
