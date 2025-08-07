#!/usr/bin/env python3
"""Test the orchestrator with our prompt files."""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Add orchestrator to path
sys.path.insert(0, '.claude/orchestrator')

from orchestrator_cli import OrchestrationCLI, OrchestrationConfig

# Initialize CLI
cli = OrchestrationCLI('.')

# Test files
prompt_files = [
    'prompts/fix-test-pyright-errors.md',
    'prompts/fix-service-pyright-errors.md',
    'prompts/fix-engine-pyright-errors.md'
]

# Validate files
validated = cli._validate_prompt_files(prompt_files)
print(f"Validated {len(validated)} files: {validated}")

if not validated:
    print("No files validated, exiting")
    sys.exit(1)

# Try to execute with a short timeout
config = OrchestrationConfig(
    max_parallel_tasks=3,
    execution_timeout_hours=0.1  # 6 minutes
)

print("Starting orchestration...")
try:
    result = cli.execute_orchestration(validated, config)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()