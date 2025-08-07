#!/usr/bin/env python3
"""Direct test of orchestrator bypassing claude CLI"""

import subprocess
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / ".claude/orchestrator"))

from orchestrator_main import OrchestratorCoordinator, OrchestrationConfig

# Create test configuration
config = OrchestrationConfig(
    max_parallel_tasks=2,
    execution_timeout_hours=1
)

# Initialize orchestrator
orchestrator = OrchestratorCoordinator(config, ".")

# Monkey-patch the execution to bypass claude CLI
def mock_execute_subprocess_fallback(self, timeout=None):
    """Mock execution that just runs the command from the prompt file"""
    from components.execution_engine import ExecutionResult
    from datetime import datetime
    
    print(f"Mock executing task: {self.task_id}")
    
    # Read the prompt file and execute it as a shell command
    try:
        with open(self.prompt_file, 'r') as f:
            command = f.read().strip()
        
        # Run the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        
        return ExecutionResult(
            task_id=self.task_id,
            task_name=self.task_context.get('task_name', 'test'),
            status='success' if result.returncode == 0 else 'failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            output_file=None,
            error_message=result.stderr if result.returncode != 0 else None,
            resource_usage={}
        )
    except Exception as e:
        return ExecutionResult(
            task_id=self.task_id,
            task_name=self.task_context.get('task_name', 'test'),
            status='failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            exit_code=1,
            stdout='',
            stderr=str(e),
            output_file=None,
            error_message=str(e),
            resource_usage={}
        )

# Apply the monkey patch
from components.execution_engine import TaskExecutor
TaskExecutor._execute_subprocess_fallback = mock_execute_subprocess_fallback

# Test with simple prompt
print("Testing orchestrator with mocked execution...")
result = orchestrator.orchestrate(["test-simple.md"])

print(f"\nResults:")
print(f"  Total tasks: {result.total_tasks}")
print(f"  Successful: {result.successful_tasks}")
print(f"  Failed: {result.failed_tasks}")
print(f"  Execution time: {result.execution_time_seconds:.2f}s")

# Cleanup
orchestrator.shutdown()