#!/usr/bin/env python3
"""Gadugi Executors - Single-purpose executors for the simplified architecture.

All executors follow the NO DELEGATION principle:
- No calling other agents
- Direct tool/system usage only
- Single responsibility per executor
- Return results for CLAUDE.md orchestration
"""

from .base_executor import BaseExecutor, ExecutorRegistry, registry
from .code_executor import CodeExecutor, execute_code_operation
from .test_executor import TestExecutor, execute_tests
from .github_executor import GitHubExecutor, execute_github_operation
from .worktree_executor import WorktreeExecutor, execute_worktree_operation

# Register all executors
registry.register("code", CodeExecutor)
registry.register("test", TestExecutor)
registry.register("github", GitHubExecutor)
registry.register("worktree", WorktreeExecutor)


# Convenience functions for CLAUDE.md orchestration
def execute(executor_name: str, params: dict) -> dict:
    """Execute an operation using a named executor.

    This is the primary interface for CLAUDE.md to use executors.

    Args:
        executor_name: Name of the executor ('code', 'test', 'github', 'worktree')
        params: Parameters for the operation

    Returns:
        Operation result dictionary

    Example:
        # Write a file
        result = execute('code', {
            'action': 'write',
            'file_path': 'hello.py',
            'content': 'print("Hello, World!")'
        })

        # Run tests
        result = execute('test', {
            'test_framework': 'pytest',
            'test_path': 'tests/'
        })
    """
    return registry.execute(executor_name, params)


def list_executors() -> list:
    """List all available executors.

    Returns:
        List of executor names
    """
    return registry.list_executors()


# Export main interfaces
__all__ = [
    # Base classes
    "BaseExecutor",
    "ExecutorRegistry",
    "registry",
    # Executor classes
    "CodeExecutor",
    "TestExecutor",
    "GitHubExecutor",
    "WorktreeExecutor",
    # Direct function interfaces
    "execute_code_operation",
    "execute_tests",
    "execute_github_operation",
    "execute_worktree_operation",
    # Convenience functions
    "execute",
    "list_executors",
]
