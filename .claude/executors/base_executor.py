#!/usr/bin/env python3
"""Base Executor - Abstract base class for all single-purpose executors.

This defines the standard interface that all executors must follow.
All executors MUST follow the NO DELEGATION principle.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List


class BaseExecutor(ABC):
    """Abstract base class for all executors.

    CRITICAL PRINCIPLES:
    1. NO DELEGATION: Executors MUST NOT call or delegate to other agents
    2. SINGLE PURPOSE: Each executor has exactly one responsibility
    3. DIRECT TOOLS: Use only direct tool/system calls, no agent invocations
    4. RETURN RESULTS: Always return structured results for coordination
    """

    def __init__(self):
        """Initialize the base executor."""
        self.name = self.__class__.__name__
        self.operations_log = []
        self.created_at = datetime.now()

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the single-purpose operation.

        This is the ONLY public method that executors should expose.
        All functionality must be accessible through this single entry point.

        Args:
            params: Dictionary of parameters for the operation

        Returns:
            Dictionary with:
                - success: Boolean indicating if operation succeeded
                - result: Operation-specific result data
                - error: Error message if operation failed

        IMPORTANT: This method MUST NOT call other agents or executors.
        """
        pass

    def validate_params(
        self, params: Dict[str, Any], required: List[str]
    ) -> Dict[str, Any]:
        """Validate that required parameters are present.

        Args:
            params: Parameters to validate
            required: List of required parameter names

        Returns:
            Validation result with success and error if failed
        """
        missing = [param for param in required if param not in params]

        if missing:
            return {
                "success": False,
                "error": f'Missing required parameters: {", ".join(missing)}',
            }

        return {"success": True}

    def log_operation(self, operation: str, details: Dict[str, Any] = None):  # type: ignore[assignment]
        """Log an operation for audit purposes.

        Args:
            operation: Name of the operation performed
            details: Additional details about the operation
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "executor": self.name,
            "operation": operation,
            "details": details or {},
        }
        self.operations_log.append(log_entry)

    def get_operations_log(self) -> List[Dict[str, Any]]:
        """Get the complete operations log.

        Returns:
            List of all logged operations
        """
        return self.operations_log.copy()

    def create_success_response(self, **kwargs) -> Dict[str, Any]:
        """Create a standardized success response.

        Args:
            **kwargs: Additional fields to include in response

        Returns:
            Success response dictionary
        """
        response = {"success": True, "executor": self.name}
        response.update(kwargs)
        return response

    def create_error_response(self, error: str, **kwargs) -> Dict[str, Any]:
        """Create a standardized error response.

        Args:
            error: Error message
            **kwargs: Additional fields to include in response

        Returns:
            Error response dictionary
        """
        response = {"success": False, "executor": self.name, "error": error}
        response.update(kwargs)
        return response


class ExecutorRegistry:
    """Registry for managing available executors.

    This allows dynamic discovery and invocation of executors
    without violating the no-delegation principle.
    """

    def __init__(self):
        """Initialize the executor registry."""
        self._executors = {}

    def register(self, name: str, executor_class: type):
        """Register an executor class.

        Args:
            name: Name to register the executor under
            executor_class: The executor class (not instance)
        """
        if not issubclass(executor_class, BaseExecutor):
            raise ValueError(f"{executor_class} must inherit from BaseExecutor")

        self._executors[name] = executor_class

    def get(self, name: str) -> BaseExecutor:
        """Get an instance of a registered executor.

        Args:
            name: Name of the executor to get

        Returns:
            New instance of the executor

        Raises:
            KeyError: If executor not found
        """
        if name not in self._executors:
            raise KeyError(
                f"Executor '{name}' not found. Available: {list(self._executors.keys())}"
            )

        return self._executors[name]()

    def list_executors(self) -> List[str]:
        """List all registered executor names.

        Returns:
            List of executor names
        """
        return list(self._executors.keys())

    def execute(self, executor_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an operation using a named executor.

        This is a convenience method for CLAUDE.md orchestration.

        Args:
            executor_name: Name of the executor to use
            params: Parameters for the operation

        Returns:
            Operation result
        """
        executor = self.get(executor_name)
        return executor.execute(params)


# Global registry instance
registry = ExecutorRegistry()
